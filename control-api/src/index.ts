import { commandKinds, DeviceRow, Env, setupSteps } from "./types";
import { HttpError, randomToken, sha256, verifyDeviceSignature } from "./security";

const jsonHeaders = { "Content-Type": "application/json", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" };
const response = (data: unknown, status = 200) => new Response(JSON.stringify(data), { status, headers: jsonHeaders });

export default {
  async fetch(request: Request, env: Env, context: ExecutionContext): Promise<Response> {
    try {
      // Run lightweight retention maintenance on roughly 1 in 256 normal requests.
      if (crypto.getRandomValues(new Uint8Array(1))[0] === 0) context.waitUntil(cleanup(env));
      const url = new URL(request.url);
      if (request.method === "GET" && url.pathname === "/health") return response({ status: "ok" });
      if (request.method === "POST" && url.pathname === "/v1/devices/pair") return await pair(request, env);
      const statusMatch = url.pathname.match(/^\/v1\/devices\/([0-9a-f-]{36})\/status$/i);
      if (request.method === "POST" && statusMatch?.[1]) return await deviceStatus(request, env, statusMatch[1]);
      const commandsMatch = url.pathname.match(/^\/v1\/devices\/([0-9a-f-]{36})\/commands$/i);
      if (request.method === "GET" && commandsMatch?.[1]) return await deviceCommands(request, env, commandsMatch[1]);
      if (url.pathname.startsWith("/v1/admin/")) {
        requireAdmin(request);
        if (request.method === "POST" && url.pathname === "/v1/admin/pairing-codes") return await createPairingCode(request, env);
        if (request.method === "GET" && url.pathname === "/v1/admin/devices") return await listDevices(env);
        const adminCommand = url.pathname.match(/^\/v1\/admin\/devices\/([0-9a-f-]{36})\/commands$/i);
        if (request.method === "POST" && adminCommand?.[1]) return await createCommand(request, env, adminCommand[1]);
        const adminDevice = url.pathname.match(/^\/v1\/admin\/devices\/([0-9a-f-]{36})$/i);
        if (request.method === "DELETE" && adminDevice?.[1]) return await deleteDevice(request, env, adminDevice[1]);
        const adminHousehold = url.pathname.match(/^\/v1\/admin\/households\/([0-9a-f-]{36})$/i);
        if (request.method === "DELETE" && adminHousehold?.[1]) return await deleteHousehold(request, env, adminHousehold[1]);
      }
      return response({ error: "not_found" }, 404);
    } catch (error) {
      if (error instanceof HttpError) return response({ error: error.code }, error.status);
      console.error(error instanceof Error ? error.message : "unknown_error");
      return response({ error: "internal_error" }, 500);
    }
  },

  async scheduled(_controller: ScheduledController, env: Env): Promise<void> {
    await cleanup(env);
  },
} satisfies ExportedHandler<Env>;

async function cleanup(env: Env): Promise<void> {
  const now = Math.floor(Date.now() / 1000);
  await env.DB.batch([
    env.DB.prepare("DELETE FROM request_nonces WHERE expires_at < ?").bind(now),
    env.DB.prepare("DELETE FROM pairing_codes WHERE expires_at < ? OR used_at IS NOT NULL").bind(now),
    env.DB.prepare("DELETE FROM audit WHERE created_at < ?").bind(now - Number(env.STATUS_RETENTION_DAYS) * 86400),
  ]);
}

async function pair(request: Request, env: Env): Promise<Response> {
  const bodyText = await limitedBody(request);
  const body = parseObject(bodyText);
  const code = text(body.code, 6, 12); const publicKey = text(body.publicKey, 80, 256); const model = text(body.model, 1, 128); const osVersion = text(body.osVersion, 1, 64);
  // Prove possession before consuming the one-time code.
  await verifyDeviceSignature(request, bodyText, publicKey);
  const codeHash = await sha256(code);
  const now = Math.floor(Date.now() / 1000);
  const pairing = await env.DB.prepare("SELECT household_id FROM pairing_codes WHERE code_hash=? AND expires_at>? AND used_at IS NULL").bind(codeHash, now).first<{ household_id: string }>();
  if (!pairing) throw new HttpError(401, "invalid_or_expired_pairing_code");
  const id = crypto.randomUUID(); const marker = crypto.randomUUID(); const token = randomToken(); const tokenHash = await sha256(token);
  const result = await env.DB.batch([
    env.DB.prepare("UPDATE pairing_codes SET used_at=?,used_marker=? WHERE code_hash=? AND used_at IS NULL").bind(now, marker, codeHash),
    env.DB.prepare("INSERT INTO devices(id,household_id,public_key_spki,token_hash,model,os_version,created_at,last_seen_at) SELECT ?,household_id,?,?,?,?,?,? FROM pairing_codes WHERE code_hash=? AND used_marker=?").bind(id, publicKey, tokenHash, model, osVersion, now, now, codeHash, marker),
  ]);
  if (!result.every(item => item.success) || Number(result[0]?.meta.changes ?? 0) !== 1 || Number(result[1]?.meta.changes ?? 0) !== 1) throw new HttpError(409, "pairing_race");
  return response({ deviceId: id, token }, 201);
}

async function authenticateDevice(request: Request, env: Env, id: string, body: string): Promise<DeviceRow> {
  const authorization = request.headers.get("Authorization") ?? "";
  if (!authorization.startsWith("Bearer ")) throw new HttpError(401, "device_token_required");
  const row = await env.DB.prepare("SELECT * FROM devices WHERE id=? AND deleted_at IS NULL").bind(id).first<DeviceRow>();
  if (!row || !constantTime(await sha256(authorization.slice(7)), row.token_hash)) throw new HttpError(401, "invalid_device_token");
  const signed = await verifyDeviceSignature(request, body, row.public_key_spki);
  try { await env.DB.prepare("INSERT INTO request_nonces(device_id,nonce,expires_at) VALUES(?,?,?)").bind(id, signed.nonce, signed.timestamp + 600).run(); }
  catch { throw new HttpError(409, "replayed_request"); }
  return row;
}

async function deviceStatus(request: Request, env: Env, id: string): Promise<Response> {
  const bodyText = await limitedBody(request); await authenticateDevice(request, env, id, bodyText); const body = parseObject(bodyText);
  const setupStep = text(body.setupStep, 1, 32); if (!setupSteps.includes(setupStep as typeof setupSteps[number])) throw new HttpError(400, "invalid_setup_step");
  const appVersion = integer(body.appVersion, 1, 1_000_000_000); const configVersion = optionalText(body.configVersion, 32); const errorCode = optionalText(body.errorCode, 64); const expiry = optionalIsoDate(body.debridExpiry);
  await env.DB.prepare("UPDATE devices SET setup_step=?,app_version=?,config_version=?,error_code=?,debrid_expiry=?,last_seen_at=? WHERE id=?").bind(setupStep, appVersion, configVersion, errorCode, expiry, Math.floor(Date.now() / 1000), id).run();
  return response({ accepted: true });
}

async function deviceCommands(request: Request, env: Env, id: string): Promise<Response> {
  await authenticateDevice(request, env, id, "");
  const rows = await env.DB.prepare("SELECT id,kind,payload,created_at FROM commands WHERE device_id=? AND delivered_at IS NULL ORDER BY created_at LIMIT 20").bind(id).all();
  const ids = rows.results.map(row => String(row.id));
  if (ids.length) {
    const now = Math.floor(Date.now() / 1000);
    await env.DB.batch(ids.map(commandId => env.DB.prepare("UPDATE commands SET delivered_at=? WHERE id=? AND device_id=? AND delivered_at IS NULL").bind(now, commandId, id)));
  }
  return response({ commands: rows.results });
}

async function createPairingCode(request: Request, env: Env): Promise<Response> {
  const body = parseObject(await limitedBody(request)); const alias = text(body.householdAlias, 1, 80); const householdId = crypto.randomUUID();
  const code = String(crypto.getRandomValues(new Uint32Array(1))[0]! % 100_000_000).padStart(8, "0"); const codeHash = await sha256(code); const now = Math.floor(Date.now() / 1000);
  await env.DB.batch([env.DB.prepare("INSERT INTO households(id,alias,created_at) VALUES(?,?,?)").bind(householdId, alias, now), env.DB.prepare("INSERT INTO pairing_codes(code_hash,household_id,expires_at) VALUES(?,?,?)").bind(codeHash, householdId, now + Number(env.PAIRING_TTL_SECONDS))]);
  await audit(env, request, "pairing.created", householdId, "One-time pairing code created"); return response({ code, expiresAt: now + Number(env.PAIRING_TTL_SECONDS) }, 201);
}

async function listDevices(env: Env): Promise<Response> {
  const rows = await env.DB.prepare("SELECT d.id,h.id AS householdId,h.alias AS householdAlias,d.model,d.os_version AS osVersion,d.app_version AS appVersion,d.config_version AS configVersion,d.setup_step AS setupStep,d.error_code AS errorCode,d.debrid_expiry AS debridExpiry,d.last_seen_at AS lastSeenAt FROM devices d JOIN households h ON h.id=d.household_id WHERE d.deleted_at IS NULL ORDER BY d.last_seen_at DESC").all();
  return response({ devices: rows.results });
}

async function createCommand(request: Request, env: Env, deviceId: string): Promise<Response> {
  const body = parseObject(await limitedBody(request)); const kind = text(body.kind, 1, 32);
  if (!commandKinds.includes(kind as typeof commandKinds[number])) throw new HttpError(400, "unsupported_command");
  const payload = validateCommandPayload(kind, body.payload ?? {});
  const exists = await env.DB.prepare("SELECT id FROM devices WHERE id=? AND deleted_at IS NULL").bind(deviceId).first(); if (!exists) throw new HttpError(404, "device_not_found");
  const id = crypto.randomUUID(); await env.DB.prepare("INSERT INTO commands(id,device_id,kind,payload,created_at) VALUES(?,?,?,?,?)").bind(id, deviceId, kind, JSON.stringify(payload), Math.floor(Date.now() / 1000)).run();
  await audit(env, request, "command.created", deviceId, kind); return response({ id }, 201);
}

export function validateCommandPayload(kind: string, input: unknown): Record<string, unknown> {
  if (!input || typeof input !== "object" || Array.isArray(input)) throw new HttpError(400, "invalid_payload");
  const payload = input as Record<string, unknown>; const keys = Object.keys(payload);
  const only = (allowed: string[]) => { if (keys.some(key => !allowed.includes(key))) throw new HttpError(400, "invalid_payload_field"); };
  if (["START_SETUP", "INSTALL_KODI", "INSTALL_PROTON", "PREPARE_BOOTSTRAP", "OPEN_KODI", "BEGIN_REAL_DEBRID_AUTH", "RETRY_CURRENT_STEP"].includes(kind)) only([]);
  else if (kind === "SYNC_CONFIG") { only(["configVersion"]); if (payload.configVersion !== undefined) text(payload.configVersion, 1, 32); }
  else if (kind === "RETRY_STEP") { only(["step"]); if (payload.step !== undefined && !setupSteps.includes(text(payload.step, 1, 32) as typeof setupSteps[number])) throw new HttpError(400, "invalid_setup_step"); }
  else if (kind === "OPEN_AUTHORIZATION") { only(["provider"]); if (payload.provider !== undefined && !["real-debrid", "proton"].includes(text(payload.provider, 1, 32))) throw new HttpError(400, "invalid_provider"); }
  else if (kind === "REQUEST_DIAGNOSTICS") { only(["reason", "requiresConsent"]); if (payload.reason !== undefined) text(payload.reason, 1, 160); if (payload.requiresConsent !== true) throw new HttpError(400, "diagnostic_consent_required"); }
  if (JSON.stringify(payload).length > 2048) throw new HttpError(400, "invalid_payload");
  return payload;
}

async function deleteDevice(request: Request, env: Env, id: string): Promise<Response> {
  const exists = await env.DB.prepare("SELECT id FROM devices WHERE id=?").bind(id).first();
  if (!exists) throw new HttpError(404, "device_not_found");
  await env.DB.prepare("DELETE FROM devices WHERE id=?").bind(id).run();
  await audit(env, request, "device.deleted", id, "Device access revoked"); return new Response(null, { status: 204, headers: jsonHeaders });
}

async function deleteHousehold(request: Request, env: Env, id: string): Promise<Response> {
  const exists = await env.DB.prepare("SELECT id FROM households WHERE id=?").bind(id).first();
  if (!exists) throw new HttpError(404, "household_not_found");
  await audit(env, request, "household.deleted", id, "Household cloud data permanently removed");
  await env.DB.prepare("DELETE FROM households WHERE id=?").bind(id).run();
  return new Response(null, { status: 204, headers: jsonHeaders });
}

function requireAdmin(request: Request): void {
  // Cloudflare Access validates this assertion before the Worker route. Requiring both headers prevents an accidentally unprotected route from acting anonymously.
  if (!request.headers.get("Cf-Access-Jwt-Assertion")) throw new HttpError(401, "cloudflare_access_required");
}
async function audit(env: Env, request: Request, action: string, target: string, detail: string) { await env.DB.prepare("INSERT INTO audit(id,actor,action,target_id,detail,created_at) VALUES(?,?,?,?,?,?)").bind(crypto.randomUUID(), request.headers.get("Cf-Access-Authenticated-User-Email") ?? "device", action, target, detail, Math.floor(Date.now() / 1000)).run(); }
async function limitedBody(request: Request): Promise<string> { const text = await request.text(); if (text.length > 16_384) throw new HttpError(413, "body_too_large"); return text; }
function parseObject(value: string): Record<string, unknown> { let parsed: unknown; try { parsed = JSON.parse(value); } catch { throw new HttpError(400, "invalid_json"); } if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new HttpError(400, "object_required"); return parsed as Record<string, unknown>; }
function text(value: unknown, minimum: number, maximum: number): string { if (typeof value !== "string" || value.length < minimum || value.length > maximum || /[\x00-\x1f<>]/.test(value)) throw new HttpError(400, "invalid_text"); return value; }
function optionalText(value: unknown, maximum: number): string | null { return value === null || value === undefined ? null : text(value, 1, maximum); }
function integer(value: unknown, minimum: number, maximum: number): number { if (!Number.isInteger(value) || (value as number) < minimum || (value as number) > maximum) throw new HttpError(400, "invalid_integer"); return value as number; }
function optionalIsoDate(value: unknown): string | null { if (value === null || value === undefined) return null; const textValue = text(value, 10, 40); if (!Number.isFinite(Date.parse(textValue))) throw new HttpError(400, "invalid_date"); return textValue; }
function constantTime(left: string, right: string): boolean { if (left.length !== right.length) return false; let difference = 0; for (let index = 0; index < left.length; index++) difference |= left.charCodeAt(index) ^ right.charCodeAt(index); return difference === 0; }

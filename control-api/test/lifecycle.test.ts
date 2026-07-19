import { applyD1Migrations, SELF } from "cloudflare:test";
import { env } from "cloudflare:workers";
import { beforeAll, describe, expect, it } from "vitest";
import worker from "../src/index";
import type { Env } from "../src/types";

type Migration = { name: string; queries: string[] };
const bindings = env as unknown as Env & { TEST_MIGRATIONS: Migration[] };
const adminHeaders = {
  "Content-Type": "application/json",
  "Cf-Access-Jwt-Assertion": "isolated-test-assertion",
  "Cf-Access-Authenticated-User-Email": "admin@example.test",
};

const base64Url = (value: ArrayBuffer | Uint8Array) => {
  const bytes = value instanceof Uint8Array ? value : new Uint8Array(value);
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
};

const derInteger = (value: Uint8Array) => {
  let start = 0;
  while (start < value.length - 1 && value[start] === 0) start++;
  let bytes = value.slice(start);
  if ((bytes[0]! & 0x80) !== 0) bytes = new Uint8Array([0, ...bytes]);
  return new Uint8Array([0x02, bytes.length, ...bytes]);
};

const p1363ToDer = (raw: Uint8Array) => {
  const r = derInteger(raw.slice(0, raw.length / 2));
  const s = derInteger(raw.slice(raw.length / 2));
  return new Uint8Array([0x30, r.length + s.length, ...r, ...s]);
};

async function digest(value: string): Promise<string> {
  const hash = new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value)));
  return Array.from(hash, byte => byte.toString(16).padStart(2, "0")).join("");
}

async function signedRequest(
  key: CryptoKey,
  method: "GET" | "POST",
  path: string,
  body = "",
  token?: string,
  nonce = crypto.randomUUID(),
): Promise<Request> {
  const timestamp = String(Math.floor(Date.now() / 1000));
  const payload = `${method}\n${path}\n${timestamp}\n${nonce}\n${await digest(body)}`;
  const raw = new Uint8Array(await crypto.subtle.sign({ name: "ECDSA", hash: "SHA-256" }, key, new TextEncoder().encode(payload)));
  const signature = raw[0] === 0x30 ? raw : p1363ToDer(raw);
  const headers = new Headers({
    "X-Device-Timestamp": timestamp,
    "X-Device-Nonce": nonce,
    "X-Device-Signature": base64Url(signature),
  });
  if (body) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const init: RequestInit = { method, headers };
  if (body) init.body = body;
  return new Request(`https://control.test${path}`, init);
}

describe.sequential("control-plane lifecycle", () => {
  beforeAll(async () => applyD1Migrations(bindings.DB, bindings.TEST_MIGRATIONS));

  it("pairs once, records status, delivers commands once, rejects replay, and revokes deletion", async () => {
    const pairingResponse = await SELF.fetch("https://control.test/v1/admin/pairing-codes", {
      method: "POST", headers: adminHeaders, body: JSON.stringify({ householdAlias: "Isolated Household" }),
    });
    expect(pairingResponse.status).toBe(201);
    const pairing = await pairingResponse.json<{ code: string }>();

    const keys = await crypto.subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign", "verify"]) as CryptoKeyPair;
    const publicKey = base64Url(await crypto.subtle.exportKey("spki", keys.publicKey) as ArrayBuffer);
    const pairBody = JSON.stringify({ code: pairing.code, publicKey, model: "Integration TV", osVersion: "9" });
    const pairedResponse = await SELF.fetch(await signedRequest(keys.privateKey, "POST", "/v1/devices/pair", pairBody));
    expect(pairedResponse.status).toBe(201);
    const paired = await pairedResponse.json<{ deviceId: string; token: string }>();

    const reused = await SELF.fetch(await signedRequest(keys.privateKey, "POST", "/v1/devices/pair", pairBody));
    expect(reused.status).toBe(401);
    expect(await reused.json()).toEqual({ error: "invalid_or_expired_pairing_code" });

    const statusBody = JSON.stringify({
      setupStep: "COMPLETE", setupPhase: "COMPLETE", progressPercent: 100, statusMessage: "Core setup complete", busy: false,
      appVersion: 3, configVersion: "2026.07.2", errorCode: null, debridExpiry: "2026-11-26T21:52:35.000Z",
      manufacturer: "Amazon", product: "sheldonp", apiLevel: 28, architecture: "armeabi-v7a", securityPatch: "2025-10-01",
      freeStorageMb: 2148, totalStorageMb: 5890, totalMemoryMb: 1944, kodiVersion: "21.3", protonVersion: "5.14.0",
      installPermission: true, bootstrapReady: true, automaticSetup: false,
    });
    const status = await SELF.fetch(await signedRequest(keys.privateKey, "POST", `/v1/devices/${paired.deviceId}/status`, statusBody, paired.token));
    expect(status.status).toBe(200);

    const listed = await (await SELF.fetch("https://control.test/v1/admin/devices", { headers: adminHeaders })).json<{ devices: Array<Record<string, unknown>> }>();
    expect(listed.devices).toHaveLength(1);
    expect(listed.devices[0]).toMatchObject({
      householdAlias: "Isolated Household", model: "Integration TV", manufacturer: "Amazon", product: "sheldonp",
      appVersion: 3, configVersion: "2026.07.2", setupStep: "COMPLETE", setupPhase: "COMPLETE", progressPercent: 100,
      statusMessage: "Core setup complete", busy: 0, apiLevel: 28, architecture: "armeabi-v7a", kodiVersion: "21.3",
      protonVersion: "5.14.0", installPermission: 1, bootstrapReady: 1, automaticSetup: 0, errorCode: null,
    });
    expect(listed.devices[0]!.events).toEqual([expect.objectContaining({ setupPhase: "COMPLETE", progressPercent: 100, statusMessage: "Core setup complete" })]);

    const repeatedStatus = await SELF.fetch(await signedRequest(keys.privateKey, "POST", `/v1/devices/${paired.deviceId}/status`, statusBody, paired.token));
    expect(repeatedStatus.status).toBe(200);
    const eventCount = await bindings.DB.prepare("SELECT COUNT(*) AS count FROM device_status_events WHERE device_id=?").bind(paired.deviceId).first<{ count: number }>();
    expect(eventCount?.count).toBe(1);

    const command = await SELF.fetch(`https://control.test/v1/admin/devices/${paired.deviceId}/commands`, {
      method: "POST", headers: adminHeaders, body: JSON.stringify({ kind: "SYNC_CONFIG", payload: { configVersion: "2026.07.2" } }),
    });
    expect(command.status).toBe(201);

    const commandPath = `/v1/devices/${paired.deviceId}/commands`;
    const commandRequest = await signedRequest(keys.privateKey, "GET", commandPath, "", paired.token);
    const delivered = await SELF.fetch(commandRequest.clone());
    expect(delivered.status).toBe(200);
    expect((await delivered.json<{ commands: unknown[] }>()).commands).toHaveLength(1);
    const replayed = await SELF.fetch(commandRequest.clone());
    expect(replayed.status).toBe(409);
    expect(await replayed.json()).toEqual({ error: "replayed_request" });
    const empty = await SELF.fetch(await signedRequest(keys.privateKey, "GET", commandPath, "", paired.token));
    expect((await empty.json<{ commands: unknown[] }>()).commands).toEqual([]);

    const deleted = await SELF.fetch(`https://control.test/v1/admin/devices/${paired.deviceId}`, { method: "DELETE", headers: adminHeaders });
    expect(deleted.status).toBe(204);
    const afterDelete = await SELF.fetch(await signedRequest(keys.privateKey, "POST", `/v1/devices/${paired.deviceId}/status`, statusBody, paired.token));
    expect(afterDelete.status).toBe(401);
    const listedAfterDelete = await (await SELF.fetch("https://control.test/v1/admin/devices", { headers: adminHeaders })).json<{ devices: unknown[] }>();
    expect(listedAfterDelete.devices).toEqual([]);
    expect((await bindings.DB.prepare("SELECT COUNT(*) AS count FROM commands WHERE device_id=?").bind(paired.deviceId).first<{ count: number }>())?.count).toBe(0);
    expect((await bindings.DB.prepare("SELECT COUNT(*) AS count FROM request_nonces WHERE device_id=?").bind(paired.deviceId).first<{ count: number }>())?.count).toBe(0);
    const deleteAgain = await SELF.fetch(`https://control.test/v1/admin/devices/${paired.deviceId}`, { method: "DELETE", headers: adminHeaders });
    expect(deleteAgain.status).toBe(404);
    expect(await deleteAgain.json()).toEqual({ error: "device_not_found" });

    const householdPairing = await SELF.fetch("https://control.test/v1/admin/pairing-codes", {
      method: "POST", headers: adminHeaders, body: JSON.stringify({ householdAlias: "Erase Entire Household" }),
    });
    const householdCode = await householdPairing.json<{ code: string }>();
    const household = await bindings.DB.prepare("SELECT id FROM households WHERE alias=?").bind("Erase Entire Household").first<{ id: string }>();
    expect(household).not.toBeNull();
    const householdDeleted = await SELF.fetch(`https://control.test/v1/admin/households/${household!.id}`, { method: "DELETE", headers: adminHeaders });
    expect(householdDeleted.status).toBe(204);
    expect(await bindings.DB.prepare("SELECT id FROM households WHERE id=?").bind(household!.id).first()).toBeNull();
    const erasedPairBody = JSON.stringify({ code: householdCode.code, publicKey, model: "Erased TV", osVersion: "9" });
    const erasedPair = await SELF.fetch(await signedRequest(keys.privateKey, "POST", "/v1/devices/pair", erasedPairBody));
    expect(erasedPair.status).toBe(401);
  });

  it("scheduled retention removes expired transient and audit records", async () => {
    const now = Math.floor(Date.now() / 1000);
    const householdId = crypto.randomUUID();
    const deviceId = crypto.randomUUID();
    await bindings.DB.batch([
      bindings.DB.prepare("INSERT INTO households(id,alias,created_at) VALUES(?,?,?)").bind(householdId, "Retention Test", now - 1000),
      bindings.DB.prepare("INSERT INTO pairing_codes(code_hash,household_id,expires_at) VALUES(?,?,?)").bind("expired-code", householdId, now - 1),
      bindings.DB.prepare("INSERT INTO devices(id,household_id,public_key_spki,token_hash,model,os_version,created_at,last_seen_at) VALUES(?,?,?,?,?,?,?,?)").bind(deviceId, householdId, "test-key", "test-token", "Retention TV", "9", now - 1000, now - 1000),
      bindings.DB.prepare("INSERT INTO request_nonces(device_id,nonce,expires_at) VALUES(?,?,?)").bind(deviceId, crypto.randomUUID(), now - 1),
      bindings.DB.prepare("INSERT INTO audit(id,actor,action,target_id,detail,created_at) VALUES(?,?,?,?,?,?)").bind(crypto.randomUUID(), "test", "old", householdId, "expired", now - 91 * 86400),
      bindings.DB.prepare("INSERT INTO device_status_events(id,device_id,setup_step,setup_phase,progress_percent,status_message,error_code,created_at) VALUES(?,?,?,?,?,?,?,?)").bind(crypto.randomUUID(), deviceId, "KODI", "KODI_READY", 45, "old", null, now - 91 * 86400),
    ]);
    await worker.scheduled({} as ScheduledController, bindings);
    expect((await bindings.DB.prepare("SELECT COUNT(*) AS count FROM pairing_codes WHERE code_hash='expired-code'").first<{ count: number }>())?.count).toBe(0);
    expect((await bindings.DB.prepare("SELECT COUNT(*) AS count FROM audit WHERE action='old'").first<{ count: number }>())?.count).toBe(0);
    expect((await bindings.DB.prepare("SELECT COUNT(*) AS count FROM request_nonces WHERE device_id=?").bind(deviceId).first<{ count: number }>())?.count).toBe(0);
    expect((await bindings.DB.prepare("SELECT COUNT(*) AS count FROM device_status_events WHERE device_id=?").bind(deviceId).first<{ count: number }>())?.count).toBe(0);
  });
});

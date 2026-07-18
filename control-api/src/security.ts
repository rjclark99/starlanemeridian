const encoder = new TextEncoder();

export function base64Url(bytes: Uint8Array): string {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function decodeBase64Url(value: string): Uint8Array {
  const padded = value.replace(/-/g, "+").replace(/_/g, "/").padEnd(Math.ceil(value.length / 4) * 4, "=");
  const binary = atob(padded);
  return Uint8Array.from(binary, character => character.charCodeAt(0));
}

export async function sha256(value: string | Uint8Array): Promise<string> {
  const input = typeof value === "string" ? encoder.encode(value) : value;
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", toArrayBuffer(input)));
  return Array.from(digest, byte => byte.toString(16).padStart(2, "0")).join("");
}

export function randomToken(bytes = 32): string {
  const value = new Uint8Array(bytes); crypto.getRandomValues(value); return base64Url(value);
}

export async function verifyDeviceSignature(request: Request, body: string, publicKeySpki: string): Promise<{ nonce: string; timestamp: number }> {
  const timestampText = request.headers.get("X-Device-Timestamp") ?? "";
  const nonce = request.headers.get("X-Device-Nonce") ?? "";
  const signature = request.headers.get("X-Device-Signature") ?? "";
  const timestamp = Number(timestampText);
  if (!Number.isInteger(timestamp) || Math.abs(Date.now() / 1000 - timestamp) > 300) throw new HttpError(401, "stale_request");
  if (!/^[0-9a-f-]{36}$/i.test(nonce) || signature.length > 256) throw new HttpError(401, "invalid_signature_headers");
  const path = new URL(request.url).pathname;
  const payload = `${request.method}\n${path}\n${timestampText}\n${nonce}\n${await sha256(body)}`;
  let key: CryptoKey;
  try {
    key = await crypto.subtle.importKey("spki", toArrayBuffer(decodeBase64Url(publicKeySpki)), { name: "ECDSA", namedCurve: "P-256" }, false, ["verify"]);
  } catch { throw new HttpError(401, "invalid_device_key"); }
  // Android returns ASN.1 DER ECDSA. WebCrypto expects IEEE-P1363 in Workers, so convert strictly.
  const rawSignature = derToP1363(decodeBase64Url(signature), 32);
  const valid = await crypto.subtle.verify({ name: "ECDSA", hash: "SHA-256" }, key, toArrayBuffer(rawSignature), toArrayBuffer(encoder.encode(payload)));
  if (!valid) throw new HttpError(401, "invalid_device_signature");
  return { nonce, timestamp };
}

export function derToP1363(der: Uint8Array, width: number): Uint8Array {
  if (der.length < 8 || der[0] !== 0x30) throw new HttpError(401, "invalid_signature_encoding");
  let offset = 1;
  const sequenceLength = readLength(der, offset); offset = sequenceLength.offset;
  if (sequenceLength.length !== der.length - offset || der[offset++] !== 0x02) throw new HttpError(401, "invalid_signature_encoding");
  const rLength = readLength(der, offset); offset = rLength.offset; const r = der.slice(offset, offset + rLength.length); offset += rLength.length;
  if (der[offset++] !== 0x02) throw new HttpError(401, "invalid_signature_encoding");
  const sLength = readLength(der, offset); offset = sLength.offset; const s = der.slice(offset, offset + sLength.length); offset += sLength.length;
  if (offset !== der.length) throw new HttpError(401, "invalid_signature_encoding");
  return concatInteger(r, s, width);
}

function readLength(input: Uint8Array, offset: number): { length: number; offset: number } {
  const first = input[offset++]; if (first === undefined) throw new HttpError(401, "invalid_signature_encoding");
  if (first < 0x80) return { length: first, offset };
  const count = first & 0x7f; if (count < 1 || count > 2 || offset + count > input.length) throw new HttpError(401, "invalid_signature_encoding");
  let length = 0; for (let index = 0; index < count; index++) length = length * 256 + input[offset++]!;
  return { length, offset };
}

function concatInteger(rInput: Uint8Array, sInput: Uint8Array, width: number): Uint8Array {
  const normalize = (value: Uint8Array) => { let start = 0; while (start < value.length - 1 && value[start] === 0) start++; const stripped = value.slice(start); if (stripped.length > width) throw new HttpError(401, "invalid_signature_encoding"); const result = new Uint8Array(width); result.set(stripped, width - stripped.length); return result; };
  const result = new Uint8Array(width * 2); result.set(normalize(rInput)); result.set(normalize(sInput), width); return result;
}

export class HttpError extends Error { constructor(public readonly status: number, public readonly code: string) { super(code); } }

function toArrayBuffer(value: Uint8Array): ArrayBuffer { const copy = new Uint8Array(value.length); copy.set(value); return copy.buffer; }

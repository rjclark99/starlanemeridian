import { describe, expect, it } from "vitest";
import { base64Url, decodeBase64Url, derToP1363 } from "../src/security";
import { validateCommandPayload } from "../src/index";

describe("security helpers", () => {
  it("round trips base64url", () => { const input = new Uint8Array([0, 1, 2, 250, 255]); expect(decodeBase64Url(base64Url(input))).toEqual(input); });
  it("converts a DER signature", () => { const der = new Uint8Array([0x30, 0x06, 0x02, 0x01, 0x01, 0x02, 0x01, 0x02]); const raw = derToP1363(der, 2); expect(Array.from(raw)).toEqual([0, 1, 0, 2]); });
  it("rejects malformed DER", () => { expect(() => derToP1363(new Uint8Array([1, 2, 3]), 32)).toThrow(); });
  it("accepts only empty payloads for active setup commands", () => {
    expect(validateCommandPayload("START_SETUP", {})).toEqual({});
    expect(() => validateCommandPayload("INSTALL_KODI", { url: "https://attacker.invalid/app.apk" })).toThrow("invalid_payload_field");
  });
  it("requires explicit consent for diagnostics", () => {
    expect(() => validateCommandPayload("REQUEST_DIAGNOSTICS", {})).toThrow("diagnostic_consent_required");
    expect(validateCommandPayload("REQUEST_DIAGNOSTICS", { requiresConsent: true })).toEqual({ requiresConsent: true });
  });
});

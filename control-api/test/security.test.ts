import { describe, expect, it } from "vitest";
import { base64Url, decodeBase64Url, derToP1363 } from "../src/security";
import { kodiArtifact, validateCommandPayload } from "../src/index";

describe("security helpers", () => {
  it("redirects only allowlisted Kodi repository artifacts", () => {
    const valid = new Request("https://control.test/v1/public/kodi/skin.starlanemeridian/skin.starlanemeridian-1.0.0.zip.sha256", { method: "HEAD" });
    const redirected = kodiArtifact(valid, new URL(valid.url));
    expect(redirected.status).toBe(307);
    expect(redirected.headers.get("Location")).toBe("https://github.com/rjclark99/starlanemeridian/releases/latest/download/skin.starlanemeridian-1.0.0.zip.sha256");
    const mismatched = new Request("https://control.test/v1/public/kodi/skin.starlanemeridian/repository.kodisetup-1.0.0.zip");
    expect(kodiArtifact(mismatched, new URL(mismatched.url)).status).toBe(404);
    const traversal = new Request("https://control.test/v1/public/kodi/skin.starlanemeridian/%2e%2e%2fmanifest.json");
    expect(kodiArtifact(traversal, new URL(traversal.url)).status).toBe(404);
  });
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
  it("rejects arbitrary fields for every no-payload command", () => {
    for (const kind of ["START_SETUP", "INSTALL_KODI", "INSTALL_PROTON", "PREPARE_BOOTSTRAP", "OPEN_KODI", "BEGIN_REAL_DEBRID_AUTH", "RETRY_CURRENT_STEP"])
      expect(() => validateCommandPayload(kind, { command: "anything" })).toThrow("invalid_payload_field");
  });
  it("allowlists retry steps and authorization providers", () => {
    expect(validateCommandPayload("RETRY_STEP", { step: "KODI" })).toEqual({ step: "KODI" });
    expect(() => validateCommandPayload("RETRY_STEP", { step: "ROOT_SHELL" })).toThrow("invalid_setup_step");
    expect(validateCommandPayload("OPEN_AUTHORIZATION", { provider: "real-debrid" })).toEqual({ provider: "real-debrid" });
    expect(() => validateCommandPayload("OPEN_AUTHORIZATION", { provider: "attacker" })).toThrow("invalid_provider");
  });
});

---
id: subsystem.signed-config-release
kind: subsystem
status: active
verified_at: 2026-07-28
tags: [release, manifest, signing, ci]
authority: [config/manifest.schema.json, config/manifest.json, tools/release.py]
supersedes: []
---

# Signed configuration and release

The JSON Schema constrains stage, stable Kodi package identity, artifacts, repositories,
add-ons, skin, and telemetry. Ed25519 signs canonical JSON; only the public key belongs
in source. Increment configuration/package versions deliberately and sign only after
all hashes are final.

Use focused Python tests, full tooling tests, compile checks, manifest validation, and
public-key verification. Package checksum sidecars must be exact LF bytes. Public
release requires explicit authority, CI, draft assembly, downloaded-byte comparison,
signature verification, route checks, hardware application, and rollback confirmation.

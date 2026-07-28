---
id: decision.trust-boundaries
kind: decision
status: active
verified_at: 2026-07-28
tags: [security, privacy, architecture]
authority: [SECURITY.md]
supersedes: []
---

# Preserve trust boundaries

Secrets remain in Android Keystore, the Windows-local vault, or owner-controlled
offline storage. The cloud stores only allowlisted status and accepts signed requests
and closed-enum commands. The portal remains loopback-only.

Rejected: cloud credential storage, arbitrary commands, remote shell/ADB, registration
or payment automation. Revisit only through explicit security design and owner/legal
approval. Validate schemas, authentication, replay protection, telemetry allowlists,
and deletion behavior.

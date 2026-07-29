---
id: decision.trust-boundaries
kind: decision
status: active
verified_at: 2026-07-29
tags: [security, privacy, architecture]
authority: [SECURITY.md]
supersedes: []
---

# Preserve trust boundaries

Secrets remain in Android Keystore, the Windows-local vault, or owner-controlled
offline storage. The cloud stores only allowlisted status and accepts signed requests
and closed-enum commands. The portal remains loopback-only.

Remote Real-Debrid authorization may relay only the provider's allowlisted
`https://real-debrid.com/device?user_code=...` URL, its matching short-lived user code
and expiry, and the matching closed-enum command ID. The control plane rejects other
hosts, paths, query fields, codes, and commands; access tokens, refresh tokens, client
credentials, and passwords remain on the TV and must never enter status, events,
audit detail, or the portal.

Rejected: cloud credential storage, arbitrary commands, remote shell/ADB, registration
or payment automation. Revisit only through explicit security design and owner/legal
approval. Validate schemas, authentication, replay protection, telemetry allowlists,
and deletion behavior.

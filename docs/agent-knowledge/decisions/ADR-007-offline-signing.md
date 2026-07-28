---
id: decision.offline-signing
kind: decision
status: active
verified_at: 2026-07-28
tags: [release, signing, security]
authority: [.github/workflows/release.yml, docs/OPERATIONS.md]
supersedes: []
---

# Keep manifest signing offline

The trusted owner workstation signs the final canonical manifest. CI receives only the
public key and verifies the signature; the manifest private key is never uploaded.

Rejected: online CI signing. Release automation previously lacked required environment
values, and expanding secret custody adds risk. Revisit only after an explicit
threat-model and owner-approved key-management design.

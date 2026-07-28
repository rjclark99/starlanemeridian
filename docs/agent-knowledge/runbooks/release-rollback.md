---
id: runbook.release-rollback
kind: runbook
status: active
verified_at: 2026-07-28
tags: [release, rollback, signing]
authority: [docs/OPERATIONS.md, docs/AGENT_HANDOFF.md]
supersedes: []
---

# Release and rollback

Require explicit publication authority. Validate source/config, increment versions,
sign the final manifest offline, build reproducibly, hardware-test candidates, commit
and pass CI, then assemble a draft retaining every required rollback asset. Generate
exact LF checksums, download each draft asset, compare bytes, verify signature and
allowlisted routes, then publish only after review.

After publication, restart Kodi to apply and again to confirm/clear recovery state.
On failure preserve evidence, restore the exact prior artifact/profile pair, confirm
version and active skin, and smoke-test. Never promote `test` to `stable` implicitly.

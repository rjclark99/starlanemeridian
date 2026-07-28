---
id: decision.skin-stream-separation
kind: decision
status: active
verified_at: 2026-07-28
tags: [kodi, skin, release]
authority: [docs/CURRENT_STATUS.md, config/manifest.json]
supersedes: []
---

# Separate production and private skins

The Estuary-derived production `skin.starlanemeridian` is built reproducibly and
distributed through the signed manifest. The BINGIE-derived
`skin.starlane.movies` is private experimental work and is not silently promoted.

Rejected: copying private device edits into production. Promotion requires an explicit
design/licensing/resource review, builder implementation, regression coverage,
hardware testing, versioned release, and rollback.

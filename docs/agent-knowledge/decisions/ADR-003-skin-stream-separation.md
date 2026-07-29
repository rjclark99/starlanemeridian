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
`skin.starlane.movies` is an experimental stream and is not silently promoted into
production. On 2026-07-29 the owner approved public distribution of version 2.2.20,
including its GPL-2.0 Titan BINGIE MOD-derived source, bundled resources, declared
Kodi dependencies, and embedded Umbrella routes. The owner then explicitly directed
Bootstrap 1.1.5 and test manifest `2026.07.29` to install and activate it. This does
not implicitly promote the experimental stream to `stable`; production skin 1.2.4
remains packaged as rollback.

Rejected: copying private device edits into production. Promotion requires an explicit
design/licensing/resource review, builder implementation, regression coverage,
hardware testing, versioned release, and rollback.

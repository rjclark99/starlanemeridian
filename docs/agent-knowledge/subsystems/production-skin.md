---
id: subsystem.production-skin
kind: subsystem
status: active
verified_at: 2026-07-28
tags: [kodi, skin, estuary, production]
authority: [tools/skin_builder.py, tools/test_skin_builder.py]
supersedes: []
---

# Production Estuary-derived skin

`tools/skin_builder.py` produces the complete GPL-attributed
`skin.starlanemeridian` package from a reviewed Estuary source archive. It compiles
manifest destinations through closed allowlists and keeps optional search helpers
non-mandatory. Current source builder version is 1.3.0; verify before use.

Make production changes in the builder, not an installed copy. Preserve one visual
focus, overscan margins, consistent D-pad geometry, capped local/PVR widgets, bounded
background loading, and rollback through Bootstrap. Private BINGIE-derived experiments
do not flow into this stream automatically.

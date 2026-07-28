---
id: decision.local-progress
kind: decision
status: active
verified_at: 2026-07-28
tags: [kodi, umbrella, sqlite, performance]
authority: [kodi/skin.starlane.movies/service.py, tools/test_experimental_skin.py]
supersedes: []
---

# Reuse Umbrella local progress

Continue Watching uses Umbrella's existing on-device progress and playback routes.
The skin service performs limited read-only existence queries and gates empty widgets
before directory loading.

Rejected: a duplicate database/helper and post-load removal of empty rows. Preserve
local-only progress ownership, no network/database writes in the polling loop, and
byte-for-byte restoration of synthetic test fixtures.

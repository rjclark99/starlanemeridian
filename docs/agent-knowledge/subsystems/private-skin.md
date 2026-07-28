---
id: subsystem.private-skin
kind: subsystem
status: active
verified_at: 2026-07-28
tags: [kodi, skin, widgets, umbrella, performance]
authority: [kodi/skin.starlane.movies, tools/test_experimental_skin.py]
supersedes: []
---

# Private poster-led skin

`skin.starlane.movies` is a GPL-attributed Titan BINGIE MOD-derived private stream.
The 2.2.17 candidate uses one Home renderer, one bounded vertical grouplist, fixed
371-pixel poster stride, 150 ms scrolling/fades, two-item preload, background artwork,
card-owned focus, and identity-guarded delayed hero/details.

Umbrella owns non-live routes and local progress; The Crew owns Live TV; Mad Titan
owns Sports. Mad Titan Live NetTV and FenLight are excluded. Keep adjacent active-
category rows instantiated and prevent empty local-progress rows before provider load.
Never mix hub renderers, fixed-focus offsets, per-position slide matrices, or view
styles. Validate changed XML/Python, focused tests, generated provider counts, package,
device geometry, and bounded logs.

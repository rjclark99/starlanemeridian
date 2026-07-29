---
id: subsystem.private-skin
kind: subsystem
status: active
verified_at: 2026-07-28
tags: [kodi, skin, widgets, umbrella, performance]
authority: [kodi/skin.starlane.movies, tools/test_experimental_skin.py]
supersedes: []
---

# Experimental poster-led skin

`skin.starlane.movies` is a GPL-attributed Titan BINGIE MOD-derived experimental
stream. Version 2.2.20 is published separately through the owner-approved
`skin-starlane-movies-2.2.20` prerelease. The owner subsequently directed Bootstrap
1.1.5 and test manifest `2026.07.29` to install and activate it; production skin
1.2.4 remains packaged as rollback. It uses one Home renderer, one bounded vertical
grouplist, fixed
371-pixel poster stride, 150 ms scrolling/fades, two-item preload, background artwork,
card-owned focus, and identity-guarded delayed hero/details.

The current provider policy is VOD-only: Umbrella owns discovery, playback, search,
and local progress, with CocoScrapers as its external provider. Live TV, Sports, Mad
Titan, The Crew, and FenLight are excluded. Keep adjacent active-category rows
instantiated and prevent empty local-progress rows before provider load. Never mix
hub renderers, fixed-focus offsets, per-position slide matrices, or view styles.
Validate changed XML/Python, focused tests, generated provider counts, package,
device geometry, and bounded logs.

---
id: research.provider-routes
kind: research
status: active
verified_at: 2026-07-28
tags: [kodi, umbrella, vod]
authority: [tools/test_experimental_skin.py, docs/TECHNICAL_HANDOFF_2026-07-26.md]
supersedes: []
---

# Provider route contracts

Current private-skin policy is VOD-only: Umbrella owns discovery, playback, search, and
local Continue Watching, with CocoScrapers as Umbrella’s external provider. Live TV and
Sports menu sections are absent. Mad Titan, The Crew, and FenLight are excluded.

On the reference device Umbrella has Starlane Movies display metadata and artwork, but
its internal add-on ID and plugin URLs remain the routing contract. Never derive a
route from the branded display name.

Validate exact actions against installed add-on routing before any change. Do not
upgrade providers, alter credentials, or substitute routes during layout work. Refresh
after an explicitly authorized provider/version change.

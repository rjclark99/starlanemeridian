---
id: incident.empty-continue-watching
kind: incident
status: active
verified_at: 2026-07-28
tags: [kodi, umbrella, empty-state, focus]
authority: [kodi/skin.starlane.movies/service.py, tools/test_experimental_skin.py]
supersedes: []
---

# Empty Continue Watching displaced first row

## Summary

Umbrella returned empty progress rows after Home initialization. Removing their
controls asynchronously left All-Time Best metadata working while its poster cards
were invisible until vertical movement.

## Diagnose and prevent

Check the local progress table before provider invocation. Instantiate movie/episode
rows only when limited existence queries match. Test empty and synthetic populated
databases and restore the original bytes.

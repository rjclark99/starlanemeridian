---
id: incident.parallel-hubs
kind: incident
status: active
verified_at: 2026-07-28
tags: [kodi, navigation, renderer]
authority: [tools/test_experimental_skin.py]
supersedes: []
---

# Parallel Home and hub renderers

## Summary

Hover populated Home while Select/Right activated separate hubs, causing inconsistent
first frames, state resets, and mixed layouts.

## Diagnose and prevent

Home-backed categories stay in one renderer. Hover updates category; Select and Right
use one idempotent first-populated-row sequence. Assert no hub activation and no
post-focus global property flush.

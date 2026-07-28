---
id: incident.competing-animations
kind: incident
status: active
verified_at: 2026-07-28
tags: [kodi, animation, clipping]
authority: [docs/TECHNICAL_HANDOFF_2026-07-26.md]
supersedes: []
---

# Competing Home animations

## Summary

Rows clipped, drifted, or accumulated offsets when native list scrolling, a
position-dependent slide matrix, and fixed-focus offsets all changed vertical position.

## Diagnose and prevent

Inspect animation owners before coordinates. The bounded grouplist alone owns vertical
movement. Remove secondary slides/fixed-focus offsets and validate repeated
up/down/reversal cycles with stable row stride.

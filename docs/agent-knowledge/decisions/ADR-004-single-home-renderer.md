---
id: decision.single-home-renderer
kind: decision
status: active
verified_at: 2026-07-28
tags: [kodi, skin, performance, ux]
authority: [tools/test_experimental_skin.py]
supersedes: []
---

# One Home renderer and motion owner

All private-skin Home categories use one renderer. The outer grouplist owns vertical
motion, horizontal lists own horizontal motion, row groups own opacity, cards own focus
borders, and deferred snapshots own hero/details.

Rejected: parallel hubs, fixed-focus overlays, per-position slides, and mixed view
styles. They caused additive offsets, inconsistent entry frames, and control churn.
Revisit only with measured hardware evidence and regression coverage.

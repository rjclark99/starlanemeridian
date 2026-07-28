---
id: decision.compatibility-identifiers
kind: decision
status: active
verified_at: 2026-07-28
tags: [compatibility, branding, migration]
authority: [README.md, docs/AGENT_HANDOFF.md]
supersedes: []
---

# Retain compatibility identifiers

The Starlane Movies user-facing rebrand does not rename the Android package,
production skin ID, bootstrap ID, repository, or established public/control routes.
Those names anchor upgrades and installed clients.

Rejected: cosmetic global renaming, because it creates parallel packages and broken
routes. Revisit only as an explicit migration with upgrade, signing, redirect,
rollback, and device tests.

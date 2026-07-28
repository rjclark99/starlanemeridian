---
id: incident.kodi-repository-layout
kind: incident
status: active
verified_at: 2026-07-28
tags: [kodi, repository, cloudflare]
authority: [control-api/src/index.ts, docs/CURRENT_STATUS.md]
supersedes: []
---

# Flat assets versus Kodi repository paths

## Summary

Kodi expects `/datadir/addon.id/addon.id-version.zip`; flat GitHub Release assets did
not satisfy that layout.

## Diagnose and prevent

Use the control API’s strictly allowlisted public redirect for supported repository
and skin paths. Validate nested URL, package bytes, sidecar, and redirect allowlist.
Do not expose a generic proxy.

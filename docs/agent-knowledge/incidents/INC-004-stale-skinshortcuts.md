---
id: incident.stale-skinshortcuts
kind: incident
status: active
verified_at: 2026-07-28
tags: [kodi, skinshortcuts, cache]
authority: [docs/TECHNICAL_HANDOFF_2026-07-26.md]
supersedes: []
---

# Saved Skin Shortcuts override source

## Summary

Removed FenLight routes and obsolete widget styles returned because profile-persisted
`.DATA.xml`, properties, and hash state regenerated the live include.

## Diagnose and prevent

Search source, saved profile, and generated include separately. Back up the profile,
retire only obsolete route files, remove only the exact hash, rebuild, count routes,
restart, and remove temporary build hooks.

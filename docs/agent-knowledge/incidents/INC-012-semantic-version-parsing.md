---
id: incident.semantic-version-parsing
kind: incident
status: active
verified_at: 2026-07-28
tags: [vendor, versions, monitoring]
authority: [tools/test_vendor_releases.py, docs/CURRENT_STATUS.md]
supersedes: []
---

# Two-part vendor versions

## Summary

The vendor monitor ignored Kodi’s two-part `21.3` version and proposed obsolete
`18.7.2`.

## Diagnose and prevent

Parse supported two- and three-part forms explicitly, compare semantic components, and
retain fixtures for current vendor naming. Vendor monitoring remains review-only and
must never auto-promote.

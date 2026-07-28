---
id: incident.empty-release-secrets
kind: incident
status: active
verified_at: 2026-07-28
tags: [release, github-actions, signing]
authority: [docs/CURRENT_STATUS.md, .github/workflows/release.yml]
supersedes: []
---

# Empty release environment values

## Summary

The automated release environment supplied empty values, including the Android
keystore, and Gradle emitted a misleading `Tag number over 30` error.

## Diagnose and prevent

Verify safe presence—not contents—of every required environment value before
packaging. Keep manifest signing offline and retain the trusted local path until CI
output is proven byte-equivalent.

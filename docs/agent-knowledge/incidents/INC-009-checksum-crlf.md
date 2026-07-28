---
id: incident.checksum-crlf
kind: incident
status: active
verified_at: 2026-07-28
tags: [kodi, release, checksums, windows]
authority: [tools/test_release.py, docs/CURRENT_STATUS.md]
supersedes: []
---

# CRLF checksum sidecars

## Summary

Kodi rejected a correct package checksum because a Windows-generated sidecar contained
CRLF bytes.

## Diagnose and prevent

Compare literal sidecar bytes as well as the digest. Release generation must emit
exact LF-only content and regression-test it. Never “fix” the artifact hash to match a
text-formatting defect.

---
id: incident.cross-platform-zip-metadata
kind: incident
status: active
verified_at: 2026-08-01
tags: [kodi, release, checksums, windows, github-actions]
authority: [tools/release.py, tools/test_release.py, github-actions]
supersedes: []
---

# Cross-platform ZIP metadata changed release hashes

## Summary

Windows and Linux produced different Bootstrap ZIP hashes from the same source because
text line endings, DEFLATE implementation details, path ordering, and ZIP
`create_system` metadata were not all pinned. The release workflow succeeded, but the
installer correctly rejected the public ZIP against the signed manifest.

## Diagnose and prevent

Do not update a signed hash from one host and assume another host reproduces it.
Canonicalize packaged text to LF, sort by POSIX archive name, pin Unix ZIP metadata,
and use stored entries for the small Bootstrap archive. CI must build the real archive
and assert its SHA-256 equals `config/manifest.json` before release publication.

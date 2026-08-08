---
id: incident.cross-platform-zip-metadata
kind: incident
status: active
verified_at: 2026-08-08
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

## 8 August follow-up

Bootstrap had been made portable, but the locked private skin and branded provider
still used DEFLATE output, and the provider packager also preserved host-native text
line endings. Corrective draft run `31270754516` therefore produced valid Linux ZIPs
whose hashes differed from the Windows-built package lock. The draft was not published.

Commit `b3fed5f` uses stored entries for both locked packages, canonicalizes supported
text files to LF, pins archive ordering and Unix metadata, and adds a workflow check
that compares built assets with the package lock before upload. Two independent local
builds matched exactly. Any package whose SHA-256 is part of a signed lock must use a
cross-host byte-reproducible archive format; sidecar agreement alone is insufficient.

The next Linux run, `31271814880`, was stopped by that new gate before upload. Its exact
size delta showed that the private skin also contained `.xsp` smart playlists and an
extensionless `LICENSE` whose CRLF bytes were not yet canonicalized. Provider artwork
also selected Segoe UI on Windows but Pillow's fallback font on Linux. Commit `2843f00`
adds only those missing text classes and switches both artwork generators to the existing
bundled Starlane fonts. The resulting local skin byte count and digest exactly match the
Linux run; the provider and Bootstrap locks were regenerated and manifest `2026.08.40`
was signed. Cross-host proof still requires one fresh Linux draft run.

Run `31272444959` proved the text fix by accepting the skin, but Pillow still emitted
different provider image bytes on Linux. Commit `5a41f22` therefore treats the four
approved Starlane provider images as release inputs, removes runtime provider-art rendering,
and removes the unrelated Android brand-asset generation step from the signed-release job.
This keeps the locked provider hash unchanged while eliminating image-library and font
rasterization from that package's build boundary.

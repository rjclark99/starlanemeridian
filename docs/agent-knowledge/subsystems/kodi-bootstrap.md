---
id: subsystem.kodi-bootstrap
kind: subsystem
status: active
verified_at: 2026-07-28
tags: [kodi, python, bootstrap, repository]
authority: [kodi/repository.kodisetup/addon.xml, kodi/repository.kodisetup/service.py]
supersedes: []
---

# Kodi bootstrap and repository

Kodi Python 3 add-on `repository.kodisetup` verifies the signed manifest, updates
allowlisted repositories/add-ons, applies non-secret settings idempotently, and
activates a skin with recovery to the prior skin or Estuary. It merge-writes only the
supported splash setting and rejects malformed XML.

Preserve pending/previous recovery state and the two-launch apply/confirm lifecycle.
Repository paths must satisfy Kodi’s nested datadir layout. Validate focused Python/XML,
the relevant Kodi suite, package paths/hashes, and physical activation/rollback before
release.

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

Stock Kodi owns the explicit Unknown Sources and Install from ZIP confirmations.
After installation, Bootstrap owns one additional first-run consent dialog. Acceptance
is persisted locally and gates all configuration changes; refusal installs nothing and
re-prompts on the next launch. Real-Debrid remains a separate official device-OAuth
flow in the Android setup app.

The 1.1.10 source candidate deliberately does not call Kodi's modal
`InstallAddon(...)` or `EnableAddon(...)` builtins. Its packaged
`resources/package-lock.json` is covered transitively by the signed manifest's
Bootstrap ZIP hash. After the single consent, Bootstrap verifies every locked URL,
SHA-256, ZIP path/root, add-on ID, and version; extracts the complete dependency
closure in topological order; performs one local add-on scan; and enables packages
through JSON-RPC. Native Android binary packages are ABI-selected. Unknown Sources
and the Bootstrap ZIP installation remain explicit Kodi actions.

Preserve pending/previous recovery state and the two-launch apply/confirm lifecycle.
Repository paths must satisfy Kodi’s nested datadir layout. Validate focused Python/XML,
the relevant Kodi suite, package paths/hashes, and physical activation/rollback before
release.

---
id: decision.trust-boundaries
kind: decision
status: active
verified_at: 2026-08-01
tags: [security, privacy, architecture]
authority: [SECURITY.md]
supersedes: []
---

# Preserve trust boundaries

Secrets remain in Android Keystore, separately maintained owner tooling, or owner-controlled
offline storage. The cloud stores only allowlisted status and accepts signed requests
and closed-enum commands. No owner administration UI or vault belongs in this repository.

Remote Real-Debrid authorization may relay only the provider's allowlisted
`https://real-debrid.com/device?user_code=...` URL, its matching short-lived user code
and expiry, and the matching closed-enum command ID. The control plane rejects other
hosts, paths, query fields, codes, and commands; access tokens, refresh tokens, client
credentials, and passwords remain on the TV and must never enter status, events,
audit detail, or owner administration tooling.

With explicit owner approval on 29 July and 1 August 2026, the Android 9/Fire OS setup
boundary permits two fixed device-local Kodi profile mutations: set
`addons.unknownsources=true` for the fixed compatibility package
`org.xbmc.kodi`. The app must first receive Android's visible runtime storage
permission, preserve every other `guisettings.xml` value, reject unsafe XML, and keep
then atomically install only the signed-manifest-selected, hash-verified
`repository.kodisetup` archive into that package's canonical profile. The archive has
one exact root/ID/version and bounded structure; the transaction refuses ambiguous or
  running Kodi state, preserves conflicting state, journals rollback, revalidates local
  consent immediately before each write, and launches only Kodi after commit. Bootstrap
  retains its own local scoped consent before locked content installation. A proven
  pre-first-launch transaction may create only the canonical missing profile ancestors
  and minimal `guisettings.xml` containing the fixed preference; existing settings are
  always preserved and merged. This is not a
  cloud command and must not expand into shell, ADB, accessibility, arbitrary archives,
URLs, paths, Kodi settings/commands, database edits, or unattended APK installation.
Newer scoped-storage Android versions retain the manual Kodi steps because cross-app
profile access is unavailable.

Rejected: cloud credential storage, arbitrary commands, remote shell/ADB, registration
or payment automation. Revisit only through explicit security design and owner/legal
approval. Validate schemas, authentication, replay protection, telemetry allowlists,
and deletion behavior.

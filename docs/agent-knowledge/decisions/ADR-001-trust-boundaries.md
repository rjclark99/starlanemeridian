---
id: decision.trust-boundaries
kind: decision
status: active
verified_at: 2026-07-29
tags: [security, privacy, architecture]
authority: [SECURITY.md]
supersedes: []
---

# Preserve trust boundaries

Secrets remain in Android Keystore, the Windows-local vault, or owner-controlled
offline storage. The cloud stores only allowlisted status and accepts signed requests
and closed-enum commands. The portal remains loopback-only.

Remote Real-Debrid authorization may relay only the provider's allowlisted
`https://real-debrid.com/device?user_code=...` URL, its matching short-lived user code
and expiry, and the matching closed-enum command ID. The control plane rejects other
hosts, paths, query fields, codes, and commands; access tokens, refresh tokens, client
credentials, and passwords remain on the TV and must never enter status, events,
audit detail, or the portal.

With explicit owner approval on 29 July 2026, the Android 9/Fire OS setup boundary
also permits one device-local Kodi profile mutation: set
`addons.unknownsources=true` for the fixed compatibility package
`org.xbmc.kodi`. The app must first receive Android's visible runtime storage
permission, preserve every other `guisettings.xml` value, reject unsafe XML, and keep
Kodi's Install from ZIP action explicit. This exception is not a cloud command and
must not expand into shell, ADB, accessibility, arbitrary paths, arbitrary Kodi
settings, or unattended APK installation. Newer scoped-storage Android versions
retain the manual Kodi step because cross-app profile access is unavailable.

Rejected: cloud credential storage, arbitrary commands, remote shell/ADB, registration
or payment automation. Revisit only through explicit security design and owner/legal
approval. Validate schemas, authentication, replay protection, telemetry allowlists,
and deletion behavior.

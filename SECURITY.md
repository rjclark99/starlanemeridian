# Security and privacy model

## Trust boundaries

- Release configuration is accepted only when its JSON Schema, Ed25519 signature, stage, minimum-app version, and revocation state validate.
- APKs must match the configured SHA-256, package name, and signing-certificate SHA-256 before installation is offered.
- Cloud commands use a closed enum. No shell, Kodi built-in string, URL, or script is accepted as a command payload.
- On Android 9/Fire OS, after visible storage permission, the setup app may locally
  enable only Kodi's `addons.unknownsources` preference for the fixed
  `org.xbmc.kodi` package. The merge rejects malformed/oversized/entity-bearing XML
  and preserves all other settings. It is not remotely parameterized and grants no
  shell, ADB, accessibility, arbitrary-file, or arbitrary-Kodi-setting capability.
  Android's Install Unknown Apps permission, runtime permission dialog, APK
  confirmation remain explicit. With the owner's explicit clean-install approval on
  1 August 2026, the same one-run local consent may also install only the
  signed-manifest-selected, hash-verified `repository.kodisetup` archive into the
  canonical `org.xbmc.kodi` profile on API 25–28. The transaction must validate one
  exact archive root/add-on ID/version, reject links/traversal/bombs/collisions, stage
  and verify on the same filesystem, preserve conflicting prior state, journal and
  atomically roll back failures, refuse while Kodi is active or state is ambiguous,
  and launch only Kodi after commit. It must accept no caller-controlled ZIP, URL,
  path, package, add-on, setting, or command. Kodi Bootstrap's own scoped consent
  remains explicit before installing its locked content. On a proven cold install it
  may create only the canonical missing profile ancestors and a minimal secure
  `guisettings.xml` containing that one fixed preference; an existing settings file
  always uses the preserving merge path. API 29+ retains Kodi's
  visible Unknown Sources and Install from ZIP steps.
- Each device creates a non-exportable P-256 signing key in Android Keystore. Pairing binds its public key to a single short-lived code.
- Device requests include a timestamp, nonce, body hash, and ECDSA signature. The API rejects stale or replayed nonces.
- Real-Debrid OAuth tokens remain encrypted on the TV device. Only premium-expiry status may be reported.
- Household credentials are never accepted by this client repository or its cloud API.
- Removing a cloud device hard-deletes its status, authentication token hash, request nonces, and pending commands. Deleting a cloud household cascades all of its pairing and device records.
- Pairing codes and request nonces are short-lived; administrator audit metadata is removed after the configured retention window.

## Account and payment boundary

Client software must not submit account-registration forms, solve or bypass human verification, accept provider terms for another person, or store payment-card data. Each provider account remains owned by the household that accepts its terms.

## Reporting

Do not open a public issue containing credentials, tokens, device pairing codes, signing keys, private configuration, or logs with personal data. Rotate the affected key and use a private security advisory.

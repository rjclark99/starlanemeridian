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
  confirmation, and Kodi's Install from ZIP action remain explicit.
- Each device creates a non-exportable P-256 signing key in Android Keystore. Pairing binds its public key to a single short-lived code.
- Device requests include a timestamp, nonce, body hash, and ECDSA signature. The API rejects stale or replayed nonces.
- Real-Debrid OAuth tokens remain encrypted on the TV device. Only premium-expiry status may be reported.
- Household credentials remain inside the Windows-local vault. The cloud API has no credential fields.
- Removing a cloud device hard-deletes its status, authentication token hash, request nonces, and pending commands. Deleting a cloud household cascades all of its pairing and device records.
- Pairing codes and request nonces are short-lived; administrator audit metadata is removed after the configured retention window.

## Account and payment boundary

The portal may generate a suggested username and strong password, record consent, open official provider pages, and track manual completion. It must not submit account-registration forms, solve or bypass human verification, accept provider terms for another person, or store payment-card data. Each provider account remains owned by the household that accepts its terms.

## Reporting

Do not open a public issue containing credentials, tokens, device pairing codes, signing keys, private configuration, or logs with personal data. Rotate the affected key and use a private security advisory.

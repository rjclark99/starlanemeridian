# Security and privacy model

## Trust boundaries

- Release configuration is accepted only when its JSON Schema, Ed25519 signature, stage, minimum-app version, and revocation state validate.
- APKs must match the configured SHA-256, package name, and signing-certificate SHA-256 before installation is offered.
- Cloud commands use a closed enum. No shell, Kodi built-in string, URL, or script is accepted as a command payload.
- Each device creates a non-exportable P-256 signing key in Android Keystore. Pairing binds its public key to a single short-lived code.
- Device requests include a timestamp, nonce, body hash, and ECDSA signature. The API rejects stale or replayed nonces.
- Real-Debrid OAuth tokens remain encrypted on the TV device. Only premium-expiry status may be reported.
- Household credentials remain inside the Windows-local vault. The cloud API has no credential fields.

## Account and payment boundary

The portal may generate a suggested username and strong password, record consent, open official provider pages, and track manual completion. It must not submit account-registration forms, solve or bypass human verification, accept provider terms for another person, or store payment-card data. Each provider account remains owned by the household that accepts its terms.

## Reporting

Do not open a public issue containing credentials, tokens, device pairing codes, signing keys, private configuration, or logs with personal data. Rotate the affected key and use a private security advisory.


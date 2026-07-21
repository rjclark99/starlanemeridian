# Current deployment status

Last verified: 21 July 2026.

## Working deployment

- Public repository: `rjclark99/starlanemeridian`.
- Control plane: `https://control.starlanemeridian.uk` (healthy).
- Windows administration portal: localhost-only with an encrypted local vault.
- Downloader code: `3467018`.
- Test device: Amazon AFTKAUK001, Fire OS / Android 9.
- Kodi 21.3 and Proton VPN are installed.
- Signed setup app 0.2.0 (version code 2) is installed on the reference Fire TV. Setup app 0.3.0 (version code 3) is published and ready for the next physical upgrade pass.
- Kodi Setup Bootstrap 1.0.2 is installed on the reference Fire TV. Bootstrap 1.1.0 and signed configuration `2026.07.3` are published and ready for the next physical skin test.
- Real-Debrid device OAuth completed. Only premium-expiry status is sent to the control plane.

## Verified behavior

- Pairing created the expected household and device record fields.
- A production `SYNC_CONFIG` command was queued, collected by the TV, and reflected in a newer `lastSeenAt` without changing completed status or expiry.
- The Worker rejects arbitrary command payloads and diagnostics without explicit consent.
- The APK verifies hashes, package identity, ABI, and signing certificates before Android's package installer is invoked.
- Fire OS signer fallback, unknown-sources launch, D-pad focus, old-Android storage permission, and duplicate installer-session handling are repaired in setup app 0.2.0.
- Android-required install and permission confirmations remain visible to the TV user.

## Reference-TV profile workflow

`tools/profile_export.py` converts a locally backed-up Kodi home into a review-only
JSON inventory. It copies no files and excludes databases, thumbnails, cache, logs,
history, favourites, sources, credentials, tokens, cookies, account identifiers,
and token-like values.

```powershell
python tools/profile_export.py "backups\kodi\<backup>\.kodi" --output "build\reference-profile-candidate.json"
```

The current saved reference TV produces 18 candidates. The output stays local under
`build/`; every third-party source and retained setting must be reviewed before it
enters the signed manifest.

## Device observability and custom skin

- The control plane accepts a strictly allowlisted, signed status payload and stores a bounded 90-day event timeline. It records model/platform facts, app versions, coarse storage and memory, install permission, bootstrap readiness, current setup phase, progress percentage, and a non-secret status message.
- The password-protected local dashboard shows live presence, installation progress, a step rail, device facts, package versions, readiness checks, Real-Debrid expiry, and the most recent 20 status events. It refreshes every 30 seconds.
- Setup app 0.3.0 sends a heartbeat every 30 seconds while it is active. It never reports credentials, OAuth tokens, payment details, Kodi activity, filenames, or browsing history.
- `skin.starlanemeridian` 1.0.0 is a complete Estuary-derived Kodi 21 skin with an original Starlane Meridian home screen, remote-friendly focus states, five allowlisted home actions, and separately updateable artwork.
- Bootstrap 1.1.0 records the previous skin before activation and restores it (or Estuary) if activation fails.
- Add-on and repository entries intentionally remain schema-driven placeholders until an owner-approved legal allowlist is supplied. The reference profile remains review-only and cannot silently copy a Kodi home directory.

## Published v0.3.0 release

The GitHub release `v0.3.0-test` is promoted as the latest release. The permanent
Downloader URL remains:

`https://github.com/rjclark99/starlanemeridian/releases/latest/download/setup.apk`

Published assets include setup app 0.3.0, Bootstrap 1.1.0, the Starlane Meridian
skin 1.0.0, signed manifest `2026.07.3`, Kodi repository metadata, the Windows
administrator bundle, and SHA-256 checksums. The published manifest was downloaded,
cryptographically verified against `config/manifest.pub`, and matched the local
release byte-for-byte.

The release workflow now verifies an offline-signed manifest and never uploads the
manifest private key to GitHub. Its two manually triggered runs did not publish or
replace any assets. The first run used the superseded online-signing design. The
second reached Android packaging but all six release-environment values were empty,
including `ANDROID_KEYSTORE_BASE64`; Gradle therefore received an empty keystore and
reported `Tag number over 30 is not supported`. The public release was assembled and
signature-verified locally and is unaffected. Before using automated release again,
restore and verify the Android signing and public-configuration secrets in GitHub's
`release` environment.

The scheduled vendor monitor successfully generated candidate data but GitHub blocked
its final pull-request step because the repository does not currently allow Actions to
create or approve pull requests. This has no effect on released configuration. Enable
that repository Actions setting before relying on automatic candidate pull requests.
GitHub also reported Node.js 20 deprecation warnings for older action revisions; these
are maintenance warnings, not product or release failures.

## Tests completed

- Python release/profile/Kodi-manifest/skin tests: 14 passed.
- Control API tests: 9 passed in Cloudflare's isolated Workers/D1 runtime; TypeScript check passed.
- Android unit tests, release compilation, lint-vital, and packaging passed.
- Windows ADB/bootstrap/vault tests passed; portal Release build and self-contained publish passed with no warnings.
- Production Worker deployment and `/health` passed.
- Production Fire TV device record and safe command round-trip passed.
- Physical Fire TV 0.2.0 upgrade regression passed: the setup screen remained on `COMPLETE`, no Android crash was logged, and the cloud record reported app version 2, configuration `2026.07.2`, no error, and the preserved Real-Debrid expiry.
- Physical Kodi bootstrap 1.0.2 regression passed: Kodi loaded the add-on, advanced its idempotent applied-version marker to `2026.07.2`, and logged no bootstrap or repository error.
- Production async authentication errors return controlled JSON 4xx responses.
- Device deletion removes status, nonces, and commands; household deletion cascades all household cloud records. Audit metadata expires under the configured retention policy.
- Production D1 migration `0003_device_observability.sql` was applied without losing the existing device or household records. The production Worker is healthy at `https://control.starlanemeridian.uk/health`.
- GitHub CI passed for both the observability/skin implementation and the offline-manifest verification change.

## Outstanding physical checks

The reference Fire TV has not yet been upgraded from setup app 0.2.0 to 0.3.0 and has
not physically loaded `skin.starlanemeridian` 1.0.0. The TV is available, but the
owner asked on 21 July to hold this installation. This does not affect the published
artifacts or cloud migration.

An Android TV/Google TV hardware pass remains outstanding because no such device is
currently available. Fire TV coverage does not substitute for that compatibility test.

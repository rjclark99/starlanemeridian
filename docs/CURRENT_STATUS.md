# Current deployment status

Last verified: 22 July 2026.

## Working deployment

- Public repository: `rjclark99/starlanemeridian`.
- Control plane: `https://control.starlanemeridian.uk` (healthy).
- Windows administration portal: localhost-only with an encrypted local vault.
- Downloader code: `3467018`.
- Test device: Amazon AFTKAUK001, Fire OS / Android 9.
- Kodi 21.3 and Proton VPN are installed.
- Signed setup app 0.3.0 (version code 3) is installed on the reference Fire TV; the in-place upgrade preserved pairing and account status.
- Kodi Setup Bootstrap 1.1.3, signed configuration `2026.07.11`, and `skin.starlanemeridian` 1.2.4 are installed and active on the reference Fire TV.
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
- `skin.starlanemeridian` 1.2.4 is a complete Estuary-derived Kodi 21 skin with an original Meridian startup transition, cinematic hero region, six ordered content destinations, two-row local/PVR widgets, Family/Animation smart playlists, white left-rail text, a five-item quick-access rail with guarded edge clearances, a branded platform-aware power dialog, a lightweight now-playing ribbon, and separately updateable artwork. Every selectable left-rail row uses the same 28-pixel label scale, 28-pixel inset, and 306-by-60-pixel focus surface. The main-list selection paints its focus surface only while that list owns focus, preventing simultaneous highlights when Quick Access or content controls are active.
- Home order is Home, Search, TV Shows, Movies, Live TV, then Kids & Family. TMDb Helper and Global Search are optional search adapters; the home screen has no helper-service dependency, automatic trailers, or remote widget requirement.
- Bootstrap 1.1.3 records the previous skin before activation and restores it (or Estuary) if activation fails. It also merge-writes only Kodi's supported `<splash>false</splash>` advanced setting, preserving every other advanced setting and refusing malformed files. A graceful restart confirmed the new skin persisted and cleared both recovery markers.
- Add-on and repository entries intentionally remain schema-driven placeholders until an owner-approved legal allowlist is supplied. The reference profile remains review-only and cannot silently copy a Kodi home directory.

## Published v0.3.8 test release

The GitHub release `v0.3.8-test` is promoted as the latest release. The permanent
Downloader URL remains:

`https://github.com/rjclark99/starlanemeridian/releases/latest/download/setup.apk`

Published assets include the unchanged setup app 0.3.0 and Windows administrator
bundle, Bootstrap 1.1.3, Starlane Meridian skins 1.0.0 through 1.2.3 (rollback) plus 1.2.4,
signed manifest `2026.07.11`, Kodi repository metadata, per-package
SHA-256 sidecars, and SHA-256 checksums. The published manifest was downloaded,
cryptographically verified against `config/manifest.pub`, and matched the local
release byte-for-byte.

All 22 draft assets were downloaded back through GitHub's authenticated asset API
and matched their local SHA-256 values before publication. After promotion, the
permanent setup, manifest, Bootstrap 1.1.3, skin 1.2.4, and Cloudflare skin-route
URLs all returned HTTP 200. The public manifest verified against the offline public
key and matched the local release byte-for-byte. CI run `29888046398` passed for
commit `8b0e4b2`.

Kodi's repository layout requires `/datadir/addon.id/addon.id-version.zip`. GitHub
Release assets are flat, so the production Worker now exposes a strictly allowlisted
public redirect for only `repository.kodisetup` and `skin.starlanemeridian` versioned
ZIP/hash paths. Physical testing found and corrected Windows CRLF in package hash
sidecars; release generation now writes exact LF-only bytes and tests that contract.

The release workflow now verifies an offline-signed manifest and never uploads the
manifest private key to GitHub. Its two manually triggered runs did not publish or
replace any assets. The first run used the superseded online-signing design. The
second reached Android packaging but all six release-environment values were empty,
including `ANDROID_KEYSTORE_BASE64`; Gradle therefore received an empty keystore and
reported `Tag number over 30 is not supported`. The public release was assembled and
signature-verified locally and is unaffected. Before using automated release again,
restore and verify the Android signing and public-configuration secrets in GitHub's
`release` environment.

GitHub Actions pull-request permission was enabled on 21 July. The vendor monitor was
rerun successfully and opened review-only PR #1. Review caught a parser defect that
ignored Kodi's two-part `21.3` version and initially proposed `18.7.2`; commit
`23f374f` corrected the parser and added regression tests. A second successful monitor
run updated PR #1 to Kodi 21.3 for ARM32/ARM64 and Proton VPN 5.19.43.0. Independent
verification then matched both Kodi APKs to Kodi's official checksum sidecars and
pinned signer, and matched Proton's official GitHub digest, package identity, API/ABI
metadata, and signing certificate to the Proton version installed on the reference TV.
PR #1 changed only `config/vendor-candidates.json` and was squash-merged as `86abb5c`;
it did not modify the signed manifest or promote an artifact. All four PR and post-merge
CI jobs passed. GitHub still reports Node.js 20 deprecation warnings for older action
revisions; these are maintenance warnings, not product or release failures.

## Tests completed

- Python release/profile/Kodi-settings/Kodi-manifest/skin/vendor-monitor tests: 29 passed, including expanded menu-order, XML, typography-width, startup, provider-allowlist, performance-bound, search-fallback, single-focus ownership, utility-rail, power-dialog, safe advanced-settings merge, and semantic-artifact-selection coverage.
- Control API tests: 10 passed in Cloudflare's isolated Workers/D1 runtime; TypeScript check passed.
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
- GitHub CI passed all four jobs for vendor-monitor parser fix `23f374f`; corrected vendor-monitor run `29866492916` also passed.
- Physical Fire TV in-place upgrade from setup app 0.2.0 to 0.3.0 passed with the original first-install timestamp, signing identity, pairing, and Real-Debrid expiry preserved.
- Expanded device telemetry passed on production: Amazon/AFTKAUK001 identity, Fire OS/API/security patch, ARM ABI, storage/RAM, Kodi/Proton versions, install permission, Bootstrap readiness, progress, and bounded event history all registered without secrets.
- Remote `SYNC_CONFIG` and `PREPARE_BOOTSTRAP` commands passed. The TV exported Bootstrap 1.1.2 with SHA-256 `63a45209194465114b011a50f68b90a9f009029e25a65cb79243e6d084d8b340`, exactly matching the signed manifest.
- Physical Bootstrap/skin installation passed after two contained defects were discovered and fixed: Kodi rejected empty internal string defaults in 1.1.0, and the first repository package route/hash sidecar was incompatible with Kodi's layout/literal hash parsing. Estuary remained active during both failures.
- `skin.starlanemeridian` 1.0.0 installed from the public repository, activated, survived a graceful Kodi restart, and Bootstrap logged confirmation before clearing its pending/previous recovery values.
- Skin 1.1.0 was then hot-deployed as a skin-only physical regression. Kodi loaded the new version without XML/skin errors; Home opens first; all six destinations remain visible through D-pad traversal; Kids & Family, Settings, and Search fallback text fit without clipping; and the branded two-second startup transition was captured after Kodi's native splash. The original installed skin was backed up under the ignored `build/device-backups` area before deployment.
- After public release, Bootstrap fetched and verified manifest `2026.07.6`, applied it on the reference TV, retained skin 1.1.0, and advanced its idempotent applied-version marker. A second Kodi start confirmed the skin and cleared both pending/previous rollback markers; the final log contains no Bootstrap or skin error.
- Skin 1.2.0 was built twice byte-for-byte identically and hot-deployed to the reference Fire TV. Home, Settings, Power, and the branded power dialog were captured at 1920×1080; white rail labels and all focus surfaces remained inside their padded bounds. Kodi logged no skin/XML error.
- Bootstrap 1.1.3 created `<splash>false</splash>` on the device, and timed restart captures showed black Android loading frames followed directly by Meridian's branded startup window with no Kodi core splash. The published Bootstrap then fetched and verified manifest `2026.07.7`, advanced its applied-version marker, confirmed skin 1.2.0 after restart, and cleared both recovery markers without an error.
- Skin 1.2.1 corrected the remaining quick-access surface issue found on hardware. Its controls are 274×48 pixels with 32-pixel pane margins and 10-pixel vertical gaps; idle controls use Kodi's native empty texture, so only the focused row paints a background. Favourites, Settings, and Power focus captures passed at 1920×1080. Bootstrap then applied public manifest `2026.07.8` and confirmed 1.2.1 without an error.
- Skin 1.2.2 corrected the final Power-row collision with the pane's rounded bottom mask. The pane now leaves 38 pixels beneath Power, and a regression assertion enforces at least 32 pixels. A new 1920×1080 Power-focus capture passed on the Fire TV; public manifest `2026.07.9` then applied and cleared both recovery markers without an error.
- Skin 1.2.3 unified the main navigation and Quick Access rows at 28-pixel text, a 28-pixel left inset, and identical 306-by-60-pixel focus surfaces. A physical Power-focus capture confirmed matching geometry and 32 pixels of protected space below the row with no Kodi skin/XML error. All 20 release assets were byte-verified before publication; the Fire TV then fetched signed manifest `2026.07.10`, retained skin 1.2.3, and cleared both recovery markers.
- Skin 1.2.4 corrected Kodi's persistent list-selection rendering so only the control that actually owns focus appears highlighted. Physical Favourites and Power captures each showed exactly one focus surface while the prior main category remained readable in white. Kodi logged no error; all 22 release assets matched after download; signed manifest `2026.07.11` applied and both recovery markers cleared.
- The setup app and production dashboard record now finish at `COMPLETE`, phase `COMPLETE`, 100%, app version 3, configuration `2026.07.5`, Kodi 21.3, Proton VPN 5.5.68.0, Bootstrap ready, and no error. The event timeline records download, verification, Bootstrap-ready, account-link, and completion transitions.
- CI passed for Bootstrap recovery commit `0b7b006`, artifact routing commit `bbe3f75`, and exact-sidecar commit `7dd4de5`.

## Outstanding physical checks

The reference Fire TV skin regression is complete for an empty local library. A later
content-populated pass should validate real poster/fanart crops, two-line long-title
wrapping, PVR channel artwork, and optional TMDb Helper search results. Those checks do
not block the navigation, startup, packaging, or empty-state behavior verified here.

An Android TV/Google TV hardware pass remains outstanding because no such device is
currently available. Fire TV coverage does not substitute for that compatibility test.

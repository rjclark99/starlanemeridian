# Current deployment status

Last verified: 19 July 2026.

## Working deployment

- Public repository: `rjclark99/starlanemeridian`.
- Control plane: `https://control.starlanemeridian.uk` (healthy).
- Windows administration portal: localhost-only with an encrypted local vault.
- Downloader code: `3467018`.
- Test device: Amazon AFTKAUK001, Fire OS / Android 9.
- Kodi 21.3 and Proton VPN are installed.
- Kodi Setup Bootstrap 1.0.1 applied configuration `2026.07.1`; release 1.0.2 and config `2026.07.2` are prepared for publication.
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

## Next phase: custom skin

The current schema-v1 manifest points to Kodi's built-in `skin.estuary`, preserving
compatibility with already-installed setup app 0.1.0. The next phase will:

1. Choose the legal add-on/repository allowlist from the reference inventory.
2. Define home menus, submenus, widgets, actions, and artwork.
3. Compile those choices into `skin.kodisetup`.
4. Test skin failure recovery and a route back to Estuary.
5. Enable the skin only after its package is present in repository metadata.

## Tests completed

- Python release/profile/Kodi-manifest tests: 10 passed.
- Control API tests: 7 passed; TypeScript check passed.
- Android unit tests, release compilation, lint-vital, and packaging passed.
- Windows portal Release build and self-contained publish passed with no warnings.
- Production Worker deployment and `/health` passed.
- Production Fire TV device record and safe command round-trip passed.

An Android TV/Google TV hardware pass remains outstanding because no such device is
currently available. Fire TV coverage does not substitute for that compatibility test.

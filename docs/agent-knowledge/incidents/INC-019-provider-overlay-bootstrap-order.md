---
id: incident.provider-overlay-bootstrap-order
kind: incident
status: active
verified_at: 2026-07-29
tags: [kodi, bootstrap, umbrella, branding, widgets, skinshortcuts]
authority: [reference-device Kodi log and add-on inspection, tools/build_kodi_branding_overlays.py, kodi/repository.kodisetup/service.py]
supersedes: []
---

# Provider overlay and Bootstrap ordering regression

## Symptom

After automated installation, user-facing Umbrella branding returned and Home widgets
repeatedly failed to populate. The generated Skin Shortcuts include still contained the
expected Umbrella routes, so stale saved shortcuts were not the primary cause.

## Root cause

The locked package and automated release path installed the exact upstream Umbrella
6.7.81 archive. The Starlane overlay builder was not part of that path. On first launch,
Umbrella also opened its automatic changelog over Home and performed a long initial
account/provider sync while Bootstrap activated the skin immediately after a single
asynchronous add-on rescan.

The repository metadata checksum route returned 404 because only nested add-on
artifact routes were allowlisted.

## Fix and prevention

- Build the branded provider deterministically from the exact SHA-256-locked upstream
  archive. Revision 6.7.81.2 also removes Umbrella's repository-version probe because
  package-lock management intentionally installs neither upstream repository.
- Package and lock the branded artifact; keep upstream repositories disabled so they
  cannot replace it automatically.
- Disable Umbrella's internal add-on update check and suppress only its automatic
  first-run changelog; preserve the manual changelog action and internal identifiers.
- Park an active Starlane Home on Estuary during provider replacement. Wait for every
  exact locked package version, enable the provider before opening its settings API,
  write settings, wait for readiness, then activate the skin and explicitly regenerate
  Skin Shortcuts before one reload.
- Keep artifact and metadata redirects exact-version allowlists.

Do not change Home geometry when generated shortcut routes are correct and the failure
coincides with provider startup or modal UI.

## Validation

Focused regressions cover archive hash/root/path validation, reproducible packaging,
automatic-versus-manual changelog behavior, exact add-on registration, configuration
ordering, Skin Shortcuts generation ordering, and Control API route allowlisting.

The owner-authorized 1.1.11/6.7.81.1 candidate was published as `v0.5.4-test` and its
allowlisted routes deployed. The first device pass then exposed the hardware findings
below; 1.1.12/6.7.81.2 is the corrected signed successor and remains unpublished and
undeployed pending coordination.

Local candidate hashes:

- `repository.kodisetup-1.1.11.zip`:
  `97629ea3ca9fcca446faa3b7a7ed62c2c1795e8a0c5db0b7a8add5aea98fbfb1`
- `plugin.video.umbrella-6.7.81.1.zip`:
  `dc4e9f8c295797cb14740be85a1de380e0912861fc455d76ceddc6af4707c176`

## Hardware finding

The first authorized 1.1.11 device pass exposed a disabled-add-on registration
deadlock. Kodi had registered branded provider 6.7.81.1 in `Addons33.db`, but
`xbmcaddon.Addon(id)` rejects disabled add-ons. The exact-version poll therefore
reported the registered provider as missing, left it disabled, and never reached the
readiness marker.

Bootstrap 1.1.12 queries `Addons.GetAddonDetails` over Kodi JSON-RPC instead. That API
reports the registered version independently of enabled state. Hardware also proved
that Umbrella's settings API rejects the disabled add-on, so Bootstrap enables it
before writing settings and keeps Home parked until readiness. Regression coverage
checks exact-version detection while disabled and enable-before-settings ordering.

The next device pass exposed a separate provider startup exception. Umbrella treats
any version string longer than six characters as a test build and queried
`repository.umbrellakodi`; Starlane's four-part branded version therefore entered that
branch even though upstream repositories are intentionally absent. Provider 6.7.81.2
replaces the repository report with `Starlane package lock / managed`. A direct,
bounded Fire TV overlay registered 6.7.81.2, started and synchronized the provider,
confirmed the Starlane skin, and produced no `repository.umbrellakodi`, unknown-add-on,
exception, or error match in the new Kodi log.

Corrected local candidate hashes:

- `repository.kodisetup-1.1.12.zip`:
  `fc33f0d66e5467666f55e9153a77a3a033956a73e9863c4465efbc8567152f5f`
- `plugin.video.umbrella-6.7.81.2.zip`:
  `3ff6402f0d4427b7ec0fa6d28bb235d5f10a4b5bc9515021aa1c3cf3ccc65810`

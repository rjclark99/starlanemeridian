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

- Build 6.7.81.1 deterministically from the exact SHA-256-locked upstream archive.
- Package and lock the branded artifact; keep upstream repositories disabled so they
  cannot replace it automatically.
- Disable Umbrella's internal add-on update check and suppress only its automatic
  first-run changelog; preserve the manual changelog action and internal identifiers.
- Wait for every exact locked package version before configuration, write provider
  settings before enabling it, then activate the skin and explicitly regenerate Skin
  Shortcuts before one reload.
- Keep artifact and metadata redirects exact-version allowlists.

Do not change Home geometry when generated shortcut routes are correct and the failure
coincides with provider startup or modal UI.

## Validation

Focused regressions cover archive hash/root/path validation, reproducible packaging,
automatic-versus-manual changelog behavior, exact add-on registration, configuration
ordering, Skin Shortcuts generation ordering, and Control API route allowlisting.

The 1.1.11/6.7.81.1 source candidate remains unsigned and undeployed until separately
authorized release signing, publication, control-plane deployment, and clean-profile
device acceptance are completed.

Local candidate hashes:

- `repository.kodisetup-1.1.11.zip`:
  `97629ea3ca9fcca446faa3b7a7ed62c2c1795e8a0c5db0b7a8add5aea98fbfb1`
- `plugin.video.umbrella-6.7.81.1.zip`:
  `dc4e9f8c295797cb14740be85a1de380e0912861fc455d76ceddc6af4707c176`

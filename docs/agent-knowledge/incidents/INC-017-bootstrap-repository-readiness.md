---
id: incident.bootstrap-repository-readiness
kind: incident
status: active
verified_at: 2026-07-29
tags: [kodi, bootstrap, repository, umbrella, dependencies]
authority: [preserved Kodi log, kodi/repository.kodisetup/service.py, config/manifest.json]
supersedes: []
---

# Bootstrap repository readiness and modal-install failure

## Symptom

A clean Kodi bootstrap reported that `skin.starlane.movies` could not find
`script.bingie.helper`; after the skin was installed manually, Home repeatedly logged
that `plugin.video.umbrella` could not be found. A later Bootstrap 1.1.9 candidate
presented the intended Starlane approval once, but Kodi then presented a separate
confirmation for every dependency.

## Root cause

The bootstrap issued one repository refresh and immediately installed the skin even
though Kodi refreshes repository metadata in a background job. The signed manifest's
add-on list was also empty, so no code path attempted to install Umbrella.

Umbrella's official repository ZIP adds a compatibility detail: its archive folder is
`repository.umbrellaplug.github.io`, while its declared Kodi add-on ID is
`repository.umbrella`.

Kodi 21.3's `InstallAddon(id)` builtin unconditionally invokes the modal installer
with a confirmation prompt. The Python builtin exposes no silent flag; wrapping
multiple calls in a prior application dialog therefore cannot provide one-shot
authorization.

## Fix and prevention

Bootstrap 1.1.10 removes all `InstallAddon(...)` and `EnableAddon(...)` calls. After
one local Starlane consent, it directly downloads a transitively signed package lock,
verifies the URL host, SHA-256, ZIP root, path safety, add-on ID, and exact version,
extracts packages in dependency order, asks Kodi to rescan once, and enables them
through `Addons.SetAddonEnabled` JSON-RPC. The lock contains 38 packages and separate
ARMv7/ARM64 variants for `inputstream.adaptive`; all 39 declared archives were
downloaded and hash-verified, and their required `addon.xml` imports form a complete
topological closure.

Manifest `2026.07.31` explicitly allowlists
BINGIE Helper, the pinned Umbrella and CocoScrapers repositories, required Umbrella
and CocoScrapers add-ons, and the three non-secret Umbrella external-provider settings.
The bootstrap accepts one safe ZIP root and still verifies the add-on ID declared
inside `addon.xml`, avoiding a new manifest field and retaining compatibility with the
existing Android app.

The candidate retains the one-time post-install Bootstrap consent gate. It cannot and
does not bypass stock Kodi's Unknown Sources warning. Declining occurs before splash,
repository, add-on, settings, or skin mutation. Acceptance is local and persistent;
successful installation offers the existing Android official Real-Debrid device flow.

Regression coverage is in `tools/test_kodi_bootstrap.py`,
`tools/test_kodi_manifest.py`, and Android `ManifestContractTest`.

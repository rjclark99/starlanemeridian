---
id: incident.android-kodi-profile-bootstrap
kind: incident
status: active
verified_at: 2026-07-29
tags: [android, kodi, bootstrap, fire-tv, xml]
authority: [device test, android-app/app/src/main/java/app/kodisetup/tv/install/KodiProfileConfigurator.kt]
supersedes: []
---

# Android Kodi-profile Bootstrap preparation

## Symptom

The first signed 0.5.2 device candidate stopped before enabling Kodi Unknown Sources
with `This parser does not support specification "Unknown" version "0.0"`. After an
in-place app restart in offline mode, Prepare Bootstrap could also appear inert.

## Root cause

Fire OS's Android 9 XML implementation rejects some otherwise standard
`DocumentBuilderFactory` hardening feature calls. The existing ViewModel restored the
saved workflow step after process restart but reloaded the signed manifest only for a
paired device, leaving an offline resumed action without its manifest.

## Fix and prevention

XML feature flags are best-effort on Android while independent size, document-type,
entity, root, duplicate-setting, package-ID, and fixed-setting checks remain
mandatory. Non-Welcome workflows reload the signed configuration whether paired or
offline. Unit coverage verifies creation, merge preservation, idempotence, fixed
package identity, malformed XML rejection, and entity-bearing document rejection.

A physical Android 9 test set the real Kodi preference false, ran the signed app's
normal Bootstrap preparation, observed true, launched Kodi, and observed true again.
Do not generalize this into arbitrary profile edits or attempt it on scoped-storage
Android versions.

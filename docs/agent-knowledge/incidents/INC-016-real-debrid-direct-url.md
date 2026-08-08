---
id: incident.real-debrid-direct-url
kind: incident
status: active
verified_at: 2026-07-29
tags: [android, real-debrid, oauth, security]
authority: [official Real-Debrid device-code response, android-app/app/src/main/java/app/kodisetup/tv/net/RealDebridAuthorization.kt]
supersedes: []
---

# Real-Debrid direct URL exceeded the relay allowlist

Symptom: setup app 0.5.0 reported `Real-Debrid returned an unexpected direct
authorization URL` before presenting a remote authorization link.

Cause: the official device-code response retained `https://real-debrid.com/device`
as its verification URL but supplied an optional direct URL on `/authorize` with
provider-specific identifiers. The app preferred that broader URL and then correctly
rejected it against the cloud relay allowlist.

Fix: ignore the optional direct URL. Strictly validate the ordinary verification URL
and device-code shape, then construct only
`https://real-debrid.com/device?user_code=...`. Do not broaden the Worker or owner tool
allowlist and never relay the direct URL's identifiers.

Regression: `RealDebridAuthorizationTest` covers the current broader direct response,
unexpected verification hosts, and query-injection device codes.

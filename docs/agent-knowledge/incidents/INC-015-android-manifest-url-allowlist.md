---
id: incident.android-manifest-url-allowlist
kind: incident
status: active
verified_at: 2026-07-29
tags: [android, manifest, release, github]
authority: [android-app/app/src/main/java/app/kodisetup/tv/security/ManifestSecurity.kt, config/manifest.json]
supersedes: []
---

# Android manifest URL allowlist mismatch

Symptom: setup app 0.5.0 displayed `Failed requirement` and `Using no unverified
configuration` after manifest `2026.07.29` became public.

Cause: the signed manifest used a commit-pinned `raw.githubusercontent.com` dependency
URL while Android's verifier required repository URLs to start with
`https://github.com/`. The no-message Kotlin `require` obscured the failed field.

Fix: use GitHub's commit-pinned `/raw/<commit>/...` URL form. Verify the downloaded
bytes against the existing approved SHA-256 before signing a new config version.

Regression: `ManifestContractTest.signedManifestRepositoryUrlsMatchAndroidAllowlist`
checks every signed-manifest repository URL against the Android verifier's accepted
prefix.

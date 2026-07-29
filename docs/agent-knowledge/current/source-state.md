---
id: current.source-state
kind: current
status: active
verified_at: 2026-07-29
tags: [git, source, versions]
authority: [git, config/manifest.json]
supersedes: []
---

# Repository source state

Commit `8af0f38` on `main` and `origin/main` contains private skin 2.2.20, the VOD-only
provider policy, and command-correlated remote Real-Debrid device authorization
across the Android app, control API, and local administration portal. Production
deployment evidence is recorded separately in `current.deployed-state`; public
release and signed-manifest state remain separate.

The working tree contains an uncommitted Bootstrap 1.1.10 and manifest `2026.07.31`
test candidate. Stock Kodi retains its native Unknown Sources confirmation; on the
first Bootstrap service launch, a separate one-time modal approval gates every
configuration change and authorizes the exact signed-manifest package. The candidate
installs a 38-package, hash-locked, complete transitive closure containing the pinned
Umbrella/CocoScrapers stack, private-skin dependencies, and private skin. It has no
Kodi modal `InstallAddon`/`EnableAddon` calls: packages are verified, extracted in
dependency order, rescanned once, and enabled through JSON-RPC after the single local
consent. All 39 downloads, including both adaptive-inputstream ABIs, match their
declared hashes and their required dependencies form a complete topological closure.
After success it offers the Android official Real-Debrid device flow. Declining
changes no configuration and prompts again next launch.

Verified source candidates: Android app 0.5.1/code 6, production skin builder 1.3.0,
Bootstrap 1.1.10, private skin 2.2.20, and manifest `2026.07.31` at `test`
stage. Inspect status and exact manifests again at task start.

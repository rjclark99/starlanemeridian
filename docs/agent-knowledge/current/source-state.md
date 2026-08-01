---
id: current.source-state
kind: current
status: active
verified_at: 2026-08-01
tags: [git, source, versions]
authority: [git, config/manifest.json]
supersedes: []
---

# Repository source state

`main` and `origin/main` are at `3c99980`. The source contains Android setup
0.5.3/code 8, Bootstrap 1.1.13, production skin 1.3.0, private skin 2.2.20,
branded provider 6.7.81.2, and signed test manifest `2026.07.37`. Commit `0609e30`
links command-correlated remote Real-Debrid authorization to the local Kodi provider;
the token remains on the television. Commits `c8ae9f1`, `0c536ce`, and `3c99980`
make Kodi archives portable across Windows and Linux and add a CI assertion that the
generated Bootstrap archive equals the signed-manifest digest. Public-release and
production-service evidence remain recorded separately.

On Android 9/Fire OS, Android setup 0.5.3/code 8 locally enables Kodi's single required
`addons.unknownsources` preference during Bootstrap preparation after visible storage
permission; newer scoped-storage Android versions retain the manual step. Kodi's
Install from ZIP confirmation remains explicit. On the
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

Bootstrap now parks an active Starlane skin,
detects disabled installed versions through JSON-RPC, and enables the provider before
settings access. The deterministic overlay removes its incompatible upstream
repository-version probe. Artifact hashes and device evidence are recorded in
`incident.provider-overlay-bootstrap-order`.

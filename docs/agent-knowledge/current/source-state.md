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

Local `main`, `origin/main`, and `origin/codex/kodi-first-run-authorisation` are at
`dfa1ea7`, which layers Android Unknown Sources automation above provider-readiness
commit `10439cb`. The baseline contains private skin 2.2.20, the VOD-only provider
policy, and command-correlated remote Real-Debrid device authorization across the
Android app, control API, and local administration portal. The branch advances the
checked-in source through signed test manifest `2026.07.32`. The coordinated
integration candidate is Bootstrap 1.1.12, branded provider 6.7.81.2, and signed test
manifest `2026.07.33`; it is not yet public.
Production deployment evidence is recorded separately in `current.deployed-state`;
public release and signed-manifest state remain separate.

The same integration candidate contains Android setup 0.5.2/code 7. On Android 9/Fire
OS it locally enables Kodi's single required
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

Verified source candidates: Android app 0.5.2/code 7, production skin builder 1.3.0,
Bootstrap 1.1.12, private skin 2.2.20, branded provider 6.7.81.2, and signed manifest
`2026.07.33` at `test` stage. Bootstrap now parks an active Starlane skin,
detects disabled installed versions through JSON-RPC, and enables the provider before
settings access. The deterministic overlay removes its incompatible upstream
repository-version probe. Artifact hashes and device evidence are recorded in
`incident.provider-overlay-bootstrap-order`.

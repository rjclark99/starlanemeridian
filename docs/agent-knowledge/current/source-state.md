---
id: current.source-state
kind: current
status: active
verified_at: 2026-08-08
tags: [git, source, versions]
authority: [git, config/manifest.json]
supersedes: []
---

# Repository source state

Read-only inspection on 1 August 2026 found a clean `main` and `origin/main` at
`cefca90`. The source contains Android setup
0.5.3/code 8, Bootstrap 1.1.13, production skin 1.3.0, private skin 2.2.20,
branded provider 6.7.81.2, and signed test manifest `2026.07.37`. Commit `0609e30`
links command-correlated remote Real-Debrid authorization to the local Kodi provider;
the token remains on the television. Commits `c8ae9f1`, `0c536ce`, and `3c99980`
make Kodi archives portable across Windows and Linux and add a CI assertion that the
generated Bootstrap archive equals the signed-manifest digest. Commit `cefca90`
records the separately verified `v0.5.8-test` release state; it does not change the
product versions or release bytes from `3c99980`. Public-release, device, and
production-service evidence remain recorded separately.

On 8 August the owner administration panel was migrated byte-for-byte into the
separate local-only `Starlane Device Manager` Git repository, which has no remote.
Its private configuration now lives under the Windows user's LocalAppData, its
existing vault was preserved and unlocked successfully, and the standalone Release
build/tests plus loopback-only launch and restart checks passed. This client candidate
removes the panel source, tests, launcher, CI job, release artifact, and documentation
coupling and adds a regression that forbids owner-tooling release assets. Existing
public releases remain separate public-release state and may still contain a legacy
panel ZIP until an explicitly authorised publication mutation removes it.

The product source candidate was committed at `fcbec9c`; checksum-inventory correction
and evidence commit `7d56f57` is the current verified GitHub `main`. GitHub Actions run
`31270686136` passed configuration/Kodi, control-service, and Android jobs for that
exact main commit. The candidate
versions are Android `0.5.9`/code 10, Bootstrap `1.1.16`, private skin `2.2.22`,
branded provider `6.7.81.3`, and offline-signed test manifest `2026.08.39`. No draft
publication, deployment, or new device acceptance has occurred.

The owner-approved signed-release run `31270299401` created an unpublished
`v0.5.9-test` draft from `c9fe233` after the GitHub `release` environment was changed
to require reviewer `rjclark99`. Independent download verification rejected that
draft because `SHA256SUMS` named two build-only files that were not uploaded and
omitted the uploaded manifest. Commit `0acb758` replaces the broad artifact scan
with an exact flattened release-asset inventory, stages the manifest with the other
published files, rejects name collisions, and passes 15 focused release tests plus the
complete 88-test Python/Kodi suite.

Corrective signed-release run `31270754516` rebuilt the same unpublished draft from
`7d56f57`. Its 13 downloadable non-inventory assets matched the LF-only checksum file,
all GitHub-reported digests matched the downloaded bytes, and the exact GitHub manifest
blob passed its Ed25519 signature. Verification nevertheless rejected the draft because
the Linux-built private skin and provider archives did not match their Windows-built
signed package-lock hashes. Local commit `b3fed5f` uses stored entries and canonical LF
text for those locked archives, adds a workflow pre-upload package-lock gate, updates
their hashes, and re-signs configuration `2026.08.39` for deterministic Bootstrap hash
`728fd821b0cfffe2c47601ce6b90d3af242b1a68798c563c9fcb0efa85384d51`.
Two independent local builds matched byte-for-byte; all 90 Python/Kodi tests passed.
This correction is not yet on GitHub `main`; the draft must not be published or used.

The clean local source state includes the project-control rollout, bounded Home
**Show more** terminal navigation, complete ordered provider/network discovery, local
artwork fallbacks, Android one-run scope-bound consent and verified resume, and
Bootstrap 1.1.16 scope-bound authorization/revocation. Treat these as validated source
and local-candidate state only; no device, public-release, or production-service
transition is implied.

On API 25-28, the strict Android candidate may atomically merge only Kodi's fixed
`addons.unknownsources=true` preference and install only the signed-manifest-selected,
hash-verified `repository.kodisetup` archive into the canonical Kodi profile. The
transaction requires current Cancel-first local consent, storage permission,
conservative proof Kodi is stopped, journaling, exact ownership checks, and rollback;
API 29+ retains the guided manual route. After launching Kodi, the app enables only
that fixed add-on through `127.0.0.1:9090`, verifies its identity and enabled state,
and rechecks consent before each bounded retry. On Bootstrap launch, a separate local
approval is bound to the exact Bootstrap version, scoped manifest content, and
package-lock digest. The candidate
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

Private-skin candidate 2.2.22 refines the bounded Home terminal-navigation
prototype. Thirty-two configured Umbrella directory-widget instances retain their
full configured preview limit and append one `Show more` card that opens the exact
source directory. The two local Continue Watching queues and custom/non-Umbrella
widgets keep their former content behavior. A comparison against the 2.2.21 local
skin package found the same 560 entries with changes limited to `addon.xml` and
`IncludesHomeWidgets.xml`. This is local-candidate evidence only; installer,
Bootstrap, provider, package-lock, device, signed-manifest, and public-release states
are unchanged.

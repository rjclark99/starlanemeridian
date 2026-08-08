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

A newer uncommitted source candidate follows the 8 August 2026 fresh-device acceptance
attempt and targets Android `0.5.10`/code 11, Bootstrap `1.1.17`, and branded provider
`6.7.81.4`; the private skin stays at `2.2.22` because no skin change was required. It
fixes four defects: Kodi's JSON-RPC framing in the setup app's Bootstrap activator;
provider service readiness, which now cycles the enabled state to raise the enable event
Kodi needs and otherwise finishes after a restart instead of reporting a false failure;
withdrawal of the applied scope when a skin activation is never confirmed, so a freeze at
Kodi's keep-skin dialog self-heals within a bounded three attempts; and network/provider
logos, which now resolve from the locked local `resource.images.studios.coloured` bundle
rather than region-blocked third-party hosts. This candidate is source and local-candidate
state only: it is unsigned, unpublished, and unverified on any device.

The previous product source candidate was committed at `fcbec9c`; GitHub `main` advanced through
reproducibility evidence commit `5691da3`. GitHub Actions run `31271671055` passed
configuration/Kodi, control-service, and Android jobs for that exact main commit. The candidate
versions are Android `0.5.9`/code 10, Bootstrap `1.1.16`, private skin `2.2.22`,
branded provider `6.7.81.3`, and offline-signed test manifest `2026.08.40`. No draft
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

Signed-release run `31271814880` then proved that two more host inputs were not yet
canonical: 172 `.xsp` playlists plus the extensionless licence retained Windows CRLF,
and branded artwork selected host system fonts. The new pre-upload gate stopped the run
before Android signing or asset upload. Commit `2843f00` normalizes only the identified
text inputs, renders with the already bundled Starlane fonts, updates the locked skin
hash to `2342155764da3cbf8ad3d0cafa1df5c01629011f542f138f12ea316bbb798a2c`
and provider hash to `0278683f400c4f71c529dded83a8c13144b12e2aa99f48005b38d9d160d54279`,
and signs configuration `2026.08.40` for Bootstrap hash
`c40ca4675fa2e4bcb7959edb49c567f2e1ea676653a780882decdb948c40d64d`.
The local package gate, signature verification, 90 unaffected tests, and the corrected
Bootstrap regression pass. A new Linux draft remains required; no existing draft is safe
to publish or use.

Run `31272444959` confirmed the skin and Bootstrap portability fixes but stopped on the
provider alone: Pillow's binary image encoding still differed across operating systems.
Commit `5a41f22` removes provider artwork rendering from the release job and copies four
visually reviewed, checked-in Starlane assets instead. Focused overlay/release tests,
manifest verification, and the unchanged provider package-lock hash pass locally. No
Umbrella logo or background is present in those canonical assets. One fresh Linux draft
remains the required proof.

Run `31272824941` showed equal provider size but a different digest after canonical
artwork, isolating the last variable to native filesystem path ordering. Commit
`1de1fc3` sorts provider ZIP entries by their explicit POSIX archive names; the local
provider now exactly reproduces the observed Linux digest
`a81eb2bcdb10c97ebf53193753080cc4c917ece7ffcb3e920daac7a19830fb38`.
It signs manifest `2026.08.41` with Bootstrap hash
`72270e8c611e4686322f45ac7e9922089346b6d2c21f6812f7ab2d3119beb6bb`.
Focused ordering, lock, signature, Bootstrap, and project-control checks pass. A clean
GitHub run remains the final cross-host confirmation.

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

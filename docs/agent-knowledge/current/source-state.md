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

The product source candidate is committed at `fcbec9c`, is contained in local `main`,
and is pushed on `codex/fresh-install-candidate`. GitHub Actions run `31265192787` passed
configuration/Kodi, control-service, and Android jobs for those exact bytes. GitHub
`main` remains at `cefca90` pending a separate owner-approved push. The candidate
versions are Android `0.5.9`/code 10, Bootstrap `1.1.16`, private skin `2.2.22`,
branded provider `6.7.81.3`, and offline-signed test manifest `2026.08.38`. No draft
release, publication, deployment, or new device acceptance has occurred.

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

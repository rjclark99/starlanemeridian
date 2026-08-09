# Starlane Movies handoff

Updated: 2026-08-09 (Europe/London)

## Start here

Read `AGENTS.md`, then use the staged routing in
`docs/agent-knowledge/index.yaml`. Do not load the historical handoffs in full unless
specific contradictory evidence requires them. Keep source, local build, device,
signed manifest, public release, and production service state separate.

The owner is conserving agent usage. Do not rebuild, republish, redeploy, or repeat
full validation without a concrete failure that requires it. Prefer one bounded check
and ask the owner to perform simple television interactions manually.

## Current authoritative state

- Client repository: `C:\Users\Admin\Documents\Codex Projects\Kodi Remote Setup APK`
- Active candidate branch: `codex/v0.5.11-acceptance` at
  `f08d52e9a4b01661a234d0ad3e160f9c7b066b7b`, pushed to `origin`. The four candidate
  commits are `db63c94`, `23cd774`, `bad935e`, and `f08d52e`. Do not assume these are
  on `main`.
- Public release: `v0.5.10-test`, built from `42a7cb2`, is the GitHub **Latest** full
  release. It was published with the owner's explicit approval; no rebuild or asset
  replacement occurred during publication, and the `latest/download` routes were
  verified afterwards.
- Public prerelease: `v0.5.11-test` is published as a prerelease, explicitly not
  Latest. Its tag resolves exactly to `f08d52e9a4b01661a234d0ad3e160f9c7b066b7b`.
  Latest remains `v0.5.10-test` and its manifest remains configuration `2026.08.42`.
- The published release reports configuration `2026.08.42`, minimum setup app code 11,
  Bootstrap 1.1.17, setup APK 0.5.10/code 11, private skin 2.2.22, provider 6.7.81.4.
- Downloader code `7499455` remains pinned to the superseded v0.5.9 APK and must not
  be used for this pass. Code `3467018` is the previously generated reusable Latest
  installer code, not a newly generated code after `7499455`. Live inspection on
  9 August confirmed that it follows `latest/download/setup.apk`, which now serves
  v0.5.10/code 11.

## v0.5.11 verified continuation point

Targets Android `0.5.11`/code 12, Bootstrap `1.1.18`, provider `6.7.81.5`, private
skin `2.2.22`, production skin `1.3.0`, and signed configuration `2026.08.43` with
minimum setup app code 12. The APK first validates the signed Latest manifest; when
Latest legitimately targets an older app code it derives only the exact current
candidate tag `v0.5.11-test/manifest.json` and applies the same signature, schema,
stage, version, URL-allowlist, and hash gates. That fallback stops once Latest targets
code 12.

GitHub CI run `31309011020` passed Android, configuration/Kodi, and control-api for
exact commit `f08d52e`. Signed-release run `31309112396` passed for the same commit.
The release workflow is now regression-tested to set
`target_commitish: ${{ github.sha }}`. Because GitHub retained the old draft target,
the unpublished draft metadata was also explicitly corrected to `f08d52e` before
publication; no tag existed at that time and no history was rewritten.

All 14 GitHub draft assets were downloaded to
`build/device-evidence/v0.5.11-github-draft-20260809`, then the 14 public prerelease
assets were independently downloaded to
`build/device-evidence/v0.5.11-github-public-20260809`. Public and draft bytes are
identical. Verification passed for the 13-entry `SHA256SUMS`, all five sidecars,
offline manifest signature, package lock, archive roots, SBOM owner-panel exclusion,
and APK identity/signing. The public APK is `app.kodisetup.tv` 0.5.11/code 12, uses
APK Signature Scheme v2, and has signer SHA-256
`e82233eb034643f9d3e6357a74348c8900d25e28f13b694e9bdee53d9ad2828c`.

Key public asset SHA-256 values:

- `setup.apk`: `0117c126032b157e3e3d0b46c40eea61652946d434cdd2f685af29e60ea543ec`
- `manifest.json`: `b9f186e28d5cf64c9a80ea924351f7de8f7132a685db8a470f5c858371ae6bc9`
- `repository.kodisetup-1.1.18.zip`: `977c374f27239888945ddc8865db5d2d87d6c44e1b7489f61d70b8eec4161915`
- `plugin.video.umbrella-6.7.81.5.zip`: `f06266e02c56800716bf7e50eba570f40c33e2637c5abdca55353f8524710996`
- `skin.starlane.movies-2.2.22.zip`: `2342155764da3cbf8ad3d0cafa1df5c01629011f542f138f12ea316bbb798a2c`
- `skin.starlanemeridian-1.3.0.zip`: `8c7fd07d91a97e3ac490a827ade92fbb0adec150bde352da279e33ede61e7bd0`

Live pre-release artwork validation already succeeded on the local candidate: a
provider route returned 8 entries, a network route returned 104, and Netflix/ABC logos
visibly rendered from local `resource.images.studios.coloured` artwork. Evidence is in
`build/device-evidence/v0.5.11-local-pretest-20260809/`.

The authorised clean-device run is **in progress, not yet passed**. Its rollback
evidence is under `build/device-evidence/v0.5.11-clean-prewipe-20260809/`. The exact
pre-wipe Kodi profile is `kodi-profile.tar.gz` (268,430,560 bytes, SHA-256
`55cfbb2fbf9df4f9aa51b8e77a24882c3a7f51e3ad42b9242216848612c1c252`); it was listed
successfully and contains `.kodi/userdata/guisettings.xml` and `.kodi/temp/kodi.log`.
The pre-wipe installed Starlane APK was also copied and hashed. Only the named temporary
TV-side archive was removed afterwards.

Kodi and Starlane were then uninstalled successfully; Downloader was preserved.
Downloader received the exact tag-specific public URL
`https://github.com/rjclark99/starlanemeridian/releases/download/v0.5.11-test/setup.apk`
and saved `/sdcard/Download/Downloader/setup(5).apk`. Its device-side SHA-256 was
`0117c126032b157e3e3d0b46c40eea61652946d434cdd2f685af29e60ea543ec`, identical to the
verified GitHub asset. Android installed it through the visible package-confirmation
screen; installed identity is `app.kodisetup.tv` 0.5.11/code 12.

Starlane was opened, `Continue offline` was selected, and the current TV screen says
`Configuration verified` / `Configuration 2026.08.43 verified`, proving the signed
prerelease fallback works while Latest remains configuration 42. The visible actions
are `Start setup`, `Allow APK installs`, and `Install Kodi`. Resume from this exact
screen. No Kodi package is currently installed. Continue with both automation consent
confirmations, the visible Kodi installer confirmation, Bootstrap approval, Home build,
movie/TV widgets, local provider/network artwork, Show More navigation, and bounded
final logs. Further ADB execution stopped only because Codex's environment approval
reviewer reported its usage limit; this was not a product failure. Do not promote
v0.5.11 to Latest without a complete device pass and separate owner approval.

## Fresh-device acceptance result: did not pass

The pass ran on 2026-08-08 against the published bytes. Configuration `2026.08.41`
applied and the Home menu was generated, but four defects were found. Acceptance areas
4 to 7 remain unverified. All four are fixed in source; see
`docs/agent-knowledge/incidents/INC-022`, `INC-023`, and `INC-024`.

1. **Provider service readiness.** Bootstrap reported `Setup finished with 2 issue(s)`
   on every first run. A directory-replaced package is often already enabled, so
   `Addons.SetAddonEnabled(true)` was a no-op that raised no enable event and Kodi never
   started the provider's service, which is the only thing that sets
   `starlane.umbrella.ready`. Restarting Kodi always fixed it.
2. **Unconfirmed skin activation.** Kodi froze at its own keep-skin dialog. Completion
   had already been committed, so the recovery path restored Estuary while the
   configuration stayed marked applied and Bootstrap never retried. Manual skin
   selection was required.
3. **Activator could not read Kodi's JSON-RPC.** The reader waited for a newline or EOF;
   Kodi's port 9090 transport sends neither and holds the socket open, so every read hit
   its timeout with a complete response already buffered.
4. **Region-blocked logo artwork.** All 115 network/provider logos were remote
   `i.imgur.com` (78) and `i.postimg.cc` (36) URLs. Imgur is region-blocked in the UK and
   returns a notice *image*, which Kodi rendered as the logo.

## Uncommitted v0.5.10 source candidate

Targets Android `0.5.10`/code 11, Bootstrap `1.1.17`, provider `6.7.81.4`, private skin
unchanged at `2.2.22`, configuration `2026.08.42`, minimum setup app code 11.

- `restart_provider_service` cycles the provider's enabled state so Kodi raises the
  enable event that starts its service, completing setup in one launch.
- If readiness is still absent the run defers: bounded attempt recorded, notification
  shown, Kodi quit, nothing committed. Absent readiness is no longer a failure. Bounded
  by `MAX_ACTIVATION_ATTEMPTS`; once exhausted it reports a real failure instead.
- `recover_pending_skin` withdraws `applied_scope` when it cannot confirm the skin, so a
  freeze self-heals within three attempts without re-asking for consent.
- The activator stops at one complete top-level JSON value, honouring strings and
  escapes, retaining the 64 KiB cap, both timeouts, and every gate call. Loopback
  `127.0.0.1:9090` stays hard-coded — `SafeAutomationContractTest` enforces that.
- `localise_directory_logo_artwork` rewrites all 115 logos to
  `resource://resource.images.studios.coloured/<Name>.png`, already in the signed
  package lock. 105 resolve; 10 have no bundled logo and fall back to the skin's card
  art. Guards raise if fewer than 100 logos are found or if either host survives.
- The two overlay replacements injecting `starlane.umbrella.ready` now raise on drift.

### Validated

102 Python tests (`python -m unittest discover -s tools -p "test_*.py"`), `compileall`
clean, 38 Bootstrap tests, 11 overlay tests, 51 Android unit tests, `lintDebug`,
`assembleDebug`, `validate_project_control.py`, `release.py validate`, and a local-asset
lock check of the built provider and skin. The rebuilt provider has zero references to
either third-party host and 115 `resource://` paths.

Test harness note: `tools/test_kodi_bootstrap.py` used to pre-set
`starlane.umbrella.ready` and set it on *any* enable call, which is why defect 1 was
invisible. It now announces readiness only on a real disabled-to-enabled transition.

### Release candidate built

`build/release-v0.5.10-candidate`, using base URL
`https://github.com/rjclark99/starlanemeridian/releases/latest/download` and data URL
`https://control.starlanemeridian.uk/v1/public/kodi`. Both are required; omitting the
data URL changes the Bootstrap bytes.

- provider `6.7.81.4` — `512d2ba29e4ffc64ad62492f8a7a948ba55a2c16af9dff5ec75025c1c264aaf8`
- Bootstrap `1.1.17` — `f28f45bb29ef4c6d79cd6f8f5246806d5ae223a9bc5332c5c87e2726702be2b8`
- upstream provider source stays pinned at `6.7.81`
  `59aca1a3910e0dfc559b47857456a236cd7b76a16c11296d7867c8eae6999b9c`; a byte-identical
  local copy is at `build/addon-install/2026-07-26/plugin.video.umbrella-6.7.81.zip`,
  so no download is needed to rebuild.

## Release status: published Latest

Manifest `2026.08.42` is signed and verified. Signed-release run `31280750978` built
`v0.5.10-test` from `main` at `42a7cb2`. All 14 draft assets were downloaded and verified:
LF-only inventory with no gaps or mismatches, correct sidecars, valid manifest signature,
APK `0.5.10`/code 11 with the unchanged production signer, SBOM clean of owner tooling,
and the provider archive byte-identical to the Windows-built candidate.

The owner explicitly approved publication and the release became GitHub **Latest** on
8 August 2026. No rebuild or asset replacement occurred. The public manifest now serves
configuration `2026.08.42`; the APK and Bootstrap 1.1.17 routes return the expected
assets, and all 38 selected ARMv7 packages passed the public lock verification.

## What to do next

1. **Resume acceptance areas 4 to 7** on the device. Start with the Providers row: Amazon,
   Apple TV+ and Hulu were the three imgur-hosted logos showing the region notice.
2. Confirm the setup app updates to configuration `2026.08.42` and uses APK 0.5.10/code
   11; code 10 cannot parse Kodi's real port-9090 framing.
3. Decide whether `minimumSetupAppVersion` 11 is right. It forces an APK update; the
   reason is that code 10's activator cannot talk to Kodi at all.
4. Optional robustness fix: the lock's private-skin entry still points at the
   `v0.5.9-test` tag. Those bytes are unchanged so it resolves correctly, but the current
   release carries the same archive and repointing would remove the cross-release
   dependency.

`gh` is installed at `C:\Program Files\GitHub CLI\gh.exe` and authenticated for
`rjclark99` with `workflow` scope. Existing shells may have a stale PATH; a new terminal
finds it.

## Environment notes

- The Android SDK is vendored at `build/android-sdk` and there is no `local.properties`.
  Gradle needs `ANDROID_HOME` pointing at it.
- `tools/requirements.txt` (Pillow, cryptography, jsonschema) is installed.
- Run the Python suite exactly as CI does, from the repository root. Adding `-t .` breaks
  discovery because `tools` has no `__init__.py`.

## PC-only management panel

- Local repository: `C:\Users\Admin\Documents\Starlane Device Manager`
- It deliberately has no Git remote and must never be included in client releases.
- Launcher: `tools\start_admin_portal.ps1`; URL `http://127.0.0.1:54731/`, loopback only.
- Private configuration remains under `%LOCALAPPDATA%\StarlaneDeviceManager`.
- Preserve the existing vault at
  `%LOCALAPPDATA%\KodiSetupAdmin\households.vault`; never inspect, print, replace, or
  commit it.

## Important boundaries

- The owner previously asked to defer additional security review until product work is
  complete; do not weaken or remove existing security controls meanwhile.
- No device wipe, deletion, secret inspection, endpoint change, deployment, release
  mutation, commit, or push without exact owner authority.
- Do not reintroduce the device-management panel into the client repository or release.
- Do not add arbitrary remote commands, ADB exposure, URL installation, shell access,
  or accessibility automation.
- Preserve user-owned worktree changes and use one writer per path.

## Known limitation, recorded not fixed

Kodi exposes no texture-loading state, so the skin cannot honestly show a spinner while
posters stream from TMDB; its widget spinner only covers an empty container. Localising
the logos removes the wait for those rows only. Movie and TV posters still populate
asynchronously and briefly show fallback card art, which reads as breakage but is not.

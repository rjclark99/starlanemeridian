# Starlane Movies handoff

Updated: 2026-08-08 (Europe/London)

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
- Git: `main` and `origin/main` are at `5187d64`. Nothing has been committed or pushed
  for the v0.5.10 work described below; it is uncommitted worktree state.
- Public release: `v0.5.9-test`, built from `da26ba0`, is the GitHub **Latest** full
  release. It was promoted from pre-release with the owner's explicit approval; no
  rebuild or asset replacement occurred, and the `latest/download` routes were
  re-verified afterwards.
- The published release reports configuration `2026.08.41`, minimum setup app code 10,
  Bootstrap 1.1.16, setup APK 0.5.9/code 10, private skin 2.2.22, provider 6.7.81.3.
- Downloader code `7499455` resolves to the tagged `v0.5.9-test/setup.apk`.

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

## What to do next

Everything an agent can do is done. The remaining steps need the owner.

1. **Sign the manifest.** `config/manifest.json` signature value is deliberately blank
   so a stale signature cannot be mistaken for a valid one. Run
   `python tools/release.py sign config/manifest.json --private-key <offline key>`.
   No agent may handle that key.
2. **Publish as tag `v0.5.10-test`.** The provider URL is baked into Bootstrap's
   `package-lock.json`, so any other tag breaks the chain.
3. **Build the release APK** with the production keystore in CI. `assembleRelease` was
   not run locally for that reason.
4. **Re-run `python tools/verify_kodi_package_lock.py` after publication.** Before it,
   the provider URL 404s by design.
5. **Resume acceptance areas 4 to 7** on the device once the signed release is installed.
6. Decide whether `minimumSetupAppVersion` 11 is right. It forces an APK update; the
   reason is that code 10's activator cannot talk to Kodi at all.

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

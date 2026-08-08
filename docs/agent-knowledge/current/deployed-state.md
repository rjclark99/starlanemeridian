---
id: current.deployed-state
kind: current
status: needs-verification
verified_at: 2026-07-29
tags: [device, kodi, fire-tv, control-api, real-debrid]
authority: [adb, wrangler, docs/CURRENT_STATUS.md]
supersedes: []
---

# Reference device state

This record contains bounded device and service observations last verified on
29 July 2026. No live device or production-service inspection was performed
during the 1 August project-control rollout. Treat installed versions, reachability,
and rollback locations below as historical evidence until they are re-established by
the matching read-only runbook.

The newest bounded Fire TV acceptance on 29 July preserved the active skin,
Bootstrap, generated menus, skin settings, `guisettings.xml`, and Kodi log under
`build/device-backups/black-screen-fix-preapply-20260729/`. Directly overlaying the
two corrected Kodi source files and restarting Kodi changed the failed
black-screen-with-logo state into the complete Starlane navigation. The skin persisted
`homelayout=bingie`; the new log contained no error, fatal, invalid-include, or
directory-failure match. This proves the two Kodi-side corrections on the reference
device, but is not a complete public ZIP installation or release claim.

The signed Android 0.5.2/code 7 candidate containing the fresh-profile safeguard was
also installed in place and launched successfully with no fatal application
exception. Its SHA-256 is
`0FC665DBBFC3AB0AED09DD19F3DCA6E21DFEDA33577D6AA4929A359DAE2CF122`.
Because the device now has a valid Kodi profile, refusal to create a missing profile
is covered by the focused Android regression rather than another destructive profile
reset.

The newest bounded Fire TV check on 29 July directly overlaid only the local branded
provider candidate for diagnostic validation. Kodi registered
`plugin.video.umbrella` 6.7.81.2, its service started and completed scraper account
sync, Bootstrap reported configuration `2026.07.32` already applied, and the pending
skin marker was clear after skin confirmation. The new Kodi log had no
`repository.umbrellakodi`, unknown-add-on, exception, or error match. This proves the
provider startup correction on the reference device; it is not evidence that the
now-public Bootstrap 1.1.12 and manifest `2026.07.33` have been applied through the
complete release flow on that device.
The pre-test provider and profile rollback remain under
`build/device-backups/2026-07-29-pre-bootstrap-1.1.11/`.

The reference Fire TV now has the signed local Starlane Movies setup 0.5.2/code 7
candidate installed in place with the production signer; application data was
preserved. The final installed candidate SHA-256 is
`9A342CD16C64775C652B2D218848E09D236FDF53F7E635A5EDB02C9D3589DC05`.
With Kodi stopped and `addons.unknownsources` deliberately set false, the
app received the visible Android storage permission, prepared the verified Bootstrap,
merged the value to true, and Kodi retained true after launch. The pre-update APK and
exact pre-test `guisettings.xml` are preserved under
`build/device-backups/unknown-sources-pre-0.5.2-20260729/`; their SHA-256 values are
`38AA5368710C9A026A1CF93A7AB31E47FD88D67078C1BA69F12C24259097FA96`
and `38D7F344221EE570E27346C56CAE1DFA1054421DCE8EC95263BA5FDA0C8A9CCF`.

The latest bounded device transition on 29 July preserved the failed Bootstrap 1.1.9
log, settings, and add-on metadata under
`build/device-backups/failed-one-shot-1.1.9-20260729/`, then cleared Kodi data with
owner authority. Kodi 21.3 remains installed and has been launched into a fresh
profile. Verified local Bootstrap 1.1.10 is staged at
`/sdcard/Download/repository.kodisetup-1.1.10.zip` but is not yet installed; Unknown
Sources and Install from ZIP remain explicit owner actions. No successful 1.1.10
device-install claim was made at that staging point.

The owner subsequently completed the clean first-run flow and confirmed it succeeded
without individual dependency authorization prompts. Fresh read-only verification
found Bootstrap 1.1.10 installed, all 38 locked package IDs present, Bootstrap's
one-time authorization persisted, `skin.starlane.movies` 2.2.20 active, and the
production signed configuration `2026.07.30` applied. Umbrella 6.7.81 and
CocoScrapers 1.0.39 registered and started. The source-only manifest remains
`2026.07.31`; source, public-release, and device states are not conflated.

The preceding 1.1.9 test accepted its one-time Starlane authorization, then stopped at
Kodi's first native confirmation for `script.bingie.helper`; `applied_version` remained
`unapplied`. The exact pre-1.1.9 Kodi profile is preserved at
`build/device-backups/initial-authorization-pre-1.1.9-20260729/` with archive SHA-256
`8EEF39F457DD7D3B53753BD3A0FF117D6FC90544860AC25EB751F51CBB5EAAF7`.

Earlier on 29 July 2026, with explicit owner authority, data was cleared for
`org.xbmc.kodi` and `app.kodisetup.tv` after Bootstrap failed while installing the
BINGIE MOD repository and Umbrella did not download. At that point both APKs remained
installed: Kodi 21.3 and Starlane Movies setup 0.5.1/code 6. Kodi's `.kodi` profile
was absent and the setup app required pairing again. The exact failed-bootstrap Kodi profile
and both installed APKs are preserved under
`build/device-backups/failed-bootstrap-pre-clear-20260729/`; the validated profile
archive SHA-256 is
`E08BEE29DD38715C588D805067EB6C12938A36F96780DDCC2D28F7C303EE77C2`.

Later on 29 July, local Bootstrap 1.1.6 was copied into the fresh Kodi profile and
Kodi registered it as installed but disabled, as expected for a package not confirmed
through Kodi's Install from ZIP flow. Its verified ZIP is also staged on the TV at
`/sdcard/Download/repository.kodisetup-1.1.6.zip`, SHA-256
`9B0ED26FF18E8F02D0FD5A8FB576AD2EA593CAC78C5F287D5C4AE29C5437C5BB`.
No Bootstrap service code has executed and this is not a successful device test.
Unknown Sources and ZIP confirmation remain explicit owner actions. The valid fresh
pre-install profile backup is
`build/device-backups/fresh-pre-bootstrap-20260729/kodi-fresh-pre-bootstrap-20260729-valid.tar.gz`,
SHA-256 `8AEFA67C3D5D68A8FE95230175AC34E7D140CA7C9A9E6BD3E60EA2A8073152F5`.

The owner then confirmed Install from ZIP and the device test advanced through 1.1.7
to verified local Bootstrap 1.1.8. Version 1.1.8 installed the private skin's exact
declared prerequisite list in order, installed and activated
`skin.starlane.movies` 2.2.20, set applied configuration `2026.07.30`, and cleared
both pending and previous skin recovery values on the second launch. The active skin
remained `skin.starlane.movies`. The device ZIP and local candidate both have SHA-256
`A63529447D8AB51BC00179A16E1CEE7E79B92E41A55C686D9A5B2E2D346D79D3`.

Umbrella remains absent in device state because the production signed manifest is
still `2026.07.30`, whose add-on list is empty. Consequently the skin logs expected
missing `plugin.video.umbrella` routes. The source candidate manifest `2026.07.31`
contains the pinned official Umbrella repository and required Umbrella entry but is
unsigned and unpublished; no Umbrella device-install claim is made. Exact intermediate
Bootstrap rollback evidence is under
`build/device-backups/bootstrap-1.1.6-pre-1.1.7-20260729/` and
`build/device-backups/bootstrap-1.1.7-pre-1.1.8-20260729/`.

Immediately before this reset, the bounded device check reported Kodi 21.3 with private
`skin.starlane.movies` 2.2.20 active. The main menu is VOD-only: Search, Home, New &
Popular, TV Shows, Movies, Categories, and My List. Mad Titan and The Crew, their
profile data, and cached install packages are absent. Starlane Movies: On Demand
6.7.81.1 remains enabled. The generated include has 106 Umbrella route references and
zero FenLight, Mad Titan, The Crew, Live TV ID, or Sports ID references. Production
skin 1.2.4 remains installed. Private 2.2.19 is the immediate rollback.

Earlier deployment evidence recorded the setup application upgraded in place to
0.5.0/code 5 using an APK signed by
the same certificate as the previously installed 0.3.0 build. It retained its
pairing and reported app version 5 through the production control plane. Kodi
remained running as 21.3 during the setup-app upgrade.

Production service state at Worker version
`0d4c80cc-0fc5-455b-b594-ceb7c918265d` includes applied D1 migration
`0004_real_debrid_authorization.sql`. Public health returned 200, unauthenticated
`/v1/admin/*` traffic was redirected to Cloudflare Access, and the separately
maintained owner tool reached the admin devices endpoint without exposing its
credentials. The exact public provider 6.7.81.2 route returned the public release
bytes while the superseded 6.7.81.1 route returned 404. Owner-tool runtime and vault
state are external to this repository and require separate live verification.

Local ignored rollback evidence is under
`build/device-backups/kodi-active-pre-real-debrid-deploy-20260729/`,
and `build/device-backups/real-debrid-remote-auth-pre-0.5.0-20260729/`.
The Kodi backup contains
the installed 21.3 APK plus a verified full `.kodi` archive; treat it as sensitive
because it contains provider settings and viewing databases.

Device reachability, installed versions, and rollback files are mutable. Recheck them
read-only before any hardware change and use the private-skin device-test runbook.

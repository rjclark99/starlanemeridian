# Starlane Meridian agent handoff

Last updated: 22 July 2026 after the verified skin 1.2.4 / v0.3.8-test release.

This is the continuity document for a new Codex task. Read this file first, then
`README.md`, `SECURITY.md`, `docs/CURRENT_STATUS.md`, and `docs/OPERATIONS.md` before
changing code or deployed state. `docs/OWNER_SETUP_GUIDE.md` is the detailed owner
runbook; some example version numbers in it are historical, so prefer the live values
below and in `config/manifest.json`.

## 1. Owner intent and standing instructions

The product is a branded, remote-friendly provisioning system for Fire TV, Fire OS,
Android TV, and Google TV. A household downloads the setup APK using a permanent
Downloader code, pairs it to the control plane, and is guided through official Kodi
and Proton VPN installation. The setup app should automate everything Android permits
while leaving unavoidable Android/Kodi permission and package-install confirmations to
the TV user. A Windows portal provides household management, observability, pairing,
safe remote commands, and an ADB fallback for exceptional support cases.

The owner prefers the agent to do as much as safely possible and request input only
when an external confirmation, secret, legal allowlist, design choice, or other
irreducible owner action is required.

Standing constraints from the owner and product design:

- Do not shut down the computer, sign the owner out, or close their running dashboard
  unless the owner explicitly changes that instruction.
- Keep the administration portal password protected and bound only to localhost.
- Retain ADB support, but do not turn the cloud service into a remote shell or arbitrary
  ADB command channel.
- Do not automate CAPTCHA, terms acceptance, Proton account farming, account transfer,
  or payment submission. Never collect or retain card details.
- Real-Debrid and Proton accounts are individually owned per household. Real-Debrid
  uses its official device OAuth path. Kodi add-ons perform their own supported
  authorization; the platform must not inject or scrape credentials.
- Do not publish unreviewed third-party repositories/add-ons. Exact add-on entries stay
  empty until the owner supplies an authorized/legal allowlist.
- Never expose or commit private keys, Android keystores, vault data, Cloudflare Access
  secrets, OAuth tokens, pairing codes, or household credentials.
- Preserve user changes and unrelated work. Do not use destructive Git or filesystem
  commands. Back up the device state before risky physical-device changes.

## 2. Repository and deployed endpoints

- Workspace: `C:\Users\Admin\Documents\Codex Projects\Kodi Remote Setup APK`
- GitHub: `https://github.com/rjclark99/starlanemeridian` (public)
- Default branch: `main`
- Current clean HEAD: `79650c2` (`Document Meridian skin 1.2.4 release`)
- Code commit for the current skin: `8b0e4b2`
- Latest release: `v0.3.8-test`
- Release URL: `https://github.com/rjclark99/starlanemeridian/releases/tag/v0.3.8-test`
- Permanent setup APK: `https://github.com/rjclark99/starlanemeridian/releases/latest/download/setup.apk`
- AFTVnews Downloader code: `3467018` (`https://aftv.news/3467018`)
- Control plane: `https://control.starlanemeridian.uk`
- Health endpoint: `https://control.starlanemeridian.uk/health`
- Windows portal: `http://127.0.0.1:54731`
- Cloudflare Worker: `starlane-meridian-control`
- D1 database: `kodi-setup-control`
- D1 ID: `7ffe748f-2434-46cf-b561-b5cfd904d085`
- Cloudflare admin boundary: only `/v1/admin/*` is behind Access. Do not protect
  `/v1/devices/*`, `/v1/public/kodi/*`, or `/health`; those routes have their own
  intended authentication/allowlisting behavior.

The GitHub CLI at `build\github-cli\bin\gh.exe` is authenticated for this repository.
ADB is at `build\android-sdk\platform-tools\adb.exe`. Bundled Python and Git have
previously been available under `C:\Users\Admin\.cache\codex-runtimes\...`; rediscover
workspace dependency paths if they change rather than hard-coding an obsolete runtime.

## 3. Current verified versions and physical device

Reference device:

- Amazon Fire TV model reported as `AFTKAUK001`
- Fire OS based on Android 9
- LAN ADB address: `192.168.1.64:5555`
- ADB was enabled and approved by the TV user
- Kodi 21.3 installed as `org.xbmc.kodi`
- Proton VPN 5.5.68.0 installed as `ch.protonvpn.android`
- Setup app 0.3.0, version code 3, package `app.kodisetup.tv`
- Kodi Bootstrap / repository add-on 1.1.3, ID `repository.kodisetup`
- Active custom skin 1.2.4, ID `skin.starlanemeridian`
- Applied signed configuration `2026.07.11`
- Bootstrap recovery settings are clear: `pending_skin` and `previous_skin` are unset
- Real-Debrid device OAuth completed; only premium-expiry status is reported to cloud

The portal process was running and responsive as `KodiSetup.Admin`, PID 3752, at the
end of the prior task. A PID is ephemeral: check by process name and URL rather than
assuming 3752 remains valid. Do not replace an existing vault or create a new one when
one already exists.

Useful device checks:

```powershell
.\build\android-sdk\platform-tools\adb.exe connect 192.168.1.64:5555
.\build\android-sdk\platform-tools\adb.exe -s 192.168.1.64:5555 shell head -n 2 /sdcard/Android/data/org.xbmc.kodi/files/.kodi/addons/skin.starlanemeridian/addon.xml
.\build\android-sdk\platform-tools\adb.exe -s 192.168.1.64:5555 shell cat /sdcard/Android/data/org.xbmc.kodi/files/.kodi/userdata/addon_data/repository.kodisetup/settings.xml
```

Do not assume the device is online. A failed connection may simply mean the television
is off, asleep, on another IP, or awaiting ADB authorization. Ask the owner only after
safe discovery/retry steps are exhausted.

## 4. Current release verification

`v0.3.8-test` is the latest non-prerelease GitHub release so the permanent `/latest/`
URLs resolve correctly. It has 22 assets, including:

- unchanged signed `setup.apk` (app 0.3.0)
- unchanged Windows self-contained administrator ZIP
- signed manifest `2026.07.11`
- Bootstrap 1.1.3 ZIP and SHA-256 sidecar
- Kodi `addons.xml` and sidecar
- rollback skins 1.0.0 through 1.2.3
- current skin 1.2.4 and sidecar
- `SHA256SUMS`

Every draft asset was downloaded back through GitHub and matched byte-for-byte before
publication. GitHub and Cloudflare public skin routes returned HTTP 200, and the
manifest verified against `config/manifest.pub`. CI run `29888046398` passed for the
code commit; CI run `29888333126` passed after the documentation commit. The repository
was clean at handoff.

Skin 1.2.4 fixed Kodi's persistent selected-list rendering. Only the control that
actually owns focus now paints a white focus surface. Physical Favourites and Power
captures each show exactly one highlight:

- `build\skin-screenshots\meridian-1.2.4-single-focus.png`
- `build\skin-screenshots\meridian-1.2.4-power-single-focus.png`
- related Kodi log: `build\skin-screenshots\kodi-1.2.4.log`

The generated/build/release folders are intentionally ignored by Git. Do not treat an
ignored artifact as reproducible proof unless its source commit, manifest signature,
hash, and release download have also been checked.

## 5. Architecture and source map

### Android TV / Fire TV setup app

Location: `android-app/`

- Kotlin, Jetpack Compose for TV, Java 17
- `minSdk 25`, `targetSdk 36`, `compileSdk 36`
- D-pad-first UI and ARM32/ARM64 detection
- Downloads and verifies the signed manifest
- Verifies artifact SHA-256, package identity, ABI, and signing certificate before
  invoking Android's package installer
- Prefers Amazon Appstore / Google Play for Proton; reviewed GitHub artifacts are a
  schema-supported fallback but the live manifest currently has no Proton APK artifact
- Creates a non-exportable P-256 device key in Android Keystore
- Signs device requests with timestamp, nonce, and body hash
- Stores Real-Debrid tokens only in Android Keystore-backed local storage
- Polls allowlisted cloud commands and sends bounded setup telemetry/heartbeats

Primary workflow code:

- `android-app/app/src/main/java/app/kodisetup/tv/SetupViewModel.kt`
- `android-app/app/src/main/java/app/kodisetup/tv/net/ControlClient.kt`
- `android-app/app/src/main/java/app/kodisetup/tv/net/RealDebridClient.kt`
- `android-app/app/src/main/java/app/kodisetup/tv/security/ManifestSecurity.kt`
- `android-app/app/src/main/java/app/kodisetup/tv/security/DeviceIdentity.kt`

### Windows administration portal

Locations: `admin-portal/`, `admin-portal.tests/`

- .NET 8 self-contained Windows portal
- Binds to `127.0.0.1:54731`; rejects non-loopback requests
- All `/api/*` routes except vault status/create/unlock require an unlocked vault
- Vault uses Argon2id, AES-256-GCM, and Windows DPAPI; auto-lock is 15 minutes
- Clipboard clearing is configured for 60 seconds
- Vault default path: `%LOCALAPPDATA%\KodiSetupAdmin\households.vault`
- No recovery backdoor and no cross-Windows-profile restore path
- Supports household records, encrypted export, audit history, pairing, device list,
  allowlisted commands, deletion, and ADB install/bootstrap fallback

The checked-in `admin-portal/appsettings.json` intentionally contains blank Cloudflare
Access credentials. The running/published local portal has been configured separately.
Never overwrite working local configuration with the blank template. Never print the
service-token values into a terminal, response, log, or handoff.

### Cloudflare Worker / D1 control plane

Location: `control-api/`

- TypeScript Worker using D1
- Production custom domain is configured in `control-api/wrangler.toml`
- Migrations `0001_initial.sql`, `0002_remote_setup_commands.sql`, and
  `0003_device_observability.sql` are deployed
- Pairing codes expire after 600 seconds
- Status/audit retention is bounded to 90 days
- Device status, nonce replay protection, command pull/ack, deletion, and bounded event
  history are implemented
- Public Kodi route redirects only allowlisted repository/skin artifact paths to flat
  GitHub Release assets
- Commands are a closed enum. Implemented families include setup/install/retry,
  `SYNC_CONFIG`, `PREPARE_BOOTSTRAP`, `OPEN_AUTHORIZATION`, and consent-required
  `REQUEST_DIAGNOSTICS`
- No arbitrary URLs, command payload fields, shell, or ADB execution are accepted

### Kodi Bootstrap and custom skin

Locations: `kodi/`, `tools/skin_builder.py`, `tools/release.py`

- `repository.kodisetup` exposes repository and service extension points
- Bootstrap verifies the signed manifest, updates repositories, installs/enables
  allowlisted add-ons, applies non-secret settings idempotently, and activates the skin
- Bootstrap safely merge-writes only `<splash>false</splash>` into Kodi advanced
  settings, preserving unrelated settings and rejecting malformed XML
- Skin activation records the previous skin and restores it or Estuary if activation
  fails; two launches are normally required to apply then confirm/clear recovery state
- The Meridian skin is generated from a reviewed Kodi/Estuary source archive, retains
  GPL attribution, and remains independently updateable
- Manifest actions/providers are closed/compiled allowlists, not arbitrary Kodi built-in
  strings, Python, shell, or plugin URLs

Current home order is exactly:

1. Home
2. Search
3. TV Shows
4. Movies
5. Live TV
6. Kids & Family

Quick Access contains Favourites, Add-ons, Profiles, Settings, and Power. Selectable
left-rail labels use 28-pixel type, a 28-pixel inset, and 306-by-60-pixel focus
surfaces. The Quick Access heading is intentionally smaller because it is a section
caption. The style is sleek, cinematic, minimal, remote-friendly, and influenced by
the information architecture of Bingie without copying protected artwork or code.
Animations are deliberately restrained. TMDb Helper and Global Search are optional;
the home screen must remain usable without them.

Brand sources live in `assets/branding/`; guidelines are in `docs/BRAND_GUIDE.md`.
Production colours, emblem, horizon art, tagline, and safe-area rules are established.

### Signed configuration and tools

Locations: `config/`, `tools/`

- Live manifest: `config/manifest.json`
- Public schema: `config/manifest.schema.json`
- Public Ed25519 key: `config/manifest.pub`
- Private Ed25519 key: ignored `.secrets/manifest.key`
- Android keystore and signing properties: ignored `.secrets/`
- Never read private key or keystore contents into chat or command output
- Increment `configVersion` for every released configuration change
- Increment `SKIN_VERSION` in `tools/skin_builder.py` for every skin package change
- Sign the final manifest only after all generated hashes/versions are correct

The live manifest is still `stage: "test"`. Kodi stable 21.3 artifacts and signer
fingerprints are pinned. `repositories` and `addons` are empty by design.

## 6. Test and build commands

Run the narrowest relevant tests during iteration, then the complete CI-equivalent
checks before a release.

Python/Kodi/configuration tests (currently 29):

```powershell
python -m unittest discover -s tools -p "test_*.py"
python -m compileall -q kodi tools
python tools\release.py validate config\manifest.json
python tools\release.py verify config\manifest.json --public-key config\manifest.pub
```

Control API:

```powershell
Set-Location control-api
pnpm install --no-frozen-lockfile
pnpm check
pnpm test
Set-Location ..
```

Android:

```powershell
Set-Location android-app
.\gradlew.bat :app:testDebugUnitTest :app:lintDebug
Set-Location ..
```

Windows portal:

```powershell
dotnet restore admin-portal\KodiSetup.Admin.csproj
dotnet build admin-portal\KodiSetup.Admin.csproj -c Release --no-restore
dotnet run --project admin-portal.tests\KodiSetup.Admin.Tests.csproj -c Release
```

Skin and repository build:

```powershell
python tools\skin_builder.py --upstream-archive artifacts\kodi-source.zip --manifest config\manifest.json --output artifacts\skin
python tools\release.py kodi --output artifacts\kodi-next --base-url https://github.com/rjclark99/starlanemeridian/releases/latest/download --data-url https://control.starlanemeridian.uk/v1/public/kodi
```

Manifest signing (trusted owner workstation only):

```powershell
python tools\release.py sign config\manifest.json --private-key .secrets\manifest.key
python tools\release.py verify config\manifest.json --public-key config\manifest.pub
```

GitHub Actions workflows:

- `.github/workflows/ci.yml`: control API, configuration/Kodi, Android, and portal
- `.github/workflows/release.yml`: signed release workflow
- `.github/workflows/vendor-monitor.yml`: review-only vendor update PRs

Current CI has harmless Node 20 action deprecation warnings and a Gradle executable-bit
warning on Linux. They do not indicate product failures, but upgrading action revisions
is a future maintenance task.

## 7. Safe release procedure used successfully

Do not publish directly from an unverified local artifact.

1. Make the source/config change and add regression tests.
2. Increment the skin/config version as applicable.
3. Validate and sign the manifest locally.
4. Build skin and Kodi repository artifacts reproducibly.
5. Test on the Fire TV as a candidate. Save screenshots/logs under ignored `build/`.
6. Commit and push source, then wait for the entire GitHub CI matrix to pass.
7. Assemble a new `build/release-vX.Y.Z-test/publish` directory. Retain all prior skin
   ZIPs and sidecars needed for rollback/history. Replace current manifest, repository
   metadata, and new skin assets. Keep `setup.apk` and portal ZIP unchanged unless those
   products actually changed.
8. Generate exact SHA-256 checksums. Package sidecars must contain LF-only bytes because
   Kodi previously exposed a Windows CRLF parsing defect.
9. Create a draft GitHub release. Do not mark it prerelease if `/releases/latest/` must
   resolve to it.
10. Download every draft asset back through GitHub and compare its SHA-256 to the local
    file. Abort on any missing or changed byte.
11. Publish as latest, then check HTTP 200 for manifest, setup APK, current skin GitHub
    URL, and the Cloudflare Kodi artifact route. Verify the public manifest signature.
12. Restart Kodi to let Bootstrap apply the new manifest. Restart again so it confirms
    the skin and clears `pending_skin`/`previous_skin`. Check the Kodi log for skin,
    Bootstrap, XML, fatal, and exception errors.
13. Update `docs/CURRENT_STATUS.md`, commit it, push, wait for final CI, and leave the
    working tree clean.

The manual release path above was used because the GitHub `release` environment had
empty signing/configuration values during earlier workflow attempts. Before trusting
the automated signed-release workflow, restore and verify all required environment
secrets listed in `docs/OWNER_SETUP_GUIDE.md`, especially `ANDROID_KEYSTORE_BASE64`.
Never upload the manifest private key to GitHub; the workflow verifies an offline-signed
manifest using the public key.

## 8. Completed goals

- Public repository, domain, Cloudflare account, Worker, D1 database, custom hostname,
  and Cloudflare Access boundary are established.
- Permanent Downloader flow works with code `3467018` and stable `setup.apk` filename.
- Signed setup app installs and upgrades on the reference Fire TV while preserving
  pairing and Real-Debrid state.
- Kodi and Proton installation paths, Android installer confirmations, ABI/signature/
  hash checks, storage/permission errors, and Fire OS compatibility fixes are built.
- Device pairing, signed status requests, replay protection, bounded telemetry, safe
  remote commands, event history, device/household deletion, and diagnostics consent
  boundaries are implemented and production tested.
- Password-protected localhost dashboard, encrypted local vault, household records,
  audit, ADB tools, progress display, device facts, package versions, readiness state,
  Real-Debrid expiry, and event timeline are implemented.
- Real-Debrid official device OAuth succeeds on the reference TV without uploading its
  token or password.
- Bootstrap 1.1.3 installs from the public repository, applies signed config
  idempotently, handles splash configuration safely, activates/restores skins, and
  clears recovery state after confirmation.
- Original Starlane Meridian branding, logo/emblem, horizon art, tagline, brand guide,
  and generated asset pipeline are established.
- Meridian skin 1.2.4 has branded startup, cinematic hero, ordered menus, local/PVR
  widgets, Family playlists, optional search adapters, Quick Access, power dialog,
  now-playing ribbon, consistent typography/focus geometry, overscan margins, no native
  Kodi splash, and exactly one visual focus target.
- CI, vendor monitoring, schema validation, release tooling, artifact allowlisting,
  checksums, rollback assets, and physical Fire TV regression procedures are working.

## 9. Incomplete and future goals, in priority order

### A. Continue physical skin quality and usability work

This is the immediate product-design stream. The empty-library Fire TV pass is strong,
but a content-populated test remains outstanding. Populate or safely point a test Kodi
library at legitimate sample content and verify:

- real poster/fanart aspect ratios and crops
- long and two-line title behavior without truncation
- widget traversal, focus handoff, back/menu behavior, and empty/error states
- PVR channel logos and Live TV presentation
- optional TMDb Helper and Global Search result layouts/performance
- Settings, add-on browser, profiles, media windows, dialogs, OSD, notifications,
  keyboard, file browser, and other inherited Estuary windows under the Meridian theme
- performance and memory on lower-end Fire OS hardware

Maintain one clear focal point, white left-rail text, consistent sizing, safe overscan,
minimal animation, and no heavy mandatory helper services. Fix issues in the builder,
not only in a generated device copy, and add a regression assertion for each defect.

### B. Obtain and test Android TV / Google TV hardware

No Android TV/Google TV device is currently available. Fire TV does not substitute for
that pass. Test API 25+, ARM32/ARM64 where available, Google Play routing, unknown-source
permissions, scoped storage, package installer resume behavior, and D-pad navigation.

### C. Owner-approved Kodi add-on/repository allowlist

The manifest intentionally has no third-party repositories or add-ons. The owner must
supply exact legal/authorized repository URLs, add-on IDs, required/optional status,
settings, desired widget providers, and authorization expectations. Then:

- validate source ownership/distribution permission and dependencies
- pin hashes and constrain GitHub release asset selection
- add only enumerated adapter IDs and documented non-secret settings
- test dependency ordering, idempotency, failure isolation, update behavior, and rollback
- open each Real-Debrid add-on's supported authorization UI; never inject credentials

A reference Kodi profile inventory exists under ignored `build/` and is generated by
`tools/profile_export.py`. It is review-only and excludes secrets/history. Do not turn
it into a raw backup restore mechanism. A schema-driven bootstrap is preferred over a
Dropbox/Kodi Backup snapshot because it is safer, maintainable, diffable, and supports
clean upgrades; backups may be offered later only as explicit disaster recovery.

### D. Repair and validate automated signed releases

The GitHub `release` environment previously returned empty values for all release
settings/secrets, causing an empty-keystore error. Verify all required names from the
owner guide, test with a non-production/draft run, require environment approval, and
prove the output matches the trusted local path before relying on automation.

### E. Promote from test to stable

The live manifest and releases are deliberately test-stage. Stable promotion requires
the owner checklist, Android TV coverage where applicable, release secrets repaired,
current vendor checks, SBOM/checksum/signing verification, recovery tests, and a clear
rollback/revocation plan. Do not call the present release production-stable.

### F. Vendor and maintenance work

- Continue scheduled review-only Kodi/Proton monitoring; never auto-publish updates.
- Kodi 21.3 is currently pinned. Re-verify official hashes/signers before any change.
- Proton store delivery remains preferred. Add a GitHub fallback only after artifact,
  signer, ABI/API, and update-behavior review.
- Upgrade deprecated GitHub Action revisions when safe.
- Revisit retention, dependency updates, security tests, and device compatibility as the
  household count grows.

### G. Operational documentation and recovery

- Keep an encrypted offline backup of `.secrets/manifest.key`, `.secrets/release.jks`,
  signing passwords, and the local vault export. The agent must not perform or inspect
  those backups without explicit owner authorization.
- Confirm Cloudflare Access service-token rotation and vault restore procedures.
- Document household consent/account handoff dates and per-household ownership without
  placing credentials or payment data in cloud records.

## 10. Known limitations and non-goals

- An ordinary sideloaded Android app cannot silently approve unknown sources or package
  installation. The remote household user must confirm required system prompts.
- Enabling Developer Options and approving ADB must be done locally on the TV.
- Cloud control is pull-based and allowlisted; it is not an unattended remote desktop.
- ADB at a private LAN address is not reachable from outside the household without an
  explicitly designed network/support path. Do not expose port 5555 to the internet.
- Proton registration automation/account generation and Real-Debrid registration/payment
  automation are intentionally excluded. The system can generate suggestions, open the
  official page, store consented local credentials, and use official OAuth only.
- Kodi itself remains the official package/name. The branded launcher/skin approach is
  deliberate; a renamed Kodi fork would create substantial GPL, trademark, signing,
  security-update, and compatibility maintenance.
- The setup app is privately sideloaded, not published in Google Play/Amazon Appstore.

## 11. First actions for the next agent

1. Read the five source-of-truth documents named at the top of this handoff.
2. Run `git status --short` and `git log -5 --oneline`; preserve a clean `main` at or
   after `79650c2`.
3. Check `http://127.0.0.1:54731` and the `KodiSetup.Admin` process without restarting or
   replacing the vault.
4. Check the public health endpoint and latest GitHub release without mutating them.
5. If the Fire TV is needed, confirm with ADB and read the current skin/config state
   before pushing anything. Do not assume it is powered on.
6. Ask the owner what they want to inspect next in the skin, unless a new concrete issue
   is already included in the new task. Reproduce on hardware, fix the generator, add a
   test, build a candidate, inspect screenshots/logs, and only then release.
7. Keep `docs/CURRENT_STATUS.md` and this handoff synchronized after material milestones.

## 12. Security stop conditions

Stop and ask the owner rather than guessing if work would require:

- revealing, rotating, deleting, or replacing a private/signing/access/vault secret
- deleting a household/device/vault or uninstalling an app with user data
- making the repository private or changing permanent release/domain URLs
- exposing ADB, the localhost portal, or admin APIs beyond their current trust boundary
- adding a third-party repository/add-on without a documented allowlist and permission
- accepting provider terms, submitting registration, bypassing verification, or handling
  payment data for another person
- promoting a test release to stable without the acceptance checklist

The safest continuation pattern is: inspect, reproduce, change source, add a regression
test, validate locally, test on hardware, pass CI, stage a draft, byte-verify downloads,
publish, verify public routes/signature, confirm Bootstrap recovery, document, and leave
the repository clean.

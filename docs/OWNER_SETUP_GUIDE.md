# Owner setup and release guide

This runbook covers every owner-operated step needed to turn this source tree into a hosted setup service, signed `setup.apk`, Windows administration bundle, Kodi repository, and Downloader code.

Do not begin a public release until the final checklist passes. The release tooling intentionally rejects placeholder hashes, `example.invalid`, and `OWNER/REPOSITORY` in a stable manifest.

## 1. Decisions and accounts you need

Prepare these first:

- The established **Starlane Meridian** identity. Production artwork and its usage rules live in `assets/branding/` and `docs/BRAND_GUIDE.md`.
- A GitHub account and the final public repository name.
- A Cloudflare account. A domain managed by Cloudflare is strongly recommended so that only `/v1/admin/*` is protected by Cloudflare Access while device endpoints remain public.
- One administrator email identity for Cloudflare Access.
- A secure offline location for the Android signing keystore and manifest signing key backups.
- At least one representative Fire TV and one Android TV/Google TV device. ARM32 and ARM64 test devices are preferable.
- A legal allowlist of any third-party Kodi repositories and add-ons you intend to distribute. Leave the lists empty until this is known.

Each household must create and own its own Proton and Real-Debrid accounts. Do not create batches of Proton addresses, automate registration, accept provider terms for someone else, or retain payment-card details.

## 2. Install the owner workstation tools

Install on Windows:

1. Git.
2. Python 3.12 or later.
3. .NET 8 SDK.
4. JDK 17. Confirm that `keytool.exe` is available.
5. Node.js 22 and pnpm 10.
6. Android Studio with Android SDK Platform 36 and current Build Tools. The Build Tools provide `apksigner` for inspecting APK certificates.
7. Android SDK Platform Tools, which provide `adb.exe`.
8. GitHub CLI (`gh`) if you want to create the repository and secrets from the command line.

From PowerShell, set the project directory for the current session and install project dependencies:

```powershell
$ProjectRoot = 'C:\Users\Admin\Documents\Codex Projects\Kodi Remote Setup APK'
Set-Location -LiteralPath $ProjectRoot
python -m pip install -r tools\requirements.txt
Set-Location control-api
pnpm install
Set-Location $ProjectRoot
```

Run the baseline checks:

```powershell
python tools\release.py validate config\manifest.example.json
python -m unittest discover -s tools -p 'test_*.py'
dotnet build admin-portal\KodiSetup.Admin.csproj -c Release
dotnet run --project admin-portal.tests\KodiSetup.Admin.Tests.csproj -c Release
Set-Location control-api
pnpm check
pnpm test
Set-Location $ProjectRoot
```

## 3. Choose names and permanent URLs

This guide uses these examples:

| Value | Example |
| --- | --- |
| GitHub owner | `rjclark99` |
| Repository | `kodi-setup-platform` |
| GitHub Pages repository base | `https://rjclark99.github.io/starlanemeridian/kodi` |
| Latest signed manifest | `https://github.com/rjclark99/starlanemeridian/releases/latest/download/manifest.json` |
| Stable setup APK | `https://github.com/rjclark99/starlanemeridian/releases/latest/download/setup.apk` |
| Control API | `https://kodi-control.example.com` |

Choose these values once. Changing the repository or URLs later changes the bootstrap ZIP hash and requires another signed release.

## 4. Create and push the GitHub repository

Create an empty **public** GitHub repository. Do not initialize it with a README, `.gitignore`, or license because the workspace already contains project files.

Review the repository licensing before publication. The generated Kodi skin is based on Estuary and preserves its GPL files. The original bootstrap metadata currently declares MIT. Add the appropriate root license and third-party notices before making the repository public.

Then run:

```powershell
Set-Location $ProjectRoot
git init -b main
git add .
git commit -m 'Initial Kodi setup platform'
git remote add origin https://github.com/rjclark99/starlanemeridian.git
git push -u origin main
```

Alternatively, after the local commit:

```powershell
gh repo create rjclark99/starlanemeridian --public --source . --remote origin --push
```

In GitHub repository settings:

1. Enable GitHub Actions.
2. Under **Pages**, select deployment from the `main` branch and `/docs` folder. The Kodi repository will be committed under `docs/kodi`.
3. Under **Environments**, create an environment named `release`.
4. Add yourself as a required reviewer if your plan supports it. Environment secrets are withheld until approval.
5. Protect `main`: require the CI workflow, prevent force pushes, and require pull requests once the initial setup is complete.

## 5. Deploy the Cloudflare control API

### 5.1 Create D1

Authenticate Wrangler and create the database:

```powershell
Set-Location "$ProjectRoot\control-api"
pnpm exec wrangler login
pnpm exec wrangler d1 create kodi-setup-control
```

Copy the returned database UUID into `control-api/wrangler.toml`, replacing:

```text
REPLACE_WITH_D1_DATABASE_ID
```

Keep the binding name as `DB` and the database name as `kodi-setup-control`.

Apply the migration to the remote database:

```powershell
pnpm exec wrangler d1 migrations apply kodi-setup-control --remote
```

Deploy the Worker:

```powershell
pnpm exec wrangler deploy
```

### 5.2 Attach the final API domain

In Cloudflare **Workers & Pages → kodi-setup-control → Settings → Domains & Routes**, attach your final hostname, for example:

```text
kodi-control.example.com
```

Test the public health endpoint:

```powershell
Invoke-RestMethod https://kodi-control.example.com/health
```

The result should contain `status: ok`.

### 5.3 Protect only the administrator path

In Cloudflare Zero Trust:

1. Go to **Access controls → Applications**.
2. Create a self-hosted application.
3. Protect `kodi-control.example.com/v1/admin/*`, not the whole API hostname.
4. Add an **Allow** policy restricted to your administrator email/OIDC identity.
5. Create a service token under **Access controls → Service credentials → Service Tokens**.
6. Add a **Service Auth** policy that includes that specific service token.
7. Record the Client ID and Client Secret once; the secret is not displayed again.

Do not put Cloudflare Access in front of `/v1/devices/*` or `/health`. Device endpoints perform their own pairing-token and request-signature authentication.

Verify that an unauthenticated request is rejected:

```powershell
try { Invoke-RestMethod https://kodi-control.example.com/v1/admin/devices } catch { $_.Exception.Response.StatusCode }
```

Then test with the service token:

```powershell
$AccessHeaders = @{
  'CF-Access-Client-Id' = 'YOUR_CLIENT_ID'
  'CF-Access-Client-Secret' = 'YOUR_CLIENT_SECRET'
}
Invoke-RestMethod https://kodi-control.example.com/v1/admin/devices -Headers $AccessHeaders
```

## 6. Generate and back up signing keys

Create a local `.secrets` directory. It is ignored by Git.

```powershell
Set-Location $ProjectRoot
New-Item -ItemType Directory -Force .secrets | Out-Null
```

### 6.1 Manifest Ed25519 key

```powershell
python tools\release.py keygen `
  --private-key .secrets\manifest.key `
  --public-key config\manifest.pub
```

`manifest.key` is the private release key. `manifest.pub` is safe to embed and publish.

Make two encrypted offline backups of `manifest.key`. Anyone with this key can authorize configuration and APK changes for installed clients. Losing it means shipping a newly signed setup APK with a new embedded public key.

### 6.2 Android application signing key

Generate one long-lived keystore:

```powershell
keytool -genkeypair -v `
  -keystore .secrets\release.jks `
  -alias kodi-setup `
  -keyalg RSA `
  -keysize 4096 `
  -validity 10000
```

Use unique, strong keystore and key passwords. Back up the JKS and passwords offline. Every future update must use the same Android signing key or Android will refuse to install it over the existing app.

Never commit `.secrets`, a JKS, passwords, Cloudflare credentials, or a vault backup.

## 7. Create the project manifest

Copy the template:

```powershell
Copy-Item config\manifest.example.json config\manifest.json
```

Keep `stage` as `draft` while editing. Update `configVersion` whenever a released configuration changes. Use a monotonically increasing value such as `2026.07.1`, `2026.07.2`, and so on.

### 7.1 Verify official Kodi APKs

At the time this guide was written, Kodi 21.3 is the latest stable Android release and Kodi 22 is still beta. Always recheck the official Kodi directories and exclude alpha, beta, and RC builds.

Download both stable APKs directly from `mirrors.kodi.tv`:

```powershell
New-Item -ItemType Directory -Force build\vendor | Out-Null
Invoke-WebRequest 'https://mirrors.kodi.tv/releases/android/arm/kodi-21.3-Omega-armeabi-v7a.apk' -OutFile build\vendor\kodi-arm32.apk
Invoke-WebRequest 'https://mirrors.kodi.tv/releases/android/arm64-v8a/kodi-21.3-Omega-arm64-v8a.apk' -OutFile build\vendor\kodi-arm64.apk
Get-FileHash build\vendor\kodi-arm32.apk -Algorithm SHA256
Get-FileHash build\vendor\kodi-arm64.apk -Algorithm SHA256
```

Use Android Build Tools to inspect the package and signing certificate:

```powershell
apksigner verify --verbose --print-certs build\vendor\kodi-arm32.apk
apksigner verify --verbose --print-certs build\vendor\kodi-arm64.apk
```

Confirm:

- Verification succeeds.
- The package is `org.xbmc.kodi`.
- Both APKs have the expected Kodi signing identity.
- The `Signer #1 certificate SHA-256 digest` is copied into `signerSha256` in lowercase without separators.
- Each file SHA-256 is copied into the matching `sha256` field.

Do not calculate these values from an APK mirror, forum attachment, or file-sharing site.

### 7.2 Proton VPN configuration

The recommended first release leaves `applications[0].artifacts` empty. The setup app opens Amazon Appstore on Fire TV or Google Play on Android TV, which allows vendor-managed updates.

Be aware that Proton currently documents Android 8+ for its standard Android TV app, while its Amazon Appstore build supports Android 7.1+. Test old API 25 devices explicitly.

If a GitHub APK fallback is required:

1. Use only a release from `github.com/ProtonVPN/android-app`.
2. Select a stable, non-prerelease APK compatible with the target ABI and Android version.
3. Download it and run `Get-FileHash` and `apksigner verify --print-certs` as above.
4. Add one artifact per ABI with `abi`, official GitHub URL, file SHA-256, and signer SHA-256.
5. Install-test it before promoting the manifest.

Official sideloaded APKs do not update themselves, which is why the store remains preferred.

### 7.3 Third-party Kodi repositories and add-ons

Leave `repositories` and `addons` as empty arrays until you have an explicit allowlist and distribution permission.

For each approved repository:

1. Pin a specific GitHub Release asset URL in `source.resolvedUrl`.
2. Verify the ZIP hash independently.
3. Confirm its root directory and `addon.xml` ID exactly match `addonId`.
4. Add the repository record and SHA-256.

For each approved add-on:

1. Use its exact Kodi add-on ID.
2. Reference an existing repository record.
3. Put only documented, non-secret scalar settings in `settings`.
4. Use `authAdapter: "real-debrid-device-v1"` only when the add-on supports its own user-visible device authorization flow.

Passwords, API tokens, arbitrary Python, shell commands, arbitrary Kodi built-in strings, and unreviewed URLs must not be placed in the manifest.

### 7.4 Menu and widgets

Supported `kodi-window` targets are:

```text
videos, tvshows, movies, addons, settings, music, pictures, favourites
```

An `addon` action target must begin with `plugin.` or `script.`. Widget providers must be allowlisted `plugin://...` URLs and limits must be from 1 to 50.

## 8. Embed the manifest trust values in the Kodi bootstrap

This step is mandatory. Open:

```text
kodi/repository.kodisetup/resources/settings.xml
```

Replace the `manifest_url` default with:

```text
https://github.com/rjclark99/starlanemeridian/releases/latest/download/manifest.json
```

Replace the empty `public_key` default with the one-line value from:

```powershell
Get-Content config\manifest.pub
```

Commit these public values. Do not put the private manifest key in the add-on.

## 9. Build the branded skin and hosted Kodi repository

### 9.1 Obtain the matching Kodi source ZIP

Use the official `xbmc/xbmc` GitHub repository and select the tag matching the stable Kodi APK. Download the exact source ZIP once and record its SHA-256:

```powershell
Invoke-WebRequest 'https://github.com/xbmc/xbmc/archive/refs/tags/21.3-Omega.zip' -OutFile build\vendor\kodi-source.zip
Get-FileHash build\vendor\kodi-source.zip -Algorithm SHA256
```

Confirm the tag exists in the official Team Kodi repository before trusting it. Save both the source URL and hash; they are release workflow inputs.

### 9.2 Build the skin

```powershell
python tools\skin_builder.py `
  --upstream-archive build\vendor\kodi-source.zip `
  --manifest config\manifest.json `
  --output artifacts\skin `
  --version 1.1.0
```

The default 1.1.0 home order is Home, Search, TV Shows, Movies, Live TV, then Kids & Family. Search uses TMDb Helper when installed and otherwise Global Search; neither is required to render the home screen. Settings and Power remain separate utility controls beneath the content destinations.

### 9.3 Generate the GitHub Pages hierarchy

```powershell
python tools\release.py kodi `
  --output docs\kodi `
  --base-url https://rjclark99.github.io/starlanemeridian/kodi
```

Verify the generated bootstrap ZIP and calculate its hash:

```powershell
$BootstrapZip = 'docs\kodi\repository.kodisetup\repository.kodisetup-1.1.0.zip'
Get-FileHash $BootstrapZip -Algorithm SHA256
```

Update `config/manifest.json`:

- Set `bootstrap.url` to `https://github.com/rjclark99/starlanemeridian/releases/latest/download/repository.kodisetup-1.1.0.zip`.
- Set `bootstrap.sha256` to the generated ZIP hash.

Changing the embedded manifest URL, public key, repository base URL, or bootstrap add-on source changes this hash. Rebuild and recalculate it after any such change.

Commit the hosted repository:

```powershell
git add config\manifest.pub config\manifest.json kodi\repository.kodisetup\resources\settings.xml docs\kodi
git commit -m 'Configure release trust and Kodi repository'
git push
```

After GitHub Pages deploys, confirm these return HTTP 200:

```text
https://rjclark99.github.io/starlanemeridian/kodi/addons.xml
https://rjclark99.github.io/starlanemeridian/kodi/addons.xml.sha256
https://rjclark99.github.io/starlanemeridian/kodi/repository.kodisetup/repository.kodisetup-1.1.0.zip
```

## 10. Validate and stage the manifest

Run:

```powershell
python tools\release.py validate config\manifest.json
```

For the first controlled household test, set `stage` to `test`. Once physical-device acceptance passes, change it to `stable` and increment `configVersion` if the payload changed.

Sign `config/manifest.json` only on the trusted owner workstation. The supplied release
workflow verifies the committed signature and refuses a stable manifest containing
placeholder hashes, `example.invalid`, or `OWNER/REPOSITORY`.

## 11. Add GitHub release secrets

Create these as secrets in the GitHub `release` environment:

| Secret | Value |
| --- | --- |
| `ANDROID_KEYSTORE_BASE64` | Base64 of `.secrets/release.jks` |
| `ANDROID_STORE_PASSWORD` | JKS store password |
| `ANDROID_KEY_ALIAS` | `kodi-setup` unless you selected another alias |
| `ANDROID_KEY_PASSWORD` | Key password |
| `PUBLIC_MANIFEST_URL` | Latest-release `manifest.json` URL |
| `MANIFEST_PUBLIC_KEY` | One-line contents of `config/manifest.pub` |
| `CONTROL_API_URL` | Final HTTPS control API base URL |

Sign `config/manifest.json` offline before committing it. The release workflow verifies
that signature against the committed public key and deliberately has no access to the
manifest private key.

With GitHub CLI authenticated, the Android signing keystore can be uploaded without
writing another plaintext copy:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes((Resolve-Path '.secrets\release.jks'))) |
  gh secret set ANDROID_KEYSTORE_BASE64 --env release

Get-Content config\manifest.pub -Raw |
  gh secret set MANIFEST_PUBLIC_KEY --env release
```

Add password and URL secrets using GitHub's masked prompt or repository web interface. Never place them in a command committed to shell history.

Confirm GitHub can see all seven names before running a release:

```powershell
gh secret list --env release
```

The values remain masked. If a workflow log shows any of these environment variables
as blank, stop: an empty keystore can produce a misleading Android `KeytoolException`.
Do not regenerate or replace the established signing key merely to clear that error.

## 12. Run the first signed release

Before starting the workflow, commit and push the final manifest and confirm CI is green.

In GitHub:

1. Open **Actions → Signed release → Run workflow**.
2. Enter a tag such as `v0.1.0-test` for household testing or `v1.0.0` for the first stable release.
3. Set `repositoryBaseUrl` to the GitHub Pages Kodi URL.
4. Set `kodiSourceUrl` to the exact reviewed Kodi source ZIP URL.
5. Set `kodiSourceSha256` to its verified SHA-256.
6. Start the workflow and approve the `release` environment deployment.

The workflow builds and publishes:

- `setup.apk`
- `KodiSetup.Admin-win-x64.zip`
- `repository.kodisetup-1.1.0.zip`
- branded skin and Kodi repository artifacts
- signed `manifest.json`
- `SHA256SUMS`
- SPDX SBOM

On the GitHub Release page, verify all required assets exist. Download `setup.apk`, the bootstrap ZIP, `manifest.json`, and `SHA256SUMS`; verify their hashes before installing anything.

Confirm the permanent URLs:

```powershell
Invoke-WebRequest 'https://github.com/rjclark99/starlanemeridian/releases/latest/download/setup.apk' -Method Head
Invoke-WebRequest 'https://github.com/rjclark99/starlanemeridian/releases/latest/download/manifest.json' -Method Head
Invoke-WebRequest 'https://github.com/rjclark99/starlanemeridian/releases/latest/download/repository.kodisetup-1.1.0.zip' -Method Head
```

GitHub's `/releases/latest/download/<asset>` URL follows the latest non-prerelease release. If you mark the release as a prerelease, it will not become the `/latest` target.

## 13. Configure the Windows administration portal

Download and extract `KodiSetup.Admin-win-x64.zip` to a directory writable only by your Windows user.

Edit the extracted `appsettings.json`:

```json
{
  "Urls": "http://127.0.0.1:54731",
  "AdbPath": "C:\\Users\\YOUR_NAME\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe",
  "ControlApi": {
    "BaseUrl": "https://kodi-control.example.com",
    "AccessClientId": "YOUR_CLOUDFLARE_ACCESS_CLIENT_ID",
    "AccessClientSecret": "YOUR_CLOUDFLARE_ACCESS_CLIENT_SECRET"
  },
  "Vault": {
    "AutoLockMinutes": 15,
    "ClipboardClearSeconds": 60
  },
  "AllowedHosts": "127.0.0.1;localhost"
}
```

Protect this folder because the Access service token is stored in this local file. Restrict its Windows ACL to your account.

Start `KodiSetup.Admin.exe`, then open:

```text
http://127.0.0.1:54731
```

Create a vault with a unique master password of at least 14 characters. Export an encrypted backup and test that you can unlock it before recording real household data. There is no recovery backdoor.

The current backup remains bound to the same Windows user profile through DPAPI. To restore it on that profile, stop the portal and place the exported file at:

```text
%LOCALAPPDATA%\KodiSetupAdmin\households.vault
```

There is currently no cross-machine or cross-profile restore path. Keep an additional offline record of essential household account ownership information rather than treating the vault as the only record.

For each household:

1. Let the household user open the official provider site.
2. Let them accept terms, CAPTCHA, verification, and ownership prompts.
3. Enter payment only on the provider's official page.
4. If they explicitly consent, save credentials in the local vault.
5. Record consent and account handoff.
6. Never share a Real-Debrid account between households.

## 14. Create the Downloader code

Use this exact public URL:

```text
https://github.com/rjclark99/starlanemeridian/releases/latest/download/setup.apk
```

The current verified public Downloader code is `3467018` (`https://aftv.news/3467018`). It resolves to the permanent URL above.

Test the code on a clean Fire TV. Treat the code as public; it must never resolve to a URL containing credentials or tokens.

Regenerate the code only if the permanent URL changes. Normal releases keep the filename `setup.apk`, so the same code should continue to resolve to the newest release.

## 15. Test the Downloader/guided installation path

On a clean Fire TV:

1. Install Downloader from the Amazon Appstore.
2. Allow Downloader to install unknown apps when Fire OS prompts.
3. Enter the Downloader code.
4. Confirm the URL is your GitHub repository before downloading.
5. Install `setup.apk` through the Android system dialog.
6. Open Kodi Setup and enter the one-time code created in the Windows portal.
7. Allow Kodi Setup to install unknown apps when prompted.
8. Install Kodi and confirm the Android installer result.
9. Install Proton VPN from Amazon Appstore; sign in using Proton's official TV code/QR flow.
10. Select **Prepare Kodi bootstrap**.
11. Open Kodi and enable **Settings → System → Add-ons → Unknown sources**.
12. Use **Install from ZIP file**, open Downloads, and select `repository.kodisetup.zip`.
13. Wait for the service bootstrap to install the configured skin and allowed add-ons.
14. Complete Real-Debrid's official device-code flow if desired.
15. Confirm the portal receives only setup state, versions, errors, last-seen time, and subscription expiry.

Android and Kodi confirmations are mandatory and should not be bypassed.

## 16. Test the managed ADB path

On Fire TV, manually reveal Developer Options by selecting the device name under **Settings → My Fire TV → About** seven times. Enable ADB debugging and approve the Windows computer on the TV.

In the Windows portal:

1. Open **Devices & ADB**.
2. Enter the TV IP address.
3. Select **Connect** and accept the fingerprint on the TV.
4. Select the downloaded `setup.apk` and choose **Install setup APK**.
5. Install Kodi through the TV workflow.
6. Select the verified `repository.kodisetup-1.1.0.zip` and choose **Deploy bootstrap**.

The portal probes Kodi's external add-on directory. When it is writable, the repository/service is pushed directly. Otherwise, the ZIP is copied to Downloads and you must complete the guided Kodi installation.

Disable ADB debugging after setup if ongoing managed access is unnecessary.

## 17. Acceptance checklist

Do not call the release stable until all applicable items pass:

- [ ] CI passes on the release commit.
- [ ] GitHub Pages serves `addons.xml`, checksum, skin, and bootstrap ZIP over HTTPS.
- [ ] The release contains `setup.apk`, signed manifest, Windows portal, checksums, and SBOM.
- [ ] APK and manifest URLs work through `/releases/latest/download/...`.
- [ ] `setup.apk` is signed with the backed-up production keystore.
- [ ] Manifest signature validation succeeds.
- [ ] ARM32 and ARM64 Kodi downloads pass file, package, and signer validation.
- [ ] No beta, RC, or unofficial vendor artifact is selected automatically.
- [ ] Store installation works for Proton on supported Fire TV and Android TV devices.
- [ ] Any Proton GitHub fallback is official and independently verified.
- [ ] Pairing codes expire and cannot be reused.
- [ ] Cloudflare Access rejects unauthenticated administrator requests.
- [ ] Device status and commands work after pairing.
- [ ] Guided Downloader setup works using only remote control input.
- [ ] ADB direct deployment and Downloads fallback both work.
- [ ] Kodi bootstrap is idempotent when Kodi restarts.
- [ ] Required add-on failures appear in the TV and portal workflows.
- [ ] Skin failure leaves a usable route back to Kodi's default skin.
- [ ] Real-Debrid authorization succeeds without transmitting the token to the cloud.
- [ ] No credentials, OAuth tokens, payment data, or Kodi viewing history appear in logs.
- [ ] Vault auto-lock, failed-attempt throttling, clipboard clearing, export, and same-profile restore are tested.
- [ ] Each household has explicitly accepted provider terms and owns its accounts.

## 18. Routine updates

The weekly vendor monitor creates a review PR containing discovery data only. It does not update the signed manifest. In **Settings → Actions → General → Workflow permissions**, enable **Allow GitHub Actions to create and approve pull requests**; without it, candidate discovery succeeds but the final PR step is rejected by GitHub.

For every Kodi or Proton update:

1. Review the vendor candidate PR.
2. Confirm the release is stable.
3. Download from the official vendor location.
4. Recalculate SHA-256.
5. Recheck package name, signer certificate, ABI, and minimum Android version.
6. Test installation and upgrade on real devices.
7. Update URLs and hashes in `config/manifest.json`.
8. Increment `configVersion`.
9. If the Kodi source or menus changed, bump the skin version, rebuild `docs/kodi`, and publish it before the manifest.
10. If the bootstrap source, manifest URL, public key, or repository base changed, rebuild it and update `bootstrap.sha256`.
11. Promote through `test`, then `stable`.
12. Run the signed release workflow with a new semantic version tag.

Never replace the Android keystore for an update. Rotate the manifest key only through a setup-app update that embeds the new public key.

## 19. Revocation and incident response

If a configuration is unsafe but the manifest key remains secure:

1. Stop promoting releases.
2. Create and sign a manifest with `stage: revoked` for the affected release.
3. Publish it at the permanent manifest URL.
4. Correct the issue, increment `configVersion`, test, and publish a new stable manifest.

If the manifest private key is compromised:

1. Remove affected releases and revoke GitHub/Cloudflare credentials.
2. Generate a new Ed25519 keypair.
3. Build a new setup APK embedding the new public key.
4. Sign it with the existing Android keystore so installed clients can upgrade.
5. Publish a security notice without exposing secrets.

If the Android keystore is lost, existing installations cannot accept a normally signed update from a replacement key. Restore it from the offline backup or require uninstall/reinstall under a new application identity.

If a Cloudflare service token is exposed, revoke it, create a replacement, and update the Windows portal's `appsettings.json` immediately.

## Official references

- GitHub repository creation: https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository
- GitHub latest-release asset URLs: https://docs.github.com/en/repositories/releasing-projects-on-github/linking-to-releases
- GitHub deployment environments: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- Android application signing: https://developer.android.com/studio/publish/app-signing
- Cloudflare D1 setup: https://developers.cloudflare.com/d1/get-started/
- Cloudflare D1 migrations: https://developers.cloudflare.com/d1/reference/migrations/
- Cloudflare Access service tokens: https://developers.cloudflare.com/cloudflare-one/access-controls/service-credentials/service-tokens/
- Cloudflare Access application paths: https://developers.cloudflare.com/cloudflare-one/access-controls/policies/app-paths/
- Kodi Android downloads: https://mirrors.kodi.tv/releases/android/
- Proton VPN on Android TV: https://protonvpn.com/support/android-tv
- Proton VPN APK installation: https://protonvpn.com/support/how-to-install-the-protonvpn-apk
- Real-Debrid API and device OAuth: https://api.real-debrid.com/
- AFTVnews Downloader code generator: https://go.aftvnews.com/

# Kodi Setup Platform

A remote-friendly Android TV / Fire TV provisioning platform consisting of:

- `android-app/` — the sideloaded setup APK.
- `admin-portal/` — a Windows-local administration portal and encrypted credential vault.
- `control-api/` — a Cloudflare Worker + D1 device control plane.
- `kodi/` — a Kodi bootstrap/repository add-on and branded skin.
- `config/` — the signed, versioned setup-manifest schema and safe example configuration.
- `tools/` — release, repository, skin-menu, signing, and validation utilities.

The project deliberately does **not** silently enable Android developer options, bypass installer confirmation, automate account registration/CAPTCHA, collect payment-card data, expose a remote shell, or upload account credentials. Those boundaries are enforced in code and documented in [SECURITY.md](SECURITY.md).

## Quick start

1. Copy `config/manifest.example.json` to `config/manifest.json` and replace placeholder artifact URLs, hashes, signer fingerprints, repository IDs, and branding.
2. Generate an Ed25519 release key and sign the manifest:

   ```powershell
   python tools/release.py keygen --private-key .secrets/manifest.key --public-key config/manifest.pub
   python tools/release.py validate config/manifest.json
   python tools/release.py sign config/manifest.json --private-key .secrets/manifest.key
   ```

3. Build Kodi artifacts with `python tools/release.py kodi --output artifacts/kodi`.
4. Build the Android app with Gradle from `android-app/` after setting its manifest URL/public key.
5. Run the Windows portal with `dotnet run --project admin-portal/KodiSetup.Admin.csproj`.
6. Deploy the control API after creating D1 and configuring `control-api/wrangler.toml`.

Start with [docs/OWNER_SETUP_GUIDE.md](docs/OWNER_SETUP_GUIDE.md) for the complete owner checklist, then use [docs/OPERATIONS.md](docs/OPERATIONS.md) as the shorter day-to-day reference.

## Current safe defaults

- Kodi uses the stable channel only.
- Proton VPN prefers the platform store; GitHub APK fallback is disabled until a reviewed artifact is entered.
- Third-party Kodi repositories and add-ons are empty placeholders.
- Telemetry is limited to setup state and version/expiry metadata.
- Diagnostics require explicit device consent.

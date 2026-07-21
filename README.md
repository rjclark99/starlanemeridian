# Starlane Meridian

A remote-friendly Android TV / Fire TV provisioning platform:

- `android-app/` - the sideloaded setup APK.
- `admin-portal/` - a Windows-local administration portal and encrypted credential vault.
- `control-api/` - a Cloudflare Worker + D1 device control plane.
- `kodi/` - the Kodi bootstrap/repository service and custom-skin source.
- `config/` - the signed, versioned setup-manifest schema.
- `profiles/` - the safe reference-TV profile workflow.
- `tools/` - release, profile, repository, skin, signing, and validation utilities.

The project does not silently enable Android developer options, bypass installer
confirmation, automate account registration/CAPTCHA, collect payment-card data,
expose a remote shell, or upload account credentials. Those boundaries are
enforced in code and documented in [SECURITY.md](SECURITY.md).

## Release outline

1. Validate and sign the reviewed manifest:

   ```powershell
   python tools/release.py validate config/manifest.json
   python tools/release.py sign config/manifest.json --private-key .secrets/manifest.key
   ```

2. Build Kodi artifacts:

   ```powershell
   python tools/release.py kodi --output artifacts/kodi --base-url https://github.com/rjclark99/starlanemeridian/releases/latest/download
   ```

3. Build the Android app with the production manifest URL, public key, control URL,
   and signing keystore.
4. Run the Windows portal with `dotnet run --project admin-portal/KodiSetup.Admin.csproj`.
5. Deploy the control API from `control-api/` with `pnpm deploy`.

Use [docs/OWNER_SETUP_GUIDE.md](docs/OWNER_SETUP_GUIDE.md) for the full checklist,
[docs/OPERATIONS.md](docs/OPERATIONS.md) for routine operations, and
[docs/CURRENT_STATUS.md](docs/CURRENT_STATUS.md) for the verified deployment state.

## Current safe defaults

- Kodi uses the stable channel only.
- Proton VPN prefers the platform store; GitHub fallback is disabled until reviewed.
- Third-party Kodi repositories and add-ons remain empty until legally allowlisted.
- Telemetry is limited to allowlisted device facts, setup progress, app/configuration versions, and subscription-expiry status.
- Diagnostics require explicit device consent.
- The signed manifest packages `skin.starlanemeridian`; Bootstrap 1.1.0 restores the previous skin or Estuary if activation fails.

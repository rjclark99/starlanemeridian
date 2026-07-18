# Operations guide

## Release keys

Keep the Android signing key, manifest Ed25519 private key, Cloudflare credentials, and admin vault outside the repository. The app embeds only the manifest public key. A lost manifest key is handled by shipping a new app release containing a new public key; it cannot be recovered remotely.

## Manifest promotion

1. Edit a `draft` manifest and validate it.
2. Replace every zero/placeholder hash and signer fingerprint with values measured from vendor-authentic artifacts.
3. Promote to `test`, sign, and exercise on physical ARM32 and ARM64 devices.
4. Promote the identical reviewed payload to `stable`, increment `configVersion`, sign, and publish.
5. Mark a compromised configuration `revoked`; clients retain the last verified non-revoked manifest.

The signature covers canonical JSON with `signature.value` set to an empty string.

## Branded skin build

Download a reviewed Kodi source release archive corresponding to the supported stable Kodi release and verify its published source provenance. Then run:

`python tools/skin_builder.py --upstream-archive kodi-source.zip --manifest config/manifest.json --output artifacts/skin`

The builder copies the complete upstream Estuary skin (including its GPL license and all fallback windows), changes its add-on identity, and generates a constrained Home screen from the manifest. Build the Kodi repository only after the skin artifact exists.

## Fire TV managed setup

1. On Fire TV, reveal Developer Options if necessary by selecting **Settings → My Fire TV → About → device name** seven times.
2. Enable **ADB debugging** and approve the Windows computer when prompted.
3. In the Windows portal, enter the Fire TV IP, connect, and confirm the fingerprint on the TV.
4. Use **Install setup APK**, complete Kodi installation, then select the built `repository.kodisetup` ZIP and use **Deploy bootstrap**.
5. The portal probes Kodi's external add-on directory and deploys directly when writable. If scoped storage blocks it, the ZIP is copied to Downloads and the TV app shows the guided Kodi steps.

No component attempts to enable Developer Options or approve ADB on the user's behalf.

## Downloader release

Publish an asset named `setup.apk`. Point a single AFTVnews code to:

`https://github.com/rjclark99/starlanemeridian/releases/latest/download/setup.apk`

AFTVnews codes and target URLs are public. Do not encode credentials or private tokens in that URL.

## Hosted API

Create a D1 database, apply `control-api/migrations/0001_initial.sql`, replace the placeholder ID in `wrangler.toml`, and configure Cloudflare Access to protect `/v1/admin/*` before exposing the Worker. Put a Cloudflare Access service-token ID and secret in the Windows portal's local `appsettings.json`; never commit them. Device endpoints remain public but require pairing codes or signed requests.

## Credential vault

The Windows portal binds to loopback only. Create a strong master password and store an encrypted backup separately. There is no password-recovery bypass. Payment data must never be typed into or pasted into the portal.

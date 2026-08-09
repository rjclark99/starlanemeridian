---
id: current.public-release-state
kind: current
status: active
verified_at: 2026-08-08
tags: [release, manifest, github]
authority: [github-release, downloaded-bytes, config/manifest.json]
supersedes: []
---

# Public release state

`v0.5.10-test` was created by successful signed-release run `31280750978` from `main`
at `42a7cb2`, independently verified as a draft, and published as the GitHub **Latest**
full release on 8 August 2026 with explicit owner approval. No asset was rebuilt or
replaced during publication.

All 14 draft assets were downloaded and independently verified before publication on
8 August 2026. The
LF-only `SHA256SUMS` names all 13 other assets exactly once with no duplicates, no
missing uploads, no unlisted uploads, and every digest matching. All five `.sha256`
sidecars are LF-only and correct. Manifest `2026.08.42` is test-stage, verifies against
`config/manifest.pub`, declares minimum setup app code 11, and selects Bootstrap 1.1.17
digest `f28f45bb29ef4c6d79cd6f8f5246806d5ae223a9bc5332c5c87e2726702be2b8`, which matches
the uploaded archive. The SBOM is valid SPDX JSON with 185 packages and contains no
owner-panel, vault, or private-runtime paths.

The branded provider 6.7.81.4 digest is
`512d2ba29e4ffc64ad62492f8a7a948ba55a2c16af9dff5ec75025c1c264aaf8`, **byte-identical to
the Windows-built local candidate**, which clears the
`incident.cross-platform-zip-metadata` risk for this archive with direct evidence. The
private skin 2.2.22 digest is unchanged at
`2342155764da3cbf8ad3d0cafa1df5c01629011f542f138f12ea316bbb798a2c`. Setup APK identity is
package `app.kodisetup.tv`, versionName `0.5.10`, versionCode 11, Android signature scheme
v2 only, and production signer
`e82233eb034643f9d3e6357a74348c8900d25e28f13b694e9bdee53d9ad2828c`, matching every prior
release.

Two observations that are not defects. The published `manifest.json` is LF-only (7570
bytes) while the repository copy is CRLF (7816 bytes) because `release.py sign` writes
through Windows text mode; the two are identical after newline normalisation and both
verify, since the signature covers canonical JSON rather than raw bytes. The production
skin advanced to `skin.starlanemeridian` 1.3.0, built by CI from the reviewed Kodi source
ZIP; it is published for rollback only and is deliberately absent from the signed package
lock, so no hash contract covers it.

After publication, the public `latest/download` manifest reports configuration
`2026.08.42`, minimum app code 11, and Bootstrap 1.1.17 with the expected digest. The
public APK and Bootstrap routes return their expected assets, and
`tools/verify_kodi_package_lock.py` checked all 38 selected ARMv7 packages with zero
failures.
The lock's private-skin entry still points at the `v0.5.9-test` tag; those bytes are
unchanged so it resolves and hashes correctly today, but the new release also carries the
same archive and pointing at the current tag would remove the cross-release dependency.

Owner-approved `v0.5.9-test` is the previous GitHub full release and was built
by successful signed-release run `31273093709` from source `da26ba0`. It was first
published as a pre-release and then promoted to Latest on 8 August 2026 with the owner's
explicit approval; no rebuild or release-asset replacement occurred during promotion, and
the `latest/download` routes for `manifest.json`, `setup.apk`, and
`repository.kodisetup-1.1.16.zip` were re-checked afterwards and resolve to it.
All 14 public files were downloaded after
publication. The LF-only `SHA256SUMS` names all 13 other assets exactly once and every
digest matches. Manifest `2026.08.41` is test-stage, verifies against
`config/manifest.pub`, and selects Bootstrap 1.1.16 digest
`72270e8c611e4686322f45ac7e9922089346b6d2c21f6812f7ab2d3119beb6bb`.
The private skin 2.2.22 digest is
`2342155764da3cbf8ad3d0cafa1df5c01629011f542f138f12ea316bbb798a2c`;
the branded provider 6.7.81.3 digest is
`a81eb2bcdb10c97ebf53193753080cc4c917ece7ffcb3e920daac7a19830fb38`.
All four Kodi roots, IDs, versions, and sidecars pass, and the locked packages use the
intended stored-entry format. The SBOM is valid SPDX JSON with 185 packages and contains
no owner-panel, vault, or private-runtime paths. Setup APK digest
`81188caa8b345fa383ed584ce947f64b0eab65d5889ea5d0cfaf69c608311a18`
verifies with Android signature scheme v2, package `app.kodisetup.tv`, version `0.5.9`,
code 10, and production signer
`e82233eb034643f9d3e6357a74348c8900d25e28f13b694e9bdee53d9ad2828c`.
A fresh-device acceptance attempt against these public bytes ran on 8 August 2026 and did
not pass. Configuration `2026.08.41` was applied and the Home menu was generated, but
four defects were found and are fixed in source for the next release: Bootstrap reported
`Setup finished with 2 issue(s)` on every first run because provider readiness could not
appear on the installing launch; a freeze at Kodi's keep-skin dialog left configuration
marked applied with the skin rolled back and no retry path; the setup app could not read
Kodi's JSON-RPC at all; and network/provider logos resolved to region-blocked
third-party hosts. Acceptance steps 4 to 7 remain unverified. See
`incident.provider-service-readiness`, `incident.unconfirmed-skin-activation`, and
`incident.region-blocked-logo-hosts`.
Downloader code `7499455` remains pinned to the superseded tagged
`v0.5.9-test/setup.apk` asset. Code `3467018` is the previously generated reusable
Latest installer code rather than a new post-7499455 code. Live inspection on 9 August
confirmed that it follows the current `latest` route and now serves v0.5.10/code 11.

The v0.5.11 acceptance-recovery work on 9 August remains local. Its configuration
`2026.08.43` is offline-signed and verified, and exact release-form Kodi packages plus a
production-signed APK pass local validation. A bounded existing-device candidate pass
succeeded, but no clean installation from prerelease bytes has occurred. `v0.5.10-test`
remains GitHub Latest; `v0.5.11-test` has not been created or uploaded, and no public
release or Latest mutation has occurred.

Owner-approved `v0.5.8-test` was the latest public release until the 8 August promotion
and targets source commit
`3c99980`. Its signed manifest is `2026.07.37`, SHA-256
`810298f27d1550cc3fe54e91bdf9f714edac1390f123537a1126e8bf41ef3fec`.
Bootstrap 1.1.13 is
`e51a3270e5e5a4a3cae1b241eab8950e3eade0a7a69cfacaff6c06b833c5fe35`;
setup APK 0.5.3/code 8 is
`357fff753fb160565fccf6482626bc7209fdd8a636303128b370b11f95afa41b`
with production signer
`e82233eb034643f9d3e6357a74348c8900d25e28f13b694e9bdee53d9ad2828c`.
All 15 uploaded assets matched the LF-only checksum inventory where listed; all four
Kodi sidecars and ZIP roots passed; the manifest signature passed; and the manifest,
Bootstrap, and APK `latest/download` routes matched the tagged assets byte-for-byte.
`v0.5.6-test` and `v0.5.7-test` remain public superseded evidence and must not be used
because their Bootstrap bytes did not match their signed manifests.

Former owner-approved `v0.5.5-test` targeted combined source
commit `d4c96cb`. All 31 draft assets matched the release candidate before publication,
and all 31 public assets matched after publication. The signed manifest is
`2026.07.33` (SHA-256
`2b1029372d3d3943eab352784d57db4365c97b859e75724ded0d422427e7caba`);
Bootstrap 1.1.12 is
`fc33f0d66e5467666f55e9153a77a3a033956a73e9863c4465efbc8567152f5f`;
and branded provider 6.7.81.2 is
`3ff6402f0d4427b7ec0fa6d28bb235d5f10a4b5bc9515021aa1c3cf3ccc65810`.
The setup APK is 0.5.2/code 7, SHA-256
`2d384f691b086737baf65b8b7ab3a5a04aee1135a2dfd8d0c943ff4f6f4ea3af`,
with production signer SHA-256
`e82233eb034643f9d3e6357a74348c8900d25e28f13b694e9bdee53d9ad2828c`.
The LF-only checksum inventory, manifest signature, APK identity/signature, ZIP
structure, GitHub `latest` routes, public health endpoint, and exact Worker provider
route passed. `v0.5.4-test` remains public as rollback evidence but is superseded
because its Bootstrap/provider sequence failed on the reference Fire TV.

Former owner-approved release `v0.5.2-test` targets `main` at `30735ab` and was
previously GitHub's non-prerelease `latest` release. Its permanent routes served
setup app 0.5.0/code 5, Bootstrap 1.1.5, signed manifest `2026.07.30`, and
`skin.starlane.movies` 2.2.20. The APK SHA-256 is
`85e10e2583c591df40babaa52458b3bc0e5cb9ef6f235ce9128132f785d3857a`
and its signer SHA-256 remains
`e82233eb034643f9d3e6357a74348c8900d25e28f13b694e9bdee53d9ad2828c`.
The portal ZIP SHA-256 is
`a9a49217a52341cf26adc77d9ff916f0be1de183eaee44639a6eed0715f2e686`.

This is legacy public-release evidence only. The 8 August source candidate removes
owner administration tooling from the client tree and future release workflow, but it
does not retroactively delete assets from existing GitHub releases. Removing a legacy
public asset is a separate owner-authorised publication mutation and remains pending.

All 27 draft assets were downloaded and matched the candidate byte-for-byte before
publication. All 27 public tag assets were downloaded again after promotion and
matched. The permanent setup APK, manifest, Bootstrap 1.1.5, and private-skin routes
also matched the candidate. `SHA256SUMS` is LF-only, the public manifest signature
verifies against `config/manifest.pub`, public health returned 200, and the allowlisted
Bootstrap and private-skin control routes returned 200.

The manifest SHA-256 is
`3c756dc8823a3dcc97d811d5da77c9cd984a4b93517923550f8f41421526a756`;
Bootstrap 1.1.5 is
`66598cbd5c14019d15b76f7c8b1b201c796d9cb6ce8ab623287c8a5754597b42`;
and the private skin is
`02d3bd72326b9b6300d3cfd97647c16f7cbf1ac39bdddbe376b124bbd0eea84e`.
Bootstrap retains production skin 1.2.4 and older production skin assets for rollback.
The 0.5.2 manifest-only hotfix replaces an Android-rejected `raw.githubusercontent.com`
dependency URL with GitHub's accepted commit-pinned `/raw/` form. The dependency
bytes and expected SHA-256 are unchanged.

Owner-approved experimental prerelease `skin-starlane-movies-2.2.20` publishes the
complete GPL-attributed `skin.starlane.movies` 2.2.20 add-on source as an installable
ZIP. Its SHA-256 is
`02d3bd72326b9b6300d3cfd97647c16f7cbf1ac39bdddbe376b124bbd0eea84e`.
The ZIP and LF-only checksum sidecar were downloaded before and after publication and
matched the candidate bytes. The later `v0.5.2-test` promotion now carries the same
approved skin bytes in the signed test-stage Bootstrap chain.

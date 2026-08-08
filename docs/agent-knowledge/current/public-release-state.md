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

Owner-approved `v0.5.9-test` is the newest public **pre-release** and was built by
successful signed-release run `31273093709` from source `da26ba0`; it was deliberately
not promoted to GitHub's stable/latest label. All 14 public files were downloaded after
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
No fresh-device acceptance has yet been performed against these public bytes.

Owner-approved `v0.5.8-test` is the latest public release and targets source commit
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

---
id: current.public-release-state
kind: current
status: active
verified_at: 2026-07-29
tags: [release, manifest, github]
authority: [github-release, downloaded-bytes, config/manifest.json]
supersedes: []
---

# Public release state

Owner-approved `v0.5.5-test` is the latest public release and targets combined source
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

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

Owner-approved release `v0.5.1-test` targets `main` at `a7bb9b0` and is GitHub's
non-prerelease `latest` release. Permanent `/releases/latest/download/...` routes now
serve setup app 0.5.0/code 5, Bootstrap 1.1.5, signed manifest `2026.07.29`, and
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
`f238ecda5d9d2b477fd0a01e327366fe878e9aba447d44b08889ec660429c9d3`;
Bootstrap 1.1.5 is
`66598cbd5c14019d15b76f7c8b1b201c796d9cb6ce8ab623287c8a5754597b42`;
and the private skin is
`02d3bd72326b9b6300d3cfd97647c16f7cbf1ac39bdddbe376b124bbd0eea84e`.
Bootstrap retains production skin 1.2.4 and older production skin assets for rollback.

Owner-approved experimental prerelease `skin-starlane-movies-2.2.20` publishes the
complete GPL-attributed `skin.starlane.movies` 2.2.20 add-on source as an installable
ZIP. Its SHA-256 is
`02d3bd72326b9b6300d3cfd97647c16f7cbf1ac39bdddbe376b124bbd0eea84e`.
The ZIP and LF-only checksum sidecar were downloaded before and after publication and
matched the candidate bytes. The later `v0.5.1-test` promotion now carries the same
approved skin bytes in the signed test-stage Bootstrap chain.

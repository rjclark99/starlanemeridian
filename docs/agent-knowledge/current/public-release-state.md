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

Public prerelease `v0.5.0-test` targets `main` at `909b8ee` and contains setup app
0.5.0/code 5 plus the updated self-contained Windows portal. The APK SHA-256 is
`85e10e2583c591df40babaa52458b3bc0e5cb9ef6f235ce9128132f785d3857a`
and its signer SHA-256 remains
`e82233eb034643f9d3e6357a74348c8900d25e28f13b694e9bdee53d9ad2828c`.
The portal ZIP SHA-256 is
`a9a49217a52341cf26adc77d9ff916f0be1de183eaee44639a6eed0715f2e686`.

All 23 draft assets were downloaded and matched the candidate byte-for-byte before
publication. The public setup APK, portal ZIP, manifest, checksum inventory, and SPDX
SBOM were then downloaded by tag URL and matched again. `SHA256SUMS` is LF-only and
verified; the SPDX 2.2 SBOM records 222 packages.

The signed manifest remains the verified `2026.07.11` test manifest, and Bootstrap
1.1.3 plus production skin assets through 1.2.4 were carried forward unchanged from
`v0.3.8-test`. The new release is deliberately a prerelease: `v0.3.8-test` remains
GitHub's non-prerelease `latest` target, so permanent `/latest/download` routes were
not promoted without separate owner approval.

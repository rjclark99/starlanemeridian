---
id: incident.draft-checksum-inventory
kind: incident
status: active
verified_at: 2026-08-08
tags: [release, github-actions, checksums, draft]
authority: [GitHub draft v0.5.9-test, downloaded draft assets, .github/workflows/release.yml]
supersedes: []
---

# Draft checksum inventory included unpublished build inputs

## Symptom

The first unpublished `v0.5.9-test` draft contained 14 client assets, but its
`SHA256SUMS` named `artifacts/kodi-source.zip` and a duplicate intermediate skin ZIP,
neither of which was uploaded. The uploaded signed `manifest.json` had no inventory
entry.

## Root cause

The workflow hashed every file below `artifacts/`, including build inputs and
intermediate output, while uploading only selected root files and the Kodi repository
tree. It uploaded the manifest directly from `config/`, outside the hashed directory.

## Resolution and durable rule

Commit `0acb758` stages the manifest with the release assets and generates checksums
from an explicit allowlist: setup APK, signed manifest, SBOM, and every Kodi repository
file. Inventory names match GitHub's flattened release names, duplicate basenames are
rejected, and output is LF-only. Release tests cover exclusion of build inputs,
inclusion of every required published file, digest accuracy, and collision rejection.

Never publish or device-test a draft unless every non-inventory release asset appears
exactly once in `SHA256SUMS` and every listed name is downloadable from that draft.

# Widget and one-run automation readiness

## Local candidate completed

- The Home renderer has a bounded terminal **Show more** action for movie, TV,
  discovery, genre, network, and provider rows. Continue Watching remains a complete
  local queue without a misleading terminal action.
- The pinned provider overlay keeps its complete network directory, orders major
  channels first, and expands provider originals to Netflix, Amazon, Apple TV+,
  Disney+, Max, Hulu, Paramount+, and Peacock.
- Home artwork now resolves TV posters and a local missing-art fallback; the terminal
  card is local, 2:3, focusable, and does not populate unrelated hero details.
- Android presents one Cancel-first, one-run security consent after installation. It
  automates verified downloads, preparation, export, launch, and stateful resume. It
  cannot and does not bypass Android installer or Kodi trust confirmations.
- Kodi Bootstrap authorization is separately bound to the exact verified scope, can be
  revoked locally, and records completion only after every required step succeeds.

## Validation completed

- GitHub main `7d56f57` passed GitHub Actions run `31270686136` across
  configuration/Kodi, control-service, and Android jobs.
- The offline signature on local manifest `2026.08.39` verifies against the checked-in
  public key, and its Bootstrap digest matches deterministic Bootstrap 1.1.16 bytes.
- Project-control schemas, authority gates, release regressions, package-lock checks,
  Python compilation, Kodi tooling, Android unit tests, and Android lint pass.
- A clean archived checkout built without the removed owner panel or its private
  runtime configuration.
- The release workflow is forced to produce a draft and rejects owner-panel artifacts.

## First draft verification

- Signed-release run `31270299401` created an unpublished `v0.5.9-test` draft from
  GitHub main `c9fe233` behind the required `rjclark99` environment approval.
- The downloaded 14-asset draft contained no owner panel, vault, or private runtime
  file, but its checksum inventory failed completeness: it listed two unuploaded build
  inputs and omitted the uploaded manifest.
- Publication and device use are stopped. Local correction `0acb758` generates an
  LF-only inventory for exactly the flattened uploaded assets, rejects duplicate
  names, and passes 15 focused plus 88 full Python/Kodi tests.
- Corrective run `31270754516` then passed exact inventory, GitHub digest, and signed
  manifest checks but failed because Linux-built skin/provider archives differed from
  their Windows-built signed package-lock hashes.
- Local commit `b3fed5f` uses stored entries plus canonical LF text for the two locked
  packages, adds a mandatory pre-upload lock check, updates the signed hashes, and
  re-signs configuration `2026.08.39`. Two builds matched byte-for-byte and all 90
  Python/Kodi tests passed.

## Remaining gated acceptance

The content/device pass is ready but blocked until the owner approves mutation of named
reference devices and their rollback baselines. It must cover populated VOD rows,
focused/unfocused terminal cards, provider/network order, failed art, exact directory
opening, consent cancellation, installer denial, Stop, process restart, Kodi warnings,
Bootstrap decline/revoke/scope change, observed completion, and skin rollback.

The candidate manifest is offline-signed and the reproducibility correction is local.
GitHub main update, draft replacement, publication, deployment, and fresh-device
acceptance remain separately gated.

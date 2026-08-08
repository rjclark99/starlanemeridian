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

- The exact candidate at `fcbec9c` passed GitHub Actions run `31265192787` across
  configuration/Kodi, control-service, and Android jobs.
- The offline signature on manifest `2026.08.38` verifies against the checked-in
  public key, and its Bootstrap digest matches deterministic Bootstrap 1.1.16 bytes.
- Project-control schemas, authority gates, release regressions, package-lock checks,
  Python compilation, Kodi tooling, Android unit tests, and Android lint pass.
- A clean archived checkout built without the removed owner panel or its private
  runtime configuration.
- The release workflow is forced to produce a draft and rejects owner-panel artifacts.

## Remaining gated acceptance

The content/device pass is ready but blocked until the owner approves mutation of named
reference devices and their rollback baselines. It must cover populated VOD rows,
focused/unfocused terminal cards, provider/network order, failed art, exact directory
opening, consent cancellation, installer denial, Stop, process restart, Kodi warnings,
Bootstrap decline/revoke/scope change, observed completion, and skin rollback.

The candidate manifest is offline-signed, the source is committed on local `main`, and
the candidate branch is pushed. GitHub `main`, release draft creation, publication,
deployment, and fresh-device acceptance remain separately gated.

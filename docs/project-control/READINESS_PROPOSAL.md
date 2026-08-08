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

- Project-control schemas and authority gates pass.
- Widget/provider affected suites: 14 passed; pinned provider package built locally.
- Bootstrap/manifest focused suites: 33 passed.
- Android focused final-delta suites: 8 passed. The preceding full Android suite passed
  22 tests plus lint; the final digest-only delta was rechecked with its focused suite.
- Full Python/Kodi tooling: 81 of 82 passed. The one rejection is the required release
  gate proving the signed manifest still identifies published Bootstrap 1.1.13, not
  unapproved local source candidate 1.1.14.
- Python compileall and repository diff checks pass.

## Remaining gated acceptance

The content/device pass is ready but blocked until the owner approves mutation of named
reference devices and their rollback baselines. It must cover populated VOD rows,
focused/unfocused terminal cards, provider/network order, failed art, exact directory
opening, consent cancellation, installer denial, Stop, process restart, Kodi warnings,
Bootstrap decline/revoke/scope change, observed completion, and skin rollback.

No candidate has been signed, deployed, published, committed, or pushed.

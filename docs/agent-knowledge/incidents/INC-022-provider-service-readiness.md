---
id: incident.provider-service-readiness
kind: incident
status: active
verified_at: 2026-08-08
tags: [kodi, bootstrap, umbrella, services, jsonrpc]
authority: [owner-reported device behaviour, kodi/repository.kodisetup/service.py, tools/test_kodi_bootstrap.py]
supersedes: []
---

# Provider service readiness could never be announced

## Symptom

Bootstrap reported `Setup finished with 2 issue(s)` on every first run. The Home menu was
never built and the television stayed on Estuary, while the provider itself appeared
correctly installed and enabled in Kodi's add-on list.

The issue count is diagnostic. The skin step raises unconditionally whenever any earlier
failure exists, so the total is always one real failure plus that cascade. Exactly two
issues therefore means exactly one root cause, and only the root cause is written to
`kodi.log` — the cascade is appended to the failure list without being logged.

## Root cause

`wait_for_provider_ready` waits for the `starlane.umbrella.ready` window property, which
is only ever set by the provider's own `service.py` after `CheckSettingsFile` and
`SyncMyAccounts` complete.

Kodi starts `xbmc.service` entry points in response to an add-on *enable event*.
`install_locked_package` replaces the add-on directory on disk, then
`install_locked_packages` calls `UpdateLocalAddons` and enables the package over
JSON-RPC. A freshly extracted package is frequently already enabled, so
`Addons.SetAddonEnabled(true)` is a no-op that raises no event and starts no service. The
property therefore could not appear on the launch that installed the provider, and the
240 s wait had to expire.

Restarting Kodi fixed it every time, because the service then started normally at launch.

## Why tests did not catch it

`tools/test_kodi_bootstrap.py` pre-set `starlane.umbrella.ready` to `"true"` in `setUp`
and set it again on *any* `Addons.SetAddonEnabled` call, including a no-op re-enable. The
harness therefore modelled readiness as always obtainable and could not express the
failure. The harness now announces readiness only on a genuine disabled-to-enabled
transition, which is what Kodi actually does.

## Fix and prevention

- `restart_provider_service` cycles the provider's enabled state once when readiness is
  absent, producing the enable event Kodi needs. This uses the JSON-RPC method already in
  the closed command set and adds no new capability.
- If readiness is still absent, the run defers: it records a bounded attempt, notifies
  that setup will finish when Kodi restarts, quits Kodi, and commits nothing. Absent
  readiness is no longer a failure. Bootstrap re-runs on the next launch and installation
  is idempotent, so the retry is cheap.
- Deferral is bounded by `MAX_ACTIVATION_ATTEMPTS`. Once exhausted it reports a real,
  actionable failure rather than quitting Kodi again.
- The readiness wait dropped from 240 s to 30 s, since a wait that long can no longer
  help.
- The INC-019 protection is intact: the skin is still never activated while the provider
  is unready. Activation is deferred, not skipped.

## Related

`incident.provider-overlay-bootstrap-order` for why the readiness gate exists, and
`incident.unconfirmed-skin-activation` for the commit-ordering defect found in the same
acceptance attempt.

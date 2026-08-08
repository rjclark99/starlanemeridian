---
id: incident.unconfirmed-skin-activation
kind: incident
status: active
verified_at: 2026-08-08
tags: [kodi, bootstrap, skin, recovery, state]
authority: [owner-reported device behaviour, kodi/repository.kodisetup/service.py, tools/test_kodi_bootstrap.py]
supersedes: []
---

# An unconfirmed skin activation stranded the television permanently

## Symptom

Setup completed and displayed `Configuration 2026.08.41 applied`. Kodi then froze at its
own "Keep this change?" skin dialog. After a restart Kodi reported that the previous skin
had been restored, ran on Estuary, and never attempted the Starlane Home menu again on any
subsequent launch. Recovery required selecting the skin by hand.

## Root cause

Two correct-looking behaviours combined into an unrecoverable state.

`run()` recorded `applied_version` and `applied_scope` as soon as the skin step returned.
The skin change itself is only *confirmed* on the following launch, by
`recover_pending_skin`, because Kodi persists `lookandfeel.skin` on clean shutdown.

Kodi froze and was killed, so the setting never reached `guisettings.xml`. On the next
launch `recover_pending_skin` correctly saw a mismatch, restored the previous skin, and
cleared the pending markers. But the applied scope was already committed, so the early
return in `run()` matched and Bootstrap considered its work finished forever.

The rollback safety net worked exactly as designed; it simply could not distinguish "the
skin crashed Kodi" from "Kodi was killed while the skin was fine".

## Fix and prevention

`recover_pending_skin` now withdraws the commit when it cannot confirm the skin: it clears
`applied_scope`, increments `activation_attempts`, and lets the same launch activate Home
again. Installation is idempotent, so the retry only redoes the activation.

The commit stays optimistic rather than being deferred to the confirming launch. That
matters because the setup app polls Bootstrap's applied-version evidence to decide that
setup finished; delaying the commit would leave the app reporting an incomplete install
for a whole session.

Retries are bounded by `MAX_ACTIVATION_ATTEMPTS`. Once exhausted, the applied scope is
left in place and the user is told to choose the skin under Settings, Interface, Skin,
rather than looping.

## Related

`incident.provider-service-readiness`, found in the same acceptance attempt, and
`subsystem.kodi-bootstrap` for the two-launch apply/confirm lifecycle this preserves.

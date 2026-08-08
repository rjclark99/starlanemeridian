# Starlane Movies agent contract

## Purpose and priorities

This is the compact project-wide contract for Starlane Movies. Detailed architecture,
state, decisions, incidents, and runbooks live under `docs/agent-knowledge/`; project
control records live under `docs/project-control/`. Historical handoffs are evidence,
not mandatory startup context.

Work in this order:

1. Preserve security, privacy, rollback, legal, authority, and compatibility boundaries.
2. Solve the stated task with the smallest source-level change and bounded context.
3. Minimize CPU, memory, storage, network, database, and artwork pressure on Kodi and
   lower-end Fire TV/Android TV hardware.
4. Preserve a fast, predictable, overscan-safe, D-pad-first television experience.
5. Keep source, local candidate, device, signed-manifest, public-release, production-
   service, and documentation states separate.
6. Convert verified reusable findings into focused tests and indexed knowledge.

## Staged startup and routing

Before changing anything:

1. Read this file completely.
2. Read `docs/agent-knowledge/index.yaml` and `docs/project-control/README.md`.
3. Inspect `git status --short` and `git log -8 --oneline --decorate`; preserve every
   pre-existing change as user-owned.
4. Classify the request as answer, diagnose, implement, deploy, release, publish, or
   monitor, and name the affected state.
5. Read the matching current-state record, one subsystem record, and no more than three
   directly relevant topic records. Expand only when contradictory evidence or a real
   subsystem boundary requires it, and record why.
6. Inspect exact source/config/tests and affected build manifests. Do not ingest whole
   logs, generated files, or historical handoffs when bounded searches answer the task.
7. State one primary hypothesis and one observation that distinguishes it from
   alternatives, then run the smallest safe read-only or static check.

For project-wide policy or unresolved history, route to `docs/TECHNICAL_HANDOFF_2026-07-26.md`,
`docs/AGENT_HANDOFF.md`, `docs/CURRENT_STATUS.md`, `docs/BRAND_GUIDE.md`, `README.md`,
`SECURITY.md`, or `docs/OPERATIONS.md` only as needed. If a required record is missing,
stale, or contradictory, report the gap; never reconstruct facts from memory or filenames.

## Supervisor and delegation

The persistent **Starlane Project Control** task is the control tower. It owns scope,
priorities, state classification, task decomposition, approvals, integration, evidence,
and closure. It does not implement product features itself except when the owner
explicitly assigns direct implementation; it may maintain project-control records.

Use `docs/project-control/roles.json` and the task/result schemas for delegation.

- Delegation is evidence-gated. Default to one specialist and add another only for a
  genuinely independent workstream or independent review.
- Maximum concurrency is the supervisor plus three specialists.
- Start specialists with no inherited full conversation when the platform supports it;
  provide the bounded task packet, exact paths, and up to three knowledge references.
- Specialists report to the supervisor. Lateral coordination is exceptional and must
  be authorised by the supervisor.
- Assign one writer per path. Parallel writers require disjoint paths and no shared
  generated output, manifest, lock file, or release directory.
- Specialists may not broaden scope, spawn an unrequested workstream, publish, deploy,
  or mutate external state. Retire them after the bounded task.
- Security review is read-only by default. Remediation is a separate implementation task.
- Release verification does not imply publication authority. Publication uses the
  separately gated publication-executor role.

## Source of truth and state separation

Resolve conflicts in this order:

1. `SECURITY.md`, schemas, and enforced security/privacy code.
2. Checked-in source, configuration, and regression tests for intended source state.
3. Fresh bounded inspection of the relevant device, service, or public bytes.
4. The newest explicitly dated and verified current-state record.
5. Older handoffs and incident narratives as historical evidence only.

Always qualify state:

| State | Establish with |
| --- | --- |
| Source state | Git commit plus exact source/config/tests |
| Local candidate | Build inputs, version, checksum, signature where applicable |
| Device state | Fresh bounded read-only inspection of a named device class |
| Signed-manifest state | Schema, canonical JSON, public-key verification |
| Public-release state | Downloaded public bytes, hashes, signatures, routes |
| Production-service state | Fresh authorised service/deployment inspection |
| Documentation state | Dated record, authority, and verification date |

Record them separately in `docs/agent-knowledge/current/`. A local artifact is never
release proof. When sources conflict, identify which state each describes and leave
unresolved uncertainty explicit.

## Security, privacy, authority, and stop conditions

Never print, commit, copy into guidance, or expose private keys, Android keystores,
vault contents, service tokens, OAuth tokens, pairing codes, provider credentials, or
complete sensitive settings files.

Non-negotiable boundaries:

- Owner administration tooling remains outside this client repository. Do not add a
  runnable management panel, vault, or private administration configuration to this tree.
- Keep cloud commands a closed enum. Never add arbitrary shell, ADB, URL, Python, Kodi
  built-in, remote-desktop, accessibility, or arbitrary-settings capability.
- Never expose ADB port 5555 to the internet or silently change VPN/network policy.
- Do not automate CAPTCHA, terms acceptance, account farming, registration, payment,
  or account transfer. Real-Debrid uses official device OAuth and tokens stay on TV.
- Require an exact owner-approved legal allowlist before adding or publishing any
  third-party Kodi repository or add-on.
- Android developer options, ADB approval, Install Unknown Apps, runtime storage
  permission, and package confirmation remain explicit user actions. On approved
  Android 9/Fire OS only, the setup app may merge the single fixed Kodi preference
  `addons.unknownsources=true` for `org.xbmc.kodi`, preserving every other setting,
  and may atomically install only the signed-manifest-selected, hash-verified
  `repository.kodisetup` archive into that package's canonical profile. This fixed
  local transaction requires the recorded owner-approved one-run consent, bounded
  archive/path/ID/version validation, conservative Kodi-not-running proof, journaling,
  and exact rollback. It must not become an arbitrary ZIP, URL, path, add-on, setting,
  command, database, shell, ADB, or accessibility capability. Bootstrap's scoped local
  consent remains explicit. A proven cold transaction may create only the canonical
  missing Kodi profile ancestors and a minimal settings file containing that fixed
  preference; existing settings always use the preserving merge. API 29+ retains the
  guided manual Kodi steps.
- Back up exact device/profile/database/log state before risky hardware mutation.
- Never delete user data, viewing progress, databases, add-on settings, rollback skins,
  backups, or recovery evidence without exact owner authority.
- Telemetry must not reveal credentials, viewing history, payment information, or
  unnecessary device facts.

Stop and ask the owner before any secret inspection, deletion, irreversible mutation,
account/payment/terms/legal decision, trust-boundary expansion, new provider/allowlist
entry, credential or provider-route change, VPN/network-policy change, D1 migration,
deployment, publication, stable promotion, commit, or push. Implementation authority
does not imply external-mutation authority.

## Git, rollback, and preservation

- Inspect status before edits and handoff. Preserve unrelated changes; never use broad
  restore, reset, clean, or whole-tree staging.
- Stage only exact paths when explicitly authorised. Commit, push, deploy, migrate,
  release, and publish are separate owner-authorised actions.
- Treat ignored `build/` artifacts as evidence, not public or reproducible source.
- Fix generators/templates rather than only generated or deployed copies.
- Preserve and hash rollback artifacts; restore synthetic progress fixtures byte-for-byte.
- Compatibility identifiers are migration boundaries: Android package
  `app.kodisetup.tv`, production skin `skin.starlanemeridian`, repository/bootstrap
  `repository.kodisetup`, and established public/control URLs. Renaming requires an
  explicit migration project and owner authority.

## Subsystem routing and validation

| Concern | Route | Focused validation |
| --- | --- | --- |
| Android setup | `android-app/` | unit test, then `:app:testDebugUnitTest :app:lintDebug` |
| Control plane | `control-api/` | focused test, then `pnpm check` and `pnpm test` |
| Signed config/release | `config/`, `tools/`, workflows | schema/public-key and focused release tests |
| Kodi bootstrap | `kodi/repository.kodisetup/` | focused Python/XML/Kodi tests |
| Production skin | `tools/skin_builder.py`, branding | focused builder/XML/package checks |
| Private skin | `kodi/skin.starlane.movies/` | XML/Python parse and focused experimental tests |
| Operations/knowledge | `docs/`, project control | link, schema, state, and authority validation |

Use the ladder in `runbook.focused-validation`: exact diff and parse/compile, smallest
regression, subsystem suite, build/package, artifact verification, rollback-safe device
test, bounded logs/state cases, then the full relevant suite once before delivery.
Never convert a local pass into a deployment or release claim.

## Kodi, resource, and UX invariants

- One visual property has one owner. The bounded outer grouplist owns Home vertical
  motion; poster containers own horizontal motion; the complete row owns opacity; the
  selected card owns its focus border; the deferred snapshot owns hero/details updates.
- Use one Home renderer. Do not mix additive slide systems, parallel hubs, or competing
  visibility/fade systems.
- Preserve constant row geometry, overscan-safe margins, adjacent instantiated rows,
  capped provider counts, background artwork loading, and stable empty/loading/error
  row height.
- Select and Right are idempotent and share the first-populated-row path. Rapid input
  supersedes stale callbacks; Left returns to the menu without stale offsets.
- Keep one obvious focus target and never communicate focus by colour alone. Keep
  motion restrained and the interface functional without optional heavy helpers.
- Keep provider failure, empty-state lifecycle, focus, geometry, generated shortcuts,
  texture loading, and deferred details as separate diagnostic dimensions.
- Do not add network/artwork/write/full-scan work to the local progress polling loop.
- Follow the current owner-authorised provider policy in source and state records; do
  not broaden it as a side effect.

For menu changes, follow `runbook.skin-shortcuts-regeneration`: stop Kodi, back up exact
saved data/include/hash, deploy source, use a neutral generated include, remove only the
exact private-skin hash when required, rebuild, pull and inspect counts, and remove any
temporary one-shot script.

## Efficient investigation and communication

- Initial search: one subsystem and at most five concepts.
- Logs: matched lines with 10-20 lines of context, never whole logs by default.
- Iteration: one hypothesis and source concern with focused validation before expansion.
- Build/deploy/hardware/web research only when the preceding evidence justifies it.
- Run the full relevant suite once. Batch related read-only device checks.
- State each rule/fact once. User updates contain hypothesis, evidence, action, result.
- Specialists return conclusions and evidence locations, not full tool output.
- Track platform token usage when available; otherwise use loaded bytes, tool calls,
  turns, retries, and agent count as explicit efficiency proxies.

## Knowledge and handoff

Update the smallest current-state, subsystem, decision, incident, research, or runbook
record when verified findings change future work. Preserve stable IDs, verification
dates, authority, related links, and supersession. Do not record transient output,
secrets, ephemeral device addresses/PIDs, or repeated test passes without new coverage.

End each task with: classified outcome and affected state/subsystem; exact changed
paths; focused and full validation separately; device/public/service checks actually
performed; unresolved uncertainty; rollback when relevant; external mutations and
authority; and knowledge/regression updates. Never claim deployment, release, or
quantitative performance without its corresponding evidence.

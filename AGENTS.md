# AGENTS.md

## Scope and status

This is the project-wide operating contract for agents working on Starlane Movies. It applies across the Android setup application, Windows administration portal, Cloudflare control plane, signed configuration and release flow, Kodi bootstrap/repository, production skin, private experimental skin, tooling, CI, branding, and operational documentation.

This file is a routing and safety document, not a project diary. Keep durable detail, current-state snapshots, decisions, incidents, runbooks, and research in `docs/agent-knowledge/`; load those records only when the task requires them.

The repository baseline supplied to the author of this file was `main` at `4aad405`, prepared on 2026-07-28. **That commit, every version number, technology version, provider route, hardware detail, and “current” behavior stated below is an authoring baseline, not a freshly verified repository fact. Verify it against the actual repository or relevant live state before relying on it.** The routed scaffold is at `docs/agent-knowledge/`; if an indexed record is missing, mark that gap rather than inventing its contents.

## Mission and priorities

Work in this order of priority:

1. Preserve security, privacy, rollback, legal, authority, and compatibility boundaries.
2. Minimize unnecessary context, tool calls, rebuilds, deployments, and repeated investigation.
3. Minimize CPU, memory, storage, network, database, and artwork pressure on Kodi and lower-end Fire TV/Android TV hardware.
4. Preserve a fast, predictable, overscan-safe, D-pad-first television experience.
5. Keep repository source, local candidates, deployed devices, signed configuration, public releases, and production services as separate states.
6. Convert confirmed failures and optimization findings into concise reusable knowledge and, where practical, regression coverage.

Make the smallest source-level change that solves the confirmed problem. Fix generators or templates rather than only generated or deployed copies. Do not broaden provider policy, trust boundaries, compatibility names, or external state as a side effect.

## Mandatory startup sequence

Before changing anything:

1. Read this file completely.
2. Read these repository documents completely, in order:
   1. `docs/TECHNICAL_HANDOFF_2026-07-26.md`
   2. `docs/AGENT_HANDOFF.md`
   3. `docs/CURRENT_STATUS.md`
   4. `docs/BRAND_GUIDE.md`
   5. `README.md`
   6. `SECURITY.md`
   7. `docs/OPERATIONS.md`
3. Inspect `git status --short`. Treat every pre-existing modification as user-owned.
4. Inspect `git log -8 --oneline --decorate`.
5. Read `docs/agent-knowledge/index.yaml`; do not recursively load the knowledge directory.
6. Classify the task as answer, diagnose, implement, deploy, release, or monitor.
7. Select the relevant current-state record, one subsystem record, and no more than three directly relevant topic records in total unless evidence shows that the task crosses boundaries.
8. Inspect `.github/workflows/`, `config/manifest.json`, `config/manifest.schema.json`, the affected subsystem’s build/test manifests, and the exact source files only when relevant to the task.
9. Record one primary hypothesis and one observation that would distinguish it from alternatives.
10. Start with the smallest safe read-only or static check.

If a required file or record is missing, stale, contradictory, or cannot be verified, report that limitation. Do not reconstruct repository facts from filenames, memory, or old narrative.

## Source-of-truth precedence

Resolve conflicts in this order:

1. Security and privacy invariants in `SECURITY.md` and rules enforced by schemas or code.
2. Checked-in source, configuration, and regression tests for intended source state.
3. Fresh read-only inspection of the relevant device, cloud service, portal, or public release.
4. The newest explicitly dated and verified status entry.
5. Older handoffs and incident narratives as historical evidence only.

Do not accept the first matching statement in a handoff. When sources conflict:

- record the contradiction;
- inspect the authoritative source or live state;
- identify which state each statement describes;
- update or supersede the stale record after verification;
- leave unresolved uncertainty explicit.

Never silently retain two competing active truths.

## State separation

Never use an unqualified word such as “current,” “deployed,” or “released.” Name the state:

| State | Meaning | How to establish it |
| --- | --- | --- |
| Source state | Checked-in intended code/configuration at an identified commit | Git and exact source/config/tests |
| Local candidate | Locally built artifact not yet proven public or installed | Source commit, version, build inputs, checksum, signature where applicable |
| Device state | Version/configuration installed on a named reference device class | Fresh bounded read-only device inspection |
| Signed-manifest state | Version and artifacts named by the signed configuration | Manifest, schema, public-key verification |
| Public-release state | Assets actually downloadable from the public release | Downloaded bytes, hashes, signatures, routes |
| Production-service state | Active portal/control-plane deployment or migration state | Fresh authorized service inspection |
| Documentation state | What status and knowledge records claim | Dated record plus its authority and verification date |

A local artifact is not release proof. Release proof requires its source commit, version, checksum, applicable signature, and comparison with the bytes downloaded from the public location.

Baseline claims requiring repository or live-state verification include:

- checked-in baseline private skin `skin.starlane.movies` 2.2.16 and the separately
  tracked 2.2.17 working-tree/device candidate;
- Kodi 21.3/Omega on an Amazon Fire TV family reference device using Fire OS based on Android 9;
- production rollback skin `skin.starlanemeridian` 1.2.4;
- the private rollback sequence involving 2.2.15, 2.2.14, and operational fallback 2.2.8;
- published `v0.3.8-test` stream;
- the private skin remaining outside the signed production manifest;
- all dependency, API, language, SDK, and build-tool versions in the subsystem map below.

Store verified states separately in:

- `docs/agent-knowledge/current/source-state.md`
- `docs/agent-knowledge/current/deployed-state.md`
- `docs/agent-knowledge/current/public-release-state.md`

## Security, privacy, authority, and stop conditions

These rules are non-negotiable:

- Never print, commit, copy into guidance, or expose private keys, Android keystores, vault contents, Cloudflare Access secrets, OAuth tokens, pairing codes, provider credentials, service tokens, or complete sensitive settings files.
- Keep the Windows portal password protected and loopback-only.
- Keep cloud commands a closed enum. Never add arbitrary shell, ADB, URL, Python, Kodi built-in, or remote-desktop capability.
- Never expose ADB port 5555 to the internet.
- Do not automate CAPTCHA, acceptance of terms, account farming, registration submission, payment, or account transfer.
- Use official device OAuth for Real-Debrid; tokens remain on the television device.
- Require an exact owner-approved legal allowlist before publishing any third-party Kodi repository or add-on.
- Leave Android developer options, ADB approval, unknown-source permission, and package-install confirmation as explicit user actions.
- Never replace a working local portal configuration or vault with a checked-in blank template.
- Back up exact device, profile, database, and log state before risky hardware mutation.
- Do not delete user data, viewing progress, databases, add-on settings, rollback skins, backups, or other recovery evidence unless the owner explicitly requests that exact destructive action.
- Do not reveal credentials, viewing history, payment information, or unnecessary device facts in UI telemetry.
- Do not commit, push, publish, promote, deploy, migrate, or release merely because implementation and tests pass.

Stop and ask the owner before work requiring:

- a secret or sensitive full-file inspection;
- deletion or irreversible mutation;
- account, payment, terms, or legal decisions;
- expansion of a trust boundary or remote command surface;
- a new third-party allowlist entry;
- a materially different provider route, credential change, or provider upgrade;
- stable promotion, public publication, deployment, D1 migration, commit, or push;
- changes to VPN state or network security policy.

Implementation authority does not imply external-mutation authority.

## Git, rollback, and preservation

- Inspect status before edits and again before handoff.
- Preserve unrelated or pre-existing changes; do not overwrite, stage, or reformat them.
- Never use `git reset --hard`, broad checkout/restore, destructive clean operations, or whole-tree staging.
- Stage only exact intended paths when staging is explicitly requested or authorized.
- Treat generated and ignored `build/` artifacts as evidence, not publishable source by default.
- Preserve rollback artifacts and hash them; avoid repeatedly copying or opening sensitive state.
- Fix source generators and templates, then regenerate.
- Add a focused regression assertion for each confirmed defect when feasible.
- Record source, device, signed-manifest, public-release, service, and documentation transitions independently.
- Restore synthetic personal-progress fixtures byte-for-byte after tests.

Compatibility identifiers are migration boundaries, not cosmetic names. The handoff identifies the following as intentionally retained; verify them before use:

- Android package `app.kodisetup.tv`
- production Kodi skin ID `skin.starlanemeridian`
- repository/bootstrap ID `repository.kodisetup`
- existing GitHub repository and public/control URLs

Renaming any of these requires an explicit migration project and owner authority.

## Subsystem routing

All paths and technology versions in this table come from the authoring handoff and require verification against the repository.

| Concern | Route first to | Baseline responsibility | First validation rung |
| --- | --- | --- | --- |
| Android setup | `android-app/` | Kotlin/Compose setup, signed-manifest consumption, verified downloads, pairing, bounded telemetry, official OAuth | Focused unit test, then `:app:testDebugUnitTest :app:lintDebug` |
| Windows portal | `admin-portal/`, `admin-portal.tests/` | Loopback UI, encrypted household vault, pairing, support, allowlisted commands, ADB fallback | Focused test, then restore/build Release and portal tests |
| Control plane | `control-api/` | Cloudflare Worker/D1 pairing, signed requests, replay defense, bounded events/status, allowlisted commands and Kodi redirects | Focused test, then `pnpm check` and `pnpm test` |
| Signed config/release | `config/`, `tools/` | JSON Schema, canonical JSON, Ed25519, staged manifest, pins, repositories, add-ons, skins, telemetry | Schema/public-key verification and focused unit tests |
| Kodi bootstrap/repository | `kodi/repository.kodisetup/` | Manifest verification, idempotent configuration, add-on/repository installation, activation and rollback | Focused Python/XML checks, then relevant Kodi suite |
| Production skin | `tools/skin_builder.py` and related Kodi inputs | Reproducible `skin.starlanemeridian` packages from Estuary-derived GPL source | Focused builder/XML tests, then package verification |
| Private skin | `kodi/skin.starlane.movies/`, `tools/test_experimental_skin.py` | Private Titan BINGIE MOD-derived interface and Home widget work | XML parse, Python compile, focused experimental-skin tests |
| Release/CI/tooling | `tools/`, `.github/workflows/` | Validation, signing, packaging, export, monitoring, branding and offline-signed release checks | Focused tool test, then full Python/tooling suite |
| Branding | `assets/branding/`, `docs/BRAND_GUIDE.md` | Reproducible visual identity | Exact generator/output checks scoped to change |
| Operations/status | `docs/` | Runbooks, security, state, handoffs, incident evidence | Link/state consistency and authority verification |

Use `docs/agent-knowledge/subsystems/` for concise subsystem architecture. Use the matching runbook for execution; use decisions for “why”; use incidents for known symptoms and failed avenues.

## Token-efficient investigation and execution

Use this task loop:

1. **Classify** the request.
2. **Route** through the knowledge index to one current-state record, one subsystem, and directly related material.
3. **Inspect** status and the exact affected source.
4. **Hypothesize** one primary cause and one discriminating check.
5. **Reproduce** with the smallest safe static or local fixture before hardware.
6. **Change** one source-level concern while preserving invariants.
7. **Validate** focused checks first.
8. **Device-test** only when static evidence justifies it and exact rollback state is preserved.
9. **Escalate validation** to the full relevant suite once before delivery or release.
10. **Document** one verified current fact and the smallest reusable incident/decision update.
11. **Mutate externally** only with explicit authority.
12. **Handoff** outcome, evidence, remaining uncertainty, rollback, and changed paths.

Default budgets:

- Startup: this file, the compact index, status, and no more than three routed topic records in addition to the relevant current-state record.
- Initial search: one subsystem and at most five search concepts.
- Logs: matched lines with 10–20 lines of context, never entire logs by default.
- Iteration: one source change followed by focused validation before device deployment.
- Documentation: one current fact and one incident or decision record; do not repeat the same narrative in multiple handoffs.

Exceed a budget only when a task spans subsystems or evidence contradicts the selected records. State which new evidence justified expansion.

Prefer exact source, local fixtures, and captured official documentation over repeated browsing. Browse only for unstable, absent, or precisely referenced external information, using primary Kodi, add-on, or upstream sources. Cache stable conclusions in a short research record with URL, retrieval date, applicable version, local consequence, and refresh conditions.

Batch related read-only device checks in one ADB session. Pull only exact files or bounded logs. Run focused tests during iteration and the full relevant suite once. Do not rebuild, deploy, restart, record, and retrieve complete device state for speculative visual tweaks.

For visual faults, separate these dimensions and change only the one supported by evidence:

- row/control existence;
- layout geometry;
- focus/navigation;
- animation ownership;
- generated Skin Shortcuts state;
- provider directory completion;
- artwork loading;
- deferred hero/details state.

Provider failure, empty-state lifecycle, focus, geometry, and texture loading are not one problem.

## Kodi, resource, and UX invariants

### Rendering ownership and geometry

- Give every visual property one owner.
- The outer bounded grouplist owns Home vertical motion.
- Horizontal poster containers own horizontal motion.
- The complete row group owns row opacity.
- The selected card owns its focus border.
- The deferred Home snapshot owns large hero/details updates.
- Do not combine position-dependent slide matrices, native scrolling, fixed-focus offsets, or parallel fade/visibility systems on the same property; Kodi animations are additive.
- Use one Home renderer for categories already served by Home. Do not activate parallel hub windows.
- Keep a constant row stride derived from header, poster height, spacing, and footer.
- Preserve the bounded widget viewport and generous overscan-safe margins.
- Empty, loading, missing-art, and provider-error states must not collapse row height or move later rows.
- Normalize Home to a single poster geometry. Do not allow saved/generated `widgetstyle.*` state to silently restore obsolete highlight layouts.

The handoff’s private-skin baseline—**requiring source/device verification**—uses a 371-pixel row stride; 150 ms `sine/out` scrolling on both Home axes; adjacent-row opacity from 35% to 100%; two-item poster preload; background dynamic-art loading; a 150 ms guarded hero/details delay; and a 100 ms hero crossfade.

### Lifecycle, input, and presentation

- Keep adjacent rows instantiated; fade the whole row rather than hiding or unloading it.
- Pre-check locally knowable empty rows before calling provider directories.
- Do not flush global widget properties after focus enters a widget container.
- Make Select and Right idempotent and route both through the same first-populated-row entry path.
- Make rapid input supersede stale callbacks.
- Hold the previous hero until the newest committed artwork is ready, then crossfade.
- Hover, Select, and Right must not expose different renderers or first frames.
- Left returns to the menu while retaining category context without stale offsets.
- Keep one obvious focus target; never communicate focus by colour alone.
- Use predictable target sizes, navigation directions, restrained animations (normally 150–280 ms), bounded missing-art fallbacks, and labels that do not collide with focus surfaces.
- Keep the interface functional without optional helper services.

### CPU, memory, storage, and network

- Treat `ReloadSkin()` as expensive. Measure before increasing polling or reload frequency.
- Keep local polling bounded, read-only, inexpensive, and transition-driven.
- The handoff describes a two-second existence check of Umbrella’s local SQLite progress table. Verify the implementation before relying on it; never add network work, artwork work, writes, or full-table scans to that loop.
- Avoid synchronous plugin enumeration during navigation, automatic trailers, per-focus heavy metadata work, and mandatory heavy helpers.
- Keep only the active category’s row set in Home while retaining adjacent rows in that set.
- Do not instantiate parallel Home/hub renderers or multiple view families.
- Cap provider item counts and do not raise them while diagnosing layout.
- Use background loading for dynamic posters, logos, fallbacks, and fanart.
- Avoid large simultaneous hero changes during list movement, excess masks/art outside the viewport, duplicate databases, and unnecessary services.
- Use indexed, limited SQLite existence queries.
- Do not enumerate slow or blocking Live TV providers in background Home widgets.
- Separate route validity, provider response time, artwork time, and renderer time.
- Prefer public TMDb discovery where personalization is unnecessary.

The latest verified provider policy—**requiring fresh verification and owner authority
before change**—assigns non-live discovery/playback to Umbrella, external scraping to
CocoScrapers, Sports to Mad Titan, and Live TV to The Crew. Mad Titan 2.0.32's broken
Live NetTV route is excluded; FenLight remains absent unless the owner changes policy.

### Skin Shortcuts

Packaged defaults may not control a live profile. Saved files under `userdata/addon_data/script.skinshortcuts/` can regenerate stale routes and styles.

For menu changes:

1. Stop Kodi.
2. Back up only the affected saved `.DATA.xml` files, generated include, and hash.
3. Deploy source.
4. Keep the packaged generated file as valid neutral `<includes />`.
5. Remove only the exact private-skin hash when regeneration is necessary.
6. Run Skin Shortcuts `buildxml`.
7. Pull and inspect the generated include.
8. Count expected provider and style references.
9. Remove any temporary one-shot `autoexec.py`.

Do not restore saved FenLight menu backups during a normal Umbrella deployment.

Known durable traps belong in incident records: competing animation owners, hidden-row churn, parallel hubs, mixed poster/highlight state, mismatched axis timing, synchronous art churn, unresolved nested include parameters, asynchronously removed empty Continue Watching controls, provider errors misdiagnosed as skin faults, stale generated shortcuts, inadequate frame instrumentation, ADB blocked by VPN, incorrect Kodi repository paths, CRLF checksum sidecars, unsupported empty Kodi defaults, empty release environment values, and two-part semantic-version parsing.

Use Fire TV `screenrecord` and `dumpsys gfxinfo` only for qualitative geometry unless their limits are re-established. The handoff requires external true-60-fps capture for quantitative frame acceptance.

## Validation escalation ladder

Validation must be proportional and progressive:

1. Inspect exact changed lines and run formatting/diff checks.
2. Parse or compile the changed file.
3. Run the smallest focused regression test.
4. Run the subsystem’s focused suite.
5. Build/package only after static checks support the hypothesis.
6. Verify artifact structure, version, paths, bytes, size, checksum, and signature as applicable.
7. Preserve rollback state and test hardware only when needed.
8. Inspect bounded logs and relevant empty, populated, loading, error, missing-art, cold, warm, and rapid-input states.
9. Run the full relevant suite once before delivery.
10. For public release, run CI-equivalent checks and separately obtain release authority.

Subsystem expectations:

- **Private skin:** parse changed XML; compile changed Python; run focused tests in `tools/test_experimental_skin.py`; run `git diff --check`; inspect generated provider/style counts. Before delivery, run the full Python/Kodi suite, verify ZIP top-level path, forward slashes, version, size, and SHA-256, preserve device/profile/database/log state, test cold and warm Home behavior, and inspect bounded Kodi error matches.
- **Python/config/release:** focused tests, then `python -m unittest discover -s tools -p "test_*.py"` and `python -m compileall -q kodi tools`; validate the manifest and verify it with the public key; verify deterministic paths, exact LF-only sidecars, hashes, and signatures without exposing the private key.
- **Control API:** work in `control-api/`; run `pnpm check` and `pnpm test`; preserve authentication and the closed command enum. Deployment and D1 migration are separate authorized mutations.
- **Android:** focused unit tests, then `:app:testDebugUnitTest :app:lintDebug`; verify the handoff’s Java 17, API 25 minimum, and API 36 compile/target claims in actual manifests before enforcing them. Preserve D-pad behavior, signature/hash verification, and visible installer permissions. Fire TV and Android TV/Google TV are distinct hardware acceptance targets.
- **Windows portal:** restore, build Release, and run `admin-portal.tests`; preserve loopback binding, vault rules, encryption, auto-lock, and clipboard clearing. Never replace or reveal the live vault/service-token configuration.
- **Public release:** require explicit authority; pass CI-equivalent checks; assemble a draft with rollback assets; download every asset and compare bytes; verify signatures and public routes; test Bootstrap application and second-launch confirmation/rollback clearing; update the separated state records and leave the repository clean.

Repository-routing details such as Kodi’s required nested datadir path, LF-only checksum sidecars, and release environment presence checks must be verified in source/tests before being treated as current behavior.

## Knowledge retrieval

The knowledge root is `docs/agent-knowledge/`:

- `INDEX.md` — human-readable map
- `index.yaml` — compact machine-routing index
- `current/` — source, deployed, and public-release state
- `subsystems/` — Android, portal, control API, signed config/release, Kodi bootstrap, production skin, private skin
- `runbooks/` — focused validation, private-skin device test, Skin Shortcuts regeneration, release/rollback, safe ADB diagnostics
- `decisions/DECISION_INDEX.md` — ADR-like architectural decisions
- `incidents/INCIDENT_INDEX.md` — reusable failures and prevention rules
- `research/RESEARCH_INDEX.md` — concise cached upstream findings
- `archive/YYYY/` — superseded chronological detail

Retrieve in this order:

1. This root contract.
2. `docs/agent-knowledge/index.yaml`.
3. Matches on `path_globs`, `tags`, and `read_when`.
4. The current-state record for the state being changed.
5. One subsystem record.
6. Only directly related runbook, incident, or decision records.
7. Related records only when evidence proves a boundary crossing.

Default cap: three topic records in addition to this file and the relevant current-state record. Search the index first, then exact source, then bounded evidence. Never recursively ingest the entire scaffold.

Example index-first searches:

```powershell
rg -n "widgets|clipping|Umbrella" docs/agent-knowledge/index.yaml
rg -n "kodi/skin.starlane.movies" docs/agent-knowledge/index.yaml
rg -n "INC-|ADR-" docs/agent-knowledge/incidents docs/agent-knowledge/decisions
```

Each indexed record should have an immutable namespaced ID, title, kind, status, path, concise summary, tags, path triggers, read triggers, authority, verification date, supersession links, related IDs, and size hint. Topic Markdown should begin with machine-readable front matter and remain factual, compact, and linked to bounded evidence.

Use decisions for architectural choices future agents might undo: trust boundaries, compatibility names, production/private skin separation, one Home renderer and vertical owner, schema-driven allowlists, local-only Umbrella progress, offline signing, and the loopback portal/closed command enum.

Use incidents for symptom, affected scope, false leads, root cause, smallest reproducer, fix, regression coverage, evidence, and prevention—not chronological narration.

## Knowledge updates and compaction

Update knowledge when a verified finding changes future implementation, diagnosis, validation, security, performance, resource use, token use, rollback, dependency/provider behavior, or UX.

Required triggers include:

- confirmed root cause or repeatable failed avenue;
- new invariant, architectural decision, trust boundary, or rollback path;
- changed source, device, manifest, public-release, or production-service state;
- provider/dependency route change;
- measured performance/resource limit;
- test or tool that materially shortens future work;
- stale, contradictory, or superseded fact.

Do not record transient output, immediately disproved hypotheses, ephemeral process IDs, temporary device addresses, or repeated test passes without new coverage.

Update the smallest relevant record. Change this root file only for project-wide rules or routing. Preserve stable IDs; mark old records `superseded`, link through `supersedes`, and move chronological detail to `archive/YYYY/`. Update `verified_at` only after actual verification. Keep summaries under about 60 words and active topic records generally under 1,500 words; split independently retrievable concerns.

Add or update a regression test when a knowledge change records a code defect. Review the index after material milestones and before releases.

The proposed future validator is `tools/validate_agent_knowledge.py`. Do not assume it exists. After schema review, it should check schema version, required fields, unique IDs, existing paths, valid related IDs, acyclic supersession, accepted kinds/status/tags, stale verification, and root/index size budgets before CI adoption.

## Handoff standard

End each task with:

- classified outcome and affected subsystem/state;
- exact changed paths;
- focused and full validation evidence, clearly separated;
- device/public/service checks actually performed;
- unresolved contradiction or uncertainty;
- rollback location and method when relevant;
- external mutations performed and the authority for each;
- knowledge and regression records updated.

Never claim a source change is deployed, a local artifact is released, a recording proves a quantitative frame threshold, or an authoring-baseline fact is repository-verified without the corresponding evidence.

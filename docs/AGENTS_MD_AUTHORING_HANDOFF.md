# Handoff for authoring the project-wide AGENTS.md

Last prepared: 28 July 2026
Repository baseline: `main` at `4aad405`
Audience: a GPT or coding agent tasked with creating the root `AGENTS.md` and its
supporting knowledge scaffold.

## 1. Purpose of this handoff

Use this document to create an in-depth, project-wide `AGENTS.md` for Starlane Movies.
The result must help future agents work safely and efficiently across the Android setup
app, Cloudflare control plane, signed configuration,
Kodi bootstrap/repository, production skin, and private experimental skin.

The root `AGENTS.md` must be a living operational contract, but it must not grow into a
chronological project diary. It should remain compact enough to load at the start of
every task. Detailed and historical knowledge must be stored in a structured,
searchable knowledge scaffold and loaded only when relevant.

The priorities, in order, are:

1. Preserve security, privacy, rollback, and compatibility boundaries.
2. Minimize tokens and unnecessary agent/tool work.
3. Minimize CPU, memory, storage, network, and artwork pressure on Kodi and lower-end
   Fire TV/Android TV hardware.
4. Preserve a fast, predictable, D-pad-first user experience.
5. Keep repository, deployed-device, and public-release state distinguishable.
6. Convert every confirmed failure or optimization finding into concise reusable
   knowledge and, where practical, a regression test.

This is an authoring brief. Do not simply copy it verbatim into `AGENTS.md`. Produce a
short root contract plus the supporting knowledge files described below.

## 2. Sources of truth and conflict resolution

Before generating `AGENTS.md`, read these repository files completely in this order:

1. `docs/TECHNICAL_HANDOFF_2026-07-26.md`
2. `docs/AGENT_HANDOFF.md`
3. `docs/CURRENT_STATUS.md`
4. `docs/BRAND_GUIDE.md`
5. `README.md`
6. `SECURITY.md`
7. `docs/OPERATIONS.md`

Then inspect:

- `git status --short`
- `git log -8 --oneline --decorate`
- `.github/workflows/`
- `config/manifest.json` and `config/manifest.schema.json`
- the build/test manifests for each subsystem
- the exact source files relevant to the requested task

Existing handoffs contain chronological material and some stale statements. For
example, older passages name private skin 2.2.11 or 2.2.15 as active while the latest
verified technical state and checked-in source are 2.2.16. `AGENTS.md` must teach
agents to resolve this deliberately rather than accepting the first matching sentence.

Use this precedence model:

1. Security and privacy invariants in `SECURITY.md` and enforced schemas/code.
2. Checked-in source, configuration, and regression tests for intended source state.
3. Fresh read-only inspection for current device, cloud, or release state.
4. The newest explicitly dated and verified status entry.
5. Older handoffs and incident narratives as historical evidence only.

Never merge the following concepts into one ambiguous “current” state:

- source version;
- locally built candidate;
- installed version on the reference device;
- signed manifest version;
- published GitHub release;
- production-active service deployment.

When two documents conflict, record the conflict, inspect the authoritative source or
live state, and update or supersede the stale fact. Do not silently propagate both.

## 3. Product and repository overview

Starlane Movies is a remote-friendly provisioning platform for Fire TV, Fire OS,
Android TV, and Google TV. It installs and configures official Kodi and Proton VPN,
provides a signed and allowlisted Kodi bootstrap path, and uses a constrained
Cloudflare control plane. Owner administration tooling is maintained separately.

Top-level source map:

| Area | Location | Primary technology | Responsibility |
| --- | --- | --- | --- |
| Setup application | `android-app/` | Kotlin 2.3.21, Jetpack Compose, Java 17, Gradle | D-pad-first setup, signed manifest consumption, verified downloads, pairing, bounded telemetry, official OAuth |
| Control plane | `control-api/` | TypeScript 5.8, Cloudflare Workers, D1, Wrangler, Vitest | Pairing, signed device requests, replay defense, bounded status/events, allowlisted commands, safe public Kodi redirects |
| Signed configuration | `config/` | JSON Schema, canonical JSON, Ed25519 | Versioned staged manifest, vendor/artifact pins, repositories, add-ons, skin, telemetry |
| Kodi bootstrap/repository | `kodi/repository.kodisetup/` | Kodi Python 3 add-on | Manifest verification, idempotent configuration, repository/add-on installation, skin activation and rollback |
| Production skin pipeline | `tools/skin_builder.py`, related Kodi inputs | Python, Kodi XML, Estuary-derived GPL source | Reproducible `skin.starlanemeridian` packages |
| Private experimental skin | `kodi/skin.starlane.movies/` | Kodi XML, Python, Titan BINGIE MOD-derived GPL source | Poster-led private interface and current widget experimentation |
| Release/tooling | `tools/` | Python, PowerShell | Validation, signing, packaging, profile export, vendor monitoring, branding |
| CI/release | `.github/workflows/` | GitHub Actions | Cross-subsystem CI, offline-signed release verification, review-only vendor monitoring |
| Branding | `assets/branding/`, `docs/BRAND_GUIDE.md` | PNG sources, Python/Pillow generation | Reproducible Starlane Movies visual identity |
| Operations/status | `docs/` | Markdown | Owner runbooks, security model, verified state, handoffs, incident evidence |

Important compatibility names remain intentionally unchanged even though the
user-facing product is Starlane Movies:

- Android package: `app.kodisetup.tv`
- production Kodi skin ID: `skin.starlanemeridian`
- repository/bootstrap ID: `repository.kodisetup`
- GitHub repository and existing public/control URLs

Renaming compatibility identifiers is a migration project, not a cosmetic edit.

## 4. Current verified baseline

The authoring GPT must verify these against the repository before encoding them:

- Current checked-in commit: `4aad405`.
- Private skin source: `skin.starlane.movies` 2.2.16.
- Reference Kodi generation: Kodi 21.3 / Omega.
- Reference hardware family: Amazon Fire TV, Fire OS based on Android 9.
- Production rollback skin: `skin.starlanemeridian` 1.2.4.
- Private rollback chain includes 2.2.15/2.2.14 and the older operational fallback
  2.2.8; use the exact current technical handoff for the immediate order.
- Published release remains the separately documented `v0.3.8-test` stream.
- The private experimental skin is not part of the signed production manifest.

Private skin 2.2.16 Home behavior:

- One Home renderer serves Home, New & Popular, TV Shows, Movies, Live TV, Sports, and
  Categories.
- One bounded vertical grouplist owns vertical motion.
- Poster rows use a fixed 371-pixel stride.
- Home vertical and horizontal scrolling use 150 ms `sine/out`.
- Adjacent rows stay instantiated and fade as complete groups between 35% and 100%.
- Poster lists preload two items and dynamic artwork uses background loading.
- The selected card owns its focus border; there is no detached fixed-focus overlay.
- Hero/details updates are deferred by 150 ms and guarded by the latest widget/item
  identity; the hero then crossfades over 100 ms.
- Home’s first two rows are local Continue Watching movies and episodes through
  Umbrella.
- `service.py` checks Umbrella’s local `watched.db` `progress` table and publishes
  `StarlaneHasContinueMovies` and `StarlaneHasContinueEpisodes`.
- Empty Continue Watching controls are omitted before their plugin directories load,
  preventing asynchronous removal from displacing or visually invalidating the first
  populated row.

Provider intent:

- Umbrella handles non-live discovery and playback routes.
- CocoScrapers is Umbrella’s configured external provider.
- Mad Titan handles Sports and part of Live TV.
- The Crew supplies the explicit Live TV fallback row currently present.
- FenLight must remain absent unless the owner explicitly changes provider policy.
- Provider upgrades, credential changes, and route substitutions are separate work.

## 5. Non-negotiable security, privacy, and authority rules

The generated `AGENTS.md` must state these prominently and tersely:

- Never print, commit, or copy private keys, Android keystores, vault contents,
  Cloudflare Access secrets, OAuth tokens, pairing codes, provider credentials, or
  full sensitive settings files.
- Owner administration tooling remains outside this repository and loopback-only.
- Cloud commands remain a closed enum. Never add arbitrary shell, ADB, URL, Python,
  Kodi built-in, or remote-desktop capability.
- Never expose ADB port 5555 to the internet.
- Do not automate CAPTCHA, terms acceptance, account farming, registration submission,
  payment, or account transfer.
- Real-Debrid uses official device OAuth. Tokens remain on the TV.
- Third-party Kodi repositories/add-ons require an exact owner-approved legal
  allowlist before publication.
- Android developer options, ADB approval, unknown-source permission, and package
  install confirmations remain user actions.
- Never add owner-tool configuration, vault data, or runnable administration tooling
  to the client repository.
- Back up exact device/profile/database state before a risky hardware mutation.
- Do not delete user data, progress databases, add-on settings, rollback skins, or
  backups unless the owner explicitly requests the exact destructive action.
- Do not publish, promote, deploy, commit, or push merely because implementation and
  tests pass. Obtain authority for the external state change.

Stop and ask the owner when work requires secrets, deletion, account/legal decisions,
trust-boundary expansion, stable promotion, or a materially different provider route.

## 6. Git and state-preservation rules

- Inspect `git status --short` before changes.
- Treat all pre-existing modifications as user-owned.
- Never use `git reset --hard`, broad checkout/restore, or destructive clean commands.
- Stage exact intended paths rather than assuming the whole dirty tree belongs to the
  current task.
- Generated and ignored `build/` files are evidence, not automatically publishable
  source.
- A local artifact is not release proof without its source commit, version, checksum,
  signature where applicable, and downloaded-public-byte verification.
- Fix generators/templates, not just generated device copies.
- Add a regression assertion for a confirmed defect whenever feasible.
- Keep source, device, public release, and documentation transitions separately
  recorded.

## 7. Kodi and skin architecture rules

These rules are central because most recent defects and wasted iterations occurred in
Home widget rendering.

### Rendering ownership

- A visual property must have one owner.
- The outer bounded grouplist owns Home vertical motion.
- Horizontal poster containers own horizontal motion.
- The complete row group owns row opacity.
- The card owns its selected border.
- The deferred Home snapshot owns large hero/details updates.
- Do not apply multiple slide/fade/visibility systems to the same property.
- Do not activate parallel hub windows for categories already served by Home.

Kodi animations are additive. Position-dependent slide matrices, fixed-focus offsets,
and native list scrolling can accumulate or conflict even when each looks correct in
isolation.

### Geometry

- Keep a constant row stride from header, poster height, spacing, and footer.
- Preserve the bounded widget viewport and overscan-safe regions.
- Empty, loading, missing-artwork, and provider-error states must not collapse row
  height or move following rows.
- Content type may vary, but Home visual geometry must not silently select another
  view style.
- Avoid saved/generated `widgetstyle.*` values restoring obsolete `highlight` layouts.

### Lifecycle

- Keep adjacent rows instantiated; reduce opacity instead of hiding/unrendering during
  movement.
- Never unload a row simply because it is not focused.
- Pre-check locally knowable empty rows before invoking a provider directory.
- Do not flush global widget properties after focus enters a widget container.
- Select and Right must be idempotent and use the same first-populated-row entry path.
- Rapid input must supersede stale presentation callbacks.
- Hold the previous hero until the newest committed art is ready.

### Performance

- Home scroll timing is intentionally 150 ms; inherited non-Home timing may differ.
- Kodi’s effective artwork preload is two items; do not increase it casually.
- Use background loading for dynamic poster, fallback, logo, and fanart textures.
- Do not increase provider item counts while diagnosing layout.
- Do not add automatic trailers or mandatory heavy helper services.
- Avoid background Live TV widgets that enumerate slow/blocking provider directories.
- Separate provider latency from renderer defects using static/local fixtures.
- Treat `ReloadSkin()` as expensive. The current local progress gate uses it only on a
  state transition while Home is active; future work should measure before increasing
  polling or reload frequency.
- The current service checks a small local SQLite table every two seconds. Do not add
  network work, artwork work, full-table scans, or database writes to that loop.

### Skin Shortcuts

Packaged defaults do not necessarily control a live profile. Saved profile files under
`userdata/addon_data/script.skinshortcuts/` can override them and regenerate stale
routes or styles.

For menu changes:

1. Stop Kodi.
2. Back up only the affected saved `.DATA.xml` files, generated include, and hash.
3. Deploy source.
4. Use a valid neutral `<includes />` as the packaged generated file.
5. Remove only the exact private-skin hash when regeneration is required.
6. Run Skin Shortcuts `buildxml`.
7. Pull and inspect the generated include.
8. Count expected provider/style references.
9. Remove any temporary one-shot `autoexec.py`.

Do not restore old saved FenLight menu backups during a normal Umbrella deployment.

## 8. Failed implementation avenues and reusable lessons

The `AGENTS.md` knowledge scaffold must preserve these as incident records rather than
repeating their full narrative in the root file.

### Competing vertical animation systems

- Symptom: rows drifted, clipped, overlapped, or accumulated offsets.
- Failed avenue: per-position `Container(...).Position` slide matrices combined with
  native scrolling and a fixed-focus workaround.
- Root cause: Kodi animations are additive and multiple mechanisms modified vertical
  position.
- Durable rule: one bounded grouplist owns vertical movement.

### Hiding or unrendering adjacent rows

- Symptom: lag/frozen-looking transitions and unstable geometry.
- Failed avenue: visibility conditions removed non-focused rows to avoid overlap.
- Root cause: Kodi had to unload/recreate controls and artwork during navigation.
- Durable rule: keep selected-category rows instantiated and fade the whole row.

### Parallel Home and hub renderers

- Symptom: different first frames for hover, Select, and Right; occasional mixed view
  geometry or doubled rendering.
- Failed avenue: category clicks activated separate Bingie hub windows while hover
  populated Home.
- Root cause: two view lifecycles and inconsistent state-reset paths.
- Durable rule: one Home renderer and one idempotent entry sequence.

### Mixed poster/highlight widget styles

- Symptom: clipped or invisible cards despite available metadata/background art.
- Failed avenue: adjusting coordinates while stale generated `widgetstyle=highlight`
  state could still select another layout.
- Root cause: saved/generated Skin Shortcuts properties overrode packaged defaults.
- Durable rule: normalize Home to poster geometry and verify the generated include.

### Mismatched scroll timings

- Symptom: vertical movement felt quicker than horizontal movement and overall widget
  navigation appeared to lag.
- Failed avenue: tuning only the outer grouplist while horizontal lists inherited a
  600 ms global scroll.
- Root cause: different axes used different timing includes.
- Durable rule: use the Home-only 150 ms timing on both axes; leave non-Home behavior
  scoped separately.

### Synchronous details and artwork churn

- Symptom: rapid poster movement caused stale hero/details or visible stalls.
- Failed avenue: committing large metadata/art changes on every transient focus event.
- Root cause: presentation work competed with navigation and texture loading.
- Durable rule: update pending focus immediately, defer/guard the snapshot, and commit
  only the final focus target.

### Literal nested include parameters

- Symptom: the first focused row failed and Kodi logged `Misplaced [` or boolean
  expression parsing errors.
- Failed avenue: passing `$PARAM[widgetid]` through a nested include where the inner
  scope did not resolve it.
- Root cause: Kodi include-parameter expansion scope.
- Durable rule: construct the complete guard where the numeric widget ID exists; give
  nested includes a safe literal fallback.

### Empty Continue Watching rows disappearing after provider load

- Symptom: after Umbrella returned no local-progress items, All-Time Best Movies became
  the first visible row; its hero and metadata worked, but its poster cards were
  invisible until moving down one row.
- Failed avenue: repeatedly changing Continue Watching routes, item rendering, and
  first-row focus behavior after the provider had already loaded an empty directory.
- Root cause: asynchronously removing the first generated controls changed the
  effective row/focus geometry after Home initialization.
- Durable rule: query the local progress table first and never instantiate/invoke an
  empty local Continue Watching widget.

### Assuming provider errors are skin errors

- Symptom: empty directories or logs suggested Home failure.
- Failed avenue: changing geometry/provider versions without isolating content.
- Root causes observed: Umbrella Trakt refresh HTTP 400 and Mad Titan’s missing local
  certificate file.
- Durable rule: reproduce with a local/static fixture, then compare live provider
  behavior. Do not upgrade or rewrite providers during a visual remediation.

### Treating generated defaults as authoritative

- Symptom: removed FenLight routes or old styles returned on device.
- Failed avenue: copying only packaged shortcut defaults.
- Root cause: profile-persisted Skin Shortcuts data regenerated the live include.
- Durable rule: preserve and deliberately regenerate the saved profile/cache pair.

### Inadequate frame instrumentation

- Symptom: a recording looked acceptable but could not prove 60 fps or a 50 ms maximum
  frozen frame.
- Failed avenue: relying on Fire TV `screenrecord` and Android `dumpsys gfxinfo`.
- Root cause: variable-frame-rate capture and Kodi’s native OpenGL renderer being
  outside meaningful Java-shell frame statistics.
- Durable rule: use these tools for qualitative geometry only; require external true
  60 fps capture for quantitative frame acceptance.

### ADB blocked by VPN

- Symptom: Windows socket error 10013 despite the correct device address.
- Failed avenue: repeated connection attempts without checking the host network
  boundary.
- Root cause: Proton VPN blocked LAN traffic.
- Durable rule: diagnose reachability once, then ask the owner to permit LAN traffic or
  pause VPN. Never silently alter VPN state.

### Kodi package repository routing

- Symptom: valid release assets could not be installed through Kodi’s expected
  repository path.
- Failed avenue: treating flat GitHub release assets as Kodi’s nested datadir.
- Root cause: Kodi requires `/datadir/addon.id/addon.id-version.zip`.
- Durable rule: use the strictly allowlisted Worker redirect for supported paths.

### Windows CRLF hash sidecars

- Symptom: a correct package hash was rejected.
- Failed avenue: emitting platform-default text line endings.
- Root cause: Kodi’s literal sidecar parsing exposed CRLF incompatibility.
- Durable rule: write and test exact LF-only checksum sidecar bytes.

### Empty Kodi string defaults

- Symptom: Bootstrap candidate failed while Estuary remained active.
- Failed avenue: writing unsupported empty internal string defaults.
- Root cause: Kodi rejected the setting representation.
- Durable rule: omit unsupported empty defaults and test settings XML on hardware.

### Automated release with empty environment values

- Symptom: Gradle reported `Tag number over 30 is not supported`.
- Failed avenue: assuming the GitHub `release` environment contained signing values.
- Root cause: all expected environment values, including the base64 keystore, were
  empty.
- Durable rule: verify required environment values through safe presence checks before
  packaging; never upload the manifest private key; retain the trusted local release
  path until automation is proven equivalent.

### Vendor semantic-version parsing

- Symptom: monitoring proposed Kodi 18.7.2 instead of 21.3.
- Failed avenue: parsing only three-part versions.
- Root cause: Kodi’s current two-part version was ignored.
- Durable rule: parse semantic variants explicitly and keep regression fixtures.

## 9. Why prior work consumed excessive tokens and how to prevent it

There is no repository-level token telemetry that attributes an exact cost to each
operation. The following are workflow causes inferred from the recorded task history
and should be presented as such, not as measured billing data.

### Main causes

- Re-reading very large handoffs and logs in full on multiple turns.
- Broad repository searches before narrowing the affected subsystem.
- Repeating web research after authoritative Kodi/provider behavior had already been
  captured locally.
- Dumping full logs, XML files, generated includes, and test output into context instead
  of extracting relevant lines.
- Running the full multi-subsystem suite during every hypothesis rather than using the
  focused private-skin tests first.
- Rebuilding, backing up, deploying, restarting, recording, and pulling complete device
  state for multiple speculative changes.
- Treating content-provider failure, empty-state lifecycle, focus state, geometry, and
  texture loading as one undifferentiated problem.
- Making successive visual tweaks without first writing a falsifiable cause and the
  smallest experiment that could disprove it.
- Repeating already established facts in commentary, plans, and handoffs.
- Failing to check the local Umbrella progress database before invoking the empty
  Continue Watching directories.
- Carrying chronological history in primary startup documents, forcing every later
  agent to ingest obsolete versions and superseded explanations.

### Required token-efficient workflow

1. Read root `AGENTS.md` and the knowledge index.
2. Inspect `git status`, the task’s exact paths, and the newest current-state record.
3. Retrieve at most the two or three topic records matching the task’s subsystem,
   symptom, provider, or file paths.
4. State one primary hypothesis and one distinguishing observation.
5. Run the smallest read-only check that can confirm or reject it.
6. Extract log lines with `rg` and bounded context; do not print whole logs.
7. Inspect targeted XML elements or functions; do not ingest whole generated files.
8. Run focused tests during iteration.
9. Build/deploy only after static checks support the hypothesis.
10. Run the full relevant suite once before handoff/release.
11. Record the confirmed finding once in the knowledge scaffold and link to evidence.

Additional rules:

- Prefer repository source and official captured documentation over repeated browsing.
- Browse only when information is unstable, absent, or a precise external reference is
  required; use primary Kodi/add-on/upstream sources.
- Cache stable research as a short knowledge record with URL, retrieval date, and
  applicable version.
- Batch related read-only device checks into one ADB session.
- Pull only bounded logs or exact files needed for comparison.
- Hash backups before and after instead of repeatedly copying/inspecting their contents.
- Do not create a new broad plan after every failed hypothesis; update the existing
  evidence ledger.
- Keep user updates concise: current hypothesis, evidence, action, result.
- Ask for missing user information only when it changes the implementation materially
  and cannot be discovered safely.

### Suggested task budgets

These are process limits, not hard guarantees:

- Startup: root `AGENTS.md`, index, status, and no more than three routed documents.
- Initial search: target one subsystem and five or fewer search concepts.
- Log inspection: matched lines plus 10-20 lines of context.
- Iteration: one source change and focused validation before device deployment.
- Documentation: update one current fact and one incident/decision record; do not copy
  the same narrative into several handoffs.

If a task exceeds a budget, the agent should explain which new evidence justified the
expansion.

## 10. Kodi/resource optimization doctrine

Future work must consider both agent efficiency and runtime efficiency.

### CPU and UI thread

- Avoid rapid `ReloadSkin()` cycles, synchronous plugin enumeration during navigation,
  automatic trailers, and per-focus heavy metadata work.
- Keep polling local, bounded, read-only, and inexpensive.
- Do not perform network requests from the local progress gate.
- Prefer event/state transitions over repeated unconditional refreshes.
- Never add full database scans to Home navigation.

### Memory and controls

- Keep only the current category’s row set in Home.
- Keep adjacent rows within that set instantiated to avoid churn.
- Do not instantiate parallel Home/hub renderers.
- Cap widget item counts and use two-item artwork preload.
- Preserve a single poster geometry rather than loading multiple view families.

### GPU and textures

- Use background loading for dynamic art.
- Avoid simultaneous large hero changes while list motion is active.
- Hold and crossfade the previous hero rather than blanking it.
- Keep overlays, focus borders, and opacity transitions synchronized at the largest
  sensible group level.
- Avoid artwork or masks outside the bounded viewport.

### Storage and I/O

- Avoid duplicate local databases or helper services when Umbrella/Kodi already owns
  progress state.
- Use indexed/limited SQLite existence queries.
- Back up material device state once per candidate, not once per command.
- Retain rollback evidence under ignored `build/` with hashes and a concise manifest.
- Do not copy sensitive settings into the repository.

### Network and providers

- Do not increase simultaneous Umbrella fetches to hide layout defects.
- Prefer public TMDb discovery routes where personalization is not required.
- Do not enumerate Live TV providers in background Home widgets when they can block.
- Bound loading/error states without collapsing geometry.
- Separate route validation, provider response timing, artwork timing, and skin
  rendering into distinct measurements.

## 11. User-experience optimization doctrine

- Design for a television viewed at distance with D-pad input.
- Maintain one obvious focus target and do not rely on colour alone.
- Preserve generous overscan-safe margins.
- Use predictable target sizes and consistent navigation direction.
- Hover, Select, and Right must not reveal different renderers or first frames.
- Left returns to the menu while preserving the category but without stale offsets.
- Keep animations restrained, normally 150-280 ms.
- Never allow an empty/error/loading row to shift another row.
- Missing art must use a bounded fallback.
- Warm cached transitions should feel immediate and avoid frozen frames.
- Avoid long titles, metadata, or labels colliding with focus surfaces.
- Keep the interface usable without optional helper services.
- Never expose credentials, viewing history, payment data, or unnecessary device facts
  in UI telemetry.

## 12. Validation strategy by change type

### Private Kodi skin

During iteration:

- parse changed XML;
- compile changed Python;
- run focused tests in `tools/test_experimental_skin.py`;
- run `git diff --check`;
- inspect provider/style counts in the generated include.

Before delivery:

- run the full Python/Kodi suite;
- build the ZIP and verify version, top-level path, forward slashes, size, and SHA-256;
- preserve the previous skin/profile/database/log state;
- test cold and warm Home behavior on hardware;
- inspect bounded Kodi log matches for XML, expression, control, exception, and fatal
  errors;
- test empty, populated, loading, missing-art, provider-error, and rapid-navigation
  states as relevant;
- restore synthetic personal-progress fixtures byte-for-byte.

### Python/configuration/release

- run focused unit tests, then `python -m unittest discover -s tools -p "test_*.py"`;
- run `python -m compileall -q kodi tools`;
- validate and verify the manifest with the public key;
- never expose the private key in commands or output;
- verify deterministic paths, exact LF sidecars, hashes, and signatures.

### Control API

- work in `control-api/`;
- run `pnpm check` and `pnpm test`;
- preserve closed command enums and authentication boundaries;
- treat deployment and D1 migration as separately authorized external mutations.

### Android

- work in `android-app/`;
- run focused unit tests, then `:app:testDebugUnitTest :app:lintDebug`;
- preserve Java 17, API 25 minimum, API 36 target/compile, D-pad behavior, signature and
  hash verification, and user-visible installer permissions;
- physical Fire TV and Android TV/Google TV are separate acceptance targets.

### Public release

- require explicit release authority;
- pass all CI-equivalent checks;
- assemble a draft while retaining rollback assets;
- download every asset and compare bytes;
- verify signature and public routes;
- test Bootstrap apply and second-launch confirmation/rollback clearing;
- update current status and leave the repository clean.

## 13. Required AGENTS.md structure

Keep root `AGENTS.md` approximately 2,500-4,000 words. If it approaches 6,000 words or
roughly 10,000-12,000 tokens, move detail into the knowledge scaffold before adding
more. The root should contain:

1. Mission and priority order.
2. Mandatory startup sequence.
3. Source-of-truth precedence and state separation.
4. Security/privacy stop conditions.
5. Dirty-worktree and external-mutation rules.
6. Concise repository/subsystem routing table.
7. Token-efficient investigation protocol.
8. Kodi/resource/UX invariants.
9. Test escalation ladder.
10. Knowledge retrieval and update protocol.
11. Links to current-state, subsystem, runbook, decision, and incident indexes.

Do not put these in root `AGENTS.md`:

- long release histories;
- every historical version/hash;
- full provider route inventories;
- complete test output;
- device IP addresses or ephemeral process IDs;
- duplicated content already stored in a topic record;
- obsolete findings without an explicit reason they remain relevant.

## 14. Scaffolding knowledge schema

Create this structure, adapting names only when repository conventions require it:

```text
docs/agent-knowledge/
  INDEX.md
  index.yaml
  current/
    source-state.md
    deployed-state.md
    public-release-state.md
  subsystems/
    android-app.md
    control-api.md
    signed-config-release.md
    kodi-bootstrap.md
    production-skin.md
    private-skin.md
  runbooks/
    focused-validation.md
    private-skin-device-test.md
    skin-shortcuts-regeneration.md
    release-and-rollback.md
    safe-adb-diagnostics.md
  decisions/
    DECISION_INDEX.md
    ADR-NNN-short-title.md
  incidents/
    INCIDENT_INDEX.md
    INC-NNN-short-title.md
  research/
    RESEARCH_INDEX.md
    kodi-skin-engine.md
    provider-routes.md
  archive/
    YYYY/
```

`INDEX.md` is the human-readable map. `index.yaml` is the compact machine-routing
index. A future validation tool should ensure every active record is indexed and every
index path exists.

### Index record schema

Use stable IDs and concise summaries:

```yaml
schema_version: 1
updated_at: 2026-07-28
records:
  - id: subsystem.private-skin
    title: Private Kodi skin architecture
    kind: subsystem
    status: active
    path: docs/agent-knowledge/subsystems/private-skin.md
    summary: One-renderer Home architecture, widget lifecycle, providers, and bounds.
    tags: [kodi, skin, home, widgets, umbrella, performance]
    path_globs:
      - kodi/skin.starlane.movies/**
      - tools/test_experimental_skin.py
    read_when:
      - editing private skin XML or Python
      - diagnosing Home widgets, focus, clipping, or lag
    authority:
      - kodi/skin.starlane.movies
      - tools/test_experimental_skin.py
    verified_at: 2026-07-28
    supersedes: []
    related:
      - incident.empty-continue-watching
      - runbook.private-skin-device-test
    size_hint: medium
```

Required fields:

- `id`: immutable namespaced identifier.
- `title`: human-readable title.
- `kind`: `current`, `subsystem`, `runbook`, `decision`, `incident`, `research`, or
  `archive`.
- `status`: `active`, `superseded`, `needs-verification`, or `archived`.
- `path`: repository-relative record path.
- `summary`: one or two sentences suitable for retrieval without opening the file.
- `tags`: controlled vocabulary.
- `path_globs`: source paths that trigger retrieval.
- `read_when`: task/symptom triggers.
- `authority`: files or live checks that can verify the record.
- `verified_at`: date of last verification.
- `supersedes`: stable IDs replaced by this record.
- `related`: other stable IDs.
- `size_hint`: `small`, `medium`, or `large`.

Optional fields:

- `versions`;
- `providers`;
- `device_scope`;
- `security_impact`;
- `expiry_or_review`;
- `evidence_paths`;
- `official_sources`.

### Topic record template

Each Markdown record should begin with machine-readable front matter:

```yaml
---
id: incident.empty-continue-watching
kind: incident
status: active
verified_at: 2026-07-28
applies_to: skin.starlane.movies >=2.2.16
tags: [kodi, skin, umbrella, empty-state, focus]
authority:
  - kodi/skin.starlane.movies/service.py
  - kodi/skin.starlane.movies/shortcuts/template.xml
  - tools/test_experimental_skin.py
supersedes: []
---
```

Then use:

- `Summary`
- `When to read this`
- `Invariant or decision`
- `Evidence`
- `Known failure modes`
- `Minimal diagnostic`
- `Safe implementation pattern`
- `Validation`
- `Rollback`
- `Related records`

Keep records factual and compact. Link to logs/screenshots/build evidence instead of
embedding large output.

### Decision records

Use ADR-like records for architectural choices that future agents might otherwise
undo, including:

- one Home renderer;
- one vertical scroll owner;
- private versus production skin separation;
- compatibility identifiers remaining unchanged;
- schema-driven allowlists;
- local-only progress using Umbrella’s existing database;
- offline manifest signing;
- external owner-tool separation and a closed command enum.

Each decision must contain context, decision, alternatives rejected, consequences,
revisit conditions, and verification.

### Incident records

Create incidents for the reusable failures in section 8. An incident is not a diary.
It should identify:

- observable symptom;
- affected versions/components;
- false leads or failed avenue;
- confirmed root cause;
- smallest reproducer;
- fix;
- regression coverage;
- evidence;
- prevention rule.

### Research records

Cache stable external findings with:

- official/upstream URL;
- retrieval date;
- applicable Kodi/add-on version;
- concise conclusion;
- local architectural consequence;
- conditions requiring refresh.

Do not paste long documentation excerpts. Prefer a short paraphrase and direct link.

## 15. Retrieval protocol as the knowledge base grows

The generated `AGENTS.md` must instruct agents to retrieve knowledge in this order:

1. Load root `AGENTS.md`.
2. Read `docs/agent-knowledge/index.yaml`, not every record.
3. Match the task against `path_globs`, `tags`, and `read_when`.
4. Load the current-state record for the state being changed.
5. Load the single subsystem record.
6. Load only directly related runbook/incident/decision records.
7. Expand to related records only when evidence shows the task crosses boundaries.

Default retrieval cap: three topic records in addition to root/current state. Exceed
the cap only when the task spans subsystems or the initial evidence contradicts the
selected records.

Recommended retrieval command patterns:

```powershell
rg -n "widgets|clipping|Umbrella" docs/agent-knowledge/index.yaml
rg -n "kodi/skin.starlane.movies" docs/agent-knowledge/index.yaml
rg -n "INC-|ADR-" docs/agent-knowledge/incidents docs/agent-knowledge/decisions
```

Agents should search the index first, then exact source, then bounded evidence. They
should not recursively ingest the entire knowledge directory.

## 16. Living-document maintenance and compaction

Update knowledge when a finding changes future implementation, diagnosis, validation,
security, performance, resource use, token use, or user experience.

Required update triggers:

- a confirmed root cause;
- a failed avenue likely to be repeated;
- a new invariant or architectural decision;
- a changed source/deployed/public version;
- a new rollback path;
- a new provider route or dependency;
- a measured performance/resource limit;
- a new security boundary;
- a test or tool that materially shortens future work;
- a stale or contradictory fact.

Do not update knowledge for:

- transient command output with no reusable result;
- speculative hypotheses disproved immediately;
- ephemeral PIDs;
- temporary device addresses unless a runbook requires a placeholder;
- repeated test passes with no change in coverage.

Maintenance rules:

- Update the smallest relevant record.
- Change root `AGENTS.md` only for project-wide rules or routing.
- Mark old records `superseded`; do not leave competing active truths.
- Move superseded chronological detail to `archive/YYYY/`.
- Preserve stable IDs and use `supersedes`.
- Update `verified_at` only after actual verification.
- Add or update a regression test when knowledge reflects a code defect.
- Keep summaries under roughly 60 words.
- Keep active topic records generally below 1,500 words.
- Split a record when it contains more than one independently retrievable concern.
- Review the index after every material milestone and before releases.

Suggested future validator:

`tools/validate_agent_knowledge.py`

It should check schema version, required fields, unique IDs, valid paths, valid related
IDs, no cycles in `supersedes`, accepted tags/status/kinds, stale verification dates,
and root/index size budgets. Add it to Python tests and CI only after its schema is
reviewed.

## 17. Task execution pattern to encode

Every agent task should follow:

1. Classify: answer, diagnose, implement, deploy, release, or monitor.
2. Route: index to current state, subsystem, and relevant incident/runbook.
3. Inspect: Git status and exact affected source.
4. Hypothesize: one primary cause and a discriminating check.
5. Reproduce: smallest safe static/local test before hardware.
6. Change: smallest source-level fix that preserves invariants.
7. Validate: focused checks first, full relevant suite once.
8. Device-test: only when needed and after preserving exact rollback state.
9. Document: current fact plus decision/incident when reusable.
10. Mutate externally: only with authority.
11. Handoff: outcome, evidence, remaining uncertainty, rollback, and changed paths.

For visual issues, explicitly separate:

- row/control existence;
- layout geometry;
- focus/navigation state;
- animation ownership;
- generated Skin Shortcuts state;
- provider directory completion;
- artwork loading;
- deferred details/hero state.

Do not tune all seven simultaneously.

## 18. Acceptance criteria for the generated guidance

The new root `AGENTS.md` and scaffold are acceptable only if:

- a new agent can identify the correct subsystem and first validation command without
  reading all historical handoffs;
- security stop conditions are visible in the root document;
- dirty-worktree, external deployment, and release authority are unambiguous;
- current source, device, and public-release state are explicitly separated;
- the private-skin one-renderer and resource constraints are preserved;
- failed approaches are searchable without bloating root context;
- token-efficient retrieval has a default cap and an escalation rule;
- knowledge records have stable IDs, verification dates, authority, and supersession;
- optimization findings have a defined update trigger;
- stale facts can be retired without deleting useful history;
- no secret, credential, private-key material, or sensitive full settings file is
  copied into the guidance;
- the scaffold can be validated mechanically later.

## 19. Suggested prompt for the authoring GPT

Use the following as the high-level instruction after providing this file and repository
access:

> Create a root `AGENTS.md` and the initial `docs/agent-knowledge/` scaffold from
> `docs/AGENTS_MD_AUTHORING_HANDOFF.md`. Read every required source-of-truth document
> named there, inspect the current repository state, and reconcile stale facts before
> writing. Keep root `AGENTS.md` compact and directive; put subsystem detail,
> historical failures, decisions, runbooks, current state, and cached research in
> indexed records. Optimize future work for security, token use, Kodi/Fire TV resource
> use, and D-pad user experience. Do not modify product behavior, deployed systems,
> secrets, releases, or Git history. Validate all index links and report any unresolved
> contradictions rather than guessing.

## 20. Initial records to create

At minimum, the first authoring pass should create:

- the three current-state records;
- all seven subsystem records listed in section 14;
- focused-validation, private-skin device test, Skin Shortcuts regeneration, release
  and rollback, and safe ADB runbooks;
- decisions for trust boundaries, compatibility IDs, private/production skin split,
  one Home renderer, and offline signing;
- incidents for competing animations, hidden-row churn, parallel hubs, stale Skin
  Shortcuts, nested parameters, empty Continue Watching controls, provider/skin
  confusion, ADB/VPN, CRLF sidecars, repository paths, empty release secrets, and
  semantic-version parsing;
- research summaries for Kodi animations, group lists, dynamic content/art loading,
  BINGIE fixed-focus behavior, and the provider route contracts actually in use.

Create these records by consolidating existing documents. Do not duplicate the entire
historical prose. Where an existing handoff is still the best evidence, link to its
section and give only the reusable conclusion.

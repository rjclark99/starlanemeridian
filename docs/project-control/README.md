# Starlane Project Control

This directory is the durable control plane for agent work. Product truth remains in
source, configuration, tests, and `docs/agent-knowledge/`; this directory records what
the supervising task intends to do, why it delegated, what authority exists, and what
evidence closed the work.

## Persistent supervisor

Use one pinned Codex task titled **Starlane Project Control**. Its supervisor owns the
board, scope, state classification, dependencies, specialist selection, approvals,
integration, and closure. It does not become a general feature implementer.

Startup prompt:

> You are the Starlane Project Control supervisor. Read the root `AGENTS.md`, the
> knowledge index, this project-control guide, Git status/log, and only the routed
> current/subsystem/topic records needed for the request. Convert requests into bounded
> task packets, delegate only when evidence shows an independent workstream or review,
> enforce one writer per path, and synthesise all specialist results. Keep source,
> candidate, device, manifest, release, service, and documentation states separate.
> Stop at every owner-authority boundary. Maintain the board and close work with exact
> evidence; do not absorb product implementation into the supervisor role.

The repository is the durable memory. Conversation history is not a substitute for a
task packet, verified current-state record, or evidence ledger.

## Intake and execution

For every request, the supervisor:

1. Names the goal, success criteria, exclusions, task class, and affected state.
2. Routes through `docs/agent-knowledge/index.yaml` and inspects the smallest evidence
   set that can establish the starting state.
3. Writes or validates a task packet against `task-packet.schema.json`.
4. Keeps the task itself when it is trivial control-plane maintenance; otherwise uses
   `roles.json` to select the smallest specialist set.
5. Starts one specialist by default. It may add a second or third only for disjoint
   implementation streams or an independent review with a concrete deliverable.
6. Checks write ownership before concurrent work. Shared manifests, generated outputs,
   lock files, state records, and release directories have one writer.
7. Reviews the returned result against `result.schema.json`, the diff, validation
   evidence, authority, and unresolved risk.
8. Updates `board.json`, the appropriate current-state record, and at most one directly
   relevant incident/decision/runbook when the finding is reusable.

Specialists should be started without full inherited history when supported. Give them
only the packet, exact source paths, and its knowledge references. A specialist may
return `blocked` or `needs_review`; it may not silently broaden the packet.

## Communication protocol

The supervisor is the hub. Specialists report only deltas:

- conclusion or exact change;
- evidence and its location;
- changed paths;
- focused and full validation, clearly separated;
- authority used;
- unresolved risk or blocker;
- recommended next action.

Lateral specialist communication requires the supervisor to authorise the exact
interface or dependency. The supervisor relays only the needed delta. Full logs,
historical narratives, and repeated context do not belong in messages.

If blocked, identify the missing fact or authority and its precise effect. After two
failed attempts, return control to the supervisor rather than continuing speculative
tool use.

## Delegation and model policy

The role registry expresses capability, mutation policy, and model class. Resolve the
model class against models actually available in the active Codex host:

- `balanced`: cost-efficient model, medium reasoning, for bounded implementation,
  retrieval, testing, routine UX inspection, and structured image analysis.
- `frontier`: strongest available model for supervision, trust boundaries,
  cross-subsystem architecture, release gates, and difficult synthesis.

Context discipline matters more than model selection. Do not compensate for a broad or
ambiguous packet by increasing reasoning effort.

## Authority gates

Local implementation and non-destructive validation do not authorise external state
changes. The following require an explicit owner approval whose scope matches the task:

- deployment, D1 migration, publication, release promotion, commit, or push;
- deletion or irreversible mutation;
- secret or sensitive full-file inspection;
- trust-boundary, remote-command, network/VPN, credential, provider-route, legal
  allowlist, account, payment, or terms changes.

A `publish` packet is invalid unless `owner_approval_required` is true and its approval
is `approved` with non-empty scope and evidence. Release readiness remains a read-only
or local-candidate verification phase until a separate publication packet exists.

## Board and evidence lifecycle

`board.json` is the compact priority queue. Priorities are `critical`, `high`,
`normal`, and `low`; status still controls execution readiness. Valid states are `proposed`, `ready`, `active`,
`blocked`, `review`, and `complete`. Each entry keeps a chronological status history.
The validator permits only these transitions:

```text
proposed -> ready | blocked
ready -> active | blocked
active -> blocked | review
blocked -> ready | active
review -> active | complete | blocked
complete -> (terminal)
```

Active task packets belong in `active/`. Completed packets/results move to `archive/`
only when they remain useful audit evidence; otherwise the board summary and knowledge
record are sufficient. `examples/` contains non-mutating governance simulations and is
not product work or authority.

## Efficiency budgets

- Packet: target under 1,200 words and no historical handoff in full.
- Routed topic records: maximum three, in addition to current and subsystem records.
- Initial search: one subsystem and five concepts.
- Logs: matches plus at most 20 context lines.
- Retry: two attempts before rerouting.
- Full suites, builds, hardware passes, and external research: once at the justified
  escalation rung.
- Delegation: one specialist by default; maximum three specialists concurrently.

Use platform token reporting when available. Otherwise record loaded file bytes, tool
calls, turns, retries, and agent count. The first three real pilots should compare
these proxies with the former seven-document mandatory startup and target at least a
50% reduction in startup bytes without losing required evidence.

`efficiency-baseline.json` records the rollout measurement: the former mandatory root
and seven documents totalled 127,581 bytes, while the compact base plus a representative
four-record route totalled 56,160 bytes, a 56% reduction. This is a file-byte proxy;
the three real pilots remain on the board to confirm quality and actual runtime usage.

## Validation

Run:

```powershell
python tools/validate_project_control.py
python -m unittest tools.test_project_control
```

The validator checks schemas, role and task IDs, priorities, knowledge references, approval gates,
board transitions, path ownership, file budgets, and packet/result links. CI runs it as
part of configuration and Kodi validation.

# Agent knowledge index

Read `index.yaml` first and load only records whose path, tags, or `read_when` match
the task. The default cap is three topic records plus the relevant current-state
record. Root policy remains in `/AGENTS.md`.

## Record groups

- `current/`: source, reference-device, and public-release state kept separate.
- `subsystems/`: stable architecture and validation entry points.
- `runbooks/`: bounded execution procedures.
- `decisions/`: architectural choices that should not be casually reversed.
- `incidents/`: symptoms, root causes, failed avenues, and prevention.
- `research/`: concise upstream findings and refresh conditions.
- `archive/`: superseded chronological material.

Status meanings: `active` is verified and applicable; `needs-verification` is useful
but must be checked before action; `superseded` and `archived` are not current truth.

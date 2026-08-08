# Specialist result template

Return `<task-id>-result.json` matching `result.schema.json`. Summarise evidence; link
to exact files, tests, logs, artifacts, or state records instead of embedding raw output.

```json
{
  "task_id": "subsystem.concise-objective",
  "outcome": "complete",
  "finding_or_change": "What was established or changed.",
  "evidence": ["Exact evidence location or bounded observation."],
  "changed_paths": ["exact/changed/path"],
  "focused_validation": ["Focused command and result."],
  "full_validation": ["Full relevant suite and result, or empty when not yet run."],
  "unresolved_risks": ["Remaining material uncertainty, or an empty list."],
  "authority_or_approval_used": "Exact authority used; state when none was required.",
  "recommended_next_action": "One concrete next action or no further action."
}
```

`complete` means the packet is satisfied, not that a local candidate is deployed or
published. Use `blocked` for missing authority/facts and `needs_review` when supervisor
integration or an independent gate remains.

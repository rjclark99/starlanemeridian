# Task packet template

Create `<task-id>-task.json` and validate it against `task-packet.schema.json`. Copy an
example packet, then replace every value; do not leave generic text or inferred owner
approval. Keep the complete packet below 1,200 words.

```json
{
  "task_id": "subsystem.concise-objective",
  "goal": "One bounded outcome.",
  "success_criteria": ["Observable acceptance condition."],
  "task_class": "implement",
  "affected_state": "source",
  "specialist_role": "feature_implementer",
  "allowed_paths": ["exact/subsystem/path"],
  "allowed_tools": ["repository search", "focused tests"],
  "prohibited_actions": ["external mutation", "scope expansion"],
  "knowledge_references": ["subsystem.relevant-id"],
  "primary_hypothesis": "A falsifiable explanation or implementation premise.",
  "discriminating_check": "The smallest observation that separates it from alternatives.",
  "required_outputs": ["bounded result", "validation evidence"],
  "validation_rung": 3,
  "owner_approval_required": false,
  "owner_approval": {"status": "not-required", "scope": "", "evidence": ""},
  "context_budget": {
    "max_packet_words": 1200,
    "max_topic_records": 3,
    "max_search_concepts": 5,
    "max_log_context_lines": 20,
    "max_retries": 2
  },
  "stop_conditions": ["State or authority no longer matches the packet."]
}
```

For `deploy` or `publish`, use `publication_executor`, set approval required to true,
and record non-empty approved scope and evidence. Never copy approval from another task.

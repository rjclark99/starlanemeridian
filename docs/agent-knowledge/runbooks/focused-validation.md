---
id: runbook.focused-validation
kind: runbook
status: active
verified_at: 2026-07-28
tags: [testing, validation, tokens]
authority: [.github/workflows/ci.yml, docs/AGENT_HANDOFF.md]
supersedes: []
---

# Focused validation

1. Inspect exact changed lines and run `git diff --check`.
2. Parse/compile the changed file.
3. Run the smallest regression test.
4. Run the subsystem suite.
5. Build only when static evidence supports the fix.
6. Verify artifact version, structure, paths, bytes, hash, and signature as applicable.
7. Preserve rollback state before hardware work.
8. Inspect bounded logs and relevant state cases.
9. Run the full relevant CI-equivalent suite once before delivery.

Do not run every subsystem for a documentation-only or isolated change. Explain any
validation gap and never convert a local pass into a deployment/release claim.

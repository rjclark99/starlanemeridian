---
id: decision.schema-allowlists
kind: decision
status: active
verified_at: 2026-07-28
tags: [schema, security, providers]
authority: [config/manifest.schema.json, SECURITY.md]
supersedes: []
---

# Schema-driven allowlists

Artifacts, repositories, add-ons, settings, providers, telemetry, and cloud commands
must be explicitly enumerated and validated. Plugin URLs are not arbitrary user or
cloud payloads.

Rejected: raw profile restoration and open command/provider fields. They weaken
review, legal approval, rollback, and security. New entries require owner-approved
scope, provenance, exact identifiers, tests, and failure isolation.

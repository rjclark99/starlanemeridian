---
id: incident.nested-params
kind: incident
status: active
verified_at: 2026-07-28
tags: [kodi, xml, includes]
authority: [docs/TECHNICAL_HANDOFF_2026-07-26.md]
supersedes: []
---

# Unresolved nested include parameters

## Summary

A literal nested `$PARAM[widgetid]` reached Kodi and caused `Misplaced [` and boolean
expression errors when the first row focused.

## Diagnose and prevent

Search the generated XML/log for unresolved parameters. Build the complete guard in
the outer scope where the numeric ID exists; give nested includes a safe literal
fallback. Add an assertion for the generated expression.

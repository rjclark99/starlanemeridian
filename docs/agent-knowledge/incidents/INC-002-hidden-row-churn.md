---
id: incident.hidden-row-churn
kind: incident
status: active
verified_at: 2026-07-28
tags: [kodi, widgets, performance]
authority: [tools/test_experimental_skin.py]
supersedes: []
---

# Hidden row control churn

## Summary

Visibility rules unloaded non-focused rows, producing frozen-looking transitions and
geometry/artwork recreation.

## Diagnose and prevent

Keep selected-category rows instantiated and bounded. Fade the complete row group
between idle and focused opacity. Test rapid vertical input and ensure no visibility
condition removes adjacent rows.

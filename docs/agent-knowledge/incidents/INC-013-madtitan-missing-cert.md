---
id: incident.madtitan-missing-cert
kind: incident
status: active
verified_at: 2026-07-28
tags: [kodi, madtitan, livetv, provider]
authority: [docs/TECHNICAL_HANDOFF_2026-07-26.md, tools/test_experimental_skin.py]
supersedes: []
---

# Mad Titan Live NetTV missing certificate

## Summary

Mad Titan 2.0.32’s `/lntv/categories` requires a client certificate/key pair omitted
from its official package. It raises `OSError`; skipping assignment produces an empty
configuration and later `NoneType` failure.

## Diagnose and prevent

Do not suppress or fabricate provider credentials. The private skin excludes this
route, uses The Crew for Live TV, and retains Mad Titan for Sports. Restore it only
after an upstream package supplies and successfully uses the pair.

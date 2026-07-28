---
id: runbook.skin-shortcuts-regeneration
kind: runbook
status: active
verified_at: 2026-07-28
tags: [kodi, skinshortcuts, widgets]
authority: [docs/TECHNICAL_HANDOFF_2026-07-26.md]
supersedes: []
---

# Skin Shortcuts regeneration

1. Stop Kodi.
2. Back up affected `.DATA.xml`, properties, hash, and generated include.
3. Deploy source with a valid neutral `<includes />`.
4. Recoverably retire only obsolete route-specific profile files.
5. Remove only the exact skin hash.
6. Start Kodi and invoke Skin Shortcuts `buildxml`.
7. Verify generated provider, style, and broken-route counts.
8. Restart cleanly and inspect include/control errors.
9. Remove temporary one-shot scripts or local forwards.

Packaged defaults do not override saved profile data. Never restore old FenLight or
obsolete provider backups unless deliberately rolling back.

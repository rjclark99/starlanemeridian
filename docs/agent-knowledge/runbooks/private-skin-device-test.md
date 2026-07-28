---
id: runbook.private-skin-device-test
kind: runbook
status: active
verified_at: 2026-07-28
tags: [kodi, skin, adb, testing]
authority: [docs/TECHNICAL_HANDOFF_2026-07-26.md]
supersedes: []
---

# Private skin device test

1. Verify source version/tests/package and device reachability.
2. Stop Kodi and preserve the installed skin, Skin Shortcuts profile/hash/include,
   settings, relevant database, and pre-test log.
3. Deploy only the candidate skin and regenerate shortcuts deliberately.
4. Restart cleanly and verify active ID/version.
5. Exercise cold/warm, hover, Select, Right, Left, rapid/reversed input, empty,
   populated, loading, error, and missing-art states relevant to the change.
6. Pull bounded logs and generated route/style counts.
7. Restore synthetic personal data byte-for-byte.

Use external true-60-fps capture for quantitative frame claims. Keep the prior private
skin/profile pair as immediate rollback; do not modify production rollback state.

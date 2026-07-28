---
id: incident.stale-provider-artwork-cache
kind: incident
status: active
verified_at: 2026-07-28
tags: [kodi, branding, artwork, cache]
authority: [tools/kodi_texture_cache.py, device visual verification]
supersedes: []
---

# Stale provider artwork cache

Symptom: provider metadata and names update, but Kodi still renders an old icon or
fanart. Re-copying the add-on files and rescanning packages does not reliably refresh
the image.

Cause: Kodi's texture database and hashed thumbnail files retain the prior bytes for
the same artwork URL.

Fix: stop Kodi; preserve `Textures13.db` and the exact matched cached thumbnails; use
`tools/kodi_texture_cache.py` on the copied database; remove only its exact provider
brand-art matches and corresponding thumbnail files; push the database; restart Kodi;
then wait for the selected item to reload before judging the image.

Rejected: clearing the complete thumbnail or texture cache. It discards unrelated
artwork, increases network and storage churn, and makes rollback harder.

Regression: `tools/test_kodi_branding_overlays.py` asserts that the selector matches
declared provider branding artwork but not unrelated provider/category icons.

# Reference-TV profiles

Starlane Meridian treats a configured TV as a design reference, not as an opaque
backup to restore. Run `tools/profile_export.py` against a locally pulled Kodi
home directory to produce a review-only inventory. The exporter copies no files
and excludes databases, history, caches, sources, favourites, account identifiers,
passwords, cookies, OAuth data, and token-like values.

The generated JSON is deliberately marked `installable: false`. Before an add-on
can enter the signed manifest, its legal distribution source, repository ID,
release URL, hash, required/optional status, and retained settings must be reviewed.
Menus and widgets will be compiled into the custom skin in the next phase.

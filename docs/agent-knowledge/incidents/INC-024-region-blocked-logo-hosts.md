---
id: incident.region-blocked-logo-hosts
kind: incident
status: active
verified_at: 2026-08-08
tags: [kodi, provider, branding, artwork, privacy, region]
authority: [downloaded public plugin.video.umbrella-6.7.81.3.zip, tools/build_kodi_branding_overlays.py, device visual verification]
supersedes: []
---

# Network and provider logos came from region-blocked third-party hosts

## Symptom

The Networks and Providers rows rendered without their logos, and some cards displayed text
stating that the content was not viewable in the viewer's region. Movie and TV rows were
unaffected.

## Root cause

Every pinned logo in `resources/lib/indexers/tmdb.py` was a remote URL: 78 on
`i.imgur.com`, 36 on `i.postimg.cc`, and zero local assets. The Starlane overlay builder
pinned the Providers row to that same mix rather than correcting it.

Imgur withdrew access for United Kingdom users in late 2025 and serves a region notice
*image* instead of the requested file. Kodi received a valid texture and drew it, so no
skin fallback ever triggered — the notice text the viewer saw was the image itself.

Three consequences followed from one cause: the rows silently degrade whenever either host
changes policy or availability; every Home render disclosed the television's address to two
third parties; and the acceptance requirement that provider and network artwork use
Starlane-safe local assets could not be met at all.

## Diagnostic signature

Because the two hosts fail independently, the split identifies the cause in seconds. In the
Providers row, Netflix, Disney+, Max, Paramount+ and Peacock are postimg-hosted and render;
Amazon, Apple TV+ and Hulu are imgur-hosted and do not. A failure affecting all eight is a
different problem.

## Fix and prevention

`localise_directory_logo_artwork` rewrites all 115 entries to
`resource://resource.images.studios.coloured/<Name>.png`. That resource add-on is already
in the signed package lock, so it is installed and hash-verified on the device and no
network request happens at all. This is better than vendoring the images: it adds no bytes
to the release and avoids redistributing third-party brand logos.

Nine display names ship under a different texture name and are aliased, including
`History Channel` to `History` and `Reelz` to `ReelzChannel`. Ten names have no bundled
logo and deliberately resolve to a missing texture so the skin's existing card fallback
renders; they remain local either way.

Two build guards prevent regression: the transform raises if fewer than 100 pinned logos are
found, and raises if either third-party host survives the rewrite.

Separately, the two overlay replacements that inject `starlane.umbrella.ready` were
unguarded, unlike their neighbours, so upstream text drift would have disabled the readiness
signal with no build failure. They now raise on drift.

## Known limitation

Kodi exposes no texture-loading state, so there is no honest way for the skin to show a
spinner while posters stream from TMDB; its widget spinner only covers an empty container.
Localising these logos removes the wait for these rows only. Movie and TV posters still
populate asynchronously and can briefly show the fallback card art.

## Related

`incident.stale-provider-artwork-cache` for artwork that changes without Kodi noticing, and
`decision.schema-allowlists` for keeping pinned artwork enumerated.

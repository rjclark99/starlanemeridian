# Starlane Movies technical handoff

Last verified: 28 July 2026, after physical deployment to the reference Fire TV.

## 29 July 2026 Bootstrap/provider remediation update

The repository baseline is now `dfa1ea7`; preserve its Android 0.5.2 Unknown Sources
automation. The coordinated successor is Bootstrap 1.1.12, branded provider 6.7.81.2,
and signed test manifest `2026.07.33`. Do not conflate it with public
`v0.5.4-test`, which remains Bootstrap 1.1.11/provider 6.7.81.1 from `10439cb`, and do
not push or publish the successor outside the coordinating task.

Two device-only lifecycle assumptions were corrected. Exact package registration must
be queried with Kodi JSON-RPC because `xbmcaddon.Addon()` rejects a disabled registered
add-on. Provider settings can be opened only after enablement, so an active Starlane
skin is temporarily parked on Estuary until provider readiness. Umbrella also mistakes
a four-part branded version for an upstream test build and queries the absent
`repository.umbrellakodi`; the 6.7.81.2 generator replaces that report with the
Starlane package lock. The direct reference-device overlay started and synchronized
6.7.81.2 with no matching repository/unknown-add-on/exception/error log entry.
Exact hashes, rollback and test evidence are in
`docs/agent-knowledge/incidents/INC-019-provider-overlay-bootstrap-order.md`.

## Read this first

This document is the technical handoff for the current private Starlane Movies skin
work. Repository files are the source of truth. Before changing the wider product,
also read:

1. `docs/AGENT_HANDOFF.md`
2. `docs/CURRENT_STATUS.md`
3. `docs/BRAND_GUIDE.md`
4. `README.md`
5. `SECURITY.md`

Do not discard or overwrite unrelated working-tree changes. The current skin changes
have been tested and deployed but have not been committed or pushed.

## Current outcome

- Private skin ID: `skin.starlane.movies`
- User-facing name: **Starlane Movies**
- Source and installed version: `2.2.20`
- Active Kodi skin: `skin.starlane.movies`
- Reference device: Amazon Fire TV `AFTKAUK001`
- Kodi package/version: `org.xbmc.kodi`, Kodi 21.3
- ADB endpoint: `192.168.1.64:5555`
- Production rollback skin: `skin.starlanemeridian` 1.2.4 remains installed
- Private operational rollback artifact: `skin.starlane.movies` 2.2.8
- Installable private-skin artifact:
  `build/skin.starlane.movies-2.2.20.zip`
- Artifact SHA-256:
  `9F97E03FD971B269A506D7E67230B030E72FC96B839147080D2B7084362B8D35`

Version 2.2.20 converts the private product to VOD-only. Live TV and Sports were
removed from packaged defaults, Home widget mappings, focus/control variables, and
the regenerated Skin Shortcuts include. The branding overlay builder and exact
texture-cache matcher now target Umbrella only. Mad Titan and The Crew add-on trees,
profile data, and cached plugin ZIPs were removed from the reference device after an
exact backup.

The regenerated include contains 106 Umbrella references and zero FenLight, Mad Titan,
The Crew, `starlane_livetv`, or `starlane_sports` references. A cold-start screenshot
confirmed the menu order Search, Home, New & Popular, TV Shows, Movies, Categories,
and My List. Kodi reports `skin.starlane.movies` 2.2.20 and Starlane Movies: On Demand
6.7.81.1 enabled, while neither retired video add-on is registered. Production skin
1.2.4 remains installed and untouched.

The exact pre-change device skin, both retired add-ons and their profile data, Skin
Shortcuts profile, private-skin settings, generated include, and log are preserved at
`build/vod-only-pre-2.2.20/`. Restore that backup to return to private build 2.2.19.
The VOD-only ZIP is 28,318,938 bytes.

## Historical 2.2.19 provider branding state

Version 2.2.19 completes the user-facing provider and private-skin branding pass.
The installed display names and overlay versions are:

- `plugin.video.umbrella` 6.7.81.1: **Starlane Movies: On Demand**
- `plugin.video.madtitansports` 2.0.32.1: **Starlane Movies: Sports**
- `plugin.video.thecrew` 3.2.0.1: **Starlane Movies: Live TV**

This is a presentation overlay only. Add-on IDs, plugin routes, settings keys, Python
identifiers, behaviour, licences, and upstream attribution are deliberately preserved.
The deterministic overlay builder is `tools/build_kodi_branding_overlays.py`; exact
installed originals and pre-deployment device state are preserved under
`build/branding-audit-2.2.19/`.

Kodi may continue to show cached provider artwork after the files change. Use
`tools/kodi_texture_cache.py` against a stopped-Kodi copy of `Textures13.db` to list
and remove only the exact top-level provider icon/fanart and Umbrella brand-art rows.
Back up the selected DB and cached thumbnail files before pushing the edited copy.
Never clear the global thumbnail or texture cache for this operation.

The device-generated include contains 106 Umbrella route references, zero FenLight
references, and no visible Umbrella, Mad Titan, or The Crew labels. Direct directory
smoke tests returned four On Demand search entries, 15 Sports entries, and 15 Live TV
entries. Cold-start logs detected all three branded versions and no new skin,
missing-control, animation, or provider execution error. Umbrella still logs its
pre-existing optional-repository lookup for internal ID `repository.umbrellakodi`.

Provider artifacts:

- `plugin.video.umbrella.zip`: 9,180,718 bytes,
  SHA-256 `33E4FDF17A5F4909A4BA40AA15D1CFAF78EAB6F77FF1244942D61FC486074B2E`
- `plugin.video.madtitansports.zip`: 4,955,990 bytes,
  SHA-256 `F9866ACEC5D04822B03BF3BD5F5AB8ED7AD199EFBE0BBA22D195201D2F0EC9C2`
- `plugin.video.thecrew.zip`: 439,855 bytes,
  SHA-256 `B79649163DEDB7E5F504CE26835423ED3EF2DC822346B66289AC97EF096C4287`

The official Mad Titan package also contains a pre-existing malformed
`resources/settings.xml` attribute. It was not introduced or rewritten by the
branding overlay. The focused add-on metadata XML, private-skin regression suite,
all 41 repository Python tests, Python compilation, package structure, routes, and
device presentation were verified.

Mad Titan's root directory obtains artwork from remote JSON after installation. A
central presentation sanitizer in its branded `default_process_item.py` replaces only
art URLs containing Titan, Thanos, wolfgirl, or metal-style branding markers with the
local Starlane Sports icon/fanart and rewrites provider-name fragments in displayed
labels. Its display boundary also removes the two inert no-review/social-media notices
and the final blank Google-proxy row that formed the remote root's last three entries.
Link, stream, and plugin route values are untouched. The remote directory
timed out during the immediate post-deployment visual retry; local compilation and the
focused overlay regression passed, and Kodi logged no Mad Titan Python error.

Version 2.2.18 converts Search from a direct Umbrella window activation to the same
focus-driven Home renderer used by the other widget-backed destinations. Its rows are
Search (`?action=tools_searchNavigator`), Discover Movies
(`?action=movieNavigator`), and Discover TV Shows (`?action=tvNavigator`). Direct
`movieSearch` or `tvSearch` widget paths are intentionally avoided because they can
open an input dialog while Kodi enumerates Home content. Search Select and Right now
enter the already rendered first row instead of creating a second window path. Search
and provider icon assets remain unchanged for a later branding pass.

The exact 2.2.17 device skin, Skin Shortcuts profile, settings, generated include, and
log are preserved under
`build/device-backups/search-hover-2.2.17-pre-2.2.18/`.

Version 2.2.17 removes Mad Titan's broken Live NetTV widget while retaining The Crew
for Live TV and Mad Titan's root for Sports. The official Mad Titan 2.0.32 ZIP omits
the `com.playnet.androidtv.ads.crt` and `.key` files that its `lntv.py` unconditionally
configures as a client-certificate pair. The original device module was restored after
a reversible guard proved that the pair is required: without it the upstream response
contains no configuration and the add-on fails with a later `NoneType` error.

Version 2.2.16 added `service.py`, a read-only local gate for Umbrella's
`watched.db`. Generated controls 2510 and 2520 are omitted before their plugin
directories load when no matching `movie` or `episode` progress record exists.
Device tests confirmed that the empty state renders All-Time Best Movies correctly,
while a reversible populated fixture restores both Continue Watching rows. The
original database was restored with matching SHA-256
`DE1409A86B479BEC49E0C7E30A0084C204FFDA71757537593DD4AE403B378B7D`.

The deployed, generated skin-shortcuts include was physically checked:

- 101 references to `plugin.video.umbrella`
- 0 references to `plugin.video.fenlight`
- 3 references to `plugin.video.madtitansports`
- 3 references to `plugin.video.thecrew`
- 0 references to `plugin.video.madtitansports/lntv/categories`

The generated file is:

`/sdcard/Android/data/org.xbmc.kodi/files/.kodi/addons/skin.starlane.movies/xml/script-skinshortcuts-includes.xml`

## Provider configuration

Umbrella and CocoScrapers are installed. The device-side Umbrella configuration was
verified after deployment:

```text
provider.external.enabled = true
external_provider.name = cocoscrapers
external_provider.module = script.module.cocoscrapers
```

Only these three settings were changed. The original complete Umbrella settings file
was preserved on the device as:

`userdata/addon_data/plugin.video.umbrella/settings.xml.starlane-backup-20260726`

Do not print, commit, or broadly copy Umbrella's complete `settings.xml`; it may contain
account configuration. A temporary local copy used during deployment was deleted.

Home's personalized Umbrella routes use Trakt-backed progress/history/recommendation
endpoints. They will be empty or unavailable until the owner authorizes Trakt inside
Umbrella. The public TMDb discovery rows do not require Trakt.

## Menu and widget mapping

All non-live destinations now use Umbrella. No FenLight path remains in the tracked
skin shortcuts.

### Home

| Label | Umbrella route |
|---|---|
| Continue Watching Movies | `?action=moviesUnfinished&url=traktunfinished` |
| Continue Watching TV Shows | `?action=calendar&url=progress` |
| Because You Watched Movies | `?action=movies&url=traktbasedonrecent` |
| Because You Watched TV Shows | `?action=tvshows&url=traktbasedonrecent` |
| Watch Again Movies | `?action=movies&url=trakthistory` |
| Watch Again TV Shows | `?action=calendar&url=trakthistory` |
| Search Movies | `?action=movieSearch` |
| Search TV Shows | `?action=tvSearch` |

All paths above use the prefix `plugin://plugin.video.umbrella/`.

### Movies

- Popular: `tmdbmovies&url=tmdb_popular`
- Trending Today: `movies&url=tmdbrecentday`
- In Theaters: `tmdbmovies&url=tmdb_nowplaying`
- Recently Released: `tmdbmovies&url=tmdb_discovery_released`
- Top Rated: `tmdbmovies&url=tmdb_toprated`
- Genres: `movieGenres&url=tmdb_genre`
- Upcoming: `tmdbmovies&url=tmdb_upcoming`
- In Progress submenu: `moviesUnfinished&url=traktunfinished`

### TV Shows

- Popular: `tmdbTvshows&url=tmdb_popular`
- Trending Today: `tvshows&url=tmdbrecentday`
- On the Air: `tmdbTvshows&url=tmdb_ontheair`
- New Shows: `tvshows&url=tmdb_newshows`
- Airing Today: `tmdbTvshows&url=tmdb_airingtoday`
- Genres: `tvGenres&url=tmdb_genre`
- Top Rated: `tmdbTvshows&url=tmdb_toprated`
- Next Episodes submenu: `calendar&url=progress`

### Other main-menu routes

- Search: Umbrella `tools_searchNavigator`, `movieNavigator`, and `tvNavigator` rows
- Categories: Umbrella root
- My List: Umbrella `mymovieNavigator`
- Live TV: The Crew `sports_channels`
- Sports: Mad Titan root

The Crew route was verified on-device and returned 15 entries. Mad Titan remains the
Sports provider, but its `/lntv/categories` route must not be restored unless an
upstream package supplies and successfully uses its required certificate/key pair.
Avoid background live widgets that block Home enumeration.

## Source files changed

Primary implementation:

- `kodi/skin.starlane.movies/addon.xml`
- `kodi/skin.starlane.movies/shortcuts/mainmenu.DATA.xml`
- `kodi/skin.starlane.movies/shortcuts/livetv.DATA.xml`
- `kodi/skin.starlane.movies/shortcuts/movies.DATA.xml`
- `kodi/skin.starlane.movies/shortcuts/tvshows.DATA.xml`
- `kodi/skin.starlane.movies/shortcuts/overrides.xml`
- `kodi/skin.starlane.movies/shortcuts/template.xml`
- `kodi/skin.starlane.movies/xml/IncludesDefaultSkinSettings.xml`
- `kodi/skin.starlane.movies/xml/IncludesAnimations.xml`
- `kodi/skin.starlane.movies/xml/IncludesHomeBingie.xml`
- `kodi/skin.starlane.movies/xml/IncludesHomeWidgets.xml`
- `tools/test_experimental_skin.py`
- `docs/CURRENT_STATUS.md`
- `docs/AGENT_HANDOFF.md`

The worktree was already dirty from the preceding private-skin fixes. Preserve all
listed changes together; do not reset or selectively restore them without reviewing
the complete diff.

## Validation completed

The full Python test suite passes:

```powershell
$env:PYTHONPATH=(Resolve-Path '.tools\python-packages').Path
& 'C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  -m unittest discover -s tools -p 'test_*.py'
```

Result: 37 tests passed.

Additional checks completed:

- All chosen route actions were matched against the locally staged Umbrella 6.7.81
  router and menu database.
- `git diff --check` passed.
- The ZIP contains Kodi-safe forward-slash paths and the correct top-level
  `skin.starlane.movies/addon.xml`.
- Kodi is running after deployment.
- `guisettings.xml` reports `lookandfeel.skin = skin.starlane.movies`.
- Installed `addon.xml` reports version 2.2.11.
- CocoScrapers' installed `addon.xml` exists.
- The Home widget viewport is bounded from y=571 to the bottom of the 1080p frame.
  Header height 40 plus poster-row height 331 produces a fixed 371-pixel stride.
  The outer grouplist is the only vertical mover and uses a 200-millisecond native
  scroll; Home no longer invokes the per-position fixed-focus animation factory.
- Adjacent rows in the selected category remain rendered at 35% opacity. Rows from
  other menu categories are excluded from Home's group even if the inherited
  `ShowAllWidgets` setting is enabled, preventing stale headers from consuming space.
- Home, New & Popular, TV Shows, and Movies use one Home widget renderer. Their menu
  entries load widgets on focus; Select and Right clear obsolete row state and focus
  the first populated poster row through the same action sequence. They do not flush
  widget properties or launch parallel hub windows.
- Home forces poster geometry even if a saved/generated shortcut tries to restore a
  different widget style. The packaged generated include is a neutral `<includes />`
  document and is rebuilt for the active profile after deployment.
- The detached fixed-focus frame is removed from Home; the selected card owns its
  border. Hardware evidence includes:
  `starlane-widget-2.2.11-direct-select2.png`,
  `starlane-widget-2.2.11-tv-isolated-loaded.png`,
  `starlane-widget-2.2.11-movies-isolated.png`,
  `starlane-widget-2.2.11-20-cycles-final.png`, and
  `starlane-widget-2.2.11-motion.mp4` under `build/skin-screenshots/`.
- The final generated include has 94 Umbrella, zero FenLight, ten Mad Titan, and zero
  `highlight` widget-style references. Kodi's final log has no private-skin XML,
  missing-control, exception, or fatal error.

## Critical skin-shortcuts behavior

Packaged shortcut defaults do not necessarily win. Kodi stores per-profile menu files
under:

`userdata/addon_data/script.skinshortcuts/`

Those saved files regenerated the old FenLight routes even after the new skin source
was copied. The following seven old files were moved to recoverable `.pre-umbrella`
backup names before the successful rebuild:

- `skin.starlane.movies-mainmenu.DATA.xml`
- `skin.starlane.movies-137.DATA.xml`
- `skin.starlane.movies-31534.DATA.xml`
- `skin.starlane.movies-10000.DATA.xml`
- `skin.starlane.movies-320032.DATA.xml`
- `skin.starlane.movies-movies.DATA.xml`
- `skin.starlane.movies-tvshows.DATA.xml`

Do not restore those backups unless deliberately rolling back to the FenLight menus.
Mad Titan-specific saved submenu files were left untouched.

The generated-cache hash is:

`userdata/addon_data/script.skinshortcuts/skin.starlane.movies.hash`

For future menu deployments:

1. Stop Kodi.
2. Back up affected saved `.DATA.xml` files.
3. Deploy the skin source.
4. Replace the generated include temporarily with a valid `<includes />` document.
5. Remove only the exact `skin.starlane.movies.hash` cache file.
6. Start Kodi and explicitly run skin-shortcuts `buildxml`.
7. Pull the generated include and verify expected provider counts.
8. Remove any temporary one-shot script.

A temporary `userdata/autoexec.py` was used to invoke:

```text
RunScript(script.skinshortcuts,type=buildxml&mainmenuID=900&group=mainmenu|powermenu)
```

It was removed after verification. Do not leave a rebuild `autoexec.py` installed.

## Deployment notes

ADB initially failed with Windows socket error `10013` because Proton VPN blocked LAN
traffic. The owner disabled Proton, after which ADB connected normally. If this recurs,
ask the owner to enable Proton's LAN-connections option or pause Proton temporarily.
Do not silently change VPN configuration.

ADB executable:

`build/android-sdk/platform-tools/adb.exe`

Basic connection:

```powershell
.\build\android-sdk\platform-tools\adb.exe connect 192.168.1.64:5555
.\build\android-sdk\platform-tools\adb.exe devices -l
```

Kodi data root:

`/sdcard/Android/data/org.xbmc.kodi/files/.kodi`

The active source was copied directly to:

`addons/skin.starlane.movies/`

No production manifest or public release was changed. The private skin remains outside
the signed production manifest.

## Known caveats and next actions

1. Confirm the eight Home rows populate after Trakt is authorized in Umbrella.
2. Exercise every Movie, TV, Search, New & Popular, Live TV, and Sports destination
   with the remote on the physical device.
3. Decide whether My List should remain `mymovieNavigator` or become a combined
   Movie/TV personal-list hub.
4. Decide whether explicit The Crew fallback submenus are still required.
5. Re-enable Proton VPN after device work if the owner has not already done so.
6. Review the full dirty diff, commit it, push it, and wait for CI only when the owner
   explicitly requests publication.

## Safety and rollback

- The exact pre-change 2.2.10 source, installed device skin, Skin Shortcuts profile,
  settings, generated include, and Kodi log are preserved under
  `build/device-backups/widget-remediation-2.2.10-pre-2.2.11/`.
- Private build 2.2.8 is the primary operational rollback. Its ZIP is
  `build/skin.starlane.movies-2.2.8.zip`, SHA-256
  `9AEB2A32A21ABAA2A54733EA34F3FB24B59A677DF79EA447BD2698D0CF92D348`.
  Stop Kodi, preserve the current private-skin/profile state, replace only
  `addons/skin.starlane.movies/` with the 2.2.8 package contents, then start Kodi and
  verify the version, active skin, generated menu counts, and navigation smoke test.
- Production skin `skin.starlanemeridian` 1.2.4 remains installed but is not the normal
  rollback for this private-skin stream.
- The previous Umbrella settings file and old FenLight menu files remain recoverable
  on-device.
- Do not delete account settings, Kodi databases, add-on data, or rollback skins.
- Do not expose tokens, passwords, pairing details, private keys, or keystores.
- Do not assume ignored `build/` artifacts are published or reproducible without their
  tracked source and validation evidence.

## Private skin 2.2.12 widget smoothing

Private build 2.2.12 was created from the dirty 2.2.11 source and installed on the
reference Fire TV. Production `skin.starlanemeridian` 1.2.4 was not modified. The
2.2.11 source, ZIP, SHA-256, installed device skin, Skin Shortcuts profile, settings,
generated include, and pre-change Kodi log are preserved under:

`build/device-backups/widget-smoothing-2.2.11-pre-2.2.12/`

The Home renderer now uses a Home-only `StarlaneHomeScrollTime` include on both axes:
150 milliseconds with `sine/out` easing. The inherited 600-millisecond `ScrollTime`
remains available to non-Home windows. Widget rows stay instantiated and transition
as one group between 35% and 100% opacity with a reversible 150-millisecond
`sine/out` fade. Home poster lists preload two items, matching Kodi's effective
preload limit, and item-specific poster, fallback, logo, and fanart textures retain
background loading.

Presentation no longer blocks navigation state. A focused poster records
`PendingWidgetID` and `PendingWidgetItem` immediately. A Home-only delayed control
waits 150 milliseconds, rechecks the current container, focused item, and both pending
values, and only then commits the movie, TV-show, or episode fields consumed by the
visible details controls. New input overwrites the pending values, so an older callback
cannot commit stale hero metadata. The prior hero remains present during the delay and
the committed hero texture crossfades over 100 milliseconds. Existing Bingie/PVR
property handling remains unchanged outside Home.

Static verification completed:

- all 38 repository tests passed;
- applicable Python compiled successfully;
- every XML file changed for 2.2.12 parsed successfully;
- `git diff --check` passed (with existing line-ending warnings only);
- package paths use forward slashes and the ZIP contains version 2.2.12;
- the final device-generated include contains 94 Umbrella, zero FenLight, ten Mad
  Titan, and zero `highlight` references;
- no provider route, Umbrella/CocoScrapers version, production manifest, or production
  skin was changed.

Artifact:

- ZIP: `build/skin.starlane.movies-2.2.12.zip`
- size: 28,208,235 bytes
- SHA-256:
  `898293BA079993CDC76335018CD7D1048FA69ADD1A9842645732116A301218A5`

The device passed repeated horizontal and vertical D-pad navigation, reversals,
category re-entry, and held-key input without a new Kodi skin, XML, missing-control,
animation, exception, or fatal error. Captures are under `build/skin-screenshots/`,
including `starlane-widget-2.2.12-motion.mp4` and
`starlane-widget-2.2.12-final.png`. The post-stress log is:

`build/device-backups/widget-smoothing-2.2.11-pre-2.2.12/device/kodi-2.2.12-post-stress.log`

The Fire TV `screenrecord` output is variable-frame-rate and encoded only 138 samples
over approximately 44.35 seconds. Android `dumpsys gfxinfo` observes Kodi's Java
shell rather than its native OpenGL renderer and reported only two frames. These tools
therefore do not prove the requested 60 fps, warm-frame, or 50-millisecond thresholds.
A true external 60 fps capture remains required for those quantitative acceptance
criteria. The capture and screenshots do verify stable end-state geometry and no
cumulative displacement. Current Umbrella directory failures in the log correspond to
the existing Trakt authentication error and are not skin-rendering errors.

Rollback order:

1. Stop Kodi and preserve the failed/current 2.2.12 skin, profile, log, and generated
   include.
2. Restore the exact saved `local/skin.starlane.movies/` tree and saved Skin Shortcuts
   profile from `widget-smoothing-2.2.11-pre-2.2.12`.
3. Start Kodi, confirm `skin.starlane.movies` 2.2.11 is active, rebuild the generated
   include only if its saved hash/include pair was not restored together, and smoke
   test Home, New & Popular, TV Shows, and Movies.
4. Use private build 2.2.8 only as the secondary fallback. Leave production 1.2.4
   installed and inactive unless the owner explicitly requests it.

No commit, push, public release, production deployment, VPN change, provider upgrade,
or production-manifest change was performed.

## Private skin 2.2.17 Mad Titan Live TV removal

Private build 2.2.17 removes only Mad Titan's failing Live NetTV row. The Crew
`?action=sports_channels` is now the sole Live TV widget, and Mad Titan's root remains
the sole Sports widget.

The diagnosis was reproduced from Kodi's live log and the cached official Mad Titan
2.0.32 ZIP:

- `/lntv/categories` configures
  `resources/com.playnet.androidtv.ads.crt` and `.key`;
- neither file exists in the installed add-on or official cached ZIP;
- `requests` raises an `OSError` before the directory loads;
- a reversible existence guard removed that exception but the upstream response then
  contained no configuration and failed with `TypeError: 'NoneType' object is not
  subscriptable`;
- the original Mad Titan module was restored byte-for-byte with SHA-256
  `76262AC91A37B5FDAA478158177DB081D51856F911B3FBECE1AE563C2A34F5D4`.

The exact pre-change skin, Skin Shortcuts profile, settings, and Kodi log are under:

`build/device-backups/madtitan-livetv-2.2.16-pre-2.2.17/`

After deploying and rebuilding Skin Shortcuts, the generated include contains 101
Umbrella, three Mad Titan, three The Crew, zero FenLight, and zero broken Live NetTV
references. A direct Kodi directory request to The Crew returned 15 entries. A clean
Kodi restart retained `skin.starlane.movies` 2.2.17 and the fresh log contains no
Mad Titan, Live NetTV, Python callback, invalid-include, or generated-control error.

Artifact:

- ZIP: `build/skin.starlane.movies-2.2.17.zip`
- size: 28,254,460 bytes
- SHA-256:
  `9C2D7F04F844AEA245618DC3242CB7C16F5CE6DD72F59C656EB34B3D705F3960`

Rollback:

1. Stop Kodi.
2. Restore the saved `skin.starlane.movies` tree and Skin Shortcuts profile from
   `madtitan-livetv-2.2.16-pre-2.2.17`.
3. Start Kodi and verify 2.2.16 plus the restored generated include/hash pair.
4. The Mad Titan Live TV error will return after rollback; use it only for comparison
   or while testing a verified upstream repair.

No provider was upgraded or modified, and no production skin, signed manifest, public
release, VPN setting, or service was changed.

## Private skin 2.2.15 first-row rendering correction

Private build 2.2.15 fixes the remaining Home first-row failure without changing
providers, widget routes, geometry, animation timing, or progress data. Kodi was
receiving a literal nested `$PARAM[widgetid]` in the deferred-details guard and logged
`Misplaced [` plus boolean-expression parse errors when the first row focused.

The complete guard is now passed from `StarlaneHomeDeferredDetailsButton`, where the
outer numeric widget ID is available, into `StarlaneHomeWidgetProperties`. The nested
include's fallback guard is simply `false`, so an omitted caller cannot produce an
unresolved expression.

Verification:

- all 38 repository tests and nine focused skin tests passed;
- the 560-entry ZIP contains 2.2.15 and passed path/version checks;
- a reversible local-progress fixture rendered Continue Watching Movies as the first
  row with its header, poster, focus border, hero, metadata, and adjacent TV preview;
- the reproduction log contains no unresolved `$PARAM[widgetid]`, `Misplaced [`,
  boolean-expression, skin XML, missing-control, exception, or fatal error;
- the original Umbrella `watched.db` was restored byte-for-byte after testing.

Artifact:

- ZIP: `build/skin.starlane.movies-2.2.15.zip`
- size: 28,208,656 bytes
- SHA-256:
  `24F462E97A69F2B55F5C54E457447F7A77957B5D6B07C653388AFC0827D4329D`

Evidence and rollback:

- screenshot: `build/skin-screenshots/starlane-widget-2.2.15-first-row.png`
- final log:
  `build/device-backups/first-row-render-2.2.14-pre-2.2.15/device/kodi-2.2.15-final.log`
- exact 2.2.14 source, ZIP, device skin/profile, progress database, and pre-change log:
  `build/device-backups/first-row-render-2.2.14-pre-2.2.15/`

No commit, push, public release, production deployment, provider upgrade, VPN change,
or production-skin change was performed.

## Private skin 2.2.14 local Continue Watching

Private build 2.2.14 was created from the dirty 2.2.13 source and installed on the
reference Fire TV. The exact 2.2.13 source and ZIP, installed skin, Skin Shortcuts
profile, generated include, Umbrella settings, Umbrella `watched.db`, and Kodi log are
preserved under:

`build/device-backups/local-continue-watching-2.2.13-pre-2.2.14/`

The first two Home rows no longer depend on Trakt history:

- Continue Watching Movies:
  `plugin://plugin.video.umbrella/?action=local_finish_watching_movies`
- Continue Watching TV Shows:
  `plugin://plugin.video.umbrella/?action=local_finish_watching_episodes`

Both routes are implemented by the installed Umbrella 6.7.81 add-on. Resume progress
is stored in Umbrella's on-device databases, sorted by last play time, and removed
after the configured watched threshold. Playback and metadata resolution still use
Umbrella. The current device configuration remains local indicators/scrobbling,
bookmarks enabled, an 85% watched threshold, user-confirmed Resume/Start Over, and
remote mark-watched toggles disabled.

The single Home renderer, row IDs 2510/2520, poster geometry, progress presentation,
150-millisecond scrolling, two-item preload, and delayed details/hero lifecycle are
unchanged. The remaining Home, Live TV, Sports, and Categories routes are unchanged.
The generated include contains 101 Umbrella, six Mad Titan, three The Crew, zero
FenLight, zero `highlight`, zero `trakthistory`, and three generated references to
each local Continue Watching action.

Verification completed:

- all 38 repository tests and all nine focused private-skin tests passed;
- applicable Python compiled and `git diff --check` passed with inherited line-ending
  warnings only;
- the ZIP contains 560 forward-slash entries and the correct 2.2.14 metadata;
- a reversible synthetic progress fixture rendered both movie and episode rows on the
  Fire TV with aligned artwork, details, focus, and adjacent-row preview;
- the exact original empty `watched.db` was restored afterward and matched its saved
  SHA-256 byte-for-byte;
- Umbrella settings also matched their pre-test SHA-256 byte-for-byte;
- the final device log contains no new skin XML, boolean-expression, missing-control,
  exception, or fatal error.

Evidence:

- `build/skin-screenshots/starlane-widget-2.2.14-continue-movies.png`
- `build/skin-screenshots/starlane-widget-2.2.14-continue-tv.png`
- `build/device-backups/local-continue-watching-2.2.13-pre-2.2.14/device/kodi-2.2.14-final.log`

Artifact:

- ZIP: `build/skin.starlane.movies-2.2.14.zip`
- size: 28,208,565 bytes
- SHA-256:
  `F355748846F1D5058411F46292702BA51FDC8EB34C746F7CF9A6D74E37E638B9`

Because the preserved device progress database was empty, the normal post-test Home
state correctly has no Continue Watching cards. A movie or episode appears after
Umbrella playback passes three minutes and stops below the configured 85% watched
threshold. The unrelated stored Trakt credential may continue to produce a background
token-refresh HTTP 400, but neither Continue Watching widget invokes a Trakt directory.

Rollback:

1. Stop Kodi and preserve the current 2.2.14 skin/profile/log state.
2. Restore the complete saved 2.2.13 skin and Skin Shortcuts profile from
   `local-continue-watching-2.2.13-pre-2.2.14`.
3. Restore Umbrella settings and `watched.db` only if they changed independently; the
   2.2.14 test left both byte-identical to their backups.
4. Start Kodi, verify 2.2.13 is active, and smoke-test Home. Keep 2.2.8 as the
   secondary fallback and production 1.2.4 installed and inactive.

No commit, push, public release, production deployment, VPN change, provider upgrade,
or production-manifest change was performed.

## Private skin 2.2.13 populated Home, Live TV, Sports, and Categories

Private build 2.2.13 was created from the dirty 2.2.12 source and installed on the
reference Fire TV. Production `skin.starlanemeridian` 1.2.4 and all provider add-ons,
versions, credentials, and settings were left unchanged. The exact pre-change 2.2.12
source, ZIP, installed skin, Skin Shortcuts profile, settings, generated include, and
Kodi log are preserved under:

`build/device-backups/widget-population-2.2.12-pre-2.2.13/`

All seven content destinations now use the single Home renderer. Live TV, Sports, and
Categories no longer activate a second hub/window renderer. Their deterministic first
widget IDs are 6510/6520 for Live TV, 7510 for Sports, and 8510-8540 for Categories.
The populated rows and tested plug-in routes are:

- Home: Umbrella Recently Watched Movies (`movies/trakthistory`), Recently Watched TV
  Shows (`calendar/trakthistory`), TMDb top-rated Movies and TV Shows, Movie Genres,
  TV Genres, Networks, and Providers.
- Live TV: Mad Titan `/lntv/categories` and The Crew `sports_channels`.
- Sports: the supported Mad Titan Sports root directory.
- Categories: Umbrella Movie Genres, TV Genres, Networks, and Providers.

The generated Skin Shortcuts include contains 101 Umbrella, six Mad Titan, three The
Crew, zero FenLight, and zero `highlight` references. No FenLight route was introduced,
and no existing Umbrella/CocoScrapers or Mad Titan route was replaced outside the
requested sections. Empty generated slots remain non-rendering because the row
visibility is bounded by the corresponding container's item count.

The change also corrected a latent deferred-details include bug inherited from 2.2.12:
the nested `guard` parameter now uses a default instead of an explicit value. Kodi no
longer reports the associated `Misplaced +`/boolean-expression parse errors when a
folder-style widget receives focus.

Static verification completed:

- all 38 repository tests passed;
- applicable Python compiled successfully;
- the changed private-skin XML parsed, apart from the separately documented inherited
  malformed entity elsewhere in `IncludesVariables.xml`;
- `git diff --check` passed with existing line-ending warnings only;
- the package contains the correct top-level 2.2.13 add-on and forward-slash paths.

Artifact:

- ZIP: `build/skin.starlane.movies-2.2.13.zip`
- size: 28,208,552 bytes
- SHA-256:
  `D1DC89E22C0BED9B745A67F6D4CFA3D6D6B55197008B3F512BE8521D777EA507`

Hardware evidence is under `build/skin-screenshots/`. Categories populated with
aligned Movie Genres and TV Genres rows, and the Mad Titan Sports root populated
without clipping. The skin kept adjacent loading/empty rows instantiated and bounded.
Two external account/add-on faults remain distinct from the skin:

- Umbrella's existing Trakt refresh returns HTTP 400, so Recently Watched rows require
  Trakt reauthorization before they can populate.
- Mad Titan Live TV reaches its supported `/lntv/categories` route, but the installed
  Mad Titan 2.0.32 add-on raises an `OSError` because its configured
  `resources/com.playnet.androidtv.ads.crt` file is absent. The provider was not
  modified or upgraded as part of this skin change.

The relevant final device logs are stored beside the rollback backup, including
`kodi-2.2.13-final.log`. Provider failures do not introduce a skin XML, animation,
missing-control, or deferred-details expression error.

Rollback order:

1. Stop Kodi and preserve the current 2.2.13 skin, profile, generated include, and log.
2. Restore the exact 2.2.12 skin and Skin Shortcuts profile from
   `widget-population-2.2.12-pre-2.2.13`.
3. Start Kodi, verify `skin.starlane.movies` 2.2.12 is active, and smoke-test Home,
   New & Popular, TV Shows, and Movies.
4. Use private build 2.2.8 only as the secondary fallback. Leave production 1.2.4
   installed and inactive unless explicitly requested.

No commit, push, public release, production deployment, VPN change, provider upgrade,
or production-manifest change was performed.

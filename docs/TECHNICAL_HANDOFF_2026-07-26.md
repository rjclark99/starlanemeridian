# Starlane Movies technical handoff

Last verified: 28 July 2026, after physical deployment to the reference Fire TV.

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
- Source and installed version: `2.2.16`
- Active Kodi skin: `skin.starlane.movies`
- Reference device: Amazon Fire TV `AFTKAUK001`
- Kodi package/version: `org.xbmc.kodi`, Kodi 21.3
- ADB endpoint: `192.168.1.64:5555`
- Production rollback skin: `skin.starlanemeridian` 1.2.4 remains installed
- Private operational rollback artifact: `skin.starlane.movies` 2.2.8
- Installable private-skin artifact:
  `build/skin.starlane.movies-2.2.16.zip`
- Artifact SHA-256:
  `9FC59B0ED2486E33872EDA689EAF2A0C1351B742DDA08F9C2A4E7AA99D91A62A`

Version 2.2.16 adds `service.py`, a read-only local gate for Umbrella's
`watched.db`. Generated controls 2510 and 2520 are omitted before their plugin
directories load when no matching `movie` or `episode` progress record exists.
Device tests confirmed that the empty state renders All-Time Best Movies correctly,
while a reversible populated fixture restores both Continue Watching rows. The
original database was restored with matching SHA-256
`DE1409A86B479BEC49E0C7E30A0084C204FFDA71757537593DD4AE403B378B7D`.

The deployed, generated skin-shortcuts include was physically checked:

- 101 references to `plugin.video.umbrella`
- 0 references to `plugin.video.fenlight`
- 6 references to `plugin.video.madtitansports`
- 3 references to `plugin.video.thecrew`

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

- Search: Umbrella `tools_searchNavigator`
- Categories: Umbrella root
- My List: Umbrella `mymovieNavigator`
- Live TV: Mad Titan `/lntv/categories`
- Sports: Mad Titan root

The Crew is installed but the currently generated menu contains no direct The Crew
route. The live/sports source presently points to Mad Titan and deliberately avoids
background live widgets because those add-ons can block home enumeration. If the owner
expects explicit Crew fallback entries, treat that as separate follow-up work and
validate the exact Crew routes on-device before adding them.

## Source files changed

Primary implementation:

- `kodi/skin.starlane.movies/addon.xml`
- `kodi/skin.starlane.movies/shortcuts/mainmenu.DATA.xml`
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

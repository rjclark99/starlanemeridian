import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIN = ROOT / "kodi" / "skin.starlane.movies"


class ExperimentalSkinTests(unittest.TestCase):
    def test_metadata_and_attribution(self):
        addon = ET.parse(SKIN / "addon.xml").getroot()
        self.assertEqual(addon.attrib["id"], "skin.starlane.movies")
        self.assertEqual(addon.attrib["version"], "2.2.22")
        service = addon.find("extension[@point='xbmc.service']")
        self.assertIsNotNone(service)
        self.assertEqual(service.attrib["library"], "service.py")
        self.assertEqual(addon.attrib["name"], "Starlane Movies")
        metadata = addon.find("extension[@point='xbmc.addon.metadata']")
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.findtext("license"), "GPL v2.0")
        self.assertEqual(
            metadata.findtext("source"),
            "https://github.com/rjclark99/starlanemeridian",
        )
        self.assertTrue((SKIN / "LICENSE").is_file())
        upstream_readme = (SKIN / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            "https://github.com/AchillesPunks/skin.titan.bingie.mod/",
            upstream_readme,
        )
        progress_gate = (SKIN / "service.py").read_text(encoding="utf-8")
        self.assertIn("SELECT 1 FROM progress WHERE media_type = ? LIMIT 1", progress_gate)
        self.assertIn('"movie", "episode"', progress_gate)
        template = (SKIN / "shortcuts" / "template.xml").read_text(
            encoding="utf-8"
        )
        self.assertIn("StarlaneHasContinueMovies", template)
        self.assertIn("StarlaneHasContinueEpisodes", template)

    def test_brand_assets_and_startup_are_present(self):
        for relative_path in (
            "extras/starlane-movies/emblem.png",
            "extras/starlane-movies/horizon.png",
            "xml/Startup.xml",
        ):
            self.assertTrue((SKIN / relative_path).is_file(), relative_path)

        defaults = (
            SKIN / "xml" / "IncludesDefaultSkinSettings.xml"
        ).read_text(encoding="utf-8")
        self.assertIn("Skin.SetBool(DisableSpotlightContent)", defaults)
        self.assertIn("Skin.Reset(EnableFixedFrameWidgets)", defaults)
        self.assertNotIn("Skin.SetBool(EnableFixedFrameWidgets)", defaults)
        self.assertIn(
            "String.IsEmpty(Skin.String(HomeLayout))"
            '">Skin.SetString(HomeLayout,bingie)',
            defaults,
        )
        self.assertIn("Skin.SetString(widgetstyle,poster)", defaults)

        home_widgets = (
            SKIN / "xml" / "IncludesHomeWidgets.xml"
        ).read_text(encoding="utf-8")
        widget_base = home_widgets[
            home_widgets.index('<include name="widget_base_normal">'):
            home_widgets.index('<include name="widget_base_vertical">')
        ]
        self.assertNotIn(
            "Control.IsVisible($PARAM[widgetid])",
            widget_base,
        )

    def test_home_widgets_keep_adjacent_rows_rendered_and_focus_the_card(self):
        home_bingie = ET.parse(
            SKIN / "xml" / "IncludesHomeBingie.xml"
        ).getroot()
        widget_group = home_bingie.find(
            ".//control[@type='grouplist'][@id='77777']"
        )
        self.assertIsNotNone(widget_group)
        self.assertEqual(widget_group.findtext("top"), "571")
        self.assertEqual(widget_group.findtext("bottom"), "0")
        self.assertEqual(widget_group.findtext("orientation"), "vertical")
        self.assertEqual(widget_group.findtext("itemgap"), "0")
        self.assertEqual(
            [
                (include.text or "").strip()
                for include in widget_group.findall("include")
                if (include.text or "").strip() == "StarlaneHomeScrollTime"
            ],
            ["StarlaneHomeScrollTime"],
        )
        self.assertFalse(
            any(
                (include.text or "").strip()
                in {"Fixed_Focus_Bottom", "Fixed_Focus_Itemgap"}
                for include in widget_group.findall("include")
            )
        )

        # Header 40 + poster container 331 gives one deterministic 371px row.
        home_widgets_root = ET.parse(
            SKIN / "xml" / "IncludesHomeWidgets.xml"
        ).getroot()
        header = home_widgets_root.find(
            ".//include[@name='widget_header_multi']/control"
        )
        poster = home_widgets_root.find(
            ".//include[@name='widget_layout_poster']"
        )
        self.assertEqual(
            int(header.findtext("height")) + int(poster.findtext("height")),
            371,
        )
        home_widgets_text = ET.tostring(
            home_widgets_root, encoding="unicode"
        )
        self.assertNotIn(
            'content="Fixed_Focus_Navigation_Factory"',
            home_widgets_text,
        )
        self.assertEqual(
            home_widgets_text.count(
                "String.IsEqual(Container(900).ListItem.Property"
                "(submenuVisibility),$PARAM[submenuid]) | "
                "[!Window.IsActive(Home) + Skin.HasSetting(ShowAllWidgets)]"
            ),
            2,
        )
        self.assertNotIn(
            "Property(submenuVisibility),$PARAM[submenuid]) | "
            "Skin.HasSetting(ShowAllWidgets)",
            home_widgets_text,
        )

        animations = (
            SKIN / "xml" / "IncludesAnimations.xml"
        ).read_text(encoding="utf-8")
        unfocused_fade = animations[
            animations.index('<include name="BingieUnfocusedWidgetFade">'):
            animations.index(
                '<include name="BingieNoCircularWidgetHeaderAnim">'
            )
        ]
        self.assertIn(
            'effect="fade" start="100" end="35" time="150" '
            'tween="sine" easing="out" reversible="true"',
            unfocused_fade,
        )
        self.assertIn(
            "Window(Home).Property(CurrentWidgetID),$PARAM[widgetid]",
            unfocused_fade,
        )
        self.assertNotIn('effect="fade" start="100" end="0"', unfocused_fade)
        self.assertNotIn("!Control.HasFocus($PARAM[widgetid])", unfocused_fade)

        home_bingie_text = ET.tostring(home_bingie, encoding="unicode")
        self.assertNotIn("Bingie_Screens_Fixed_Focus_Frame", home_bingie_text)

    def test_home_scroll_preload_and_details_settle_are_bounded(self):
        includes = ET.parse(SKIN / "xml" / "Includes.xml").getroot()
        global_scroll = includes.find(".//include[@name='ScrollTime']/scrolltime")
        home_scroll = includes.find(
            ".//include[@name='StarlaneHomeScrollTime']/scrolltime"
        )
        home_preload = includes.find(
            ".//include[@name='StarlaneHomeWidgetPreload']/preloaditems"
        )
        self.assertEqual(global_scroll.text, "600")
        self.assertEqual(
            global_scroll.attrib, {"tween": "cubic", "easing": "out"}
        )
        self.assertEqual(home_scroll.text, "150")
        self.assertEqual(
            home_scroll.attrib, {"tween": "sine", "easing": "out"}
        )
        self.assertEqual(home_preload.text, "2")

        home_widgets = (
            SKIN / "xml" / "IncludesHomeWidgets.xml"
        ).read_text(encoding="utf-8")
        widget_base = home_widgets[
            home_widgets.index('<include name="widget_base_normal">'):
            home_widgets.index('<include name="widget_base_vertical">')
        ]
        self.assertIn(
            '<include condition="Window.IsActive(Home)">'
            "StarlaneHomeScrollTime</include>",
            widget_base,
        )
        self.assertIn(
            '<include condition="!Window.IsActive(Home)">ScrollTime</include>',
            widget_base,
        )
        self.assertIn(
            '<include condition="Window.IsActive(Home)">'
            "StarlaneHomeWidgetPreload</include>",
            widget_base,
        )
        self.assertNotIn("<preloaditems>5</preloaditems>", widget_base)
        self.assertEqual(
            home_widgets.count(
                'content="StarlaneHomeDeferredDetailsButton" '
                'condition="Window.IsActive(Home)"'
            ),
            2,
        )

        functions = (
            SKIN / "xml" / "IncludesFunctions.xml"
        ).read_text(encoding="utf-8")
        delayed = functions[
            functions.index(
                '<include name="StarlaneHomeDeferredDetailsButton">'
            ):
            functions.index('<include name="StarlaneHomePendingDetails">')
        ]
        self.assertIn(
            'effect="fade" start="100" end="100" time="150" '
            'tween="sine" easing="out" reversible="true">Focus',
            delayed,
        )
        self.assertIn("PendingWidgetID", functions)
        self.assertIn("PendingWidgetItem", functions)
        self.assertIn("CommittedWidgetID", functions)
        self.assertIn("CommittedWidgetItem", functions)
        self.assertIn(
            "Control.HasFocus($PARAM[widgetid]) + "
            "String.IsEqual(Window(Home).Property(PendingWidgetID),"
            "$PARAM[widgetid])",
            functions,
        )
        self.assertIn('<param name="guard" default="false"', functions)
        self.assertIn(
            '<param name="guard" value="Window.IsActive(Home) + '
            'Control.HasFocus($PARAM[widgetid])',
            functions,
        )
        self.assertIn(
            '<include content="WidgetProperties" '
            'condition="!Window.IsActive(Home)">',
            functions,
        )
        for legacy_field in (
            "ListItem.Artist",
            "ListItem.Album",
            "ListItem.StartTime",
            "ListItem.ChannelName",
            "ListItem.ChannelNumberLabel",
            "ListItem.StartDate",
            "ListItem.ChannelLogo",
        ):
            home_properties = functions[
                functions.index(
                    '<include name="StarlaneHomeWidgetProperties">'
                ):
                functions.index('<include name="HighlightHiddenWidgetButton">')
            ]
            self.assertNotIn(legacy_field, home_properties)

        home_bingie = (
            SKIN / "xml" / "IncludesHomeBingie.xml"
        ).read_text(encoding="utf-8")
        self.assertGreaterEqual(home_bingie.count("<fadetime>100</fadetime>"), 2)

    def test_home_uses_one_poster_widget_geometry(self):
        template = ET.parse(
            SKIN / "shortcuts" / "template.xml"
        ).getroot()
        style_defaults = [
            (property_node.text or "").strip()
            for property_node in template.findall(".//property")
            if property_node.attrib.get("name", "").startswith("widgetStyle")
            and "tag" not in property_node.attrib
        ]
        self.assertEqual(style_defaults, ["poster"] * 8)

        functions = (
            SKIN / "xml" / "IncludesFunctions.xml"
        ).read_text(encoding="utf-8")
        self.assertIn(
            '<onfocus condition="Window.IsActive(Home)">'
            "SetProperty(widgetstyle,poster,Home)</onfocus>",
            functions,
        )

        generated = ET.parse(
            SKIN / "xml" / "script-skinshortcuts-includes.xml"
        ).getroot()
        self.assertEqual(generated.tag, "includes")
        self.assertEqual(len(generated), 0)

    def test_widget_backed_main_menu_items_use_the_home_renderer(self):
        shortcuts = ET.parse(
            SKIN / "shortcuts" / "mainmenu.DATA.xml"
        ).getroot()
        widget_backed_ids = {
            "10000",
            "320032",
            "20343",
            "342",
            "31025",
        }
        actions = {
            shortcut.findtext("defaultID"): shortcut.findtext("action")
            for shortcut in shortcuts.findall("shortcut")
        }
        for default_id in widget_backed_ids:
            self.assertEqual(actions[default_id], "noop")

        duplicate_hubs = {
            "ActivateWindow(home,return)",
            "ActivateWindow(1110,return)",
            "ActivateWindow(1111,return)",
            "ActivateWindow(1112,return)",
        }
        self.assertTrue(duplicate_hubs.isdisjoint(actions.values()))

        overrides = ET.parse(
            SKIN / "shortcuts" / "overrides.xml"
        ).getroot()
        main_menu_overrides = overrides.findall(
            "override[@action='globaloverride'][@group='mainmenu']"
        )
        noop_override = next(
            (
                override
                for override in main_menu_overrides
                if override.findtext("condition")
                == "String.IsEqual(ListItem.Property(path),noop)"
            ),
            None,
        )
        self.assertIsNotNone(noop_override)
        self.assertEqual(
            [action.text for action in noop_override.findall("action")],
            [
                "::ACTION::",
                "ClearProperty(ShowViewSubMenu,Home)",
                "ClearProperty(CurrentWidgetID,Home)",
                "ClearProperty(CurrentWidgetPos,Home)",
                "ClearProperty(PrevWidgetPos,Home)",
                "ClearProperty(LastFocusWidgetPos,Home)",
                "ClearProperty(PendingWidgetID,Home)",
                "ClearProperty(PendingWidgetItem,Home)",
                "SetFocus($VAR[StarlaneFirstWidgetFocus],0,absolute)",
            ],
        )

        home_menu = (
            SKIN / "xml" / "IncludesBingie.xml"
        ).read_text(encoding="utf-8")
        for action in (
            "ClearProperty(CurrentWidgetID,Home)",
            "ClearProperty(CurrentWidgetPos,Home)",
            "ClearProperty(PrevWidgetPos,Home)",
            "ClearProperty(LastFocusWidgetPos,Home)",
            "ClearProperty(PendingWidgetID,Home)",
            "ClearProperty(PendingWidgetItem,Home)",
            "SetFocus($VAR[StarlaneFirstWidgetFocus],0,absolute)",
        ):
            self.assertIn(f"<onright condition=", home_menu)
            self.assertIn(f">{action}</onright>", home_menu)

        variables = (
            SKIN / "xml" / "IncludesVariables.xml"
        ).read_text(encoding="utf-8")
        for submenu, first_id, last_id in (
            ("num-10000", 2510, 2580),
            ("num-320032", 3510, 3550),
            ("tvshows", 4510, 4570),
            ("movies", 5510, 5570),
        ):
            for widget_id in range(first_id, last_id + 1, 10):
                self.assertIn(
                    f"Property(submenuVisibility),{submenu}) + "
                    f"Integer.IsGreater(Container({widget_id}).NumItems,0)"
                    f'">{widget_id}</value>',
                    variables,
                )
        for default_id, widget_ids in (
            ("31025", (8510, 8520, 8530, 8540)),
        ):
            for widget_id in widget_ids:
                self.assertIn(
                    f"Property(defaultID),{default_id}) + "
                    f"Integer.IsGreater(Container({widget_id}).NumItems,0)"
                    f'">{widget_id}</value>',
                    variables,
                )

    def test_home_and_pvr_hubs_have_persistent_menu_fallback(self):
        home = ET.parse(SKIN / "xml/Home.xml").getroot()
        home_default = home.find("defaultcontrol")
        self.assertIsNotNone(home_default)
        self.assertEqual(home_default.text, "1000")
        self.assertEqual(home_default.attrib.get("always"), "true")
        bootstrap_focus = home.find(".//control[@type='button'][@id='1000']")
        self.assertIsNotNone(bootstrap_focus)
        self.assertTrue(
            any("SetFocus($VAR[DefaultMenuFocus])" in (item.text or "")
                for item in bootstrap_focus.findall("onfocus"))
        )

        pvr = ET.parse(SKIN / "xml/Custom_1116_PVR_Hub.xml").getroot()
        pvr_default = pvr.find("defaultcontrol")
        self.assertIsNotNone(pvr_default)
        self.assertEqual(pvr_default.text, "900")
        self.assertEqual(pvr_default.attrib.get("always"), "true")

    def test_user_visible_language_has_no_upstream_branding(self):
        upstream_branding = re.compile(r"\b(?:Titan|Bingie)\b", re.IGNORECASE)
        for language_file in (SKIN / "language").rglob("strings.po"):
            text = language_file.read_text(encoding="utf-8-sig")
            remaining = [
                line for line in text.splitlines()
                if upstream_branding.search(line)
                and not line.startswith("#")
                and not line.startswith('"Language-Team:')
            ]
            self.assertEqual(remaining, [], language_file)

    def test_vod_menu_routes_use_umbrella_only(self):
        main_menu = ET.parse(SKIN / "shortcuts/mainmenu.DATA.xml").getroot()
        shortcuts = {
            item.findtext("defaultID"): item
            for item in main_menu.findall("shortcut")
        }
        self.assertIn("342", shortcuts)
        self.assertIn("20343", shortcuts)
        self.assertIn("10000", shortcuts)
        self.assertIn("320032", shortcuts)
        self.assertNotIn("starlane_livetv", shortcuts)
        self.assertNotIn("starlane_sports", shortcuts)
        self.assertEqual(shortcuts["137"].findtext("action"), "noop")
        self.assertEqual(shortcuts["31025"].findtext("action"), "noop")
        self.assertIn(
            "plugin.video.umbrella/?action=mymovieNavigator",
            shortcuts["31534"].findtext("action"),
        )

        overrides = ET.parse(SKIN / "shortcuts/overrides.xml").getroot()
        properties = overrides.findall("propertydefault")

        def widget_paths(default_id):
            return {
                item.text or ""
                for item in properties
                if item.attrib.get("defaultID") == default_id
                and item.attrib.get("property", "").startswith("widgetPath")
            }

        movie_paths = widget_paths("342")
        tv_paths = widget_paths("20343")
        home_paths = widget_paths("10000")
        new_paths = widget_paths("320032")
        category_paths = widget_paths("31025")
        search_paths = widget_paths("137")
        self.assertTrue(home_paths)
        self.assertTrue(new_paths)
        self.assertTrue(movie_paths)
        self.assertTrue(tv_paths)
        self.assertEqual(
            search_paths,
            {
                "plugin://plugin.video.umbrella/?action=tools_searchNavigator",
                "plugin://plugin.video.umbrella/?action=movieNavigator",
                "plugin://plugin.video.umbrella/?action=tvNavigator",
            },
        )
        self.assertTrue(all("plugin.video.umbrella" in path for path in home_paths))
        self.assertTrue(all("plugin.video.umbrella" in path for path in new_paths))
        self.assertTrue(all("plugin.video.umbrella" in path for path in movie_paths))
        self.assertTrue(all("plugin.video.umbrella" in path for path in tv_paths))
        self.assertEqual(
            home_paths,
            {
                "plugin://plugin.video.umbrella/?action=local_finish_watching_movies",
                "plugin://plugin.video.umbrella/?action=local_finish_watching_episodes",
                "plugin://plugin.video.umbrella/?action=tmdbmovies&url=tmdb_toprated",
                "plugin://plugin.video.umbrella/?action=tmdbTvshows&url=tmdb_toprated",
                "plugin://plugin.video.umbrella/?action=movieGenres&url=tmdb_genre",
                "plugin://plugin.video.umbrella/?action=tvGenres&url=tmdb_genre",
                "plugin://plugin.video.umbrella/?action=tvNetworks",
                "plugin://plugin.video.umbrella/?action=tvOriginals",
            },
        )
        home_defaults = {
            item.attrib.get("property"): item.text or ""
            for item in properties
            if item.attrib.get("defaultID") == "10000"
        }
        self.assertEqual(
            home_defaults["widget"],
            "umbrella_home_continue_movies",
        )
        self.assertEqual(
            home_defaults["widgetName"],
            "Continue Watching Movies",
        )
        self.assertEqual(
            home_defaults["widget.1"],
            "umbrella_home_continue_tv",
        )
        self.assertEqual(
            home_defaults["widgetName.1"],
            "Continue Watching TV Shows",
        )
        self.assertFalse(any("trakthistory" in path for path in home_paths))
        visible_provider_labels = {
            item.text or ""
            for item in properties
            if item.attrib.get("property", "").startswith("widgetName")
        }
        self.assertFalse(
            any(
                re.search(r"\bUmbrella\b", label, re.IGNORECASE)
                for label in visible_provider_labels
            )
        )
        self.assertEqual(
            category_paths,
            {
                "plugin://plugin.video.umbrella/?action=movieGenres&url=tmdb_genre",
                "plugin://plugin.video.umbrella/?action=tvGenres&url=tmdb_genre",
                "plugin://plugin.video.umbrella/?action=tvNetworks",
                "plugin://plugin.video.umbrella/?action=tvOriginals",
            },
        )
        self.assertFalse(any("trakt_" in path for path in home_paths | new_paths))

        for submenu_file in ("movies.DATA.xml", "tvshows.DATA.xml"):
            submenu = (
                SKIN / "shortcuts" / submenu_file
            ).read_text(encoding="utf-8")
            self.assertNotIn("trakt_", submenu)
            self.assertNotIn("plugin.video.fenlight", submenu)
            self.assertIn("plugin.video.umbrella", submenu)

        shortcut_sources = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (SKIN / "shortcuts").glob("*.xml")
        )
        self.assertNotIn("plugin.video.fenlight", shortcut_sources)
        self.assertNotIn("plugin.video.madtitansports", shortcut_sources)
        self.assertNotIn("plugin.video.thecrew", shortcut_sources)
        self.assertNotIn("starlane_livetv", shortcut_sources)
        self.assertNotIn("starlane_sports", shortcut_sources)

        widget_path_nodes = [
            item.text
            for item in overrides.findall("propertydefault")
            if item.attrib.get("property", "").startswith("widgetPath")
            and item.text
        ]
        widget_paths = set(widget_path_nodes)
        managed_paths = {
            path
            for path in widget_paths
            if path.startswith("plugin://plugin.video.umbrella/")
            and "action=local_finish_watching_" not in path
        }
        complete_local_paths = {
            path
            for path in widget_paths
            if "action=local_finish_watching_" in path
        }
        self.assertEqual(len(widget_path_nodes), 34)
        self.assertEqual(len(widget_paths), 21)
        self.assertEqual(
            sum(
                path.startswith("plugin://plugin.video.umbrella/")
                and "action=local_finish_watching_" not in path
                for path in widget_path_nodes
            ),
            32,
        )
        self.assertEqual(len(managed_paths), 19)
        self.assertEqual(len(complete_local_paths), 2)
        for representative in (
            "plugin://plugin.video.umbrella/?action=tmdbmovies&url=tmdb_toprated",
            "plugin://plugin.video.umbrella/?action=tmdbTvshows&url=tmdb_toprated",
            "plugin://plugin.video.umbrella/?action=movieGenres&url=tmdb_genre",
            "plugin://plugin.video.umbrella/?action=tvNetworks",
            "plugin://plugin.video.umbrella/?action=tvOriginals",
        ):
            self.assertIn(representative, managed_paths)

        widgets = (SKIN / "xml/IncludesHomeWidgets.xml").read_text(encoding="utf-8")
        managed_condition = (
            "String.StartsWith($PARAM[widgetPath],"
            "plugin://plugin.video.umbrella/) + "
            "!String.Contains($PARAM[widgetPath],action=local_finish_watching_)"
        )
        self.assertIn('<label>Show more</label>', widgets)
        self.assertIn('<property name="path">$PARAM[widgetPath]</property>', widgets)
        self.assertIn(
            '<property name="starlane.terminal">show_more</property>', widgets
        )
        self.assertIn(
            '<property name="SpecialSort">bottom</property>', widgets
        )
        self.assertIn(
            '<onclick>ActivateWindow(Videos,$PARAM[widgetPath],return)</onclick>',
            widgets,
        )
        self.assertNotIn('limit="19"', widgets)
        self.assertGreaterEqual(widgets.count('limit="$PARAM[widgetLimit]"'), 3)
        self.assertEqual(widgets.count('<item id="900001">'), 1)
        self.assertIn(
            'condition="String.Contains($PARAM[widgetPath],action=local_finish_watching_)"',
            widgets,
        )
        self.assertIn(
            f'condition="{managed_condition}"',
            widgets,
        )
        self.assertIn(
            'condition="!String.StartsWith($PARAM[widgetPath],'
            'plugin://plugin.video.umbrella/)"',
            widgets,
        )

        poster_layout = (
            SKIN / "xml/IncludesViewsLayoutPoster.xml"
        ).read_text(encoding="utf-8")
        poster_variable = poster_layout.split(
            '<variable name="PosterThumbList">', 1
        )[1].split("</variable>", 1)[0]
        self.assertIn("<value>DefaultVideo.png</value>", poster_variable)
        self.assertIn("ListItem.Art(tvshow.poster)", poster_variable)
        self.assertIn(
            'ListItem.IsFolder + !String.IsEmpty(ListItem.Art(poster))',
            poster_variable,
        )
        self.assertIn(
            'ListItem.IsFolder + !String.IsEmpty(ListItem.Art(thumb))',
            poster_variable,
        )
        self.assertIn(
            'ListItem.IsFolder + !String.IsEmpty(ListItem.Icon)',
            poster_variable,
        )
        self.assertNotIn("ListItem.Art(fanart)", poster_variable)
        self.assertIn(
            "String.IsEqual(ListItem.Property(starlane.terminal),show_more)",
            poster_layout,
        )
        self.assertIn("colors/color_white.png", poster_layout)

        functions = (SKIN / "xml/IncludesFunctions.xml").read_text(encoding="utf-8")
        self.assertIn("SetProperty(StarlaneTerminalAction", functions)
        self.assertIn("ClearProperty(ListItem.Art.fanart,Home)", functions)
        self.assertIn(
            "!String.IsEqual(Container($PARAM[widgetid]).ListItem.Property(starlane.terminal),show_more)",
            functions,
        )

        template = (SKIN / "shortcuts/template.xml").read_text(encoding="utf-8")
        self.assertEqual(
            template.count(
                "String.IsEqual(Container(900).ListItem.Property(submenuVisibility),"
                "$SKINSHORTCUTS[submenuid])"
            ),
            8,
        )

        global_override = next(
            item for item in overrides.findall("override")
            if item.attrib.get("action") == "globaloverride"
            and item.attrib.get("group") == "mainmenu"
        )
        self.assertEqual(
            global_override.findtext("condition"),
            "!String.IsEqual(ListItem.Property(path),noop)",
        )
        self.assertEqual(
            [action.text for action in global_override.findall("action")],
            ["::ACTION::", "SetProperty(flushWidgetProps,1,Home)"],
        )



if __name__ == "__main__":
    unittest.main()

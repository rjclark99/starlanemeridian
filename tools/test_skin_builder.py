import unittest
from xml.etree import ElementTree

import skin_builder


class SkinBuilderTests(unittest.TestCase):
    def menu(self):
        return [
            {"id": "home", "label": "Home", "action": {"type": "kodi-window", "target": "home"}, "widgets": [
                {"id": "recent", "label": "Recently Added", "provider": "special://skin/playlists/recent_unwatched_movies.xsp", "limit": 12}
            ]},
            {"id": "search", "label": "Search", "action": {"type": "kodi-window", "target": "search"}, "widgets": []},
            {"id": "tv-shows", "label": "TV Shows", "action": {"type": "kodi-window", "target": "tvshows"}, "widgets": []},
            {"id": "movies", "label": "Movies", "action": {"type": "kodi-window", "target": "movies"}, "widgets": []},
            {"id": "live-tv", "label": "Live TV", "action": {"type": "kodi-window", "target": "live-tv"}, "widgets": []},
            {"id": "kids-family", "label": "Kids & Family", "action": {"type": "kodi-window", "target": "kids-family"}, "widgets": []},
        ]

    def test_home_is_valid_remote_first_xml(self):
        document = skin_builder.home_xml(self.menu())
        root = ElementTree.fromstring(document)
        self.assertEqual(root.findtext("defaultcontrol"), "9000")
        self.assertEqual(root.find(".//control[@id='9000']").attrib["type"], "list")
        self.assertIsNone(root.find(".//control[@id='9000']/focusposition"))
        self.assertIn("STARLANE MERIDIAN", document)
        self.assertIn("ActivateWindow(Videos,movietitles)", document)
        self.assertIn("ActivateWindow(TVChannels)", document)

    def test_menu_order_and_full_width_labels_are_fixed(self):
        document = skin_builder.home_xml(self.menu())
        root = ElementTree.fromstring(document)
        content = root.find(".//control[@id='9000']/content")
        self.assertEqual([item.findtext("label") for item in content.findall("item")],
                         ["Home", "Search", "TV Shows", "Movies", "Live TV", "Kids & Family"])
        nav = root.find(".//control[@id='9000']")
        nav_labels = nav.findall("./itemlayout/control[@type='label']") + nav.findall("./focusedlayout/control[@type='label']")
        self.assertTrue(nav_labels)
        self.assertTrue(all(int(label.findtext("width")) >= 260 for label in nav_labels))
        self.assertTrue(all(label.findtext("scroll") == "false" for label in nav_labels))
        resting_labels = nav.findall("./itemlayout/control[@type='label']")
        self.assertTrue(all(label.findtext("textcolor") == "FFF4FAFF" for label in resting_labels))

    def test_startup_is_branded_and_valid(self):
        root = ElementTree.fromstring(skin_builder.startup_xml())
        self.assertEqual(root.findtext("backgroundcolor"), "FF050B14")
        serialized = ElementTree.tostring(root, encoding="unicode")
        self.assertIn("brand/horizon.png", serialized)
        self.assertIn("STARLANE MERIDIAN", serialized)
        self.assertIn("ReplaceWindow($INFO[System.StartupWindow])", serialized)
        self.assertIn("00:02", serialized)

    def test_power_dialog_is_branded_complete_and_safely_padded(self):
        root = ElementTree.fromstring(skin_builder.power_dialog_xml())
        self.assertEqual(root.attrib.get("type"), "dialog")
        self.assertEqual(root.findtext("defaultcontrol"), "9000")
        serialized = ElementTree.tostring(root, encoding="unicode")
        self.assertIn("POWER &amp; SESSION", serialized)
        self.assertIn("brand/emblem.png", serialized)
        for action in ("Quit()", "Powerdown()", "Suspend()", "Hibernate()", "Reset()", "System.LogOff"):
            self.assertIn(action, serialized)
        panel = root.find(".//control[@id='9000']")
        self.assertEqual(panel.findtext("left"), "42")
        self.assertEqual(panel.findtext("width"), "616")
        focus_surface = panel.find("./focusedlayout/control[@type='image']")
        self.assertEqual(focus_surface.findtext("width"), "616")

    def test_widget_sources_are_allowlisted_and_performance_bounded(self):
        document = skin_builder.home_xml(self.menu())
        self.assertIn("<preloaditems>1</preloaditems>", document)
        self.assertIn('browse="never"', document)
        self.assertNotIn("script.skin.helper", document)
        poisoned = self.menu()
        poisoned[0]["widgets"][0]["provider"] = "plugin://attacker.invalid/execute"
        with self.assertRaisesRegex(SystemExit, "Unsupported widget provider"):
            skin_builder.home_xml(poisoned)

    def test_search_helper_is_optional_with_safe_fallback(self):
        document = skin_builder.home_xml(self.menu())
        self.assertIn("System.HasAddon(plugin.video.themoviedb.helper)", document)
        self.assertIn("System.HasAddon(script.globalsearch)", document)
        self.assertIn("Install TMDb Helper for search", document)

    def test_quick_access_is_full_width_padded_and_remote_navigable(self):
        root = ElementTree.fromstring(skin_builder.home_xml(self.menu()))
        self.assertEqual(root.findtext("menucontrol"), "9050")
        expected = {
            "9050": ("FAVOURITES", "ActivateWindow(FavouritesBrowser)"),
            "9051": ("ADD-ONS", "ActivateWindow(AddonBrowser)"),
            "9052": ("PROFILES", "ActivateWindow(Profiles)"),
            "9053": ("SETTINGS", "ActivateWindow(Settings)"),
            "9054": ("POWER", "ActivateWindow(ShutdownMenu)"),
        }
        for control_id, (label, action) in expected.items():
            control = root.find(f".//control[@id='{control_id}']")
            self.assertEqual(control.findtext("label"), label)
            self.assertEqual(control.findtext("onclick"), action)
            self.assertEqual(control.findtext("width"), "274")
            self.assertEqual(control.findtext("height"), "48")
            self.assertGreaterEqual(int(control.findtext("left")), 90)
            self.assertLessEqual(int(control.findtext("left")) + int(control.findtext("width")), 364)
            self.assertEqual(control.findtext("textcolor"), "FFF4FAFF")
            self.assertEqual(control.findtext("aligny"), "center")
            self.assertEqual(control.findtext("texturenofocus"), "")
            self.assertEqual(control.find("texturenofocus").attrib, {})

    def test_now_playing_ribbon_is_conditional_and_static(self):
        document = skin_builder.home_xml(self.menu())
        self.assertIn("Player.HasMedia", document)
        self.assertIn("Player.Progress", document)
        self.assertIn("$INFO[Player.Title]", document)
        self.assertNotIn("script.skin.helper", document)

    def test_untrusted_actions_cannot_be_compiled(self):
        with self.assertRaisesRegex(SystemExit, "Unsupported Kodi window"):
            skin_builder.action({"type": "kodi-window", "target": "../../shell"})
        with self.assertRaisesRegex(SystemExit, "plugin"):
            skin_builder.action({"type": "addon", "target": "https://attacker.invalid"})

    def test_brand_metadata_preserves_license_and_replaces_copy(self):
        root = ElementTree.fromstring("""<addon><extension point="xbmc.addon.metadata"><license>GPL-2.0</license><source>old</source><summary lang="en_GB">Old</summary></extension></addon>""")
        skin_builder.brand_metadata(root)
        metadata = root.find("extension")
        self.assertEqual(metadata.findtext("license"), "GPL-2.0")
        self.assertEqual(metadata.findtext("source"), "https://github.com/rjclark99/starlanemeridian")
        self.assertEqual(len(metadata.findall("summary")), 1)
        self.assertIn("calm, modern", metadata.findtext("summary"))


if __name__ == "__main__":
    unittest.main()

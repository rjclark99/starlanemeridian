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
        self.assertEqual(addon.attrib["version"], "2.2.3")
        self.assertEqual(addon.attrib["name"], "Starlane Movies")
        metadata = addon.find("extension[@point='xbmc.addon.metadata']")
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.findtext("license"), "GPL v2.0")
        self.assertEqual(
            metadata.findtext("source"),
            "https://github.com/AchillesPunks/skin.titan.bingie.mod/",
        )
        self.assertTrue((SKIN / "LICENSE").is_file())

    def test_brand_assets_and_startup_are_present(self):
        for relative_path in (
            "extras/starlane-movies/emblem.png",
            "extras/starlane-movies/horizon.png",
            "xml/Startup.xml",
        ):
            self.assertTrue((SKIN / relative_path).is_file(), relative_path)

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


if __name__ == "__main__":
    unittest.main()

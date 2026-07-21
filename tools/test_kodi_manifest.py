import importlib
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree


def load_manifest_module():
    addon_root = Path(__file__).resolve().parents[1] / "kodi" / "repository.kodisetup"
    if str(addon_root) not in sys.path:
        sys.path.insert(0, str(addon_root))
    return importlib.import_module("resources.lib.manifest")


class KodiManifestTests(unittest.TestCase):
    def setUp(self):
        self.module = load_manifest_module()
        self.document = {
            "schemaVersion": 1,
            "stage": "test",
            "kodi": {"channel": "stable", "packageName": "org.xbmc.kodi"},
            "repositories": [],
            "addons": [],
            "skin": {"addonId": "skin.starlanemeridian", "homeMenu": [{"action": {"type": "noop"}}]},
        }

    def test_custom_skin_is_allowlisted_by_manifest_contract(self):
        self.module.validate(self.document)

    def test_arbitrary_menu_actions_are_rejected(self):
        self.document["skin"]["homeMenu"][0]["action"]["type"] = "shell"
        with self.assertRaisesRegex(ValueError, "unsafe menu action"):
            self.module.validate(self.document)

    def test_bootstrap_string_settings_have_kodi_readable_defaults(self):
        settings_path = Path(__file__).resolve().parents[1] / "kodi" / "repository.kodisetup" / "resources" / "settings.xml"
        root = ElementTree.parse(settings_path).getroot()
        string_settings = [item for item in root.iter("setting") if item.attrib.get("type") == "string"]
        self.assertGreater(len(string_settings), 0)
        for item in string_settings:
            default = item.find("default")
            self.assertIsNotNone(default, item.attrib["id"])
            self.assertTrue(default.text, item.attrib["id"])

        defaults = {item.attrib["id"]: item.findtext("default") for item in string_settings}
        self.assertEqual("__unset__", defaults["pending_skin"])
        self.assertEqual("__unset__", defaults["previous_skin"])


if __name__ == "__main__":
    unittest.main()

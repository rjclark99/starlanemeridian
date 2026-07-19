import importlib
import sys
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()

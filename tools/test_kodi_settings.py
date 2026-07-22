import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "kodi" / "repository.kodisetup"))
from resources.lib.kodi_settings import disable_core_splash


class KodiSettingsTests(unittest.TestCase):
    def test_disables_splash_without_discarding_existing_settings(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "advancedsettings.xml"
            path.write_text("<advancedsettings><network><curlclienttimeout>20</curlclienttimeout></network></advancedsettings>", encoding="utf-8")
            self.assertTrue(disable_core_splash(str(path)))
            root = ElementTree.parse(path).getroot()
            self.assertEqual(root.findtext("splash"), "false")
            self.assertEqual(root.findtext("network/curlclienttimeout"), "20")
            self.assertFalse(disable_core_splash(str(path)))

    def test_rejects_unexpected_or_malformed_documents(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "advancedsettings.xml"
            path.write_text("<settings />", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unexpected root"):
                disable_core_splash(str(path))
            self.assertEqual(path.read_text(encoding="utf-8"), "<settings />")


if __name__ == "__main__":
    unittest.main()

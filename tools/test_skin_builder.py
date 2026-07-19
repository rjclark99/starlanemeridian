import unittest
from xml.etree import ElementTree

import skin_builder


class SkinBuilderTests(unittest.TestCase):
    def test_home_is_valid_remote_first_xml(self):
        document = skin_builder.home_xml([
            {"id": "movies", "label": "Movies", "action": {"type": "kodi-window", "target": "movies"}, "widgets": []},
            {"id": "favourites", "label": "Favourites", "action": {"type": "favourite", "target": ""}, "widgets": []},
        ])
        root = ElementTree.fromstring(document)
        self.assertEqual(root.findtext("defaultcontrol"), "9000")
        self.assertIn("STARLANE MERIDIAN", document)
        self.assertIn("ActivateWindow(Videos,movietitles)", document)
        self.assertIn("ActivateWindow(Favourites)", document)

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

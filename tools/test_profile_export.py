import tempfile
import unittest
from pathlib import Path

from profile_export import export_profile, parse_settings, safe_setting


class ProfileExportTests(unittest.TestCase):
    def test_sensitive_keys_and_values_are_rejected(self):
        self.assertFalse(safe_setting("oauth_token", "hello"))
        self.assertFalse(safe_setting("theme", "person@example.com"))
        self.assertFalse(safe_setting("endpoint", "https://example.com/path"))
        self.assertTrue(safe_setting("items_per_page", "20"))

    def test_settings_are_typed_and_secrets_omitted(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "settings.xml"
            path.write_text('<settings><setting id="enabled">true</setting><setting id="limit">20</setting><setting id="password">nope</setting></settings>')
            kept, omitted = parse_settings(path)
            self.assertEqual(kept, {"enabled": True, "limit": 20})
            self.assertEqual(omitted, ["password"])

    def test_export_is_inventory_not_installable_backup(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); addon = root / "addons" / "plugin.video.safe"; addon.mkdir(parents=True)
            (addon / "addon.xml").write_text('<addon id="plugin.video.safe" name="Safe" version="1.2.3"><extension point="xbmc.python.pluginsource"/></addon>')
            output = root / "out" / "profile.json"
            document = export_profile(root, output)
            self.assertFalse(document["installable"])
            self.assertEqual(document["addons"][0]["id"], "plugin.video.safe")
            self.assertNotIn("userdata", output.read_text())


if __name__ == "__main__":
    unittest.main()

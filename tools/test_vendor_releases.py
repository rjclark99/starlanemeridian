import unittest
from unittest.mock import patch

import check_vendor_releases


class StableKodiTests(unittest.TestCase):
    @patch("check_vendor_releases.get_text")
    def test_accepts_two_part_versions_and_selects_latest_stable(self, get_text):
        get_text.return_value = """
            <a href="kodi-18.7.2-Leia-arm64-v8a.apk">old</a>
            <a href="kodi-21.3-Omega-arm64-v8a.apk">stable</a>
            <a href="kodi-22.0-Beta1-arm64-v8a.apk">beta</a>
        """

        candidate = check_vendor_releases.stable_kodi(
            "arm64-v8a", "https://mirrors.kodi.tv/releases/android/arm64-v8a/"
        )

        self.assertEqual("21.3", candidate["version"])
        self.assertTrue(candidate["url"].endswith("kodi-21.3-Omega-arm64-v8a.apk"))
        self.assertIsNone(candidate["sha256"])
        self.assertIsNone(candidate["signerSha256"])

    @patch("check_vendor_releases.get_text", return_value="<html></html>")
    def test_rejects_directory_without_stable_builds(self, _get_text):
        with self.assertRaisesRegex(RuntimeError, "No stable Kodi build"):
            check_vendor_releases.stable_kodi("armeabi-v7a", "https://example.invalid/")


if __name__ == "__main__":
    unittest.main()

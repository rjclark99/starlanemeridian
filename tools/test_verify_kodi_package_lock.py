import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.verify_kodi_package_lock import selected_packages, verify


class VerifyKodiPackageLockTests(unittest.TestCase):
    def test_selects_fixed_and_matching_abi_packages(self):
        document = {
            "packages": [
                {"id": "fixed", "version": "1.0", "url": "https://fixed", "sha256": "a" * 64},
                {
                    "id": "binary",
                    "version": "2.0",
                    "variants": {
                        "armeabi-v7a": {"url": "https://arm", "sha256": "b" * 64},
                        "arm64-v8a": {"url": "https://arm64", "sha256": "c" * 64},
                    },
                },
            ]
        }
        self.assertEqual(
            [("fixed", "1.0", "https://fixed", "a" * 64), ("binary", "2.0", "https://arm", "b" * 64)],
            list(selected_packages(document, "armeabi-v7a")),
        )

    def test_reports_only_mismatches_in_quiet_mode(self):
        document = {"packages": [{"id": "example", "version": "1.0", "url": "https://example", "sha256": "a" * 64}]}
        with tempfile.TemporaryDirectory() as name:
            lock = Path(name) / "lock.json"
            lock.write_text(json.dumps(document), encoding="utf-8")
            with patch("tools.verify_kodi_package_lock.remote_sha256", return_value=("b" * 64, 12)), contextlib.redirect_stdout(io.StringIO()):
                failures = verify(lock, "armeabi-v7a", 1)
        self.assertEqual(1, len(failures))
        self.assertIn("example 1.0", failures[0])


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from validate_fresh_install_release import ROOT, validate, verify_file


class FreshInstallReleaseTests(unittest.TestCase):
    def test_checked_in_candidate_has_one_consistent_release_identity(self):
        validate(ROOT, "v0.5.11-test")

    def test_wrong_release_tag_is_rejected_before_build_or_upload(self):
        with self.assertRaisesRegex(SystemExit, "Release tag must be v0.5.11-test"):
            validate(ROOT, "v0.5.10-test")

    def test_release_tag_is_pinned_to_the_tested_workflow_commit(self):
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("target_commitish: ${{ github.sha }}", workflow)

    def test_release_asset_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            artifact = Path(name) / "artifact.zip"
            artifact.write_bytes(b"wrong")
            with self.assertRaisesRegex(SystemExit, "hash does not match"):
                verify_file(artifact, "0" * 64, "candidate archive")


if __name__ == "__main__":
    unittest.main()

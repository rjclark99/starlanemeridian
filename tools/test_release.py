import base64
import json
import tempfile
import unittest
import importlib.util
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from release import canonical_payload, safe_zip_tree


class ReleaseTests(unittest.TestCase):
    def test_canonical_payload_blanks_signature_and_sorts(self):
        value = {"z": 1, "signature": {"value": "secret", "algorithm": "Ed25519"}, "a": 2}
        self.assertEqual(canonical_payload(value), b'{"a":2,"signature":{"algorithm":"Ed25519","value":""},"z":1}')

    def test_signature_contract(self):
        value = {"signature": {"value": "", "algorithm": "Ed25519"}, "schemaVersion": 1}
        key = Ed25519PrivateKey.generate()
        signature = key.sign(canonical_payload(value))
        key.public_key().verify(signature, canonical_payload(value))

    def test_kodi_pure_python_verifier_matches_release_signer(self):
        module_path = Path(__file__).resolve().parents[1] / "kodi" / "repository.kodisetup" / "resources" / "lib" / "ed25519_verify.py"
        spec = importlib.util.spec_from_file_location("kodi_ed25519", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        key = Ed25519PrivateKey.generate()
        message = b"signed setup manifest"
        signature = key.sign(message)
        from cryptography.hazmat.primitives import serialization
        public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        self.assertTrue(module.verify(signature, message, public))
        self.assertFalse(module.verify(signature, message + b"!", public))

    def test_zip_is_reproducible_and_rooted(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); source = root / "source"; source.mkdir(); (source / "file.txt").write_text("ok")
            first, second = root / "first.zip", root / "second.zip"
            safe_zip_tree(source, first, "addon.id"); safe_zip_tree(source, second, "addon.id")
            self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main()

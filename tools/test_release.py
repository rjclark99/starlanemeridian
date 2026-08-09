import base64
import hashlib
import io
import json
import tempfile
import unittest
import importlib.util
import zipfile
from unittest.mock import patch
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from release import (
    build_kodi,
    canonical_payload,
    download_provider_source,
    latest_skin_zip,
    safe_zip_tree,
    verify_manifest,
    write_release_checksums,
)


class ReleaseTests(unittest.TestCase):
    def test_client_release_excludes_owner_administration_tooling(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        for forbidden in ("admin-portal", "KodiSetup.Admin", "Admin-win", "households.vault"):
            self.assertNotIn(forbidden, workflow)
        self.assertIn("draft: true", workflow)
        self.assertIn("cp config/manifest.json artifacts/manifest.json", workflow)
        self.assertIn("release.py checksums", workflow)
        self.assertIn("verify_kodi_package_lock.py --local-assets", workflow)
        self.assertEqual(workflow.count("validate_fresh_install_release.py"), 2)
        self.assertIn('RELEASE_TAG: ${{ inputs.tag }}', workflow)
        self.assertNotIn("secrets.PUBLIC_MANIFEST_URL", workflow)
        self.assertNotIn("secrets.MANIFEST_PUBLIC_KEY", workflow)
        self.assertNotIn("secrets.CONTROL_API_URL", workflow)
        self.assertIn("releases/latest/download/manifest.json", workflow)
        self.assertIn("$(cat ../config/manifest.pub)", workflow)
        self.assertIn("https://control.starlanemeridian.uk", workflow)
        self.assertNotIn("python tools/build_brand_assets.py", workflow)
        self.assertNotIn("find artifacts -type f", workflow)
        self.assertIn("artifacts/manifest.json", workflow)
        self.assertFalse((root / "admin-portal").exists())
        self.assertFalse((root / "admin-portal.tests").exists())
        self.assertFalse((root / "tools" / "start_admin_portal.ps1").exists())
        owner_guide = (root / "docs" / "OWNER_SETUP_GUIDE.md").read_text(encoding="utf-8")
        self.assertNotIn("repository.kodisetup-1.1.0.zip", owner_guide)
        self.assertIn("repository.kodisetup-1.1.16.zip", owner_guide)

    def test_release_checksum_inventory_matches_only_uploaded_assets(self):
        with tempfile.TemporaryDirectory() as name:
            artifacts = Path(name) / "artifacts"
            kodi = artifacts / "kodi" / "repository.kodisetup"
            kodi.mkdir(parents=True)
            expected = {
                "setup.apk": b"apk",
                "manifest.json": b"manifest",
                "sbom.spdx.json": b"sbom",
                "repository.kodisetup-1.1.16.zip": b"bootstrap",
            }
            for filename, payload in expected.items():
                destination = kodi / filename if filename.startswith("repository.") else artifacts / filename
                destination.write_bytes(payload)
            (artifacts / "kodi-source.zip").write_bytes(b"build input")
            skin_input = artifacts / "skin" / "skin.starlanemeridian-1.3.0.zip"
            skin_input.parent.mkdir()
            skin_input.write_bytes(b"duplicate build output")

            output = artifacts / "SHA256SUMS"
            write_release_checksums(artifacts, output)

            lines = output.read_bytes().splitlines()
            self.assertTrue(output.read_bytes().endswith(b"\n"))
            self.assertNotIn(b"\r", output.read_bytes())
            actual_names = {line.split(b"  ", 1)[1].decode("ascii") for line in lines}
            self.assertEqual(set(expected), actual_names)
            for line in lines:
                digest, filename = line.decode("ascii").split("  ", 1)
                self.assertEqual(hashlib.sha256(expected[filename]).hexdigest(), digest)

    def test_release_checksum_inventory_rejects_flattened_name_collisions(self):
        with tempfile.TemporaryDirectory() as name:
            artifacts = Path(name) / "artifacts"
            for filename in ("setup.apk", "manifest.json", "sbom.spdx.json"):
                (artifacts / filename).parent.mkdir(parents=True, exist_ok=True)
                (artifacts / filename).write_bytes(filename.encode("ascii"))
            for directory in ("first", "second"):
                target = artifacts / "kodi" / directory / "same.zip"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(directory.encode("ascii"))
            with self.assertRaisesRegex(SystemExit, "Duplicate flattened"):
                write_release_checksums(artifacts, artifacts / "SHA256SUMS")

    def test_canonical_payload_blanks_signature_and_sorts(self):
        value = {"z": 1, "signature": {"value": "secret", "algorithm": "Ed25519"}, "a": 2}
        self.assertEqual(canonical_payload(value), b'{"a":2,"signature":{"algorithm":"Ed25519","value":""},"z":1}')

    def test_signature_contract(self):
        value = {"signature": {"value": "", "algorithm": "Ed25519"}, "schemaVersion": 1}
        key = Ed25519PrivateKey.generate()
        signature = key.sign(canonical_payload(value))
        key.public_key().verify(signature, canonical_payload(value))

    def test_offline_signature_verification(self):
        from cryptography.hazmat.primitives import serialization
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            document = json.loads((Path(__file__).resolve().parents[1] / "config" / "manifest.example.json").read_text(encoding="utf-8"))
            key = Ed25519PrivateKey.generate()
            document["signature"]["value"] = base64.urlsafe_b64encode(key.sign(canonical_payload(document))).decode("ascii").rstrip("=")
            manifest = root / "manifest.json"; manifest.write_text(json.dumps(document), encoding="utf-8")
            public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
            public_path = root / "manifest.pub"; public_path.write_text(base64.urlsafe_b64encode(public).decode("ascii").rstrip("="), encoding="ascii")
            verify_manifest(manifest, public_path)

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

    def test_zip_normalizes_text_line_endings_across_build_hosts(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            windows = root / "windows"; linux = root / "linux"
            windows.mkdir(); linux.mkdir()
            windows.joinpath("service.py").write_bytes(b"first\r\nsecond\r\n")
            linux.joinpath("service.py").write_bytes(b"first\nsecond\n")
            windows.joinpath("category.xsp").write_bytes(b"<smartplaylist>\r\n</smartplaylist>\r\n")
            linux.joinpath("category.xsp").write_bytes(b"<smartplaylist>\n</smartplaylist>\n")
            windows.joinpath("LICENSE").write_bytes(b"terms\r\n")
            linux.joinpath("LICENSE").write_bytes(b"terms\n")
            windows.joinpath("Z-last-on-Windows.py").write_bytes(b"same\r\n")
            linux.joinpath("Z-last-on-Windows.py").write_bytes(b"same\n")
            windows.joinpath("a-first-on-Windows.py").write_bytes(b"same\r\n")
            linux.joinpath("a-first-on-Windows.py").write_bytes(b"same\n")
            windows.joinpath("icon.png").write_bytes(b"binary\r\nbytes")
            linux.joinpath("icon.png").write_bytes(b"binary\r\nbytes")
            first, second = root / "windows.zip", root / "linux.zip"
            safe_zip_tree(windows, first, "addon.id")
            safe_zip_tree(linux, second, "addon.id")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                self.assertTrue(all(info.create_system == 3 for info in archive.infolist()))
                self.assertTrue(all(info.compress_type == zipfile.ZIP_STORED for info in archive.infolist()))
                self.assertLess(
                    archive.namelist().index("addon.id/Z-last-on-Windows.py"),
                    archive.namelist().index("addon.id/a-first-on-Windows.py"),
                )
                self.assertEqual(archive.read("addon.id/service.py"), b"first\nsecond\n")
                self.assertEqual(archive.read("addon.id/category.xsp"), b"<smartplaylist>\n</smartplaylist>\n")
                self.assertEqual(archive.read("addon.id/LICENSE"), b"terms\n")
                self.assertEqual(archive.read("addon.id/icon.png"), b"binary\r\nbytes")

    def test_latest_skin_artifact_is_selected_semantically(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            for version in ("1.0.9", "1.1.0", "1.0.10"):
                root.joinpath(f"skin.starlanemeridian-{version}.zip").touch()
            self.assertEqual(latest_skin_zip(root).name, "skin.starlanemeridian-1.1.0.zip")

    def test_kodi_repository_checksum_matches_published_bytes(self):
        import hashlib
        with tempfile.TemporaryDirectory() as name:
            output = Path(name) / "kodi"
            build_kodi(output, "https://github.com/example/project/releases/latest/download")
            expected = (output / "addons.xml.sha256").read_text(encoding="ascii").strip()
            self.assertEqual(hashlib.sha256((output / "addons.xml").read_bytes()).hexdigest(), expected)

    def test_bootstrap_archive_matches_signed_manifest(self):
        with tempfile.TemporaryDirectory() as name:
            output = Path(name) / "kodi"
            build_kodi(
                output,
                "https://github.com/rjclark99/starlanemeridian/releases/latest/download",
                "https://control.starlanemeridian.uk/v1/public/kodi",
            )
            document = json.loads((Path(__file__).resolve().parents[1] / "config" / "manifest.json").read_text(encoding="utf-8"))
            archive = next((output / "repository.kodisetup").glob("repository.kodisetup-*.zip"))
            self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), document["bootstrap"]["sha256"])

    def test_kodi_repository_uses_routable_data_layout_and_zip_sidecars(self):
        import hashlib
        with tempfile.TemporaryDirectory() as name:
            output = Path(name) / "kodi"
            build_kodi(output, "https://github.com/example/project/releases/latest/download", "https://control.example.test/v1/public/kodi")
            repository_zip = next((output / "repository.kodisetup").glob("repository.kodisetup-*.zip"))
            sidecar = repository_zip.with_name(repository_zip.name + ".sha256")
            self.assertEqual(sidecar.read_text(encoding="ascii").strip(), hashlib.sha256(repository_zip.read_bytes()).hexdigest())
            self.assertTrue(sidecar.read_bytes().endswith(b"\n"))
            self.assertNotIn(b"\r", sidecar.read_bytes())
            with __import__("zipfile").ZipFile(repository_zip) as archive:
                addon_xml = archive.read("repository.kodisetup/addon.xml").decode("utf-8")
            self.assertIn('<datadir zip="true">https://control.example.test/v1/public/kodi/</datadir>', addon_xml)
            self.assertNotIn("${REPOSITORY_", addon_xml)
            private_skin = output / "skin.starlane.movies" / "skin.starlane.movies-2.2.22.zip"
            self.assertTrue(private_skin.is_file())
            self.assertEqual(
                private_skin.with_name(private_skin.name + ".sha256").read_text(encoding="ascii").strip(),
                hashlib.sha256(private_skin.read_bytes()).hexdigest(),
            )
            with __import__("zipfile").ZipFile(private_skin) as archive:
                names = archive.namelist()
                self.assertIn("skin.starlane.movies/addon.xml", names)
                self.assertIn("skin.starlane.movies/LICENSE", names)
                self.assertFalse(any("__pycache__" in name or name.endswith(".pyc") for name in names))
            addons_xml = (output / "addons.xml").read_text(encoding="utf-8")
            self.assertIn('id="skin.starlane.movies"', addons_xml)

    def test_kodi_repository_builds_hash_locked_branded_provider(self):
        import zipfile
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            upstream = root / "plugin.video.umbrella-6.7.81.zip"
            with zipfile.ZipFile(upstream, "w") as archive:
                archive.writestr(
                    "plugin.video.umbrella/addon.xml",
                    '<addon id="plugin.video.umbrella" name="Umbrella" '
                    'provider-name="Umbrella" version="6.7.81">'
                    '<extension point="xbmc.addon.metadata"><summary>Umbrella</summary>'
                    '<description>Umbrella</description><assets /></extension></addon>',
                )
                for artwork_name in (
                    "icon.png",
                    "fanart.jpg",
                    "banner.png",
                    "genres.png",
                ):
                    archive.writestr(
                        "plugin.video.umbrella/resources/artwork/umbrella/"
                        + artwork_name,
                        b"reviewed-upstream-artwork",
                    )
            digest = hashlib.sha256(upstream.read_bytes()).hexdigest()
            output = root / "kodi"
            build_kodi(
                output,
                "https://github.com/example/project/releases/latest/download",
                provider_archive=upstream,
                provider_sha256=digest,
            )
            provider = (
                output
                / "plugin.video.umbrella"
                / "plugin.video.umbrella-6.7.81.5.zip"
            )
            self.assertTrue(provider.is_file())
            self.assertEqual(
                hashlib.sha256(provider.read_bytes()).hexdigest(),
                provider.with_name(provider.name + ".sha256")
                .read_text(encoding="ascii")
                .strip(),
            )
            self.assertIn(
                'id="plugin.video.umbrella"',
                (output / "addons.xml").read_text(encoding="utf-8"),
            )

    def test_provider_source_download_is_pinned_by_hash(self):
        payload = b"reviewed upstream provider archive"
        with tempfile.TemporaryDirectory() as name:
            destination = Path(name) / "provider.zip"
            with patch(
                "release.PROVIDER_SOURCE_SHA256",
                hashlib.sha256(payload).hexdigest(),
            ), patch(
                "release.urllib.request.urlopen",
                return_value=io.BytesIO(payload),
            ):
                download_provider_source(destination)
            self.assertEqual(payload, destination.read_bytes())

            with patch("release.PROVIDER_SOURCE_SHA256", "0" * 64), patch(
                "release.urllib.request.urlopen",
                return_value=io.BytesIO(payload),
            ):
                with self.assertRaisesRegex(SystemExit, "hash mismatch"):
                    download_provider_source(destination)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()

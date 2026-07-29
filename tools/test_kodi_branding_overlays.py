import hashlib
import sqlite3
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from PIL import Image

from tools.build_kodi_branding_overlays import (
    ADDONS,
    build,
    build_from_archive,
    replace_human_brand,
)
from tools.kodi_texture_cache import matching_rows


class KodiBrandingOverlayTests(unittest.TestCase):
    def test_texture_cache_match_is_limited_to_provider_brand_art(self):
        connection = sqlite3.connect(":memory:")
        connection.execute(
            "CREATE TABLE texture (id INTEGER PRIMARY KEY, url TEXT, cachedurl TEXT)"
        )
        connection.executemany(
            "INSERT INTO texture (id, url, cachedurl) VALUES (?, ?, ?)",
            (
                (
                    1,
                    "image://C%3a/addons/plugin.video.umbrella/icon.png/",
                    "a/a.png",
                ),
                (
                    2,
                    "image://C%3a/addons/plugin.video.umbrella/resources/artwork/"
                    "umbrella/genres.png/",
                    "b/b.png",
                ),
                (
                    3,
                    "image://C%3a/addons/plugin.video.umbrella/resources/artwork/"
                    "umbrella/banner.png/",
                    "c/c.png",
                ),
                (
                    4,
                    "image://C%3a/addons/plugin.video.other/icon.png/",
                    "d/d.png",
                ),
            ),
        )

        self.assertEqual(
            [(row[0], row[2]) for row in matching_rows(connection)],
            [(1, "a/a.png"), (3, "c/c.png")],
        )

    def test_human_brand_replacement_preserves_internal_identifiers(self):
        umbrella = ADDONS[0]
        text = (
            "Umbrella Settings | UMBRELLA | showUmbrella | "
            "isUmbrella_widget | plugin.video.umbrella | UmbrellaPlayer"
        )
        self.assertEqual(
            replace_human_brand(text, umbrella),
            (
                "Starlane Movies Settings | STARLANE MOVIES | showUmbrella | "
                "isUmbrella_widget | plugin.video.umbrella | UmbrellaPlayer"
            ),
        )

    def test_build_rebrands_metadata_strings_and_artwork_without_changing_ids(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            output = root / "output"
            for addon in ADDONS:
                addon_root = source / addon.addon_id
                language = addon_root / "resources" / "language" / "English"
                screenshots = addon_root / "resources" / "screenshots"
                language.mkdir(parents=True)
                screenshots.mkdir(parents=True)
                Image.new("RGB", (32, 32), "red").save(addon_root / "icon.png")
                Image.new("RGB", (64, 36), "red").save(addon_root / "fanart.jpg")
                Image.new("RGB", (16, 9), "red").save(screenshots / "old.jpg")
                original_name = addon.upstream_name
                (language / "strings.po").write_text(
                    f'msgid "{original_name} Settings"\n'
                    f'msgstr "{original_name} Settings"\n',
                    encoding="utf-8",
                )
                (addon_root / "entry.py").write_text(
                    f"# {original_name} upstream credit\n"
                    f"notice = '{original_name} is ready'\n"
                    f"route = 'plugin://{addon.addon_id}/'\n",
                    encoding="utf-8",
                )
                if addon.addon_id == "plugin.video.umbrella":
                    control = addon_root / "resources/lib/modules/control.py"
                    control.parent.mkdir(parents=True, exist_ok=True)
                    control.write_text(
                        "notification('Umbrella', 'Ready')\n"
                        "setting_key = 'context.useUmbrellaContext'\n"
                        "route = 'plugin://plugin.video.umbrella/'\n",
                        encoding="utf-8",
                    )
                    router = addon_root / "resources/lib/modules/router.py"
                    router.write_text(
                        "if isUpdate:\n"
                        "            from resources.lib.modules import changelog\n"
                        "            changelog.get('Umbrella')\n"
                        "elif action == 'changelog':\n"
                        "    changelog.get('Umbrella')\n",
                        encoding="utf-8",
                    )
                    (addon_root / "service.py").write_text(
                        "testUmbrella = False\n"
                        "\tif len(str(control.getUmbrellaVersion())) > 6:\n"
                        "\t\trepoVersion = control.addon('repository.umbrellakodi').getAddonInfo('version')\n"
                        "\t\trepoName = 'repository.umbrellakodi'\n"
                        "\t\ttestUmbrella = True\n"
                        "\telse:\n"
                        "\t\ttry:\n"
                        "\t\t\trepoVersion = control.addon('repository.umbrella').getAddonInfo('version')\n"
                        "\t\t\trepoName = 'repository.umbrella'\n"
                        "\t\texcept Exception:\n"
                        "\t\t\trepoVersion = 'unknown'\n"
                        "\t\t\trepoName = 'Unknown Repo'\n"
                        "def main():\n"
                        "\twhile not control.monitor.abortRequested():\n"
                        "\t\tSyncMyAccounts().run()\n"
                        "\t\tPremAccntNotification().run()\n"
                        "\t\tif control.setting('general.checkAddonUpdates') == 'true':\n"
                        "\t\t\tAddonCheckUpdate().run()\n",
                        encoding="utf-8",
                    )
                (addon_root / "addon.xml").write_text(
                    (
                        f'<addon id="{addon.addon_id}" name="{original_name}" '
                        f'provider-name="{original_name}" version="{addon.source_version}">'
                        '<extension point="xbmc.addon.metadata">'
                        f'<summary>{original_name}</summary>'
                        f'<description>{original_name}</description>'
                        '<license>GPL</license>'
                        '<assets><icon>icon.png</icon><fanart>fanart.jpg</fanart>'
                        '<screenshot>resources/screenshots/old.jpg</screenshot></assets>'
                        "</extension></addon>"
                    ),
                    encoding="utf-8",
                )

            artifacts = build(source, output)
            self.assertEqual(len(artifacts), 1)
            for addon, artifact in zip(ADDONS, artifacts):
                addon_root = output / addon.addon_id
                metadata = ET.parse(addon_root / "addon.xml").getroot()
                self.assertEqual(metadata.attrib["id"], addon.addon_id)
                self.assertEqual(metadata.attrib["version"], addon.branded_version)
                self.assertEqual(metadata.attrib["name"], addon.display_name)
                self.assertEqual(metadata.attrib["provider-name"], "Starlane Movies")
                self.assertFalse(metadata.findall(".//screenshot"))
                self.assertFalse((addon_root / "resources" / "screenshots").exists())
                translated = (
                    addon_root / "resources/language/English/strings.po"
                ).read_text(encoding="utf-8")
                self.assertIn("Starlane Movies", translated)
                self.assertNotIn(addon.upstream_name, translated)
                entry = (addon_root / "entry.py").read_text(encoding="utf-8")
                self.assertIn(f"plugin://{addon.addon_id}/", entry)
                self.assertIn("# " + addon.upstream_name + " upstream credit", entry)
                self.assertIn(f"'{addon.upstream_name} is ready'", entry)
                if addon.addon_id == "plugin.video.umbrella":
                    control = (
                        addon_root / "resources/lib/modules/control.py"
                    ).read_text(encoding="utf-8")
                    self.assertIn("notification('Starlane Movies',", control)
                    self.assertIn("'context.useUmbrellaContext'", control)
                    self.assertIn("'plugin://plugin.video.umbrella/'", control)
                    router = (
                        addon_root / "resources/lib/modules/router.py"
                    ).read_text(encoding="utf-8")
                    self.assertNotIn("if isUpdate:\n            from resources.lib.modules import changelog", router)
                    self.assertIn("elif action == 'changelog':", router)
                    service = (addon_root / "service.py").read_text(encoding="utf-8")
                    self.assertIn(
                        "window.clearProperty('starlane.umbrella.ready')",
                        service,
                    )
                    self.assertIn(
                        "window.setProperty('starlane.umbrella.ready', 'true')",
                        service,
                    )
                    self.assertIn("repoVersion = 'managed'", service)
                    self.assertIn("repoName = 'Starlane package lock'", service)
                    self.assertNotIn("repository.umbrellakodi", service)
                    self.assertNotIn("control.addon('repository.umbrella')", service)
                    self.assertNotIn("AddonCheckUpdate().run()", service)
                    self.assertIn("package lock exclusively owns provider updates", service)
                self.assertTrue((addon_root / "UPSTREAM_ATTRIBUTION.txt").is_file())
                self.assertNotEqual(
                    Image.open(addon_root / "icon.png").getpixel((0, 0)),
                    (255, 0, 0),
                )
                with zipfile.ZipFile(artifact) as archive:
                    self.assertEqual(
                        artifact.name,
                        f"{addon.addon_id}-{addon.branded_version}.zip",
                    )
                    names = archive.namelist()
                    self.assertIn(f"{addon.addon_id}/addon.xml", names)
                    self.assertTrue(all("\\" not in name for name in names))

    def test_archive_input_is_hash_locked_and_reproducible(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source_root = root / "source" / "plugin.video.umbrella"
            source_root.mkdir(parents=True)
            (source_root / "addon.xml").write_text(
                '<addon id="plugin.video.umbrella" name="Umbrella" '
                'provider-name="Umbrella" version="6.7.81">'
                '<extension point="xbmc.addon.metadata"><summary>Umbrella</summary>'
                '<description>Umbrella</description><assets /></extension></addon>',
                encoding="utf-8",
            )
            archive_path = root / "upstream.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.write(
                    source_root / "addon.xml",
                    "plugin.video.umbrella/addon.xml",
                )
            digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
            first = build_from_archive(archive_path, digest, root / "first")[0]
            second = build_from_archive(archive_path, digest, root / "second")[0]
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with self.assertRaisesRegex(ValueError, "expected SHA-256"):
                build_from_archive(archive_path, "0" * 64, root / "bad")


if __name__ == "__main__":
    unittest.main()

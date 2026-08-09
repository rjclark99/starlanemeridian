import hashlib
import json
import sqlite3
import sys
import tempfile
import unittest
import types
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from PIL import Image

from tools.build_kodi_branding_overlays import (
    ADDONS,
    add_tmdb_request_diagnostics,
    CANONICAL_PROVIDER_ARTWORK,
    DIRECTORY_LOGO_HOSTS,
    DIRECTORY_LOGO_MINIMUM,
    DIRECTORY_LOGO_RESOURCE,
    build,
    build_from_archive,
    localise_directory_logo_artwork,
    package,
    preserve_absolute_directory_artwork,
    replace_human_brand,
    rewrite_discovery_previews,
    rewrite_user_facing_python,
)
from tools.kodi_texture_cache import matching_rows


class KodiBrandingOverlayTests(unittest.TestCase):
    def test_tmdb_request_diagnostics_are_redacted_and_stable(self):
        with tempfile.TemporaryDirectory() as temp:
            addon_root = Path(temp) / "plugin.video.umbrella"
            tmdb = addon_root / "resources/lib/indexers/tmdb.py"
            tmdb.parent.mkdir(parents=True)
            tmdb.write_text(
                "import requests\nfrom urllib3.util.retry import Retry\n"
                "class TMDb:\n"
                "\tdef get_request(self, url):\n"
                "\t\ttry:\n\t\t\ttry: response = session.get(url, timeout=20)\n"
                "\t\t\texcept requests.exceptions.SSLError:\n\t\t\t\tresponse = session.get(url, verify=False)\n"
                "\t\texcept requests.exceptions.ConnectionError:\n\t\t\tnotification(message=32024)\n"
                "\t\t\tfrom resources.lib.modules import log_utils\n\t\t\tlog_utils.error()\n\t\t\treturn None\n"
                "\t\ttry:\n\t\t\tif response.status_code in (200, 201): return response.json()\n"
                "\t\t\telif response.status_code == 404: return '404:NOT FOUND'\n"
                "\t\t\telif 'Retry-After' in response.headers: return self.get_request(url)\n"
                "\t\t\telse: return None\n"
                "\t\texcept:\n\t\t\tfrom resources.lib.modules import log_utils\n\t\t\tlog_utils.error()\n\t\t\treturn None\n"
                "\tdef get_v4_request(self, url):\n"
                "\t\theaders = {}\n"
                "\t\ttry:\n"
                "\t\t\ttry: response = session.get(url, headers=headers, timeout=20)\n"
                "\t\t\texcept requests.exceptions.SSLError:\n"
                "\t\t\t\tresponse = session.get(url, headers=headers, verify=False)\n"
                "\t\t\treturn response.json()\n"
                "\t\texcept: return None\n"
                "\tdef userlists(self, url): pass\n",
                encoding="utf-8",
            )
            add_tmdb_request_diagnostics(addon_root, ADDONS[0])
            source = tmdb.read_text(encoding="utf-8")
            compile(source, str(tmdb), "exec")
            self.assertIn("def starlane_provider_request_diagnostic", source)
            self.assertIn("except requests.exceptions.RequestException as error", source)
            self.assertNotIn("verify=False", source)
            self.assertNotIn("url, response.text", source)
            logs = []
            packages = {name: sys.modules.get(name) for name in ("resources", "resources.lib", "resources.lib.modules", "resources.lib.modules.log_utils", "requests", "urllib3", "urllib3.util", "urllib3.util.retry")}
            log_utils = types.ModuleType("resources.lib.modules.log_utils")
            log_utils.LOGINFO = 1
            log_utils.LOGWARNING = 2
            log_utils.LOGDEBUG = 3
            log_utils.log = lambda message, level: logs.append((message, level))
            log_utils.error = lambda: None
            requests = types.ModuleType("requests")
            class RequestException(Exception): pass
            class Timeout(RequestException): pass
            class SSLError(RequestException): pass
            requests.exceptions = types.SimpleNamespace(RequestException=RequestException, Timeout=Timeout, SSLError=SSLError)
            retry = types.ModuleType("urllib3.util.retry")
            retry.Retry = type("Retry", (), {})
            sys.modules.update({"resources": types.ModuleType("resources"), "resources.lib": types.ModuleType("resources.lib"), "resources.lib.modules": types.ModuleType("resources.lib.modules"), "resources.lib.modules.log_utils": log_utils, "requests": requests, "urllib3": types.ModuleType("urllib3"), "urllib3.util": types.ModuleType("urllib3.util"), "urllib3.util.retry": retry})
            try:
                helper = source.split("\ndef starlane_provider_request_diagnostic", 1)[1]
                helper = "def starlane_provider_request_diagnostic" + helper.split("\nclass TMDb:", 1)[0]
                namespace = {"urlsplit": __import__("urllib.parse", fromlist=["urlsplit"]).urlsplit, "re": __import__("re")}
                exec(helper, namespace)
                diagnostic = namespace["starlane_provider_request_diagnostic"]
                route = "https://api.tmdb.org/3/discover/movie?api_key=secret&body=private"
                for status in (200, 401, 403, 429): diagnostic(route, status=status)
                diagnostic(route, error=TimeoutError("secret"))
                diagnostic(route, error=ValueError("malformed JSON private"))
                diagnostic("https://user:password@api.tmdb.org:443/3/movie/12345?api_key=secret", status=403)
                diagnostic_logs = [item[0] for item in logs]
                logs.clear()

                class Response:
                    def __init__(self, status, payload=None, malformed=False):
                        self.status_code = status
                        self.payload = payload
                        self.malformed = malformed
                        self.headers = {}
                    def json(self):
                        if self.malformed: raise ValueError("private response body")
                        return self.payload
                class Session:
                    def __init__(self):
                        self.next = None
                        self.calls = []
                    def get(self, url, **kwargs):
                        self.calls.append((url, kwargs))
                        if isinstance(self.next, Exception): raise self.next
                        return self.next
                session = Session()
                runtime = {"session": session, "notification": lambda **kwargs: None}
                exec(source, runtime)
                client = runtime["TMDb"]()
                session.next = Response(200, {"items": [1]})
                self.assertEqual({"items": [1]}, client.get_request(route))
                for status in (401, 403, 429):
                    session.next = Response(status)
                    self.assertIsNone(client.get_request(route))
                session.next = requests.exceptions.Timeout("secret")
                self.assertIsNone(client.get_request(route))
                session.next = requests.exceptions.SSLError("certificate")
                calls_before_tls = len(session.calls)
                self.assertIsNone(client.get_request(route))
                self.assertEqual(calls_before_tls + 1, len(session.calls))
                self.assertNotIn("verify", session.calls[-1][1])
                session.next = Response(200, malformed=True)
                self.assertIsNone(client.get_request(route))
            finally:
                for name, module in packages.items():
                    if module is None: sys.modules.pop(name, None)
                    else: sys.modules[name] = module
            self.assertEqual(diagnostic_logs, [
                "Starlane provider request host=api.tmdb.org path=/3/discover/movie status=200",
                "Starlane provider request host=api.tmdb.org path=/3/discover/movie status=401",
                "Starlane provider request host=api.tmdb.org path=/3/discover/movie status=403",
                "Starlane provider request host=api.tmdb.org path=/3/discover/movie status=429",
                "Starlane provider request host=api.tmdb.org path=/3/discover/movie exception=TimeoutError",
                "Starlane provider request host=api.tmdb.org path=/3/discover/movie exception=ValueError",
                "Starlane provider request host=api.tmdb.org:443 path=/3/movie/:id status=403",
            ])
    def test_directory_consumer_preserves_absolute_artwork_uris_at_setart(self):
        with tempfile.TemporaryDirectory() as temp:
            addon_root = Path(temp) / "plugin.video.umbrella"
            tvshows = addon_root / "resources/lib/menus/tvshows.py"
            tvshows.parent.mkdir(parents=True)
            tvshows.write_text(
                "class TVshows:\n"
                "\tdef addDirectory(self, items):\n"
                "\t\taddonThumb = control.addonThumb()\n"
                "\t\tartPath = control.artPath()\n"
                "\t\tfor i in items:\n"
                "\t\t\ttry:\n"
                "\t\t\t\tcontent = i.get('content', '')\n"
                "\t\t\t\tif i['image'].startswith('http'): poster = i['image']\n"
                "\t\t\t\telif artPath: poster = control.joinPath(artPath, i['image'])\n"
                "\t\t\t\telse: poster = addonThumb\n"
                "\t\t\t\tif content == 'genres':\n"
                "\t\t\t\t\ticon = control.joinPath(control.genreIconPath(), i['icon']) or 'DefaultFolder.png'\n"
                "\t\t\t\t\tposter = control.joinPath(control.genrePosterPath(), i['image']) or addonThumb\n"
                "\t\t\t\telse:\n"
                "\t\t\t\t\ticon = i['icon']\n"
                "\t\t\t\t\tif icon.startswith('http'): pass\n"
                "\t\t\t\t\telif not icon.startswith('Default'): icon = control.joinPath(artPath, icon)\n"
                "\t\t\t\titem = control.item()\n"
                "\t\t\t\titem.setArt({'icon': icon, 'poster': poster, 'thumb': icon})\n"
                "\t\t\texcept: pass\n",
                encoding="utf-8",
            )
            preserve_absolute_directory_artwork(addon_root, ADDONS[0])
            captured = []

            class Item:
                def setArt(self, art):
                    captured.append(art)

            class Control:
                @staticmethod
                def addonThumb(): return "thumb.png"
                @staticmethod
                def artPath(): return "special://home/addons/plugin.video.umbrella/resources/artwork/starlane movies/"
                @staticmethod
                def joinPath(base, name): return base + name
                @staticmethod
                def genreIconPath(): return "genre-icons/"
                @staticmethod
                def genrePosterPath(): return "genre-posters/"
                @staticmethod
                def item(): return Item()

            namespace = {"control": Control}
            exec(tvshows.read_text(encoding="utf-8"), namespace)
            namespace["TVshows"]().addDirectory([
                {"image": "resource://resource.images.studios.coloured/BBC One.png", "icon": "special://home/icon.png"},
                {"image": "https://example.test/poster.png", "icon": "http://example.test/icon.png"},
                {"image": "bare.png", "icon": "bare-icon.png"},
            ])
            self.assertEqual("resource://resource.images.studios.coloured/BBC One.png", captured[0]["poster"])
            self.assertEqual("special://home/icon.png", captured[0]["icon"])
            self.assertEqual("https://example.test/poster.png", captured[1]["poster"])
            self.assertEqual("http://example.test/icon.png", captured[1]["icon"])
            self.assertTrue(captured[2]["poster"].endswith("/bare.png"))
            self.assertTrue(captured[2]["icon"].endswith("/bare-icon.png"))
    def test_provider_artwork_is_checked_in_release_input(self):
        for name in ("icon.png", "fanart.jpg", "banner.png", "circle.png"):
            artwork = CANONICAL_PROVIDER_ARTWORK / name
            self.assertTrue(artwork.is_file())
            self.assertGreater(artwork.stat().st_size, 100)

    def test_package_is_cross_platform_and_uses_stored_entries(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            outputs = []
            for host, newline in (("windows", b"\r\n"), ("linux", b"\n")):
                addon = root / host / "plugin.video.umbrella"
                addon.mkdir(parents=True)
                addon.joinpath("addon.xml").write_bytes(
                    b'<addon id="plugin.video.umbrella" version="6.7.81.3" />' + newline
                )
                addon.joinpath("service.py").write_bytes(b"first" + newline + b"second" + newline)
                addon.joinpath("Z-last-on-Windows.py").write_bytes(b"same" + newline)
                addon.joinpath("a-first-on-Windows.py").write_bytes(b"same" + newline)
                addon.joinpath("icon.png").write_bytes(b"binary\r\nbytes")
                output = root / f"{host}-output"
                output.mkdir()
                outputs.append(package(addon, output))

            self.assertEqual(outputs[0].read_bytes(), outputs[1].read_bytes())
            with zipfile.ZipFile(outputs[0]) as archive:
                self.assertTrue(all(info.create_system == 3 for info in archive.infolist()))
                self.assertTrue(all(info.compress_type == zipfile.ZIP_STORED for info in archive.infolist()))
                self.assertEqual(
                    archive.read("plugin.video.umbrella/service.py"),
                    b"first\nsecond\n",
                )
                self.assertEqual(
                    archive.read("plugin.video.umbrella/icon.png"),
                    b"binary\r\nbytes",
                )
                self.assertLess(
                    archive.namelist().index("plugin.video.umbrella/Z-last-on-Windows.py"),
                    archive.namelist().index("plugin.video.umbrella/a-first-on-Windows.py"),
                )

    def test_discovery_previews_are_complete_ordered_and_keep_full_lists(self):
        with tempfile.TemporaryDirectory() as temp:
            addon_root = Path(temp) / "plugin.video.umbrella"
            tmdb = addon_root / "resources/lib/indexers/tmdb.py"
            tmdb.parent.mkdir(parents=True)
            tmdb.write_text(
                "\tdef get_networks(self):\n\t\treturn [\n"
                "\t\t\t('A&E', '129', 'a.png'),\n"
                "\t\t\t('ABC (US)', '2', 'abc.png'),\n"
                "\t\t\t('CBS', '16', 'cbs.png'),\n"
                "\t\t\t('NBC', '6', 'nbc.png'),\n"
                "\t\t\t('FOX', '19', 'fox.png'),\n"
                "\t\t\t('BBC One', '4', 'bbc.png'),\n"
                "\t\t\t('ITV', '9', 'itv.png'),\n"
                "\t\t\t('Channel 4', '26', 'c4.png'),\n"
                "\t\t\t('AMC', '174', 'amc.png'),\n"
                "\t\t\t('HBO', '49', 'hbo.png'),\n"
                "\t\t\t('Discovery Channel', '64', 'discovery.png'),\n"
                "\t\t\t('FX', '88', 'fx.png'),\n"
                "\t\t\t('Comedy Central', '47', 'comedy.png'),\n"
                "\t\t\t('Cartoon Network', '56', 'cartoon.png'),\n"
                "\t\t\t('YouTube Premium', '1436', "
                "'https://i.postimg.cc/vHtqdhyt/youtube-premium.png')]\n\n"
                "\tdef get_originals(self):\n\t\treturn [\n"
                "\t\t\t('Amazon', '1024', 'amazon.png'),\n"
                "\t\t\t('Hulu', '453', 'hulu.png'),\n"
                "\t\t\t('Netflix', '213', 'netflix.png')]\n\n"
                "\tdef actorSearch(self, url):\n\t\tpass\n",
                encoding="utf-8",
            )
            rewrite_discovery_previews(addon_root, ADDONS[0])
            updated = tmdb.read_text(encoding="utf-8")
            preferred = updated.split("preferred = ", 1)[1].split("\n", 1)[0]
            self.assertLess(preferred.index("'ABC (US)'"), preferred.index("'CBS'"))
            for provider in (
                "Netflix", "Amazon", "Apple TV+", "Disney+", "Max",
                "Hulu", "Paramount+", "Peacock",
            ):
                self.assertIn(f"('{provider}',", updated)
            self.assertIn("item for item in networks if item[0] not in preferred", updated)

    def _provider_service_fixture(self, addon_root: Path, *, account_sync: bool) -> Path:
        """Write the upstream service.py landmarks the overlay expects to find."""
        service = addon_root / "service.py"
        addon_root.mkdir(parents=True, exist_ok=True)
        body = (
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
            "\t\tif control.setting('general.checkAddonUpdates') == 'true':\n"
            "\t\t\tAddonCheckUpdate().run()\n"
            "def main():\n\twhile not control.monitor.abortRequested():\n"
        )
        if account_sync:
            body += "\t\tSyncMyAccounts().run()\n\t\tPremAccntNotification().run()\n"
        else:
            body += "\t\tSyncMyAccounts().run()\n\t\tsomethingElse().run()\n"
        service.write_text(body, encoding="utf-8")
        return service

    def test_provider_readiness_injection_is_guarded(self):
        with tempfile.TemporaryDirectory() as temp:
            addon_root = Path(temp) / "plugin.video.umbrella"
            service = self._provider_service_fixture(addon_root, account_sync=True)
            rewrite_user_facing_python(addon_root, ADDONS[0])
            updated = service.read_text(encoding="utf-8")
            self.assertIn("window.clearProperty('starlane.umbrella.ready')", updated)
            self.assertIn("window.setProperty('starlane.umbrella.ready', 'true')", updated)

    def test_missing_readiness_landmark_fails_the_build(self):
        with tempfile.TemporaryDirectory() as temp:
            addon_root = Path(temp) / "plugin.video.umbrella"
            self._provider_service_fixture(addon_root, account_sync=False)
            with self.assertRaisesRegex(ValueError, "account sync sequence"):
                rewrite_user_facing_python(addon_root, ADDONS[0])

    def _directory_logo_fixture(self, addon_root: Path, entries: int) -> Path:
        """Write a pinned network directory that mirrors upstream's host split."""
        tmdb = addon_root / "resources/lib/indexers/tmdb.py"
        tmdb.parent.mkdir(parents=True, exist_ok=True)
        rows = [
            "\t\t\t('A&E', '129', 'https://i.imgur.com/xLDfHjH.png'),",
            "\t\t\t('History Channel', '65', 'https://i.imgur.com/abc.png'),",
            "\t\t\t('TruTV', '364', 'https://i.postimg.cc/xyz/trutv.png'),",
        ]
        rows += [
            "\t\t\t('Filler %d', '%d', 'https://i.imgur.com/f%d.png')," % (index, index, index)
            for index in range(entries - len(rows))
        ]
        tmdb.write_text(
            "\tdef get_networks(self):\n\t\treturn [\n" + "\n".join(rows) + "]\n",
            encoding="utf-8",
        )
        return tmdb

    def test_directory_logos_resolve_locally_without_third_party_hosts(self):
        with tempfile.TemporaryDirectory() as temp:
            addon_root = Path(temp) / "plugin.video.umbrella"
            tmdb = self._directory_logo_fixture(addon_root, DIRECTORY_LOGO_MINIMUM)
            localise_directory_logo_artwork(addon_root, ADDONS[0])
            updated = tmdb.read_text(encoding="utf-8")
            for host in DIRECTORY_LOGO_HOSTS:
                self.assertNotIn(host, updated)
            self.assertNotIn("http", updated)
            # An exact bundle name, an aliased name, and a name with no bundled
            # logo all resolve to the locked local resource add-on.
            self.assertIn(
                "('A&E', '129', 'resource://%s/A&E.png')" % DIRECTORY_LOGO_RESOURCE, updated
            )
            self.assertIn(
                "('History Channel', '65', 'resource://%s/History.png')"
                % DIRECTORY_LOGO_RESOURCE,
                updated,
            )
            self.assertIn(
                "('TruTV', '364', 'resource://%s/TruTV.png')" % DIRECTORY_LOGO_RESOURCE,
                updated,
            )

    def test_directory_logo_localisation_rejects_upstream_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            addon_root = Path(temp) / "plugin.video.umbrella"
            self._directory_logo_fixture(addon_root, DIRECTORY_LOGO_MINIMUM - 1)
            with self.assertRaisesRegex(ValueError, "pinned directory logos"):
                localise_directory_logo_artwork(addon_root, ADDONS[0])

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
                    settings = addon_root / "resources/settings.xml"
                    settings.parent.mkdir(parents=True, exist_ok=True)
                    settings.write_text(
                        '<settings><setting id="skinpackicons" type="string">'
                        '<default>Umbrella</default></setting></settings>',
                        encoding="utf-8",
                    )
                    artwork = addon_root / "resources/artwork/umbrella"
                    (artwork / "genre_media/icons").mkdir(parents=True)
                    (artwork / "genre_media/posters").mkdir(parents=True)
                    Image.new("RGB", (40, 40), "red").save(artwork / "icon.png")
                    Image.new("RGB", (160, 90), "red").save(artwork / "fanart.jpg")
                    Image.new("RGB", (120, 30), "red").save(artwork / "banner.png")
                    Image.new("RGB", (32, 32), "blue").save(artwork / "genres.png")
                    Image.new("RGB", (32, 32), "green").save(
                        artwork / "genre_media/icons/action.png"
                    )
                    Image.new("RGB", (60, 90), "yellow").save(
                        artwork / "genre_media/posters/action.jpg"
                    )
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
                    old_theme = addon_root / "resources/artwork/umbrella"
                    theme = addon_root / "resources/artwork/starlane movies"
                    self.assertFalse(old_theme.exists())
                    self.assertTrue(theme.is_dir())
                    self.assertIn(
                        "<default>Starlane Movies</default>",
                        (addon_root / "resources/settings.xml").read_text(encoding="utf-8"),
                    )
                    self.assertEqual(
                        Image.open(theme / "genres.png").getpixel((0, 0)),
                        (0, 0, 255),
                    )
                    self.assertEqual(
                        Image.open(theme / "genre_media/icons/action.png").getpixel((0, 0)),
                        (0, 128, 0),
                    )
                    for global_name in ("icon.png", "fanart.jpg", "banner.png"):
                        self.assertNotEqual(
                            Image.open(theme / global_name).getpixel((0, 0)),
                            (255, 0, 0),
                        )
                    inventory = json.loads(
                        (theme / "ARTWORK_INVENTORY.json").read_text(encoding="utf-8")
                    )
                    self.assertEqual(inventory["theme"], "starlane movies")
                    self.assertEqual(
                        set(inventory["functional_artwork_sha256"]),
                        {
                            "genres.png",
                            "genre_media/icons/action.png",
                            "genre_media/posters/action.jpg",
                        },
                    )
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
            artwork = source_root / "resources/artwork/umbrella"
            artwork.mkdir(parents=True)
            Image.new("RGB", (32, 32), "red").save(artwork / "icon.png")
            Image.new("RGB", (64, 36), "red").save(artwork / "fanart.jpg")
            Image.new("RGB", (48, 16), "red").save(artwork / "banner.png")
            Image.new("RGB", (16, 16), "blue").save(artwork / "genres.png")
            (source_root / "addon.xml").write_text(
                '<addon id="plugin.video.umbrella" name="Umbrella" '
                'provider-name="Umbrella" version="6.7.81">'
                '<extension point="xbmc.addon.metadata"><summary>Umbrella</summary>'
                '<description>Umbrella</description><assets /></extension></addon>',
                encoding="utf-8",
            )
            archive_path = root / "upstream.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                for path in source_root.rglob("*"):
                    if path.is_file():
                        archive.write(path, path.relative_to(source_root.parent).as_posix())
            digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
            first = build_from_archive(archive_path, digest, root / "first")[0]
            second = build_from_archive(archive_path, digest, root / "second")[0]
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with self.assertRaisesRegex(ValueError, "expected SHA-256"):
                build_from_archive(archive_path, "0" * 64, root / "bad")


if __name__ == "__main__":
    unittest.main()

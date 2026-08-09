import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import time
import types
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ADDON_ROOT = REPOSITORY_ROOT / "kodi" / "repository.kodisetup"


class KodiBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.commands = []
        self.installed = set()
        self.addon_versions = {None: "1.1.14"}
        self.addons_path = None
        self.profile_path = None
        self.platform_android = True
        self.dialog_answers = []
        self.dialog_calls = []
        self.settings = {}
        self.addon_settings = {}
        self.skin = "skin.estuary"
        self.window_properties = {"starlane.umbrella.ready": "true"}
        self.addon_enable_events = []

        xbmc = types.ModuleType("xbmc")
        xbmc.LOGINFO = 1
        xbmc.LOGWARNING = 2
        xbmc.LOGERROR = 3
        xbmc.log = lambda *_args, **_kwargs: None

        def json_rpc(request_text):
            request = json.loads(request_text)
            method = request["method"]
            if method == "Settings.GetSettingValue":
                return json.dumps({"result": {"value": self.skin}})
            if method == "Settings.SetSettingValue":
                self.skin = request["params"]["value"]
                return json.dumps({"result": True})
            if method == "Addons.SetAddonEnabled":
                addon_id = request["params"]["addonid"]
                self.addon_enable_events.append(
                    (addon_id, request["params"]["enabled"])
                )
                if request["params"]["enabled"]:
                    # Kodi starts a service add-on in response to an enable
                    # event, so re-enabling an already-enabled package starts
                    # nothing. Only a real transition announces readiness.
                    transitioned = addon_id not in self.installed
                    self.installed.add(addon_id)
                    if addon_id == "plugin.video.umbrella" and transitioned:
                        self.window_properties["starlane.umbrella.ready"] = "true"
                else:
                    self.installed.discard(addon_id)
                return json.dumps({"result": "OK"})
            if method == "Addons.GetAddonDetails":
                addon_id = request["params"]["addonid"]
                version = self.addon_versions.get(addon_id, "")
                if version:
                    return json.dumps(
                        {
                            "result": {
                                "addon": {
                                    "addonid": addon_id,
                                    "version": version,
                                    "enabled": addon_id in self.installed,
                                }
                            }
                        }
                    )
                return json.dumps({"error": {"message": "Unknown addon"}})
            if method == "Files.GetDirectory":
                return json.dumps({"result": {"files": [{}] * 20}})
            return json.dumps({"error": {"message": "unexpected method"}})

        xbmc.executeJSONRPC = json_rpc
        xbmc.executebuiltin = lambda command, wait=False: self.commands.append(
            (command, wait)
        )

        def get_condition(condition):
            if condition == "System.Platform.Android":
                return self.platform_android
            if condition.startswith("System.HasAddon("):
                return condition[len("System.HasAddon(") : -1] in self.installed
            return False

        xbmc.getCondVisibility = get_condition

        class Monitor:
            def waitForAbort(self, _seconds):
                return False

        xbmc.Monitor = Monitor
        owner = self

        xbmcaddon = types.ModuleType("xbmcaddon")

        class Addon:
            def __init__(self, addon_id=None):
                self.addon_id = addon_id

            def getAddonInfo(self, key):
                if key == "path" and self.addon_id is None:
                    return os.fspath(ADDON_ROOT)
                if key == "version":
                    return owner.addon_versions.get(self.addon_id, "")
                return ""

            def getSettingString(self, setting_id):
                settings = owner.settings if self.addon_id is None else owner.addon_settings.setdefault(self.addon_id, {})
                return settings.get(setting_id, "")

            def setSettingString(self, setting_id, value):
                settings = owner.settings if self.addon_id is None else owner.addon_settings.setdefault(self.addon_id, {})
                settings[setting_id] = value

            def getSetting(self, setting_id):
                return self.getSettingString(setting_id)

            def setSetting(self, setting_id, value):
                self.setSettingString(setting_id, value)

            def getSettingBool(self, setting_id):
                settings = owner.settings if self.addon_id is None else owner.addon_settings.setdefault(self.addon_id, {})
                return settings.get(setting_id, False)

            def setSettingBool(self, setting_id, value):
                settings = owner.settings if self.addon_id is None else owner.addon_settings.setdefault(self.addon_id, {})
                settings[setting_id] = value

            def setSettingInt(self, setting_id, value):
                settings = owner.settings if self.addon_id is None else owner.addon_settings.setdefault(self.addon_id, {})
                settings[setting_id] = value

        xbmcaddon.Addon = Addon

        xbmcgui = types.ModuleType("xbmcgui")

        class Dialog:
            def yesno(self, heading, message, **kwargs):
                owner.dialog_calls.append((heading, message, kwargs))
                return owner.dialog_answers.pop(0) if owner.dialog_answers else False

        class DialogProgressBG:
            def create(self, *_args):
                return None

            def update(self, *_args):
                return None

            def close(self):
                return None

        xbmcgui.Dialog = Dialog
        xbmcgui.DialogProgressBG = DialogProgressBG

        class Window:
            def __init__(self, _window_id):
                pass

            def getProperty(self, key):
                return owner.window_properties.get(key, "")

            def clearProperty(self, key):
                owner.window_properties.pop(key, None)

            def setProperty(self, key, value):
                owner.window_properties[key] = value

        xbmcgui.Window = Window

        xbmcvfs = types.ModuleType("xbmcvfs")

        def translate_path(path):
            if path == "special://home/addons" and self.addons_path:
                return self.addons_path
            if path == self.service.REAL_DEBRID_HANDOFF and self.profile_path:
                return self.profile_path
            return path

        xbmcvfs.translatePath = translate_path

        self.previous_modules = {
            name: sys.modules.get(name)
            for name in ("xbmc", "xbmcaddon", "xbmcgui", "xbmcvfs")
        }
        sys.modules.update(
            {
                "xbmc": xbmc,
                "xbmcaddon": xbmcaddon,
                "xbmcgui": xbmcgui,
                "xbmcvfs": xbmcvfs,
            }
        )

        if os.fspath(ADDON_ROOT) not in sys.path:
            sys.path.insert(0, os.fspath(ADDON_ROOT))
        spec = importlib.util.spec_from_file_location(
            "test_bootstrap_service", ADDON_ROOT / "service.py"
        )
        self.service = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.service)

    def tearDown(self):
        for name, module in self.previous_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    def manifest(self):
        return {
            "schemaVersion": 1,
            "configVersion": "2026.07.34",
            "stage": "test",
            "bootstrap": {
                "url": "https://github.com/example/repository.kodisetup.zip",
                "sha256": "f" * 64,
            },
            "repositories": [],
            "addons": [
                {
                    "id": "script.module.cocoscrapers",
                    "name": "CocoScrapers Module",
                    "enabled": True,
                    "required": True,
                    "settings": {},
                    "authAdapter": None,
                },
                {
                    "id": "plugin.video.umbrella",
                    "name": "Starlane Movies: On Demand",
                    "enabled": True,
                    "required": True,
                    "settings": {
                        "provider.external.enabled": True,
                        "external_provider.name": "cocoscrapers",
                        "external_provider.module": "script.module.cocoscrapers",
                    },
                    "authAdapter": "real-debrid-device-v1",
                },
            ],
            "skin": {"addonId": "skin.starlane.movies"},
        }

    def test_bootstrap_has_no_interactive_kodi_install_or_enable_commands(self):
        source = (ADDON_ROOT / "service.py").read_text(encoding="utf-8")
        self.assertNotIn("InstallAddon(", source)
        self.assertNotIn("EnableAddon(", source)
        self.assertNotIn("InstallFromZip", source)
        self.assertNotIn("sqlite", source.lower())
        self.assertNotIn("executeJSONRPC(sys.", source)
        self.assertNotIn("executebuiltin(sys.", source)

    def test_real_debrid_handoff_imports_only_umbrella_settings_and_deletes_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            handoff = Path(temporary) / "real-debrid-handoff.json"
            self.profile_path = os.fspath(handoff)
            self.installed.add("plugin.video.umbrella")
            handoff.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "addonId": "plugin.video.umbrella",
                        "accessToken": "access-value",
                        "refreshToken": "refresh-value",
                        "clientId": "client-id",
                        "clientSecret": "client-secret",
                        "username": "owner",
                    }
                ),
                encoding="utf-8",
            )

            self.assertTrue(self.service.consume_real_debrid_handoff())
            self.assertFalse(handoff.exists())
            self.assertEqual(
                {
                    "realdebrid.enable": "true",
                    "realdebridtoken": "access-value",
                    "realdebridrefresh": "refresh-value",
                    "realdebrid.clientid": "client-id",
                    "realdebridsecret": "client-secret",
                    "realdebridusername": "owner",
                },
                self.addon_settings["plugin.video.umbrella"],
            )
            self.assertEqual(
                "true", self.window_properties["umbrella.updateSettings"]
            )

    def test_real_debrid_handoff_rejects_extra_fields_without_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            handoff = Path(temporary) / "real-debrid-handoff.json"
            self.profile_path = os.fspath(handoff)
            self.installed.add("plugin.video.umbrella")
            handoff.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "addonId": "plugin.video.umbrella",
                        "accessToken": "access-value",
                        "refreshToken": "refresh-value",
                        "clientId": "client-id",
                        "clientSecret": "client-secret",
                        "username": "owner",
                        "unexpected": "rejected",
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "schema is invalid"):
                self.service.consume_real_debrid_handoff()
            self.assertTrue(handoff.exists())
            self.assertNotIn("plugin.video.umbrella", self.addon_settings)

    def test_package_lock_covers_manifest_and_private_skin_requirements(self):
        packages, lock_digest = self.service.load_package_lock_with_digest()
        self.service.validate_lock_for_manifest(packages, self.manifest())
        self.assertEqual(
            hashlib.sha256(
                (ADDON_ROOT / "resources" / "package-lock.json").read_bytes()
            ).hexdigest(),
            lock_digest,
        )
        managed = {
            package["id"]: package["url"]
            for package in packages
            if package["id"] in {"skin.starlane.movies", "plugin.video.umbrella"}
        }
        self.assertEqual({"skin.starlane.movies", "plugin.video.umbrella"}, set(managed))
        for url in managed.values():
            self.assertTrue(url.startswith("https://github.com/rjclark99/starlanemeridian/releases/download/"))
            self.assertNotIn("/latest/", url)

        ids = [item["id"] for item in packages]
        self.assertEqual(38, len(ids))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("plugin.video.umbrella", ids)
        self.assertIn("script.module.cocoscrapers", ids)
        self.assertIn("skin.starlane.movies", ids)

    def test_prerequisite_allowlist_matches_private_skin_requires(self):
        root = ElementTree.parse(
            REPOSITORY_ROOT / "kodi" / "skin.starlane.movies" / "addon.xml"
        ).getroot()
        required = tuple(
            item.attrib["addon"]
            for item in root.find("requires")
            if item.attrib["addon"] != "xbmc.gui"
        )
        self.assertEqual(
            required, self.service.SKIN_PREREQUISITES["skin.starlane.movies"]
        )

    def test_locked_package_is_verified_and_extracted_without_kodi_prompt(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            source = root / "package.zip"
            self.addons_path = os.fspath(root / "addons")
            Path(self.addons_path).mkdir()
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr(
                    "plugin.video.example/addon.xml",
                    '<addon id="plugin.video.example" version="1.2.3" />',
                )
            self.service.download = (
                lambda _url, destination, _sha256, _prefixes: shutil.copyfile(
                    source, destination
                )
            )

            self.service.install_locked_package(
                {
                    "id": "plugin.video.example",
                    "version": "1.2.3",
                    "url": "https://github.com/example/package.zip",
                    "sha256": "a" * 64,
                }
            )

            self.assertTrue(
                (Path(self.addons_path) / "plugin.video.example" / "addon.xml").is_file()
            )
            self.assertFalse(
                any(
                    command.startswith(("InstallAddon(", "EnableAddon("))
                    for command, _wait in self.commands
                )
            )

    def test_locked_package_with_exact_installed_version_is_idempotent(self):
        self.installed.add("plugin.video.example")
        self.addon_versions["plugin.video.example"] = "1.2.3"
        self.service.download = lambda *_args: self.fail("package was downloaded again")

        self.service.install_locked_package(
            {
                "id": "plugin.video.example",
                "version": "1.2.3",
                "url": "https://github.com/example/package.zip",
                "sha256": "a" * 64,
            }
        )

    def test_locked_upgrade_stops_old_provider_service_before_replacement(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            source = root / "package.zip"
            self.addons_path = os.fspath(root / "addons")
            target = Path(self.addons_path) / "plugin.video.umbrella"
            target.mkdir(parents=True)
            (target / "addon.xml").write_text(
                '<addon id="plugin.video.umbrella" version="6.7.81" />',
                encoding="utf-8",
            )
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr(
                    "plugin.video.umbrella/addon.xml",
                    '<addon id="plugin.video.umbrella" version="6.7.81.1" />',
                )
            self.installed.add("plugin.video.umbrella")
            self.addon_versions["plugin.video.umbrella"] = "6.7.81"
            self.service.download = (
                lambda _url, destination, _sha256, _prefixes: shutil.copyfile(
                    source, destination
                )
            )

            self.service.install_locked_package(
                {
                    "id": "plugin.video.umbrella",
                    "version": "6.7.81.1",
                    "url": "https://control.starlanemeridian.uk/v1/public/kodi/"
                    "plugin.video.umbrella/plugin.video.umbrella-6.7.81.1.zip",
                    "sha256": "a" * 64,
                }
            )

            self.assertIn(
                ("plugin.video.umbrella", False), self.addon_enable_events
            )
            self.assertNotIn("plugin.video.umbrella", self.installed)
            installed = ElementTree.parse(target / "addon.xml").getroot()
            self.assertEqual("6.7.81.1", installed.attrib["version"])

    def test_registration_wait_requires_every_exact_locked_version(self):
        packages = [
            {"id": "plugin.video.example", "version": "1.2.3"},
            {"id": "script.module.example", "version": "4.5.6"},
        ]
        self.installed.update(item["id"] for item in packages)
        self.addon_versions.update(
            {"plugin.video.example": "1.2.3", "script.module.example": "4.5.6"}
        )
        self.service.wait_for_registered_packages(packages, attempts=1, interval=0)

        self.installed.discard("plugin.video.example")
        self.service.wait_for_registered_packages(packages, attempts=1, interval=0)

        self.addon_versions["plugin.video.example"] = "1.2.2"
        with self.assertRaisesRegex(ValueError, "plugin.video.example=1.2.3"):
            self.service.wait_for_registered_packages(packages, attempts=1, interval=0)

    def test_configuration_writes_settings_before_enabling_provider(self):
        self.installed.add("plugin.video.umbrella")
        events = []
        original = self.service.set_addon_enabled
        self.service.set_addon_enabled = (
            lambda addon_id, enabled: events.append(("enable", addon_id, enabled))
        )
        original_set_bool = sys.modules["xbmcaddon"].Addon.setSettingBool
        sys.modules["xbmcaddon"].Addon.setSettingBool = (
            lambda _addon, key, value: events.append(("setting", key, value))
        )
        try:
            self.service.configure_addon(
                {
                    "id": "plugin.video.umbrella",
                    "enabled": True,
                    "settings": {"general.checkAddonUpdates": False},
                }
            )
        finally:
            self.service.set_addon_enabled = original
            sys.modules["xbmcaddon"].Addon.setSettingBool = original_set_bool
        self.assertEqual(
            [
                ("enable", "plugin.video.umbrella", True),
                ("setting", "general.checkAddonUpdates", False),
            ],
            events,
        )
        self.assertEqual(
            "true", self.window_properties["starlane.umbrella.ready"]
        )

    def test_locked_package_download_failure_names_package(self):
        with tempfile.TemporaryDirectory() as name:
            self.addons_path = os.fspath(Path(name) / "addons")
            self.service.download = lambda *_args: (_ for _ in ()).throw(
                ValueError("download hash mismatch")
            )

            with self.assertRaisesRegex(
                ValueError, "plugin.video.example: download hash mismatch"
            ):
                self.service.install_locked_package(
                    {
                        "id": "plugin.video.example",
                        "version": "1.2.3",
                        "url": "https://example.test/plugin.video.example.zip",
                        "sha256": "0" * 64,
                    }
                )
    def test_skin_activation_generates_shortcuts_before_reload(self):
        current = {"skin": "skin.estuary"}

        def setting():
            return current["skin"]

        def activate(value):
            current["skin"] = value

        with tempfile.TemporaryDirectory() as temporary:
            self.addons_path = temporary
            generated = (
                Path(temporary)
                / "skin.starlane.movies"
                / "xml"
                / "script-skinshortcuts-includes.xml"
            )
            generated.parent.mkdir(parents=True)
            generated.write_text(
                """
                <includes>
                  <include name="skinshortcuts-mainmenu" />
                  <include name="skinshortcuts-submenu" />
                  <include name="skinshortcuts-group-powermenu" />
                </includes>
                """,
                encoding="utf-8",
            )
            self.service.skin_setting = setting
            self.service.set_skin = activate
            self.service.activate_skin_and_generate_shortcuts(
                "skin.starlane.movies"
            )
            self.assertEqual(
                [
                    (
                        "RunScript(script.skinshortcuts,type=buildxml&mainmenuID=900&group=mainmenu|powermenu)",
                        True,
                    ),
                    ("ReloadSkin()", True),
                ],
                self.commands,
            )

    def test_skin_activation_rejects_incomplete_generated_shortcuts(self):
        with tempfile.TemporaryDirectory() as temporary:
            self.addons_path = temporary
            generated = (
                Path(temporary)
                / "skin.starlane.movies"
                / "xml"
                / "script-skinshortcuts-includes.xml"
            )
            generated.parent.mkdir(parents=True)
            generated.write_text("<includes />", encoding="utf-8")
            self.service.skin_setting = lambda: "skin.starlane.movies"
            self.service.set_skin = lambda _value: None
            with self.assertRaisesRegex(
                ValueError, "did not generate the required Home menu"
            ):
                self.service.wait_for_generated_skin_shortcuts(
                    "skin.starlane.movies", attempts=1, interval=0
                )

    def test_active_package_skin_is_parked_before_provider_upgrade(self):
        self.skin = "skin.starlane.movies"
        self.service.park_active_package_skin("skin.starlane.movies")
        self.assertEqual("skin.estuary", self.skin)

        self.service.park_active_package_skin("skin.starlane.movies")
        self.assertEqual("skin.estuary", self.skin)

    def test_skin_parking_is_required_only_for_provider_replacement(self):
        package = {"id": "plugin.video.umbrella", "version": "6.7.81.2"}
        self.addon_versions["plugin.video.umbrella"] = "6.7.81.1"
        self.assertTrue(self.service.provider_replacement_required([package]))
        self.assertTrue(
            self.service.prepare_provider_replacement(
                [package], "skin.starlane.movies"
            )
        )
        self.assertNotIn("starlane.umbrella.ready", self.window_properties)
        self.addon_versions["plugin.video.umbrella"] = "6.7.81.2"
        self.assertFalse(self.service.provider_replacement_required([package]))
        self.window_properties["starlane.umbrella.ready"] = "true"
        self.assertFalse(
            self.service.prepare_provider_replacement(
                [package], "skin.starlane.movies"
            )
        )
        self.assertEqual(
            "true", self.window_properties["starlane.umbrella.ready"]
        )

    def test_provider_readiness_is_bounded_and_required(self):
        self.service.wait_for_provider_ready(
            "plugin.video.umbrella", attempts=1, interval=0
        )
        self.window_properties.clear()
        with self.assertRaisesRegex(ValueError, "did not finish initialising"):
            self.service.wait_for_provider_ready(
                "plugin.video.umbrella", attempts=1, interval=0
            )
        self.service.wait_for_provider_ready(
            "script.module.cocoscrapers", attempts=1, interval=0
        )

    def test_provider_directory_probe_requires_both_canonical_routes_once(self):
        requests = []
        original = self.service.provider_directory_ready
        self.service.provider_directory_ready = requests.append
        try:
            self.service.wait_for_provider_directories("plugin.video.umbrella")
        finally:
            self.service.provider_directory_ready = original
        self.assertEqual(list(self.service.PROVIDER_DIRECTORY_ROUTES), requests)

    def test_provider_request_diagnostics_redact_queries_bodies_and_keys(self):
        messages = []
        self.service.log = lambda message, *_args: messages.append(message)
        route = "https://user:password@provider.example:443/path?api_key=secret&body=private"
        for status in (200, 401, 403, 429):
            self.service.log_provider_directory_diagnostic(route, status=status)
        self.service.log_provider_directory_diagnostic(route, error=TimeoutError("secret"))
        self.service.log_provider_directory_diagnostic(route, error=ValueError("body secret"))
        self.assertEqual(
            [
                "Provider request host=provider.example:443 path=/path status=200",
                "Provider request host=provider.example:443 path=/path status=401",
                "Provider request host=provider.example:443 path=/path status=403",
                "Provider request host=provider.example:443 path=/path status=429",
                "Provider request host=provider.example:443 path=/path exception=TimeoutError",
                "Provider request host=provider.example:443 path=/path exception=ValueError",
            ],
            messages,
        )

    def test_provider_directory_probe_rejects_malformed_response_without_logging_data(self):
        messages = []
        self.service.log = lambda message, *_args: messages.append(message)
        original = self.service.xbmc.executeJSONRPC
        self.service.xbmc.executeJSONRPC = lambda _request: "not-json"
        try:
            with self.assertRaises(ValueError):
                self.service.provider_directory_ready(self.service.PROVIDER_DIRECTORY_ROUTES[0])
        finally:
            self.service.xbmc.executeJSONRPC = original
        self.assertEqual(
            "Provider request host=plugin.video.umbrella path=/ exception=JSONDecodeError",
            messages[-1],
        )

    def test_provider_directory_probe_times_out_without_blocking_bootstrap(self):
        original = self.service.xbmc.executeJSONRPC
        self.service.xbmc.executeJSONRPC = lambda _request: time.sleep(0.1)
        started = time.monotonic()
        try:
            with self.assertRaisesRegex(ValueError, "timed out"):
                request = {"jsonrpc": "2.0", "id": 1, "method": "Files.GetDirectory"}
                self.service.execute_provider_directory_request(request, timeout=0.01)
        finally:
            self.service.xbmc.executeJSONRPC = original
        self.assertLess(time.monotonic() - started, 0.08)

    def test_locked_package_rejects_wrong_identity_before_extraction(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            source = root / "package.zip"
            self.addons_path = os.fspath(root / "addons")
            Path(self.addons_path).mkdir()
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr(
                    "plugin.video.wrong/addon.xml",
                    '<addon id="plugin.video.wrong" version="1.2.3" />',
                )
            self.service.download = (
                lambda _url, destination, _sha256, _prefixes: shutil.copyfile(
                    source, destination
                )
            )

            with self.assertRaisesRegex(ValueError, "ZIP root"):
                self.service.install_locked_package(
                    {
                        "id": "plugin.video.example",
                        "version": "1.2.3",
                        "url": "https://github.com/example/package.zip",
                        "sha256": "a" * 64,
                    }
                )

            self.assertFalse((Path(self.addons_path) / "plugin.video.wrong").exists())

    def test_repository_archive_root_can_differ_from_addon_id(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            source = root / "repository.zip"
            self.addons_path = os.fspath(root / "addons")
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr(
                    "repository.umbrellaplug.github.io/addon.xml",
                    '<addon id="repository.umbrella" version="2.2.6" />',
                )
            self.service.download = (
                lambda _url, destination, _sha256, _prefixes: shutil.copyfile(
                    source, destination
                )
            )

            self.service.install_repository(
                {
                    "addonId": "repository.umbrella",
                    "source": {
                        "resolvedUrl": "https://github.com/example/repository.zip"
                    },
                    "sha256": "a" * 64,
                }
            )

            self.assertTrue(
                (
                    root
                    / "addons"
                    / "repository.umbrellaplug.github.io"
                    / "addon.xml"
                ).is_file()
            )
            self.assertIn("repository.umbrella", self.installed)

    def test_installation_authorization_is_canonical_and_scope_bound(self):
        document = self.manifest()
        scope = self.service.canonical_installation_scope(document, "a" * 64)
        self.dialog_answers = [True]

        self.assertTrue(
            self.service.ensure_installation_authorized(
                document, package_count=38, scope_digest=scope
            )
        )
        self.assertEqual(scope, self.settings["authorized_scope"])
        self.assertIn("Starlane Movies: On Demand", self.dialog_calls[0][1])
        self.assertIn("38 hash-locked packages", self.dialog_calls[0][1])
        self.assertEqual("Install all", self.dialog_calls[0][2]["yeslabel"])

        self.dialog_answers = [False]
        self.assertTrue(
            self.service.ensure_installation_authorized(
                document, package_count=38, scope_digest=scope
            )
        )
        self.assertEqual(1, len(self.dialog_calls))

        reordered = json.loads(json.dumps(document, sort_keys=True))
        self.assertEqual(
            scope,
            self.service.canonical_installation_scope(reordered, "a" * 64),
        )

    def test_security_scope_change_clears_old_grant_and_requires_fresh_consent(self):
        document = self.manifest()
        original_scope = self.service.canonical_installation_scope(document, "a" * 64)
        changed = self.manifest()
        changed["addons"][1]["settings"]["provider.external.enabled"] = False
        changed_scope = self.service.canonical_installation_scope(changed, "a" * 64)
        self.assertNotEqual(original_scope, changed_scope)
        self.settings["authorized_scope"] = original_scope
        self.dialog_answers = [False]

        self.assertFalse(
            self.service.ensure_installation_authorized(
                changed, package_count=38, scope_digest=changed_scope
            )
        )
        self.assertEqual(self.service.INTERNAL_UNSET, self.settings["authorized_scope"])

    def test_package_lock_or_bootstrap_version_change_changes_scope(self):
        document = self.manifest()
        original = self.service.canonical_installation_scope(document, "a" * 64)
        self.assertNotEqual(
            original,
            self.service.canonical_installation_scope(document, "b" * 64),
        )
        self.addon_versions[None] = "1.1.15"
        self.assertNotEqual(
            original,
            self.service.canonical_installation_scope(document, "a" * 64),
        )

    def test_declined_installation_is_not_persisted_and_will_prompt_again(self):
        document = self.manifest()
        scope = self.service.canonical_installation_scope(document, "a" * 64)
        self.dialog_answers = [False]
        self.assertFalse(
            self.service.ensure_installation_authorized(
                document, package_count=38, scope_digest=scope
            )
        )
        self.assertNotIn("authorized_scope", self.settings)

    def test_local_revocation_clears_only_future_authorization(self):
        self.settings.update(
            {
                "authorized_scope": "a" * 64,
                "applied_scope": "b" * 64,
                "applied_version": "2026.07.34",
            }
        )
        self.installed.add("plugin.video.umbrella")
        self.dialog_answers = [True]

        self.assertTrue(
            self.service.handle_local_action([self.service.REVOKE_CONSENT_ACTION])
        )

        self.assertEqual(self.service.INTERNAL_UNSET, self.settings["authorized_scope"])
        self.assertEqual("b" * 64, self.settings["applied_scope"])
        self.assertEqual("2026.07.34", self.settings["applied_version"])
        self.assertIn("plugin.video.umbrella", self.installed)

    def test_unknown_local_action_is_rejected_without_mutation(self):
        self.settings["authorized_scope"] = "a" * 64
        self.assertTrue(self.service.handle_local_action(["arbitrary-command"]))
        self.assertEqual("a" * 64, self.settings["authorized_scope"])
        self.assertEqual([], self.commands)

    def test_settings_exposes_only_fixed_local_revoke_action(self):
        root = ElementTree.parse(ADDON_ROOT / "resources" / "settings.xml").getroot()
        revoke = root.find(
            ".//setting[@id='revoke_installation_authorization']"
        )
        self.assertIsNotNone(revoke)
        self.assertEqual("action", revoke.attrib["type"])
        self.assertEqual(
            "RunScript(repository.kodisetup,revoke-consent)",
            revoke.findtext("data"),
        )

    def test_real_debrid_offer_opens_setup_app_only_after_user_accepts(self):
        self.dialog_answers = [True]
        self.service.offer_real_debrid_authorization(self.manifest())
        self.assertIn(
            ("StartAndroidActivity(app.kodisetup.tv)", True), self.commands
        )

    def test_run_stops_before_configuration_when_authorization_is_declined(self):
        document = self.manifest()
        self.settings.update(
            {
                "manifest_url": "https://example.invalid/manifest.json",
                "public_key": "test-key",
                "authorized_scope": "b" * 64,
            }
        )
        self.service.fetch_and_verify = lambda _url, _key: document
        self.service.load_package_lock_with_digest = lambda: (
            [
                {"id": "skin.starlane.movies"},
                {"id": "script.module.cocoscrapers"},
                {"id": "plugin.video.umbrella"},
            ],
            "a" * 64,
        )
        self.service.validate_lock_for_manifest = lambda _packages, _document: None
        configured = []
        self.service.configure_kodi_quality_of_life = lambda: configured.append(True)
        self.dialog_answers = [False]

        self.service.run()

        self.assertEqual([], configured)
        self.assertNotIn("applied_version", self.settings)
        self.assertEqual(self.service.INTERNAL_UNSET, self.settings["authorized_scope"])

    def test_run_applies_locked_package_after_single_authorization(self):
        document = self.manifest()
        document["repositories"] = [
            {
                "id": "repository.cocoscrapers",
                "name": "CocoScrapers Repository",
                "enabled": True,
            },
            {
                "id": "repository.umbrella",
                "name": "Umbrella Repository",
                "enabled": True,
            },
        ]
        self.settings.update(
            {
                "manifest_url": "https://example.invalid/manifest.json",
                "public_key": "test-key",
            }
        )
        self.service.fetch_and_verify = lambda _url, _key: document
        packages = [
            {"id": "script.module.cocoscrapers"},
            {"id": "plugin.video.umbrella"},
            {"id": "skin.starlane.movies"},
        ]
        self.service.load_package_lock_with_digest = lambda: (packages, "a" * 64)
        self.service.validate_lock_for_manifest = lambda _packages, _document: None
        installed_repositories = []
        self.service.install_repository = lambda item: installed_repositories.append(
            item["id"]
        )

        def install_all(items, _progress):
            self.installed.update(item["id"] for item in items)

        self.service.install_locked_packages = install_all
        self.service.configure_kodi_quality_of_life = lambda: None
        self.service.wait_for_generated_skin_shortcuts = lambda _skin_id: None
        self.dialog_answers = [True, False]

        self.service.run()

        self.assertEqual(
            ["repository.cocoscrapers", "repository.umbrella"],
            installed_repositories,
        )
        provider_settings = self.addon_settings["plugin.video.umbrella"]
        self.assertTrue(provider_settings["provider.external.enabled"])
        self.assertEqual("cocoscrapers", provider_settings["external_provider.name"])
        self.assertEqual(
            "script.module.cocoscrapers",
            provider_settings["external_provider.module"],
        )
        self.assertEqual("2026.07.34", self.settings["applied_version"])
        self.assertEqual(
            self.service.canonical_installation_scope(document, "a" * 64),
            self.settings["applied_scope"],
        )
        self.assertEqual(2, len(self.dialog_calls))

    def test_exact_applied_scope_skips_without_prompt_or_mutation(self):
        document = self.manifest()
        packages = [
            {"id": "skin.starlane.movies"},
            {"id": "script.module.cocoscrapers"},
            {"id": "plugin.video.umbrella"},
        ]
        scope = self.service.canonical_installation_scope(document, "a" * 64)
        self.settings.update(
            {
                "manifest_url": "https://example.invalid/manifest.json",
                "public_key": "test-key",
                "applied_version": document["configVersion"],
                "applied_scope": scope,
            }
        )
        self.service.fetch_and_verify = lambda _url, _key: document
        self.service.load_package_lock_with_digest = lambda: (packages, "a" * 64)
        self.service.validate_lock_for_manifest = lambda _packages, _document: None
        configured = []
        self.service.configure_kodi_quality_of_life = lambda: configured.append(True)

        self.service.run()

        self.assertEqual([], configured)
        self.assertEqual([], self.dialog_calls)

    def _install_only_run(self, document, packages):
        """Drive run() with installation stubbed but readiness left realistic."""
        self.settings.update(
            {
                "manifest_url": "https://example.invalid/manifest.json",
                "public_key": "test-key",
            }
        )
        self.service.fetch_and_verify = lambda _url, _key: document
        self.service.load_package_lock_with_digest = lambda: (packages, "a" * 64)
        self.service.validate_lock_for_manifest = lambda _packages, _document: None
        self.service.install_locked_packages = (
            lambda items, _progress: self.installed.update(item["id"] for item in items)
        )
        self.service.configure_kodi_quality_of_life = lambda: None
        self.dialog_answers = [True]

    def test_absent_provider_readiness_defers_instead_of_reporting_failure(self):
        # A launch that installs the provider cannot have started its service,
        # so readiness is legitimately absent and must not become an error.
        document = self.manifest()
        packages = [
            {"id": "script.module.cocoscrapers"},
            {"id": "plugin.video.umbrella"},
            {"id": "skin.starlane.movies"},
        ]
        self._install_only_run(document, packages)
        self.window_properties.clear()
        self.service.wait_for_provider_ready = (
            lambda addon_id, attempts=1, interval=0: (_ for _ in ()).throw(
                ValueError("Starlane on-demand provider did not finish initialising")
            )
            if addon_id == "plugin.video.umbrella"
            else None
        )
        activated = []
        self.service.activate_skin_and_generate_shortcuts = activated.append

        self.service.run()

        self.assertEqual([], activated)
        self.assertNotIn("applied_version", self.settings)
        self.assertEqual("", self.service.internal_setting("applied_scope"))
        self.assertEqual("1", self.service.internal_setting("activation_attempts"))
        self.assertIn(("Quit", False), self.commands)

    def test_unready_canonical_directory_defers_without_repeating_the_probe(self):
        document = self.manifest()
        packages = [
            {"id": "script.module.cocoscrapers"},
            {"id": "plugin.video.umbrella"},
            {"id": "skin.starlane.movies"},
        ]
        self._install_only_run(document, packages)
        self.service.wait_for_provider_ready = lambda _addon_id: (_ for _ in ()).throw(
            self.service.ProviderDirectoryReadinessError("provider directory returned no items")
        )
        restart_calls = []
        self.service.restart_provider_service = lambda addon_id: restart_calls.append(addon_id)
        activated = []
        self.service.activate_skin_and_generate_shortcuts = activated.append

        self.service.run()

        self.assertEqual([], restart_calls)
        self.assertEqual([], activated)
        self.assertEqual("1", self.service.internal_setting("activation_attempts"))
        self.assertIn(("Quit", False), self.commands)

    def test_unready_canonical_directory_stops_after_bounded_restarts(self):
        document = self.manifest()
        packages = [
            {"id": "script.module.cocoscrapers"},
            {"id": "plugin.video.umbrella"},
            {"id": "skin.starlane.movies"},
        ]
        self._install_only_run(document, packages)
        self.service.set_internal_setting(
            "activation_attempts", str(self.service.MAX_ACTIVATION_ATTEMPTS)
        )
        self.service.wait_for_provider_ready = lambda _addon_id: (_ for _ in ()).throw(
            self.service.ProviderDirectoryReadinessError("provider directory returned no items")
        )
        self.service.activate_skin_and_generate_shortcuts = lambda _skin_id: None

        self.service.run()

        self.assertNotIn(("Quit", False), self.commands)
        self.assertTrue(
            any(command.startswith("Notification(Starlane Movies,Setup finished with")
                for command, _wait in self.commands)
        )

    def test_cycling_the_provider_starts_its_service_and_avoids_a_restart(self):
        # An already-enabled package raises no enable event, so its service never
        # starts. Cycling it produces that event and setup finishes in one launch.
        document = self.manifest()
        packages = [
            {"id": "script.module.cocoscrapers"},
            {"id": "plugin.video.umbrella"},
            {"id": "skin.starlane.movies"},
        ]
        self._install_only_run(document, packages)
        self.window_properties.clear()
        # The extracted package is already enabled, so configuring it raises no
        # enable event and its service stays down: the real device situation.
        self.installed.add("plugin.video.umbrella")
        activated = []
        self.service.activate_skin_and_generate_shortcuts = activated.append

        self.service.run()

        self.assertEqual(["skin.starlane.movies"], activated)
        self.assertEqual("2026.07.34", self.settings["applied_version"])
        self.assertIn(("plugin.video.umbrella", False), self.addon_enable_events)
        self.assertNotIn(("Quit", False), self.commands)

    def test_deferred_activation_completes_on_the_next_launch(self):
        document = self.manifest()
        packages = [
            {"id": "script.module.cocoscrapers"},
            {"id": "plugin.video.umbrella"},
            {"id": "skin.starlane.movies"},
        ]
        self._install_only_run(document, packages)
        # Kodi has restarted: the provider's own service is running and has
        # announced readiness before Bootstrap's second run begins.
        self.window_properties["starlane.umbrella.ready"] = "true"
        self.settings["activation_attempts"] = "1"
        activated = []
        self.service.activate_skin_and_generate_shortcuts = activated.append

        self.service.run()

        self.assertEqual(["skin.starlane.movies"], activated)
        self.assertEqual("2026.07.34", self.settings["applied_version"])
        self.assertEqual("", self.service.internal_setting("activation_attempts"))

    def test_deferral_is_bounded_and_finally_reports_a_real_failure(self):
        document = self.manifest()
        packages = [
            {"id": "script.module.cocoscrapers"},
            {"id": "plugin.video.umbrella"},
            {"id": "skin.starlane.movies"},
        ]
        self._install_only_run(document, packages)
        self.window_properties.clear()
        self.settings["activation_attempts"] = "3"
        self.service.wait_for_provider_ready = (
            lambda addon_id, attempts=1, interval=0: (_ for _ in ()).throw(
                ValueError("Starlane on-demand provider did not finish initialising")
            )
            if addon_id == "plugin.video.umbrella"
            else None
        )
        activated = []
        self.service.activate_skin_and_generate_shortcuts = activated.append

        self.service.run()

        self.assertEqual([], activated)
        self.assertNotIn("applied_version", self.settings)
        self.assertNotIn(("Quit", False), self.commands)

    def test_self_healing_retry_does_not_ask_for_consent_again(self):
        # Withdrawing the applied scope must not withdraw consent: recovering
        # from a frozen skin activation has to be silent.
        document = self.manifest()
        packages = [
            {"id": "script.module.cocoscrapers"},
            {"id": "plugin.video.umbrella"},
            {"id": "skin.starlane.movies"},
        ]
        self._install_only_run(document, packages)
        activated = []

        def activate(skin_id):
            activated.append(skin_id)
            self.skin = skin_id

        self.service.activate_skin_and_generate_shortcuts = activate

        self.service.run()
        consent_heading = "Complete Starlane Movies setup"
        consents = [call for call in self.dialog_calls if call[0] == consent_heading]
        self.assertEqual(1, len(consents))
        self.assertEqual(["skin.starlane.movies"], activated)

        # Kodi is killed at its keep-skin dialog, so the change never persisted.
        self.skin = "skin.estuary"
        self.settings["pending_skin"] = "skin.starlane.movies"
        self.settings["previous_skin"] = "skin.estuary"

        self.service.run()

        # The retry re-activates Home without asking for installation consent
        # a second time, because consent is bound to the unchanged scope digest.
        self.assertEqual(
            1, len([call for call in self.dialog_calls if call[0] == consent_heading])
        )
        self.assertEqual(
            ["skin.starlane.movies", "skin.starlane.movies"], activated
        )
        self.assertEqual("2026.07.34", self.settings["applied_version"])

    def test_unconfirmed_skin_withdraws_applied_scope_and_retries(self):
        # Kodi killed at its own keep-skin dialog must not strand the television
        # on Estuary with the configuration still marked as applied.
        self.settings.update(
            {
                "pending_skin": "skin.starlane.movies",
                "previous_skin": "skin.estuary",
                "applied_version": "2026.07.34",
                "applied_scope": "b" * 64,
            }
        )
        self.skin = "skin.estuary"

        self.service.recover_pending_skin()

        self.assertEqual("", self.service.internal_setting("applied_scope"))
        self.assertEqual("1", self.service.internal_setting("activation_attempts"))
        self.assertEqual("", self.service.internal_setting("pending_skin"))
        self.assertEqual("skin.estuary", self.skin)

    def test_confirmed_skin_keeps_applied_scope_and_clears_retries(self):
        self.settings.update(
            {
                "pending_skin": "skin.starlane.movies",
                "previous_skin": "skin.estuary",
                "applied_scope": "b" * 64,
                "activation_attempts": "2",
            }
        )
        self.skin = "skin.starlane.movies"

        self.service.recover_pending_skin()

        self.assertEqual("b" * 64, self.settings["applied_scope"])
        self.assertEqual("", self.service.internal_setting("activation_attempts"))

    def test_repeated_activation_failure_stops_withdrawing_applied_scope(self):
        self.settings.update(
            {
                "pending_skin": "skin.starlane.movies",
                "previous_skin": "skin.estuary",
                "applied_scope": "b" * 64,
                "activation_attempts": "3",
            }
        )
        self.skin = "skin.estuary"

        self.service.recover_pending_skin()

        self.assertEqual("b" * 64, self.settings["applied_scope"])
        self.assertEqual("3", self.settings["activation_attempts"])

    def test_run_does_not_activate_skin_when_provider_never_becomes_ready(self):
        document = self.manifest()
        self.settings.update(
            {
                "manifest_url": "https://example.invalid/manifest.json",
                "public_key": "test-key",
            }
        )
        self.service.fetch_and_verify = lambda _url, _key: document
        packages = [
            {"id": "script.module.cocoscrapers"},
            {"id": "plugin.video.umbrella"},
            {"id": "skin.starlane.movies"},
        ]
        self.service.load_package_lock_with_digest = lambda: (packages, "a" * 64)
        self.service.validate_lock_for_manifest = lambda _packages, _document: None
        self.service.install_locked_packages = (
            lambda items, _progress: self.installed.update(
                item["id"] for item in items
            )
        )
        self.service.configure_kodi_quality_of_life = lambda: None
        self.service.wait_for_provider_ready = (
            lambda addon_id: (_ for _ in ()).throw(ValueError("not ready"))
            if addon_id == "plugin.video.umbrella"
            else None
        )
        activated = []
        self.service.activate_skin_and_generate_shortcuts = activated.append
        self.dialog_answers = [True]

        self.service.run()

        self.assertEqual([], activated)
        self.assertNotIn("applied_version", self.settings)
        self.assertNotIn("applied_scope", self.settings)


if __name__ == "__main__":
    unittest.main()

import importlib.util
import json
import os
import shutil
import sys
import tempfile
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
        self.addon_versions = {}
        self.addons_path = None
        self.platform_android = True
        self.dialog_answers = []
        self.dialog_calls = []
        self.settings = {}
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
                    self.installed.add(addon_id)
                    if addon_id == "plugin.video.umbrella":
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
                return owner.settings.get(setting_id, "")

            def setSettingString(self, setting_id, value):
                owner.settings[setting_id] = value

            def getSettingBool(self, setting_id):
                return owner.settings.get(setting_id, False)

            def setSettingBool(self, setting_id, value):
                owner.settings[setting_id] = value

            def setSettingInt(self, setting_id, value):
                owner.settings[setting_id] = value

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

        xbmcgui.Window = Window

        xbmcvfs = types.ModuleType("xbmcvfs")

        def translate_path(path):
            if path == "special://home/addons" and self.addons_path:
                return self.addons_path
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
            "configVersion": "2026.07.33",
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

    def test_package_lock_covers_manifest_and_private_skin_requirements(self):
        packages = self.service.load_package_lock()
        self.service.validate_lock_for_manifest(packages, self.manifest())

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
        self.assertNotIn("starlane.umbrella.ready", self.window_properties)

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
        self.addon_versions["plugin.video.umbrella"] = "6.7.81.2"
        self.assertFalse(self.service.provider_replacement_required([package]))

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

    def test_initial_installation_requires_one_time_explicit_authorization(self):
        document = self.manifest()
        self.dialog_answers = [True]

        self.assertTrue(
            self.service.ensure_installation_authorized(document, package_count=38)
        )
        self.assertTrue(self.settings["installation_authorized"])
        self.assertIn("Starlane Movies: On Demand", self.dialog_calls[0][1])
        self.assertIn("38 hash-locked packages", self.dialog_calls[0][1])
        self.assertEqual("Install all", self.dialog_calls[0][2]["yeslabel"])

        self.dialog_answers = [False]
        self.assertTrue(
            self.service.ensure_installation_authorized(document, package_count=38)
        )
        self.assertEqual(1, len(self.dialog_calls))

    def test_declined_installation_is_not_persisted_and_will_prompt_again(self):
        self.dialog_answers = [False]
        self.assertFalse(
            self.service.ensure_installation_authorized(
                self.manifest(), package_count=38
            )
        )
        self.assertNotIn("installation_authorized", self.settings)

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
            }
        )
        self.service.fetch_and_verify = lambda _url, _key: document
        self.service.load_package_lock = lambda: [
            {"id": "skin.starlane.movies"},
            {"id": "script.module.cocoscrapers"},
            {"id": "plugin.video.umbrella"},
        ]
        self.service.validate_lock_for_manifest = lambda _packages, _document: None
        configured = []
        self.service.configure_kodi_quality_of_life = lambda: configured.append(True)
        self.dialog_answers = [False]

        self.service.run()

        self.assertEqual([], configured)
        self.assertNotIn("applied_version", self.settings)

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
        self.service.load_package_lock = lambda: packages
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
        self.assertTrue(self.settings["provider.external.enabled"])
        self.assertEqual("cocoscrapers", self.settings["external_provider.name"])
        self.assertEqual(
            "script.module.cocoscrapers",
            self.settings["external_provider.module"],
        )
        self.assertEqual("2026.07.33", self.settings["applied_version"])
        self.assertEqual(2, len(self.dialog_calls))

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
        self.service.load_package_lock = lambda: packages
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


if __name__ == "__main__":
    unittest.main()

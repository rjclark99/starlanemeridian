import hashlib
import json
import os
import platform
import posixpath
import re
import shutil
import stat
import struct
import sys
import tempfile
import urllib.request
import zipfile
from xml.etree import ElementTree

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from resources.lib.manifest import fetch_and_verify, sha256
from resources.lib.kodi_settings import disable_core_splash

ADDON = xbmcaddon.Addon()
LOG_PREFIX = "[Starlane Movies] "
INTERNAL_UNSET = "__unset__"
ADDON_ID = re.compile(r"^[a-z][a-z0-9]*(\.[a-z0-9_-]+)+$")
PACKAGE_VERSION = re.compile(r"^[A-Za-z0-9.+_-]{1,64}$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
PACKAGE_URL_PREFIXES = (
    "https://github.com/",
    "https://mirrors.kodi.tv/addons/omega/",
)
SKIN_PREREQUISITES = {
    "skin.starlane.movies": (
        "script.bingie.helper",
        "script.skinshortcuts",
        "script.skin.helper.service",
        "script.skin.helper.widgets",
        "script.skin.helper.backgrounds",
        "resource.images.skinbackgrounds.titanium",
        "resource.images.skinicons.wide",
        "resource.images.backgroundoverlays.basic",
        "resource.images.studios.coloured",
        "plugin.video.themoviedb.helper",
        "plugin.program.autocompletion",
        "plugin.video.youtube",
    ),
}
SETUP_APP_PACKAGE = "app.kodisetup.tv"
BOOTSTRAP_ADDON_ID = "repository.kodisetup"
CONSENT_SCOPE_VERSION = 1
MAX_ACTIVATION_ATTEMPTS = 3
CONSENT_SCOPE_FIELDS = (
    "schemaVersion",
    "configVersion",
    "stage",
    "bootstrap",
    "repositories",
    "addons",
    "skin",
)
REVOKE_CONSENT_ACTION = "revoke-consent"
REAL_DEBRID_ADDON = "plugin.video.umbrella"
REAL_DEBRID_HANDOFF = "special://profile/addon_data/repository.kodisetup/real-debrid-handoff.json"
REAL_DEBRID_FIELDS = {
    "accessToken": "realdebridtoken",
    "refreshToken": "realdebridrefresh",
    "clientId": "realdebrid.clientid",
    "clientSecret": "realdebridsecret",
    "username": "realdebridusername",
}


def log(message, level=xbmc.LOGINFO):
    xbmc.log(LOG_PREFIX + message, level)


def notify(message):
    xbmc.executebuiltin("Notification(Starlane Movies,%s,5000)" % message.replace(",", " "))


def installation_summary(document, package_count):
    repository_count = sum(1 for item in document["repositories"] if item["enabled"])
    addon_names = [item["name"] for item in document["addons"] if item["enabled"]]
    addon_count = len(addon_names)
    configured = {item["id"] for item in document["addons"]}
    dependency_count = sum(
        1
        for addon_id in SKIN_PREREQUISITES.get(document["skin"]["addonId"], ())
        if addon_id not in configured
    )
    addon_summary = ", ".join(addon_names[:4]) if addon_names else "no configured provider add-ons"
    if addon_count > 4:
        addon_summary += ", and %d more" % (addon_count - 4)
    return (
        "Install the approved Starlane Movies Kodi package? "
        "Verified add-ons: %s. The package also includes the Starlane Movies skin, "
        "%d repositories, %d required skin dependencies, and %d hash-locked packages. "
        "Kodi's Unknown Sources approval remains controlled separately by Kodi."
        % (addon_summary, repository_count, dependency_count, package_count)
    )


def canonical_installation_scope(document, package_lock_sha256):
    if not isinstance(package_lock_sha256, str) or not SHA256.fullmatch(
        package_lock_sha256
    ):
        raise ValueError("package lock digest is invalid")
    bootstrap_version = ADDON.getAddonInfo("version")
    if not isinstance(bootstrap_version, str) or not PACKAGE_VERSION.fullmatch(
        bootstrap_version
    ):
        raise ValueError("Bootstrap version is invalid")
    scope = {
        "scopeVersion": CONSENT_SCOPE_VERSION,
        "bootstrap": {
            "id": BOOTSTRAP_ADDON_ID,
            "version": bootstrap_version,
        },
        "manifest": {field: document.get(field) for field in CONSENT_SCOPE_FIELDS},
        "packageLockSha256": package_lock_sha256,
    }
    canonical = json.dumps(
        scope, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def ensure_installation_authorized(document, package_count, scope_digest):
    authorized_scope = internal_setting("authorized_scope")
    if authorized_scope == scope_digest:
        return True
    if authorized_scope:
        set_internal_setting("authorized_scope", "")
    approved = xbmcgui.Dialog().yesno(
        "Complete Starlane Movies setup",
        installation_summary(document, package_count),
        nolabel="Cancel",
        yeslabel="Install all",
    )
    if not approved:
        log("Initial package installation was not authorized")
        notify("Setup was not authorized; Kodi will ask again next launch")
        return False
    set_internal_setting("authorized_scope", scope_digest)
    log("Verified package scope authorized")
    return True


def revoke_installation_authorization():
    if not internal_setting("authorized_scope"):
        notify("No future package installation is currently authorized")
        return False
    approved = xbmcgui.Dialog().yesno(
        "Revoke package authorization",
        "Revoke authorization for future Starlane Movies package changes? "
        "Already installed add-ons, settings, and skins will not be removed.",
        nolabel="Keep authorization",
        yeslabel="Revoke",
    )
    if not approved:
        return False
    set_internal_setting("authorized_scope", "")
    log("Verified package scope authorization revoked")
    notify("Future package changes require fresh local authorization")
    return True


def handle_local_action(arguments):
    if not arguments:
        return False
    if arguments == [REVOKE_CONSENT_ACTION]:
        revoke_installation_authorization()
    else:
        log("Unsupported local Bootstrap action rejected", xbmc.LOGWARNING)
    return True


def offer_real_debrid_authorization(document):
    if not any(item.get("authAdapter") == "real-debrid-device-v1" for item in document["addons"]):
        return
    open_now = xbmcgui.Dialog().yesno(
        "Authorize Real-Debrid",
        "The Kodi package is installed. Open Starlane Movies Setup to start the official "
        "Real-Debrid device authorization now? You can also do this later from the app "
        "or setup provider.",
        nolabel="Later",
        yeslabel="Open setup app",
    )
    if not open_now:
        return
    if xbmc.getCondVisibility("System.Platform.Android"):
        xbmc.executebuiltin("StartAndroidActivity(%s)" % SETUP_APP_PACKAGE, True)
    else:
        notify("Open Starlane Movies Setup on the TV to authorize Real-Debrid")


def consume_real_debrid_handoff():
    path = xbmcvfs.translatePath(REAL_DEBRID_HANDOFF)
    if not os.path.exists(path):
        return False
    file_stat = os.lstat(path)
    if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_size < 2 or file_stat.st_size > 16384:
        raise ValueError("Real-Debrid handoff file is invalid")
    with open(path, "r", encoding="utf-8") as handoff:
        document = json.load(handoff)
    expected = {"version", "addonId", *REAL_DEBRID_FIELDS}
    if (
        not isinstance(document, dict)
        or set(document) != expected
        or document["version"] != 1
        or document["addonId"] != REAL_DEBRID_ADDON
    ):
        raise ValueError("Real-Debrid handoff schema is invalid")
    for field in REAL_DEBRID_FIELDS:
        value = document[field]
        maximum = 256 if field == "username" else 4096
        if not isinstance(value, str) or not value or len(value) > maximum:
            raise ValueError("Real-Debrid handoff value is invalid")
    if not xbmc.getCondVisibility("System.HasAddon(%s)" % REAL_DEBRID_ADDON):
        raise ValueError("Real-Debrid target add-on is not installed")

    addon = xbmcaddon.Addon(REAL_DEBRID_ADDON)
    home = xbmcgui.Window(10000)
    home.setProperty("umbrella.updateSettings", "false")
    try:
        addon.setSetting("realdebrid.enable", "true")
        for field, setting_id in REAL_DEBRID_FIELDS.items():
            addon.setSetting(setting_id, document[field])
    finally:
        home.setProperty("umbrella.updateSettings", "true")
    if not all(addon.getSetting(setting_id) for setting_id in REAL_DEBRID_FIELDS.values()):
        raise ValueError("Real-Debrid settings did not persist")
    os.remove(path)
    notify("Real-Debrid linked to Starlane Movies")
    log("Real-Debrid credentials imported locally")
    return True


def process_real_debrid_handoff():
    try:
        return consume_real_debrid_handoff()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        log(str(error), xbmc.LOGERROR)
        path = xbmcvfs.translatePath(REAL_DEBRID_HANDOFF)
        try:
            os.remove(path)
        except OSError:
            pass
        notify("Real-Debrid handoff was rejected; authorize again")
        return False


def monitor_real_debrid_handoff(monitor, interval=2):
    while not monitor.waitForAbort(interval):
        process_real_debrid_handoff()


def skin_setting():
    request = {"jsonrpc": "2.0", "id": 1, "method": "Settings.GetSettingValue", "params": {"setting": "lookandfeel.skin"}}
    result = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
    return result.get("result", {}).get("value")


def internal_setting(setting_id):
    value = ADDON.getSettingString(setting_id)
    return "" if value == INTERNAL_UNSET else value


def set_internal_setting(setting_id, value):
    ADDON.setSettingString(setting_id, value or INTERNAL_UNSET)


def set_skin(value):
    request = {"jsonrpc": "2.0", "id": 1, "method": "Settings.SetSettingValue", "params": {"setting": "lookandfeel.skin", "value": value}}
    result = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
    if "error" in result:
        raise ValueError(result["error"].get("message", "skin activation failed"))


def configure_kodi_quality_of_life():
    """Disable Kodi's core splash without replacing any other advanced setting."""
    path = xbmcvfs.translatePath("special://profile/advancedsettings.xml")
    try:
        changed = disable_core_splash(path)
    except (OSError, ValueError, ElementTree.ParseError) as error:
        log("advancedsettings.xml was left unchanged: " + str(error), xbmc.LOGWARNING)
        return
    if changed:
        log("Kodi core splash disabled; Starlane Movies startup will lead on the next launch")


def recover_pending_skin():
    target = internal_setting("pending_skin")
    if not target:
        return
    current = skin_setting()
    if current == target:
        set_internal_setting("pending_skin", "")
        set_internal_setting("previous_skin", "")
        record_activation_attempt(0)
        log("Skin activation confirmed: " + target)
        return
    previous = internal_setting("previous_skin") or "skin.estuary"
    log("Skin activation did not persist; restoring " + previous, xbmc.LOGWARNING)
    set_skin(previous)
    set_internal_setting("pending_skin", "")
    set_internal_setting("previous_skin", "")
    # Completion was recorded optimistically so the setup app could observe it.
    # An unconfirmed skin means the run did not really finish, so withdraw the
    # applied scope and let this launch activate the Home menu again. Kodi being
    # killed at its own keep-skin dialog must not strand the television on
    # Estuary with the configuration marked as applied.
    attempts = activation_attempts() + 1
    if attempts > MAX_ACTIVATION_ATTEMPTS:
        log("Home activation exhausted its retries; leaving the skin unchanged", xbmc.LOGWARNING)
        notify("Starlane Movies could not load; choose it in Settings, Interface, Skin")
        return
    record_activation_attempt(attempts)
    set_internal_setting("applied_scope", "")
    notify("Starlane Movies did not load; retrying its Home menu now")


def download(url, destination, expected_hash, allowed_prefixes):
    if not any(url.startswith(prefix) for prefix in allowed_prefixes):
        raise ValueError("download URL is outside the approved package hosts")
    request = urllib.request.Request(url, headers={"User-Agent": "KodiSetupBootstrap/1"})
    with urllib.request.urlopen(request, timeout=30) as response, open(destination, "wb") as output:
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            output.write(block)
    if sha256(destination) != expected_hash:
        os.remove(destination)
        raise ValueError("download hash mismatch")


def set_addon_enabled(addon_id, enabled):
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "Addons.SetAddonEnabled",
        "params": {"addonid": addon_id, "enabled": bool(enabled)},
    }
    result = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
    if "error" in result:
        raise ValueError(
            result["error"].get("message", "%s could not be enabled" % addon_id)
        )


def android_abi():
    machine = platform.machine().lower()
    if struct.calcsize("P") == 8 and ("aarch64" in machine or "arm64" in machine):
        return "arm64-v8a"
    return "armeabi-v7a"


def validate_package_item(item):
    addon_id = item.get("id")
    version = item.get("version")
    if not isinstance(addon_id, str) or not ADDON_ID.fullmatch(addon_id):
        raise ValueError("package lock contains an invalid add-on ID")
    if not isinstance(version, str) or not PACKAGE_VERSION.fullmatch(version):
        raise ValueError("%s has an invalid locked version" % addon_id)
    if ("url" in item) == ("variants" in item):
        raise ValueError("%s must define either a URL or ABI variants" % addon_id)
    selected = item
    if "variants" in item:
        variants = item["variants"]
        if not isinstance(variants, dict):
            raise ValueError("%s has invalid ABI variants" % addon_id)
        selected = variants.get(android_abi())
        if not isinstance(selected, dict):
            raise ValueError("%s has no package for this Android ABI" % addon_id)
    url = selected.get("url")
    expected_hash = selected.get("sha256")
    if not isinstance(url, str) or not any(
        url.startswith(prefix) for prefix in PACKAGE_URL_PREFIXES
    ):
        raise ValueError("%s uses an unapproved package URL" % addon_id)
    if not isinstance(expected_hash, str) or not SHA256.fullmatch(expected_hash):
        raise ValueError("%s has an invalid package hash" % addon_id)
    return {
        "id": addon_id,
        "version": version,
        "url": url,
        "sha256": expected_hash,
    }


def load_package_lock_with_digest():
    path = os.path.join(ADDON.getAddonInfo("path"), "resources", "package-lock.json")
    with open(path, "rb") as source:
        raw = source.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("package lock exceeds size limit")
    document = json.loads(raw.decode("utf-8"))
    if document.get("schemaVersion") != 1 or not isinstance(
        document.get("packages"), list
    ):
        raise ValueError("package lock schema is not supported")
    packages = [validate_package_item(item) for item in document["packages"]]
    ids = [item["id"] for item in packages]
    if len(ids) != len(set(ids)):
        raise ValueError("package lock contains duplicate add-on IDs")
    return packages, hashlib.sha256(raw).hexdigest()


def load_package_lock():
    return load_package_lock_with_digest()[0]


def validate_lock_for_manifest(packages, document):
    locked = {item["id"] for item in packages}
    required = {document["skin"]["addonId"]}
    required.update(
        item["id"] for item in document["addons"] if item.get("enabled")
    )
    required.update(SKIN_PREREQUISITES.get(document["skin"]["addonId"], ()))
    missing = sorted(required - locked)
    if missing:
        raise ValueError("package lock is missing: " + ", ".join(missing))


def addon_version(addon_id):
    try:
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "Addons.GetAddonDetails",
            "params": {"addonid": addon_id, "properties": ["version", "enabled"]},
        }
        result = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
        return result.get("result", {}).get("addon", {}).get("version", "")
    except (RuntimeError, TypeError, ValueError):
        return ""


def inspect_package_archive(archive, package):
    members = archive.infolist()
    roots = {
        member.filename.replace("\\", "/").split("/")[0]
        for member in members
        if member.filename
    }
    if roots != {package["id"]}:
        raise ValueError("%s ZIP root does not match its add-on ID" % package["id"])
    for member in members:
        normalized = posixpath.normpath(member.filename.replace("\\", "/"))
        mode = member.external_attr >> 16
        if (
            normalized == ".."
            or normalized.startswith("../")
            or normalized.startswith("/")
            or stat.S_ISLNK(mode)
        ):
            raise ValueError("%s ZIP contains an unsafe path" % package["id"])
    addon_member = package["id"] + "/addon.xml"
    try:
        root = ElementTree.fromstring(archive.read(addon_member))
    except KeyError as error:
        raise ValueError("%s ZIP has no root addon.xml" % package["id"]) from error
    if root.attrib.get("id") != package["id"]:
        raise ValueError("%s addon.xml ID does not match" % package["id"])
    if root.attrib.get("version") != package["version"]:
        raise ValueError("%s addon.xml version does not match" % package["id"])


def install_locked_package(package):
    previous_version = addon_version(package["id"])
    if previous_version == package["version"]:
        return
    was_enabled = xbmc.getCondVisibility("System.HasAddon(%s)" % package["id"])
    addons_path = xbmcvfs.translatePath("special://home/addons")
    packages_path = os.path.join(addons_path, "packages")
    os.makedirs(packages_path, exist_ok=True)
    archive_path = os.path.join(
        packages_path, "%s-%s.zip" % (package["id"], package["version"])
    )
    try:
        download(
            package["url"],
            archive_path,
            package["sha256"],
            PACKAGE_URL_PREFIXES,
        )
    except (OSError, ValueError) as error:
        raise ValueError("%s: %s" % (package["id"], error)) from error
    staging = tempfile.mkdtemp(prefix=".starlane-", dir=addons_path)
    backup = os.path.join(addons_path, "." + package["id"] + ".starlane-backup")
    target = os.path.join(addons_path, package["id"])
    disabled_for_upgrade = False
    try:
        with zipfile.ZipFile(archive_path) as archive:
            inspect_package_archive(archive, package)
            archive.extractall(staging)
        extracted = os.path.join(staging, package["id"])
        if previous_version and was_enabled:
            set_addon_enabled(package["id"], False)
            disabled_for_upgrade = True
        if os.path.exists(backup):
            shutil.rmtree(backup)
        if os.path.exists(target):
            os.replace(target, backup)
        try:
            os.replace(extracted, target)
        except Exception:
            if os.path.exists(backup) and not os.path.exists(target):
                os.replace(backup, target)
            if disabled_for_upgrade:
                xbmc.executebuiltin("UpdateLocalAddons", True)
                set_addon_enabled(package["id"], True)
            raise
        if os.path.exists(backup):
            shutil.rmtree(backup)
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def install_locked_packages(packages, progress):
    for index, package in enumerate(packages):
        progress.update(
            25 + int(55 * index / max(1, len(packages))),
            "Starlane Movies",
            "Installing package: " + package["id"],
        )
        install_locked_package(package)
    xbmc.executebuiltin("UpdateLocalAddons", True)
    wait_for_registered_packages(packages)


def wait_for_registered_packages(packages, attempts=120, interval=0.25):
    """Wait for Kodi's asynchronous add-on scan to expose every exact locked version."""
    pending = {item["id"]: item["version"] for item in packages}
    monitor = xbmc.Monitor()
    for _attempt in range(attempts):
        pending = {
            addon_id: version
            for addon_id, version in pending.items()
            if addon_version(addon_id) != version
        }
        if not pending:
            return
        if monitor.waitForAbort(interval):
            raise ValueError("Kodi stopped while registering add-ons")
    details = ", ".join(
        "%s=%s" % (addon_id, version) for addon_id, version in sorted(pending.items())
    )
    raise ValueError("Kodi did not register locked package versions: " + details)


def install_repository(repository):
    addons_path = xbmcvfs.translatePath("special://home/addons")
    packages_path = os.path.join(addons_path, "packages")
    os.makedirs(packages_path, exist_ok=True)
    archive_path = os.path.join(packages_path, repository["addonId"] + ".zip")
    download(
        repository["source"]["resolvedUrl"],
        archive_path,
        repository["sha256"],
        ("https://github.com/",),
    )
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        roots = {member.filename.split("/")[0] for member in members if member.filename}
        if len(roots) != 1:
            raise ValueError("repository ZIP must contain exactly one root")
        archive_root = next(iter(roots))
        for member in members:
            normalized = posixpath.normpath(member.filename.replace("\\", "/"))
            mode = member.external_attr >> 16
            if (
                normalized == ".."
                or normalized.startswith("../")
                or normalized.startswith("/")
                or stat.S_ISLNK(mode)
            ):
                raise ValueError("repository ZIP contains an unsafe path")
        addon_member = archive_root + "/addon.xml"
        root = ElementTree.fromstring(archive.read(addon_member))
        if root.attrib.get("id") != repository["addonId"]:
            raise ValueError("repository addon.xml ID mismatch")
        archive.extractall(addons_path)
    xbmc.executebuiltin("UpdateLocalAddons", True)
    set_addon_enabled(repository["addonId"], True)


def configure_addon(item):
    if not addon_version(item["id"]) and not xbmc.getCondVisibility(
        "System.HasAddon(%s)" % item["id"]
    ):
        raise ValueError("%s is not installed" % item["id"])
    set_addon_enabled(item["id"], item["enabled"])
    if not item["enabled"]:
        return
    target = xbmcaddon.Addon(item["id"])
    for key, value in item.get("settings", {}).items():
        if isinstance(value, bool):
            target.setSettingBool(key, value)
        elif isinstance(value, int):
            target.setSettingInt(key, value)
        else:
            target.setSettingString(key, str(value))


def activation_attempts():
    try:
        return int(internal_setting("activation_attempts") or 0)
    except ValueError:
        return 0


def record_activation_attempt(count):
    set_internal_setting("activation_attempts", str(count) if count else "")


def wait_for_provider_ready(addon_id, attempts=120, interval=0.25):
    """Wait briefly for the provider's own service to announce readiness.

    Kodi starts ``xbmc.service`` entry points at launch. A locked package is
    installed by replacing its directory and enabling it over JSON-RPC, which
    never spawns that service, so on the installing launch this property cannot
    appear at all. Callers treat the timeout as a reason to finish after Kodi
    restarts rather than as a failure.
    """
    if addon_id != "plugin.video.umbrella":
        return
    window = xbmcgui.Window(10000)
    monitor = xbmc.Monitor()
    for _attempt in range(attempts):
        if window.getProperty("starlane.umbrella.ready") == "true":
            return
        if monitor.waitForAbort(interval):
            raise ValueError("Kodi stopped while waiting for the provider")
    raise ValueError("Starlane on-demand provider did not finish initialising")


def restart_provider_service(addon_id):
    """Ask Kodi to start a service add-on by cycling its enabled state.

    Kodi starts ``xbmc.service`` entry points in response to an enable event. A
    locked package installed by directory replacement can already be enabled, so
    re-enabling it is a no-op that fires no event and its service never starts.
    Cycling the state produces that event using the same JSON-RPC method already
    in use, without adding any new capability.
    """
    if addon_id != "plugin.video.umbrella":
        return False
    xbmcgui.Window(10000).clearProperty("starlane.umbrella.ready")
    set_addon_enabled(addon_id, False)
    set_addon_enabled(addon_id, True)
    log("Cycled %s to start its service" % addon_id)
    return True


def activate_skin_and_generate_shortcuts(skin_id):
    previous = skin_setting() or "skin.estuary"
    set_internal_setting("previous_skin", previous)
    set_internal_setting("pending_skin", skin_id)
    set_skin(skin_id)
    monitor = xbmc.Monitor()
    for _attempt in range(40):
        if skin_setting() == skin_id:
            break
        if monitor.waitForAbort(0.25):
            raise ValueError("Kodi stopped while activating the skin")
    else:
        raise ValueError("skin activation did not complete")
    xbmc.executebuiltin(
        "RunScript(script.skinshortcuts,type=buildxml&mainmenuID=900&group=mainmenu|powermenu)",
        True,
    )
    wait_for_generated_skin_shortcuts(skin_id)
    xbmc.executebuiltin("ReloadSkin()", True)


def wait_for_generated_skin_shortcuts(skin_id, attempts=360, interval=0.25):
    includes_path = os.path.join(
        xbmcvfs.translatePath("special://home/addons"),
        skin_id,
        "xml",
        "script-skinshortcuts-includes.xml",
    )
    required = (
        'include name="skinshortcuts-mainmenu"',
        'include name="skinshortcuts-submenu"',
        'include name="skinshortcuts-group-powermenu"',
    )
    monitor = xbmc.Monitor()
    for _attempt in range(attempts):
        try:
            with open(includes_path, "r", encoding="utf-8") as generated:
                content = generated.read(2 * 1024 * 1024)
            if all(marker in content for marker in required):
                return
        except OSError:
            pass
        if monitor.waitForAbort(interval):
            raise ValueError("Kodi stopped while generating the Home menu")
    raise ValueError("Skin Shortcuts did not generate the required Home menu")


def park_active_package_skin(skin_id):
    if skin_setting() != skin_id:
        return
    set_skin("skin.estuary")
    monitor = xbmc.Monitor()
    for _attempt in range(40):
        if skin_setting() == "skin.estuary":
            log("Active package skin parked on Estuary during provider upgrade")
            return
        if monitor.waitForAbort(0.25):
            raise ValueError("Kodi stopped while parking the active skin")
    raise ValueError("active package skin could not be parked")


def provider_replacement_required(packages):
    for package in packages:
        if package["id"] == "plugin.video.umbrella":
            expected = package.get("version", "")
            return not expected or addon_version(package["id"]) != expected
    return False


def prepare_provider_replacement(packages, skin_id):
    if not provider_replacement_required(packages):
        return False
    xbmcgui.Window(10000).clearProperty("starlane.umbrella.ready")
    park_active_package_skin(skin_id)
    return True


def run():
    recover_pending_skin()
    manifest_url = ADDON.getSettingString("manifest_url")
    public_key = ADDON.getSettingString("public_key")
    if not public_key:
        log("Public key has not been configured", xbmc.LOGWARNING)
        notify("Bootstrap requires a release public key")
        return
    document = fetch_and_verify(manifest_url, public_key)
    packages, package_lock_digest = load_package_lock_with_digest()
    validate_lock_for_manifest(packages, document)
    scope_digest = canonical_installation_scope(document, package_lock_digest)
    if (
        ADDON.getSettingString("applied_version") == document["configVersion"]
        and internal_setting("applied_scope") == scope_digest
    ):
        log("Verified configuration scope is already applied")
        return
    if not ensure_installation_authorized(document, len(packages), scope_digest):
        return
    configure_kodi_quality_of_life()
    progress = xbmcgui.DialogProgressBG()
    progress.create("Starlane Movies", "Preparing the approved Kodi package")
    failures = []
    deferred = ""
    try:
        prepare_provider_replacement(packages, document["skin"]["addonId"])
        enabled_repositories = [item for item in document["repositories"] if item["enabled"]]
        for index, repository in enumerate(enabled_repositories):
            progress.update(
                5 + int(20 * index / max(1, len(enabled_repositories))),
                "Starlane Movies",
                "Installing repository: " + repository["name"],
            )
            try:
                install_repository(repository)
            except Exception as error:  # Kodi must continue to report all failed items.
                failures.append(repository["id"] + ": " + str(error))
                log(failures[-1], xbmc.LOGERROR)
        progress.update(25, "Starlane Movies", "Installing verified Kodi packages")
        try:
            install_locked_packages(packages, progress)
        except Exception as error:
            failures.append("package installation: " + str(error))
            log(failures[-1], xbmc.LOGERROR)
        package_install_failed = bool(failures)
        enabled_addons = [item for item in document["addons"] if item["enabled"]]
        for index, item in enumerate(enabled_addons):
            progress.update(
                81 + int(4 * index / max(1, len(enabled_addons))),
                "Starlane Movies",
                "Configuring add-on: " + item["name"],
            )
            try:
                configure_addon(item)
            except Exception as error:
                failures.append(item["id"] + ": " + str(error))
                log(failures[-1], xbmc.LOGERROR)
        for item in enabled_addons:
            try:
                wait_for_provider_ready(item["id"])
            except Exception as error:
                # Most often the freshly installed package was already enabled,
                # so Kodi never raised the enable event that starts its service.
                # Cycle it once and wait again before giving up on this launch.
                try:
                    cycled = restart_provider_service(item["id"])
                except Exception:
                    cycled = False
                if cycled:
                    try:
                        wait_for_provider_ready(item["id"])
                        continue
                    except Exception as retry_error:
                        error = retry_error
                # Readiness can still be legitimately absent on the launch that
                # installed the provider, so finish after Kodi restarts rather
                # than reporting a false failure.
                if activation_attempts() < MAX_ACTIVATION_ATTEMPTS:
                    deferred = item["id"] + ": " + str(error)
                    log("Deferring Home activation until Kodi restarts: " + deferred)
                    break
                failures.append(item["id"] + ": " + str(error))
                log(failures[-1], xbmc.LOGERROR)
        if not deferred:
            configured_ids = {item["id"] for item in enabled_addons}
            if not package_install_failed:
                for package in packages:
                    if package["id"] not in configured_ids:
                        try:
                            set_addon_enabled(package["id"], True)
                        except Exception as error:
                            failures.append(package["id"] + ": " + str(error))
                            log(failures[-1], xbmc.LOGERROR)
            progress.update(
                85, "Starlane Movies", "Installing and activating the Starlane Movies skin"
            )
            try:
                if failures:
                    raise ValueError("verified package or provider readiness failed")
                skin_id = document["skin"]["addonId"]
                if not xbmc.getCondVisibility("System.HasAddon(%s)" % skin_id):
                    raise ValueError("skin was not registered by Kodi")
                activate_skin_and_generate_shortcuts(skin_id)
            except Exception as error:
                failures.append("skin: " + str(error))
        progress.update(100, "Starlane Movies", "Kodi package installation complete")
    finally:
        progress.close()
    if deferred:
        record_activation_attempt(activation_attempts() + 1)
        notify("Starlane Movies will finish setting up when Kodi restarts")
        xbmc.executebuiltin("Quit")
        return
    if failures:
        notify("Setup finished with %d issue(s)" % len(failures))
        return
    set_internal_setting("applied_scope", scope_digest)
    ADDON.setSettingString("applied_version", document["configVersion"])
    record_activation_attempt(0)
    notify("Configuration %s applied" % document["configVersion"])
    offer_real_debrid_authorization(document)


if __name__ == "__main__":
    if not handle_local_action(sys.argv[1:]):
        monitor = xbmc.Monitor()
        if not monitor.waitForAbort(5):
            try:
                process_real_debrid_handoff()
                run()
                process_real_debrid_handoff()
            except Exception as error:
                log(str(error), xbmc.LOGERROR)
                notify("Setup failed; check kodi.log")
            monitor_real_debrid_handoff(monitor)

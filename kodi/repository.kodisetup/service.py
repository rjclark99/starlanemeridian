import json
import os
import platform
import posixpath
import re
import shutil
import stat
import struct
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
    "https://control.starlanemeridian.uk/v1/public/kodi/",
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


def ensure_installation_authorized(document, package_count):
    if ADDON.getSettingBool("installation_authorized"):
        return True
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
    ADDON.setSettingBool("installation_authorized", True)
    log("Initial package installation authorized")
    return True


def offer_real_debrid_authorization(document):
    if not any(item.get("authAdapter") == "real-debrid-device-v1" for item in document["addons"]):
        return
    open_now = xbmcgui.Dialog().yesno(
        "Authorize Real-Debrid",
        "The Kodi package is installed. Open Starlane Movies Setup to start the official "
        "Real-Debrid device authorization now? You can also do this later from the app "
        "or device management panel.",
        nolabel="Later",
        yeslabel="Open setup app",
    )
    if not open_now:
        return
    if xbmc.getCondVisibility("System.Platform.Android"):
        xbmc.executebuiltin("StartAndroidActivity(%s)" % SETUP_APP_PACKAGE, True)
    else:
        notify("Open Starlane Movies Setup on the TV to authorize Real-Debrid")


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
        log("Skin activation confirmed: " + target)
        return
    previous = internal_setting("previous_skin") or "skin.estuary"
    log("Skin activation did not persist; restoring " + previous, xbmc.LOGWARNING)
    set_skin(previous)
    set_internal_setting("pending_skin", "")
    set_internal_setting("previous_skin", "")
    notify("Skin load failed; the previous Kodi skin was restored")


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


def load_package_lock():
    path = os.path.join(ADDON.getAddonInfo("path"), "resources", "package-lock.json")
    with open(path, "r", encoding="utf-8") as source:
        document = json.load(source)
    if document.get("schemaVersion") != 1 or not isinstance(
        document.get("packages"), list
    ):
        raise ValueError("package lock schema is not supported")
    packages = [validate_package_item(item) for item in document["packages"]]
    ids = [item["id"] for item in packages]
    if len(ids) != len(set(ids)):
        raise ValueError("package lock contains duplicate add-on IDs")
    return packages


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
        return xbmcaddon.Addon(addon_id).getAddonInfo("version")
    except (RuntimeError, TypeError):
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
    download(
        package["url"],
        archive_path,
        package["sha256"],
        PACKAGE_URL_PREFIXES,
    )
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
    target = xbmcaddon.Addon(item["id"])
    for key, value in item.get("settings", {}).items():
        if isinstance(value, bool):
            target.setSettingBool(key, value)
        elif isinstance(value, int):
            target.setSettingInt(key, value)
        else:
            target.setSettingString(key, str(value))
    if item["id"] == "plugin.video.umbrella":
        xbmcgui.Window(10000).clearProperty("starlane.umbrella.ready")
    set_addon_enabled(item["id"], item["enabled"])


def wait_for_provider_ready(addon_id, attempts=960, interval=0.25):
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
    xbmc.executebuiltin("ReloadSkin()", True)


def run():
    recover_pending_skin()
    manifest_url = ADDON.getSettingString("manifest_url")
    public_key = ADDON.getSettingString("public_key")
    if not public_key:
        log("Public key has not been configured", xbmc.LOGWARNING)
        notify("Bootstrap requires a release public key")
        return
    document = fetch_and_verify(manifest_url, public_key)
    if ADDON.getSettingString("applied_version") == document["configVersion"]:
        log("Configuration is already applied")
        return
    packages = load_package_lock()
    validate_lock_for_manifest(packages, document)
    if not ensure_installation_authorized(document, len(packages)):
        return
    configure_kodi_quality_of_life()
    progress = xbmcgui.DialogProgressBG()
    progress.create("Starlane Movies", "Preparing the approved Kodi package")
    failures = []
    try:
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
                failures.append(item["id"] + ": " + str(error))
                log(failures[-1], xbmc.LOGERROR)
        configured_ids = {item["id"] for item in enabled_addons}
        if not package_install_failed:
            for package in packages:
                if package["id"] not in configured_ids:
                    try:
                        set_addon_enabled(package["id"], True)
                    except Exception as error:
                        failures.append(package["id"] + ": " + str(error))
                        log(failures[-1], xbmc.LOGERROR)
        progress.update(85, "Starlane Movies", "Installing and activating the Starlane Movies skin")
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
    if failures:
        notify("Setup finished with %d issue(s)" % len(failures))
        return
    ADDON.setSettingString("applied_version", document["configVersion"])
    notify("Configuration %s applied" % document["configVersion"])
    offer_real_debrid_authorization(document)


if __name__ == "__main__":
    monitor = xbmc.Monitor()
    if not monitor.waitForAbort(5):
        try:
            run()
        except Exception as error:
            log(str(error), xbmc.LOGERROR)
            notify("Setup failed; check kodi.log")

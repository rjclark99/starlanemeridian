import hashlib
import json
import os
import urllib.request
import zipfile
from xml.etree import ElementTree

import xbmc
import xbmcaddon
import xbmcvfs

from resources.lib.manifest import fetch_and_verify, sha256

ADDON = xbmcaddon.Addon()
LOG_PREFIX = "[Kodi Setup] "


def log(message, level=xbmc.LOGINFO):
    xbmc.log(LOG_PREFIX + message, level)


def notify(message):
    xbmc.executebuiltin("Notification(Kodi Setup,%s,5000)" % message.replace(",", " "))


def download(url, destination, expected_hash):
    if not url.startswith("https://github.com/"):
        raise ValueError("repository downloads must be GitHub HTTPS URLs")
    request = urllib.request.Request(url, headers={"User-Agent": "KodiSetupBootstrap/1"})
    with urllib.request.urlopen(request, timeout=30) as response, open(destination, "wb") as output:
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            output.write(block)
    if sha256(destination) != expected_hash:
        os.remove(destination)
        raise ValueError("repository hash mismatch")


def install_repository(repository):
    addons_path = xbmcvfs.translatePath("special://home/addons")
    packages_path = xbmcvfs.translatePath("special://home/addons/packages")
    os.makedirs(packages_path, exist_ok=True)
    archive_path = os.path.join(packages_path, repository["addonId"] + ".zip")
    download(repository["source"]["resolvedUrl"], archive_path, repository["sha256"])
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        roots = {member.filename.split("/")[0] for member in members if member.filename}
        if roots != {repository["addonId"]}:
            raise ValueError("repository ZIP root does not match addonId")
        for member in members:
            normalized = os.path.normpath(member.filename).replace("\\", "/")
            if normalized.startswith("../") or normalized.startswith("/"):
                raise ValueError("repository ZIP contains an unsafe path")
        addon_member = repository["addonId"] + "/addon.xml"
        root = ElementTree.fromstring(archive.read(addon_member))
        if root.attrib.get("id") != repository["addonId"]:
            raise ValueError("repository addon.xml ID mismatch")
        archive.extractall(addons_path)
    xbmc.executebuiltin("UpdateLocalAddons", True)
    xbmc.executebuiltin("EnableAddon(%s)" % repository["addonId"], True)


def apply_addon(item):
    xbmc.executebuiltin("InstallAddon(%s)" % item["id"], True)
    if item["enabled"]:
        xbmc.executebuiltin("EnableAddon(%s)" % item["id"], True)
    target = xbmcaddon.Addon(item["id"])
    for key, value in item.get("settings", {}).items():
        if isinstance(value, bool):
            target.setSettingBool(key, value)
        elif isinstance(value, int):
            target.setSettingInt(key, value)
        else:
            target.setSettingString(key, str(value))
    if item.get("authAdapter") == "real-debrid-device-v1":
        notify("Authorize Real-Debrid in %s settings" % item["name"])


def run():
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
    failures = []
    for repository in document["repositories"]:
        if repository["enabled"]:
            try:
                install_repository(repository)
            except Exception as error:  # Kodi must continue to report all failed items.
                failures.append(repository["id"] + ": " + str(error))
                log(failures[-1], xbmc.LOGERROR)
    xbmc.executebuiltin("UpdateAddonRepos", True)
    for item in document["addons"]:
        try:
            apply_addon(item)
        except Exception as error:
            failures.append(item["id"] + ": " + str(error))
            log(failures[-1], xbmc.LOGERROR)
            if item["required"]:
                continue
    if document["skin"].get("enabled", False):
        try:
            skin_id = document["skin"]["addonId"]
            xbmc.executebuiltin("InstallAddon(%s)" % skin_id, True)
            request = {"jsonrpc": "2.0", "id": 1, "method": "Settings.SetSettingValue", "params": {"setting": "lookandfeel.skin", "value": skin_id}}
            result = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
            if "error" in result:
                failures.append("skin: " + result["error"].get("message", "activation failed"))
        except Exception as error:
            failures.append("skin: " + str(error))
    if failures:
        notify("Setup finished with %d issue(s)" % len(failures))
        return
    ADDON.setSettingString("applied_version", document["configVersion"])
    notify("Configuration %s applied" % document["configVersion"])


if __name__ == "__main__":
    monitor = xbmc.Monitor()
    if not monitor.waitForAbort(5):
        try:
            run()
        except Exception as error:
            log(str(error), xbmc.LOGERROR)
            notify("Setup failed; check kodi.log")

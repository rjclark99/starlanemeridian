import base64
import hashlib
import json
import re
import urllib.request

from .ed25519_verify import verify

ADDON_ID = re.compile(r"^[a-z][a-z0-9]*(\.[a-z0-9_-]+)+$")
SAFE_SETTING = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
ALLOWED_ADAPTERS = {None, "real-debrid-device-v1"}
ALLOWED_MENU_ACTIONS = {"kodi-window", "addon", "favourite", "noop"}


def _decode(value):
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def canonical(document):
    clone = json.loads(json.dumps(document))
    clone["signature"]["value"] = ""
    return json.dumps(clone, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def fetch_and_verify(url, public_key):
    if not url.startswith("https://"):
        raise ValueError("manifest URL must use HTTPS")
    request = urllib.request.Request(url, headers={"User-Agent": "KodiSetupBootstrap/1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise ValueError("manifest exceeds size limit")
    document = json.loads(raw.decode("utf-8"))
    validate(document)
    if not verify(_decode(document["signature"]["value"]), canonical(document), _decode(public_key)):
        raise ValueError("manifest signature is invalid")
    return document


def validate(document):
    if document.get("schemaVersion") != 1 or document.get("stage") not in ("test", "stable"):
        raise ValueError("unsupported or inactive manifest")
    if document.get("kodi", {}).get("channel") != "stable" or document.get("kodi", {}).get("packageName") != "org.xbmc.kodi":
        raise ValueError("unsupported Kodi distribution")
    repositories = {item["id"] for item in document.get("repositories", [])}
    for repository in document.get("repositories", []):
        if not ADDON_ID.fullmatch(repository["id"]) or not repository["source"]["resolvedUrl"].startswith("https://github.com/"):
            raise ValueError("unsafe repository definition")
        if not re.fullmatch(r"[a-f0-9]{64}", repository["sha256"]):
            raise ValueError("invalid repository hash")
    for addon in document.get("addons", []):
        if not ADDON_ID.fullmatch(addon["id"]) or addon["repositoryId"] not in repositories:
            raise ValueError("unsafe add-on definition")
        if addon.get("authAdapter") not in ALLOWED_ADAPTERS:
            raise ValueError("unsupported authorization adapter")
        if any(not SAFE_SETTING.fullmatch(key) or isinstance(value, (dict, list)) for key, value in addon.get("settings", {}).items()):
            raise ValueError("unsafe add-on setting")
    for item in document["skin"]["homeMenu"]:
        if item["action"]["type"] not in ALLOWED_MENU_ACTIONS:
            raise ValueError("unsafe menu action")


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

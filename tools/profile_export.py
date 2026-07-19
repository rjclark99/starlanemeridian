#!/usr/bin/env python3
"""Create a secret-scrubbed, review-only profile from a Kodi home directory.

The exporter intentionally does not copy Kodi databases, addon_data files, caches,
credentials, or history. Its JSON output is an inventory used to curate a signed
manifest and skin; it is never installed directly.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from xml.etree import ElementTree

ADDON_ID = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z0-9_-]+)+$")
SENSITIVE_KEY = re.compile(
    r"pass|secret|token|oauth|auth|credential|cookie|session|api.?key|client.?id|device.?id|"
    r"username|user.?name|email|account|real.?debrid|premiumize|alldebrid|pin",
    re.IGNORECASE,
)
SENSITIVE_VALUE = re.compile(
    r"(?:bearer\s+|https?://|[A-Za-z0-9_-]{32,}|[^\s@]+@[^\s@]+\.[^\s@]+)", re.IGNORECASE
)
CORE_PREFIXES = ("xbmc.", "kodi.")


def safe_setting(key: str, value: str) -> bool:
    if not key or len(key) > 64 or SENSITIVE_KEY.search(key):
        return False
    if len(value) > 128 or SENSITIVE_VALUE.search(value):
        return False
    return True


def parse_settings(path: Path) -> tuple[dict[str, object], list[str]]:
    kept: dict[str, object] = {}
    omitted: list[str] = []
    if not path.is_file():
        return kept, omitted
    try:
        root = ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError):
        return kept, ["<unreadable-settings.xml>"]
    for element in root.findall(".//setting"):
        key = element.get("id") or element.get("name") or ""
        value = element.get("value") if element.get("value") is not None else (element.text or "")
        value = value.strip()
        if not safe_setting(key, value):
            omitted.append(key or "<unnamed>")
            continue
        lowered = value.lower()
        if lowered in ("true", "false"):
            kept[key] = lowered == "true"
        elif re.fullmatch(r"-?[0-9]+", value):
            kept[key] = int(value)
        else:
            kept[key] = value
    return kept, sorted(set(omitted))


def addon_inventory(kodi_home: Path) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    addons_dir = kodi_home / "addons"
    addon_data = kodi_home / "userdata" / "addon_data"
    if not addons_dir.is_dir():
        raise ValueError(f"Kodi add-ons directory was not found: {addons_dir}")
    for addon_xml in sorted(addons_dir.glob("*/addon.xml")):
        try:
            root = ElementTree.parse(addon_xml).getroot()
        except (ElementTree.ParseError, OSError):
            continue
        addon_id = root.get("id", "")
        if not ADDON_ID.fullmatch(addon_id) or addon_id.startswith(CORE_PREFIXES):
            continue
        extensions = sorted({item.get("point", "") for item in root.findall("extension") if item.get("point")})
        if not any(point in extensions for point in ("xbmc.python.pluginsource", "xbmc.addon.repository", "xbmc.service", "xbmc.gui.skin")):
            continue
        settings, omitted = parse_settings(addon_data / addon_id / "settings.xml")
        result.append({
            "id": addon_id,
            "name": root.get("name", addon_id),
            "version": root.get("version", "unknown"),
            "extensionPoints": extensions,
            "safeSettings": settings,
            "omittedSettingKeys": omitted,
            "repositoryId": None,
            "required": False,
            "reviewRequired": True,
        })
    return result


def export_profile(kodi_home: Path, output: Path) -> dict[str, object]:
    document = {
        "formatVersion": 1,
        "source": "secret-scrubbed Kodi inventory",
        "installable": False,
        "reviewRequired": True,
        "addons": addon_inventory(kodi_home),
        "skin": {"addonId": None, "menuCapture": "deferred-to-custom-skin-phase"},
        "excluded": [
            "databases", "thumbnails", "cache", "logs", "history", "favourites",
            "sources", "passwords", "tokens", "cookies", "account identifiers",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return document


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kodi_home", type=Path, help="Path containing Kodi addons/ and userdata/")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    document = export_profile(args.kodi_home.resolve(), args.output.resolve())
    print(f"Wrote {len(document['addons'])} review-only add-on candidates to {args.output}")


if __name__ == "__main__":
    main()

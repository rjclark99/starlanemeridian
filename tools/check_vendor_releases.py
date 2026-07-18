#!/usr/bin/env python3
"""Produce review-only vendor update candidates; never edits signed manifests."""

import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = {"User-Agent": "KodiSetupReleaseMonitor/1"}


def get_text(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=USER_AGENT), timeout=30) as response:
        return response.read().decode("utf-8")


def stable_kodi(abi, directory):
    page = get_text(directory)
    pattern = rf'href="(kodi-(\d+)\.(\d+)\.(\d+)-[^"/]+-{re.escape(abi)}\.apk)"'
    matches = [(tuple(map(int, item[1:])), item[0]) for item in re.findall(pattern, page, re.I) if not re.search(r"alpha|beta|rc", item[0], re.I)]
    if not matches:
        raise RuntimeError(f"No stable Kodi build found at {directory}")
    version, filename = max(matches)
    return {"version": ".".join(map(str, version)), "url": directory + filename, "sha256": None, "signerSha256": None}


def proton_candidates():
    payload = json.loads(get_text("https://api.github.com/repos/ProtonVPN/android-app/releases/latest"))
    return {"version": payload["tag_name"], "releaseUrl": payload["html_url"], "apkAssets": [{"name": asset["name"], "url": asset["browser_download_url"], "sha256": asset.get("digest")} for asset in payload.get("assets", []) if asset["name"].lower().endswith(".apk")]}


result = {
    "checkedAt": datetime.now(timezone.utc).isoformat(),
    "reviewRequired": True,
    "warning": "Do not promote these candidates until package identity, compatibility, SHA-256, and signer certificate are independently verified.",
    "kodi": {
        "armeabi-v7a": stable_kodi("armeabi-v7a", "https://mirrors.kodi.tv/releases/android/arm/"),
        "arm64-v8a": stable_kodi("arm64-v8a", "https://mirrors.kodi.tv/releases/android/arm64-v8a/"),
    },
    "protonVpn": proton_candidates(),
}
(ROOT / "config" / "vendor-candidates.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


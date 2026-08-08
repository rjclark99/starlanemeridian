#!/usr/bin/env python3
"""Download each selected Kodi package once and verify its locked SHA-256."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
import urllib.parse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK = ROOT / "kodi" / "repository.kodisetup" / "resources" / "package-lock.json"


def selected_packages(document: dict, abi: str):
    for package in document["packages"]:
        selected = package.get("variants", {}).get(abi) if "variants" in package else package
        if not isinstance(selected, dict):
            raise ValueError(f"{package.get('id', '<unknown>')} has no {abi} variant")
        yield package["id"], package["version"], selected["url"], selected["sha256"]


def remote_sha256(url: str, timeout: float) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    request = urllib.request.Request(url, headers={"User-Agent": "StarlanePackageLockVerifier/1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        while block := response.read(1024 * 1024):
            digest.update(block)
            size += len(block)
    return digest.hexdigest(), size


def verify(lock_path: Path, abi: str, timeout: float, verbose: bool = False) -> list[str]:
    document = json.loads(lock_path.read_text(encoding="utf-8"))
    failures = []
    checked = 0
    for addon_id, version, url, expected in selected_packages(document, abi):
        checked += 1
        try:
            actual, size = remote_sha256(url, timeout)
            if actual.lower() != expected.lower():
                failures.append(f"{addon_id} {version}: expected {expected}, found {actual} ({size} bytes) {url}")
            elif verbose:
                print(f"OK {addon_id} {version} {size} bytes")
        except Exception as error:  # A failed URL is a verification failure, not a traceback dump.
            failures.append(f"{addon_id} {version}: {type(error).__name__}: {error} {url}")
    print(f"Checked {checked} selected packages for {abi}; failures: {len(failures)}")
    for failure in failures:
        print("FAIL " + failure)
    return failures


def verify_local_assets(lock_path: Path, assets: Path, required_ids: list[str]) -> list[str]:
    document = json.loads(lock_path.read_text(encoding="utf-8"))
    packages = {package["id"]: package for package in document["packages"]}
    indexed: dict[str, Path] = {}
    for path in assets.rglob("*"):
        if not path.is_file() or path.name.endswith(".sha256"):
            continue
        if path.name in indexed:
            raise ValueError(f"duplicate local asset name: {path.name}")
        indexed[path.name] = path
    failures = []
    for addon_id in required_ids:
        package = packages.get(addon_id)
        if not package or "variants" in package:
            failures.append(f"{addon_id}: missing fixed package lock entry")
            continue
        filename = Path(urllib.parse.urlparse(package["url"]).path).name
        artifact = indexed.get(filename)
        if not artifact:
            failures.append(f"{addon_id}: missing built release asset {filename}")
            continue
        actual = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if actual.lower() != package["sha256"].lower():
            failures.append(
                f"{addon_id} {package['version']}: expected {package['sha256']}, "
                f"found {actual} ({artifact.stat().st_size} bytes)"
            )
    print(f"Checked {len(required_ids)} required local release packages; failures: {len(failures)}")
    for failure in failures:
        print("FAIL " + failure)
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--abi", choices=("armeabi-v7a", "arm64-v8a"), default="armeabi-v7a")
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--local-assets", type=Path)
    parser.add_argument("--require-id", action="append", default=[])
    args = parser.parse_args()
    if args.local_assets:
        if not args.require_id:
            parser.error("--local-assets requires at least one --require-id")
        return 1 if verify_local_assets(args.lock, args.local_assets, args.require_id) else 0
    if args.require_id:
        parser.error("--require-id requires --local-assets")
    return 1 if verify(args.lock, args.abi, args.timeout, args.verbose) else 0


if __name__ == "__main__":
    raise SystemExit(main())

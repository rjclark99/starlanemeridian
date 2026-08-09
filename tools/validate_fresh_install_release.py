import argparse
import hashlib
import json
import re
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_URL = "https://github.com/rjclark99/starlanemeridian/releases/latest/download/manifest.json"
CONTROL_API_URL = "https://control.starlanemeridian.uk"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_match(pattern: str, text: str, label: str) -> str:
    match = re.search(pattern, text)
    if not match:
        raise SystemExit(f"Could not establish {label}")
    return match.group(1)


def verify_file(path: Path, expected: str, label: str) -> None:
    if not path.is_file():
        raise SystemExit(f"Missing {label}")
    if sha256(path) != expected:
        raise SystemExit(f"{label} hash does not match the signed release contract")


def validate(root: Path, tag: str, kodi_assets: Path | None = None) -> None:
    gradle = (root / "android-app" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    version_code = int(require_match(r"versionCode\s*=\s*(\d+)", gradle, "Android version code"))
    version_name = require_match(r'versionName\s*=\s*"([0-9]+(?:\.[0-9]+){2})"', gradle, "Android version name")
    expected_tag = f"v{version_name}-test"
    if tag != expected_tag:
        raise SystemExit(f"Release tag must be {expected_tag}")

    manifest = json.loads((root / "config" / "manifest.json").read_text(encoding="utf-8"))
    if manifest["minimumSetupAppVersion"] != version_code:
        raise SystemExit("Manifest minimum app code does not match the release APK")
    if not manifest["signature"]["value"]:
        raise SystemExit("Release manifest is unsigned")

    bootstrap_root = root / "kodi" / "repository.kodisetup"
    bootstrap_version = ElementTree.parse(bootstrap_root / "addon.xml").getroot().attrib["version"]
    bootstrap_name = f"repository.kodisetup-{bootstrap_version}.zip"
    expected_bootstrap_url = (
        f"https://github.com/rjclark99/starlanemeridian/releases/download/{tag}/{bootstrap_name}"
    )
    if manifest["bootstrap"]["url"] != expected_bootstrap_url:
        raise SystemExit("Manifest Bootstrap URL does not match the release tag and version")

    lock = json.loads((bootstrap_root / "resources" / "package-lock.json").read_text(encoding="utf-8"))
    packages = {item["id"]: item for item in lock["packages"]}
    provider = packages["plugin.video.umbrella"]
    provider_name = f"plugin.video.umbrella-{provider['version']}.zip"
    expected_provider_url = (
        f"https://github.com/rjclark99/starlanemeridian/releases/download/{tag}/{provider_name}"
    )
    if provider["url"] != expected_provider_url:
        raise SystemExit("Provider URL does not match the release tag and version")

    if kodi_assets is not None:
        verify_file(
            kodi_assets / "repository.kodisetup" / bootstrap_name,
            manifest["bootstrap"]["sha256"],
            "Bootstrap archive",
        )
        for package_id in ("plugin.video.umbrella", "skin.starlane.movies"):
            package = packages[package_id]
            filename = f"{package_id}-{package['version']}.zip"
            verify_file(kodi_assets / package_id / filename, package["sha256"], f"{package_id} archive")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--kodi-assets", type=Path)
    args = parser.parse_args()
    validate(ROOT, args.tag, args.kodi_assets)
    print("Fresh-install release contract passed")


if __name__ == "__main__":
    main()

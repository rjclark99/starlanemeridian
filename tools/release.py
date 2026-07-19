#!/usr/bin/env python3
"""Release utilities. Private keys are never written unless --private-key is explicit."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]


def canonical_payload(document: dict) -> bytes:
    clone = json.loads(json.dumps(document))
    clone["signature"]["value"] = ""
    return json.dumps(clone, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def validate_manifest(path: Path) -> dict:
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError as exc:
        raise SystemExit("Install tools/requirements.txt before validation") from exc

    document = load_json(path)
    schema = load_json(ROOT / "config" / "manifest.schema.json")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda item: list(item.path))
    if errors:
        for error in errors:
            location = ".".join(map(str, error.absolute_path)) or "<root>"
            print(f"{location}: {error.message}", file=sys.stderr)
        raise SystemExit(f"Manifest failed validation with {len(errors)} error(s)")

    repository_ids = {item["id"] for item in document["repositories"]}
    duplicate_repo_ids = len(repository_ids) != len(document["repositories"])
    addon_ids = [item["id"] for item in document["addons"]]
    if duplicate_repo_ids or len(set(addon_ids)) != len(addon_ids):
        raise SystemExit("Repository and add-on IDs must be unique")
    unknown_repositories = sorted({item["repositoryId"] for item in document["addons"]} - repository_ids)
    if unknown_repositories:
        raise SystemExit(f"Add-ons reference unknown repositories: {', '.join(unknown_repositories)}")
    return document


def keygen(private_path: Path, public_path: Path) -> None:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    if private_path.exists() or public_path.exists():
        raise SystemExit("Refusing to overwrite an existing key")
    private_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    private = Ed25519PrivateKey.generate()
    private_path.write_bytes(private.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption()))
    public_path.write_text(b64url(private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)) + "\n", encoding="ascii")
    if os.name != "nt":
        private_path.chmod(0o600)


def sign_manifest(path: Path, private_path: Path) -> None:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    document = validate_manifest(path)
    if document["stage"] == "stable":
        serialized = json.dumps(document)
        if "0" * 64 in serialized or "example.invalid" in serialized or "OWNER/REPOSITORY" in serialized:
            raise SystemExit("Stable manifests may not contain placeholder hashes, owners, or example.invalid URLs")
    private = Ed25519PrivateKey.from_private_bytes(private_path.read_bytes())
    document["signature"]["value"] = b64url(private.sign(canonical_payload(document)))
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def safe_zip_tree(source: Path, destination: Path, root_name: str | None = None) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for file in sorted(source.rglob("*")):
            if file.is_file():
                relative = file.relative_to(source)
                arcname = Path(root_name, relative) if root_name else relative
                info = zipfile.ZipInfo(str(arcname).replace("\\", "/"), date_time=(2020, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, file.read_bytes())


def build_kodi(output: Path, base_url: str) -> None:
    if not base_url.startswith("https://"):
        raise SystemExit("Kodi repository base URL must use HTTPS")
    output.mkdir(parents=True, exist_ok=True)
    source = ROOT / "kodi" / "repository.kodisetup"
    with tempfile.TemporaryDirectory() as temp_name:
        staged = Path(temp_name) / "repository.kodisetup"
        shutil.copytree(source, staged)
        addon_xml = staged.joinpath("addon.xml").read_text(encoding="utf-8").replace("${REPOSITORY_BASE_URL}", base_url.rstrip("/"))
        staged.joinpath("addon.xml").write_text(addon_xml, encoding="utf-8")
        root = ElementTree.fromstring(addon_xml)
        version = root.attrib["version"]
        addon_dir = output / "repository.kodisetup"
        addon_dir.mkdir(exist_ok=True)
        zip_path = addon_dir / f"repository.kodisetup-{version}.zip"
        safe_zip_tree(staged, zip_path, "repository.kodisetup")
        shutil.copy2(staged / "icon.png", addon_dir / "icon.png") if (staged / "icon.png").exists() else None

        metadata = [ElementTree.tostring(root, encoding="unicode")]
        skin_zip = next((ROOT / "artifacts" / "skin").glob("skin.starlanemeridian-*.zip"), None) if (ROOT / "artifacts" / "skin").exists() else None
        if skin_zip:
            skin_dir = output / "skin.starlanemeridian"
            skin_dir.mkdir(exist_ok=True)
            shutil.copy2(skin_zip, skin_dir / skin_zip.name)
            with zipfile.ZipFile(skin_zip) as archive:
                skin_root = ElementTree.fromstring(archive.read("skin.starlanemeridian/addon.xml"))
                metadata.append(ElementTree.tostring(skin_root, encoding="unicode"))
        addons_xml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<addons>\n" + "\n".join(metadata) + "\n</addons>\n"
        addons_bytes = addons_xml.encode("utf-8")
        # Write exact bytes so the published checksum is platform-independent on Windows and Linux.
        (output / "addons.xml").write_bytes(addons_bytes)
        (output / "addons.xml.sha256").write_bytes((hashlib.sha256(addons_bytes).hexdigest() + "\n").encode("ascii"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("manifest", type=Path)
    generate = sub.add_parser("keygen")
    generate.add_argument("--private-key", type=Path, required=True)
    generate.add_argument("--public-key", type=Path, required=True)
    sign = sub.add_parser("sign")
    sign.add_argument("manifest", type=Path)
    sign.add_argument("--private-key", type=Path, required=True)
    kodi = sub.add_parser("kodi")
    kodi.add_argument("--output", type=Path, required=True)
    kodi.add_argument("--base-url", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "validate":
        validate_manifest(args.manifest)
        print("Manifest is valid")
    elif args.command == "keygen":
        keygen(args.private_key, args.public_key)
    elif args.command == "sign":
        sign_manifest(args.manifest, args.private_key)
        print("Manifest signed")
    elif args.command == "kodi":
        build_kodi(args.output, args.base_url)
        print(f"Kodi repository written to {args.output}")


if __name__ == "__main__":
    main()

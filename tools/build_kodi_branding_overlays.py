#!/usr/bin/env python3
"""Build a Starlane-branded copy of the Umbrella Kodi provider add-on.

The add-on IDs, routes, settings keys, Python identifiers, and upstream licences stay
unchanged. Only user-facing metadata, human-readable brand strings, and declared
artwork are replaced.
"""

from __future__ import annotations

import argparse
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "assets" / "branding"
EMBLEM = BRAND / "starlane-movies-emblem-v2.png"
BACKGROUND = BRAND / "starlane-movies-home-1920x1080.jpg"
MINT = "ff67e8c4"
VISIBLE_BRAND = re.compile(r"(?<![A-Za-z0-9_])(?:Umbrella|UMBRELLA)(?![A-Za-z0-9_])")


@dataclass(frozen=True)
class AddonBrand:
    addon_id: str
    source_version: str
    branded_version: str
    display_name: str
    subtitle: str
    summary: str
    description: str
    upstream_name: str
    upstream_source: str
    replacements: tuple[tuple[str, str], ...]


ADDONS = (
    AddonBrand(
        addon_id="plugin.video.umbrella",
        source_version="6.7.81",
        branded_version="6.7.81.1",
        display_name="Starlane Movies: On Demand",
        subtitle="ON DEMAND",
        summary="Starlane Movies on-demand discovery and playback.",
        description=(
            "The on-demand playback integration for Starlane Movies. This add-on "
            "does not host content and is not part of the official Kodi project."
        ),
        upstream_name="Umbrella",
        upstream_source="https://umbrellaplug.github.io",
        replacements=(
            (r"(?<![A-Za-z0-9_])UMBRELLA(?![A-Za-z0-9_])", "STARLANE MOVIES"),
            (r"(?<![A-Za-z0-9_])Umbrella(?![A-Za-z0-9_])", "Starlane Movies"),
        ),
    ),
)

UMBRELLA_PYTHON_VISIBLE_REPLACEMENTS = {
    "resources/help/help.py": {
        "[B]Umbrella -  v%s - %s[/B]": "[B]Starlane Movies -  v%s - %s[/B]",
    },
    "resources/lib/context/addLibtoFavourite.py": {"heading='Umbrella'": "heading='Starlane Movies'"},
    "resources/lib/context/libMdblistManager.py": {"heading='Umbrella'": "heading='Starlane Movies'"},
    "resources/lib/context/libRescrape.py": {"heading='Umbrella'": "heading='Starlane Movies'"},
    "resources/lib/database/artwork.py": {"'Umbrella Art'": "'Starlane Movies Art'"},
    "resources/lib/debrid/torbox.py": {
        "Umbrella TorBox Referral Link": "Starlane Movies TorBox Referral Link",
    },
    "resources/lib/menus/collections.py": {"Umbrella Settings": "Starlane Movies Settings"},
    "resources/lib/menus/episodes.py": {"Umbrella Settings": "Starlane Movies Settings"},
    "resources/lib/menus/movies.py": {"Umbrella Settings": "Starlane Movies Settings"},
    "resources/lib/menus/navigator.py": {
        "'Umbrella Icons'": "'Starlane Movies Icons'",
        "Umbrella Settings": "Starlane Movies Settings",
    },
    "resources/lib/menus/seasons.py": {"Umbrella Settings": "Starlane Movies Settings"},
    "resources/lib/menus/tvshows.py": {
        "folderName='Umbrella'": "folderName='Starlane Movies'",
        "Umbrella Settings": "Starlane Movies Settings",
    },
    "resources/lib/modules/control.py": {
        "]Umbrella[/COLOR": "]Starlane Movies[/COLOR",
        "notification('Umbrella',": "notification('Starlane Movies',",
    },
    "resources/lib/modules/library.py": {
        "'Umbrella Movies'": "'Starlane Movies Movies'",
        "'Umbrella TV Shows'": "'Starlane Movies TV Shows'",
    },
    "resources/lib/modules/router.py": {
        "Umbrella Log File Successfully Cleared": "Starlane Movies Log File Successfully Cleared",
        "Error clearing Umbrella Log File": "Error clearing Starlane Movies Log File",
    },
    "resources/lib/windows/textviewer.py": {
        "kwargs.get('heading','Umbrella')": "kwargs.get('heading','Starlane Movies')",
    },
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidate = Path("C:/Windows/Fonts") / ("segoeuib.ttf" if bold else "segoeui.ttf")
    return ImageFont.truetype(str(candidate), size) if candidate.is_file() else ImageFont.load_default()


def contain(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    clone = image.copy()
    clone.thumbnail(size, Image.Resampling.LANCZOS)
    return clone


def make_icon(subtitle: str, size: int = 512) -> Image.Image:
    result = Image.new("RGBA", (size, size), "#050B14")
    emblem = contain(Image.open(EMBLEM).convert("RGBA"), (round(size * 0.58), round(size * 0.58)))
    result.alpha_composite(emblem, ((size - emblem.width) // 2, round(size * 0.06)))
    draw = ImageDraw.Draw(result)
    draw.text(
        (size // 2, round(size * 0.69)),
        "STARLANE MOVIES",
        anchor="mm",
        font=font(round(size * 0.064), True),
        fill="#F4FAFF",
    )
    draw.line(
        (round(size * 0.22), round(size * 0.77), round(size * 0.78), round(size * 0.77)),
        fill="#67E8C4",
        width=max(2, round(size * 0.006)),
    )
    draw.text(
        (size // 2, round(size * 0.84)),
        subtitle,
        anchor="mm",
        font=font(round(size * 0.055), True),
        fill="#91A8C0",
    )
    return result


def make_fanart(subtitle: str) -> Image.Image:
    result = Image.open(BACKGROUND).convert("RGBA")
    result.alpha_composite(Image.new("RGBA", result.size, (5, 11, 20, 70)))
    emblem = contain(Image.open(EMBLEM).convert("RGBA"), (250, 250))
    result.alpha_composite(emblem, (110, 120))
    draw = ImageDraw.Draw(result)
    draw.text((390, 170), "STARLANE MOVIES", font=font(56, True), fill="#F4FAFF")
    draw.text((392, 245), subtitle, font=font(38, True), fill="#67E8C4")
    draw.line((392, 310, 860, 310), fill="#67E8C4", width=4)
    draw.text((392, 330), "YOUR MEDIA. ON COURSE.", font=font(22), fill="#91A8C0")
    return result.convert("RGB")


def make_banner(subtitle: str) -> Image.Image:
    result = Image.new("RGBA", (758, 140), "#050B14")
    emblem = contain(Image.open(EMBLEM).convert("RGBA"), (116, 116))
    result.alpha_composite(emblem, (18, 12))
    draw = ImageDraw.Draw(result)
    draw.text((160, 29), "STARLANE MOVIES", font=font(36, True), fill="#F4FAFF")
    draw.text((162, 78), subtitle, font=font(25, True), fill="#67E8C4")
    draw.line((162, 114, 700, 114), fill="#67E8C4", width=3)
    return result


def replace_human_brand(text: str, addon: AddonBrand) -> str:
    result = text
    for pattern, replacement in addon.replacements:
        result = re.sub(pattern, replacement, result)
    result = result.replace("[COLOR orchid]", f"[COLOR {MINT}]")
    result = result.replace("[COLORyellow]", f"[COLOR {MINT}]")
    return result


def rewrite_user_facing_text(addon_root: Path, addon: AddonBrand) -> None:
    text_extensions = {".po", ".xml", ".txt"}
    excluded_names = {
        "LICENSE",
        "LICENSE.txt",
        "README.md",
        "UPSTREAM_ATTRIBUTION.txt",
        "UPSTREAM_CHANGELOG.txt",
    }
    for path in addon_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in text_extensions:
            continue
        if path.name in excluded_names or path.name in {"changelog.txt", "fullchangelog.txt"}:
            continue
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            continue
        updated = replace_human_brand(text, addon)
        if updated != text:
            path.write_text(updated, encoding="utf-8", newline="")


def rewrite_user_facing_python(addon_root: Path, addon: AddonBrand) -> None:
    if addon.addon_id != "plugin.video.umbrella":
        return
    for relative, replacements in UMBRELLA_PYTHON_VISIBLE_REPLACEMENTS.items():
        path = addon_root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8-sig")
        for old, new in replacements.items():
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8", newline="")


def update_metadata(addon_root: Path, addon: AddonBrand) -> None:
    addon_xml = addon_root / "addon.xml"
    tree = ET.parse(addon_xml)
    root = tree.getroot()
    if root.attrib.get("id") != addon.addon_id:
        raise ValueError(f"{addon_xml}: expected id {addon.addon_id}")
    if root.attrib.get("version") != addon.source_version:
        raise ValueError(
            f"{addon_xml}: expected version {addon.source_version}, "
            f"found {root.attrib.get('version')}"
        )
    root.set("name", addon.display_name)
    root.set("provider-name", "Starlane Movies")
    root.set("version", addon.branded_version)

    metadata = root.find("extension[@point='xbmc.addon.metadata']")
    if metadata is None:
        raise ValueError(f"{addon_xml}: missing metadata extension")
    summary = metadata.find("summary")
    description = metadata.find("description")
    if summary is None:
        summary = ET.SubElement(metadata, "summary", {"lang": "en"})
    if description is None:
        description = ET.SubElement(metadata, "description", {"lang": "en"})
    summary.text = addon.summary
    description.text = addon.description
    for tag in ("website", "source"):
        node = metadata.find(tag)
        if node is None:
            node = ET.SubElement(metadata, tag)
        node.text = "https://github.com/rjclark99/starlanemeridian"
    for screenshot in list(metadata.findall("./assets/screenshot")):
        metadata.find("assets").remove(screenshot)
    news = metadata.find("news")
    if news is None:
        news = ET.SubElement(metadata, "news")
    news.text = (
        f"[B]STARLANE MOVIES[/B][CR]Local presentation overlay for "
        f"version {addon.source_version}."
    )
    ET.indent(tree, space="  ")
    tree.write(addon_xml, encoding="utf-8", xml_declaration=True)


def replace_artwork(addon_root: Path, addon: AddonBrand) -> None:
    icon = make_icon(addon.subtitle)
    fanart = make_fanart(addon.subtitle)
    banner = make_banner(addon.subtitle)
    icon_targets = [
        addon_root / "icon.png",
        addon_root / "resources" / "artwork" / "icon.png",
        addon_root / "resources" / "artwork" / "umbrella" / "icon.png",
        addon_root / "resources" / "skins" / "Default" / "media" / "common" / "icon.png",
    ]
    fanart_targets = [
        addon_root / "fanart.jpg",
        addon_root / "resources" / "artwork" / "umbrella" / "fanart.jpg",
        addon_root / "resources" / "skins" / "Default" / "media" / "common" / "fanart.jpg",
    ]
    for target in icon_targets:
        if target.is_file():
            icon.save(target, optimize=True)
    for target in fanart_targets:
        if target.is_file():
            fanart.save(target, quality=92, optimize=True)
    banner_target = addon_root / "resources" / "artwork" / "umbrella" / "banner.png"
    if banner_target.is_file():
        banner.save(banner_target, optimize=True)
    circle_target = (
        addon_root
        / "resources"
        / "skins"
        / "Default"
        / "media"
        / "common"
        / "umbrellacircle.png"
    )
    if circle_target.is_file():
        circle = contain(Image.open(EMBLEM).convert("RGBA"), (54, 54))
        canvas = Image.new("RGBA", (60, 60))
        canvas.alpha_composite(circle, ((60 - circle.width) // 2, (60 - circle.height) // 2))
        canvas.save(circle_target, optimize=True)


def preserve_upstream_records(addon_root: Path, addon: AddonBrand) -> None:
    changelog = next(
        (path for path in (addon_root / "fullchangelog.txt", addon_root / "changelog.txt") if path.is_file()),
        None,
    )
    if changelog:
        shutil.copy2(changelog, addon_root / "UPSTREAM_CHANGELOG.txt")
        changelog.write_text(
            "[B]STARLANE MOVIES[/B]\n"
            f"Local presentation overlay for version {addon.source_version}.\n"
            "Provider routes and playback behavior are unchanged.\n",
            encoding="utf-8",
        )
    (addon_root / "UPSTREAM_ATTRIBUTION.txt").write_text(
        f"Upstream add-on: {addon.upstream_name}\n"
        f"Upstream version: {addon.source_version}\n"
        f"Upstream source: {addon.upstream_source}\n"
        "The original licence files and source headers are preserved.\n"
        "Starlane Movies changes presentation metadata, display strings, and artwork only.\n",
        encoding="utf-8",
    )
    for screenshots in (
        addon_root / "resources" / "screenshots",
        addon_root / "resources" / "art" / "ss",
    ):
        if screenshots.is_dir():
            shutil.rmtree(screenshots)


def audit_user_facing(addon_root: Path) -> None:
    excluded_names = {
        "LICENSE",
        "LICENSE.txt",
        "README.md",
        "UPSTREAM_ATTRIBUTION.txt",
        "UPSTREAM_CHANGELOG.txt",
    }
    findings = []
    for path in addon_root.rglob("*"):
        if (
            not path.is_file()
            or path.suffix.lower() not in {".po", ".xml", ".txt"}
            or path.name in excluded_names
        ):
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            continue
        match = VISIBLE_BRAND.search(text)
        if match:
            findings.append(f"{path.relative_to(addon_root)}: {match.group(0)}")
    if findings:
        raise ValueError(
            f"{addon_root.name}: user-facing upstream branding remains:\n"
            + "\n".join(findings)
        )
    if addon_root.name == "plugin.video.umbrella":
        for relative, replacements in UMBRELLA_PYTHON_VISIBLE_REPLACEMENTS.items():
            path = addon_root / relative
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8-sig")
            stale = [old for old in replacements if old in text]
            if stale:
                raise ValueError(f"{path}: user-facing runtime branding remains: {stale}")


def package(addon_root: Path, output_root: Path) -> Path:
    zip_path = output_root / f"{addon_root.name}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(addon_root.rglob("*")):
            if path.is_file():
                info = zipfile.ZipInfo(
                    path.relative_to(addon_root.parent).as_posix(),
                    date_time=(2026, 7, 28, 0, 0, 0),
                )
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, path.read_bytes(), compresslevel=9)
    return zip_path


def build(source_root: Path, output_root: Path) -> list[Path]:
    output_root.mkdir(parents=True, exist_ok=True)
    built = []
    for addon in ADDONS:
        source = source_root / addon.addon_id
        target = output_root / addon.addon_id
        if not source.is_dir():
            raise FileNotFoundError(source)
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(
            source,
            target,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
        preserve_upstream_records(target, addon)
        rewrite_user_facing_text(target, addon)
        rewrite_user_facing_python(target, addon)
        update_metadata(target, addon)
        replace_artwork(target, addon)
        audit_user_facing(target)
        built.append(package(target, output_root))
    return built


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    for artifact in build(args.source_root.resolve(), args.output_root.resolve()):
        print(artifact)


if __name__ == "__main__":
    main()

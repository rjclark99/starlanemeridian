#!/usr/bin/env python3
"""Build a branded GPL skin from a reviewed Kodi source archive containing Estuary."""

from __future__ import annotations

import argparse
import html
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from release import safe_zip_tree, validate_manifest

WINDOWS = {"videos": "Videos", "tvshows": "Videos,tvshowtitles", "movies": "Videos,movietitles", "addons": "AddonBrowser", "settings": "Settings", "music": "Music", "pictures": "Pictures", "favourites": "Favourites"}


def action(value: dict) -> str:
    kind, target = value["type"], value["target"]
    if kind == "kodi-window":
        if target not in WINDOWS:
            raise SystemExit(f"Unsupported Kodi window target: {target}")
        return f"ActivateWindow({WINDOWS[target]})"
    if kind == "addon":
        if not target.startswith(("plugin.", "script.")):
            raise SystemExit("Add-on menu targets must be plugin.* or script.* IDs")
        return f"RunAddon({target})"
    if kind == "favourite":
        return "ActivateWindow(Favourites)"
    return "Noop"


def home_xml(menu: list[dict]) -> str:
    items = []
    widgets = []
    for index, item in enumerate(menu):
        items.append(f"""          <item id=\"{index + 1}\"><label>{html.escape(item['label'])}</label><onclick>{html.escape(action(item['action']))}</onclick><property name=\"MenuId\">{html.escape(item['id'])}</property></item>""")
        for widget_index, widget in enumerate(item["widgets"]):
            control_id = 11000 + index * 100 + widget_index
            widgets.append(f"""
      <control type=\"group\">
        <visible>String.IsEqual(Container(9000).ListItem.Property(MenuId),{html.escape(item['id'])})</visible>
        <top>{180 + widget_index * 250}</top><left>430</left>
        <control type=\"label\"><width>1400</width><height>45</height><font>font20_title</font><label>{html.escape(widget['label'])}</label></control>
        <control type=\"panel\" id=\"{control_id}\"><top>50</top><width>1420</width><height>195</height><orientation>horizontal</orientation><content target=\"videos\" limit=\"{widget['limit']}\">{html.escape(widget['provider'])}</content></control>
      </control>""")
    return f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<window>
  <defaultcontrol always=\"true\">9000</defaultcontrol>
  <controls>
    <control type=\"image\"><left>0</left><top>0</top><width>1920</width><height>1080</height><texture>colors/black.png</texture><colordiffuse>FF07111F</colordiffuse></control>
    <control type=\"label\"><left>85</left><top>65</top><width>1500</width><height>80</height><font>font45_title</font><label>KODI SETUP</label><textcolor>FF52B8FF</textcolor></control>
    <control type=\"fixedlist\" id=\"9000\"><left>70</left><top>175</top><width>330</width><height>780</height><orientation>vertical</orientation><focusposition>2</focusposition>
      <itemlayout width=\"330\" height=\"76\"><control type=\"label\"><width>320</width><height>70</height><font>font20</font><label>$INFO[ListItem.Label]</label></control></itemlayout>
      <focusedlayout width=\"330\" height=\"76\"><control type=\"image\"><width>320</width><height>70</height><texture colordiffuse=\"FF52B8FF\">colors/white.png</texture></control><control type=\"label\"><width>320</width><height>70</height><font>font20</font><label>$INFO[ListItem.Label]</label><textcolor>FF07111F</textcolor></control></focusedlayout>
      <content>
{chr(10).join(items)}
      </content>
    </control>
{''.join(widgets)}
  </controls>
</window>
"""


def find_estuary(extracted: Path) -> Path:
    matches = [path for path in extracted.rglob("skin.estuary") if path.is_dir() and (path / "addon.xml").exists()]
    if len(matches) != 1:
        raise SystemExit(f"Expected one skin.estuary directory, found {len(matches)}")
    return matches[0]


def build(archive: Path, manifest_path: Path, output: Path, version: str) -> None:
    manifest = validate_manifest(manifest_path)
    with tempfile.TemporaryDirectory() as name:
        temporary = Path(name)
        with zipfile.ZipFile(archive) as source:
            for member in source.infolist():
                normalized = Path(member.filename)
                if normalized.is_absolute() or ".." in normalized.parts:
                    raise SystemExit("Upstream archive contains an unsafe path")
            source.extractall(temporary / "source")
        upstream = find_estuary(temporary / "source")
        staged = temporary / "skin.kodisetup"
        shutil.copytree(upstream, staged)
        addon_path = staged / "addon.xml"
        root = ElementTree.parse(addon_path).getroot()
        root.attrib.update({"id": "skin.kodisetup", "name": "Kodi Setup", "version": version, "provider-name": "Kodi Setup Platform; based on Team Kodi Estuary"})
        ElementTree.indent(root)
        addon_path.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + ElementTree.tostring(root, encoding="unicode") + "\n", encoding="utf-8")
        (staged / "xml" / "Home.xml").write_text(home_xml(manifest["skin"]["homeMenu"]), encoding="utf-8")
        output.mkdir(parents=True, exist_ok=True)
        destination = output / f"skin.kodisetup-{version}.zip"
        safe_zip_tree(staged, destination, "skin.kodisetup")
        print(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream-archive", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--version", default="1.0.0")
    args = parser.parse_args()
    build(args.upstream_archive, args.manifest, args.output, args.version)


#!/usr/bin/env python3
"""Build the Starlane Meridian GPL skin from a reviewed Kodi Estuary source archive."""

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

SKIN_ID = "skin.starlanemeridian"
SKIN_NAME = "Starlane Meridian"
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
        items.append(f"""          <item id=\"{index + 1}\"><label>{html.escape(item['label'])}</label><label2>{index + 1:02d}</label2><onclick>{html.escape(action(item['action']))}</onclick><property name=\"MenuId\">{html.escape(item['id'])}</property></item>""")
        for widget_index, widget in enumerate(item["widgets"]):
            control_id = 11000 + index * 100 + widget_index
            widgets.append(f"""
      <control type=\"group\">
        <visible>String.IsEqual(Container(9000).ListItem.Property(MenuId),{html.escape(item['id'])})</visible>
        <top>{390 + widget_index * 250}</top><left>610</left>
        <control type=\"label\"><width>1180</width><height>45</height><font>font20_title</font><label>{html.escape(widget['label'])}</label><textcolor>white</textcolor></control>
        <control type=\"panel\" id=\"{control_id}\"><top>55</top><width>1210</width><height>190</height><orientation>horizontal</orientation><content target=\"videos\" limit=\"{widget['limit']}\" browse=\"auto\">{html.escape(widget['provider'])}</content></control>
      </control>""")
    return f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<window>
  <defaultcontrol always=\"true\">9000</defaultcontrol>
  <animation effect=\"fade\" start=\"0\" end=\"100\" time=\"280\">WindowOpen</animation>
  <animation effect=\"fade\" start=\"100\" end=\"0\" time=\"180\">WindowClose</animation>
  <controls>
    <control type=\"image\"><left>0</left><top>0</top><width>1920</width><height>1080</height><aspectratio>scale</aspectratio><texture>brand/home.jpg</texture></control>
    <control type=\"image\"><left>0</left><top>0</top><width>1920</width><height>1080</height><texture colordiffuse=\"B808111D\">colors/white.png</texture></control>
    <control type=\"image\"><left>72</left><top>58</top><width>72</width><height>72</height><aspectratio>keep</aspectratio><texture>brand/emblem.png</texture></control>
    <control type=\"label\"><left>162</left><top>63</top><width>900</width><height>42</height><font>font30_title</font><label>STARLANE MERIDIAN</label><textcolor>white</textcolor></control>
    <control type=\"label\"><left>164</left><top>105</top><width>700</width><height>30</height><font>font12</font><label>YOUR MEDIA. ON COURSE.</label><textcolor>FF67E8C4</textcolor></control>
    <control type=\"label\"><right>74</right><top>64</top><width>400</width><height>40</height><align>right</align><font>font30_title</font><label>$INFO[System.Time]</label><textcolor>white</textcolor></control>
    <control type=\"label\"><right>76</right><top>107</top><width>400</width><height>28</height><align>right</align><font>font12</font><label>$INFO[System.Date]</label><textcolor>FF91A8C0</textcolor></control>
    <control type=\"image\"><left>70</left><top>194</top><width>4</width><height>690</height><texture colordiffuse=\"4052B8FF\">colors/white.png</texture></control>
    <control type=\"fixedlist\" id=\"9000\"><left>98</left><top>210</top><width>430</width><height>650</height><orientation>vertical</orientation><focusposition>2</focusposition>
      <itemlayout width=\"430\" height=\"88\">
        <control type=\"label\"><left>8</left><top>9</top><width>44</width><height>64</height><font>font12</font><label>$INFO[ListItem.Label2]</label><textcolor>FF5F7891</textcolor><aligny>center</aligny></control>
        <control type=\"label\"><left>64</left><top>9</top><width>345</width><height>64</height><font>font20</font><label>$INFO[ListItem.Label]</label><textcolor>FF91A8C0</textcolor><aligny>center</aligny></control>
      </itemlayout>
      <focusedlayout width=\"430\" height=\"88\">
        <control type=\"image\"><left>0</left><top>6</top><width>420</width><height>70</height><texture colordiffuse=\"EAF4FAFF\" border=\"21\">buttons/button-fo.png</texture></control>
        <control type=\"image\"><left>0</left><top>20</top><width>4</width><height>42</height><texture colordiffuse=\"FF67E8C4\">colors/white.png</texture></control>
        <control type=\"label\"><left>16</left><top>9</top><width>44</width><height>64</height><font>font12</font><label>$INFO[ListItem.Label2]</label><textcolor>FF0A1825</textcolor><aligny>center</aligny></control>
        <control type=\"label\"><left>72</left><top>9</top><width>332</width><height>64</height><font>font20_title</font><label>$INFO[ListItem.Label]</label><textcolor>FF07111F</textcolor><aligny>center</aligny></control>
        <animation effect=\"slide\" start=\"-8,0\" end=\"0,0\" time=\"150\">Focus</animation>
      </focusedlayout>
      <content>
{chr(10).join(items)}
      </content>
    </control>
    <control type=\"group\"><left>610</left><top>224</top>
      <control type=\"label\"><width>1150</width><height>52</height><font>font45_title</font><label>$INFO[Container(9000).ListItem.Label]</label><textcolor>white</textcolor></control>
      <control type=\"label\"><top>62</top><width>1040</width><height>62</height><font>font14</font><label>Navigate your library, add-ons and settings from one clear horizon.</label><textcolor>FF91A8C0</textcolor><wrapmultiline>true</wrapmultiline></control>
      <control type=\"image\"><top>142</top><width>90</width><height>3</height><texture colordiffuse=\"FF67E8C4\">colors/white.png</texture></control>
    </control>
{''.join(widgets)}
    <control type=\"label\"><left>74</left><bottom>55</bottom><width>1200</width><height>30</height><font>font12</font><label>KODI $INFO[System.BuildVersion]  |  STARLANE MERIDIAN</label><textcolor>FF5F7891</textcolor></control>
  </controls>
</window>
"""


def find_estuary(extracted: Path) -> Path:
    matches = [path for path in extracted.rglob("skin.estuary") if path.is_dir() and (path / "addon.xml").exists()]
    if len(matches) != 1:
        raise SystemExit(f"Expected one skin.estuary directory, found {len(matches)}")
    return matches[0]


def brand_metadata(root: ElementTree.Element) -> None:
    metadata = root.find("extension[@point='xbmc.addon.metadata']")
    if metadata is None:
        raise SystemExit("Upstream skin metadata extension is missing")
    for element in list(metadata):
        if element.tag in {"summary", "description", "disclaimer"}:
            metadata.remove(element)
    source = metadata.find("source")
    if source is not None:
        source.text = "https://github.com/rjclark99/starlanemeridian"
    summary = ElementTree.SubElement(metadata, "summary", {"lang": "en_GB"})
    summary.text = "A calm, modern TV interface built around clear navigation and generous focus states."
    description = ElementTree.SubElement(metadata, "description", {"lang": "en_GB"})
    description.text = "Starlane Meridian is a branded Kodi skin based on Team Kodi's Estuary, retaining complete system-window compatibility while introducing a minimalist celestial-navigation home experience."


def apply_brand_assets(staged: Path, branding: Path) -> None:
    emblem = branding / "starlane-meridian-emblem-v2.png"
    background = branding / "starlane-meridian-home-1920x1080.jpg"
    if not emblem.is_file() or not background.is_file():
        raise SystemExit("Brand emblem and home background must be generated before building the skin")
    brand_media = staged / "media" / "brand"
    brand_media.mkdir(parents=True, exist_ok=True)
    shutil.copy2(emblem, brand_media / "emblem.png")
    shutil.copy2(background, brand_media / "home.jpg")
    shutil.copy2(emblem, staged / "resources" / "icon.png")
    shutil.copy2(background, staged / "resources" / "fanart.jpg")
    (staged / "colors" / "defaults.xml").write_text("""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<colors>
  <color name=\"primary_background\">FF0A1825</color><color name=\"secondary_background\">66102A42</color>
  <color name=\"dialog_tint\">FF081522</color><color name=\"background\">FF050B14</color><color name=\"bg_image\">FF90A6BC</color>
  <color name=\"bg_overlay\">24000000</color><color name=\"black\">FF000000</color><color name=\"white\">FFF4FAFF</color>
  <color name=\"grey\">FF91A8C0</color><color name=\"blue\">FF61C8FF</color><color name=\"red\">FFFF7B72</color>
  <color name=\"button_focus\">FF61C8FF</color><color name=\"button_alt_focus\">8061C8FF</color><color name=\"text_shadow\">44000000</color>
  <color name=\"border_alpha\">5261C8FF</color><color name=\"disabled\">40FFFFFF</color><color name=\"selected\">FF67E8C4</color><color name=\"invalid\">FFFF7B72</color>
</colors>
""", encoding="utf-8")


def build(archive: Path, manifest_path: Path, output: Path, version: str, branding: Path) -> None:
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
        staged = temporary / SKIN_ID
        shutil.copytree(upstream, staged)
        addon_path = staged / "addon.xml"
        root = ElementTree.parse(addon_path).getroot()
        root.attrib.update({"id": SKIN_ID, "name": SKIN_NAME, "version": version, "provider-name": "Starlane Meridian; based on Team Kodi Estuary"})
        brand_metadata(root)
        ElementTree.indent(root)
        addon_path.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + ElementTree.tostring(root, encoding="unicode") + "\n", encoding="utf-8")
        (staged / "xml" / "Home.xml").write_text(home_xml(manifest["skin"]["homeMenu"]), encoding="utf-8")
        apply_brand_assets(staged, branding)
        output.mkdir(parents=True, exist_ok=True)
        destination = output / f"{SKIN_ID}-{version}.zip"
        safe_zip_tree(staged, destination, SKIN_ID)
        print(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream-archive", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--version", default="1.0.0")
    parser.add_argument("--branding", type=Path, default=Path(__file__).resolve().parents[1] / "assets" / "branding")
    args = parser.parse_args()
    build(args.upstream_archive, args.manifest, args.output, args.version, args.branding)

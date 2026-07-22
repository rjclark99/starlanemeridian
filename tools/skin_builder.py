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
SKIN_VERSION = "1.2.2"
WINDOWS = {
    "home": "Home",
    "videos": "Videos",
    "tvshows": "Videos,tvshowtitles",
    "movies": "Videos,movietitles",
    "live-tv": "TVChannels",
    "kids-family": "Videos,special://skin/playlists/meridian_family_movies.xsp,return",
    "addons": "AddonBrowser",
    "settings": "Settings",
    "music": "Music",
    "pictures": "Pictures",
    "favourites": "Favourites",
}

ALLOWED_WIDGET_PROVIDERS = {
    "special://skin/playlists/inprogress_movies.xsp",
    "special://skin/playlists/recent_unwatched_movies.xsp",
    "special://skin/playlists/recent_unwatched_episodes.xsp",
    "special://skin/playlists/unwatched_tvshows.xsp",
    "special://skin/playlists/meridian_family_movies.xsp",
    "special://skin/playlists/meridian_family_tvshows.xsp",
    "pvr://channels/tv/*",
}

SECTION_DESCRIPTIONS = {
    "home": "Resume what you started and discover the newest additions to your library.",
    "tv-shows": "Continue through recent episodes and browse series waiting in your library.",
    "movies": "Pick up a film in progress or choose from your latest movie additions.",
    "live-tv": "Open the channel list supplied by your configured Kodi PVR service.",
    "kids-family": "A calm, dedicated route to Family and Animation titles in your library.",
}


def action(value: dict) -> str:
    kind, target = value["type"], value["target"]
    if kind == "kodi-window":
        if target == "search":
            return "ActivateWindow(Videos,plugin://plugin.video.themoviedb.helper/?info=search,return)"
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


def onclick_markup(value: dict) -> str:
    """Compile a closed set of actions; search degrades safely when helpers are absent."""
    if value["type"] == "kodi-window" and value["target"] == "search":
        return """<onclick condition="System.HasAddon(plugin.video.themoviedb.helper)">ActivateWindow(Videos,plugin://plugin.video.themoviedb.helper/?info=search,return)</onclick>
            <onclick condition="!System.HasAddon(plugin.video.themoviedb.helper) + System.HasAddon(script.globalsearch)">RunAddon(script.globalsearch)</onclick>
            <onclick condition="!System.HasAddon(plugin.video.themoviedb.helper) + !System.HasAddon(script.globalsearch)">Notification(Starlane Meridian,Install TMDb Helper for search,5000)</onclick>"""
    return f"<onclick>{html.escape(action(value))}</onclick>"


def _widget_xml(menu_id: str, widget: dict, control_id: int, top: int, previous_id: int | None, next_id: int | None) -> str:
    provider = widget["provider"]
    if provider not in ALLOWED_WIDGET_PROVIDERS:
        raise SystemExit(f"Unsupported widget provider: {provider}")
    up = previous_id or 9000
    down = next_id or control_id
    target = "tvchannels" if provider.startswith("pvr://") else "videos"
    return f"""
      <control type="group">
        <visible>String.IsEqual(Container(9000).ListItem.Property(MenuId),{html.escape(menu_id)})</visible>
        <left>432</left><top>{top}</top>
        <control type="label"><left>0</left><top>0</top><width>1398</width><height>42</height><font>Meridian_Section</font><label>{html.escape(widget['label'])}</label><textcolor>FFF4FAFF</textcolor></control>
        <control type="fixedlist" id="{control_id}">
          <left>-10</left><top>46</top><width>1450</width><height>170</height><orientation>horizontal</orientation><scrolltime>180</scrolltime><preloaditems>1</preloaditems>
          <onleft>9000</onleft><onup>{up}</onup><ondown>{down}</ondown>
          <itemlayout width="270" height="166">
            <control type="image"><left>10</left><top>6</top><width>250</width><height>120</height><aspectratio align="center" aligny="center">scale</aspectratio><texture fallback="DefaultVideo.png">$INFO[ListItem.Art(fanart)]</texture></control>
            <control type="image"><left>10</left><top>6</top><width>250</width><height>120</height><texture colordiffuse="26050B14">colors/white.png</texture></control>
            <control type="textbox"><left>10</left><top>130</top><width>250</width><height>34</height><font>Meridian_Card</font><label>$INFO[ListItem.Label]</label><textcolor>FFB6C7D8</textcolor><aligny>top</aligny><autoscroll>false</autoscroll></control>
          </itemlayout>
          <focusedlayout width="270" height="166">
            <control type="image"><left>4</left><top>0</top><width>262</width><height>132</height><texture colordiffuse="FF61C8FF">colors/white.png</texture></control>
            <control type="image"><left>10</left><top>6</top><width>250</width><height>120</height><aspectratio align="center" aligny="center">scale</aspectratio><texture fallback="DefaultVideo.png">$INFO[ListItem.Art(fanart)]</texture></control>
            <control type="image"><left>10</left><top>6</top><width>250</width><height>120</height><texture colordiffuse="18050B14">colors/white.png</texture></control>
            <control type="textbox"><left>10</left><top>130</top><width>250</width><height>34</height><font>Meridian_CardFocus</font><label>$INFO[ListItem.Label]</label><textcolor>FFF4FAFF</textcolor><aligny>top</aligny><autoscroll>false</autoscroll></control>
            <animation effect="zoom" start="96" end="100" center="135,66" time="150">Focus</animation>
          </focusedlayout>
          <content target="{target}" limit="{widget['limit']}" browse="never">{html.escape(provider)}</content>
        </control>
        <control type="label"><visible>Integer.IsEqual(Container({control_id}).NumItems,0)</visible><left>0</left><top>68</top><width>900</width><height>44</height><font>Meridian_Body</font><label>No items available yet</label><textcolor>FF607991</textcolor></control>
      </control>"""


def home_xml(menu: list[dict]) -> str:
    items = []
    widgets = []
    backdrops = []
    hero_details = []
    first_widget_ids: dict[str, int] = {}
    for index, item in enumerate(menu):
        widget_ids = [9100 + index * 10 + widget_index for widget_index, _ in enumerate(item["widgets"])]
        if widget_ids:
            first_widget_ids[item["id"]] = widget_ids[0]
        items.append(f"""          <item id=\"{index + 1}\"><label>{html.escape(item['label'])}</label>{onclick_markup(item['action'])}<property name=\"MenuId\">{html.escape(item['id'])}</property></item>""")
        for widget_index, widget in enumerate(item["widgets"]):
            control_id = widget_ids[widget_index]
            widgets.append(_widget_xml(item["id"], widget, control_id, 580 + widget_index * 215,
                                       widget_ids[widget_index - 1] if widget_index else None,
                                       widget_ids[widget_index + 1] if widget_index + 1 < len(widget_ids) else None))
        if widget_ids:
            first = widget_ids[0]
            backdrops.append(f"""
    <control type="image"><visible>String.IsEqual(Container(9000).ListItem.Property(MenuId),{html.escape(item['id'])}) + !String.IsEmpty(Container({first}).ListItem.Art(fanart))</visible><left>650</left><top>0</top><width>1270</width><height>650</height><aspectratio align="right" aligny="top">scale</aspectratio><texture background="true">$INFO[Container({first}).ListItem.Art(fanart)]</texture><fadetime>250</fadetime></control>""")
            description = SECTION_DESCRIPTIONS.get(item["id"], "Browse this section of your Kodi library.")
            hero_details.append(f"""
      <control type="group"><visible>String.IsEqual(Container(9000).ListItem.Property(MenuId),{html.escape(item['id'])}) + Integer.IsGreater(Container({first}).NumItems,0)</visible>
        <control type="textbox"><left>0</left><top>0</top><width>970</width><height>116</height><font>Meridian_Hero</font><label>$INFO[Container({first}).ListItem.Title,{html.escape(item['label'])}: ]</label><textcolor>FFF4FAFF</textcolor><aligny>bottom</aligny><autoscroll>false</autoscroll></control>
        <control type="label"><left>0</left><top>122</top><width>950</width><height>32</height><font>Meridian_Meta</font><label>$INFO[Container({first}).ListItem.Year]  $INFO[Container({first}).ListItem.Duration]  $INFO[Container({first}).ListItem.Genre]</label><textcolor>FF67E8C4</textcolor></control>
        <control type="textbox"><left>0</left><top>164</top><width>930</width><height>98</height><font>Meridian_Body</font><label>$INFO[Container({first}).ListItem.Plot]</label><textcolor>FFB6C7D8</textcolor><aligny>top</aligny><autoscroll>false</autoscroll></control>
      </control>
      <control type="group"><visible>String.IsEqual(Container(9000).ListItem.Property(MenuId),{html.escape(item['id'])}) + Integer.IsEqual(Container({first}).NumItems,0)</visible>
        <control type="label"><left>0</left><top>34</top><width>970</width><height>72</height><font>Meridian_Hero</font><label>{html.escape(item['label'])}</label><textcolor>FFF4FAFF</textcolor></control>
        <control type="textbox"><left>0</left><top>128</top><width>900</width><height>98</height><font>Meridian_Body</font><label>{html.escape(description)}</label><textcolor>FFB6C7D8</textcolor><autoscroll>false</autoscroll></control>
      </control>""")
        else:
            hero_details.append(f"""
      <control type="group"><visible>String.IsEqual(Container(9000).ListItem.Property(MenuId),{html.escape(item['id'])})</visible>
        <control type="label"><left>0</left><top>36</top><width>970</width><height>72</height><font>Meridian_Hero</font><label>{html.escape(item['label'])}</label><textcolor>FFF4FAFF</textcolor></control>
        <control type="textbox"><left>0</left><top>130</top><width>900</width><height>98</height><font>Meridian_Body</font><label>Search your library and online catalogue. TMDb Helper is used when installed; Global Search is the lightweight fallback.</label><textcolor>FFB6C7D8</textcolor><autoscroll>false</autoscroll></control>
      </control>""")
    nav_right = "\n".join(
        f"      <onright condition=\"String.IsEqual(Container(9000).ListItem.Property(MenuId),{html.escape(menu_id)})\">{control_id}</onright>"
        for menu_id, control_id in first_widget_ids.items()
    )
    return f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<window>
  <defaultcontrol always=\"true\">9000</defaultcontrol>
  <menucontrol>9050</menucontrol>
  <backgroundcolor>FF050B14</backgroundcolor>
  <animation effect=\"fade\" start=\"0\" end=\"100\" time=\"220\">WindowOpen</animation>
  <animation effect=\"fade\" start=\"100\" end=\"0\" time=\"150\">WindowClose</animation>
  <controls>
    <control type=\"image\"><left>0</left><top>0</top><width>1920</width><height>1080</height><aspectratio>scale</aspectratio><texture background=\"true\">brand/horizon.png</texture></control>
{''.join(backdrops)}
    <control type=\"image\"><left>0</left><top>0</top><width>1920</width><height>1080</height><texture colordiffuse=\"9E050B14\">colors/white.png</texture></control>
    <control type=\"image\"><left>0</left><top>520</top><width>1920</width><height>560</height><texture colordiffuse=\"D9050B14\">colors/white.png</texture></control>
    <control type=\"image\"><left>58</left><top>46</top><width>66</width><height>66</height><aspectratio>keep</aspectratio><texture>brand/emblem.png</texture></control>
    <control type=\"label\"><left>142</left><top>48</top><width>720</width><height>38</height><font>Meridian_Wordmark</font><label>STARLANE MERIDIAN</label><textcolor>FFF4FAFF</textcolor></control>
    <control type=\"label\"><left>144</left><top>87</top><width>620</width><height>28</height><font>Meridian_Meta</font><label>YOUR MEDIA. ON COURSE.</label><textcolor>FF67E8C4</textcolor></control>
    <control type=\"label\"><right>62</right><top>50</top><width>390</width><height>40</height><align>right</align><font>Meridian_Clock</font><label>$INFO[System.Time]</label><textcolor>FFF4FAFF</textcolor></control>
    <control type=\"label\"><right>64</right><top>91</top><width>390</width><height>26</height><align>right</align><font>Meridian_Meta</font><label>$INFO[System.Date]</label><textcolor>FF91A8C0</textcolor></control>
    <control type=\"image\"><left>58</left><top>170</top><width>338</width><height>810</height><texture colordiffuse=\"9C081522\" border=\"18\">buttons/button-fo.png</texture></control>
    <control type=\"list\" id=\"9000\"><left>74</left><top>190</top><width>314</width><height>418</height><orientation>vertical</orientation><scrolltime>150</scrolltime>
{nav_right}
      <ondown>9050</ondown>
      <itemlayout width=\"314\" height=\"68\">
        <control type=\"label\"><left>28</left><top>5</top><width>266</width><height>58</height><font>Meridian_Nav</font><label>$INFO[ListItem.Label]</label><textcolor>FFF4FAFF</textcolor><aligny>center</aligny><scroll>false</scroll></control>
      </itemlayout>
      <focusedlayout width=\"314\" height=\"68\">
        <control type=\"image\"><left>0</left><top>4</top><width>306</width><height>60</height><texture colordiffuse=\"F2F4FAFF\">colors/white.png</texture></control>
        <control type=\"image\"><left>0</left><top>15</top><width>5</width><height>38</height><texture colordiffuse=\"FF67E8C4\">colors/white.png</texture></control>
        <control type=\"label\"><left>28</left><top>5</top><width>266</width><height>58</height><font>Meridian_NavFocus</font><label>$INFO[ListItem.Label]</label><textcolor>FF07111F</textcolor><aligny>center</aligny><scroll>false</scroll></control>
        <animation effect=\"slide\" start=\"-6,0\" end=\"0,0\" time=\"140\">Focus</animation>
      </focusedlayout>
      <content>
{chr(10).join(items)}
      </content>
    </control>
    <control type=\"image\"><left>90</left><top>620</top><width>274</width><height>1</height><texture colordiffuse=\"5261C8FF\">colors/white.png</texture></control>
    <control type=\"label\"><left>102</left><top>632</top><width>250</width><height>24</height><font>Meridian_Utility</font><label>QUICK ACCESS</label><textcolor>FF91A8C0</textcolor></control>
    <control type=\"button\" id=\"9050\"><left>90</left><top>662</top><width>274</width><height>48</height><font>Meridian_Utility</font><label>FAVOURITES</label><align>left</align><aligny>center</aligny><textoffsetx>18</textoffsetx><textcolor>FFF4FAFF</textcolor><focusedcolor>FF07111F</focusedcolor><texturefocus colordiffuse=\"F2F4FAFF\">colors/white.png</texturefocus><texturenofocus /><onup>9000</onup><ondown>9051</ondown><onright>9000</onright><onclick>ActivateWindow(FavouritesBrowser)</onclick></control>
    <control type=\"button\" id=\"9051\"><left>90</left><top>720</top><width>274</width><height>48</height><font>Meridian_Utility</font><label>ADD-ONS</label><align>left</align><aligny>center</aligny><textoffsetx>18</textoffsetx><textcolor>FFF4FAFF</textcolor><focusedcolor>FF07111F</focusedcolor><texturefocus colordiffuse=\"F2F4FAFF\">colors/white.png</texturefocus><texturenofocus /><onup>9050</onup><ondown>9052</ondown><onright>9000</onright><onclick>ActivateWindow(AddonBrowser)</onclick></control>
    <control type=\"button\" id=\"9052\"><left>90</left><top>778</top><width>274</width><height>48</height><font>Meridian_Utility</font><label>PROFILES</label><align>left</align><aligny>center</aligny><textoffsetx>18</textoffsetx><textcolor>FFF4FAFF</textcolor><focusedcolor>FF07111F</focusedcolor><texturefocus colordiffuse=\"F2F4FAFF\">colors/white.png</texturefocus><texturenofocus /><onup>9051</onup><ondown>9053</ondown><onright>9000</onright><onclick>ActivateWindow(Profiles)</onclick></control>
    <control type=\"button\" id=\"9053\"><left>90</left><top>836</top><width>274</width><height>48</height><font>Meridian_Utility</font><label>SETTINGS</label><align>left</align><aligny>center</aligny><textoffsetx>18</textoffsetx><textcolor>FFF4FAFF</textcolor><focusedcolor>FF07111F</focusedcolor><texturefocus colordiffuse=\"F2F4FAFF\">colors/white.png</texturefocus><texturenofocus /><onup>9052</onup><ondown>9054</ondown><onright>9000</onright><onclick>ActivateWindow(Settings)</onclick></control>
    <control type=\"button\" id=\"9054\"><left>90</left><top>894</top><width>274</width><height>48</height><font>Meridian_Utility</font><label>POWER</label><align>left</align><aligny>center</aligny><textoffsetx>18</textoffsetx><textcolor>FFF4FAFF</textcolor><focusedcolor>FF07111F</focusedcolor><texturefocus colordiffuse=\"F2F4FAFF\">colors/white.png</texturefocus><texturenofocus /><onup>9053</onup><ondown>9000</ondown><onright>9000</onright><onclick>ActivateWindow(ShutdownMenu)</onclick></control>
    <control type=\"group\"><left>432</left><top>220</top><width>1000</width><height>300</height>
{''.join(hero_details)}
    </control>
{''.join(widgets)}
    <control type=\"group\"><visible>Player.HasMedia</visible><left>432</left><top>968</top><width>1426</width><height>76</height>
      <control type=\"image\"><left>0</left><top>0</top><width>1426</width><height>76</height><texture colordiffuse=\"E6081522\">colors/white.png</texture></control>
      <control type=\"image\"><left>10</left><top>8</top><width>96</width><height>60</height><aspectratio align=\"center\">scale</aspectratio><texture fallback=\"DefaultVideo.png\">$INFO[Player.Art(thumb)]</texture></control>
      <control type=\"label\"><left>124</left><top>8</top><width>720</width><height>30</height><font>Meridian_CardFocus</font><label>$INFO[Player.Title]</label><textcolor>FFF4FAFF</textcolor><scroll>false</scroll></control>
      <control type=\"label\"><left>124</left><top>40</top><width>720</width><height>24</height><font>Meridian_Utility</font><label>$INFO[Player.Artist]$INFO[Player.TVShowTitle,  ·  ]</label><textcolor>FF91A8C0</textcolor><scroll>false</scroll></control>
      <control type=\"progress\"><left>880</left><top>29</top><width>330</width><height>10</height><info>Player.Progress</info></control>
      <control type=\"label\"><right>20</right><top>18</top><width>176</width><height>34</height><align>right</align><font>Meridian_Utility</font><label>$INFO[Player.Time] / $INFO[Player.Duration]</label><textcolor>FFF4FAFF</textcolor></control>
    </control>
    <control type=\"label\"><visible>!Player.HasMedia</visible><left>62</left><bottom>34</bottom><width>830</width><height>26</height><font>Meridian_Meta</font><label>KODI $INFO[System.BuildVersion]  ·  STARLANE MERIDIAN</label><textcolor>FF607991</textcolor></control>
    <control type=\"label\"><visible>!Player.HasMedia</visible><right>62</right><bottom>34</bottom><width>720</width><height>26</height><align>right</align><font>Meridian_Meta</font><label>OK SELECTS  ·  BACK RETURNS  ·  MENU OPENS QUICK ACCESS</label><textcolor>FF607991</textcolor></control>
  </controls>
</window>
"""


def startup_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<window>
  <onload>AlarmClock(StarlaneMeridianStartup,ReplaceWindow($INFO[System.StartupWindow]),00:02,silent)</onload>
  <backgroundcolor>FF050B14</backgroundcolor>
  <controls>
    <control type="image"><left>0</left><top>0</top><width>1920</width><height>1080</height><aspectratio>scale</aspectratio><texture>brand/horizon.png</texture></control>
    <control type="image"><left>0</left><top>0</top><width>1920</width><height>1080</height><texture colordiffuse="78050B14">colors/white.png</texture></control>
    <control type="image"><left>820</left><top>328</top><width>280</width><height>280</height><aspectratio>keep</aspectratio><texture>brand/emblem.png</texture><animation effect="fade" start="0" end="100" time="500">WindowOpen</animation></control>
    <control type="label"><left>460</left><top>634</top><width>1000</width><height>64</height><align>center</align><font>Meridian_Splash</font><label>STARLANE MERIDIAN</label><textcolor>FFF4FAFF</textcolor><animation effect="fade" start="0" end="100" delay="160" time="500">WindowOpen</animation></control>
    <control type="image"><left>820</left><top>718</top><width>280</width><height>3</height><texture colordiffuse="FF67E8C4">colors/white.png</texture></control>
    <control type="label"><left>560</left><top>748</top><width>800</width><height>34</height><align>center</align><font>Meridian_Meta</font><label>YOUR MEDIA. ON COURSE.</label><textcolor>FF91A8C0</textcolor></control>
  </controls>
</window>
"""


def power_dialog_xml() -> str:
    """Render Kodi's platform-aware power actions in an original Meridian dialog."""
    items = (
        ("$LOCALIZE[13012]", "Quit()", "System.ShowExitButton"),
        ("$LOCALIZE[13016]", "Powerdown()", "System.CanPowerDown"),
        ("$LOCALIZE[20150]", "AlarmClock(shutdowntimer,Shutdown())", "!System.HasAlarm(shutdowntimer) + [System.CanPowerDown | System.CanSuspend | System.CanHibernate]"),
        ("$LOCALIZE[20151] $INFO[System.AlarmPos,(,)]", "CancelAlarm(shutdowntimer)", "System.HasAlarm(shutdowntimer)"),
        ("$LOCALIZE[13011]", "Suspend()", "System.CanSuspend"),
        ("$LOCALIZE[13010]", "Hibernate()", "System.CanHibernate"),
        ("$LOCALIZE[13013]", "Reset()", "System.CanReboot"),
        ("$LOCALIZE[20126] $INFO[System.ProfileName]", "System.LogOff", "[System.HasLoginScreen | Integer.IsGreater(System.ProfileCount,1)] + System.Loggedon"),
        ("$VAR[MasterModeLabel]", "Mastermode", "System.HasLocks"),
        ("$LOCALIZE[13017]", "InhibitIdleShutdown(true)", "System.HasShutdown + !System.IdleShutdownInhibited"),
        ("$LOCALIZE[13018]", "InhibitIdleShutdown(false)", "System.HasShutdown + System.IdleShutdownInhibited"),
    )
    content = "\n".join(
        f"        <item><label>{label}</label><onclick>{html.escape(command)}</onclick><visible>{html.escape(visible)}</visible></item>"
        for label, command, visible in items
    )
    return f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<window type=\"dialog\">
  <defaultcontrol always=\"true\">9000</defaultcontrol>
  <backgroundcolor>00000000</backgroundcolor>
  <animation effect=\"fade\" start=\"0\" end=\"100\" time=\"140\">WindowOpen</animation>
  <animation effect=\"fade\" start=\"100\" end=\"0\" time=\"110\">WindowClose</animation>
  <controls>
    <control type=\"image\"><left>0</left><top>0</top><width>1920</width><height>1080</height><texture colordiffuse=\"B8050B14\">colors/white.png</texture></control>
    <control type=\"group\"><left>610</left><top>250</top><width>700</width><height>580</height>
      <control type=\"image\"><left>0</left><top>0</top><width>700</width><height>580</height><texture colordiffuse=\"F2081522\" border=\"20\">buttons/button-fo.png</texture></control>
      <control type=\"image\"><left>0</left><top>0</top><width>700</width><height>4</height><texture colordiffuse=\"FF67E8C4\">colors/white.png</texture></control>
      <control type=\"image\"><left>42</left><top>34</top><width>64</width><height>64</height><aspectratio>keep</aspectratio><texture>brand/emblem.png</texture></control>
      <control type=\"label\"><left>128</left><top>38</top><width>510</width><height>50</height><font>Meridian_Section</font><label>POWER &amp; SESSION</label><textcolor>FFF4FAFF</textcolor><aligny>center</aligny></control>
      <control type=\"label\"><left>42</left><top>108</top><width>616</width><height>30</height><font>Meridian_Utility</font><label>Available actions depend on this device</label><textcolor>FF91A8C0</textcolor></control>
      <control type=\"panel\" id=\"9000\"><left>42</left><top>154</top><width>616</width><height>356</height><orientation>vertical</orientation><scrolltime>100</scrolltime>
        <itemlayout width=\"616\" height=\"64\"><control type=\"label\"><left>24</left><top>5</top><width>568</width><height>54</height><font>Meridian_Body</font><label>$INFO[ListItem.Label]</label><textcolor>FFF4FAFF</textcolor><aligny>center</aligny><scroll>false</scroll></control></itemlayout>
        <focusedlayout width=\"616\" height=\"64\"><control type=\"image\"><left>0</left><top>4</top><width>616</width><height>56</height><texture colordiffuse=\"F2F4FAFF\">colors/white.png</texture></control><control type=\"image\"><left>0</left><top>14</top><width>5</width><height>36</height><texture colordiffuse=\"FF67E8C4\">colors/white.png</texture></control><control type=\"label\"><left>24</left><top>5</top><width>568</width><height>54</height><font>Meridian_CardFocus</font><label>$INFO[ListItem.Label]</label><textcolor>FF07111F</textcolor><aligny>center</aligny><scroll>false</scroll></control></focusedlayout>
        <content>
{content}
        </content>
      </control>
      <control type=\"label\"><left>42</left><bottom>20</bottom><width>616</width><height>24</height><font>Meridian_Utility</font><label>BACK  ·  CLOSE</label><textcolor>FF607991</textcolor><align>right</align></control>
    </control>
  </controls>
</window>
"""


def apply_brand_fonts(path: Path) -> None:
    root = ElementTree.parse(path).getroot()
    specifications = (
        ("Meridian_Meta", 18, False), ("Meridian_Card", 20, False), ("Meridian_CardFocus", 20, True),
        ("Meridian_Body", 24, False), ("Meridian_Nav", 28, False), ("Meridian_NavFocus", 28, True),
        ("Meridian_Section", 26, True), ("Meridian_Wordmark", 30, True), ("Meridian_Clock", 32, False),
        ("Meridian_Hero", 52, True), ("Meridian_Splash", 46, True), ("Meridian_Utility", 17, True),
    )
    for fontset in root.findall("fontset"):
        filename = "arial.ttf" if fontset.attrib.get("id") == "Arial" else "NotoSans-Regular.ttf"
        for name, size, bold in specifications:
            node = ElementTree.SubElement(fontset, "font")
            ElementTree.SubElement(node, "name").text = name
            ElementTree.SubElement(node, "filename").text = filename
            ElementTree.SubElement(node, "size").text = str(size)
            if bold:
                ElementTree.SubElement(node, "style").text = "bold"
    ElementTree.indent(root)
    path.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + ElementTree.tostring(root, encoding="unicode") + "\n", encoding="utf-8")


def apply_family_playlists(staged: Path) -> None:
    playlists = staged / "playlists"
    playlists.joinpath("meridian_family_movies.xsp").write_text("""<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<smartplaylist type="movies"><name>Kids &amp; Family Movies</name><match>one</match><rule field="genre" operator="contains"><value>Family</value></rule><rule field="genre" operator="contains"><value>Animation</value></rule><limit>30</limit><order direction="descending">dateadded</order></smartplaylist>
""", encoding="utf-8")
    playlists.joinpath("meridian_family_tvshows.xsp").write_text("""<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<smartplaylist type="tvshows"><name>Kids &amp; Family TV</name><match>one</match><rule field="genre" operator="contains"><value>Family</value></rule><rule field="genre" operator="contains"><value>Animation</value></rule><limit>30</limit><order direction="descending">dateadded</order></smartplaylist>
""", encoding="utf-8")


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
    horizon = branding / "starlane-meridian-horizon.png"
    if not emblem.is_file() or not background.is_file() or not horizon.is_file():
        raise SystemExit("Brand emblem, fanart, and horizon artwork must be generated before building the skin")
    brand_media = staged / "media" / "brand"
    brand_media.mkdir(parents=True, exist_ok=True)
    shutil.copy2(emblem, brand_media / "emblem.png")
    shutil.copy2(background, brand_media / "home.jpg")
    shutil.copy2(horizon, brand_media / "horizon.png")
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
        (staged / "xml" / "Startup.xml").write_text(startup_xml(), encoding="utf-8")
        (staged / "xml" / "DialogButtonMenu.xml").write_text(power_dialog_xml(), encoding="utf-8")
        apply_brand_fonts(staged / "xml" / "Font.xml")
        apply_family_playlists(staged)
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
    parser.add_argument("--version", default=SKIN_VERSION)
    parser.add_argument("--branding", type=Path, default=Path(__file__).resolve().parents[1] / "assets" / "branding")
    args = parser.parse_args()
    build(args.upstream_archive, args.manifest, args.output, args.version, args.branding)

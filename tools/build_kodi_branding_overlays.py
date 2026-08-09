#!/usr/bin/env python3
"""Build a Starlane-branded copy of the Umbrella Kodi provider add-on.

The add-on IDs, routes, settings keys, Python identifiers, and upstream licences stay
unchanged. Only user-facing metadata, human-readable brand strings, and declared
artwork are replaced.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import shutil
import stat
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "assets" / "branding"
CANONICAL_PROVIDER_ARTWORK = BRAND / "provider-overlay"
MINT = "ff67e8c4"
VISIBLE_BRAND = re.compile(r"(?<![A-Za-z0-9_])(?:Umbrella|UMBRELLA)(?![A-Za-z0-9_])")
PROVIDER_ARTWORK_THEME = "starlane movies"
UPSTREAM_ARTWORK_THEME = "umbrella"
GLOBAL_PROVIDER_ARTWORK = frozenset({"banner.png", "fanart.jpg", "icon.png"})
DIRECTORY_LOGO_RESOURCE = "resource.images.studios.coloured"
DIRECTORY_LOGO_TUPLE = re.compile(
    r"\('(?P<name>[^']+)', ?'(?P<tmdb_id>\d+)', ?'https?://[^']+'\)"
)
DIRECTORY_LOGO_MINIMUM = 100
DIRECTORY_LOGO_HOSTS = ("i.imgur.com", "i.postimg.cc")
ABSOLUTE_ARTWORK_URI_PREFIXES = ("resource://", "special://", "https://", "http://")
# Display names whose logo ships under a different texture name in the locked
# resource.images.studios.coloured 0.0.24 bundle.
DIRECTORY_LOGO_ALIASES = {
    "BET+": "BET",
    "City (CA)": "City",
    "CW Seed": "CW",
    "Fearnet": "Fear Net",
    "Hallmark Movies & Mysteries": "Hallmark",
    "History Channel": "History",
    "Reelz": "ReelzChannel",
    "Showcase (AU)": "Showcase",
    "Smithsonian": "Smithsonian Channel",
}
# Display names with no logo in that bundle. They deliberately resolve to a
# missing texture so the skin's own card fallback renders, which keeps every
# directory logo local instead of reaching a third-party host for these ten.
DIRECTORY_LOGO_UNAVAILABLE = frozenset({
    "Brat", "CuriosityStream", "Discovery ID", "Disney Junior", "Fusion",
    "H2", "Motor Trend", "OWN", "TruTV", "TV One",
})
PORTABLE_TEXT_SUFFIXES = frozenset({
    ".css", ".html", ".ini", ".js", ".json", ".md", ".po", ".properties",
    ".py", ".txt", ".xml",
})


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
        branded_version="6.7.81.5",
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
    router = addon_root / "resources/lib/modules/router.py"
    if router.is_file():
        text = router.read_text(encoding="utf-8-sig")
        text = text.replace(
            "from resources.lib.modules import changelog\n"
            "            changelog.get('Umbrella')",
            "# The Starlane bootstrap owns first-run presentation; keep the changelog manual.",
        )
        router.write_text(text, encoding="utf-8", newline="")
    service = addon_root / "service.py"
    if service.is_file():
        text = service.read_text(encoding="utf-8-sig")
        upstream_repository_probe = (
            "\tif len(str(control.getUmbrellaVersion())) > 6:\n"
            "\t\trepoVersion = control.addon('repository.umbrellakodi').getAddonInfo('version')\n"
            "\t\trepoName = 'repository.umbrellakodi'\n"
            "\t\ttestUmbrella = True\n"
            "\telse:\n"
            "\t\ttry:\n"
            "\t\t\trepoVersion = control.addon('repository.umbrella').getAddonInfo('version')\n"
            "\t\t\trepoName = 'repository.umbrella'\n"
            "\t\texcept Exception:\n"
            "\t\t\trepoVersion = 'unknown'\n"
            "\t\t\trepoName = 'Unknown Repo'"
        )
        if upstream_repository_probe not in text:
            raise ValueError(f"{service}: expected upstream repository-version probe")
        text = text.replace(
            upstream_repository_probe,
            "\trepoVersion = 'managed'\n"
            "\trepoName = 'Starlane package lock'",
        )
        upstream_update_check = (
            "\t\tif control.setting('general.checkAddonUpdates') == 'true':\n"
            "\t\t\tAddonCheckUpdate().run()"
        )
        if upstream_update_check not in text:
            raise ValueError(f"{service}: expected upstream automatic update check")
        text = text.replace(
            upstream_update_check,
            "\t\t# The signed Starlane package lock exclusively owns provider updates.",
        )
        # Bootstrap defers Home activation until this property appears, so a silently
        # missed injection would strand every install. Fail the build instead.
        upstream_service_entry = "def main():\n\twhile not control.monitor.abortRequested():"
        if upstream_service_entry not in text:
            raise ValueError(f"{service}: expected upstream service entry point")
        text = text.replace(
            upstream_service_entry,
            "def main():\n"
            "\twindow.clearProperty('starlane.umbrella.ready')\n"
            "\twhile not control.monitor.abortRequested():",
        )
        upstream_account_sync = "\t\tSyncMyAccounts().run()\n\t\tPremAccntNotification().run()"
        if upstream_account_sync not in text:
            raise ValueError(f"{service}: expected upstream account sync sequence")
        text = text.replace(
            upstream_account_sync,
            "\t\tSyncMyAccounts().run()\n"
            "\t\twindow.setProperty('starlane.umbrella.ready', 'true')\n"
            "\t\tPremAccntNotification().run()",
        )
        service.write_text(text, encoding="utf-8", newline="")


def preserve_absolute_directory_artwork(addon_root: Path, addon: AddonBrand) -> None:
    """Keep Kodi resource URIs out of Umbrella's themed artwork directory.

    ``tvshows.addDirectory`` is the consumer that calls ``setArt`` for the
    Networks and Providers rows.  It previously regarded only ``http`` values
    as absolute, turning a local ``resource://`` texture into a non-existent
    path below the selected artwork theme.
    """
    if addon.addon_id != "plugin.video.umbrella":
        return
    tvshows = addon_root / "resources/lib/menus/tvshows.py"
    if not tvshows.is_file():
        return
    text = tvshows.read_text(encoding="utf-8-sig")
    upstream_consumer = (
        "\t\t\t\tif i['image'].startswith('http'): poster = i['image']\n"
        "\t\t\t\telif artPath: poster = control.joinPath(artPath, i['image'])\n"
        "\t\t\t\telse: poster = addonThumb\n"
        "\t\t\t\tif content == 'genres':\n"
        "\t\t\t\t\ticon = control.joinPath(control.genreIconPath(), i['icon']) or 'DefaultFolder.png'\n"
        "\t\t\t\t\tposter = control.joinPath(control.genrePosterPath(), i['image']) or addonThumb\n"
        "\t\t\t\telse:\n"
        "\t\t\t\t\ticon = i['icon']\n"
        "\t\t\t\t\tif icon.startswith('http'): pass\n"
        "\t\t\t\t\telif not icon.startswith('Default'): icon = control.joinPath(artPath, icon)"
    )
    if upstream_consumer not in text:
        raise ValueError(f"{tvshows}: expected directory artwork consumer")
    absolute = repr(ABSOLUTE_ARTWORK_URI_PREFIXES)
    replacement = upstream_consumer.replace(
        "i['image'].startswith('http')", f"i['image'].startswith({absolute})"
    ).replace("icon.startswith('http')", f"icon.startswith({absolute})")
    tvshows.write_text(text.replace(upstream_consumer, replacement), encoding="utf-8", newline="")


def add_tmdb_request_diagnostics(addon_root: Path, addon: AddonBrand) -> None:
    """Add privacy-safe result diagnostics to Umbrella's TMDB HTTP consumer."""
    if addon.addon_id != "plugin.video.umbrella":
        return
    tmdb = addon_root / "resources/lib/indexers/tmdb.py"
    if not tmdb.is_file():
        return
    text = tmdb.read_text(encoding="utf-8-sig")
    import_landmark = "from urllib3.util.retry import Retry\n"
    if import_landmark not in text:
        raise ValueError(f"{tmdb}: expected TMDB retry import")
    text = text.replace(import_landmark, import_landmark + "from urllib.parse import urlsplit\n", 1)
    start = "\tdef get_request(self, url):\n"
    end = "\tdef userlists(self, url):"
    try:
        before, remainder = text.split(start, 1)
        upstream_request, after = remainder.split(end, 1)
    except ValueError as error:
        raise ValueError(f"{tmdb}: expected TMDB get_request consumer") from error
    expected = (
        "\t\ttry:\n\t\t\ttry: response = session.get(url, timeout=20)\n"
        "\t\t\texcept requests.exceptions.SSLError:\n\t\t\t\tresponse = session.get(url, verify=False)\n"
        "\t\texcept requests.exceptions.ConnectionError:\n\t\t\tnotification(message=32024)\n"
        "\t\t\tfrom resources.lib.modules import log_utils\n\t\t\tlog_utils.error()\n\t\t\treturn None\n"
        "\t\ttry:\n\t\t\tif response.status_code in (200, 201): return response.json()\n"
    )
    if not upstream_request.startswith(expected):
        raise ValueError(f"{tmdb}: expected TMDB request response handling")
    diagnostic = (
        "\ndef starlane_provider_request_diagnostic(url, status=None, error=None):\n"
        "\t\"\"\"Record only provider result metadata; never URL query or response data.\"\"\"\n"
        "\ttry:\n\t\tparsed = urlsplit(url)\n\t\thost = parsed.hostname or parsed.scheme\n\t\tif parsed.port: host = '%s:%s' % (host, parsed.port)\n\t\tsegments = (parsed.path or '/').split('/')\n\t\tpath = '/'.join(segment if index <= 1 or not segment.isdigit() else ':id' for index, segment in enumerate(segments))\n"
        "\t\tfrom resources.lib.modules import log_utils\n"
        "\t\tif error is None:\n\t\t\tlevel = log_utils.LOGDEBUG if status in (200, 201) else log_utils.LOGWARNING\n\t\t\tlog_utils.log('Starlane provider request host=%s path=%s status=%s' % (host, path, status), level=level)\n"
        "\t\telse:\n\t\t\tlog_utils.log('Starlane provider request host=%s path=%s exception=%s' % (host, path, type(error).__name__), level=log_utils.LOGWARNING)\n"
        "\texcept Exception:\n\t\tpass\n\n"
    )
    rewritten = upstream_request.replace(
        "\t\ttry:\n\t\t\ttry: response = session.get(url, timeout=20)\n"
        "\t\t\texcept requests.exceptions.SSLError:\n\t\t\t\tresponse = session.get(url, verify=False)\n",
        "\t\ttry:\n\t\t\tresponse = session.get(url, timeout=20)\n",
        1,
    ).replace(
        "\t\texcept requests.exceptions.ConnectionError:\n",
        "\t\texcept requests.exceptions.RequestException as error:\n\t\t\tstarlane_provider_request_diagnostic(url, error=error)\n",
        1,
    ).replace(
        "\t\ttry:\n\t\t\tif response.status_code in (200, 201): return response.json()\n",
        "\t\ttry:\n\t\t\tstarlane_provider_request_diagnostic(url, status=response.status_code)\n\t\t\tif response.status_code in (200, 201): return response.json()\n",
        1,
    ).replace(
        "\t\texcept:\n\t\t\tfrom resources.lib.modules import log_utils\n\t\t\tlog_utils.error()\n\t\t\treturn None",
        "\t\texcept Exception as error:\n\t\t\tstarlane_provider_request_diagnostic(url, error=error)\n\t\t\tfrom resources.lib.modules import log_utils\n\t\t\tlog_utils.error()\n\t\t\treturn None",
        1,
    )
    rewritten_source = before + start + rewritten + end + after
    v4_tls_fallback = (
        "\t\t\ttry: response = session.get(url, headers=headers, timeout=20)\n"
        "\t\t\texcept requests.exceptions.SSLError:\n"
        "\t\t\t\tresponse = session.get(url, headers=headers, verify=False)\n"
    )
    rewritten_source = rewritten_source.replace(
        v4_tls_fallback,
        "\t\t\tresponse = session.get(url, headers=headers, timeout=20)\n",
        1,
    )
    if "verify=False" in rewritten_source:
        raise ValueError(f"{tmdb}: TLS certificate verification bypass remains")
    class_landmark = "\nclass TMDb:\n"
    if class_landmark not in rewritten_source:
        raise ValueError(f"{tmdb}: expected TMDB class")
    rewritten_source = rewritten_source.replace(class_landmark, diagnostic + class_landmark, 1)
    compile(rewritten_source, str(tmdb), "exec")
    tmdb.write_text(rewritten_source, encoding="utf-8", newline="")


def rewrite_discovery_previews(addon_root: Path, addon: AddonBrand) -> None:
    """Keep Umbrella routes intact while making bounded Home previews useful."""
    if addon.addon_id != "plugin.video.umbrella":
        return
    tmdb = addon_root / "resources/lib/indexers/tmdb.py"
    if not tmdb.is_file():
        return
    text = tmdb.read_text(encoding="utf-8-sig")
    network_start = "\tdef get_networks(self):\n\t\treturn ["
    network_end = (
        "\t\t\t('YouTube Premium', '1436', "
        "'https://i.postimg.cc/vHtqdhyt/youtube-premium.png')]"
    )
    if network_start not in text or network_end not in text:
        raise ValueError(f"{tmdb}: expected pinned network directory")
    text = text.replace(network_start, "\tdef get_networks(self):\n\t\tnetworks = [", 1)
    preferred_networks = (
        "ABC (US)", "CBS", "NBC", "FOX", "BBC One", "ITV", "Channel 4",
        "AMC", "HBO", "Discovery Channel", "FX", "Comedy Central",
        "Cartoon Network",
    )
    ordering = (
        network_end
        + "\n\t\tpreferred = "
        + repr(preferred_networks)
        + "\n\t\tby_name = {item[0]: item for item in networks}"
        + "\n\t\treturn [by_name[name] for name in preferred] + "
        + "[item for item in networks if item[0] not in preferred]\n"
    )
    text = text.replace(network_end, ordering, 1)

    originals_start = text.index("\tdef get_originals(self):")
    originals_end = text.index("\n\tdef actorSearch", originals_start)
    originals = (
        "\tdef get_originals(self):\n"
        "\t\treturn [\n"
        "\t\t\t('Netflix', '213', 'https://i.postimg.cc/c4vHp9wV/netflix.png'),\n"
        "\t\t\t('Amazon', '1024', 'https://i.imgur.com/ru9DDlL.png'),\n"
        "\t\t\t('Apple TV+', '2552', 'https://i.imgur.com/fAQMVNp.png'),\n"
        "\t\t\t('Disney+', '2739', 'https://i.postimg.cc/zBNHHbKZ/disney.png'),\n"
        "\t\t\t('Max', '3186', 'https://i.postimg.cc/pLdCcdGt/hbo-max.png'),\n"
        "\t\t\t('Hulu', '453', 'https://i.imgur.com/cLVo7NH.png'),\n"
        "\t\t\t('Paramount+', '4330', 'https://i.postimg.cc/1zTXGsF6/paramountplus.png'),\n"
        "\t\t\t('Peacock', '3353', 'https://i.postimg.cc/76m4v7VW/NBCUniversal-Peacock-Logo.png')]\n"
    )
    text = text[:originals_start] + originals + text[originals_end:]
    tmdb.write_text(text, encoding="utf-8", newline="")


def directory_logo_texture(name: str) -> str:
    """Return the local resource path that renders ``name``'s logo."""
    return "resource://%s/%s.png" % (
        DIRECTORY_LOGO_RESOURCE,
        DIRECTORY_LOGO_ALIASES.get(name, name),
    )


def localise_directory_logo_artwork(addon_root: Path, addon: AddonBrand) -> None:
    """Serve network and provider logos from the locked local resource add-on.

    Upstream pins every logo to ``i.imgur.com`` or ``i.postimg.cc``. Imgur is
    region-blocked in the United Kingdom and answers with a notice image, which
    Kodi then renders in place of the logo; both hosts also disclose the
    television's address on every card render and break the row whenever their
    policy or availability changes. ``resource.images.studios.coloured`` is
    already in the signed package lock, so the same artwork resolves from local
    storage with no network access at all.
    """
    if addon.addon_id != "plugin.video.umbrella":
        return
    tmdb = addon_root / "resources/lib/indexers/tmdb.py"
    if not tmdb.is_file():
        return
    text = tmdb.read_text(encoding="utf-8-sig")
    rewritten = 0

    def localise(match: re.Match[str]) -> str:
        nonlocal rewritten
        rewritten += 1
        name = match.group("name")
        return "('%s', '%s', '%s')" % (
            name,
            match.group("tmdb_id"),
            directory_logo_texture(name),
        )

    text = DIRECTORY_LOGO_TUPLE.sub(localise, text)
    if rewritten < DIRECTORY_LOGO_MINIMUM:
        raise ValueError(
            f"{tmdb}: expected at least {DIRECTORY_LOGO_MINIMUM} pinned directory "
            f"logos, localised {rewritten}"
        )
    remaining = sorted(host for host in DIRECTORY_LOGO_HOSTS if host in text)
    if remaining:
        raise ValueError(f"{tmdb}: third-party logo hosts remain: {', '.join(remaining)}")
    tmdb.write_text(text, encoding="utf-8", newline="")


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


def prepare_artwork_theme(addon_root: Path, addon: AddonBrand) -> None:
    """Vendor functional artwork under the rebranded theme name.

    Umbrella lower-cases the configured theme name before resolving its directory.
    User-facing rebranding therefore has to rename the directory as well as the
    setting value.  The three global brand images are deliberately excluded from
    the inventory because ``replace_artwork`` replaces them with Starlane assets.
    """
    if addon.addon_id != "plugin.video.umbrella":
        return
    artwork_root = addon_root / "resources" / "artwork"
    upstream = artwork_root / UPSTREAM_ARTWORK_THEME
    branded = artwork_root / PROVIDER_ARTWORK_THEME
    if not upstream.is_dir():
        raise FileNotFoundError(upstream)
    if branded.exists():
        raise ValueError(f"{branded}: branded artwork theme already exists")

    functional = {
        path.relative_to(upstream).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(upstream.rglob("*"))
        if path.is_file() and path.relative_to(upstream).as_posix() not in GLOBAL_PROVIDER_ARTWORK
    }
    if not functional:
        raise ValueError(f"{upstream}: no functional provider artwork found")
    upstream.rename(branded)
    inventory = {
        "schema_version": 1,
        "upstream_name": addon.upstream_name,
        "upstream_source": addon.upstream_source,
        "upstream_version": addon.source_version,
        "theme": PROVIDER_ARTWORK_THEME,
        "global_brand_artwork": sorted(GLOBAL_PROVIDER_ARTWORK),
        "functional_artwork_sha256": functional,
    }
    (branded / "ARTWORK_INVENTORY.json").write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="",
    )


def replace_artwork(addon_root: Path, addon: AddonBrand) -> None:
    artwork = {
        name: (CANONICAL_PROVIDER_ARTWORK / name).read_bytes()
        for name in ("icon.png", "fanart.jpg", "banner.png", "circle.png")
    }
    icon_targets = [
        addon_root / "icon.png",
        addon_root / "resources" / "artwork" / "icon.png",
        addon_root / "resources" / "artwork" / PROVIDER_ARTWORK_THEME / "icon.png",
        addon_root / "resources" / "skins" / "Default" / "media" / "common" / "icon.png",
    ]
    fanart_targets = [
        addon_root / "fanart.jpg",
        addon_root / "resources" / "artwork" / PROVIDER_ARTWORK_THEME / "fanart.jpg",
        addon_root / "resources" / "skins" / "Default" / "media" / "common" / "fanart.jpg",
    ]
    for target in icon_targets:
        if target.is_file():
            target.write_bytes(artwork["icon.png"])
    for target in fanart_targets:
        if target.is_file():
            target.write_bytes(artwork["fanart.jpg"])
    banner_target = addon_root / "resources" / "artwork" / PROVIDER_ARTWORK_THEME / "banner.png"
    if banner_target.is_file():
        banner_target.write_bytes(artwork["banner.png"])
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
        circle_target.write_bytes(artwork["circle.png"])


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
    version = ET.parse(addon_root / "addon.xml").getroot().attrib["version"]
    zip_path = output_root / f"{addon_root.name}-{version}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as archive:
        for path in sorted(
            addon_root.rglob("*"),
            key=lambda candidate: candidate.relative_to(addon_root.parent).as_posix(),
        ):
            if path.is_file():
                info = zipfile.ZipInfo(
                    path.relative_to(addon_root.parent).as_posix(),
                    date_time=(2026, 7, 28, 0, 0, 0),
                )
                info.create_system = 3
                info.compress_type = zipfile.ZIP_STORED
                info.external_attr = 0o100644 << 16
                payload = path.read_bytes()
                if path.suffix.lower() in PORTABLE_TEXT_SUFFIXES:
                    payload = payload.replace(b"\r\n", b"\n")
                archive.writestr(info, payload)
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
        rewrite_discovery_previews(target, addon)
        localise_directory_logo_artwork(target, addon)
        preserve_absolute_directory_artwork(target, addon)
        add_tmdb_request_diagnostics(target, addon)
        update_metadata(target, addon)
        prepare_artwork_theme(target, addon)
        replace_artwork(target, addon)
        audit_user_facing(target)
        built.append(package(target, output_root))
    return built


def build_from_archive(
    source_archive: Path,
    expected_sha256: str,
    output_root: Path,
) -> list[Path]:
    actual_sha256 = hashlib.sha256(source_archive.read_bytes()).hexdigest()
    if actual_sha256 != expected_sha256.lower():
        raise ValueError(
            f"{source_archive}: expected SHA-256 {expected_sha256}, found {actual_sha256}"
        )
    with tempfile.TemporaryDirectory() as temp_name:
        source_root = Path(temp_name)
        with zipfile.ZipFile(source_archive) as archive:
            members = archive.infolist()
            roots = {
                member.filename.replace("\\", "/").split("/", 1)[0]
                for member in members
                if member.filename
            }
            if roots != {ADDONS[0].addon_id}:
                raise ValueError("provider ZIP must contain the expected single add-on root")
            for member in members:
                normalized = posixpath.normpath(member.filename.replace("\\", "/"))
                if (
                    normalized == ".."
                    or normalized.startswith("../")
                    or normalized.startswith("/")
                    or stat.S_ISLNK(member.external_attr >> 16)
                ):
                    raise ValueError("provider ZIP contains an unsafe path")
            archive.extractall(source_root)
        return build(source_root, output_root)


def main() -> None:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--source-root", type=Path)
    source.add_argument("--source-archive", type=Path)
    parser.add_argument("--source-sha256")
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    if args.source_archive:
        if not args.source_sha256:
            parser.error("--source-sha256 is required with --source-archive")
        artifacts = build_from_archive(
            args.source_archive.resolve(),
            args.source_sha256,
            args.output_root.resolve(),
        )
    else:
        artifacts = build(args.source_root.resolve(), args.output_root.resolve())
    for artifact in artifacts:
        print(artifact)


if __name__ == "__main__":
    main()

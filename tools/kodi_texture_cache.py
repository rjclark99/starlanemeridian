#!/usr/bin/env python3
"""List or remove exact provider artwork records from a copied Kodi texture DB."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


PROVIDER_IDS = (
    "plugin.video.umbrella",
)


def matching_rows(connection: sqlite3.Connection) -> list[tuple[int, str, str]]:
    condition = " OR ".join("lower(url) LIKE ?" for _ in PROVIDER_IDS)
    values = tuple(f"%{addon_id}%" for addon_id in PROVIDER_IDS)
    rows = connection.execute(
        f"SELECT id, url, cachedurl FROM texture WHERE {condition}", values
    ).fetchall()
    exact_suffixes = tuple(
        f"/addons/{addon_id}/{asset}"
        for addon_id in PROVIDER_IDS
        for asset in ("icon.png", "fanart.jpg")
    )
    umbrella_suffixes = (
        "/resources/artwork/umbrella/icon.png",
        "/resources/artwork/umbrella/fanart.jpg",
        "/resources/artwork/umbrella/banner.png",
        "/resources/skins/default/media/common/icon.png",
        "/resources/skins/default/media/common/fanart.jpg",
        "/resources/skins/default/media/common/umbrellacircle.png",
    )
    return [
        row
        for row in rows
        if row[1].lower().rstrip("/").endswith(exact_suffixes + umbrella_suffixes)
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("--remove", action="store_true")
    args = parser.parse_args()
    connection = sqlite3.connect(args.database)
    rows = matching_rows(connection)
    print(json.dumps([{"id": row[0], "url": row[1], "cachedurl": row[2]} for row in rows], indent=2))
    if args.remove and rows:
        ids = tuple(row[0] for row in rows)
        placeholders = ",".join("?" for _ in ids)
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "sizes" in tables:
            connection.execute(f"DELETE FROM sizes WHERE idtexture IN ({placeholders})", ids)
        connection.execute(f"DELETE FROM texture WHERE id IN ({placeholders})", ids)
        connection.commit()
    connection.close()


if __name__ == "__main__":
    main()

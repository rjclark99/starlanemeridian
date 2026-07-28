import os
import sqlite3

import xbmc
import xbmcgui
import xbmcvfs


DATABASE = xbmcvfs.translatePath(
    "special://profile/addon_data/plugin.video.umbrella/watched.db"
)
HOME = xbmcgui.Window(10000)
PROPERTIES = {
    "movie": "StarlaneHasContinueMovies",
    "episode": "StarlaneHasContinueEpisodes",
}


def read_progress():
    if not os.path.isfile(DATABASE):
        return False, False
    connection = sqlite3.connect(DATABASE, timeout=1)
    try:
        query = "SELECT 1 FROM progress WHERE media_type = ? LIMIT 1"
        return tuple(
            connection.execute(query, (media_type,)).fetchone() is not None
            for media_type in ("movie", "episode")
        )
    finally:
        connection.close()


def publish(state):
    for present, media_type in zip(state, ("movie", "episode")):
        name = PROPERTIES[media_type]
        if present:
            HOME.setProperty(name, "1")
        else:
            HOME.clearProperty(name)


monitor = xbmc.Monitor()
state = read_progress()
publish(state)
if any(state) and xbmc.getCondVisibility("Window.IsActive(Home)"):
    xbmc.executebuiltin("ReloadSkin()")

while not monitor.waitForAbort(2):
    try:
        current = read_progress()
    except sqlite3.Error:
        continue
    if current != state:
        state = current
        publish(state)
        if xbmc.getCondVisibility("Window.IsActive(Home)"):
            xbmc.executebuiltin("ReloadSkin()")

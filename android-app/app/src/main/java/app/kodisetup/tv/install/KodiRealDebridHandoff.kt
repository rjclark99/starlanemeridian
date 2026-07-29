package app.kodisetup.tv.install

import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.io.File

@Serializable
data class KodiRealDebridCredentials(
    val accessToken: String,
    val refreshToken: String,
    val clientId: String,
    val clientSecret: String,
    val username: String,
)

@Serializable
private data class KodiRealDebridDocument(
    val version: Int = 1,
    val addonId: String = "plugin.video.umbrella",
    val accessToken: String,
    val refreshToken: String,
    val clientId: String,
    val clientSecret: String,
    val username: String,
)

class KodiRealDebridHandoff(private val externalStorageRoot: File) {
    fun write(kodiPackageName: String, credentials: KodiRealDebridCredentials): File {
        require(kodiPackageName == KODI_PACKAGE) { "Unsupported Kodi package identity" }
        validate(credentials)
        val directory = File(
            externalStorageRoot,
            "Android/data/$KODI_PACKAGE/files/.kodi/userdata/addon_data/repository.kodisetup",
        )
        require(directory.exists() || directory.mkdirs()) {
            "Kodi Bootstrap profile directory could not be created"
        }
        val target = File(directory, HANDOFF_FILE)
        val pending = File(directory, "$HANDOFF_FILE.starlane-new")
        pending.delete()
        try {
            val document = KodiRealDebridDocument(
                accessToken = credentials.accessToken,
                refreshToken = credentials.refreshToken,
                clientId = credentials.clientId,
                clientSecret = credentials.clientSecret,
                username = credentials.username,
            )
            pending.writeText(json.encodeToString(document))
            require(pending.length() in 2..MAX_HANDOFF_BYTES) {
                "Real-Debrid handoff is unexpectedly large"
            }
            if (target.exists()) {
                require(target.isFile && target.delete()) {
                    "Previous Real-Debrid handoff could not be replaced"
                }
            }
            require(pending.renameTo(target)) {
                "Real-Debrid handoff could not be activated"
            }
            return target
        } finally {
            pending.delete()
        }
    }

    private fun validate(credentials: KodiRealDebridCredentials) {
        mapOf(
            "access token" to credentials.accessToken,
            "refresh token" to credentials.refreshToken,
            "client ID" to credentials.clientId,
            "client secret" to credentials.clientSecret,
            "username" to credentials.username,
        ).forEach { (name, value) ->
            val maximum = if (name == "username") 256 else 4096
            require(value.isNotBlank() && value.length <= maximum) {
                "Real-Debrid $name is invalid"
            }
        }
    }

    companion object {
        private const val KODI_PACKAGE = "org.xbmc.kodi"
        private const val TARGET_ADDON = "plugin.video.umbrella"
        private const val HANDOFF_FILE = "real-debrid-handoff.json"
        private const val MAX_HANDOFF_BYTES = 16L * 1024
        private val json = Json { encodeDefaults = true }
    }
}

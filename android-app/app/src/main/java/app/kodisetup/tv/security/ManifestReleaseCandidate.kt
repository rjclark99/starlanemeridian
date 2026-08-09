package app.kodisetup.tv.security

import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.int
import kotlinx.serialization.json.jsonPrimitive

internal object ManifestReleaseCandidate {
    private val versionName = Regex("^[0-9]+(?:\\.[0-9]+){2}$")
    private val latestManifest = Regex(
        "^https://github\\.com/([^/]+)/([^/]+)/releases/latest/download/manifest\\.json$",
    )

    fun url(latestUrl: String, appVersionName: String): String? {
        if (!versionName.matches(appVersionName)) return null
        val match = latestManifest.matchEntire(latestUrl) ?: return null
        val (owner, repository) = match.destructured
        return "https://github.com/$owner/$repository/releases/download/v$appVersionName-test/manifest.json"
    }

    fun shouldCheck(latest: JsonObject, appVersionCode: Int): Boolean =
        latest["minimumSetupAppVersion"]!!.jsonPrimitive.int < appVersionCode
}

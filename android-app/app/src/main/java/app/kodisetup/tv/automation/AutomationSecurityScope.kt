package app.kodisetup.tv.automation

import app.kodisetup.tv.model.Artifact
import app.kodisetup.tv.model.SetupManifest
import java.security.MessageDigest

object AutomationSecurityScope {
    const val UNVERIFIED = "unverified"

    /** Canonical digest of fields whose change can alter Android-side automated effects. */
    fun digest(manifest: SetupManifest): String {
        val canonical = StringBuilder()
        fun token(name: String, value: Any?) {
            val text = value?.toString() ?: ""
            canonical.append(name.length).append(':').append(name)
                .append(text.length).append(':').append(text)
        }
        fun artifact(prefix: String, value: Artifact) {
            token("$prefix.url", value.url)
            token("$prefix.sha256", value.sha256)
            token("$prefix.signer", value.signerSha256)
            token("$prefix.abi", value.abi)
        }

        token("schemaVersion", manifest.schemaVersion)
        token("configVersion", manifest.configVersion)
        token("stage", manifest.stage)
        token("minimumSetupAppVersion", manifest.minimumSetupAppVersion)
        token("kodi.channel", manifest.kodi.channel)
        token("kodi.packageName", manifest.kodi.packageName)
        manifest.kodi.architectures.toSortedMap().forEach { (abi, value) -> artifact("kodi.$abi", value) }
        token("bootstrap.url", manifest.bootstrap.url)
        token("bootstrap.sha256", manifest.bootstrap.sha256)
        manifest.applications.sortedBy { it.id }.forEachIndexed { index, app ->
            val prefix = "application.$index"
            token("$prefix.id", app.id)
            token("$prefix.packageName", app.packageName)
            token("$prefix.required", app.required)
            app.storePreference.forEachIndexed { order, store -> token("$prefix.storePreference.$order", store) }
            app.storeUris.toSortedMap().forEach { (store, uri) -> token("$prefix.storeUri.$store", uri) }
            app.artifacts.sortedWith(compareBy<Artifact>({ it.abi ?: "" }, { it.url }, { it.sha256 })).forEachIndexed { order, value ->
                artifact("$prefix.artifact.$order", value)
            }
        }
        return MessageDigest.getInstance("SHA-256").digest(canonical.toString().encodeToByteArray())
            .joinToString("") { "%02x".format(it) }
    }
}

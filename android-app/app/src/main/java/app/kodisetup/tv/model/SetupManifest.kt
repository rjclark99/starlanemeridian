package app.kodisetup.tv.model

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement

@Serializable
data class SetupManifest(
    val schemaVersion: Int,
    val configVersion: String,
    val stage: String,
    val minimumSetupAppVersion: Int,
    val kodi: KodiConfig,
    val bootstrap: BootstrapConfig,
    val applications: List<ApplicationConfig>,
    val repositories: List<RepositoryConfig>,
    val addons: List<AddonConfig>,
    val skin: SkinConfig,
    val telemetry: TelemetryConfig,
    val signature: ManifestSignature,
)

@Serializable data class KodiConfig(val channel: String, val packageName: String, val architectures: Map<String, Artifact>)
@Serializable data class BootstrapConfig(val url: String, val sha256: String)
@Serializable data class Artifact(val url: String, val sha256: String, val signerSha256: String, val abi: String? = null)
@Serializable data class ApplicationConfig(val id: String, val name: String, val packageName: String, val storePreference: List<String>, val storeUris: Map<String, String>, val artifacts: List<Artifact>, val required: Boolean)
@Serializable data class RepositoryConfig(val id: String, val name: String, val addonId: String, val source: RepositorySource, val sha256: String, val enabled: Boolean)
@Serializable data class RepositorySource(val type: String, val repository: String, val assetPattern: String, val resolvedUrl: String)
@Serializable data class AddonConfig(val id: String, val name: String, val repositoryId: String, val required: Boolean, val enabled: Boolean, val settings: Map<String, JsonElement>, val authAdapter: String?)
@Serializable data class SkinConfig(val enabled: Boolean = true, val addonId: String, val homeMenu: List<HomeMenuItem>)
@Serializable data class HomeMenuItem(val id: String, val label: String, val action: MenuAction, val widgets: List<Widget>)
@Serializable data class MenuAction(val type: String, val target: String)
@Serializable data class Widget(val id: String, val label: String, val provider: String, val limit: Int)
@Serializable data class TelemetryConfig(val enabled: Boolean, val diagnosticsRequireConsent: Boolean)
@Serializable data class ManifestSignature(val keyId: String, val algorithm: String, val value: String)

enum class SetupStep { WELCOME, CONFIGURATION, KODI, PROTON, BOOTSTRAP, ACCOUNT_LINK, COMPLETE }

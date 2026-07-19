package app.kodisetup.tv.security

import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import com.google.crypto.tink.subtle.Ed25519Verify
import kotlinx.serialization.json.*
import java.io.File
import java.security.MessageDigest

object ManifestSecurity {
    private val json = Json { ignoreUnknownKeys = false; explicitNulls = true }
    private val safeId = Regex("^[a-z0-9][a-z0-9.-]{0,63}$")
    private val addonId = Regex("^[a-z][a-z0-9]*(\\.[a-z0-9_-]+)+$")
    private val sha = Regex("^[a-f0-9]{64}$")
    private val menuTypes = setOf("kodi-window", "addon", "favourite", "noop")
    private val adapters = setOf<String?>(null, "real-debrid-device-v1")

    fun verify(raw: String, publicKeyBase64Url: String, appVersion: Int): JsonObject {
        val root = json.parseToJsonElement(raw).jsonObject
        require(root["schemaVersion"]?.jsonPrimitive?.int == 1) { "Unsupported schema version" }
        require(root["minimumSetupAppVersion"]!!.jsonPrimitive.int <= appVersion) { "Setup app update required" }
        val signature = root["signature"]!!.jsonObject
        require(signature["algorithm"]!!.jsonPrimitive.content == "Ed25519") { "Unsupported signature algorithm" }
        require(safeId.matches(signature["keyId"]!!.jsonPrimitive.content)) { "Invalid key ID" }
        val signedValue = signature["value"]!!.jsonPrimitive.content
        val canonical = canonical(root).encodeToByteArray()
        Ed25519Verify(decodeUrl(publicKeyBase64Url)).verify(decodeUrl(signedValue), canonical)
        val stage = root["stage"]?.jsonPrimitive?.content
        if (stage == "revoked") throw ManifestRevokedException()
        require(stage in setOf("test", "stable")) { "Manifest is not active" }
        validateAllowlist(root)
        return root
    }

    private fun validateAllowlist(root: JsonObject) {
        val kodi = root["kodi"]!!.jsonObject
        require(kodi["channel"]!!.jsonPrimitive.content == "stable" && kodi["packageName"]!!.jsonPrimitive.content == "org.xbmc.kodi")
        kodi["architectures"]!!.jsonObject.values.map { it.jsonObject }.forEach { artifact ->
            require(artifact["url"]!!.jsonPrimitive.content.startsWith("https://mirrors.kodi.tv/releases/android/"))
            require(sha.matches(artifact["sha256"]!!.jsonPrimitive.content) && sha.matches(artifact["signerSha256"]!!.jsonPrimitive.content))
        }
        val bootstrap = root["bootstrap"]!!.jsonObject
        require(bootstrap["url"]!!.jsonPrimitive.content.startsWith("https://github.com/"))
        require(sha.matches(bootstrap["sha256"]!!.jsonPrimitive.content))
        val repositories = root["repositories"]!!.jsonArray.map { it.jsonObject }
        val repositoryIds = repositories.map { it["id"]!!.jsonPrimitive.content }.toSet()
        repositories.forEach {
            require(addonId.matches(it["id"]!!.jsonPrimitive.content))
            require(sha.matches(it["sha256"]!!.jsonPrimitive.content))
            require(it["source"]!!.jsonObject["resolvedUrl"]!!.jsonPrimitive.content.startsWith("https://github.com/"))
        }
        root["addons"]!!.jsonArray.map { it.jsonObject }.forEach {
            require(addonId.matches(it["id"]!!.jsonPrimitive.content))
            require(it["repositoryId"]!!.jsonPrimitive.content in repositoryIds)
            val adapter = it["authAdapter"].let { value -> if (value == null || value is JsonNull) null else value.jsonPrimitive.content }
            require(adapter in adapters)
        }
        root["applications"]!!.jsonArray.map { it.jsonObject }.forEach { application ->
            require(safeId.matches(application["id"]!!.jsonPrimitive.content))
            application["artifacts"]!!.jsonArray.map { it.jsonObject }.forEach { artifact ->
                require(artifact["url"]!!.jsonPrimitive.content.startsWith("https://github.com/ProtonVPN/android-app/"))
                require(sha.matches(artifact["sha256"]!!.jsonPrimitive.content) && sha.matches(artifact["signerSha256"]!!.jsonPrimitive.content))
            }
        }
        root["skin"]!!.jsonObject["homeMenu"]!!.jsonArray.forEach {
            require(it.jsonObject["action"]!!.jsonObject["type"]!!.jsonPrimitive.content in menuTypes)
        }
    }

    private fun canonical(root: JsonObject): String {
        val signature = JsonObject(root["signature"]!!.jsonObject.toMutableMap().apply { put("value", JsonPrimitive("")) })
        val copy = JsonObject(root.toMutableMap().apply { put("signature", signature) })
        return canonicalElement(copy)
    }

    private fun canonicalElement(element: JsonElement): String = when (element) {
        is JsonObject -> element.entries.sortedBy { it.key }.joinToString(",", "{", "}") { (key, value) -> JsonPrimitive(key).toString() + ":" + canonicalElement(value) }
        is JsonArray -> element.joinToString(",", "[", "]") { canonicalElement(it) }
        else -> element.toString()
    }

    fun sha256(file: File): String = MessageDigest.getInstance("SHA-256").let { digest ->
        file.inputStream().use { input ->
            val buffer = ByteArray(1024 * 1024)
            while (true) { val count = input.read(buffer); if (count < 0) break; digest.update(buffer, 0, count) }
        }
        digest.digest().joinToString("") { "%02x".format(it) }
    }

    fun archiveSignerSha256(context: Context, apk: File): String {
        // Fire OS 7 (Android 9/API 28) can return a null SigningInfo for a valid
        // archive even though its legacy signatures field is populated. Request
        // both representations and prefer SigningInfo on platforms that provide it.
        @Suppress("DEPRECATION")
        val flags = if (Build.VERSION.SDK_INT >= 28) {
            PackageManager.GET_SIGNING_CERTIFICATES or PackageManager.GET_SIGNATURES
        } else {
            PackageManager.GET_SIGNATURES
        }
        val info = requireNotNull(context.packageManager.getPackageArchiveInfo(apk.absolutePath, flags)) { "Invalid APK" }
        val signatures = if (Build.VERSION.SDK_INT >= 28) {
            @Suppress("DEPRECATION")
            info.signingInfo?.apkContentsSigners?.takeIf { it.isNotEmpty() }
                ?: info.signatures?.takeIf { it.isNotEmpty() }
                ?: throw IllegalArgumentException("APK has no signing certificates")
        } else {
            @Suppress("DEPRECATION")
            info.signatures?.takeIf { it.isNotEmpty() }
                ?: throw IllegalArgumentException("APK has no signing certificates")
        }
        require(signatures.size == 1) { "APK must have exactly one current signer" }
        val signature = signatures[0]
        return MessageDigest.getInstance("SHA-256").digest(signature.toByteArray()).joinToString("") { "%02x".format(it) }
    }

    private fun decodeUrl(value: String): ByteArray = android.util.Base64.decode(value, android.util.Base64.URL_SAFE or android.util.Base64.NO_WRAP or android.util.Base64.NO_PADDING)
}

class ManifestRevokedException : SecurityException("The published configuration has been revoked")

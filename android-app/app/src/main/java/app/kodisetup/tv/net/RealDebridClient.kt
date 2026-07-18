package app.kodisetup.tv.net

import app.kodisetup.tv.security.TokenVault
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import java.net.HttpURLConnection
import java.net.URLEncoder
import java.net.URL

class RealDebridClient(private val vault: TokenVault) {
    private val json = Json { ignoreUnknownKeys = true }
    private val base = "https://api.real-debrid.com/oauth/v2"

    @Serializable data class DeviceCode(@SerialName("device_code") val deviceCode: String, @SerialName("user_code") val userCode: String, val interval: Int, @SerialName("expires_in") val expiresIn: Int, @SerialName("verification_url") val verificationUrl: String)
    @Serializable data class Token(@SerialName("access_token") val accessToken: String, @SerialName("refresh_token") val refreshToken: String, @SerialName("expires_in") val expiresIn: Int)
    @Serializable data class Credentials(@SerialName("client_id") val clientId: String, @SerialName("client_secret") val clientSecret: String)
    @Serializable data class User(val id: Int, val username: String, val premium: Int, val expiration: String?)

    fun begin(clientId: String): DeviceCode = json.decodeFromString(Http.getText("$base/device/code?client_id=${encode(clientId)}&new_credentials=yes"))

    fun credentials(clientId: String, deviceCode: String): Credentials? = runCatching {
        json.decodeFromString<Credentials>(Http.getText("$base/device/credentials?client_id=${encode(clientId)}&code=${encode(deviceCode)}"))
    }.getOrNull()

    fun poll(clientId: String, clientSecret: String, code: String): Boolean {
        val success = requestToken(clientId, clientSecret, code)
        if (success) { vault.put("rd_client_id", clientId); vault.put("rd_client_secret", clientSecret) }
        return success
    }

    private fun requestToken(clientId: String, clientSecret: String, code: String): Boolean {
        val body = "client_id=${encode(clientId)}&client_secret=${encode(clientSecret)}&code=${encode(code)}&grant_type=${encode("http://oauth.net/grant_type/device/1.0")}" 
        val connection = URL("$base/token").openConnection() as HttpURLConnection
        connection.connectTimeout = 15_000; connection.readTimeout = 20_000
        connection.requestMethod = "POST"; connection.doOutput = true; connection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded")
        connection.outputStream.use { it.write(body.encodeToByteArray()) }
        if (connection.responseCode !in 200..299) return false
        val token = json.decodeFromString<Token>(connection.inputStream.bufferedReader().use { it.readText() })
        vault.put("rd_access", token.accessToken); vault.put("rd_refresh", token.refreshToken)
        return true
    }

    fun user(): User? = userWithToken() ?: if (refresh()) userWithToken() else null

    private fun userWithToken(): User? = vault.get("rd_access")?.let { token ->
        val connection = URL("https://api.real-debrid.com/rest/1.0/user").openConnection() as HttpURLConnection
        connection.connectTimeout = 15_000; connection.readTimeout = 20_000
        connection.setRequestProperty("Authorization", "Bearer $token")
        if (connection.responseCode !in 200..299) null else json.decodeFromString(connection.inputStream.bufferedReader().use { it.readText() })
    }

    private fun refresh(): Boolean {
        val clientId = vault.get("rd_client_id") ?: return false
        val clientSecret = vault.get("rd_client_secret") ?: return false
        val refreshToken = vault.get("rd_refresh") ?: return false
        return requestToken(clientId, clientSecret, refreshToken)
    }

    private fun encode(value: String) = URLEncoder.encode(value, "UTF-8")
}

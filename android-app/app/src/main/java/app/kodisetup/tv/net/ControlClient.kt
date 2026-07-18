package app.kodisetup.tv.net

import android.os.Build
import app.kodisetup.tv.security.DeviceIdentity
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest
import java.util.UUID

class ControlClient(private val baseUrl: String, private val identity: DeviceIdentity) {
    private val json = Json { ignoreUnknownKeys = false }

    @Serializable data class PairRequest(val code: String, val publicKey: String, val model: String, val osVersion: String)
    @Serializable data class PairResponse(val deviceId: String, val token: String)
    @Serializable data class Status(val setupStep: String, val appVersion: Int, val configVersion: String?, val errorCode: String?, val debridExpiry: String?)
    @Serializable data class Command(val id: String, val kind: String, val payload: String, val created_at: Long)
    @Serializable data class Commands(val commands: List<Command>)

    fun pair(code: String): PairResponse = json.decodeFromString(post("/v1/devices/pair", json.encodeToString(PairRequest(code, identity.publicKey(), Build.MODEL, Build.VERSION.RELEASE)), null))

    fun report(deviceId: String, token: String, status: Status) {
        post("/v1/devices/$deviceId/status", json.encodeToString(status), token)
    }

    fun commands(deviceId: String, token: String): Commands {
        val path = "/v1/devices/$deviceId/commands"
        val timestamp = (System.currentTimeMillis() / 1000).toString(); val nonce = UUID.randomUUID().toString()
        val emptyHash = MessageDigest.getInstance("SHA-256").digest(byteArrayOf()).joinToString("") { "%02x".format(it) }
        val signed = "GET\n$path\n$timestamp\n$nonce\n$emptyHash".encodeToByteArray()
        val connection = URL(baseUrl.trimEnd('/') + path).openConnection() as HttpURLConnection
        connection.requestMethod = "GET"; connection.connectTimeout = 15_000; connection.readTimeout = 15_000
        connection.setRequestProperty("Authorization", "Bearer $token"); connection.setRequestProperty("X-Device-Timestamp", timestamp)
        connection.setRequestProperty("X-Device-Nonce", nonce); connection.setRequestProperty("X-Device-Signature", identity.sign(signed))
        val response = (if (connection.responseCode in 200..299) connection.inputStream else connection.errorStream).bufferedReader().use { it.readText() }
        require(connection.responseCode in 200..299) { "Command API returned ${connection.responseCode}" }
        return json.decodeFromString(response)
    }

    private fun post(path: String, body: String, token: String?): String {
        val timestamp = (System.currentTimeMillis() / 1000).toString()
        val nonce = UUID.randomUUID().toString()
        val bodyHash = MessageDigest.getInstance("SHA-256").digest(body.encodeToByteArray()).joinToString("") { "%02x".format(it) }
        val signed = "POST\n$path\n$timestamp\n$nonce\n$bodyHash".encodeToByteArray()
        val connection = URL(baseUrl.trimEnd('/') + path).openConnection() as HttpURLConnection
        connection.requestMethod = "POST"; connection.doOutput = true; connection.connectTimeout = 15_000; connection.readTimeout = 15_000
        connection.setRequestProperty("Content-Type", "application/json")
        connection.setRequestProperty("X-Device-Timestamp", timestamp); connection.setRequestProperty("X-Device-Nonce", nonce)
        connection.setRequestProperty("X-Device-Signature", identity.sign(signed)); token?.let { connection.setRequestProperty("Authorization", "Bearer $it") }
        connection.outputStream.use { it.write(body.encodeToByteArray()) }
        val stream = if (connection.responseCode in 200..299) connection.inputStream else connection.errorStream
        val response = stream.bufferedReader().use { it.readText() }
        require(connection.responseCode in 200..299) { "Control API returned ${connection.responseCode}: $response" }
        return response
    }
}

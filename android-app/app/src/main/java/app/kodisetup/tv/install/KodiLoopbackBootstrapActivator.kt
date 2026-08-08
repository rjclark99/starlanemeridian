package app.kodisetup.tv.install

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.boolean
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import java.io.InputStream
import java.net.InetSocketAddress
import java.net.Socket

internal const val MAX_RESPONSE_BYTES = 64 * 1024

/**
 * Read exactly one complete top-level JSON value from Kodi's TCP transport.
 *
 * Kodi's JSON-RPC socket sends neither a trailing newline nor EOF and keeps the
 * connection open, so reading until a delimiter can only ever end in a socket
 * timeout. Tracking brace depth — while honouring string literals and their
 * escapes — lets the read finish the moment the response is actually complete.
 * Scanning bytes is safe because UTF-8 continuation bytes never collide with the
 * ASCII structural characters.
 */
internal fun readFramedKodiJson(input: InputStream, limit: Int = MAX_RESPONSE_BYTES): String {
    val response = ByteArray(limit)
    var count = 0
    var depth = 0
    var started = false
    var inString = false
    var escaped = false
    while (count < response.size) {
        val next = input.read()
        if (next < 0) break
        val character = next.toChar()
        if (!started && character.isWhitespace()) continue
        response[count++] = next.toByte()
        if (inString) {
            when {
                escaped -> escaped = false
                character == '\\' -> escaped = true
                character == '"' -> inString = false
            }
            continue
        }
        when (character) {
            '"' -> { started = true; inString = true }
            '{', '[' -> { started = true; depth++ }
            '}', ']' -> {
                depth--
                if (started && depth <= 0) return response.copyOf(count).toString(Charsets.UTF_8)
            }
            '\n' -> if (started && depth == 0) return response.copyOf(count - 1).toString(Charsets.UTF_8)
        }
    }
    require(count in 1 until response.size) { "Kodi JSON-RPC response is empty or oversized" }
    return response.copyOf(count).toString(Charsets.UTF_8)
}

internal fun exchangeWithKodi(request: String): String {
    Socket().use { socket ->
        socket.soTimeout = 1_000
        socket.connect(InetSocketAddress("127.0.0.1", 9090), 500)
        socket.getOutputStream().apply {
            write(request.toByteArray(Charsets.UTF_8))
            write('\n'.code)
            flush()
        }
        return readFramedKodiJson(socket.getInputStream())
    }
}

/** Enables only Starlane's fixed Bootstrap through Kodi's loopback JSON-RPC endpoint. */
class KodiLoopbackBootstrapActivator internal constructor(
    private val exchange: (String) -> String = ::exchangeWithKodi,
    private val pause: (Long) -> Unit = Thread::sleep,
    private val attempts: Int = 120,
) {
    fun activate(gate: () -> Unit): Boolean {
        var lastFailure: Throwable? = null
        repeat(attempts) { attempt ->
            gate()
            val alreadyEnabled = try {
                enabled(GET_ID)
            } catch (failure: Throwable) {
                lastFailure = failure
                if (attempt + 1 < attempts) { gate(); pause(RETRY_DELAY_MS) }
                return@repeat
            }
            if (alreadyEnabled) {
                quitKodi(gate)
                return false
            }
            gate()
            try {
                val set = parse(exchange(SET_REQUEST), SET_ID)
                require(set["result"]?.jsonPrimitive?.content == "OK") { "Kodi rejected fixed Bootstrap activation" }
            } catch (failure: Throwable) {
                lastFailure = failure
                if (attempt + 1 < attempts) { gate(); pause(RETRY_DELAY_MS) }
                return@repeat
            }
            gate()
            try {
                require(enabled(VERIFY_ID)) { "Kodi did not confirm fixed Bootstrap activation" }
                quitKodi(gate)
                return true
            } catch (failure: Throwable) {
                lastFailure = failure
                if (attempt + 1 < attempts) { gate(); pause(RETRY_DELAY_MS) }
            }
        }
        throw IllegalStateException("Kodi did not make the fixed Bootstrap activation API ready in time", lastFailure)
    }

    private fun quitKodi(gate: () -> Unit) {
        gate()
        val response = parse(exchange(QUIT_REQUEST), QUIT_ID)
        require(response["result"]?.jsonPrimitive?.content == "OK") { "Kodi rejected the fixed Bootstrap restart" }
        pause(KODI_SHUTDOWN_GRACE_MS)
    }

    private fun enabled(id: Int): Boolean {
        val response = parse(exchange(getRequest(id)), id)
        val addon = response["result"]?.jsonObject?.get("addon")?.jsonObject
            ?: error("Kodi has not discovered the fixed Bootstrap yet")
        require(addon["addonid"]?.jsonPrimitive?.content == ADDON_ID) { "Kodi returned an unexpected add-on identity" }
        return addon["enabled"]?.jsonPrimitive?.boolean
            ?: error("Kodi omitted the fixed Bootstrap enabled state")
    }

    private fun parse(source: String, id: Int) = Json.parseToJsonElement(source).jsonObject.also { response ->
        require(response["jsonrpc"]?.jsonPrimitive?.content == "2.0" && response["id"]?.jsonPrimitive?.content == id.toString()) {
            "Kodi returned an unrelated JSON-RPC response"
        }
        response["error"]?.let { error("Kodi JSON-RPC is not ready: $it") }
    }

    private companion object {
        const val ADDON_ID = "repository.kodisetup"
        const val GET_ID = 4101
        const val SET_ID = 4102
        const val VERIFY_ID = 4103
        const val QUIT_ID = 4104
        const val RETRY_DELAY_MS = 500L
        const val KODI_SHUTDOWN_GRACE_MS = 3_000L
        fun getRequest(id: Int) = """{"jsonrpc":"2.0","method":"Addons.GetAddonDetails","params":{"addonid":"$ADDON_ID","properties":["enabled"]},"id":$id}"""
        val SET_REQUEST = """{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","params":{"addonid":"$ADDON_ID","enabled":true},"id":$SET_ID}"""
        val QUIT_REQUEST = """{"jsonrpc":"2.0","method":"Application.Quit","id":$QUIT_ID}"""
    }
}

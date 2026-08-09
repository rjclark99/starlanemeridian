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

enum class BootstrapActivationOutcome {
    ENABLED_AWAITING_CONSENT,
    ALREADY_ENABLED_AWAITING_CONSENT,
    API_UNAVAILABLE,
    BOOTSTRAP_MISSING,
    BOOTSTRAP_INSTALLED_DISABLED,
    UNKNOWN_SOURCES_DISABLED,
}

/** Enables only Starlane's fixed Bootstrap through Kodi's loopback JSON-RPC endpoint. */
class KodiLoopbackBootstrapActivator internal constructor(
    private val exchange: (String) -> String = ::exchangeWithKodi,
    private val pause: (Long) -> Unit = Thread::sleep,
    private val attempts: Int = 110,
    private val now: () -> Long = System::currentTimeMillis,
) {
    /** One foreground activation attempt. Retries are only Kodi-startup readiness probes. */
    fun activate(gate: () -> Unit): BootstrapActivationOutcome {
        val deadline = now() + MAX_ACTIVATION_MILLIS
        var bootstrapWasDiscoveredDisabled = false
        repeat(attempts) { attempt ->
            if (now() >= deadline) return if (bootstrapWasDiscoveredDisabled) {
                BootstrapActivationOutcome.BOOTSTRAP_INSTALLED_DISABLED
            } else BootstrapActivationOutcome.API_UNAVAILABLE
            gate()
            val unknownSourcesAreEnabled = try {
                unknownSourcesEnabled()
            } catch (failure: Throwable) {
                if (attempt + 1 < attempts) { gate(); pause(RETRY_DELAY_MS) }
                return@repeat
            }
            if (!unknownSourcesAreEnabled) return BootstrapActivationOutcome.UNKNOWN_SOURCES_DISABLED
            gate()
            val alreadyEnabled = try {
                enabled(GET_ID)
            } catch (failure: Throwable) {
                if (failure is BootstrapMissingException) return BootstrapActivationOutcome.BOOTSTRAP_MISSING
                if (attempt + 1 < attempts) { gate(); pause(RETRY_DELAY_MS) }
                return@repeat
            }
            if (alreadyEnabled) {
                quitKodi(gate, deadline)
                return BootstrapActivationOutcome.ALREADY_ENABLED_AWAITING_CONSENT
            }
            bootstrapWasDiscoveredDisabled = true
            gate()
            try {
                val set = parse(exchange(SET_REQUEST), SET_ID)
                require(set["result"]?.jsonPrimitive?.content == "OK") { "Kodi rejected fixed Bootstrap activation" }
            } catch (failure: Throwable) {
                if (attempt + 1 < attempts) { gate(); pause(RETRY_DELAY_MS) }
                return@repeat
            }
            gate()
            try {
                require(enabled(VERIFY_ID)) { "Kodi did not confirm fixed Bootstrap activation" }
                quitKodi(gate, deadline)
                return BootstrapActivationOutcome.ENABLED_AWAITING_CONSENT
            } catch (failure: Throwable) {
                if (attempt + 1 < attempts) { gate(); pause(RETRY_DELAY_MS) }
            }
        }
        return if (bootstrapWasDiscoveredDisabled) BootstrapActivationOutcome.BOOTSTRAP_INSTALLED_DISABLED
        else BootstrapActivationOutcome.API_UNAVAILABLE
    }

    private fun quitKodi(gate: () -> Unit, deadline: Long): Boolean {
        if (now() + KODI_QUIT_BUDGET_MS > deadline) return false
        gate()
        val response = runCatching { parse(exchange(QUIT_REQUEST), QUIT_ID) }.getOrNull() ?: return false
        if (response["result"]?.jsonPrimitive?.content != "OK") return false
        pause(KODI_SHUTDOWN_GRACE_MS)
        return true
    }

    private fun enabled(id: Int): Boolean {
        val response = parse(exchange(getRequest(id)), id)
        val addon = response["result"]?.jsonObject?.get("addon")?.jsonObject
            ?: throw BootstrapMissingException()
        require(addon["addonid"]?.jsonPrimitive?.content == ADDON_ID) { "Kodi returned an unexpected add-on identity" }
        return addon["enabled"]?.jsonPrimitive?.boolean
            ?: error("Kodi omitted the fixed Bootstrap enabled state")
    }

    private fun unknownSourcesEnabled(): Boolean {
        val response = parse(exchange(UNKNOWN_SOURCES_REQUEST), UNKNOWN_SOURCES_ID)
        val value = response["result"]?.jsonObject?.entries
            ?.singleOrNull { it.key == "value" }?.value?.jsonPrimitive?.content
            ?: error("Kodi omitted the Unknown Sources setting")
        return when (value.lowercase()) {
            "true" -> true
            "false" -> false
            else -> error("Kodi returned an invalid Unknown Sources setting")
        }
    }

    private class BootstrapMissingException : IllegalStateException("Kodi has not discovered the fixed Bootstrap yet")

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
        const val UNKNOWN_SOURCES_ID = 4105
        const val RETRY_DELAY_MS = 500L
        const val KODI_SHUTDOWN_GRACE_MS = 3_000L
        const val MAX_ACTIVATION_MILLIS = 45_000L
        const val KODI_QUIT_BUDGET_MS = 4_500L
        fun getRequest(id: Int) = """{"jsonrpc":"2.0","method":"Addons.GetAddonDetails","params":{"addonid":"$ADDON_ID","properties":["enabled"]},"id":$id}"""
        val UNKNOWN_SOURCES_REQUEST = """{"jsonrpc":"2.0","method":"Settings.GetSettingValue","params":{"setting":"addons.unknownsources"},"id":$UNKNOWN_SOURCES_ID}"""
        val SET_REQUEST = """{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","params":{"addonid":"$ADDON_ID","enabled":true},"id":$SET_ID}"""
        val QUIT_REQUEST = """{"jsonrpc":"2.0","method":"Application.Quit","id":$QUIT_ID}"""
    }
}

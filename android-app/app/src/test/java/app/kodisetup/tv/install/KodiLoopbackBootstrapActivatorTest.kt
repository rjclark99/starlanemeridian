package app.kodisetup.tv.install

import java.io.ByteArrayInputStream
import java.net.InetSocketAddress
import java.net.ServerSocket
import java.net.Socket
import kotlin.concurrent.thread
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

class KodiLoopbackBootstrapActivatorTest {
    @Test fun `unknown sources reply uses Kodi boolean value`() {
        assertEquals("true", Json.parseToJsonElement(unknownSources(true)).jsonObject["result"]!!.jsonObject["value"]!!.jsonPrimitive.content)
    }
    @Test fun `enables only fixed bootstrap and verifies state`() {
        val requests = mutableListOf<String>()
        val replies = ArrayDeque(listOf(
            unknownSources(true),
            details(4101, false),
            """{"jsonrpc":"2.0","id":4102,"result":"OK"}""",
            details(4103, true),
            ok(4104),
        ))
        var gates = 0
        val outcome = KodiLoopbackBootstrapActivator({ request -> requests += request; replies.removeFirst() }, {}, 3).activate { gates++ }

        assertEquals(BootstrapActivationOutcome.ENABLED_AWAITING_CONSENT, outcome)
        assertTrue(gates >= requests.size)
        assertTrue(requests.any { it.contains("Settings.GetSettingValue") && it.contains("addons.unknownsources") })
        assertTrue(requests.single { it.contains("SetAddonEnabled") }.contains("\"enabled\":true"))
        assertTrue(requests.single { it.contains("Application.Quit") } == """{"jsonrpc":"2.0","method":"Application.Quit","id":4104}""")
        assertTrue(requests.none { it.contains("host") || it.contains("port") })
    }

    @Test fun `already enabled skips enable and requests fixed restart`() {
        val requests = mutableListOf<String>()
        val replies = ArrayDeque(listOf(unknownSources(true), details(4101, true), ok(4104)))
        val outcome = KodiLoopbackBootstrapActivator({ request -> requests += request; replies.removeFirst() }, {}, 1).activate {}
        assertEquals(BootstrapActivationOutcome.ALREADY_ENABLED_AWAITING_CONSENT, outcome)
        assertTrue(requests.none { it.contains("SetAddonEnabled") })
        assertTrue(requests.single { it.contains("Application.Quit") }.contains("\"id\":4104"))
    }

    @Test fun `disabled unknown sources prevents add-on mutation`() {
        val requests = mutableListOf<String>()
        val outcome = KodiLoopbackBootstrapActivator({ request -> requests += request; unknownSources(false) }, {}, 2).activate {}
        assertEquals(BootstrapActivationOutcome.UNKNOWN_SOURCES_DISABLED, outcome)
        assertTrue(requests.none { it.contains("Addons.SetAddonEnabled") })
    }

    @Test fun `missing bootstrap is distinguished from an unavailable API`() {
        val missing = KodiLoopbackBootstrapActivator({ request ->
            if (request.contains("Settings.GetSettingValue")) unknownSources(true) else """{"jsonrpc":"2.0","id":4101,"result":{}}"""
        }, {}, 1).activate {}
        val unavailable = KodiLoopbackBootstrapActivator({ error(4105) }, {}, 1).activate {}

        assertEquals(BootstrapActivationOutcome.BOOTSTRAP_MISSING, missing)
        assertEquals(BootstrapActivationOutcome.API_UNAVAILABLE, unavailable)
    }

    @Test fun `installed but persistently disabled bootstrap has a distinct outcome`() {
        val replies = ArrayDeque(listOf(
            unknownSources(true),
            details(4101, false),
            error(4102),
        ))
        val outcome = KodiLoopbackBootstrapActivator({ replies.removeFirst() }, {}, 1).activate {}

        assertEquals(BootstrapActivationOutcome.BOOTSTRAP_INSTALLED_DISABLED, outcome)
    }

    @Test fun `activation does not exceed its foreground time budget`() {
        var clock = 0L
        var exchanges = 0
        val outcome = KodiLoopbackBootstrapActivator(
            { exchanges++; error(4105) }, {}, 110,
            now = { clock += 60_000L; clock },
        ).activate {}

        assertEquals(BootstrapActivationOutcome.API_UNAVAILABLE, outcome)
        assertEquals(0, exchanges)
    }

    @Test fun `late successful activation reserves time for bounded Kodi shutdown`() {
        var clock = 34_000L
        var firstClockRead = true
        val replies = ArrayDeque(listOf(
            unknownSources(true),
            details(4101, false),
            """{"jsonrpc":"2.0","id":4102,"result":"OK"}""",
            details(4103, true),
            ok(4104),
        ))
        val outcome = KodiLoopbackBootstrapActivator(
            exchange = { clock += 1_500L; replies.removeFirst() },
            pause = { clock += it },
            attempts = 1,
            now = { if (firstClockRead) { firstClockRead = false; 0L } else clock },
        ).activate {}

        assertEquals(BootstrapActivationOutcome.ENABLED_AWAITING_CONSENT, outcome)
        assertTrue(clock <= 60_000L)
    }

    @Test fun `enabled result near deadline skips restart instead of throwing`() {
        var clock = 43_000L
        var firstClockRead = true
        val requests = mutableListOf<String>()
        val replies = ArrayDeque(listOf(unknownSources(true), details(4101, true)))
        val outcome = KodiLoopbackBootstrapActivator(
            exchange = { request -> requests += request; clock += 750L; replies.removeFirst() },
            pause = { clock += it },
            attempts = 1,
            now = { if (firstClockRead) { firstClockRead = false; 0L } else clock },
        ).activate {}

        assertEquals(BootstrapActivationOutcome.ALREADY_ENABLED_AWAITING_CONSENT, outcome)
        assertTrue(requests.none { it.contains("Application.Quit") })
        assertTrue(clock <= 60_000L)
    }

    @Test fun `restart rejection does not hide verified enabled state`() {
        val replies = ArrayDeque(listOf(unknownSources(true), details(4101, true), error(4104)))
        val outcome = KodiLoopbackBootstrapActivator({ replies.removeFirst() }, {}, 1).activate {}

        assertEquals(BootstrapActivationOutcome.ALREADY_ENABLED_AWAITING_CONSENT, outcome)
    }

    @Test fun `slow first Kodi start is tolerated`() {
        var calls = 0
        val outcome = KodiLoopbackBootstrapActivator({
            calls++
            if (calls <= 25) error(4105) else when (calls) {
                26 -> unknownSources(true)
                27 -> details(4101, false)
                28 -> """{"jsonrpc":"2.0","id":4102,"result":"OK"}"""
                29 -> details(4103, true)
                else -> ok(4104)
            }
        }, {}, 30).activate {}

        assertEquals(BootstrapActivationOutcome.ENABLED_AWAITING_CONSENT, outcome)
        assertTrue(calls == 30)
    }

    @Test fun `revoked gate stops before enable mutation`() {
        var calls = 0
        var gates = 0
        val result = runCatching {
            KodiLoopbackBootstrapActivator({ calls++; unknownSources(true) }, {}, 2).activate {
                gates++
                if (gates == 2) error("revoked")
            }
        }
        assertTrue(result.exceptionOrNull()?.message == "revoked")
        assertTrue(calls == 1)
    }

    @Test fun `reads a complete response over a real socket with no newline and no EOF`() {
        // Kodi's TCP transport sends neither delimiter and holds the socket open,
        // which is exactly what made the previous read loop time out. The loopback
        // address and port of the shipping code stay hard-coded, so this exercises
        // the framing itself against a genuine socket rather than a stream stub.
        val payload = details(4101, false)
        val server = ServerSocket(0)
        val responder = thread {
            server.accept().use { accepted ->
                accepted.getOutputStream().apply { write(payload.toByteArray()); flush() }
                Thread.sleep(400)
            }
        }
        try {
            Socket().use { client ->
                client.soTimeout = 2_000
                client.connect(InetSocketAddress("127.0.0.1", server.localPort), 1_000)
                assertEquals(payload, readFramedKodiJson(client.getInputStream()))
            }
        } finally {
            responder.join(3_000)
            server.close()
        }
    }

    @Test fun `stops at one value when Kodi leaves trailing bytes unsent`() {
        val payload = details(4101, true)
        val stream = ByteArrayInputStream(payload.toByteArray())
        assertEquals(payload, readFramedKodiJson(stream))
    }

    @Test fun `braces inside strings and escapes do not end the read early`() {
        val payload = """{"jsonrpc":"2.0","id":7,"result":{"note":"a } \" { \\ brace"}}"""
        assertEquals(payload, readFramedKodiJson(ByteArrayInputStream(payload.toByteArray())))
    }

    @Test fun `oversized response is rejected rather than truncated`() {
        val unterminated = "{" + "a".repeat(64)
        val result = runCatching { readFramedKodiJson(ByteArrayInputStream(unterminated.toByteArray()), limit = 32) }
        assertTrue(result.isFailure)
    }

    @Test fun `trailing newline after a complete value is not returned`() {
        val payload = details(4103, true)
        assertEquals(payload, readFramedKodiJson(ByteArrayInputStream((payload + "\n").toByteArray())))
    }

    private fun details(id: Int, enabled: Boolean) = """{"jsonrpc":"2.0","id":$id,"result":{"addon":{"addonid":"repository.kodisetup","enabled":$enabled}}}"""
    private fun unknownSources(enabled: Boolean) = """{"jsonrpc":"2.0","id":4105,"result":{"value":$enabled}}"""
    private fun error(id: Int) = """{"jsonrpc":"2.0","id":$id,"error":{"code":-32602,"message":"Invalid params."}}"""
    private fun ok(id: Int) = """{"jsonrpc":"2.0","id":$id,"result":"OK"}"""
}

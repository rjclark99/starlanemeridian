package app.kodisetup.tv.install

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class KodiLoopbackBootstrapActivatorTest {
    @Test fun `enables only fixed bootstrap and verifies state`() {
        val requests = mutableListOf<String>()
        val replies = ArrayDeque(listOf(
            error(4101),
            details(4101, false),
            """{"jsonrpc":"2.0","id":4102,"result":"OK"}""",
            details(4103, true),
            ok(4104),
        ))
        var gates = 0
        val changed = KodiLoopbackBootstrapActivator({ request -> requests += request; replies.removeFirst() }, {}, 3).activate { gates++ }

        assertTrue(changed)
        assertTrue(gates >= requests.size)
        assertTrue(requests.filterNot { it.contains("Application.Quit") }.all { it.contains("repository.kodisetup") })
        assertTrue(requests.single { it.contains("SetAddonEnabled") }.contains("\"enabled\":true"))
        assertTrue(requests.single { it.contains("Application.Quit") } == """{"jsonrpc":"2.0","method":"Application.Quit","id":4104}""")
        assertTrue(requests.none { it.contains("host") || it.contains("port") })
    }

    @Test fun `already enabled skips enable and requests fixed restart`() {
        val requests = mutableListOf<String>()
        val replies = ArrayDeque(listOf(details(4101, true), ok(4104)))
        val changed = KodiLoopbackBootstrapActivator({ request -> requests += request; replies.removeFirst() }, {}, 1).activate {}
        assertFalse(changed)
        assertTrue(requests.none { it.contains("SetAddonEnabled") })
        assertTrue(requests.single { it.contains("Application.Quit") }.contains("\"id\":4104"))
    }

    @Test fun `wrong identity fails boundedly`() {
        var calls = 0
        val result = runCatching {
            KodiLoopbackBootstrapActivator({ calls++; details(4101, false).replace("repository.kodisetup", "other") }, {}, 2).activate {}
        }
        assertTrue(result.isFailure)
        assertTrue(calls == 2)
    }

    @Test fun `slow first Kodi start is tolerated`() {
        var calls = 0
        val changed = KodiLoopbackBootstrapActivator({
            calls++
            if (calls <= 25) error("Kodi is still starting")
            when (calls) {
                26 -> details(4101, false)
                27 -> """{"jsonrpc":"2.0","id":4102,"result":"OK"}"""
                28 -> details(4103, true)
                else -> ok(4104)
            }
        }, {}, 30).activate {}

        assertTrue(changed)
        assertTrue(calls == 29)
    }

    @Test fun `revoked gate stops before enable mutation`() {
        var calls = 0
        var gates = 0
        val result = runCatching {
            KodiLoopbackBootstrapActivator({ calls++; details(4101, false) }, {}, 2).activate {
                gates++
                if (gates == 2) error("revoked")
            }
        }
        assertTrue(result.exceptionOrNull()?.message == "revoked")
        assertTrue(calls == 1)
    }

    private fun details(id: Int, enabled: Boolean) = """{"jsonrpc":"2.0","id":$id,"result":{"addon":{"addonid":"repository.kodisetup","enabled":$enabled}}}"""
    private fun error(id: Int) = """{"jsonrpc":"2.0","id":$id,"error":{"code":-32602,"message":"Invalid params."}}"""
    private fun ok(id: Int) = """{"jsonrpc":"2.0","id":$id,"result":"OK"}"""
}

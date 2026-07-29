package app.kodisetup.tv.install

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class KodiRealDebridHandoffTest {
    @get:Rule
    val temporary = TemporaryFolder()

    @Test
    fun writesOnlyTheAllowlistedUmbrellaHandoff() {
        val root = temporary.newFolder("external")
        val file = KodiRealDebridHandoff(root).write(
            "org.xbmc.kodi",
            credentials(),
        )

        val document = Json.parseToJsonElement(file.readText()).jsonObject
        assertEquals(
            setOf(
                "version", "addonId", "accessToken", "refreshToken",
                "clientId", "clientSecret", "username",
            ),
            document.keys,
        )
        assertEquals("1", document.getValue("version").jsonPrimitive.content)
        assertEquals(
            "plugin.video.umbrella",
            document.getValue("addonId").jsonPrimitive.content,
        )
        assertEquals("access-value", document.getValue("accessToken").jsonPrimitive.content)
        assertFalse(file.resolveSibling(file.name + ".starlane-new").exists())
    }

    @Test
    fun rejectsEveryOtherKodiPackage() {
        assertThrows(IllegalArgumentException::class.java) {
            KodiRealDebridHandoff(temporary.newFolder("external"))
                .write("org.example.kodi", credentials())
        }
    }

    @Test
    fun rejectsMissingCredentialValues() {
        val error = assertThrows(IllegalArgumentException::class.java) {
            KodiRealDebridHandoff(temporary.newFolder("external"))
                .write("org.xbmc.kodi", credentials().copy(accessToken = ""))
        }
        assertTrue(error.message!!.contains("access token"))
    }

    private fun credentials() = KodiRealDebridCredentials(
        accessToken = "access-value",
        refreshToken = "refresh-value",
        clientId = "client-id",
        clientSecret = "client-secret",
        username = "owner",
    )
}

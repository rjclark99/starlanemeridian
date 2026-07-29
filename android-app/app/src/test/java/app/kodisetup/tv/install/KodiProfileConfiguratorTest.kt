package app.kodisetup.tv.install

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import javax.xml.parsers.DocumentBuilderFactory

class KodiProfileConfiguratorTest {
    @get:Rule
    val temporary = TemporaryFolder()

    @Test
    fun createsMinimalKodiProfileWithUnknownSourcesEnabled() {
        val root = temporary.newFolder("external")

        val update = KodiProfileConfigurator(root).enableUnknownSources("org.xbmc.kodi")

        assertTrue(update.changed)
        assertTrue(update.settingsFile.isFile)
        assertEquals("true", settingValue(update.settingsFile, "addons.unknownsources"))
    }

    @Test
    fun mergePreservesExistingKodiSettings() {
        val root = temporary.newFolder("external")
        val settings = settingsFile(root)
        settings.parentFile!!.mkdirs()
        settings.writeText(
            """<?xml version="1.0" encoding="UTF-8"?>
                |<settings version="2">
                |  <setting id="lookandfeel.skin">skin.estuary</setting>
                |  <setting id="addons.unknownsources">false</setting>
                |</settings>
            """.trimMargin(),
        )

        val update = KodiProfileConfigurator(root).enableUnknownSources("org.xbmc.kodi")

        assertTrue(update.changed)
        assertEquals("true", settingValue(settings, "addons.unknownsources"))
        assertEquals("skin.estuary", settingValue(settings, "lookandfeel.skin"))
        assertFalse(java.io.File(settings.parentFile, settings.name + ".starlane-backup").exists())
        assertFalse(java.io.File(settings.parentFile, settings.name + ".starlane-new").exists())
    }

    @Test
    fun alreadyEnabledProfileIsNotRewritten() {
        val root = temporary.newFolder("external")
        val settings = settingsFile(root)
        settings.parentFile!!.mkdirs()
        settings.writeText(
            """<settings version="2"><setting id="addons.unknownsources">true</setting></settings>""",
        )
        val before = settings.readBytes()

        val update = KodiProfileConfigurator(root).enableUnknownSources("org.xbmc.kodi")

        assertFalse(update.changed)
        assertTrue(before.contentEquals(settings.readBytes()))
    }

    @Test(expected = IllegalArgumentException::class)
    fun rejectsAnyPackageOtherThanOfficialKodiCompatibilityId() {
        KodiProfileConfigurator(temporary.newFolder("external"))
            .enableUnknownSources("example.other.kodi")
    }

    @Test(expected = IllegalArgumentException::class)
    fun rejectsMalformedExistingProfileWithoutReplacingIt() {
        val root = temporary.newFolder("external")
        val settings = settingsFile(root)
        settings.parentFile!!.mkdirs()
        settings.writeText("<not-settings />")

        KodiProfileConfigurator(root).enableUnknownSources("org.xbmc.kodi")
    }

    @Test(expected = IllegalArgumentException::class)
    fun rejectsDocumentTypeBeforeParsingExistingProfile() {
        val root = temporary.newFolder("external")
        val settings = settingsFile(root)
        settings.parentFile!!.mkdirs()
        settings.writeText(
            """<!DOCTYPE settings [<!ENTITY unsafe SYSTEM "file:///data/local/tmp/value">]>
                |<settings version="2"><setting id="addons.unknownsources">&unsafe;</setting></settings>
            """.trimMargin(),
        )

        KodiProfileConfigurator(root).enableUnknownSources("org.xbmc.kodi")
    }

    private fun settingsFile(root: java.io.File) = java.io.File(
        root,
        "Android/data/org.xbmc.kodi/files/.kodi/userdata/guisettings.xml",
    )

    private fun settingValue(file: java.io.File, id: String): String {
        val document = DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(file)
        val nodes = document.getElementsByTagName("setting")
        return (0 until nodes.length)
            .map { nodes.item(it) }
            .first { it.attributes.getNamedItem("id").nodeValue == id }
            .textContent
            .trim()
    }
}

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
    fun refusesToCreateAnIncompleteFreshKodiProfile() {
        val root = temporary.newFolder("external")

        val error = runCatching {
            KodiProfileConfigurator(root).enableUnknownSources("org.xbmc.kodi")
        }.exceptionOrNull()

        assertTrue(error is IllegalArgumentException)
        assertTrue(error!!.message!!.contains("Open Kodi once"))
        assertFalse(settingsFile(root).exists())
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

    @Test
    fun `real Kodi default form becomes an explicit true without changing other attributes`() {
        val root = temporary.newFolder("external")
        val settings = settingsFile(root)
        settings.parentFile!!.mkdirs()
        settings.writeText(
            """<settings version="2"><setting id="lookandfeel.skin" default="skin.estuary" tag="keep">skin.estuary</setting><setting id="addons.unknownsources" default="true" level="advanced">false</setting></settings>""",
        )

        val update = KodiProfileConfigurator(root).enableUnknownSources("org.xbmc.kodi")
        val document = DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(settings)
        val nodes = document.getElementsByTagName("setting")
        val unknown = (0 until nodes.length).map { nodes.item(it) as org.w3c.dom.Element }.single { it.getAttribute("id") == "addons.unknownsources" }
        val skin = (0 until nodes.length).map { nodes.item(it) as org.w3c.dom.Element }.single { it.getAttribute("id") == "lookandfeel.skin" }

        assertTrue(update.changed)
        assertEquals("true", unknown.textContent.trim())
        assertFalse(unknown.hasAttribute("default"))
        assertEquals("advanced", unknown.getAttribute("level"))
        assertEquals("skin.estuary", skin.getAttribute("default"))
        assertEquals("keep", skin.getAttribute("tag"))
    }

    @Test
    fun `default marker is removed even when its serialized text is already true`() {
        val root = temporary.newFolder("external")
        val settings = settingsFile(root)
        settings.parentFile!!.mkdirs()
        settings.writeText(
            """<settings version="2"><setting id="addons.unknownsources" default="true" level="keep">true</setting></settings>""",
        )

        val update = KodiProfileConfigurator(root).enableUnknownSources("org.xbmc.kodi")
        val unknown = DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(settings)
            .getElementsByTagName("setting").item(0) as org.w3c.dom.Element

        assertTrue(update.changed)
        assertEquals("true", unknown.textContent.trim())
        assertFalse(unknown.hasAttribute("default"))
        assertEquals("keep", unknown.getAttribute("level"))
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

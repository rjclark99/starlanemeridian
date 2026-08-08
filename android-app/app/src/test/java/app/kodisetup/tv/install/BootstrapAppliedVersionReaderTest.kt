package app.kodisetup.tv.install

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File

class BootstrapAppliedVersionReaderTest {
    @get:Rule val temporary = TemporaryFolder()

    @Test fun `reads only Bootstrap applied version evidence`() {
        val root = temporary.newFolder("external")
        val settings = File(root, "Android/data/org.xbmc.kodi/files/.kodi/userdata/addon_data/repository.kodisetup/settings.xml")
        settings.parentFile!!.mkdirs()
        settings.writeText("""<settings><setting id="other">x</setting><setting id="applied_version">5.8-test</setting></settings>""")
        assertEquals("5.8-test", BootstrapAppliedVersionReader(root).read("org.xbmc.kodi"))
    }

    @Test fun `rejects unsafe or absent evidence`() {
        val root = temporary.newFolder("external")
        val settings = File(root, "Android/data/org.xbmc.kodi/files/.kodi/userdata/addon_data/repository.kodisetup/settings.xml")
        settings.parentFile!!.mkdirs()
        settings.writeText("""<!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><settings><setting id="applied_version">&e;</setting></settings>""")
        assertNull(runCatching { BootstrapAppliedVersionReader(root).read("org.xbmc.kodi") }.getOrNull())
    }
}

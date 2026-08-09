package app.kodisetup.tv.install

import java.io.File
import javax.xml.parsers.DocumentBuilderFactory

/** Read-only observation of the state written by repository.kodisetup itself. */
class BootstrapAppliedVersionReader(private val externalStorageRoot: File) {
    fun read(kodiPackage: String): String? {
        require(kodiPackage == KODI_PACKAGE) { "Unsupported Kodi package" }
        val settings = File(
            externalStorageRoot,
            "Android/data/$KODI_PACKAGE/files/.kodi/userdata/addon_data/repository.kodisetup/settings.xml",
        )
        if (!settings.isFile || settings.length() > MAX_SETTINGS_BYTES) return null
        val text = settings.readText(Charsets.UTF_8)
        require(!text.contains("<!DOCTYPE", true) && !text.contains("<!ENTITY", true)) {
            "Unsafe Bootstrap settings XML"
        }
        val factory = DocumentBuilderFactory.newInstance().apply {
            // Fire OS does not implement every JAXP hardening switch. Reject the
            // dangerous declarations above, then enable all supported safeguards.
            runCatching { setFeature("http://apache.org/xml/features/disallow-doctype-decl", true) }
            runCatching { setFeature("http://xml.org/sax/features/external-general-entities", false) }
            runCatching { setFeature("http://xml.org/sax/features/external-parameter-entities", false) }
            runCatching { setAttribute("http://javax.xml.XMLConstants/property/accessExternalDTD", "") }
            runCatching { setAttribute("http://javax.xml.XMLConstants/property/accessExternalSchema", "") }
            runCatching { isXIncludeAware = false }
            runCatching { isExpandEntityReferences = false }
        }
        val document = text.byteInputStream(Charsets.UTF_8).use { factory.newDocumentBuilder().parse(it) }
        val nodes = document.getElementsByTagName("setting")
        for (index in 0 until nodes.length) {
            val element = nodes.item(index)
            if (element.attributes?.getNamedItem("id")?.nodeValue == "applied_version") {
                return element.textContent?.trim()?.takeIf { it.matches(VERSION_PATTERN) }
            }
        }
        return null
    }

    private companion object {
        const val KODI_PACKAGE = "org.xbmc.kodi"
        const val MAX_SETTINGS_BYTES = 128L * 1024L
        val VERSION_PATTERN = Regex("^[A-Za-z0-9._-]{1,64}$")
    }
}

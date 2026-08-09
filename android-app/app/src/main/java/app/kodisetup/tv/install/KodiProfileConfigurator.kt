package app.kodisetup.tv.install

import org.w3c.dom.Document
import org.w3c.dom.Element
import java.io.File
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import javax.xml.XMLConstants
import javax.xml.parsers.DocumentBuilderFactory
import javax.xml.transform.OutputKeys
import javax.xml.transform.TransformerFactory
import javax.xml.transform.dom.DOMSource
import javax.xml.transform.stream.StreamResult

data class KodiProfileUpdate(val changed: Boolean, val settingsFile: File)

/**
 * Applies the single Kodi preference required before the signed Bootstrap can run.
 *
 * This is intentionally not a general Kodi settings writer. The caller supplies only
 * Kodi's compatibility package ID, and this class can mutate only
 * `addons.unknownsources`.
 */
class KodiProfileConfigurator(private val externalStorageRoot: File) {
    fun enableUnknownSources(kodiPackageName: String): KodiProfileUpdate {
        require(kodiPackageName == KODI_PACKAGE) { "Unsupported Kodi package identity" }
        val settingsFile = File(
            externalStorageRoot,
            "Android/data/$KODI_PACKAGE/files/.kodi/userdata/guisettings.xml",
        )
        val original = readExistingBytes(settingsFile)
        val merged = mergeUnknownSources(original)
        val changed = !original.contentEquals(merged)
        if (changed) writeAtomically(merged, settingsFile)
        return KodiProfileUpdate(changed, settingsFile)
    }

    private fun readExistingBytes(settingsFile: File): ByteArray {
        require(settingsFile.isFile) {
            "Open Kodi once to create its profile, then return and prepare the bootstrap again"
        }
        require(settingsFile.length() <= MAX_SETTINGS_BYTES) { "Kodi guisettings.xml is unexpectedly large" }
        return settingsFile.readBytes()
    }

    private fun writeAtomically(contents: ByteArray, settingsFile: File) {
        val parent = requireNotNull(settingsFile.parentFile)
        require(parent.exists() || parent.mkdirs()) { "Kodi profile directory could not be created" }
        val pending = File(parent, settingsFile.name + ".starlane-new")
        val backup = File(parent, settingsFile.name + ".starlane-backup")
        pending.delete()
        require(!backup.exists()) { "An unresolved Kodi settings backup already exists" }
        try {
            pending.writeBytes(contents)
            require(settingsFile.renameTo(backup)) { "Kodi guisettings.xml could not be preserved" }
            if (!pending.renameTo(settingsFile)) {
                backup.renameTo(settingsFile)
                error("Kodi guisettings.xml could not be updated")
            }
            backup.delete()
        } finally {
            pending.delete()
            if (!settingsFile.exists() && backup.exists()) backup.renameTo(settingsFile)
        }
    }

    companion object {
        private const val KODI_PACKAGE = "org.xbmc.kodi"
        private const val SETTING_ID = "addons.unknownsources"
        private const val MAX_SETTINGS_BYTES = 2L * 1024 * 1024

        fun mergeUnknownSources(original: ByteArray?): ByteArray {
            require(original == null || original.size <= MAX_SETTINGS_BYTES) { "Kodi guisettings.xml is unexpectedly large" }
            val document = if (original == null) documentBuilder().newDocument().also {
                it.appendChild(it.createElement("settings"))
            } else {
                val source = original.toString(Charsets.UTF_8)
                require(!source.contains("<!DOCTYPE", ignoreCase = true)) { "Kodi guisettings.xml must not contain a document type" }
                require(!source.contains("<!ENTITY", ignoreCase = true)) { "Kodi guisettings.xml must not contain entities" }
                ByteArrayInputStream(original).use { documentBuilder().parse(it) }
            }
        val settings = document.documentElement
        require(settings.tagName == "settings") { "Kodi guisettings.xml has an unexpected root" }

        val matches = (0 until settings.childNodes.length)
            .map { settings.childNodes.item(it) }
            .filterIsInstance<Element>()
            .filter { it.tagName == "setting" && it.getAttribute("id") == SETTING_ID }
        require(matches.size <= 1) { "Kodi guisettings.xml contains duplicate Unknown Sources settings" }

        val existing = matches.singleOrNull()
        // Kodi treats default="true" as the serialized default, not a user choice.
        // Leaving that attribute on this one fixed setting lets Kodi restore `false`
        // after the next launch. Preserve every other setting and attribute exactly.
        if (existing?.textContent?.trim() == "true" && !existing.hasAttribute("default") && original != null) return original

        val target = existing ?: document.createElement("setting").also {
            it.setAttribute("id", SETTING_ID)
            settings.appendChild(it)
        }
        target.textContent = "true"
        target.removeAttribute("default")
        val output = ByteArrayOutputStream()
        transformer().transform(DOMSource(document), StreamResult(output))
        return output.toByteArray()
        }

        private fun documentBuilder() = DocumentBuilderFactory.newInstance().also { factory ->
        factory.isNamespaceAware = false
        runCatching { factory.isXIncludeAware = false }
        runCatching { factory.setExpandEntityReferences(false) }
        runCatching {
            factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true)
        }
        runCatching {
            factory.setFeature("http://xml.org/sax/features/external-general-entities", false)
        }
        runCatching {
            factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false)
        }
        }.newDocumentBuilder()

        private fun transformer() = TransformerFactory.newInstance().apply {
                runCatching { setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true) }
                runCatching { setAttribute("http://javax.xml.XMLConstants/property/accessExternalDTD", "") }
                runCatching { setAttribute("http://javax.xml.XMLConstants/property/accessExternalStylesheet", "") }
            }.newTransformer().apply {
                setOutputProperty(OutputKeys.ENCODING, "UTF-8")
                setOutputProperty(OutputKeys.INDENT, "yes")
            }
    }
}

package app.kodisetup.tv.install

import org.w3c.dom.Element
import java.io.File
import java.nio.charset.CodingErrorAction
import java.security.MessageDigest
import java.util.Properties
import java.util.zip.CRC32
import java.util.zip.ZipFile
import javax.xml.parsers.DocumentBuilderFactory

data class FixedBootstrapResult(val version: String, val alreadyInstalled: Boolean)

object FixedBootstrapEligibility {
    fun usesAutomaticPath(apiLevel: Int, strictConsent: Boolean): Boolean = apiLevel in 25..28 && strictConsent
    fun requireEligible(apiLevel: Int, strictConsent: Boolean, storagePermission: Boolean, kodiInstalled: Boolean, processStateKnown: Boolean, kodiActive: Boolean) {
        require(usesAutomaticPath(apiLevel, strictConsent)) { "Fixed Bootstrap automation is unavailable" }
        require(storagePermission) { "Visible storage permission is required" }
        require(kodiInstalled) { "Official Kodi is not installed" }
        require(processStateKnown) { "Kodi running state is ambiguous" }
        require(!kodiActive) { "Close Kodi completely before automatic Bootstrap installation" }
    }
}

/** Fixed-target API 25-28 transaction. It has no caller-selectable package, path, add-on ID, or setting. */
class FixedBootstrapTransaction(
    private val externalStorageRoot: File,
    private val fault: (String) -> Unit = {},
) {
    fun install(archive: File, manifestSha256: String, gate: () -> Unit): FixedBootstrapResult {
        require(archive.isFile && archive.length() in 1..MAX_ARCHIVE_BYTES) { "Bootstrap archive is unavailable or oversized" }
        require(sha256(archive) == manifestSha256.lowercase()) { "Bootstrap hash mismatch" }
        gate()
        recoverInterrupted(gate)
        val validated = validateArchive(archive)
        require(sha256(archive) == manifestSha256.lowercase()) { "Bootstrap archive changed during validation" }
        val paths = fixedPaths()
        val coldInstall = !paths.profile.exists()
        if (!coldInstall) {
            require(paths.profile.isDirectory && paths.settings.isFile && File(paths.profile, "userdata").isDirectory && File(paths.profile, "addons").isDirectory) {
                "Kodi profile is partial or ambiguous; open and close Kodi before retrying"
            }
        }
        val created = paths.requiredDirectories.filterNot(File::exists)
        paths.requiredDirectories.filter(File::exists).forEach(::requireCanonicalObject)
        require(!paths.settings.exists() || paths.settings.isFile) { "Kodi settings path is not a regular file" }
        require(!paths.addon.exists() || paths.addon.isDirectory) { "Existing Bootstrap path is not a directory" }
        val removeOwnedAutoexec = paths.autoexec.isFile && paths.autoexec.readBytes().contentEquals(OWNED_AUTOEXEC)
        if (removeOwnedAutoexec) requireCanonicalObject(paths.autoexec)

        gate()
        require(paths.transaction.mkdir()) { "Bootstrap transaction could not be created" }
        val journal = Journal(paths.settings.exists(), paths.addon.exists(), paths.autoexec.exists(), removeOwnedAutoexec, created.map { relative(it) })
        try {
            writeJournal(paths, journal, gate)
            created.forEach { directory -> gate(); require(directory.mkdir()) { "Canonical Kodi profile directory could not be created" }; fault("created:${relative(directory)}") }
            gate()
            archive.inputStream().use { input -> paths.archiveCopy.outputStream().use { input.copyTo(it) } }
            require(paths.archiveCopy.length() == archive.length() && sha256(paths.archiveCopy) == manifestSha256.lowercase()) { "Immutable Bootstrap staging failed" }
            val immutableValidated = validateArchive(paths.archiveCopy)
            require(immutableValidated.version == validated.version && immutableValidated.treeDigest == validated.treeDigest) { "Bootstrap archive changed before staging" }
            fault("archive-copied")
            val original = paths.settings.takeIf(File::isFile)?.readBytes()
            original?.let { gate(); paths.originalSettings.writeBytes(it); fault("original-settings") }
            val merged = KodiProfileConfigurator.mergeUnknownSources(original)
            gate(); paths.stagedSettings.writeBytes(merged); fault("staged-settings")
            gate(); require(paths.stagedAddon.mkdir()) { "Bootstrap staging directory could not be created" }
            extractValidated(paths.archiveCopy, immutableValidated, paths.stagedAddon, gate)
            fault("staged-addon")
            require(treeDigest(paths.stagedAddon) == immutableValidated.treeDigest) { "Staged Bootstrap verification failed" }

            val alreadyInstalled = if (paths.addon.exists()) {
                require(treeDigest(paths.addon) == immutableValidated.treeDigest) { "A conflicting repository.kodisetup installation already exists" }
                true
            } else false
            gate()
            require(sha256(paths.stagedSettings) == sha256(merged)) { "Staged Kodi settings verification failed" }
            if (paths.settings.exists()) require(paths.settings.renameTo(paths.displacedSettings)) { "Kodi settings could not be journaled" }
            fault("settings-displaced")
            if (journal.removeOwnedAutoexec) {
                gate()
                require(paths.autoexec.renameTo(paths.displacedAutoexec)) { "Owned deprecated Kodi launcher could not be journaled" }
                fault("owned-autoexec-displaced")
            }
            gate()
            require(paths.stagedSettings.renameTo(paths.settings)) { "Kodi settings could not be committed" }
            fault("settings-committed")
            if (!alreadyInstalled) {
                gate()
                require(paths.stagedAddon.renameTo(paths.addon)) { "Bootstrap add-on could not be committed" }
                fault("addon-committed")
            }
            gate()
            require(sha256(paths.settings) == sha256(merged)) { "Committed Kodi settings verification failed" }
            require(treeDigest(paths.addon) == immutableValidated.treeDigest) { "Committed Bootstrap verification failed" }
            if (journal.removeOwnedAutoexec) require(!paths.autoexec.exists()) { "Deprecated owned Kodi launcher removal failed" }
            writeJournal(paths, journal.copy(phase = "COMMITTED"), gate)
            fault("committed")
            deleteFixedTree(paths.transaction)
            return FixedBootstrapResult(immutableValidated.version, alreadyInstalled)
        } catch (error: Throwable) {
            runCatching { rollback(paths, journal, gate) }.getOrElse { rollbackError -> error.addSuppressed(rollbackError) }
            throw error
        }
    }

    fun recoverInterrupted(gate: () -> Unit) {
        val paths = fixedPaths()
        if (!paths.transaction.exists()) return
        require(paths.transaction.isDirectory) { "Bootstrap transaction marker is not a directory" }
        if (!paths.journal.isFile) {
            require(paths.transaction.listFiles().orEmpty().all { it == paths.journalNew }) { "Unjournaled Bootstrap transaction is ambiguous" }
            deleteFixedTree(paths.transaction)
            return
        }
        val journal = readJournal(paths)
        rollback(paths, journal, gate)
    }

    private fun rollback(paths: Paths, journal: Journal, gate: () -> Unit) {
        gate()
        if (!journal.hadAddon && paths.addon.exists()) deleteFixedTree(paths.addon)
        if (journal.removeOwnedAutoexec && paths.displacedAutoexec.isFile) {
            require(!paths.autoexec.exists()) { "Kodi autoexec.py changed during rollback" }
            require(paths.displacedAutoexec.renameTo(paths.autoexec)) { "Owned deprecated Kodi launcher could not be restored" }
        } else if (!journal.hadAutoexec && paths.autoexec.isFile && paths.autoexec.readBytes().contentEquals(OWNED_AUTOEXEC)) {
            // Recover an interrupted transaction created by the deprecated v1 launcher candidate.
            requireCanonicalObject(paths.autoexec)
            require(paths.autoexec.delete()) { "Deprecated transaction-owned autoexec.py could not be removed" }
        }
        gate()
        if (journal.hadSettings) {
            if (paths.settings.exists()) require(paths.settings.delete()) { "Changed Kodi settings could not be rolled back" }
            val source = when {
                paths.displacedSettings.isFile -> paths.displacedSettings
                paths.originalSettings.isFile -> paths.originalSettings
                else -> error("Original Kodi settings are unavailable for rollback")
            }
            require(source.copyTo(paths.settings, overwrite = false).isFile) { "Original Kodi settings could not be restored" }
            require(paths.originalSettings.takeIf(File::isFile)?.let { sha256(it) } == sha256(paths.settings)) { "Kodi settings rollback verification failed" }
        } else if (paths.settings.exists()) {
            require(paths.settings.delete()) { "Transaction-created Kodi settings could not be removed" }
        }
        deleteFixedTree(paths.transaction)
        journal.createdDirectories.asReversed().forEach { relative ->
            val directory = fixedRelative(relative)
            if (directory.isDirectory && directory.list()?.isEmpty() == true) require(directory.delete()) { "Transaction-created directory could not be removed" }
        }
    }

    private fun validateArchive(archive: File): ValidatedArchive {
        val records = CentralDirectory.read(archive)
        require(records.size in 2..MAX_ENTRIES) { "Bootstrap archive entry count is invalid" }
        var expanded = 0L
        val names = HashSet<String>()
        val folded = HashSet<String>()
        records.forEach { record ->
            validatePath(record.name)
            require(names.add(record.name)) { "Duplicate Bootstrap path" }
            require(folded.add(record.name.lowercase())) { "Case-colliding Bootstrap path" }
            require(record.flags and 1 == 0) { "Encrypted Bootstrap entries are forbidden" }
            require(record.method == 0 || record.method == 8) { "Unsupported Bootstrap compression" }
            require(record.uncompressedSize <= MAX_ENTRY_BYTES) { "Bootstrap entry is oversized" }
            expanded += record.uncompressedSize
            require(expanded <= MAX_EXPANDED_BYTES) { "Bootstrap archive expands beyond its limit" }
            if (!record.directory && record.uncompressedSize > 0) {
                require(record.compressedSize > 0 && record.uncompressedSize <= record.compressedSize * MAX_RATIO) { "Bootstrap compression ratio is unsafe" }
            }
            require(record.regularOrDirectory) { "Bootstrap links and special files are forbidden" }
        }
        val addonRecord = records.singleOrNull { it.name == "$ROOT/addon.xml" }
            ?: error("Bootstrap archive must contain exactly one repository.kodisetup/addon.xml")
        val addonBytes = readEntry(archive, addonRecord)
        val version = validateAddonXml(addonBytes)
        val digestParts = records.filterNot { it.directory }.sortedBy { it.name }.associate { record ->
            record.name.removePrefix("$ROOT/") to sha256(readEntry(archive, record))
        }
        return ValidatedArchive(records, version, digestMap(digestParts))
    }

    private fun extractValidated(archive: File, validated: ValidatedArchive, destination: File, gate: () -> Unit) {
        ZipFile(archive).use { zip ->
            validated.records.sortedBy { it.name }.forEach { record ->
                if (record.name == "$ROOT/") return@forEach
                val relative = record.name.removePrefix("$ROOT/").trimEnd('/')
                if (relative.isEmpty()) return@forEach
                val target = File(destination, relative)
                require(target.canonicalPath.startsWith(destination.canonicalPath + File.separator)) { "Bootstrap path escaped staging" }
                gate()
                if (record.directory) require(target.mkdirs() || target.isDirectory) { "Bootstrap directory could not be staged" }
                else {
                    val parent = requireNotNull(target.parentFile)
                    require(parent.isDirectory || parent.mkdirs()) { "Bootstrap parent could not be staged" }
                    val entry = requireNotNull(zip.getEntry(record.name))
                    val crc = CRC32()
                    var written = 0L
                    zip.getInputStream(entry).use { input -> target.outputStream().use { output ->
                        val buffer = ByteArray(16 * 1024)
                        while (true) {
                            val count = input.read(buffer); if (count < 0) break
                            written += count; require(written <= record.uncompressedSize && written <= MAX_ENTRY_BYTES)
                            crc.update(buffer, 0, count); output.write(buffer, 0, count)
                        }
                    } }
                    require(written == record.uncompressedSize && crc.value == record.crc) { "Bootstrap entry verification failed" }
                }
            }
        }
    }

    private fun validateAddonXml(bytes: ByteArray): String {
        require(bytes.size <= MAX_ADDON_XML_BYTES)
        val text = bytes.toString(Charsets.UTF_8)
        require(!text.contains("<!DOCTYPE", true) && !text.contains("<!ENTITY", true)) { "Unsafe Bootstrap add-on XML" }
        val factory = DocumentBuilderFactory.newInstance().apply {
            // Fire OS's bundled parser does not implement every hardening feature.
            // DOCTYPE/ENTITY text is rejected above; apply additional parser guards
            // where the runtime supports them without turning capability detection
            // into a Bootstrap installation failure.
            runCatching { setFeature("http://apache.org/xml/features/disallow-doctype-decl", true) }
            runCatching { setFeature("http://xml.org/sax/features/external-general-entities", false) }
            runCatching { setFeature("http://xml.org/sax/features/external-parameter-entities", false) }
            runCatching { isXIncludeAware = false }
            runCatching { isExpandEntityReferences = false }
        }
        val root = bytes.inputStream().use { factory.newDocumentBuilder().parse(it).documentElement }
        require(root.tagName == "addon" && root.getAttribute("id") == ROOT) { "Bootstrap add-on identity mismatch" }
        val version = root.getAttribute("version")
        require(version.matches(Regex("^[0-9]+(?:\\.[0-9]+){1,3}(?:[-+][A-Za-z0-9.-]+)?$"))) { "Bootstrap add-on version is invalid" }
        return version
    }

    private fun validatePath(name: String) {
        require(name.length in 1..MAX_PATH && '\u0000' !in name && '\\' !in name) { "Unsafe Bootstrap path" }
        require(!name.startsWith('/') && !Regex("^[A-Za-z]:").containsMatchIn(name)) { "Absolute Bootstrap path" }
        val path = name.trimEnd('/')
        val parts = path.split('/')
        require(parts.firstOrNull() == ROOT && parts.none { it.isEmpty() || it == "." || it == ".." || it.length > MAX_SEGMENT }) { "Bootstrap path is outside its fixed root" }
    }

    private fun readEntry(archive: File, record: CentralRecord): ByteArray = ZipFile(archive).use { zip ->
        val entry = requireNotNull(zip.getEntry(record.name))
        zip.getInputStream(entry).use { input ->
            val bytes = input.readBytes()
            require(bytes.size.toLong() == record.uncompressedSize)
            bytes
        }
    }

    private fun treeDigest(root: File): String {
        require(root.isDirectory)
        val values = linkedMapOf<String, String>()
        root.walkTopDown().filter { it != root }.forEach { file ->
            requireCanonicalObject(file)
            val relative = file.relativeTo(root).invariantSeparatorsPath
            if (file.isFile) values[relative] = sha256(file) else require(file.isDirectory)
        }
        return digestMap(values)
    }

    private fun digestMap(values: Map<String, String>): String = sha256(values.toSortedMap().entries.joinToString("\n") { "${it.key.length}:${it.key}:${it.value}" }.toByteArray())
    private fun sha256(file: File) = file.inputStream().use { input ->
        val digest = MessageDigest.getInstance("SHA-256"); val buffer = ByteArray(16 * 1024)
        while (true) { val count = input.read(buffer); if (count < 0) break; digest.update(buffer, 0, count) }
        digest.digest().hex()
    }
    private fun sha256(bytes: ByteArray) = MessageDigest.getInstance("SHA-256").digest(bytes).hex()
    private fun ByteArray.hex() = joinToString("") { "%02x".format(it) }

    private fun fixedPaths(): Paths {
        val profile = fixedRelative("Android/data/$KODI_PACKAGE/files/.kodi")
        val transaction = fixedRelative(TRANSACTION)
        return Paths(
            profile,
            File(profile, "userdata/guisettings.xml"), File(profile, "userdata/autoexec.py"), File(profile, "addons/$ROOT"), transaction,
            File(transaction, "journal.properties"), File(transaction, "journal.new"),
            File(transaction, "archive.zip"), File(transaction, "original-settings"), File(transaction, "displaced-settings"),
            File(transaction, "staged-settings"), File(transaction, "displaced-autoexec.py"), File(transaction, "staged-addon"),
            listOf("Android", "Android/data", "Android/data/$KODI_PACKAGE", "Android/data/$KODI_PACKAGE/files", "Android/data/$KODI_PACKAGE/files/.kodi", "Android/data/$KODI_PACKAGE/files/.kodi/userdata", "Android/data/$KODI_PACKAGE/files/.kodi/addons").map(::fixedRelative),
        )
    }

    private fun fixedRelative(relative: String): File {
        require(relative in ALLOWED_RELATIVES || relative == TRANSACTION)
        val file = File(externalStorageRoot, relative)
        require(file.canonicalPath.startsWith(externalStorageRoot.canonicalPath + File.separator))
        return file
    }
    private fun relative(file: File) = file.relativeTo(externalStorageRoot).invariantSeparatorsPath
    private fun requireCanonicalObject(file: File) { require(file.absoluteFile.normalize().path == file.canonicalFile.path) { "Symbolic or redirected Kodi path is forbidden" } }

    private fun writeJournal(paths: Paths, journal: Journal, gate: () -> Unit) {
        gate()
        val properties = Properties().apply {
            setProperty("schema", "1"); setProperty("phase", journal.phase)
            setProperty("hadSettings", journal.hadSettings.toString()); setProperty("hadAddon", journal.hadAddon.toString())
            setProperty("hadAutoexec", journal.hadAutoexec.toString())
            setProperty("removeOwnedAutoexec", journal.removeOwnedAutoexec.toString())
            setProperty("created", journal.createdDirectories.joinToString("|"))
        }
        paths.journalNew.outputStream().use { properties.store(it, null) }
        if (paths.journal.exists()) require(paths.journal.delete())
        require(paths.journalNew.renameTo(paths.journal))
    }
    private fun readJournal(paths: Paths): Journal {
        require(paths.journal.isFile && paths.journal.length() <= 16 * 1024)
        val properties = Properties().also { value -> paths.journal.inputStream().use(value::load) }
        require(properties.getProperty("schema") == "1")
        val created = properties.getProperty("created", "").split('|').filter(String::isNotEmpty)
        require(created.all { it in ALLOWED_RELATIVES })
        return Journal(
            properties.getProperty("hadSettings").toBooleanStrict(), properties.getProperty("hadAddon").toBooleanStrict(),
            properties.getProperty("hadAutoexec").toBooleanStrict(), properties.getProperty("removeOwnedAutoexec", "false").toBooleanStrict(),
            created, properties.getProperty("phase"),
        )
    }
    private fun deleteFixedTree(root: File) {
        if (!root.exists()) return
        require(root.canonicalPath == fixedPaths().transaction.canonicalPath || root.canonicalPath == fixedPaths().addon.canonicalPath)
        root.walkBottomUp().forEach { require(it.delete()) { "Fixed transaction path could not be removed" } }
    }

    private data class Journal(
        val hadSettings: Boolean, val hadAddon: Boolean, val hadAutoexec: Boolean, val removeOwnedAutoexec: Boolean,
        val createdDirectories: List<String>, val phase: String = "PREPARED",
    )
    private data class Paths(
        val profile: File, val settings: File, val autoexec: File, val addon: File, val transaction: File, val journal: File, val journalNew: File,
        val archiveCopy: File, val originalSettings: File, val displacedSettings: File, val stagedSettings: File,
        val displacedAutoexec: File, val stagedAddon: File,
        val requiredDirectories: List<File>,
    )
    private data class ValidatedArchive(val records: List<CentralRecord>, val version: String, val treeDigest: String)

    private companion object {
        const val KODI_PACKAGE = "org.xbmc.kodi"
        const val ROOT = "repository.kodisetup"
        const val TRANSACTION = ".starlane-repository-kodisetup-transaction"
        const val MAX_ARCHIVE_BYTES = 25L * 1024 * 1024
        const val MAX_EXPANDED_BYTES = 64L * 1024 * 1024
        const val MAX_ENTRY_BYTES = 16L * 1024 * 1024
        const val MAX_ADDON_XML_BYTES = 512 * 1024
        const val MAX_ENTRIES = 512
        const val MAX_RATIO = 100L
        const val MAX_PATH = 240
        const val MAX_SEGMENT = 128
        val OWNED_AUTOEXEC = """# Starlane Movies owned one-shot Bootstrap launcher v1
import os
import xbmc
import xbmcvfs

xbmc.executebuiltin("RunScript(repository.kodisetup)")
_starlane_autoexec = xbmcvfs.translatePath("special://profile/autoexec.py")
try:
    os.remove(_starlane_autoexec)
except OSError:
    pass
""".toByteArray(Charsets.UTF_8)
        val ALLOWED_RELATIVES = setOf(
            "Android", "Android/data", "Android/data/$KODI_PACKAGE", "Android/data/$KODI_PACKAGE/files",
            "Android/data/$KODI_PACKAGE/files/.kodi", "Android/data/$KODI_PACKAGE/files/.kodi/userdata",
            "Android/data/$KODI_PACKAGE/files/.kodi/addons",
        )
    }
}

private data class CentralRecord(
    val name: String, val flags: Int, val method: Int, val crc: Long, val compressedSize: Long,
    val uncompressedSize: Long, val directory: Boolean, val regularOrDirectory: Boolean,
)

private object CentralDirectory {
    fun read(file: File): List<CentralRecord> {
        val bytes = file.readBytes()
        val eocd = (bytes.size - 22 downTo maxOf(0, bytes.size - 65_557)).firstOrNull { u32(bytes, it) == 0x06054b50L }
            ?: error("Bootstrap ZIP end record is missing")
        require(u16(bytes, eocd + 4) == 0 && u16(bytes, eocd + 6) == 0) { "Multi-disk Bootstrap ZIP is forbidden" }
        val count = u16(bytes, eocd + 10)
        require(count == u16(bytes, eocd + 8) && count <= 512)
        val size = u32(bytes, eocd + 12).toInt(); var offset = u32(bytes, eocd + 16).toInt()
        require(offset >= 0 && size >= 0 && offset + size <= eocd)
        val end = offset + size
        val result = ArrayList<CentralRecord>(count)
        repeat(count) {
            require(offset + 46 <= end && u32(bytes, offset) == 0x02014b50L) { "Malformed Bootstrap central directory" }
            val flags = u16(bytes, offset + 8); val method = u16(bytes, offset + 10)
            val crc = u32(bytes, offset + 16); val compressed = u32(bytes, offset + 20); val expanded = u32(bytes, offset + 24)
            val nameLength = u16(bytes, offset + 28); val extraLength = u16(bytes, offset + 30); val commentLength = u16(bytes, offset + 32)
            require(offset + 46 + nameLength + extraLength + commentLength <= end)
            val nameBytes = bytes.copyOfRange(offset + 46, offset + 46 + nameLength)
            val decoder = Charsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT)
            val name = decoder.decode(java.nio.ByteBuffer.wrap(nameBytes)).toString()
            require(name.toByteArray(Charsets.UTF_8).contentEquals(nameBytes)) { "Non-UTF-8 Bootstrap path" }
            val external = u32(bytes, offset + 38)
            val madeBy = u16(bytes, offset + 4); val unix = (madeBy ushr 8) == 3
            val mode = ((external ushr 16) and 0xffff).toInt(); val type = mode and 0xf000
            val directory = name.endsWith('/')
            // Reproducible release ZIPs intentionally store POSIX permissions (0644)
            // without file-type bits. Treat type 0 as a regular file/directory while
            // still rejecting explicit link, device, socket and FIFO types.
            val regular = !unix || mode == 0 || type == 0 || type == 0x8000 || (directory && type == 0x4000)
            val localOffset = u32(bytes, offset + 42).toInt()
            require(localOffset >= 0 && localOffset + 30 <= bytes.size && u32(bytes, localOffset) == 0x04034b50L)
            require(u16(bytes, localOffset + 6) == flags && u16(bytes, localOffset + 8) == method)
            val localNameLength = u16(bytes, localOffset + 26); val localExtra = u16(bytes, localOffset + 28)
            require(localOffset + 30 + localNameLength + localExtra <= bytes.size)
            require(bytes.copyOfRange(localOffset + 30, localOffset + 30 + localNameLength).contentEquals(nameBytes))
            result += CentralRecord(name, flags, method, crc, compressed, expanded, directory, regular)
            offset += 46 + nameLength + extraLength + commentLength
        }
        require(offset == end)
        return result
    }

    private fun u16(bytes: ByteArray, offset: Int): Int {
        require(offset >= 0 && offset + 2 <= bytes.size)
        return (bytes[offset].toInt() and 0xff) or ((bytes[offset + 1].toInt() and 0xff) shl 8)
    }
    private fun u32(bytes: ByteArray, offset: Int): Long {
        require(offset >= 0 && offset + 4 <= bytes.size)
        return u16(bytes, offset).toLong() or (u16(bytes, offset + 2).toLong() shl 16)
    }
}

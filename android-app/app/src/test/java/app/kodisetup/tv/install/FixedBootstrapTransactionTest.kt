package app.kodisetup.tv.install

import org.junit.Assert.*
import org.junit.Assume.assumeNoException
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File
import java.nio.file.Files
import java.security.MessageDigest
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

class FixedBootstrapTransactionTest {
    @get:Rule val temporary = TemporaryFolder()

    @Test fun `cold install creates only minimal canonical profile then is idempotent`() {
        val root = temporary.newFolder("cold")
        val archive = archive(root)
        val transaction = FixedBootstrapTransaction(root)
        val first = transaction.install(archive, sha256(archive)) {}
        val settings = settings(root)
        assertEquals("1.2.3", first.version)
        assertTrue(settings.readText().contains("addons.unknownsources"))
        assertTrue(settings.readText().contains(">true<"))
        assertTrue(File(profile(root), "addons/repository.kodisetup/addon.xml").isFile)
        val autoexec = File(profile(root), "userdata/autoexec.py")
        assertFalse(autoexec.exists())
        assertFalse(File(root, ".starlane-repository-kodisetup-transaction").exists())

        val second = transaction.install(archive, sha256(archive)) {}
        assertTrue(second.alreadyInstalled)
        assertFalse(autoexec.exists())
    }

    @Test fun `pre-existing user autoexec is preserved and ignored`() {
        val root = temporary.newFolder("autoexec-conflict")
        createProfile(root, "<settings><setting id=\"addons.unknownsources\">false</setting></settings>")
        val autoexec = File(profile(root), "userdata/autoexec.py")
        val userBytes = "# user-owned\nprint('keep')\n".toByteArray()
        autoexec.writeBytes(userBytes)
        val zip = archive(root)

        assertTrue(runCatching { FixedBootstrapTransaction(root).install(zip, sha256(zip)) {} }.isSuccess)
        assertArrayEquals(userBytes, autoexec.readBytes())
        assertTrue(File(profile(root), "addons/repository.kodisetup").exists())
    }

    @Test fun `exact deprecated owned launcher is removed while foreign content is untouched`() {
        val root = temporary.newFolder("autoexec-owned")
        createProfile(root, "<settings><setting id=\"addons.unknownsources\">false</setting></settings>")
        val autoexec = File(profile(root), "userdata/autoexec.py")
        autoexec.writeBytes(ownedAutoexec())
        val zip = archive(root)
        FixedBootstrapTransaction(root).install(zip, sha256(zip)) {}
        assertFalse(autoexec.exists())
    }

    @Test fun `deprecated owned launcher is restored if the replacement transaction fails`() {
        val root = temporary.newFolder("autoexec-owned-rollback")
        createProfile(root, "<settings><setting id=\"addons.unknownsources\">false</setting></settings>")
        val autoexec = File(profile(root), "userdata/autoexec.py")
        val original = ownedAutoexec()
        autoexec.writeBytes(original)
        val zip = archive(root)

        assertTrue(runCatching {
            FixedBootstrapTransaction(root) { if (it == "owned-autoexec-displaced") error("injected") }.install(zip, sha256(zip)) {}
        }.isFailure)
        assertArrayEquals(original, autoexec.readBytes())
    }

    @Test fun `existing settings merge preserves unrelated values`() {
        val root = temporary.newFolder("existing")
        createProfile(root, "<settings><setting id=\"lookandfeel.skin\">skin.estuary</setting><setting id=\"addons.unknownsources\">false</setting></settings>")
        FixedBootstrapTransaction(root).install(archive(root), sha256(archiveFile(root))) {}
        val value = settings(root).readText()
        assertTrue(value.contains("skin.estuary"))
        assertTrue(value.contains(">true<"))
    }

    @Test fun `partial profile and conflicting addon are refused unchanged`() {
        val partialRoot = temporary.newFolder("partial")
        File(profile(partialRoot), "userdata").mkdirs()
        val partialArchive = archive(partialRoot)
        assertTrue(runCatching { FixedBootstrapTransaction(partialRoot).install(partialArchive, sha256(partialArchive)) {} }.isFailure)
        assertFalse(settings(partialRoot).exists())

        val conflictRoot = temporary.newFolder("conflict")
        val original = "<settings><setting id=\"addons.unknownsources\">false</setting></settings>".toByteArray()
        createProfile(conflictRoot, original.toString(Charsets.UTF_8))
        val conflict = File(profile(conflictRoot), "addons/repository.kodisetup").also { it.mkdirs() }
        File(conflict, "foreign.txt").writeText("preserve")
        val conflictArchive = archive(conflictRoot)
        assertTrue(runCatching { FixedBootstrapTransaction(conflictRoot).install(conflictArchive, sha256(conflictArchive)) {} }.isFailure)
        assertArrayEquals(original, settings(conflictRoot).readBytes())
        assertEquals("preserve", File(conflict, "foreign.txt").readText())
    }

    @Test fun `archive traversal extra roots backslashes case collisions and bad identity are rejected before mutation`() {
        val attacks = listOf(
            listOf("repository.kodisetup/addon.xml" to addonXml(), "repository.kodisetup/../escape" to "x"),
            listOf("repository.kodisetup/addon.xml" to addonXml(), "other.root/file" to "x"),
            listOf("repository.kodisetup/addon.xml" to addonXml(), "repository.kodisetup\\escape" to "x"),
            listOf("repository.kodisetup/addon.xml" to addonXml(), "/repository.kodisetup/absolute" to "x"),
            listOf("repository.kodisetup/addon.xml" to addonXml(), "C:/repository.kodisetup/drive" to "x"),
            listOf("repository.kodisetup/addon.xml" to addonXml(), "repository.kodisetup/${"x".repeat(200)}" to "x"),
            listOf("repository.kodisetup/addon.xml" to addonXml(), "repository.kodisetup/A" to "x", "repository.kodisetup/a" to "x"),
            listOf("repository.kodisetup/addon.xml" to "<addon id=\"other\" version=\"1.2.3\"/>", "repository.kodisetup/service.py" to "x"),
        )
        attacks.forEachIndexed { index, entries ->
            val root = temporary.newFolder("attack-$index")
            val zip = zip(File(root, "attack.zip"), entries)
            assertTrue(runCatching { FixedBootstrapTransaction(root).install(zip, sha256(zip)) {} }.isFailure)
            assertFalse(profile(root).exists())
        }
    }

    @Test fun `encrypted links devices duplicates and compression bombs are rejected`() {
        val encryptedRoot = temporary.newFolder("encrypted")
        val encrypted = mutateFlags(archive(encryptedRoot), encrypted = true)
        assertTrue(runCatching { FixedBootstrapTransaction(encryptedRoot).install(encrypted, sha256(encrypted)) {} }.isFailure)

        listOf(0xA1FF, 0x21B6).forEachIndexed { index, mode ->
            val root = temporary.newFolder("special-$index")
            val special = mutateUnixMode(archive(root), mode)
            assertTrue(runCatching { FixedBootstrapTransaction(root).install(special, sha256(special)) {} }.isFailure)
        }

        val duplicateRoot = temporary.newFolder("duplicate")
        val duplicate = zip(File(duplicateRoot, "duplicate.zip"), listOf(
            "repository.kodisetup/addon.xml" to addonXml(), "repository.kodisetup/a" to "1", "repository.kodisetup/b" to "2",
        ))
        replaceAscii(duplicate, "repository.kodisetup/b", "repository.kodisetup/a")
        assertTrue(runCatching { FixedBootstrapTransaction(duplicateRoot).install(duplicate, sha256(duplicate)) {} }.isFailure)

        val bombRoot = temporary.newFolder("bomb")
        val bomb = zip(File(bombRoot, "bomb.zip"), listOf(
            "repository.kodisetup/addon.xml" to addonXml(), "repository.kodisetup/bomb" to "A".repeat(200_000),
        ))
        assertTrue(runCatching { FixedBootstrapTransaction(bombRoot).install(bomb, sha256(bomb)) {} }.isFailure)
    }

    @Test fun `permission-only unix metadata from reproducible release is accepted`() {
        val root = temporary.newFolder("permission-only")
        val archive = mutateAllUnixModes(archive(root), 0x01A4)

        val result = FixedBootstrapTransaction(root).install(archive, sha256(archive)) {}

        assertEquals("1.2.3", result.version)
        assertTrue(File(profile(root), "addons/repository.kodisetup/addon.xml").isFile)
    }

    @Test fun `fault injection restores exact prior bytes at every commit boundary`() {
        listOf("original-settings", "staged-settings", "staged-addon", "settings-displaced", "settings-committed", "addon-committed", "committed").forEachIndexed { index, stage ->
            val root = temporary.newFolder("fault-$index")
            val original = "<settings version=\"2\"><setting id=\"custom\">exact-$index</setting></settings>".toByteArray()
            createProfile(root, original.toString(Charsets.UTF_8))
            val zip = archive(root)
            val error = runCatching {
                FixedBootstrapTransaction(root) { point -> if (point == stage) error("injected") }.install(zip, sha256(zip)) {}
            }.exceptionOrNull()
            assertNotNull("fault $stage must fire", error)
            assertArrayEquals("fault $stage", original, settings(root).readBytes())
            assertFalse(File(profile(root), "addons/repository.kodisetup").exists())
            assertFalse(File(profile(root), "userdata/autoexec.py").exists())
            assertFalse(File(root, ".starlane-repository-kodisetup-transaction").exists())
        }
    }

    @Test fun `interrupted rollback is recovered before retry`() {
        val root = temporary.newFolder("recover")
        val original = "<settings><setting id=\"custom\">exact</setting></settings>".toByteArray()
        createProfile(root, original.toString(Charsets.UTF_8))
        val zip = archive(root)
        var faulted = false
        runCatching {
            FixedBootstrapTransaction(root) { point -> if (point == "settings-committed") { faulted = true; error("crash") } }
                .install(zip, sha256(zip)) { if (faulted) error("process unavailable") }
        }
        assertTrue(File(root, ".starlane-repository-kodisetup-transaction").exists())
        FixedBootstrapTransaction(root).recoverInterrupted {}
        assertArrayEquals(original, settings(root).readBytes())
        assertFalse(File(profile(root), "addons/repository.kodisetup").exists())
    }

    @Test fun `symbolic canonical profile component is rejected`() {
        val root = temporary.newFolder("symlink")
        val outside = temporary.newFolder("outside")
        val android = File(root, "Android").toPath()
        try { Files.createSymbolicLink(android, outside.toPath()) } catch (error: Exception) { assumeNoException(error) }
        val zip = archive(root)
        assertTrue(runCatching { FixedBootstrapTransaction(root).install(zip, sha256(zip)) {} }.isFailure)
    }

    @Test fun `stale gate and wrong manifest hash mutate nothing`() {
        val root = temporary.newFolder("gates")
        val zip = archive(root)
        assertTrue(runCatching { FixedBootstrapTransaction(root).install(zip, "00".repeat(32)) {} }.isFailure)
        assertTrue(runCatching { FixedBootstrapTransaction(root).install(zip, sha256(zip)) { error("revoked") } }.isFailure)
        assertFalse(profile(root).exists())
    }

    private fun archive(root: File): File = zip(File(root, "repository.zip"), listOf(
        "repository.kodisetup/addon.xml" to addonXml(),
        "repository.kodisetup/service.py" to "print('fixed')",
        "repository.kodisetup/resources/settings.xml" to "<settings />",
    ))
    private fun archiveFile(root: File) = File(root, "repository.zip")
    private fun addonXml() = "<addon id=\"repository.kodisetup\" version=\"1.2.3\" name=\"Bootstrap\" provider-name=\"Starlane\" />"
    private fun ownedAutoexec() = """# Starlane Movies owned one-shot Bootstrap launcher v1
import os
import xbmc
import xbmcvfs

xbmc.executebuiltin("RunScript(repository.kodisetup)")
_starlane_autoexec = xbmcvfs.translatePath("special://profile/autoexec.py")
try:
    os.remove(_starlane_autoexec)
except OSError:
    pass
""".toByteArray()
    private fun zip(file: File, entries: List<Pair<String, String>>): File {
        ZipOutputStream(file.outputStream()).use { output -> entries.forEach { (name, value) ->
            output.putNextEntry(ZipEntry(name)); output.write(value.toByteArray()); output.closeEntry()
        } }
        return file
    }
    private fun createProfile(root: File, xml: String) {
        settings(root).parentFile!!.mkdirs(); settings(root).writeText(xml)
        File(profile(root), "addons").mkdirs()
    }
    private fun profile(root: File) = File(root, "Android/data/org.xbmc.kodi/files/.kodi")
    private fun settings(root: File) = File(profile(root), "userdata/guisettings.xml")
    private fun sha256(file: File): String = MessageDigest.getInstance("SHA-256").digest(file.readBytes()).joinToString("") { "%02x".format(it) }
    private fun mutateFlags(file: File, encrypted: Boolean): File {
        val bytes = file.readBytes()
        scanSignatures(bytes, 0x04034b50) { offset -> if (encrypted) put16(bytes, offset + 6, get16(bytes, offset + 6) or 1) }
        scanSignatures(bytes, 0x02014b50) { offset -> if (encrypted) put16(bytes, offset + 8, get16(bytes, offset + 8) or 1) }
        file.writeBytes(bytes); return file
    }
    private fun mutateUnixMode(file: File, mode: Int): File {
        val bytes = file.readBytes()
        var changed = false
        scanSignatures(bytes, 0x02014b50) { offset -> if (!changed) {
            bytes[offset + 5] = 3
            put32(bytes, offset + 38, mode.toLong() shl 16)
            changed = true
        } }
        file.writeBytes(bytes); return file
    }
    private fun mutateAllUnixModes(file: File, mode: Int): File {
        val bytes = file.readBytes()
        scanSignatures(bytes, 0x02014b50) { offset ->
            bytes[offset + 5] = 3
            put32(bytes, offset + 38, mode.toLong() shl 16)
        }
        file.writeBytes(bytes); return file
    }
    private fun replaceAscii(file: File, from: String, to: String) {
        require(from.length == to.length)
        val bytes = file.readBytes(); val needle = from.toByteArray(); val replacement = to.toByteArray()
        for (offset in 0..bytes.size - needle.size) if (bytes.copyOfRange(offset, offset + needle.size).contentEquals(needle)) replacement.copyInto(bytes, offset)
        file.writeBytes(bytes)
    }
    private fun scanSignatures(bytes: ByteArray, signature: Int, action: (Int) -> Unit) {
        for (offset in 0..bytes.size - 4) if (get32(bytes, offset).toInt() == signature) action(offset)
    }
    private fun get16(bytes: ByteArray, offset: Int) = (bytes[offset].toInt() and 0xff) or ((bytes[offset + 1].toInt() and 0xff) shl 8)
    private fun get32(bytes: ByteArray, offset: Int) = get16(bytes, offset).toLong() or (get16(bytes, offset + 2).toLong() shl 16)
    private fun put16(bytes: ByteArray, offset: Int, value: Int) { bytes[offset] = value.toByte(); bytes[offset + 1] = (value ushr 8).toByte() }
    private fun put32(bytes: ByteArray, offset: Int, value: Long) { put16(bytes, offset, value.toInt()); put16(bytes, offset + 2, (value ushr 16).toInt()) }
}

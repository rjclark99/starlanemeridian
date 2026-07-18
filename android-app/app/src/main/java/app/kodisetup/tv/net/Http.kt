package app.kodisetup.tv.net

import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.io.ByteArrayOutputStream

object Http {
    fun getText(url: String, maxBytes: Int = 1024 * 1024): String {
        require(url.startsWith("https://"))
        val connection = URL(url).openConnection() as HttpURLConnection
        connection.connectTimeout = 15_000; connection.readTimeout = 20_000; connection.instanceFollowRedirects = true
        connection.setRequestProperty("User-Agent", "KodiSetupTv/1")
        connection.inputStream.use { input ->
            val output = ByteArrayOutputStream()
            val buffer = ByteArray(16 * 1024)
            while (true) { val count = input.read(buffer); if (count < 0) break; require(output.size() + count <= maxBytes) { "Response exceeds size limit" }; output.write(buffer, 0, count) }
            return output.toByteArray().decodeToString()
        }
    }

    fun download(url: String, destination: File, maxBytes: Long = 300L * 1024 * 1024) {
        require(url.startsWith("https://"))
        val connection = URL(url).openConnection() as HttpURLConnection
        connection.connectTimeout = 15_000; connection.readTimeout = 60_000; connection.instanceFollowRedirects = true
        connection.setRequestProperty("User-Agent", "KodiSetupTv/1")
        val declared = connection.contentLengthLong
        require(declared in -1..maxBytes) { "Package exceeds size limit" }
        destination.parentFile?.mkdirs()
        connection.inputStream.use { input -> destination.outputStream().use { output ->
            val buffer = ByteArray(1024 * 1024); var total = 0L
            while (true) { val count = input.read(buffer); if (count < 0) break; total += count; require(total <= maxBytes); output.write(buffer, 0, count) }
        } }
    }
}

package app.kodisetup.tv.install

import android.content.ContentValues
import android.content.Context
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import java.io.File

class BootstrapExporter(private val context: Context) {
    fun export(source: File, filename: String): String {
        require(filename.matches(Regex("^[A-Za-z0-9_.-]+\\.zip$")))
        return if (Build.VERSION.SDK_INT >= 29) {
            val values = ContentValues().apply { put(MediaStore.Downloads.DISPLAY_NAME, filename); put(MediaStore.Downloads.MIME_TYPE, "application/zip"); put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS); put(MediaStore.Downloads.IS_PENDING, 1) }
            val uri = requireNotNull(context.contentResolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values))
            try { context.contentResolver.openOutputStream(uri, "w")!!.use { output -> source.inputStream().use { it.copyTo(output) } }; values.clear(); values.put(MediaStore.Downloads.IS_PENDING, 0); context.contentResolver.update(uri, values, null, null); uri.toString() }
            catch (error: Exception) { context.contentResolver.delete(uri, null, null); throw error }
        } else {
            @Suppress("DEPRECATION") val downloads = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS)
            require(downloads.exists() || downloads.mkdirs())
            val destination = File(downloads, filename); source.copyTo(destination, overwrite = true); destination.absolutePath
        }
    }
}


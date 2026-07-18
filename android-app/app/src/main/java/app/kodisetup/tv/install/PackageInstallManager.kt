package app.kodisetup.tv.install

import android.app.PendingIntent
import android.content.*
import android.content.pm.PackageInstaller
import android.net.Uri
import android.os.Build
import android.provider.Settings
import java.io.File

class PackageInstallManager(private val context: Context) {
    fun canRequestInstalls(): Boolean = Build.VERSION.SDK_INT < 26 || context.packageManager.canRequestPackageInstalls()

    fun openUnknownSourcesSettings() {
        context.startActivity(Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES, Uri.parse("package:${context.packageName}")))
    }

    fun install(apk: File, expectedPackage: String) {
        require(canRequestInstalls()) { "Install unknown apps permission is required" }
        val params = PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL).apply { setAppPackageName(expectedPackage) }
        val installer = context.packageManager.packageInstaller
        val sessionId = installer.createSession(params)
        installer.openSession(sessionId).use { session ->
            apk.inputStream().use { input -> session.openWrite("package.apk", 0, apk.length()).use { output -> input.copyTo(output); session.fsync(output) } }
            val intent = Intent(context, InstallResultReceiver::class.java).putExtra("package", expectedPackage)
            val flags = PendingIntent.FLAG_UPDATE_CURRENT or if (Build.VERSION.SDK_INT >= 31) PendingIntent.FLAG_MUTABLE else 0
            val pending = PendingIntent.getBroadcast(context, sessionId, intent, flags)
            session.commit(pending.intentSender)
        }
    }
}

class InstallResultReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val status = intent.getIntExtra(PackageInstaller.EXTRA_STATUS, PackageInstaller.STATUS_FAILURE)
        val packageName = intent.getStringExtra("package") ?: "unknown"
        context.getSharedPreferences("install_status", Context.MODE_PRIVATE).edit()
            .putInt("$packageName.status", status)
            .putString("$packageName.message", intent.getStringExtra(PackageInstaller.EXTRA_STATUS_MESSAGE)).apply()
        if (status == PackageInstaller.STATUS_PENDING_USER_ACTION) {
            @Suppress("DEPRECATION") val confirmation = intent.getParcelableExtra<Intent>(Intent.EXTRA_INTENT)
            confirmation?.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            confirmation?.let(context::startActivity)
        }
    }
}

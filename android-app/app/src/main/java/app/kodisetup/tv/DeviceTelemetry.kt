package app.kodisetup.tv

import android.app.ActivityManager
import android.app.Application
import android.os.Build
import android.os.StatFs
import app.kodisetup.tv.net.ControlClient

class DeviceTelemetry(private val application: Application) {
    fun status(snapshot: SetupUiState, installPermission: Boolean, bootstrapReady: Boolean, automaticSetup: Boolean): ControlClient.Status {
        val storage = StatFs(application.filesDir.absolutePath)
        val memory = ActivityManager.MemoryInfo().also {
            (application.getSystemService(ActivityManager::class.java)).getMemoryInfo(it)
        }
        return ControlClient.Status(
            setupStep = snapshot.step.name,
            appVersion = BuildConfig.VERSION_CODE,
            configVersion = snapshot.manifest?.configVersion,
            errorCode = snapshot.error?.take(64),
            debridExpiry = snapshot.debridExpiry,
            setupPhase = if (snapshot.error == null) snapshot.phase.name else SetupPhase.ERROR.name,
            progressPercent = snapshot.progress.coerceIn(0, 100),
            statusMessage = snapshot.message.take(160),
            busy = snapshot.busy,
            manufacturer = Build.MANUFACTURER.take(64),
            product = Build.PRODUCT.take(96),
            apiLevel = Build.VERSION.SDK_INT,
            architecture = (Build.SUPPORTED_ABIS.firstOrNull() ?: "unknown").take(32),
            securityPatch = Build.VERSION.SECURITY_PATCH.take(16),
            freeStorageMb = bytesToMb(storage.availableBytes),
            totalStorageMb = bytesToMb(storage.totalBytes),
            totalMemoryMb = bytesToMb(memory.totalMem),
            kodiVersion = packageVersion("org.xbmc.kodi"),
            protonVersion = packageVersion("ch.protonvpn.android"),
            installPermission = installPermission,
            bootstrapReady = bootstrapReady,
            automaticSetup = automaticSetup,
        )
    }

    private fun packageVersion(packageName: String): String? = runCatching {
        application.packageManager.getPackageInfo(packageName, 0).versionName?.take(64)
    }.getOrNull()

    private fun bytesToMb(value: Long): Int = (value / (1024L * 1024L)).coerceIn(0, 10_000_000).toInt()
}

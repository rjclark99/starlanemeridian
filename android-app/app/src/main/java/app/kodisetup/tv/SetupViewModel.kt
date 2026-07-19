package app.kodisetup.tv

import android.app.Application
import android.content.Intent
import android.content.Context
import android.content.pm.PackageInstaller
import android.net.Uri
import android.os.Build
import android.Manifest
import android.content.pm.PackageManager
import androidx.core.content.ContextCompat
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import app.kodisetup.tv.install.PackageInstallManager
import app.kodisetup.tv.install.BootstrapExporter
import app.kodisetup.tv.model.*
import app.kodisetup.tv.net.Http
import app.kodisetup.tv.net.ControlClient
import app.kodisetup.tv.net.RealDebridClient
import app.kodisetup.tv.security.DeviceIdentity
import app.kodisetup.tv.security.TokenVault
import app.kodisetup.tv.security.ManifestSecurity
import app.kodisetup.tv.security.ManifestRevokedException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.Job
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonPrimitive
import java.io.File

enum class SetupPhase {
    READY, PAIRING, VERIFYING_CONFIGURATION, CONFIGURATION_VERIFIED,
    DOWNLOADING_KODI, WAITING_INSTALL_CONFIRMATION, KODI_READY,
    WAITING_PROTON_STORE, DOWNLOADING_PROTON, PROTON_READY,
    DOWNLOADING_BOOTSTRAP, BOOTSTRAP_READY, WAITING_KODI_BOOTSTRAP,
    REQUESTING_REAL_DEBRID_AUTH, WAITING_REAL_DEBRID_AUTH, ACCOUNT_LINKED,
    COMPLETE, ERROR
}

data class SetupUiState(
    val step: SetupStep = SetupStep.WELCOME,
    val phase: SetupPhase = SetupPhase.READY,
    val progress: Int = 0,
    val busy: Boolean = false,
    val message: String = "Ready",
    val error: String? = null,
    val manifest: SetupManifest? = null,
    val debridCode: String? = null,
    val debridUrl: String? = null,
    val debridExpiry: String? = null,
)

class SetupViewModel(application: Application) : AndroidViewModel(application) {
    private val mutable = MutableStateFlow(SetupUiState())
    val state = mutable.asStateFlow()
    private val json = Json { ignoreUnknownKeys = false }
    private val installer = PackageInstallManager(application)
    private val control = ControlClient(BuildConfig.CONTROL_API_URL, DeviceIdentity())
    private val devicePrefs = application.getSharedPreferences("device_pairing", Context.MODE_PRIVATE)
    private val installPrefs = application.getSharedPreferences("install_status", Context.MODE_PRIVATE)
    private val workflowPrefs = application.getSharedPreferences("setup_workflow", Context.MODE_PRIVATE)
    private val tokenVault = TokenVault(application)
    private val realDebrid = RealDebridClient(tokenVault)
    private val telemetry = DeviceTelemetry(application)
    private var installMonitor: Job? = null

    init {
        val restored = runCatching { SetupStep.valueOf(workflowPrefs.getString("step", SetupStep.WELCOME.name)!!) }.getOrDefault(SetupStep.WELCOME)
        mutable.value = mutable.value.copy(step = restored)
        viewModelScope.launch(Dispatchers.IO) {
            runCatching { realDebrid.user()?.expiration }.getOrNull()?.let { expiry ->
                mutable.value = mutable.value.copy(debridExpiry = expiry)
                reportStatus()
            }
            resumePendingInstall()
            if (devicePrefs.contains("device_id")) loadConfiguration()
            while (isActive) { pollCommands(); reportStatus(); delay(30_000) }
        }
    }

    fun pair(code: String) = viewModelScope.launch(Dispatchers.IO) {
        update(busy = true, error = null, message = "Pairing this TV...", phase = SetupPhase.PAIRING, progress = 5)
        runCatching { require(code.matches(Regex("^[0-9]{8}$"))) { "Enter the 8-digit code from the Windows portal" }; control.pair(code) }
            .onSuccess { result ->
                devicePrefs.edit().putString("device_id", result.deviceId).remove("device_token").apply()
                tokenVault.put("control_token", result.token)
                loadConfiguration()
            }
            .onFailure { update(busy = false, error = it.message ?: "Pairing failed", message = "This TV was not paired") }
    }

    fun continueOffline() = loadConfiguration()

    fun loadConfiguration() = viewModelScope.launch(Dispatchers.IO) {
        update(busy = true, error = null, message = "Verifying signed configuration...", phase = SetupPhase.VERIFYING_CONFIGURATION, progress = 10)
        runCatching {
            require(BuildConfig.MANIFEST_PUBLIC_KEY.isNotBlank()) { "Release public key is not configured" }
            val cache = File(getApplication<Application>().filesDir, "last-verified-manifest.json")
            val downloaded = runCatching { Http.getText(BuildConfig.MANIFEST_URL) }
            val remote = downloaded.getOrNull()?.let { raw -> runCatching { ManifestSecurity.verify(raw, BuildConfig.MANIFEST_PUBLIC_KEY, BuildConfig.VERSION_CODE) } }
            val remoteFailure = remote?.exceptionOrNull()
            if (remoteFailure is ManifestRevokedException) {
                cache.delete()
                throw remoteFailure
            }
            val cached = cache.takeIf { it.isFile }?.let {
                runCatching { ManifestSecurity.verify(it.readText(), BuildConfig.MANIFEST_PUBLIC_KEY, BuildConfig.VERSION_CODE) }.getOrNull()
            }
            val verified = remote?.getOrNull()
            val selected = when {
                verified == null -> cached ?: throw (remoteFailure ?: downloaded.exceptionOrNull() ?: SecurityException("No verified configuration is available"))
                cached != null && compareVersions(verified["configVersion"]!!.jsonPrimitive.content, cached["configVersion"]!!.jsonPrimitive.content) < 0 -> cached
                else -> verified
            }
            if (selected === verified && downloaded.isSuccess) {
                val pending = File(cache.parentFile, cache.name + ".new")
                pending.writeText(downloaded.getOrThrow())
                require(pending.renameTo(cache) || runCatching { pending.copyTo(cache, overwrite = true); pending.delete(); true }.getOrDefault(false)) { "Verified configuration could not be cached" }
            }
            json.decodeFromJsonElement(SetupManifest.serializer(), selected)
        }.onSuccess { manifest ->
            val restored = state.value.step.takeUnless { it == SetupStep.WELCOME } ?: SetupStep.CONFIGURATION
            transition(restored, "Configuration ${manifest.configVersion} verified", manifest = manifest)
            if (workflowPrefs.getBoolean("automatic", false)) advanceAutomatedWorkflow()
        }
            .onFailure { update(busy = false, error = it.message ?: "Configuration failed", message = "Using no unverified configuration") }
    }

    fun startAutomatedSetup() {
        workflowPrefs.edit().putBoolean("automatic", true).apply()
        val startingStep = if (state.value.step == SetupStep.COMPLETE) SetupStep.CONFIGURATION else state.value.step
        transition(startingStep, "Remote setup started")
        if (state.value.manifest == null) loadConfiguration() else advanceAutomatedWorkflow()
    }

    fun installKodi() {
        val packageName = state.value.manifest?.kodi?.packageName
        if (packageName != null && isInstalled(packageName)) {
            transition(SetupStep.KODI, "Kodi is already installed")
            if (workflowPrefs.getBoolean("automatic", false)) advanceAutomatedWorkflow()
            return
        }
        installArtifact(state.value.manifest?.kodi?.architectures?.get(preferredAbi()), packageName, SetupStep.KODI)
    }

    fun installProton() {
        val app = state.value.manifest?.applications?.firstOrNull { it.id == "proton-vpn" } ?: return
        if (isInstalled(app.packageName)) {
            transition(SetupStep.PROTON, "Proton VPN is already installed")
            if (workflowPrefs.getBoolean("automatic", false)) advanceAutomatedWorkflow()
            return
        }
        val artifact = app.artifacts.firstOrNull { it.abi == preferredAbi() } ?: app.artifacts.firstOrNull { it.abi == null }
        if (artifact != null) {
            installArtifact(artifact, app.packageName, SetupStep.PROTON)
            return
        }
        val store = if (isAmazonDevice()) "amazon" else "google-play"
        val uri = app.storeUris[store] ?: app.storeUris.values.firstOrNull()
        val opened = uri != null && runCatching {
            getApplication<Application>().startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(uri)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        }.isSuccess
        if (opened) {
            workflowPrefs.edit().putBoolean("proton_store_opened", true).apply()
            transition(SetupStep.KODI, "Install Proton VPN from the official store, then return to Starlane Meridian")
            update(phase = SetupPhase.WAITING_PROTON_STORE, progress = 55)
        } else {
            update(error = "PROTON_INSTALL_UNAVAILABLE", message = "No compatible official Proton VPN installation route is configured")
        }
    }

    fun openProton() = installProton()

    fun continueToBootstrap() { transition(SetupStep.BOOTSTRAP, "Install the Kodi Setup Bootstrap ZIP from Downloads") }
    fun prepareBootstrap() = viewModelScope.launch(Dispatchers.IO) {
        if (Build.VERSION.SDK_INT < 29 && ContextCompat.checkSelfPermission(getApplication(), Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) {
            update(busy = false, error = "STORAGE_PERMISSION_REQUIRED", message = "Select Prepare Kodi bootstrap and allow storage access")
            return@launch
        }
        val bootstrap = state.value.manifest?.bootstrap ?: return@launch
        update(busy = true, error = null, message = "Downloading and verifying the Kodi bootstrap...", phase = SetupPhase.DOWNLOADING_BOOTSTRAP, progress = 72)
        runCatching {
            val file = File(getApplication<Application>().cacheDir, "packages/repository.kodisetup.zip")
            Http.download(bootstrap.url, file, 25L * 1024 * 1024)
            require(ManifestSecurity.sha256(file) == bootstrap.sha256) { "Bootstrap hash mismatch" }
            BootstrapExporter(getApplication()).export(file, "repository.kodisetup.zip")
        }.onSuccess { location ->
            workflowPrefs.edit().putBoolean("bootstrap_ready", true).apply()
            transition(SetupStep.BOOTSTRAP, "Bootstrap saved to Downloads. In Kodi, enable Unknown Sources and install repository.kodisetup.zip. Location: $location")
        }
            .onFailure { update(busy = false, error = it.message ?: "Bootstrap export failed", message = "Bootstrap was not saved") }
    }
    fun storagePermissionDenied() = update(busy = false, error = "STORAGE_PERMISSION_DENIED", message = "Storage access is required to save the Kodi bootstrap ZIP")
    fun continueToAccounts() { transition(SetupStep.ACCOUNT_LINK, "Link Real-Debrid with its official device authorization flow, or finish without linking") }
    fun markComplete() { workflowPrefs.edit().putBoolean("automatic", false).apply(); transition(SetupStep.COMPLETE, "Core setup complete") }
    fun beginRealDebrid() = viewModelScope.launch(Dispatchers.IO) {
        val openSourceClient = "X245A4XAIBGVM"
        update(busy = true, error = null, message = "Requesting a Real-Debrid device code...", phase = SetupPhase.REQUESTING_REAL_DEBRID_AUTH, progress = 88)
        runCatching {
            val code = realDebrid.begin(openSourceClient)
            transition(SetupStep.ACCOUNT_LINK, "Open the URL and enter the code. This app never receives your password or payment details.", debridCode = code.userCode, debridUrl = code.verificationUrl)
            update(busy = true, phase = SetupPhase.WAITING_REAL_DEBRID_AUTH, progress = 92)
            val deadline = System.currentTimeMillis() + code.expiresIn * 1000L
            var credentials: RealDebridClient.Credentials? = null
            while (credentials == null && System.currentTimeMillis() < deadline) { delay(code.interval.coerceAtLeast(5) * 1000L); credentials = realDebrid.credentials(openSourceClient, code.deviceCode) }
            requireNotNull(credentials) { "Real-Debrid authorization expired" }
            require(realDebrid.poll(credentials.clientId, credentials.clientSecret, code.deviceCode)) { "Real-Debrid token request failed" }
            val user = requireNotNull(realDebrid.user()) { "Real-Debrid account status was unavailable" }
            user.expiration
        }.onSuccess { expiry -> transition(SetupStep.ACCOUNT_LINK, if (expiry == null) "Real-Debrid linked; no premium expiry was reported" else "Real-Debrid premium active until $expiry", debridCode = null, debridUrl = null, debridExpiry = expiry) }
            .onFailure { update(busy = false, error = it.message ?: "Real-Debrid authorization failed", message = "Authorization was not completed") }
    }
    fun grantInstallPermission() = installer.openUnknownSourcesSettings()

    fun resumeWorkflow() {
        if (state.value.busy) return
        if (resumePendingInstall()) return
        val proton = state.value.manifest?.applications?.firstOrNull { it.id == "proton-vpn" }
        if (state.value.step == SetupStep.KODI && proton != null && isInstalled(proton.packageName)) {
            workflowPrefs.edit().remove("proton_store_opened").apply()
            transition(SetupStep.PROTON, "Proton VPN installed successfully")
        }
        if (workflowPrefs.getBoolean("automatic", false)) advanceAutomatedWorkflow()
    }

    fun openKodi() {
        val packageName = state.value.manifest?.kodi?.packageName ?: "org.xbmc.kodi"
        val intent = getApplication<Application>().packageManager.getLaunchIntentForPackage(packageName)?.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        if (intent == null) update(error = "KODI_NOT_INSTALLED", message = "Kodi is not installed")
        else runCatching { getApplication<Application>().startActivity(intent) }
            .onSuccess { update(error = null, message = "Kodi opened for bootstrap confirmation", phase = SetupPhase.WAITING_KODI_BOOTSTRAP, progress = 84) }
            .onFailure { update(error = "KODI_LAUNCH_FAILED", message = it.message ?: "Kodi could not be opened") }
    }

    fun retryCurrentStep() {
        when (state.value.step) {
            SetupStep.WELCOME -> update(error = null, message = "Enter a new pairing code")
            SetupStep.CONFIGURATION -> loadConfiguration()
            SetupStep.KODI -> if (workflowPrefs.getBoolean("proton_store_opened", false)) update(message = "Waiting for Proton VPN installation; return here when the store finishes") else installProton()
            SetupStep.PROTON -> prepareBootstrap()
            SetupStep.BOOTSTRAP -> openKodi()
            SetupStep.ACCOUNT_LINK -> beginRealDebrid()
            SetupStep.COMPLETE -> update(error = null, message = "Setup is already complete")
        }
    }

    private fun installArtifact(artifact: Artifact?, packageName: String?, target: SetupStep) = viewModelScope.launch(Dispatchers.IO) {
        if (artifact == null || packageName == null) { update(error = "No compatible package configured", message = "Installation cannot continue"); return@launch }
        if (workflowPrefs.getString("pending_install_package", null) == packageName) {
            update(busy = false, error = null, message = "Waiting for the Android package installer to finish")
            monitorInstall(packageName, target)
            return@launch
        }
        val downloadPhase = if (target == SetupStep.KODI) SetupPhase.DOWNLOADING_KODI else SetupPhase.DOWNLOADING_PROTON
        val downloadProgress = if (target == SetupStep.KODI) 28 else 50
        update(busy = true, error = null, message = "Downloading verified package...", phase = downloadPhase, progress = downloadProgress)
        runCatching {
            val file = File(getApplication<Application>().cacheDir, "packages/${packageName}.apk")
            Http.download(artifact.url, file)
            require(ManifestSecurity.sha256(file) == artifact.sha256) { "Package hash mismatch" }
            val archive = requireNotNull(getApplication<Application>().packageManager.getPackageArchiveInfo(file.absolutePath, 0)) { "Downloaded file is not an APK" }
            require(archive.packageName == packageName) { "Package identity mismatch" }
            require(ManifestSecurity.archiveSignerSha256(getApplication(), file) == artifact.signerSha256) { "Package signer mismatch" }
            installPrefs.edit().remove("$packageName.status").remove("$packageName.message").apply()
            workflowPrefs.edit().putString("pending_install_package", packageName).putString("pending_install_target", target.name).apply()
            installer.install(file, packageName)
        }.onSuccess {
            mutable.value = mutable.value.copy(busy = false, phase = SetupPhase.WAITING_INSTALL_CONFIRMATION, progress = downloadProgress + 8, message = "Confirm installation in the Android system dialog")
            reportStatus()
            monitorInstall(packageName, target)
        }
            .onFailure { clearPendingInstall(); update(busy = false, error = it.message ?: "Install failed", message = "Package was not installed") }
    }

    private fun monitorInstall(packageName: String, target: SetupStep) {
        if (installMonitor?.isActive == true) return
        installMonitor = viewModelScope.launch(Dispatchers.IO) {
        val deadline = System.currentTimeMillis() + 15 * 60_000L
        while (System.currentTimeMillis() < deadline) {
            delay(1_500)
            when (val status = installPrefs.getInt("$packageName.status", Int.MIN_VALUE)) {
                Int.MIN_VALUE, PackageInstaller.STATUS_PENDING_USER_ACTION -> continue
                PackageInstaller.STATUS_SUCCESS -> {
                    clearPendingInstall()
                    transition(target, "$packageName installed successfully")
                    if (workflowPrefs.getBoolean("automatic", false)) advanceAutomatedWorkflow()
                    return@launch
                }
                else -> {
                    clearPendingInstall()
                    val detail = installPrefs.getString("$packageName.message", null)?.take(160)
                    update(busy = false, error = "INSTALL_STATUS_$status", message = detail ?: "Android rejected the package installation")
                    return@launch
                }
            }
        }
        clearPendingInstall()
        update(busy = false, error = "INSTALL_INTERRUPTED", message = "Installation did not finish; retry when the system installer is available")
        }
    }

    private fun advanceAutomatedWorkflow() {
        if (state.value.busy) return
        when (state.value.step) {
            SetupStep.WELCOME -> loadConfiguration()
            SetupStep.CONFIGURATION -> if (installer.canRequestInstalls()) installKodi() else update(message = "Select Allow APK installs, approve Starlane Meridian, then return here")
            SetupStep.KODI -> installProton()
            SetupStep.PROTON -> if (Build.VERSION.SDK_INT < 29 && ContextCompat.checkSelfPermission(getApplication(), Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) update(message = "Select Prepare Kodi bootstrap and allow storage access") else prepareBootstrap()
            SetupStep.BOOTSTRAP -> update(message = "Open Kodi and confirm the one-time bootstrap ZIP installation")
            SetupStep.ACCOUNT_LINK -> update(message = "Choose whether to link Real-Debrid or finish setup")
            SetupStep.COMPLETE -> workflowPrefs.edit().putBoolean("automatic", false).apply()
        }
    }

    private fun transition(step: SetupStep, message: String, manifest: SetupManifest? = state.value.manifest, debridCode: String? = state.value.debridCode, debridUrl: String? = state.value.debridUrl, debridExpiry: String? = state.value.debridExpiry) {
        val (phase, progress) = when (step) {
            SetupStep.WELCOME -> SetupPhase.READY to 0
            SetupStep.CONFIGURATION -> SetupPhase.CONFIGURATION_VERIFIED to 15
            SetupStep.KODI -> SetupPhase.KODI_READY to 45
            SetupStep.PROTON -> SetupPhase.PROTON_READY to 65
            SetupStep.BOOTSTRAP -> SetupPhase.BOOTSTRAP_READY to 80
            SetupStep.ACCOUNT_LINK -> SetupPhase.ACCOUNT_LINKED to 94
            SetupStep.COMPLETE -> SetupPhase.COMPLETE to 100
        }
        mutable.value = state.value.copy(step = step, phase = phase, progress = progress, busy = false, error = null, message = message, manifest = manifest, debridCode = debridCode, debridUrl = debridUrl, debridExpiry = debridExpiry)
        workflowPrefs.edit().putString("step", step.name).apply()
        reportStatus()
    }

    private fun resumePendingInstall(): Boolean {
        val packageName = workflowPrefs.getString("pending_install_package", null) ?: return false
        val target = workflowPrefs.getString("pending_install_target", null)?.let { runCatching { SetupStep.valueOf(it) }.getOrNull() } ?: return false
        when (val status = installPrefs.getInt("$packageName.status", Int.MIN_VALUE)) {
            PackageInstaller.STATUS_SUCCESS -> {
                clearPendingInstall()
                transition(target, "$packageName installed successfully")
                if (workflowPrefs.getBoolean("automatic", false)) advanceAutomatedWorkflow()
            }
            Int.MIN_VALUE, PackageInstaller.STATUS_PENDING_USER_ACTION -> {
                update(busy = false, error = null, message = "Waiting for the Android package installer to finish")
                monitorInstall(packageName, target)
            }
            else -> {
                clearPendingInstall()
                update(busy = false, error = "INSTALL_STATUS_$status", message = installPrefs.getString("$packageName.message", null) ?: "Android rejected the package installation")
            }
        }
        return true
    }

    private fun clearPendingInstall() {
        workflowPrefs.edit().remove("pending_install_package").remove("pending_install_target").apply()
    }

    private fun update(
        busy: Boolean = mutable.value.busy,
        error: String? = mutable.value.error,
        message: String = mutable.value.message,
        phase: SetupPhase = mutable.value.phase,
        progress: Int = mutable.value.progress,
    ) { mutable.value = mutable.value.copy(busy = busy, error = error, message = message, phase = phase, progress = progress); reportStatus() }
    private fun reportStatus() {
        val id = devicePrefs.getString("device_id", null) ?: return
        val token = tokenVault.get("control_token") ?: return
        val snapshot = mutable.value
        val status = telemetry.status(
            snapshot,
            installPermission = installer.canRequestInstalls(),
            bootstrapReady = workflowPrefs.getBoolean("bootstrap_ready", false),
            automaticSetup = workflowPrefs.getBoolean("automatic", false),
        )
        viewModelScope.launch(Dispatchers.IO) { runCatching { control.report(id, token, status) } }
    }
    private fun pollCommands() {
        val id = devicePrefs.getString("device_id", null) ?: return
        val token = tokenVault.get("control_token") ?: return
        runCatching { control.commands(id, token).commands }.getOrDefault(emptyList()).forEach { command ->
            when (command.kind) {
                "START_SETUP" -> startAutomatedSetup()
                "INSTALL_KODI" -> installKodi()
                "INSTALL_PROTON" -> installProton()
                "PREPARE_BOOTSTRAP" -> prepareBootstrap()
                "OPEN_KODI" -> openKodi()
                "BEGIN_REAL_DEBRID_AUTH" -> beginRealDebrid()
                "SYNC_CONFIG" -> loadConfiguration()
                "RETRY_CURRENT_STEP", "RETRY_STEP" -> retryCurrentStep()
                "OPEN_AUTHORIZATION" -> transition(SetupStep.ACCOUNT_LINK, "Complete authorization on the official provider screen")
                "REQUEST_DIAGNOSTICS" -> update(message = "Diagnostics were requested. Nothing will be sent without your confirmation.")
            }
        }
    }
    private fun preferredAbi() = if (Build.SUPPORTED_ABIS.any { it == "arm64-v8a" }) "arm64-v8a" else "armeabi-v7a"
    private fun isAmazonDevice() = Build.MANUFACTURER.equals("Amazon", ignoreCase = true)
    private fun isInstalled(packageName: String) = runCatching { getApplication<Application>().packageManager.getPackageInfo(packageName, 0); true }.getOrDefault(false)
    private fun compareVersions(left: String, right: String): Int {
        val a = left.split('.').map { it.toIntOrNull() ?: 0 }; val b = right.split('.').map { it.toIntOrNull() ?: 0 }
        for (index in 0 until maxOf(a.size, b.size)) {
            val difference = (a.getOrElse(index) { 0 }).compareTo(b.getOrElse(index) { 0 })
            if (difference != 0) return difference
        }
        return 0
    }
}

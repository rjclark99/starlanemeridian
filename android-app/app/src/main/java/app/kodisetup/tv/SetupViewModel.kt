package app.kodisetup.tv

import android.app.Application
import android.app.ActivityManager
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
import app.kodisetup.tv.install.BootstrapAppliedVersionReader
import app.kodisetup.tv.install.FixedBootstrapTransaction
import app.kodisetup.tv.install.FixedBootstrapEligibility
import app.kodisetup.tv.install.KodiRealDebridCredentials
import app.kodisetup.tv.install.KodiRealDebridHandoff
import app.kodisetup.tv.install.KodiLoopbackBootstrapActivator
import app.kodisetup.tv.install.BootstrapActivationOutcome
import app.kodisetup.tv.automation.AutomationConsentCoordinator
import app.kodisetup.tv.automation.AutomationSecurityScope
import app.kodisetup.tv.automation.AutomationScope
import app.kodisetup.tv.automation.ConsentInvalidationReason
import app.kodisetup.tv.automation.ConsentStatus
import app.kodisetup.tv.automation.SharedPreferencesConsentStorage
import app.kodisetup.tv.model.*
import app.kodisetup.tv.net.Http
import app.kodisetup.tv.net.ControlClient
import app.kodisetup.tv.net.RealDebridAuthorization
import app.kodisetup.tv.net.RealDebridClient
import app.kodisetup.tv.security.DeviceIdentity
import app.kodisetup.tv.security.TokenVault
import app.kodisetup.tv.security.ManifestReleaseCandidate
import app.kodisetup.tv.security.ManifestSecurity
import app.kodisetup.tv.security.ManifestRevokedException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.Job
import kotlinx.coroutines.ensureActive
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonPrimitive
import java.io.File
import android.os.Environment
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone

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
    val debridAuthExpiresAt: String? = null,
    val debridAuthCommandId: String? = null,
    val consentGeneration: String? = null,
    val consentScope: AutomationScope? = null,
    val consentRequestId: String? = null,
    val automationRunning: Boolean = false,
    val bootstrapActivationPending: Boolean = false,
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
    private val consent = AutomationConsentCoordinator(
        SharedPreferencesConsentStorage(application.getSharedPreferences("automation_consent", Context.MODE_PRIVATE)),
        BuildConfig.VERSION_CODE,
    )
    private val tokenVault = TokenVault(application)
    private val realDebrid = RealDebridClient(tokenVault)
    private val telemetry = DeviceTelemetry(application)
    private var installMonitor: Job? = null
    private var bootstrapPreparation: Job? = null

    init {
        val restored = runCatching { SetupStep.valueOf(workflowPrefs.getString("step", SetupStep.WELCOME.name)!!) }.getOrDefault(SetupStep.WELCOME)
        mutable.value = mutable.value.copy(step = restored)
        viewModelScope.launch(Dispatchers.IO) {
            runCatching { realDebrid.user() }.getOrNull()?.let { user ->
                runCatching { stageRealDebridForKodi(user) }
                mutable.value = mutable.value.copy(debridExpiry = user.expiration)
                reportStatus()
            }
            resumePendingInstall()
            if (devicePrefs.contains("device_id") || restored != SetupStep.WELCOME) {
                loadConfiguration()
            }
            while (isActive) { pollCommands(); reportStatus(); delay(30_000) }
        }
    }

    fun pair(code: String) = viewModelScope.launch(Dispatchers.IO) {
        update(busy = true, error = null, message = "Pairing this TV...", phase = SetupPhase.PAIRING, progress = 5)
        runCatching { require(code.matches(Regex("^[0-9]{8}$"))) { "Enter the 8-digit owner-provided pairing code" }; control.pair(code) }
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
            val downloadedLatest = runCatching { Http.getText(BuildConfig.MANIFEST_URL) }
            val remoteLatest = downloadedLatest.getOrNull()?.let { raw ->
                runCatching { ManifestSecurity.verify(raw, BuildConfig.MANIFEST_PUBLIC_KEY, BuildConfig.VERSION_CODE) }
            }
            val latestFailure = remoteLatest?.exceptionOrNull()
            if (latestFailure is ManifestRevokedException) {
                cache.delete()
                throw latestFailure
            }
            val candidateUrl = remoteLatest?.getOrNull()
                ?.takeIf { ManifestReleaseCandidate.shouldCheck(it, BuildConfig.VERSION_CODE) }
                ?.let { ManifestReleaseCandidate.url(BuildConfig.MANIFEST_URL, BuildConfig.VERSION_NAME) }
            val downloadedCandidate = candidateUrl?.let { url -> runCatching { Http.getText(url) } }
            val remoteCandidate = downloadedCandidate?.getOrNull()?.let { raw ->
                runCatching { ManifestSecurity.verify(raw, BuildConfig.MANIFEST_PUBLIC_KEY, BuildConfig.VERSION_CODE) }
            }
            val candidateFailure = remoteCandidate?.exceptionOrNull()
            if (candidateFailure is ManifestRevokedException) {
                cache.delete()
                throw candidateFailure
            }
            val cached = cache.takeIf { it.isFile }?.let {
                runCatching { ManifestSecurity.verify(it.readText(), BuildConfig.MANIFEST_PUBLIC_KEY, BuildConfig.VERSION_CODE) }.getOrNull()
            }
            val remote = listOfNotNull(
                remoteLatest?.getOrNull()?.let { it to downloadedLatest.getOrThrow() },
                remoteCandidate?.getOrNull()?.let { it to downloadedCandidate!!.getOrThrow() },
            ).maxWithOrNull { left, right ->
                compareVersions(
                    left.first["configVersion"]!!.jsonPrimitive.content,
                    right.first["configVersion"]!!.jsonPrimitive.content,
                )
            }
            val verified = remote?.first
            val selected = when {
                verified == null -> cached ?: throw (candidateFailure ?: latestFailure ?: downloadedLatest.exceptionOrNull() ?: SecurityException("No verified configuration is available"))
                cached != null && compareVersions(verified["configVersion"]!!.jsonPrimitive.content, cached["configVersion"]!!.jsonPrimitive.content) < 0 -> cached
                else -> verified
            }
            if (selected === verified) {
                val pending = File(cache.parentFile, cache.name + ".new")
                pending.writeText(remote!!.second)
                require(pending.renameTo(cache) || runCatching { pending.copyTo(cache, overwrite = true); pending.delete(); true }.getOrDefault(false)) { "Verified configuration could not be cached" }
            }
            json.decodeFromJsonElement(SetupManifest.serializer(), selected)
        }.onSuccess { manifest ->
            val securityScope = AutomationSecurityScope.digest(manifest)
            recordConsentInvalidation(consent.invalidationReason(securityScope))
            val restoredConsent = consent.current(securityScope)
            val restored = state.value.step.takeUnless { it == SetupStep.WELCOME } ?: SetupStep.CONFIGURATION
            transition(restored, "Configuration ${manifest.configVersion} verified", manifest = manifest)
            mutable.value = mutable.value.copy(
                consentGeneration = restoredConsent?.takeIf { it.status == ConsentStatus.REQUESTED }?.generation,
                consentScope = restoredConsent?.takeIf { it.status == ConsentStatus.REQUESTED }?.scope,
                consentRequestId = restoredConsent?.takeIf { it.status == ConsentStatus.REQUESTED }?.requestId,
                automationRunning = restoredConsent?.status == ConsentStatus.GRANTED && restoredConsent.scope == AutomationScope.STRICT_SETUP,
                bootstrapActivationPending = bootstrapActivationIsPending(manifest.configVersion),
            )
            if (strictAutomationIsActive()) advanceAutomatedWorkflow()
            else if (restoredConsent?.status == ConsentStatus.GRANTED &&
                workflowPrefs.getString("handled_command_id", null) != restoredConsent.requestId
            ) executeApprovedAction(restoredConsent.scope, restoredConsent.generation, restoredConsent.requestId)
        }
            .onFailure { update(busy = false, error = it.message ?: "Configuration failed", message = "Using no unverified configuration") }
    }

    fun startAutomatedSetup() {
        requestLocalConsent(AutomationScope.STRICT_SETUP, "local-strict-setup")
    }

    fun resumeAutomatedBootstrap() {
        mutable.value = mutable.value.copy(bootstrapActivationPending = true)
        requestLocalConsent(AutomationScope.STRICT_SETUP, "resume-fixed-bootstrap")
    }

    fun grantAutomationConsent() {
        val generation = state.value.consentGeneration ?: return
        val requestId = state.value.consentRequestId
        val securityScope = state.value.manifest?.let(AutomationSecurityScope::digest) ?: AutomationSecurityScope.UNVERIFIED
        val granted = consent.grant(generation, securityScope) ?: return
        mutable.value = mutable.value.copy(consentGeneration = null, consentScope = null, consentRequestId = null)
        if (granted.scope == AutomationScope.STRICT_SETUP) {
            workflowPrefs.edit().putBoolean("automatic", true).putString("automation_generation", granted.generation).apply()
            mutable.value = mutable.value.copy(automationRunning = true)
            val startingStep = if (state.value.step == SetupStep.COMPLETE) SetupStep.CONFIGURATION else state.value.step
            transition(startingStep, "Locally approved setup started")
            advanceAutomatedWorkflow()
        } else executeApprovedAction(granted.scope, granted.generation, requestId)
    }

    fun cancelAutomationConsent() {
        consent.invalidate()
        mutable.value = mutable.value.copy(consentGeneration = null, consentScope = null, consentRequestId = null)
        update(message = "Automated setup was not approved")
    }

    fun stopAutomatedSetup() {
        consent.invalidate()
        installMonitor?.cancel()
        workflowPrefs.edit().putBoolean("automatic", false).remove("automation_generation")
            .putString("automation_invalidation_reason", "STOPPED").apply()
        mutable.value = mutable.value.copy(
            busy = false, automationRunning = false, consentGeneration = null, consentScope = null,
            consentRequestId = null, message = "Automated setup stopped; no further automated steps will run",
        )
        reportStatus()
    }

    fun installKodi() {
        val packageName = state.value.manifest?.kodi?.packageName
        if (packageName != null && isInstalled(packageName)) {
            transition(SetupStep.KODI, "Kodi is already installed")
            if (strictAutomationIsActive()) advanceAutomatedWorkflow()
            return
        }
        installArtifact(state.value.manifest?.kodi?.architectures?.get(preferredAbi()), packageName, SetupStep.KODI)
    }

    fun installProton() {
        val app = state.value.manifest?.applications?.firstOrNull { it.id == "proton-vpn" } ?: return
        if (isInstalled(app.packageName)) {
            transition(SetupStep.PROTON, "Proton VPN is already installed")
            if (strictAutomationIsActive()) advanceAutomatedWorkflow()
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
            transition(SetupStep.KODI, "Install Proton VPN from the official store, then return to Starlane Movies")
            update(phase = SetupPhase.WAITING_PROTON_STORE, progress = 55)
        } else {
            update(error = "PROTON_INSTALL_UNAVAILABLE", message = "No compatible official Proton VPN installation route is configured")
        }
    }

    fun openProton() = installProton()

    fun continueToBootstrap() { transition(SetupStep.BOOTSTRAP, "Install the Kodi Setup Bootstrap ZIP from Downloads") }
    fun prepareBootstrap() {
        if (bootstrapPreparation?.isActive == true || state.value.busy) return
        bootstrapPreparation = viewModelScope.launch(Dispatchers.IO) {
        if (Build.VERSION.SDK_INT < 29 && ContextCompat.checkSelfPermission(getApplication(), Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) {
            update(busy = false, error = "STORAGE_PERMISSION_REQUIRED", message = "Select Prepare Kodi bootstrap and allow storage access")
            return@launch
        }
        val bootstrap = state.value.manifest?.bootstrap ?: return@launch
        val configVersion = state.value.manifest?.configVersion ?: return@launch
        val strictGeneration = activeStrictGeneration()
        val fixedAutomatic = FixedBootstrapEligibility.usesAutomaticPath(Build.VERSION.SDK_INT, strictGeneration != null)
        if (!fixedAutomatic && workflowPrefs.getString("bootstrap_prepared_version", null) == configVersion) {
            transition(SetupStep.BOOTSTRAP, "Bootstrap is already verified in Downloads. In Kodi, enable Unknown Sources, install repository.kodisetup.zip, and approve Bootstrap.")
            return@launch
        }
        val expectedScope = state.value.manifest?.let(AutomationSecurityScope::digest) ?: return@launch
        val resumeFixedActivation = fixedAutomatic &&
            workflowPrefs.getBoolean("bootstrap_launch_pending", false) &&
            workflowPrefs.getString("bootstrap_auto_installed_version", null) == configVersion
        update(
            busy = true,
            error = null,
            message = if (resumeFixedActivation) "Resuming verified Kodi bootstrap activation..." else "Downloading and verifying the Kodi bootstrap...",
            phase = SetupPhase.DOWNLOADING_BOOTSTRAP,
            progress = 72,
        )
        runCatching {
            if (resumeFixedActivation) {
                revalidateManifestScope(expectedScope, bootstrap.url, bootstrap.sha256)
                val outcome = activateFixedBootstrap(requireNotNull(strictGeneration), expectedScope)
                return@runCatching activationInstruction(outcome, resumed = true)
            }
            val file = File(getApplication<Application>().cacheDir, "packages/repository.kodisetup.zip")
            Http.download(bootstrap.url, file, 25L * 1024 * 1024)
            require(ManifestSecurity.sha256(file) == bootstrap.sha256) { "Bootstrap hash mismatch" }
            require(strictGeneration == null || strictConsentStillValid(strictGeneration)) { "Automated setup was stopped" }
            if (fixedAutomatic) {
                revalidateManifestScope(expectedScope, bootstrap.url, bootstrap.sha256)
                @Suppress("DEPRECATION") val root = Environment.getExternalStorageDirectory()
                val result = FixedBootstrapTransaction(root).install(file, bootstrap.sha256) {
                    requireFixedBootstrapGate(requireNotNull(strictGeneration), expectedScope)
                }
                workflowPrefs.edit().putBoolean("bootstrap_ready", true).putString("bootstrap_auto_installed_version", configVersion)
                    .putBoolean("bootstrap_launch_pending", true).apply()
                mutable.value = mutable.value.copy(bootstrapActivationPending = true)
                val outcome = activateFixedBootstrap(requireNotNull(strictGeneration), expectedScope)
                "Bootstrap ${result.version} installed atomically. ${activationInstruction(outcome, resumed = false)}"
            } else {
                val location = BootstrapExporter(getApplication()).export(file, "repository.kodisetup.zip")
                workflowPrefs.edit().putBoolean("bootstrap_ready", true).putString("bootstrap_prepared_version", configVersion).apply()
                "In Kodi, enable Unknown Sources, install repository.kodisetup.zip from Downloads, and approve Bootstrap. Location: $location"
            }
        }.onSuccess { instruction ->
            transition(SetupStep.BOOTSTRAP, instruction)
        }
            .onFailure { update(busy = false, error = it.message ?: "Bootstrap preparation failed", message = "Bootstrap preparation did not complete") }
        }
    }

    private fun activateFixedBootstrap(strictGeneration: String, expectedScope: String): BootstrapActivationOutcome {
        requireFixedBootstrapActivationGate(strictGeneration, expectedScope)
        val intent = requireNotNull(getApplication<Application>().packageManager.getLaunchIntentForPackage(FIXED_KODI_PACKAGE)) {
            "Kodi launch activity is unavailable"
        }.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        getApplication<Application>().startActivity(intent)
        val outcome = KodiLoopbackBootstrapActivator().activate {
            bootstrapPreparation?.ensureActive()
            requireFixedBootstrapActivationGate(strictGeneration, expectedScope)
        }
        requireFixedBootstrapActivationGate(strictGeneration, expectedScope)
        if (outcome == BootstrapActivationOutcome.ENABLED_AWAITING_CONSENT || outcome == BootstrapActivationOutcome.ALREADY_ENABLED_AWAITING_CONSENT) {
            getApplication<Application>().startActivity(intent)
            workflowPrefs.edit().putBoolean("bootstrap_launch_pending", false).apply()
            mutable.value = mutable.value.copy(bootstrapActivationPending = false)
        } else {
            consent.invalidate()
            workflowPrefs.edit()
                .putBoolean("automatic", false)
                .remove("automation_generation")
                .putString("automation_invalidation_reason", outcome.name)
                .apply()
            mutable.value = mutable.value.copy(
                automationRunning = false,
                bootstrapActivationPending = true,
            )
        }
        return outcome
    }

    private fun activationInstruction(outcome: BootstrapActivationOutcome, resumed: Boolean): String = when (outcome) {
        BootstrapActivationOutcome.ENABLED_AWAITING_CONSENT -> "Bootstrap is enabled and awaiting its visible Kodi consent"
        BootstrapActivationOutcome.ALREADY_ENABLED_AWAITING_CONSENT -> "Bootstrap was already enabled and is awaiting its visible Kodi consent"
        BootstrapActivationOutcome.API_UNAVAILABLE -> "Kodi activation API is unavailable; keep Kodi open and select Resume automated setup"
        BootstrapActivationOutcome.BOOTSTRAP_MISSING -> "Kodi has not discovered the verified Bootstrap yet; keep Kodi open and select Resume automated setup"
        BootstrapActivationOutcome.BOOTSTRAP_INSTALLED_DISABLED -> "Bootstrap is installed but remains disabled; keep Kodi open and select Resume automated setup"
        BootstrapActivationOutcome.UNKNOWN_SOURCES_DISABLED -> if (resumed) {
            "Kodi still reports Unknown Sources disabled; fully close Kodi, then select Resume automated setup"
        } else {
            "Kodi reports Unknown Sources disabled after the fixed profile update; fully close Kodi, then select Resume automated setup"
        }
    }

    fun storagePermissionDenied() = update(busy = false, error = "STORAGE_PERMISSION_DENIED", message = "Storage access is required to save the Kodi bootstrap ZIP")
    fun checkBootstrapApplied() {
        if (state.value.busy) return
        val expected = state.value.manifest?.configVersion ?: return
        val observed = if (Build.VERSION.SDK_INT < 29) runCatching {
            @Suppress("DEPRECATION") val root = Environment.getExternalStorageDirectory()
            BootstrapAppliedVersionReader(root).read(state.value.manifest?.kodi?.packageName ?: "org.xbmc.kodi")
        }.getOrNull() else null
        val applied = observed == expected
        if (applied) {
            workflowPrefs.edit().putString("bootstrap_applied_version", observed).putBoolean("bootstrap_launch_pending", false).apply()
            consent.invalidate()
            workflowPrefs.edit().putBoolean("automatic", false).remove("automation_generation").apply()
            mutable.value = mutable.value.copy(automationRunning = false, bootstrapActivationPending = false)
            transition(SetupStep.ACCOUNT_LINK, "Bootstrap $observed was observed as applied. Link Real-Debrid or finish.")
        } else {
            update(message = "Waiting for Kodi Bootstrap to report applied configuration $expected. Complete the visible Kodi confirmations, then check again.")
        }
    }
    fun markComplete() {
        val expected = state.value.manifest?.configVersion
        if (expected == null || workflowPrefs.getString("bootstrap_applied_version", null) != expected) {
            update(error = "BOOTSTRAP_NOT_OBSERVED", message = "Setup cannot complete until Bootstrap reports the verified configuration as applied")
            return
        }
        consent.invalidate()
        workflowPrefs.edit().putBoolean("automatic", false).remove("automation_generation").apply()
        mutable.value = mutable.value.copy(automationRunning = false)
        transition(SetupStep.COMPLETE, "Core setup complete from observed Bootstrap state")
    }
    fun beginRealDebrid(commandId: String? = null) = viewModelScope.launch(Dispatchers.IO) {
        val openSourceClient = "X245A4XAIBGVM"
        update(busy = true, error = null, message = "Requesting a Real-Debrid device code...", phase = SetupPhase.REQUESTING_REAL_DEBRID_AUTH, progress = 88)
        runCatching {
            val code = realDebrid.begin(openSourceClient)
            val authorizationUrl = RealDebridAuthorization.deviceUrl(code)
            val authorizationExpiresAt = isoDateAfter(code.expiresIn)
            transition(
                SetupStep.ACCOUNT_LINK,
                "Open the URL and enter the code. This app never receives your password or payment details.",
                debridCode = code.userCode,
                debridUrl = authorizationUrl,
                debridAuthExpiresAt = authorizationExpiresAt,
                debridAuthCommandId = commandId,
            )
            update(busy = true, phase = SetupPhase.WAITING_REAL_DEBRID_AUTH, progress = 92)
            val deadline = System.currentTimeMillis() + code.expiresIn * 1000L
            var credentials: RealDebridClient.Credentials? = null
            while (credentials == null && System.currentTimeMillis() < deadline) { delay(code.interval.coerceAtLeast(5) * 1000L); credentials = realDebrid.credentials(openSourceClient, code.deviceCode) }
            requireNotNull(credentials) { "Real-Debrid authorization expired" }
            require(realDebrid.poll(credentials.clientId, credentials.clientSecret, code.deviceCode)) { "Real-Debrid token request failed" }
            val user = requireNotNull(realDebrid.user()) { "Real-Debrid account status was unavailable" }
            stageRealDebridForKodi(user, credentials.clientId, credentials.clientSecret)
            user.expiration
        }.onSuccess { expiry -> transition(SetupStep.ACCOUNT_LINK, if (expiry == null) "Real-Debrid linked to Starlane Movies; no premium expiry was reported" else "Real-Debrid linked to Starlane Movies; premium active until $expiry", debridCode = null, debridUrl = null, debridExpiry = expiry, debridAuthExpiresAt = null, debridAuthCommandId = null) }
            .onFailure {
                mutable.value = mutable.value.copy(debridCode = null, debridUrl = null, debridAuthExpiresAt = null, debridAuthCommandId = null)
                update(busy = false, error = it.message ?: "Real-Debrid authorization failed", message = "Authorization was not completed")
            }
    }
    fun grantInstallPermission() = installer.openUnknownSourcesSettings()

    private fun stageRealDebridForKodi(
        user: RealDebridClient.User,
        clientId: String = requireNotNull(tokenVault.get("rd_client_id")),
        clientSecret: String = requireNotNull(tokenVault.get("rd_client_secret")),
    ) {
        require(Build.VERSION.SDK_INT < 29) {
            "Android restricts the local Kodi account handoff; authorize Real-Debrid in Starlane Movies: On Demand"
        }
        @Suppress("DEPRECATION")
        val externalRoot = Environment.getExternalStorageDirectory()
        val kodiPackage = state.value.manifest?.kodi?.packageName ?: "org.xbmc.kodi"
        KodiRealDebridHandoff(externalRoot).write(
            kodiPackage,
            KodiRealDebridCredentials(
                accessToken = requireNotNull(tokenVault.get("rd_access")),
                refreshToken = requireNotNull(tokenVault.get("rd_refresh")),
                clientId = clientId,
                clientSecret = clientSecret,
                username = user.username,
            ),
        )
    }

    fun resumeWorkflow() {
        if (state.value.busy) return
        if (resumePendingInstall()) return
        val proton = state.value.manifest?.applications?.firstOrNull { it.id == "proton-vpn" }
        if (state.value.step == SetupStep.KODI && proton != null && isInstalled(proton.packageName)) {
            workflowPrefs.edit().remove("proton_store_opened").apply()
            transition(SetupStep.PROTON, "Proton VPN installed successfully")
        }
        if (strictAutomationIsActive()) advanceAutomatedWorkflow()
    }

    fun openKodi() {
        val packageName = FIXED_KODI_PACKAGE
        val intent = getApplication<Application>().packageManager.getLaunchIntentForPackage(FIXED_KODI_PACKAGE)?.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
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
        val strictGeneration = activeStrictGeneration()
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
            require(strictGeneration == null || strictConsentStillValid(strictGeneration)) { "Automated setup was stopped" }
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
                    if (strictAutomationIsActive()) advanceAutomatedWorkflow()
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
            SetupStep.CONFIGURATION -> if (installer.canRequestInstalls()) installKodi() else update(message = "Select Allow APK installs, approve Starlane Movies, then return here")
            SetupStep.KODI -> installProton()
            SetupStep.PROTON -> if (Build.VERSION.SDK_INT < 29 && ContextCompat.checkSelfPermission(getApplication(), Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) update(message = "Select Prepare Kodi bootstrap and allow storage access") else prepareBootstrap()
            SetupStep.BOOTSTRAP -> if (state.value.bootstrapActivationPending) prepareBootstrap() else update(message = "Open Kodi and confirm the one-time bootstrap ZIP installation")
            SetupStep.ACCOUNT_LINK -> update(message = "Choose whether to link Real-Debrid or finish setup")
            SetupStep.COMPLETE -> workflowPrefs.edit().putBoolean("automatic", false).apply()
        }
    }

    private fun transition(step: SetupStep, message: String, manifest: SetupManifest? = state.value.manifest, debridCode: String? = state.value.debridCode, debridUrl: String? = state.value.debridUrl, debridExpiry: String? = state.value.debridExpiry, debridAuthExpiresAt: String? = state.value.debridAuthExpiresAt, debridAuthCommandId: String? = state.value.debridAuthCommandId) {
        val (phase, progress) = when (step) {
            SetupStep.WELCOME -> SetupPhase.READY to 0
            SetupStep.CONFIGURATION -> SetupPhase.CONFIGURATION_VERIFIED to 15
            SetupStep.KODI -> SetupPhase.KODI_READY to 45
            SetupStep.PROTON -> SetupPhase.PROTON_READY to 65
            SetupStep.BOOTSTRAP -> SetupPhase.BOOTSTRAP_READY to 80
            SetupStep.ACCOUNT_LINK -> SetupPhase.ACCOUNT_LINKED to 94
            SetupStep.COMPLETE -> SetupPhase.COMPLETE to 100
        }
        mutable.value = state.value.copy(step = step, phase = phase, progress = progress, busy = false, error = null, message = message, manifest = manifest, debridCode = debridCode, debridUrl = debridUrl, debridExpiry = debridExpiry, debridAuthExpiresAt = debridAuthExpiresAt, debridAuthCommandId = debridAuthCommandId)
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
                if (strictAutomationIsActive()) advanceAutomatedWorkflow()
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
            if (workflowPrefs.getString("handled_command_id", null) == command.id) return@forEach
            when (command.kind) {
                "START_SETUP" -> requestLocalConsent(AutomationScope.STRICT_SETUP, command.id)
                "INSTALL_KODI" -> requestLocalConsent(AutomationScope.INSTALL_KODI, command.id)
                "INSTALL_PROTON" -> requestLocalConsent(AutomationScope.INSTALL_PROTON, command.id)
                "PREPARE_BOOTSTRAP" -> requestLocalConsent(AutomationScope.PREPARE_BOOTSTRAP, command.id)
                "OPEN_KODI" -> requestLocalConsent(AutomationScope.OPEN_KODI, command.id)
                "BEGIN_REAL_DEBRID_AUTH" -> requestLocalConsent(AutomationScope.BEGIN_REAL_DEBRID_AUTH, command.id)
                "SYNC_CONFIG" -> requestLocalConsent(AutomationScope.SYNC_CONFIG, command.id)
                "RETRY_CURRENT_STEP", "RETRY_STEP" -> requestLocalConsent(AutomationScope.RETRY_CURRENT_STEP, command.id)
                "OPEN_AUTHORIZATION" -> transition(SetupStep.ACCOUNT_LINK, "Complete authorization on the official provider screen")
                "REQUEST_DIAGNOSTICS" -> update(message = "Diagnostics were requested. Nothing will be sent without your confirmation.")
            }
        }
    }

    private fun requestLocalConsent(scope: AutomationScope, requestId: String) {
        val securityScope = state.value.manifest?.let(AutomationSecurityScope::digest) ?: AutomationSecurityScope.UNVERIFIED
        val requested = consent.request(scope, requestId, securityScope)
        mutable.value = mutable.value.copy(
            busy = false,
            consentGeneration = requested.generation,
            consentScope = requested.scope,
            consentRequestId = requested.requestId,
            message = "Local approval is required before automated setup can act",
        )
        reportStatus()
    }

    private fun executeApprovedAction(scope: AutomationScope, generation: String, requestId: String?) {
        val securityScope = state.value.manifest?.let(AutomationSecurityScope::digest) ?: AutomationSecurityScope.UNVERIFIED
        if (!consent.isGranted(scope, generation, securityScope)) return
        requestId?.let { workflowPrefs.edit().putString("handled_command_id", it).apply() }
        when (scope) {
            AutomationScope.STRICT_SETUP -> Unit
            AutomationScope.INSTALL_KODI -> installKodi()
            AutomationScope.INSTALL_PROTON -> installProton()
            AutomationScope.PREPARE_BOOTSTRAP -> prepareBootstrap()
            AutomationScope.OPEN_KODI -> openKodi()
            AutomationScope.BEGIN_REAL_DEBRID_AUTH -> beginRealDebrid()
            AutomationScope.SYNC_CONFIG -> loadConfiguration()
            AutomationScope.RETRY_CURRENT_STEP -> retryCurrentStep()
        }
    }

    private fun activeStrictGeneration(): String? =
        workflowPrefs.getString("automation_generation", null)?.takeIf { strictConsentStillValid(it) }

    private fun strictConsentStillValid(generation: String): Boolean {
        val securityScope = state.value.manifest?.let(AutomationSecurityScope::digest) ?: return false
        return consent.isGranted(AutomationScope.STRICT_SETUP, generation, securityScope)
    }

    private fun strictAutomationIsActive(): Boolean {
        if (!workflowPrefs.getBoolean("automatic", false)) return false
        val expectedScope = state.value.manifest?.let(AutomationSecurityScope::digest) ?: return false
        val generation = workflowPrefs.getString("automation_generation", null) ?: return false
        val invalidationReason = consent.invalidationReason(expectedScope)
        val active = strictConsentStillValid(generation)
        if (!active) {
            workflowPrefs.edit().putBoolean("automatic", false).remove("automation_generation")
                .putString("automation_invalidation_reason", invalidationReason?.name ?: "REVOKED_OR_MISSING").apply()
            mutable.value = mutable.value.copy(automationRunning = false)
        }
        return active
    }
    private fun recordConsentInvalidation(reason: ConsentInvalidationReason?) {
        if (reason != null && workflowPrefs.getBoolean("automatic", false)) {
            workflowPrefs.edit().putBoolean("automatic", false).remove("automation_generation")
                .putString("automation_invalidation_reason", reason.name).apply()
        }
    }
    private fun bootstrapActivationIsPending(configVersion: String): Boolean =
        workflowPrefs.getBoolean("bootstrap_launch_pending", false) &&
            workflowPrefs.getString("bootstrap_auto_installed_version", null) == configVersion
    private fun requireFixedBootstrapGate(generation: String, expectedScope: String) {
        val permission = ContextCompat.checkSelfPermission(getApplication(), Manifest.permission.WRITE_EXTERNAL_STORAGE) == PackageManager.PERMISSION_GRANTED
        val installed = state.value.manifest?.kodi?.packageName == FIXED_KODI_PACKAGE && isInstalled(FIXED_KODI_PACKAGE)
        require(state.value.manifest?.let(AutomationSecurityScope::digest) == expectedScope) { "Verified manifest scope changed" }
        require(consent.isGranted(AutomationScope.STRICT_SETUP, generation, expectedScope)) { "Local setup consent is no longer current" }
        val processes = (getApplication<Application>().getSystemService(ActivityManager::class.java)).runningAppProcesses
        val active = processes?.any { process -> process.processName == FIXED_KODI_PACKAGE || process.pkgList?.contains(FIXED_KODI_PACKAGE) == true } == true
        FixedBootstrapEligibility.requireEligible(Build.VERSION.SDK_INT, true, permission, installed, processes != null, active)
    }

    private fun requireFixedBootstrapActivationGate(generation: String, expectedScope: String) {
        require(Build.VERSION.SDK_INT in 25..28) { "Fixed Bootstrap activation is unavailable" }
        require(state.value.manifest?.kodi?.packageName == FIXED_KODI_PACKAGE && isInstalled(FIXED_KODI_PACKAGE)) { "Official Kodi is unavailable" }
        require(state.value.manifest?.let(AutomationSecurityScope::digest) == expectedScope) { "Verified manifest scope changed" }
        require(consent.isGranted(AutomationScope.STRICT_SETUP, generation, expectedScope)) { "Local setup consent is no longer current" }
    }

    private fun revalidateManifestScope(expectedScope: String, expectedUrl: String, expectedHash: String) {
        val cache = File(getApplication<Application>().filesDir, "last-verified-manifest.json")
        require(cache.isFile) { "Verified manifest cache is unavailable" }
        val verified = ManifestSecurity.verify(cache.readText(), BuildConfig.MANIFEST_PUBLIC_KEY, BuildConfig.VERSION_CODE)
        val manifest = json.decodeFromJsonElement(SetupManifest.serializer(), verified)
        require(AutomationSecurityScope.digest(manifest) == expectedScope) { "Verified manifest security scope changed" }
        require(manifest.bootstrap.url == expectedUrl && manifest.bootstrap.sha256 == expectedHash) { "Bootstrap selection changed" }
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

    private fun isoDateAfter(seconds: Int): String =
        SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.US).apply {
            timeZone = TimeZone.getTimeZone("UTC")
        }.format(Date(System.currentTimeMillis() + seconds * 1000L))

    private companion object { const val FIXED_KODI_PACKAGE = "org.xbmc.kodi" }
}

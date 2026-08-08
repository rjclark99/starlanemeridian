package app.kodisetup.tv.automation

import android.content.SharedPreferences
import java.util.UUID

enum class AutomationScope {
    STRICT_SETUP,
    INSTALL_KODI,
    INSTALL_PROTON,
    PREPARE_BOOTSTRAP,
    OPEN_KODI,
    BEGIN_REAL_DEBRID_AUTH,
    SYNC_CONFIG,
    RETRY_CURRENT_STEP,
}

enum class ConsentStatus { REQUESTED, GRANTED }

data class AutomationConsent(
    val schemaVersion: Int,
    val generation: String,
    val requestId: String,
    val scope: AutomationScope,
    val appVersion: Int,
    val securityScopeDigest: String,
    val status: ConsentStatus,
    val grantedAtMillis: Long,
    val expiresAtMillis: Long,
    val lastObservedMillis: Long,
)

interface ConsentStorage {
    fun load(): AutomationConsent?
    fun save(consent: AutomationConsent?)
}

class SharedPreferencesConsentStorage(private val prefs: SharedPreferences) : ConsentStorage {
    override fun load(): AutomationConsent? = runCatching {
        if (!prefs.contains("schema")) return null
        AutomationConsent(
            schemaVersion = prefs.getInt("schema", 0),
            generation = requireNotNull(prefs.getString("generation", null)),
            requestId = requireNotNull(prefs.getString("request_id", null)),
            scope = AutomationScope.valueOf(requireNotNull(prefs.getString("scope", null))),
            appVersion = prefs.getInt("app_version", -1),
            securityScopeDigest = requireNotNull(prefs.getString("security_scope_digest", null)),
            status = ConsentStatus.valueOf(requireNotNull(prefs.getString("status", null))),
            grantedAtMillis = prefs.getLong("granted_at", 0),
            expiresAtMillis = prefs.getLong("expires_at", 0),
            lastObservedMillis = prefs.getLong("last_observed", 0),
        )
    }.getOrNull()

    override fun save(consent: AutomationConsent?) {
        val edit = prefs.edit().clear()
        if (consent != null) edit
            .putInt("schema", consent.schemaVersion)
            .putString("generation", consent.generation)
            .putString("request_id", consent.requestId)
            .putString("scope", consent.scope.name)
            .putInt("app_version", consent.appVersion)
            .putString("security_scope_digest", consent.securityScopeDigest)
            .putString("status", consent.status.name)
            .putLong("granted_at", consent.grantedAtMillis)
            .putLong("expires_at", consent.expiresAtMillis)
            .putLong("last_observed", consent.lastObservedMillis)
        edit.commit()
    }
}

class AutomationConsentCoordinator(
    private val storage: ConsentStorage,
    private val appVersion: Int,
    private val now: () -> Long = System::currentTimeMillis,
    private val newGeneration: () -> String = { UUID.randomUUID().toString() },
) {
    companion object {
        const val SCHEMA_VERSION = 1
        const val MAX_LIFETIME_MILLIS = 24L * 60L * 60L * 1000L
    }

    fun current(securityScopeDigest: String): AutomationConsent? {
        val consent = storage.load() ?: return null
        val currentTime = now()
        if (consent.schemaVersion != SCHEMA_VERSION || consent.appVersion != appVersion ||
            consent.securityScopeDigest != securityScopeDigest || currentTime < consent.lastObservedMillis ||
            (consent.status == ConsentStatus.GRANTED && currentTime >= consent.expiresAtMillis)
        ) {
            storage.save(null)
            return null
        }
        val observed = consent.copy(lastObservedMillis = currentTime)
        storage.save(observed)
        return observed
    }

    fun request(scope: AutomationScope, requestId: String, securityScopeDigest: String): AutomationConsent {
        val existing = current(securityScopeDigest)
        if (existing?.status == ConsentStatus.REQUESTED && existing.scope == scope && existing.requestId == requestId) return existing
        val requested = AutomationConsent(
            SCHEMA_VERSION, newGeneration(), requestId, scope, appVersion, securityScopeDigest,
            ConsentStatus.REQUESTED, 0, 0, now(),
        )
        storage.save(requested)
        return requested
    }

    fun grant(generation: String, securityScopeDigest: String): AutomationConsent? {
        val requested = current(securityScopeDigest)
        if (requested?.generation != generation || requested.status != ConsentStatus.REQUESTED) return null
        val currentTime = now()
        return requested.copy(
            status = ConsentStatus.GRANTED,
            grantedAtMillis = currentTime,
            expiresAtMillis = currentTime + MAX_LIFETIME_MILLIS,
            lastObservedMillis = currentTime,
        ).also(storage::save)
    }

    fun isGranted(scope: AutomationScope, generation: String, securityScopeDigest: String): Boolean {
        val consent = current(securityScopeDigest)
        return consent?.status == ConsentStatus.GRANTED && consent.scope == scope && consent.generation == generation
    }

    fun invalidate() = storage.save(null)
}

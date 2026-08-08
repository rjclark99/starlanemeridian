package app.kodisetup.tv.automation

import app.kodisetup.tv.model.SetupManifest
import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Test

class AutomationSecurityScopeTest {
    private val json = Json { ignoreUnknownKeys = false }

    @Test fun `same config version with changed install payload has different digest`() {
        val original = manifest(bootstrapHash = "aaa", telemetryEnabled = true)
        val changedPayload = manifest(bootstrapHash = "bbb", telemetryEnabled = true)
        assertNotEquals(AutomationSecurityScope.digest(original), AutomationSecurityScope.digest(changedPayload))
    }

    @Test fun `telemetry does not enter automation security scope`() {
        val enabled = manifest(bootstrapHash = "aaa", telemetryEnabled = true)
        val disabled = manifest(bootstrapHash = "aaa", telemetryEnabled = false)
        assertEquals(AutomationSecurityScope.digest(enabled), AutomationSecurityScope.digest(disabled))
    }

    private fun manifest(bootstrapHash: String, telemetryEnabled: Boolean): SetupManifest = json.decodeFromString(
        """{
          "schemaVersion":1,"configVersion":"5.8","stage":"test","minimumSetupAppVersion":8,
          "kodi":{"channel":"stable","packageName":"org.xbmc.kodi","architectures":{"arm64-v8a":{"url":"https://example.test/kodi.apk","sha256":"kodi-hash","signerSha256":"signer","abi":"arm64-v8a"}}},
          "bootstrap":{"url":"https://example.test/bootstrap.zip","sha256":"$bootstrapHash"},
          "applications":[{"id":"proton-vpn","name":"Proton","packageName":"ch.protonvpn.android","storePreference":["google-play"],"storeUris":{"google-play":"market://details?id=ch.protonvpn.android"},"artifacts":[],"required":true}],
          "repositories":[],"addons":[],"skin":{"addonId":"skin.test","homeMenu":[]},
          "telemetry":{"enabled":$telemetryEnabled,"diagnosticsRequireConsent":true},
          "signature":{"keyId":"test","algorithm":"Ed25519","value":"ignored"}
        }""",
    )
}

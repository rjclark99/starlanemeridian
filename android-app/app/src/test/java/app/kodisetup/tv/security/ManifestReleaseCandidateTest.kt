package app.kodisetup.tv.security

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ManifestReleaseCandidateTest {
    @Test
    fun derivesOnlyTheCurrentVersionTagFromTheFixedGitHubLatestUrl() {
        assertEquals(
            "https://github.com/rjclark99/starlanemeridian/releases/download/v0.5.11-test/manifest.json",
            ManifestReleaseCandidate.url(
                "https://github.com/rjclark99/starlanemeridian/releases/latest/download/manifest.json",
                "0.5.11",
            ),
        )
        assertNull(ManifestReleaseCandidate.url("https://example.test/manifest.json", "0.5.11"))
        assertNull(
            ManifestReleaseCandidate.url(
                "https://github.com/rjclark99/starlanemeridian/releases/latest/download/manifest.json",
                "0.5.11/../../latest",
            ),
        )
    }

    @Test
    fun checksTheVersionTagOnlyWhileLatestTargetsAnOlderApp() {
        val older = Json.parseToJsonElement("""{"minimumSetupAppVersion":11}""").jsonObject
        val current = Json.parseToJsonElement("""{"minimumSetupAppVersion":12}""").jsonObject

        assertTrue(ManifestReleaseCandidate.shouldCheck(older, 12))
        assertFalse(ManifestReleaseCandidate.shouldCheck(current, 12))
    }
}

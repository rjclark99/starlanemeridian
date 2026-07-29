package app.kodisetup.tv.net

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class RealDebridAuthorizationTest {
    @Test fun ignoresBroaderDirectUrlAndBuildsAllowlistedDeviceUrl() {
        val code = deviceCode(
            directUrl = "https://real-debrid.com/authorize?client_id=public&device_id=opaque",
        )

        assertEquals(
            "https://real-debrid.com/device?user_code=ABCD-EFGH",
            RealDebridAuthorization.deviceUrl(code),
        )
    }

    @Test fun rejectsUnexpectedVerificationUrl() {
        val code = deviceCode(verificationUrl = "https://example.com/device")

        assertThrows(IllegalArgumentException::class.java) {
            RealDebridAuthorization.deviceUrl(code)
        }
    }

    @Test fun rejectsUnexpectedDeviceCodeShape() {
        val code = deviceCode(userCode = "code&next=bad")

        assertThrows(IllegalArgumentException::class.java) {
            RealDebridAuthorization.deviceUrl(code)
        }
    }

    private fun deviceCode(
        userCode: String = "ABCD-EFGH",
        verificationUrl: String = "https://real-debrid.com/device",
        directUrl: String? = null,
    ) = RealDebridClient.DeviceCode(
        deviceCode = "opaque-device-code",
        userCode = userCode,
        interval = 5,
        expiresIn = 900,
        verificationUrl = verificationUrl,
        directVerificationUrl = directUrl,
    )
}

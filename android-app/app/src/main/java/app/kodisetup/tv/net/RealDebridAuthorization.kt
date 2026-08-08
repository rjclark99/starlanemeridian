package app.kodisetup.tv.net

import java.net.URI

object RealDebridAuthorization {
    private val userCode = Regex("^[A-Z0-9-]{4,32}$", RegexOption.IGNORE_CASE)

    fun deviceUrl(code: RealDebridClient.DeviceCode): String {
        val verification = URI.create(code.verificationUrl)
        require(
            verification.scheme == "https" &&
                verification.host == "real-debrid.com" &&
                verification.path == "/device" &&
                verification.port == -1 &&
                verification.userInfo == null &&
                verification.rawQuery == null &&
                verification.rawFragment == null
        ) { "Real-Debrid returned an unexpected authorization URL" }
        require(userCode.matches(code.userCode)) { "Real-Debrid returned an unexpected device code" }

        // Real-Debrid's optional direct URL can use a broader /authorize flow. The
        // The control service may relay only the official device page and short-lived code.
        return "https://real-debrid.com/device?user_code=${code.userCode}"
    }
}

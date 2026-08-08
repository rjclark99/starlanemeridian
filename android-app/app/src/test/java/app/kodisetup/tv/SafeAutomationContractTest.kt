package app.kodisetup.tv

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class SafeAutomationContractTest {
    @Test fun `strict flow preserves visible confirmations and profile boundary`() {
        val root = File("src/main/java/app/kodisetup/tv")
        val viewModel = File(root, "SetupViewModel.kt").readText()
        val activity = File(root, "MainActivity.kt").readText()
        val installer = File(root, "install/PackageInstallManager.kt").readText()

        assertFalse(viewModel.contains("KodiProfileConfigurator("))
        assertTrue(activity.contains("Kodi Unknown Sources"))
        assertTrue(activity.contains("Install from ZIP"))
        assertTrue(activity.contains("Bootstrap's separate approval"))
        assertTrue(activity.contains("Check applied setup"))
        assertTrue(installer.contains("USER_ACTION_REQUIRED"))
        val transaction = File(root, "install/FixedBootstrapTransaction.kt").readText()
        val activation = File(root, "install/KodiLoopbackBootstrapActivator.kt").readText()
        assertTrue(transaction.contains("runCatching { setFeature(\"http://apache.org/xml/features/disallow-doctype-decl\""))
        assertTrue(viewModel.contains("FixedBootstrapEligibility.usesAutomaticPath"))
        assertTrue(viewModel.contains("FixedBootstrapTransaction(root).install"))
        assertTrue(viewModel.contains("BootstrapExporter(getApplication()).export"))
        assertTrue(viewModel.contains("FixedBootstrapEligibility.requireEligible"))
        assertTrue(viewModel.contains("bootstrap_launch_pending"))
        assertTrue(viewModel.contains("bootstrapPreparation?.isActive == true"))
        assertTrue(viewModel.contains("BootstrapRecoveryPolicy.shouldRetry"))
        assertTrue(viewModel.contains("retrying the fixed loopback activation"))
        assertFalse(transaction.contains("staged-autoexec"))
        assertTrue(activation.contains("InetSocketAddress(\"127.0.0.1\", 9090)"))
        assertTrue(activation.contains("Addons.GetAddonDetails"))
        assertTrue(activation.contains("Addons.SetAddonEnabled"))
        assertTrue(activation.contains("\"method\":\"Application.Quit\""))
        assertFalse(activation.contains("Addons.ExecuteAddon"))
    }

    @Test fun `remote mutating commands request consent instead of invoking effects`() {
        val source = File("src/main/java/app/kodisetup/tv/SetupViewModel.kt").readText()
        listOf("INSTALL_KODI", "INSTALL_PROTON", "PREPARE_BOOTSTRAP", "OPEN_KODI", "BEGIN_REAL_DEBRID_AUTH", "SYNC_CONFIG").forEach {
            assertTrue(source.contains("\"$it\" -> requestLocalConsent("))
        }
    }
}

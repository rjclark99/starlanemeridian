package app.kodisetup.tv

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class BootstrapRecoveryPolicyTest {
    @Test fun `missing applied state retries only eligible fixed automatic flow`() {
        assertTrue(BootstrapRecoveryPolicy.shouldRetry(false, false, 25, true, true))
        assertTrue(BootstrapRecoveryPolicy.shouldRetry(false, false, 28, true, true))
        assertFalse(BootstrapRecoveryPolicy.shouldRetry(true, false, 28, true, true))
        assertFalse(BootstrapRecoveryPolicy.shouldRetry(false, true, 28, true, true))
        assertFalse(BootstrapRecoveryPolicy.shouldRetry(false, false, 28, false, true))
        assertFalse(BootstrapRecoveryPolicy.shouldRetry(false, false, 28, true, false))
    }

    @Test fun `modern Android and unsupported older APIs remain manual`() {
        assertFalse(BootstrapRecoveryPolicy.shouldRetry(false, false, 24, true, true))
        assertFalse(BootstrapRecoveryPolicy.shouldRetry(false, false, 29, true, true))
        assertFalse(BootstrapRecoveryPolicy.shouldRetry(false, false, 36, true, true))
    }
}

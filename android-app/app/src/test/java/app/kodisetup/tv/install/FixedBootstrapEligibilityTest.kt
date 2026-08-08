package app.kodisetup.tv.install

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class FixedBootstrapEligibilityTest {
    @Test fun `only API25-28 strict flow uses automatic path`() {
        assertTrue(FixedBootstrapEligibility.usesAutomaticPath(25, true))
        assertTrue(FixedBootstrapEligibility.usesAutomaticPath(28, true))
        assertFalse(FixedBootstrapEligibility.usesAutomaticPath(29, true))
        assertFalse(FixedBootstrapEligibility.usesAutomaticPath(28, false))
    }

    @Test fun `permission denial unknown process state and active Kodi are refused`() {
        assertFailure { FixedBootstrapEligibility.requireEligible(28, true, false, true, true, false) }
        assertFailure { FixedBootstrapEligibility.requireEligible(28, true, true, true, false, false) }
        assertFailure { FixedBootstrapEligibility.requireEligible(28, true, true, true, true, true) }
        assertFailure { FixedBootstrapEligibility.requireEligible(28, true, true, false, true, false) }
    }

    private fun assertFailure(block: () -> Unit) { assertTrue(runCatching(block).isFailure) }
}

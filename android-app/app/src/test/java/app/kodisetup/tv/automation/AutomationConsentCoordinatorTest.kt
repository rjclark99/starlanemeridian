package app.kodisetup.tv.automation

import org.junit.Assert.*
import org.junit.Test

class AutomationConsentCoordinatorTest {
    private class MemoryStorage(var value: AutomationConsent? = null) : ConsentStorage {
        override fun load() = value
        override fun save(consent: AutomationConsent?) { value = consent }
    }

    @Test fun `request has no grant and grant is generation bound`() {
        val storage = MemoryStorage()
        val clock = longArrayOf(1_000)
        val coordinator = AutomationConsentCoordinator(storage, 8, { clock[0] }, { "run-1" })
        val request = coordinator.request(AutomationScope.INSTALL_KODI, "command-1", "5.8")

        assertEquals(ConsentStatus.REQUESTED, request.status)
        assertFalse(coordinator.isGranted(AutomationScope.INSTALL_KODI, request.generation, "5.8"))
        assertNull(coordinator.grant("stale", "5.8"))
        assertNotNull(coordinator.grant("run-1", "5.8"))
        assertNull("a callback cannot commit the same consent twice", coordinator.grant("run-1", "5.8"))
        coordinator.request(AutomationScope.INSTALL_PROTON, "command-2", "5.8")
        assertFalse("a callback from the superseded generation is stale", coordinator.isGranted(AutomationScope.INSTALL_KODI, "run-1", "5.8"))
    }

    @Test fun `grant resumes but expires and detects clock rollback`() {
        val storage = MemoryStorage()
        var time = 5_000L
        val first = AutomationConsentCoordinator(storage, 8, { time }, { "run-1" })
        first.request(AutomationScope.STRICT_SETUP, "local", "5.8")
        first.grant("run-1", "5.8")
        val restored = AutomationConsentCoordinator(storage, 8, { time })
        assertTrue(restored.isGranted(AutomationScope.STRICT_SETUP, "run-1", "5.8"))

        time -= 1
        assertFalse(restored.isGranted(AutomationScope.STRICT_SETUP, "run-1", "5.8"))

        time = 10_000
        first.request(AutomationScope.STRICT_SETUP, "local", "5.8")
        first.grant("run-1", "5.8")
        time += AutomationConsentCoordinator.MAX_LIFETIME_MILLIS
        assertFalse(first.isGranted(AutomationScope.STRICT_SETUP, "run-1", "5.8"))
    }

    @Test fun `operation app security digest and revocation invalidate consent`() {
        val storage = MemoryStorage()
        val coordinator = AutomationConsentCoordinator(storage, 8, { 1_000 }, { "run-1" })
        coordinator.request(AutomationScope.INSTALL_KODI, "command-1", "5.8")
        coordinator.grant("run-1", "5.8")
        assertFalse(coordinator.isGranted(AutomationScope.INSTALL_PROTON, "run-1", "5.8"))
        assertNull("same-version payload digest changes invalidate consent", coordinator.current("different-security-digest"))

        coordinator.request(AutomationScope.STRICT_SETUP, "local", "5.8")
        coordinator.invalidate()
        assertNull(coordinator.current("5.8"))

        val oldApp = AutomationConsentCoordinator(storage, 7, { 1_000 }, { "old" })
        oldApp.request(AutomationScope.STRICT_SETUP, "local", "5.8")
        assertNull(AutomationConsentCoordinator(storage, 8, { 1_000 }).current("5.8"))
    }

    @Test fun `repeated remote request is idempotent`() {
        val storage = MemoryStorage()
        var generated = 0
        val coordinator = AutomationConsentCoordinator(storage, 8, { 1_000 }, { "run-${++generated}" })
        val first = coordinator.request(AutomationScope.PREPARE_BOOTSTRAP, "command-1", "5.8")
        val repeated = coordinator.request(AutomationScope.PREPARE_BOOTSTRAP, "command-1", "5.8")
        assertEquals(first.generation, repeated.generation)
        assertEquals(1, generated)
    }

    @Test fun `invalidation reasons distinguish expiry update scope and clock rollback`() {
        val storage = MemoryStorage()
        var time = 5_000L
        val coordinator = AutomationConsentCoordinator(storage, 8, { time }, { "run-1" })
        coordinator.request(AutomationScope.STRICT_SETUP, "local", "scope-1")
        coordinator.grant("run-1", "scope-1")

        assertEquals(ConsentInvalidationReason.APP_UPDATED,
            AutomationConsentCoordinator(storage, 9, { time }).invalidationReason("scope-1"))
        assertEquals(ConsentInvalidationReason.SCOPE_CHANGED, coordinator.invalidationReason("scope-2"))
        time = 4_999L
        assertEquals(ConsentInvalidationReason.CLOCK_ROLLBACK, coordinator.invalidationReason("scope-1"))
        time = 5_000L + AutomationConsentCoordinator.MAX_LIFETIME_MILLIS
        assertEquals(ConsentInvalidationReason.EXPIRED, coordinator.invalidationReason("scope-1"))
    }
}

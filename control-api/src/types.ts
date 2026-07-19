export interface Env {
  DB: D1Database;
  PAIRING_TTL_SECONDS: string;
  STATUS_RETENTION_DAYS: string;
}

export const commandKinds = [
  "START_SETUP",
  "INSTALL_KODI",
  "INSTALL_PROTON",
  "PREPARE_BOOTSTRAP",
  "OPEN_KODI",
  "BEGIN_REAL_DEBRID_AUTH",
  "SYNC_CONFIG",
  "RETRY_CURRENT_STEP",
  "RETRY_STEP",
  "OPEN_AUTHORIZATION",
  "REQUEST_DIAGNOSTICS",
] as const;
export type CommandKind = typeof commandKinds[number];
export const setupSteps = ["WELCOME", "CONFIGURATION", "KODI", "PROTON", "BOOTSTRAP", "ACCOUNT_LINK", "COMPLETE"] as const;
export const setupPhases = [
  "READY", "PAIRING", "VERIFYING_CONFIGURATION", "CONFIGURATION_VERIFIED",
  "DOWNLOADING_KODI", "WAITING_INSTALL_CONFIRMATION", "KODI_READY",
  "WAITING_PROTON_STORE", "DOWNLOADING_PROTON", "PROTON_READY",
  "DOWNLOADING_BOOTSTRAP", "BOOTSTRAP_READY", "WAITING_KODI_BOOTSTRAP",
  "REQUESTING_REAL_DEBRID_AUTH", "WAITING_REAL_DEBRID_AUTH", "ACCOUNT_LINKED",
  "COMPLETE", "ERROR",
] as const;

export interface DeviceRow {
  id: string; household_id: string; public_key_spki: string; token_hash: string; model: string; os_version: string;
  app_version: number | null; config_version: string | null; setup_step: string | null; error_code: string | null;
  debrid_expiry: string | null; created_at: number; last_seen_at: number | null; deleted_at: number | null;
  manufacturer: string | null; product: string | null; api_level: number | null; architecture: string | null;
  security_patch: string | null; free_storage_mb: number | null; total_storage_mb: number | null; total_memory_mb: number | null;
  kodi_version: string | null; proton_version: string | null; install_permission: number | null; bootstrap_ready: number | null;
  automatic_setup: number | null; setup_phase: string | null; progress_percent: number | null; status_message: string | null; busy: number | null;
}

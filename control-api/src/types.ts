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

export interface DeviceRow {
  id: string; household_id: string; public_key_spki: string; token_hash: string; model: string; os_version: string;
  app_version: number | null; config_version: string | null; setup_step: string | null; error_code: string | null;
  debrid_expiry: string | null; created_at: number; last_seen_at: number | null; deleted_at: number | null;
}

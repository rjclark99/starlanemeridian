PRAGMA foreign_keys = ON;

CREATE TABLE households (
  id TEXT PRIMARY KEY,
  alias TEXT NOT NULL CHECK(length(alias) BETWEEN 1 AND 80),
  created_at INTEGER NOT NULL,
  deleted_at INTEGER
);

CREATE TABLE pairing_codes (
  code_hash TEXT PRIMARY KEY,
  household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
  expires_at INTEGER NOT NULL,
  used_at INTEGER,
  used_marker TEXT UNIQUE
);

CREATE TABLE devices (
  id TEXT PRIMARY KEY,
  household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
  public_key_spki TEXT NOT NULL,
  token_hash TEXT NOT NULL UNIQUE,
  model TEXT NOT NULL CHECK(length(model) <= 128),
  os_version TEXT NOT NULL CHECK(length(os_version) <= 64),
  app_version INTEGER,
  config_version TEXT,
  setup_step TEXT,
  error_code TEXT,
  debrid_expiry TEXT,
  created_at INTEGER NOT NULL,
  last_seen_at INTEGER,
  deleted_at INTEGER
);

CREATE TABLE request_nonces (
  device_id TEXT NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  nonce TEXT NOT NULL,
  expires_at INTEGER NOT NULL,
  PRIMARY KEY(device_id, nonce)
);

CREATE TABLE commands (
  id TEXT PRIMARY KEY,
  device_id TEXT NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK(kind IN ('START_SETUP','INSTALL_KODI','INSTALL_PROTON','PREPARE_BOOTSTRAP','OPEN_KODI','BEGIN_REAL_DEBRID_AUTH','SYNC_CONFIG','RETRY_CURRENT_STEP','RETRY_STEP','OPEN_AUTHORIZATION','REQUEST_DIAGNOSTICS')),
  payload TEXT NOT NULL DEFAULT '{}',
  created_at INTEGER NOT NULL,
  delivered_at INTEGER,
  completed_at INTEGER,
  result TEXT
);

CREATE TABLE audit (
  id TEXT PRIMARY KEY,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  target_id TEXT,
  detail TEXT NOT NULL,
  created_at INTEGER NOT NULL
);

CREATE INDEX idx_devices_household ON devices(household_id);
CREATE INDEX idx_commands_pending ON commands(device_id, delivered_at);
CREATE INDEX idx_nonces_expiry ON request_nonces(expires_at);

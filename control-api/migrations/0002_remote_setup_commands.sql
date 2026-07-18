PRAGMA foreign_keys = OFF;

CREATE TABLE commands_v2 (
  id TEXT PRIMARY KEY,
  device_id TEXT NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK(kind IN ('START_SETUP','INSTALL_KODI','INSTALL_PROTON','PREPARE_BOOTSTRAP','OPEN_KODI','BEGIN_REAL_DEBRID_AUTH','SYNC_CONFIG','RETRY_CURRENT_STEP','RETRY_STEP','OPEN_AUTHORIZATION','REQUEST_DIAGNOSTICS')),
  payload TEXT NOT NULL DEFAULT '{}',
  created_at INTEGER NOT NULL,
  delivered_at INTEGER,
  completed_at INTEGER,
  result TEXT
);

INSERT INTO commands_v2(id,device_id,kind,payload,created_at,delivered_at,completed_at,result)
SELECT id,device_id,kind,payload,created_at,delivered_at,completed_at,result FROM commands;

DROP TABLE commands;
ALTER TABLE commands_v2 RENAME TO commands;
CREATE INDEX idx_commands_pending ON commands(device_id, delivered_at);

PRAGMA foreign_keys = ON;

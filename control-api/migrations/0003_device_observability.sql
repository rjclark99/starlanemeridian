ALTER TABLE devices ADD COLUMN manufacturer TEXT;
ALTER TABLE devices ADD COLUMN product TEXT;
ALTER TABLE devices ADD COLUMN api_level INTEGER;
ALTER TABLE devices ADD COLUMN architecture TEXT;
ALTER TABLE devices ADD COLUMN security_patch TEXT;
ALTER TABLE devices ADD COLUMN free_storage_mb INTEGER;
ALTER TABLE devices ADD COLUMN total_storage_mb INTEGER;
ALTER TABLE devices ADD COLUMN total_memory_mb INTEGER;
ALTER TABLE devices ADD COLUMN kodi_version TEXT;
ALTER TABLE devices ADD COLUMN proton_version TEXT;
ALTER TABLE devices ADD COLUMN install_permission INTEGER;
ALTER TABLE devices ADD COLUMN bootstrap_ready INTEGER;
ALTER TABLE devices ADD COLUMN automatic_setup INTEGER;
ALTER TABLE devices ADD COLUMN setup_phase TEXT;
ALTER TABLE devices ADD COLUMN progress_percent INTEGER;
ALTER TABLE devices ADD COLUMN status_message TEXT;
ALTER TABLE devices ADD COLUMN busy INTEGER;

CREATE TABLE device_status_events (
  id TEXT PRIMARY KEY,
  device_id TEXT NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  setup_step TEXT NOT NULL,
  setup_phase TEXT NOT NULL,
  progress_percent INTEGER NOT NULL,
  status_message TEXT,
  error_code TEXT,
  created_at INTEGER NOT NULL
);

CREATE INDEX idx_device_status_events_device ON device_status_events(device_id, created_at DESC);

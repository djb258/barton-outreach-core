-- BAR-307: Cross-channel state machine per contact
-- Tracks which channel is primary (MG=email, HR=LinkedIn/HeyReach)
-- Advisory for now — logs and tracks but doesn't hard-block

CREATE TABLE IF NOT EXISTS lcs_contact_channel_state (
  contact_email     TEXT PRIMARY KEY,
  sovereign_company_id TEXT NOT NULL,
  primary_channel   TEXT NOT NULL DEFAULT 'MG',
  channel_state     TEXT NOT NULL DEFAULT 'email_active',
  email_status      TEXT NOT NULL DEFAULT 'active',
  linkedin_status   TEXT NOT NULL DEFAULT 'not_started',
  last_channel_switch_at TEXT,
  switch_reason     TEXT,
  created_at        TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_channel_state_company ON lcs_contact_channel_state(sovereign_company_id);

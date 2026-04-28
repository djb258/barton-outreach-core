-- ─────────────────────────────────────────────────────────────
-- BAR-304: Multi-Touch Sequence Engine
--
-- Two tables:
--   lcs_sequence_def — defines multi-step playbooks
--   lcs_contact_sequence_state — tracks each contact's position
--
-- Trunk Constants addressed:
--   #8 Interaction Sequence Blueprint
--   #20 Publishing Cadence Flow
--   #26 Trust Accumulation Sequence
-- ─────────────────────────────────────────────────────────────

-- Sequence definitions — what messages, in what order, with what delays
CREATE TABLE IF NOT EXISTS lcs_sequence_def (
  sequence_id      TEXT NOT NULL,
  step_number      INTEGER NOT NULL,
  frame_id         TEXT NOT NULL,           -- which message template from lcs_frame_registry
  channel          TEXT NOT NULL DEFAULT 'MG',  -- MG (Mailgun) or HR (HeyReach/LinkedIn)
  delay_hours      INTEGER NOT NULL DEFAULT 0,  -- hours after previous step (0 = immediate)
  condition        TEXT DEFAULT NULL,        -- NULL = always send, 'opened' = only if prev opened, 'not_opened' = only if NOT opened
  is_active        INTEGER NOT NULL DEFAULT 1,
  created_at       TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (sequence_id, step_number)
);

-- Seed: Default outreach sequence (5-touch, email, 3-day cadence)
INSERT OR IGNORE INTO lcs_sequence_def VALUES
  ('SEQ-COLD-EMAIL-V1', 1, 'COLD-INTRO-V1',      'MG', 0,   NULL,         1, datetime('now')),
  ('SEQ-COLD-EMAIL-V1', 2, 'FOLLOWUP-OPEN-V1',    'MG', 72,  'opened',     1, datetime('now')),
  ('SEQ-COLD-EMAIL-V1', 3, 'FOLLOWUP-GHOST-V1',   'MG', 72,  'not_opened', 1, datetime('now')),
  ('SEQ-COLD-EMAIL-V1', 4, 'FOLLOWUP-VALUE-V1',   'MG', 96,  NULL,         1, datetime('now')),
  ('SEQ-COLD-EMAIL-V1', 5, 'FOLLOWUP-BREAK-V1',   'MG', 120, NULL,         1, datetime('now'));

-- Per-contact sequence state — where each contact is in which sequence
CREATE TABLE IF NOT EXISTS lcs_contact_sequence_state (
  id                TEXT PRIMARY KEY,
  sovereign_company_id TEXT NOT NULL,
  contact_email     TEXT NOT NULL,
  sequence_id       TEXT NOT NULL,
  current_step      INTEGER NOT NULL DEFAULT 1,
  status            TEXT NOT NULL DEFAULT 'active',  -- active | paused | completed | stopped
  last_step_at      TEXT,                            -- when the last step was sent
  next_step_after   TEXT,                            -- when the next step should fire
  last_engagement   TEXT DEFAULT NULL,               -- last engagement event (opened, clicked, etc)
  created_at        TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_contact_seq_company ON lcs_contact_sequence_state(sovereign_company_id);
CREATE INDEX IF NOT EXISTS idx_contact_seq_status ON lcs_contact_sequence_state(status, next_step_after);
CREATE INDEX IF NOT EXISTS idx_contact_seq_email ON lcs_contact_sequence_state(contact_email);

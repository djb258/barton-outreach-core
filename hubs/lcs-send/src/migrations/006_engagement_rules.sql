-- ─────────────────────────────────────────────────────────────
-- lcs_engagement_rules — Closed Loop Response Rules
-- BAR-303: Close the Circle
--
-- One row per trigger event. Compiler reads this to decide next action.
-- Human-owned. No LLM modifies this table.
--
-- Trunk Constants addressed:
--   #2 Engagement Signal Flow
--   #4 Feedback Return Loop
--   #24 Signal-to-Distribution Feedback Loop
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS lcs_engagement_rules (
  rule_id          TEXT PRIMARY KEY,
  trigger_event    TEXT NOT NULL UNIQUE,
  action           TEXT NOT NULL,
  delay_hours      INTEGER NOT NULL DEFAULT 0,
  followup_frame_id TEXT,
  is_active        INTEGER NOT NULL DEFAULT 1,
  created_at       TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Seed defaults — Dave tunes values, not the code
INSERT OR IGNORE INTO lcs_engagement_rules VALUES
  ('ER-001', 'opened',          'send_followup',    48,  'FOLLOWUP-OPEN-V1',   1, datetime('now'), datetime('now')),
  ('ER-002', 'clicked',         'send_followup',    24,  'FOLLOWUP-CLICK-V1',  1, datetime('now'), datetime('now')),
  ('ER-003', 'bounced',         'stop',              0,   NULL,                 1, datetime('now'), datetime('now')),
  ('ER-004', 'complained',      'stop',              0,   NULL,                 1, datetime('now'), datetime('now')),
  ('ER-005', 'no_response_3d',  'send_followup',    72,  'FOLLOWUP-GHOST-V1',  1, datetime('now'), datetime('now')),
  ('ER-006', 'no_response_7d',  'escalate_channel',  0,   NULL,                1, datetime('now'), datetime('now'));

CREATE INDEX IF NOT EXISTS idx_engagement_rules_trigger ON lcs_engagement_rules(trigger_event);

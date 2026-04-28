CREATE TABLE IF NOT EXISTS lcs_contact_engagement_score (
  contact_email     TEXT PRIMARY KEY,
  sovereign_company_id TEXT NOT NULL,
  email_score       REAL NOT NULL DEFAULT 0,
  linkedin_score    REAL NOT NULL DEFAULT 0,
  web_score         REAL NOT NULL DEFAULT 0,
  composite_score   REAL NOT NULL DEFAULT 0,
  total_events      INTEGER NOT NULL DEFAULT 0,
  last_event_type   TEXT,
  last_event_at     TEXT,
  is_hot_lead       INTEGER NOT NULL DEFAULT 0,
  created_at        TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_engagement_company ON lcs_contact_engagement_score(sovereign_company_id);
CREATE INDEX IF NOT EXISTS idx_engagement_hot ON lcs_contact_engagement_score(is_hot_lead) WHERE is_hot_lead = 1;
CREATE INDEX IF NOT EXISTS idx_engagement_composite ON lcs_contact_engagement_score(composite_score DESC);

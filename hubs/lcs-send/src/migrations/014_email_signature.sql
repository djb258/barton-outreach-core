-- ═══════════════════════════════════════════════════════════════
-- Migration 014: Email Signature Table
-- BAR-176 — Data-driven sender signature for all outbound email
-- ═══════════════════════════════════════════════════════════════
-- One row per agent. Pulled at constructSid time, keyed by
-- cid.agent_number. Falls back to is_active = 1 if no agent match.
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS lcs_email_signature (
  sig_id        TEXT PRIMARY KEY,          -- SIG-{uuid}
  agent_number  TEXT NOT NULL UNIQUE,      -- SA-001, SA-002, etc.
  name          TEXT NOT NULL,             -- Full name
  title         TEXT NOT NULL,             -- Job title
  company       TEXT NOT NULL,             -- Company name
  phone         TEXT,                      -- Phone (optional — omit if null)
  website       TEXT,                      -- Website URL (no https://)
  linkedin_url  TEXT,                      -- linkedin.com/in/handle
  booking_link  TEXT,                      -- Primary CTA — calendar URL
  tagline       TEXT,                      -- One-liner under company
  is_active     INTEGER NOT NULL DEFAULT 1, -- 1 = active, 0 = inactive
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Seed: Dave Barton (SA-001)
INSERT OR IGNORE INTO lcs_email_signature (
  sig_id, agent_number, name, title, company,
  phone, website, linkedin_url, booking_link, tagline,
  is_active, created_at, updated_at
) VALUES (
  'SIG-SA001-20260416',
  'SA-001',
  'Dave Barton',
  'Founder & Insurance Informatics Pioneer',
  'Insurance Informatics',
  '(304) 821-2400',
  'insuranceinformatics.com',
  'linkedin.com/in/dbarton',
  'https://calendar.app.google/VT41mpEgTWDexFET8',
  'The only insurance informatics firm in the country.',
  1,
  datetime('now'),
  datetime('now')
);

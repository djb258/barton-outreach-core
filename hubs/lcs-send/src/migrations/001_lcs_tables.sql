-- ═══════════════════════════════════════════════════════════════
-- LCS Hub — D1 Working Tables
-- ═══════════════════════════════════════════════════════════════
-- D1 = workspace (edge). Neon = vault (source of truth).
-- Hub-spoke: all tables serve the hub. Spokes are external.
--
-- CQRS: Each stage has its own CANONICAL table.
--       All failures write to err0 (single ERROR table).
--       All actions logged to event (append-only CET).
-- ═══════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────
-- COMPANY — Working copy seeded from Neon vault
-- Neon is the vault. D1 is the workspace.
-- Lifecycle: SEED (Neon→D1) → WORK (all processing) → PUSH (D1→Neon)
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS company (
  sovereign_company_id  TEXT PRIMARY KEY,
  company_name          TEXT NOT NULL,
  state                 TEXT,
  zip                   TEXT,
  employee_count        INTEGER,
  assigned_agent        TEXT,               -- gate 0 — set during seed from territory views
  -- DOL data (seeded from Neon DOL views)
  has_5500_filing       INTEGER NOT NULL DEFAULT 0,  -- 0/1 boolean
  renewal_month         INTEGER,
  premium_current       REAL,
  premium_prior         REAL,
  carrier_current       TEXT,
  carrier_prior         TEXT,
  broker_current        TEXT,
  broker_prior          TEXT,
  -- People slots (seeded from Neon people views)
  ceo_name              TEXT,
  ceo_email             TEXT,
  ceo_linkedin          TEXT,
  cfo_name              TEXT,
  cfo_email             TEXT,
  cfo_linkedin          TEXT,
  hr_name               TEXT,
  hr_email              TEXT,
  hr_linkedin           TEXT,
  -- Lifecycle
  lifecycle_phase       TEXT NOT NULL DEFAULT 'OUTREACH',  -- OUTREACH, SALES, CLIENT
  seeded_at             TEXT,
  updated_at            TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_company_agent ON company(assigned_agent);
CREATE INDEX IF NOT EXISTS idx_company_state ON company(state);
CREATE INDEX IF NOT EXISTS idx_company_lifecycle ON company(lifecycle_phase);

-- ─────────────────────────────────────────────────────────────
-- SIGNAL QUEUE — Ingress from dumb worker spokes
-- Standard format. Hub doesn't care which spoke produced it.
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS signal_queue (
  signal_id             TEXT PRIMARY KEY,
  sovereign_company_id  TEXT NOT NULL,
  worker                TEXT NOT NULL,       -- DOL, PEOPLE, BLOG, TALENT_FLOW
  signal_type           TEXT NOT NULL,       -- RENEWAL_APPROACHING, TF-01, EXPANSION, etc.
  magnitude             REAL,               -- signal strength (TBD for some workers)
  expires_at            TEXT,               -- ISO8601 — signal is stale after this
  raw_payload           TEXT,               -- JSON — worker-specific data
  status                TEXT NOT NULL DEFAULT 'pending',  -- pending, processing, compiled, expired
  created_at            TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at            TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_signal_status ON signal_queue(status);
CREATE INDEX IF NOT EXISTS idx_signal_company ON signal_queue(sovereign_company_id);
CREATE INDEX IF NOT EXISTS idx_signal_worker ON signal_queue(worker);
CREATE INDEX IF NOT EXISTS idx_signal_expires ON signal_queue(expires_at);

-- ─────────────────────────────────────────────────────────────
-- CID — Compiled Intelligence Dossier (Stage 1 CANONICAL)
-- One per compilation event. Company may have multiple CIDs over time.
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS cid (
  cid_id                TEXT PRIMARY KEY,    -- CID-{DATE}-{ULID}
  sovereign_company_id  TEXT NOT NULL,
  assigned_agent        TEXT,               -- gate 0 — service agent
  signal_ids            TEXT NOT NULL,       -- JSON array of signal_ids that triggered this
  layer_financial       TEXT,               -- JSON — DOL data snapshot
  layer_personnel       TEXT,               -- JSON — people slots snapshot
  layer_behavioral      TEXT,               -- JSON — blog signals snapshot
  layer_movement        TEXT,               -- JSON — talent flow signals snapshot
  layer_engagement      TEXT,               -- JSON — outreach history snapshot
  gate_results          TEXT,               -- JSON — pass/fail per gate (0-8)
  status                TEXT NOT NULL DEFAULT 'compiled',  -- compiled, promoted, failed, blocked
  created_at            TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_cid_company ON cid(sovereign_company_id);
CREATE INDEX IF NOT EXISTS idx_cid_status ON cid(status);
CREATE INDEX IF NOT EXISTS idx_cid_agent ON cid(assigned_agent);

-- ─────────────────────────────────────────────────────────────
-- SID — Signal Document / Campaign (Stage 2 CANONICAL)
-- One campaign per CID. Contains multiple messages (sequence).
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS sid (
  sid_id                TEXT PRIMARY KEY,    -- SID-{DATE}-{ULID}
  cid_id                TEXT NOT NULL,
  sovereign_company_id  TEXT NOT NULL,
  campaign_type         TEXT NOT NULL,       -- monthly_touch, renewal, exec_change, activity, priority
  audience_path         TEXT NOT NULL,       -- cfo_ceo_money, hr_workload
  target_slot           TEXT NOT NULL,       -- CEO, CFO, HR
  target_name           TEXT,
  target_email          TEXT,
  target_linkedin       TEXT,
  message_count         INTEGER NOT NULL DEFAULT 1,
  messages              TEXT NOT NULL,       -- JSON array of message objects
  content_sources       TEXT,               -- JSON — which svg-brain chunks were used
  monte_carlo_ref       TEXT,               -- JSON — what Monte Carlo recommended
  status                TEXT NOT NULL DEFAULT 'designed',  -- designed, active, completed, stopped
  created_at            TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at            TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_sid_cid ON sid(cid_id);
CREATE INDEX IF NOT EXISTS idx_sid_company ON sid(sovereign_company_id);
CREATE INDEX IF NOT EXISTS idx_sid_status ON sid(status);
CREATE INDEX IF NOT EXISTS idx_sid_campaign ON sid(campaign_type);

-- ─────────────────────────────────────────────────────────────
-- MID — Message Delivery Record (Stage 3 CANONICAL)
-- One per message delivery attempt. Dumb — just ships and tracks.
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS mid (
  mid_id                TEXT PRIMARY KEY,    -- MID-{SID}-{SEQ}-{CHANNEL}
  sid_id                TEXT NOT NULL,
  cid_id                TEXT NOT NULL,
  sovereign_company_id  TEXT NOT NULL,
  sequence_num          INTEGER NOT NULL,    -- position in campaign (1, 2, 3...)
  channel               TEXT NOT NULL,       -- MG (Mailgun), HR (HeyReach)
  path_type             TEXT NOT NULL,       -- WARM, COLD
  recipient_email       TEXT,
  recipient_linkedin    TEXT,
  subject               TEXT,
  body_plain            TEXT,
  body_html             TEXT,
  delivery_status       TEXT NOT NULL DEFAULT 'queued',  -- queued, sent, delivered, opened, clicked, bounced, failed
  sent_at               TEXT,
  delivered_at          TEXT,
  opened_at             TEXT,
  clicked_at            TEXT,
  bounced_at            TEXT,
  webhook_payload       TEXT,               -- JSON — raw webhook response
  strike_count          INTEGER NOT NULL DEFAULT 0,
  created_at            TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at            TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_mid_sid ON mid(sid_id);
CREATE INDEX IF NOT EXISTS idx_mid_company ON mid(sovereign_company_id);
CREATE INDEX IF NOT EXISTS idx_mid_status ON mid(delivery_status);
CREATE INDEX IF NOT EXISTS idx_mid_channel ON mid(channel);

-- ─────────────────────────────────────────────────────────────
-- SUPPRESSION LIST — Learned shutoff valves
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS suppression (
  suppression_id        TEXT PRIMARY KEY,
  sovereign_company_id  TEXT,
  entity_type           TEXT NOT NULL,       -- company, email, linkedin
  entity_value          TEXT NOT NULL,       -- the blocked value
  reason                TEXT NOT NULL,       -- hard_bounce, strike_3, unsubscribed, never_contact
  created_at            TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_suppression_entity ON suppression(entity_type, entity_value);

-- ─────────────────────────────────────────────────────────────
-- EVENT — CET Append-Only Audit Trail (the meters)
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS event (
  event_id              TEXT PRIMARY KEY,
  sovereign_company_id  TEXT NOT NULL,
  cid_id                TEXT,
  sid_id                TEXT,
  mid_id                TEXT,
  event_type            TEXT NOT NULL,       -- signal_received, cid_compiled, sid_designed, mid_sent, mid_delivered, mid_bounced, mid_opened, mid_clicked, campaign_stopped, suppressed
  event_data            TEXT,               -- JSON — event-specific detail
  created_at            TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_event_company ON event(sovereign_company_id);
CREATE INDEX IF NOT EXISTS idx_event_cid ON event(cid_id);
CREATE INDEX IF NOT EXISTS idx_event_sid ON event(sid_id);
CREATE INDEX IF NOT EXISTS idx_event_mid ON event(mid_id);
CREATE INDEX IF NOT EXISTS idx_event_type ON event(event_type);

-- ─────────────────────────────────────────────────────────────
-- ERR0 — Error Table (the drain)
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS err0 (
  error_id              TEXT PRIMARY KEY,
  sovereign_company_id  TEXT,
  cid_id                TEXT,
  sid_id                TEXT,
  mid_id                TEXT,
  stage                 TEXT NOT NULL,       -- signal, gate, cid, sid, mid, webhook
  error_type            TEXT NOT NULL,
  error_message         TEXT NOT NULL,
  error_detail          TEXT,               -- JSON — full context
  strike_count          INTEGER DEFAULT 0,
  created_at            TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_err0_company ON err0(sovereign_company_id);
CREATE INDEX IF NOT EXISTS idx_err0_stage ON err0(stage);

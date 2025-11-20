-- BIT Scoring Database Tables
-- Barton Doctrine ID: 04.04.02.04.70000.###
-- Purpose: Convert events (signals) into numeric Buyer Intent Scores

-- ==============================================================
-- Table: bit_signal_weights
-- Purpose: Define weights for each signal type
-- ==============================================================
CREATE TABLE IF NOT EXISTS marketing.bit_signal_weights (
    weight_id SERIAL PRIMARY KEY,
    signal_type TEXT NOT NULL UNIQUE,
    weight INTEGER NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insert default weights
INSERT INTO marketing.bit_signal_weights (signal_type, weight, description) VALUES
    ('movement_hire', 50, 'Person hired at new company'),
    ('movement_exit', 30, 'Person left company'),
    ('movement_promotion', 70, 'Person promoted within company'),
    ('movement_transfer', 40, 'Person transferred roles'),
    ('email_open', 10, 'Email opened'),
    ('email_click', 25, 'Email link clicked'),
    ('email_reply', 60, 'Email replied to'),
    ('website_visit', 15, 'Company website visited'),
    ('content_download', 35, 'Whitepaper/content downloaded'),
    ('demo_request', 100, 'Demo request submitted'),
    ('pricing_page_view', 45, 'Pricing page viewed'),
    ('linkedin_engage', 20, 'LinkedIn post engagement'),
    ('enrichment_update', 5, 'Profile enriched with new data'),
    ('role_executive', 30, 'Executive-level role (CEO/CFO/CTO)'),
    ('role_director', 20, 'Director-level role'),
    ('role_manager', 10, 'Manager-level role'),
    ('company_size_large', 25, 'Company size 500+ employees'),
    ('company_size_medium', 15, 'Company size 50-500 employees'),
    ('industry_target', 20, 'Company in target industry')
ON CONFLICT (signal_type) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_signal_weights_type ON marketing.bit_signal_weights(signal_type);
CREATE INDEX IF NOT EXISTS idx_signal_weights_active ON marketing.bit_signal_weights(active);

COMMENT ON TABLE marketing.bit_signal_weights IS 'Signal type → weight mapping for BIT scoring';

-- ==============================================================
-- Table: bit_decay_rules
-- Purpose: Time-based decay factors for signals
-- ==============================================================
CREATE TABLE IF NOT EXISTS marketing.bit_decay_rules (
    decay_id SERIAL PRIMARY KEY,
    rule_name TEXT NOT NULL UNIQUE,
    days_threshold INTEGER NOT NULL,
    decay_factor NUMERIC(4,3) NOT NULL CHECK (decay_factor >= 0 AND decay_factor <= 1),
    applies_to TEXT[], -- NULL means applies to all signal types
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insert default decay rules
INSERT INTO marketing.bit_decay_rules (rule_name, days_threshold, decay_factor, description) VALUES
    ('fresh_0_7', 7, 1.000, 'Fresh signals (0-7 days): full weight'),
    ('recent_8_30', 30, 0.850, 'Recent signals (8-30 days): 85% weight'),
    ('moderate_31_90', 90, 0.650, 'Moderate age (31-90 days): 65% weight'),
    ('aged_91_180', 180, 0.400, 'Aged signals (91-180 days): 40% weight'),
    ('stale_181_365', 365, 0.200, 'Stale signals (181-365 days): 20% weight'),
    ('expired_365_plus', 9999, 0.050, 'Expired signals (365+ days): 5% weight')
ON CONFLICT (rule_name) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_decay_rules_name ON marketing.bit_decay_rules(rule_name);
CREATE INDEX IF NOT EXISTS idx_decay_rules_active ON marketing.bit_decay_rules(active);

COMMENT ON TABLE marketing.bit_decay_rules IS 'Time-based decay factors for signal aging';

-- ==============================================================
-- Table: bit_confidence_modifiers
-- Purpose: Confidence multipliers based on data source
-- ==============================================================
CREATE TABLE IF NOT EXISTS marketing.bit_confidence_modifiers (
    modifier_id SERIAL PRIMARY KEY,
    source TEXT NOT NULL UNIQUE,
    confidence_multiplier NUMERIC(4,3) NOT NULL CHECK (confidence_multiplier >= 0 AND confidence_multiplier <= 2),
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insert default confidence modifiers
INSERT INTO marketing.bit_confidence_modifiers (source, confidence_multiplier, description) VALUES
    ('manual', 1.200, 'Manual data entry (highest trust)'),
    ('peopledatalabs', 1.150, 'PeopleDataLabs (verified data)'),
    ('rocketreach', 1.100, 'RocketReach (high quality)'),
    ('clearbit', 1.050, 'Clearbit (good quality)'),
    ('talent_flow_movement', 1.100, 'Talent Flow detected movement'),
    ('email_tracking', 1.000, 'Email open/click tracking'),
    ('abacus', 0.950, 'Abacus.AI enrichment'),
    ('apify', 0.900, 'Apify scraping'),
    ('clay', 0.900, 'Clay enrichment'),
    ('firecrawl', 0.850, 'Firecrawl web scraping'),
    ('scraperapi', 0.800, 'ScraperAPI'),
    ('zenrows', 0.800, 'ZenRows'),
    ('scrapingbee', 0.750, 'ScrapingBee'),
    ('serpapi', 0.750, 'SerpAPI'),
    ('unknown', 0.700, 'Unknown source')
ON CONFLICT (source) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_confidence_modifiers_source ON marketing.bit_confidence_modifiers(source);
CREATE INDEX IF NOT EXISTS idx_confidence_modifiers_active ON marketing.bit_confidence_modifiers(active);

COMMENT ON TABLE marketing.bit_confidence_modifiers IS 'Data source → confidence multiplier mapping';

-- ==============================================================
-- Table: bit_trigger_thresholds
-- Purpose: Score thresholds that trigger actions
-- ==============================================================
CREATE TABLE IF NOT EXISTS marketing.bit_trigger_thresholds (
    threshold_id SERIAL PRIMARY KEY,
    trigger_level TEXT NOT NULL UNIQUE,
    min_score INTEGER NOT NULL,
    max_score INTEGER,
    action_type TEXT NOT NULL CHECK (action_type IN ('nurture', 'sdr_escalate', 'auto_meeting', 'watch', 'ignore')),
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insert default thresholds
INSERT INTO marketing.bit_trigger_thresholds (trigger_level, min_score, max_score, action_type, description) VALUES
    ('cold', 0, 49, 'ignore', 'No engagement, no action'),
    ('warm', 50, 99, 'watch', 'Monitor for additional signals'),
    ('engaged', 100, 199, 'nurture', 'Send targeted nurture content'),
    ('hot', 200, 299, 'sdr_escalate', 'Escalate to SDR for outreach'),
    ('burning', 300, NULL, 'auto_meeting', 'Auto-schedule meeting or urgent follow-up')
ON CONFLICT (trigger_level) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_trigger_thresholds_level ON marketing.bit_trigger_thresholds(trigger_level);
CREATE INDEX IF NOT EXISTS idx_trigger_thresholds_score ON marketing.bit_trigger_thresholds(min_score, max_score);
CREATE INDEX IF NOT EXISTS idx_trigger_thresholds_active ON marketing.bit_trigger_thresholds(active);

COMMENT ON TABLE marketing.bit_trigger_thresholds IS 'Score thresholds that trigger sales actions';

-- ==============================================================
-- Table: bit_score
-- Purpose: Computed BIT scores per person/company
-- ==============================================================
CREATE TABLE IF NOT EXISTS marketing.bit_score (
    score_id BIGSERIAL PRIMARY KEY,
    person_unique_id TEXT NOT NULL,
    company_unique_id TEXT NOT NULL,
    raw_score INTEGER NOT NULL DEFAULT 0,
    decayed_score INTEGER NOT NULL DEFAULT 0,
    score_tier TEXT NOT NULL CHECK (score_tier IN ('cold', 'warm', 'engaged', 'hot', 'burning')),
    last_signal_at TIMESTAMPTZ,
    signal_count INTEGER NOT NULL DEFAULT 0,
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    metadata JSONB,

    FOREIGN KEY (person_unique_id) REFERENCES marketing.people_master(unique_id),
    FOREIGN KEY (company_unique_id) REFERENCES marketing.company_master(company_unique_id),

    UNIQUE (person_unique_id, company_unique_id)
);

CREATE INDEX IF NOT EXISTS idx_bit_score_person ON marketing.bit_score(person_unique_id);
CREATE INDEX IF NOT EXISTS idx_bit_score_company ON marketing.bit_score(company_unique_id);
CREATE INDEX IF NOT EXISTS idx_bit_score_tier ON marketing.bit_score(score_tier);
CREATE INDEX IF NOT EXISTS idx_bit_score_decayed ON marketing.bit_score(decayed_score DESC);
CREATE INDEX IF NOT EXISTS idx_bit_score_computed ON marketing.bit_score(computed_at DESC);

COMMENT ON TABLE marketing.bit_score IS 'Computed BIT scores per person/company combination';
COMMENT ON COLUMN marketing.bit_score.raw_score IS 'Sum of all signal weights (no decay)';
COMMENT ON COLUMN marketing.bit_score.decayed_score IS 'Score after applying time decay';
COMMENT ON COLUMN marketing.bit_score.score_tier IS 'Tier based on thresholds (cold/warm/engaged/hot/burning)';

-- ==============================================================
-- Table: bit_signal (add processed flag if not exists)
-- Purpose: Track which signals have been scored
-- ==============================================================
ALTER TABLE marketing.bit_signal
ADD COLUMN IF NOT EXISTS scored BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS scored_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_bit_signal_scored ON marketing.bit_signal(scored);

-- ==============================================================
-- Table: outreach_log (if not exists)
-- Purpose: Log outreach actions triggered by BIT scores
-- ==============================================================
CREATE TABLE IF NOT EXISTS marketing.outreach_log (
    outreach_id BIGSERIAL PRIMARY KEY,
    person_unique_id TEXT NOT NULL,
    company_unique_id TEXT NOT NULL,
    action_type TEXT NOT NULL CHECK (action_type IN ('nurture', 'sdr_escalate', 'auto_meeting', 'watch')),
    bit_score INTEGER NOT NULL,
    score_tier TEXT NOT NULL,
    trigger_reason TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMPTZ,

    FOREIGN KEY (person_unique_id) REFERENCES marketing.people_master(unique_id),
    FOREIGN KEY (company_unique_id) REFERENCES marketing.company_master(company_unique_id)
);

CREATE INDEX IF NOT EXISTS idx_outreach_log_person ON marketing.outreach_log(person_unique_id);
CREATE INDEX IF NOT EXISTS idx_outreach_log_company ON marketing.outreach_log(company_unique_id);
CREATE INDEX IF NOT EXISTS idx_outreach_log_action ON marketing.outreach_log(action_type);
CREATE INDEX IF NOT EXISTS idx_outreach_log_processed ON marketing.outreach_log(processed);
CREATE INDEX IF NOT EXISTS idx_outreach_log_created ON marketing.outreach_log(created_at DESC);

COMMENT ON TABLE marketing.outreach_log IS 'Outreach actions triggered by BIT scores';

-- ==============================================================
-- Table: meeting_queue (if not exists)
-- Purpose: Queue for auto-meeting scheduling
-- ==============================================================
CREATE TABLE IF NOT EXISTS marketing.meeting_queue (
    meeting_id BIGSERIAL PRIMARY KEY,
    person_unique_id TEXT NOT NULL,
    company_unique_id TEXT NOT NULL,
    bit_score INTEGER NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'scheduled', 'completed', 'cancelled')),
    scheduled_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    FOREIGN KEY (person_unique_id) REFERENCES marketing.people_master(unique_id),
    FOREIGN KEY (company_unique_id) REFERENCES marketing.company_master(company_unique_id)
);

CREATE INDEX IF NOT EXISTS idx_meeting_queue_person ON marketing.meeting_queue(person_unique_id);
CREATE INDEX IF NOT EXISTS idx_meeting_queue_company ON marketing.meeting_queue(company_unique_id);
CREATE INDEX IF NOT EXISTS idx_meeting_queue_status ON marketing.meeting_queue(status);
CREATE INDEX IF NOT EXISTS idx_meeting_queue_priority ON marketing.meeting_queue(priority);
CREATE INDEX IF NOT EXISTS idx_meeting_queue_created ON marketing.meeting_queue(created_at DESC);

COMMENT ON TABLE marketing.meeting_queue IS 'Queue for high-score contacts requiring meetings';

-- ==============================================================
-- Function: Prevent double-scoring (idempotent writes)
-- ==============================================================
CREATE OR REPLACE FUNCTION marketing.mark_signal_scored()
RETURNS TRIGGER AS $$
BEGIN
    -- When bit_score is updated, mark source signals as scored
    UPDATE marketing.bit_signal
    SET scored = TRUE,
        scored_at = NOW()
    WHERE person_unique_id = NEW.person_unique_id
      AND company_unique_id = NEW.company_unique_id
      AND scored = FALSE;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_mark_signals_scored
AFTER INSERT OR UPDATE ON marketing.bit_score
FOR EACH ROW
EXECUTE FUNCTION marketing.mark_signal_scored();

COMMENT ON FUNCTION marketing.mark_signal_scored IS 'Auto-mark signals as scored to prevent double-scoring';

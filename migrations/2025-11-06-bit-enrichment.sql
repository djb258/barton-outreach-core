-- ═══════════════════════════════════════════════════════════════════════════
-- SVG-PLE Doctrine Alignment — BIT + Enrichment Infrastructure
-- ═══════════════════════════════════════════════════════════════════════════
-- Altitude: 10,000 ft (Execution Layer)
-- Doctrine: Barton / SVG-PLE / BIT-Axle
-- Owner: Data Automation / LOM
-- Generated: 2025-11-06
--
-- Purpose: Create Buyer Intent Tool (BIT) and Data Enrichment infrastructure
--          following the Perpetual Lead Engine (PLE) hub-spoke-axle architecture.
--
-- Architecture:
--   Hub: marketing.company_master + marketing.people_master
--   Spokes: intake, vault, enrichment logging
--   Axle: BIT signals, rules, and scoring engine
--
-- Components:
--   1. bit.rule_reference — Signal detection rules and weights
--   2. bit.events — Detected buying intent signals
--   3. bit.scores — Real-time company scoring view
--   4. marketing.data_enrichment_log — Enrichment tracking and ROI
--   5. Indexes and constraints for performance
--
-- Compatibility: PostgreSQL 15+ (Neon)
-- Idempotent: Yes (IF NOT EXISTS / IF EXISTS)
-- ═══════════════════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────────────────
-- 🎯 SECTION 1: BIT Schema Setup
-- ───────────────────────────────────────────────────────────────────────────

-- Create BIT schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS bit;

COMMENT ON SCHEMA bit IS 'Buyer Intent Tool (BIT) — Signal detection and scoring for the Perpetual Lead Engine';

-- ───────────────────────────────────────────────────────────────────────────
-- 📋 TABLE: bit.rule_reference
-- ───────────────────────────────────────────────────────────────────────────
-- Doctrine: Master catalog of BIT rules that detect buying intent signals.
--           Each rule has a weight that contributes to overall company score.
--           Rules are categorized by intent type (renewal, hiring, funding, growth).
--
-- Examples:
--   - renewal_window_120d: Company entering 120-day renewal window
--   - executive_movement: New C-level hire detected
--   - funding_round: Company announced funding
--   - tech_stack_expansion: New job postings for specific technologies
-- ───────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS bit.rule_reference (
    rule_id SERIAL PRIMARY KEY,
    rule_name TEXT NOT NULL UNIQUE,
    rule_description TEXT,
    weight INTEGER NOT NULL DEFAULT 10,
    category TEXT NOT NULL CHECK (category IN ('renewal', 'hiring', 'funding', 'growth', 'technology', 'executive', 'other')),
    is_active BOOLEAN NOT NULL DEFAULT true,
    detection_logic TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Metadata
    detection_frequency TEXT DEFAULT 'daily',
    confidence_threshold NUMERIC(3,2) DEFAULT 0.75,

    -- Constraints
    CONSTRAINT rule_reference_weight_positive CHECK (weight > 0),
    CONSTRAINT rule_reference_confidence_range CHECK (confidence_threshold >= 0 AND confidence_threshold <= 1)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_rule_reference_category ON bit.rule_reference(category);
CREATE INDEX IF NOT EXISTS idx_rule_reference_is_active ON bit.rule_reference(is_active);
CREATE INDEX IF NOT EXISTS idx_rule_reference_weight ON bit.rule_reference(weight DESC);

-- Comments
COMMENT ON TABLE bit.rule_reference IS 'BIT Rule Catalog — Defines signal detection rules with weights and categories for scoring';
COMMENT ON COLUMN bit.rule_reference.rule_name IS 'Unique identifier for the rule (e.g., renewal_window_120d, executive_movement)';
COMMENT ON COLUMN bit.rule_reference.weight IS 'Score contribution when rule triggers (higher = stronger intent signal)';
COMMENT ON COLUMN bit.rule_reference.category IS 'Intent category: renewal, hiring, funding, growth, technology, executive, other';
COMMENT ON COLUMN bit.rule_reference.confidence_threshold IS 'Minimum confidence score (0-1) required to trigger this rule';
COMMENT ON COLUMN bit.rule_reference.detection_logic IS 'Human-readable description of how this rule is detected';

-- Auto-update trigger for updated_at
DROP TRIGGER IF EXISTS trigger_rule_reference_updated_at ON bit.rule_reference;
CREATE TRIGGER trigger_rule_reference_updated_at
    BEFORE UPDATE ON bit.rule_reference
    FOR EACH ROW
    EXECUTE FUNCTION trigger_updated_at();

-- ───────────────────────────────────────────────────────────────────────────
-- 📋 TABLE: bit.events
-- ───────────────────────────────────────────────────────────────────────────
-- Doctrine: Detected buying intent signals for companies. Each event represents
--           a single signal detection (e.g., company entered renewal window,
--           new executive hired, funding announced). Events aggregate into scores.
--
-- Data Flow:
--   1. Signal detected by automated job or manual entry
--   2. Event created with reference to rule and company
--   3. Event processed and added to company score
--   4. Scores used to prioritize outreach campaigns
-- ───────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS bit.events (
    event_id BIGSERIAL PRIMARY KEY,
    company_unique_id TEXT NOT NULL,
    rule_id INTEGER NOT NULL,

    -- Event details
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_payload JSONB DEFAULT '{}',
    confidence_score NUMERIC(3,2),

    -- Scoring
    weight INTEGER NOT NULL,
    processed BOOLEAN NOT NULL DEFAULT false,
    processed_at TIMESTAMPTZ,

    -- Metadata
    detection_source TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Foreign keys
    CONSTRAINT fk_events_company
        FOREIGN KEY (company_unique_id)
        REFERENCES marketing.company_master(company_unique_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_events_rule
        FOREIGN KEY (rule_id)
        REFERENCES bit.rule_reference(rule_id)
        ON DELETE RESTRICT,

    -- Constraints
    CONSTRAINT events_confidence_range CHECK (confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)),
    CONSTRAINT events_weight_positive CHECK (weight > 0)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_events_company_id ON bit.events(company_unique_id);
CREATE INDEX IF NOT EXISTS idx_events_rule_id ON bit.events(rule_id);
CREATE INDEX IF NOT EXISTS idx_events_detected_at ON bit.events(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_processed ON bit.events(processed);
CREATE INDEX IF NOT EXISTS idx_events_weight ON bit.events(weight DESC);

-- Composite index for scoring queries
CREATE INDEX IF NOT EXISTS idx_events_company_processed ON bit.events(company_unique_id, processed);

-- GIN index for JSONB payload searches
CREATE INDEX IF NOT EXISTS idx_events_payload ON bit.events USING GIN(event_payload);

-- Comments
COMMENT ON TABLE bit.events IS 'BIT Events — Detected buying intent signals linked to companies and rules';
COMMENT ON COLUMN bit.events.company_unique_id IS 'Reference to marketing.company_master Barton ID (04.04.01)';
COMMENT ON COLUMN bit.events.rule_id IS 'Reference to bit.rule_reference that triggered this event';
COMMENT ON COLUMN bit.events.event_payload IS 'JSONB payload with event-specific data (e.g., executive name, funding amount)';
COMMENT ON COLUMN bit.events.confidence_score IS 'Detection confidence 0-1 (higher = more certain)';
COMMENT ON COLUMN bit.events.weight IS 'Score contribution copied from rule at detection time';
COMMENT ON COLUMN bit.events.processed IS 'Whether this event has been included in scoring and campaign logic';

-- ───────────────────────────────────────────────────────────────────────────
-- 📊 VIEW: bit.scores
-- ───────────────────────────────────────────────────────────────────────────
-- Doctrine: Real-time company scoring based on aggregated BIT events.
--           Scores are calculated from weighted sum of events in the last 90 days.
--           Companies are tiered as hot/warm/cold based on score thresholds.
--
-- Scoring Logic:
--   - Hot (score >= 50): High intent, immediate outreach
--   - Warm (score 25-49): Medium intent, monitor and engage
--   - Cold (score < 25): Low intent, nurture campaigns
--   - Unscored (no events): No signals detected
--
-- Integration:
--   - Used by marketing campaigns to prioritize outreach
--   - Feeds Grafana BIT Heatmap dashboard
--   - Drives PLE re-engagement cycles
-- ───────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW bit.scores AS
SELECT
    cm.company_unique_id,
    cm.company_name,
    cm.website_url,
    cm.industry,

    -- Scoring metrics
    COALESCE(SUM(e.weight), 0) AS total_score,
    COUNT(e.event_id) AS signal_count,
    MAX(e.detected_at) AS last_signal_at,

    -- Score tier classification
    CASE
        WHEN COALESCE(SUM(e.weight), 0) >= 50 THEN 'hot'
        WHEN COALESCE(SUM(e.weight), 0) >= 25 THEN 'warm'
        WHEN COALESCE(SUM(e.weight), 0) > 0 THEN 'cold'
        ELSE 'unscored'
    END AS score_tier,

    -- Event breakdown by category
    COUNT(e.event_id) FILTER (WHERE rr.category = 'renewal') AS renewal_signals,
    COUNT(e.event_id) FILTER (WHERE rr.category = 'hiring') AS hiring_signals,
    COUNT(e.event_id) FILTER (WHERE rr.category = 'funding') AS funding_signals,
    COUNT(e.event_id) FILTER (WHERE rr.category = 'growth') AS growth_signals,
    COUNT(e.event_id) FILTER (WHERE rr.category = 'executive') AS executive_signals,

    -- Metadata
    NOW() AS calculated_at

FROM marketing.company_master cm
LEFT JOIN bit.events e
    ON cm.company_unique_id = e.company_unique_id
    AND e.detected_at >= NOW() - INTERVAL '90 days'
    AND e.processed = true
LEFT JOIN bit.rule_reference rr
    ON e.rule_id = rr.rule_id

GROUP BY
    cm.company_unique_id,
    cm.company_name,
    cm.website_url,
    cm.industry

ORDER BY total_score DESC, last_signal_at DESC;

-- Comments
COMMENT ON VIEW bit.scores IS 'BIT Scoring View — Real-time company scores based on weighted events from last 90 days';

-- ───────────────────────────────────────────────────────────────────────────
-- 🔧 SECTION 2: Data Enrichment Infrastructure
-- ───────────────────────────────────────────────────────────────────────────

-- ───────────────────────────────────────────────────────────────────────────
-- 📋 TABLE: marketing.data_enrichment_log
-- ───────────────────────────────────────────────────────────────────────────
-- Doctrine: Comprehensive tracking of all data enrichment operations.
--           Tracks which agents (Apify, Apollo, LinkedIn) enriched which companies,
--           with cost, quality, and ROI metrics.
--
-- Use Cases:
--   1. ROI Analysis: Cost per successful enrichment by agent
--   2. Quality Tracking: Data quality scores and validation
--   3. Agent Performance: Success rates and error patterns
--   4. Movement Detection: Executive changes triggering BIT signals
--   5. Re-enrichment Scheduling: TTL-based refresh logic
--
-- Integration with BIT:
--   - movement_detected = true triggers executive_movement rule in BIT
--   - Quality scores contribute to confidence scores in bit.events
-- ───────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS marketing.data_enrichment_log (
    enrichment_id BIGSERIAL PRIMARY KEY,
    company_unique_id TEXT NOT NULL,

    -- Agent and operation details
    agent_name TEXT NOT NULL,
    enrichment_type TEXT NOT NULL CHECK (enrichment_type IN ('profile', 'email', 'linkedin', 'news', 'social', 'executive', 'company_data', 'contact_discovery')),

    -- Status and timing
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'success', 'failed', 'timeout', 'rate_limited')),
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER GENERATED ALWAYS AS (EXTRACT(EPOCH FROM (completed_at - attempted_at))::INTEGER) STORED,

    -- Quality and validation
    data_quality_score NUMERIC(5,2),
    records_found INTEGER DEFAULT 0,
    records_validated INTEGER DEFAULT 0,
    validation_pass_rate NUMERIC(5,2) GENERATED ALWAYS AS (
        CASE
            WHEN records_found > 0 THEN (records_validated::NUMERIC / records_found::NUMERIC) * 100
            ELSE NULL
        END
    ) STORED,

    -- Cost tracking
    cost_credits NUMERIC(10,4) DEFAULT 0,
    cost_usd NUMERIC(10,4),

    -- Movement detection (for BIT integration)
    movement_detected BOOLEAN DEFAULT false,
    movement_type TEXT CHECK (movement_type IS NULL OR movement_type IN ('executive_hire', 'executive_departure', 'title_change', 'company_change')),
    movement_details JSONB,

    -- Results and errors
    result_data JSONB DEFAULT '{}',
    error_message TEXT,
    error_code TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Metadata
    api_request_id TEXT,
    actor_run_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Foreign key
    CONSTRAINT fk_enrichment_company
        FOREIGN KEY (company_unique_id)
        REFERENCES marketing.company_master(company_unique_id)
        ON DELETE CASCADE,

    -- Constraints
    CONSTRAINT enrichment_quality_range CHECK (data_quality_score IS NULL OR (data_quality_score >= 0 AND data_quality_score <= 100)),
    CONSTRAINT enrichment_cost_positive CHECK (cost_credits >= 0),
    CONSTRAINT enrichment_records_positive CHECK (records_found >= 0 AND records_validated >= 0),
    CONSTRAINT enrichment_validated_not_exceed_found CHECK (records_validated <= records_found)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_enrichment_company_id ON marketing.data_enrichment_log(company_unique_id);
CREATE INDEX IF NOT EXISTS idx_enrichment_agent_name ON marketing.data_enrichment_log(agent_name);
CREATE INDEX IF NOT EXISTS idx_enrichment_type ON marketing.data_enrichment_log(enrichment_type);
CREATE INDEX IF NOT EXISTS idx_enrichment_status ON marketing.data_enrichment_log(status);
CREATE INDEX IF NOT EXISTS idx_enrichment_attempted_at ON marketing.data_enrichment_log(attempted_at DESC);
CREATE INDEX IF NOT EXISTS idx_enrichment_movement_detected ON marketing.data_enrichment_log(movement_detected) WHERE movement_detected = true;

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_enrichment_agent_status ON marketing.data_enrichment_log(agent_name, status);
CREATE INDEX IF NOT EXISTS idx_enrichment_company_type ON marketing.data_enrichment_log(company_unique_id, enrichment_type);

-- GIN index for JSONB result searches
CREATE INDEX IF NOT EXISTS idx_enrichment_result_data ON marketing.data_enrichment_log USING GIN(result_data);
CREATE INDEX IF NOT EXISTS idx_enrichment_movement_details ON marketing.data_enrichment_log USING GIN(movement_details);

-- Comments
COMMENT ON TABLE marketing.data_enrichment_log IS 'Data Enrichment Tracking — Comprehensive log of all enrichment operations with cost, quality, and ROI metrics';
COMMENT ON COLUMN marketing.data_enrichment_log.agent_name IS 'Enrichment agent identifier (Apify, Apollo, LinkedIn, MillionVerifier, etc.)';
COMMENT ON COLUMN marketing.data_enrichment_log.enrichment_type IS 'Type of data enriched: profile, email, linkedin, news, social, executive, company_data, contact_discovery';
COMMENT ON COLUMN marketing.data_enrichment_log.data_quality_score IS 'Quality score 0-100 based on completeness, accuracy, and validation';
COMMENT ON COLUMN marketing.data_enrichment_log.cost_credits IS 'Cost in agent-specific credits (Apify compute units, Apollo credits, etc.)';
COMMENT ON COLUMN marketing.data_enrichment_log.cost_usd IS 'Estimated cost in USD for ROI calculations';
COMMENT ON COLUMN marketing.data_enrichment_log.movement_detected IS 'TRUE if executive movement detected (triggers BIT signal)';
COMMENT ON COLUMN marketing.data_enrichment_log.movement_type IS 'Type of movement: executive_hire, executive_departure, title_change, company_change';
COMMENT ON COLUMN marketing.data_enrichment_log.validation_pass_rate IS 'Percentage of found records that passed validation (auto-calculated)';
COMMENT ON COLUMN marketing.data_enrichment_log.actor_run_id IS 'Reference to Apify actor run for result retrieval';

-- Auto-update trigger for updated_at
DROP TRIGGER IF EXISTS trigger_enrichment_log_updated_at ON marketing.data_enrichment_log;
CREATE TRIGGER trigger_enrichment_log_updated_at
    BEFORE UPDATE ON marketing.data_enrichment_log
    FOR EACH ROW
    EXECUTE FUNCTION trigger_updated_at();

-- ───────────────────────────────────────────────────────────────────────────
-- 📊 VIEW: marketing.data_enrichment_summary
-- ───────────────────────────────────────────────────────────────────────────
-- Doctrine: Enrichment ROI and performance summary by agent and type.
--           Used for Grafana "Enrichment ROI" panel and cost optimization.
-- ───────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW marketing.data_enrichment_summary AS
SELECT
    agent_name,
    enrichment_type,

    -- Volume metrics
    COUNT(*) AS total_attempts,
    COUNT(*) FILTER (WHERE status = 'success') AS successful_attempts,
    COUNT(*) FILTER (WHERE status = 'failed') AS failed_attempts,
    COUNT(*) FILTER (WHERE status = 'timeout') AS timeout_attempts,
    COUNT(*) FILTER (WHERE status = 'rate_limited') AS rate_limited_attempts,

    -- Success rate
    ROUND(
        (COUNT(*) FILTER (WHERE status = 'success')::NUMERIC / NULLIF(COUNT(*), 0)::NUMERIC) * 100,
        2
    ) AS success_rate_pct,

    -- Cost metrics
    SUM(cost_credits) AS total_cost_credits,
    SUM(cost_usd) AS total_cost_usd,
    AVG(cost_credits) FILTER (WHERE status = 'success') AS avg_cost_per_success_credits,
    AVG(cost_usd) FILTER (WHERE status = 'success') AS avg_cost_per_success_usd,

    -- Quality metrics
    AVG(data_quality_score) FILTER (WHERE status = 'success') AS avg_quality_score,
    SUM(records_found) AS total_records_found,
    SUM(records_validated) AS total_records_validated,
    ROUND(
        (SUM(records_validated)::NUMERIC / NULLIF(SUM(records_found), 0)::NUMERIC) * 100,
        2
    ) AS overall_validation_rate_pct,

    -- Movement detection
    COUNT(*) FILTER (WHERE movement_detected = true) AS movements_detected,

    -- Performance metrics
    AVG(duration_seconds) FILTER (WHERE status = 'success') AS avg_duration_seconds,
    SUM(retry_count) AS total_retries,

    -- Time range
    MIN(attempted_at) AS first_attempt,
    MAX(attempted_at) AS last_attempt,

    -- ROI calculation (records validated per dollar)
    CASE
        WHEN SUM(cost_usd) > 0 THEN
            ROUND(SUM(records_validated)::NUMERIC / SUM(cost_usd)::NUMERIC, 2)
        ELSE NULL
    END AS records_per_dollar,

    NOW() AS calculated_at

FROM marketing.data_enrichment_log

GROUP BY agent_name, enrichment_type

ORDER BY total_attempts DESC, success_rate_pct DESC;

COMMENT ON VIEW marketing.data_enrichment_summary IS 'Enrichment ROI Summary — Performance and cost metrics by agent and enrichment type';

-- ───────────────────────────────────────────────────────────────────────────
-- 🔗 SECTION 3: Integration Functions
-- ───────────────────────────────────────────────────────────────────────────

-- ───────────────────────────────────────────────────────────────────────────
-- 🔧 FUNCTION: bit.trigger_movement_event()
-- ───────────────────────────────────────────────────────────────────────────
-- Doctrine: Automatically create BIT event when executive movement is detected
--           during data enrichment. Bridges enrichment log with BIT scoring.
--
-- Trigger Logic:
--   1. When data_enrichment_log.movement_detected changes to TRUE
--   2. Look up "executive_movement" rule from bit.rule_reference
--   3. Create new event in bit.events
--   4. Event contributes to company score in bit.scores view
-- ───────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION bit.trigger_movement_event()
RETURNS TRIGGER AS $$
DECLARE
    v_rule_id INTEGER;
    v_weight INTEGER;
BEGIN
    -- Only trigger if movement was just detected
    IF NEW.movement_detected = true AND (OLD.movement_detected IS NULL OR OLD.movement_detected = false) THEN

        -- Get the executive_movement rule
        SELECT rule_id, weight
        INTO v_rule_id, v_weight
        FROM bit.rule_reference
        WHERE rule_name = 'executive_movement'
          AND is_active = true
        LIMIT 1;

        -- Create BIT event if rule exists
        IF v_rule_id IS NOT NULL THEN
            INSERT INTO bit.events (
                company_unique_id,
                rule_id,
                weight,
                confidence_score,
                event_payload,
                detection_source,
                processed
            ) VALUES (
                NEW.company_unique_id,
                v_rule_id,
                v_weight,
                NEW.data_quality_score / 100.0, -- Convert 0-100 to 0-1
                jsonb_build_object(
                    'movement_type', NEW.movement_type,
                    'movement_details', NEW.movement_details,
                    'enrichment_id', NEW.enrichment_id,
                    'agent_name', NEW.agent_name,
                    'detected_at', NEW.completed_at
                ),
                'data_enrichment_log',
                false -- Will be processed by scoring job
            );
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION bit.trigger_movement_event() IS 'Auto-create BIT event when executive movement detected in enrichment log';

-- Create trigger on enrichment log
DROP TRIGGER IF EXISTS trigger_enrichment_movement_to_bit ON marketing.data_enrichment_log;
CREATE TRIGGER trigger_enrichment_movement_to_bit
    AFTER INSERT OR UPDATE OF movement_detected
    ON marketing.data_enrichment_log
    FOR EACH ROW
    EXECUTE FUNCTION bit.trigger_movement_event();

-- ───────────────────────────────────────────────────────────────────────────
-- 🌱 SECTION 4: Seed Data
-- ───────────────────────────────────────────────────────────────────────────

-- Seed BIT rules with common intent signals
INSERT INTO bit.rule_reference (rule_name, rule_description, weight, category, detection_logic, is_active)
VALUES
    ('renewal_window_120d', 'Company entering 120-day renewal window', 50, 'renewal', 'Triggered when current date is within 120 days of company.renewal_month', true),
    ('renewal_window_90d', 'Company entering 90-day renewal window', 60, 'renewal', 'Triggered when current date is within 90 days of company.renewal_month', true),
    ('renewal_window_60d', 'Company entering 60-day renewal window', 70, 'renewal', 'Triggered when current date is within 60 days of company.renewal_month', true),
    ('renewal_window_30d', 'Company entering 30-day renewal window', 80, 'renewal', 'Triggered when current date is within 30 days of company.renewal_month', true),
    ('executive_movement', 'New C-level executive hired or departed', 40, 'executive', 'Detected via LinkedIn enrichment when title changes to C-level', true),
    ('executive_hire_ceo', 'New CEO hired', 50, 'executive', 'Detected when new CEO appears in company data', true),
    ('executive_hire_cfo', 'New CFO hired', 45, 'executive', 'Detected when new CFO appears in company data', true),
    ('funding_announced', 'Company announced funding round', 60, 'funding', 'Detected via news scraping or company intelligence', true),
    ('job_posting_spike', 'Significant increase in job postings', 35, 'hiring', 'Detected when company job postings increase >50% over 30 days', true),
    ('tech_stack_expansion', 'Company hiring for new technologies', 30, 'technology', 'Detected via job posting analysis for new tech keywords', true),
    ('acquisition_announced', 'Company announced acquisition', 55, 'growth', 'Detected via news scraping', true),
    ('office_expansion', 'Company opened new office location', 25, 'growth', 'Detected via company data updates', true),
    ('website_redesign', 'Company launched new website', 20, 'technology', 'Detected via website monitoring', true),
    ('social_engagement_spike', 'Increased social media activity', 15, 'other', 'Detected via social media API monitoring', true),
    ('press_coverage_positive', 'Positive press coverage detected', 25, 'other', 'Detected via news sentiment analysis', true)
ON CONFLICT (rule_name) DO NOTHING;

-- ───────────────────────────────────────────────────────────────────────────
-- ✅ VERIFICATION QUERIES
-- ───────────────────────────────────────────────────────────────────────────

-- Run these queries to verify the migration succeeded:

-- 1. Verify BIT tables exist
-- SELECT schemaname, tablename FROM pg_tables WHERE schemaname = 'bit' ORDER BY tablename;

-- 2. Verify rule count
-- SELECT COUNT(*) as rule_count FROM bit.rule_reference;

-- 3. Verify enrichment log table
-- SELECT COUNT(*) as column_count FROM information_schema.columns WHERE table_schema = 'marketing' AND table_name = 'data_enrichment_log';

-- 4. Test bit.scores view
-- SELECT COUNT(*) as company_count FROM bit.scores;

-- 5. Test enrichment summary view
-- SELECT * FROM marketing.data_enrichment_summary LIMIT 1;

-- ═══════════════════════════════════════════════════════════════════════════
-- END OF MIGRATION
-- ═══════════════════════════════════════════════════════════════════════════
-- Generated: 2025-11-06
-- Doctrine: SVG-PLE / BIT-Axle
-- Status: Production Ready
-- ═══════════════════════════════════════════════════════════════════════════

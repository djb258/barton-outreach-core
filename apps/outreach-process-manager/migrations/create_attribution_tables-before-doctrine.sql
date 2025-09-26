/**
 * Step 5 Closed-Loop Attribution Tables - Barton Doctrine Pipeline
 *
 * This creates the attribution tracking system that captures CRM outcomes
 * and feeds them back into PLE (Perpetual Lead Engine) and BIT (Buyer Intent Trigger)
 * for continuous learning and improvement.
 *
 * Barton Doctrine Rules:
 * - Attribution outcomes must preserve all Barton IDs for traceability
 * - All attribution events must be audited with before/after values
 * - Attribution data feeds back into PLE scoring and BIT signal weights
 * - MCP-only execution, no direct database writes
 */

-- Main Attribution Table
CREATE TABLE IF NOT EXISTS marketing.closed_loop_attribution (
    id SERIAL PRIMARY KEY,

    -- Barton Doctrine IDs (preserved from intake → master → campaign → attribution)
    company_unique_id TEXT NOT NULL,
    person_unique_id TEXT, -- optional if attribution is contact-level
    company_slot_unique_id TEXT,

    -- Campaign/Source Tracking
    campaign_id TEXT,
    source_campaign TEXT,
    touchpoint_sequence TEXT[], -- array of touchpoints that led to outcome

    -- Outcome Details
    crm_system TEXT NOT NULL CHECK (crm_system IN ('Salesforce', 'HubSpot', 'Pipedrive', 'Zoho', 'Other')),
    crm_record_id TEXT NOT NULL,
    crm_opportunity_id TEXT, -- specific opportunity/deal ID
    outcome TEXT NOT NULL CHECK (outcome IN ('closed_won', 'closed_lost', 'nurture', 'churn', 'qualified', 'disqualified')),
    outcome_reason TEXT,
    revenue_amount NUMERIC(12,2),
    expected_close_date TIMESTAMPTZ,
    actual_close_date TIMESTAMPTZ,

    -- Sales Process Metrics
    sales_cycle_days INTEGER,
    touchpoints_to_close INTEGER,
    deal_stage_at_attribution TEXT,
    lost_to_competitor TEXT,

    -- Attribution Context
    attribution_model TEXT DEFAULT 'first_touch', -- first_touch, last_touch, multi_touch
    attribution_confidence NUMERIC(3,2) DEFAULT 1.0, -- 0.0 to 1.0
    data_source TEXT DEFAULT 'crm_webhook',

    -- Doctrine Metadata
    altitude INTEGER DEFAULT 10000,
    process_id TEXT DEFAULT 'step_5_attribution',
    session_id TEXT,
    batch_id TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT attribution_barton_id_format
        CHECK (company_unique_id ~ '^04\.04\.01\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'),
    CONSTRAINT attribution_person_id_format
        CHECK (person_unique_id IS NULL OR person_unique_id ~ '^04\.04\.02\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'),
    CONSTRAINT attribution_slot_id_format
        CHECK (company_slot_unique_id IS NULL OR company_slot_unique_id ~ '^04\.04\.05\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'),
    CONSTRAINT attribution_revenue_positive
        CHECK (revenue_amount IS NULL OR revenue_amount >= 0),
    CONSTRAINT attribution_confidence_range
        CHECK (attribution_confidence >= 0.0 AND attribution_confidence <= 1.0)
);

-- Attribution Audit Log Table
CREATE TABLE IF NOT EXISTS marketing.attribution_audit_log (
    id SERIAL PRIMARY KEY,

    -- Attribution Record Reference
    attribution_id INTEGER REFERENCES marketing.closed_loop_attribution(id),

    -- Barton IDs for cross-reference
    company_unique_id TEXT NOT NULL,
    person_unique_id TEXT,

    -- Audit Details
    action TEXT NOT NULL CHECK (action IN ('create', 'update', 'delete', 'ple_update', 'bit_update')),
    status TEXT NOT NULL CHECK (status IN ('success', 'failed', 'partial')),
    source TEXT NOT NULL,

    -- Change Tracking
    previous_values JSONB,
    new_values JSONB,
    changed_fields TEXT[],

    -- Impact Tracking
    ple_score_impact JSONB, -- how this affected PLE scoring
    bit_signal_impact JSONB, -- how this affected BIT signals

    -- Metadata
    altitude INTEGER DEFAULT 10000,
    process_id TEXT DEFAULT 'step_5_attribution',
    session_id TEXT,
    batch_id TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- PLE Lead Scoring History (enhanced with attribution outcomes)
CREATE TABLE IF NOT EXISTS marketing.ple_lead_scoring_history (
    id SERIAL PRIMARY KEY,

    -- Record Identifiers
    company_unique_id TEXT,
    person_unique_id TEXT,

    -- Scoring Details
    model_version TEXT NOT NULL,
    score_before NUMERIC(5,2),
    score_after NUMERIC(5,2),
    score_factors JSONB, -- breakdown of scoring factors

    -- Attribution Impact
    attribution_outcome TEXT, -- what actual outcome occurred
    attribution_revenue NUMERIC(12,2),
    prediction_accuracy NUMERIC(5,2), -- how accurate was the original prediction

    -- Learning Metrics
    feature_weights_before JSONB,
    feature_weights_after JSONB,
    model_confidence NUMERIC(3,2),

    -- Metadata
    updated_by TEXT DEFAULT 'attribution_feedback',
    altitude INTEGER DEFAULT 10000,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- BIT Signal Performance (enhanced with attribution outcomes)
CREATE TABLE IF NOT EXISTS marketing.bit_signal_performance (
    id SERIAL PRIMARY KEY,

    -- Signal Details
    signal_type TEXT NOT NULL, -- 'funding_news', 'hiring_surge', 'tech_adoption', etc.
    signal_source TEXT NOT NULL,
    company_unique_id TEXT NOT NULL,

    -- Signal Metrics
    signal_strength NUMERIC(3,2), -- 0.0 to 1.0
    signal_timestamp TIMESTAMPTZ,

    -- Attribution Correlation
    attribution_outcome TEXT,
    attribution_revenue NUMERIC(12,2),
    correlation_strength NUMERIC(3,2), -- how well did this signal predict the outcome

    -- Weight Adjustments
    weight_before NUMERIC(5,4),
    weight_after NUMERIC(5,4),
    weight_adjustment_reason TEXT,

    -- Performance Tracking
    true_positive_rate NUMERIC(5,4),
    false_positive_rate NUMERIC(5,4),
    precision_score NUMERIC(5,4),
    recall_score NUMERIC(5,4),

    -- Metadata
    model_version TEXT,
    updated_by TEXT DEFAULT 'attribution_feedback',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_attribution_company
    ON marketing.closed_loop_attribution(company_unique_id);

CREATE INDEX IF NOT EXISTS idx_attribution_person
    ON marketing.closed_loop_attribution(person_unique_id);

CREATE INDEX IF NOT EXISTS idx_attribution_outcome
    ON marketing.closed_loop_attribution(outcome);

CREATE INDEX IF NOT EXISTS idx_attribution_crm_system
    ON marketing.closed_loop_attribution(crm_system);

CREATE INDEX IF NOT EXISTS idx_attribution_close_date
    ON marketing.closed_loop_attribution(actual_close_date);

CREATE INDEX IF NOT EXISTS idx_attribution_revenue
    ON marketing.closed_loop_attribution(revenue_amount);

CREATE INDEX IF NOT EXISTS idx_attribution_audit_company
    ON marketing.attribution_audit_log(company_unique_id);

CREATE INDEX IF NOT EXISTS idx_attribution_audit_action
    ON marketing.attribution_audit_log(action);

CREATE INDEX IF NOT EXISTS idx_attribution_audit_created
    ON marketing.attribution_audit_log(created_at);

CREATE INDEX IF NOT EXISTS idx_ple_history_company
    ON marketing.ple_lead_scoring_history(company_unique_id);

CREATE INDEX IF NOT EXISTS idx_ple_history_person
    ON marketing.ple_lead_scoring_history(person_unique_id);

CREATE INDEX IF NOT EXISTS idx_ple_history_outcome
    ON marketing.ple_lead_scoring_history(attribution_outcome);

CREATE INDEX IF NOT EXISTS idx_bit_performance_signal
    ON marketing.bit_signal_performance(signal_type);

CREATE INDEX IF NOT EXISTS idx_bit_performance_company
    ON marketing.bit_signal_performance(company_unique_id);

CREATE INDEX IF NOT EXISTS idx_bit_performance_outcome
    ON marketing.bit_signal_performance(attribution_outcome);

-- Comments for documentation
COMMENT ON TABLE marketing.closed_loop_attribution IS 'Step 5: Closed-loop attribution tracking for CRM outcomes feeding back to PLE and BIT systems';
COMMENT ON COLUMN marketing.closed_loop_attribution.company_unique_id IS 'Barton ID linking back to company_raw_intake → company_master';
COMMENT ON COLUMN marketing.closed_loop_attribution.person_unique_id IS 'Barton ID linking back to people_raw_intake → people_master';
COMMENT ON COLUMN marketing.closed_loop_attribution.touchpoint_sequence IS 'Array of marketing touchpoints that led to this outcome';
COMMENT ON COLUMN marketing.closed_loop_attribution.attribution_confidence IS 'Confidence score (0.0-1.0) for attribution accuracy';

COMMENT ON TABLE marketing.attribution_audit_log IS 'Audit trail for all attribution events and their impact on PLE/BIT systems';
COMMENT ON COLUMN marketing.attribution_audit_log.ple_score_impact IS 'JSON describing how this attribution affected PLE lead scoring';
COMMENT ON COLUMN marketing.attribution_audit_log.bit_signal_impact IS 'JSON describing how this attribution affected BIT signal weights';

COMMENT ON TABLE marketing.ple_lead_scoring_history IS 'Historical record of PLE scoring changes based on attribution outcomes';
COMMENT ON COLUMN marketing.ple_lead_scoring_history.prediction_accuracy IS 'How accurate was the original PLE prediction vs actual outcome';

COMMENT ON TABLE marketing.bit_signal_performance IS 'Performance tracking for BIT signals based on actual attribution outcomes';
COMMENT ON COLUMN marketing.bit_signal_performance.correlation_strength IS 'How strongly this signal correlated with the actual outcome';
-- ─────────────────────────────────────────────
-- 📁 CTB Classification Metadata
-- ─────────────────────────────────────────────
-- CTB Branch: data/migrations
-- Barton ID: 05.01.02
-- Unique ID: CTB-C881105E
-- Blueprint Hash:
-- Last Updated: 2025-10-23
-- Enforcement: HEIR
-- ─────────────────────────────────────────────

-- Step 8: Lead Scoring + Trigger Optimization - Database Schema
-- Barton Doctrine Scoring and Signal Weight Tables

-- Ensure marketing schema exists
CREATE SCHEMA IF NOT EXISTS marketing;

-- PLE Lead Scoring table with version-locked models
CREATE TABLE IF NOT EXISTS marketing.ple_lead_scoring (
    person_unique_id TEXT PRIMARY KEY,
    company_unique_id TEXT NOT NULL,
    score NUMERIC NOT NULL CHECK (score >= 0 AND score <= 100),

    -- Detailed score breakdown for transparency
    score_breakdown JSONB NOT NULL,

    -- Model versioning for auditability
    model_version TEXT NOT NULL,
    model_name TEXT DEFAULT 'ple_standard',

    -- Scoring factors
    firmographics_score NUMERIC,
    engagement_score NUMERIC,
    intent_score NUMERIC,
    attribution_score NUMERIC,

    -- Metadata
    last_scored_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Foreign keys
    FOREIGN KEY (person_unique_id) REFERENCES marketing.people_master(unique_id),
    FOREIGN KEY (company_unique_id) REFERENCES marketing.company_master(unique_id)
);

-- BIT Signal Weights table for dynamic optimization
CREATE TABLE IF NOT EXISTS marketing.bit_signal_weights (
    signal_name TEXT PRIMARY KEY,
    weight NUMERIC NOT NULL CHECK (weight >= 0 AND weight <= 100),

    -- Signal metadata
    signal_category TEXT CHECK (signal_category IN (
        'funding', 'hiring', 'technology', 'news',
        'engagement', 'competitor', 'regulatory', 'financial'
    )),
    signal_description TEXT,

    -- Model versioning
    model_version TEXT NOT NULL,

    -- Performance metrics for optimization
    effectiveness_score NUMERIC DEFAULT 50, -- 0-100 scale
    conversion_rate NUMERIC, -- % of signals that led to opportunity
    attribution_count INTEGER DEFAULT 0, -- Number of closed-won deals attributed

    -- Timestamps
    last_optimized TIMESTAMPTZ,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Scoring Model Versions table for complete auditability
CREATE TABLE IF NOT EXISTS marketing.scoring_model_versions (
    id SERIAL PRIMARY KEY,
    model_type TEXT CHECK (model_type IN ('PLE', 'BIT')),
    version TEXT NOT NULL,
    model_config JSONB NOT NULL, -- Complete model configuration

    -- Performance metrics
    avg_score NUMERIC,
    score_distribution JSONB,
    accuracy_rate NUMERIC,

    -- Attribution feedback
    closed_won_correlation NUMERIC,
    closed_lost_correlation NUMERIC,

    -- Status
    is_active BOOLEAN DEFAULT false,
    activated_at TIMESTAMPTZ,
    deactivated_at TIMESTAMPTZ,

    -- Metadata
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT,

    UNIQUE(model_type, version)
);

-- Scoring History table for tracking changes over time
CREATE TABLE IF NOT EXISTS marketing.scoring_history (
    id SERIAL PRIMARY KEY,
    person_unique_id TEXT NOT NULL,
    company_unique_id TEXT NOT NULL,

    -- Score snapshot
    score NUMERIC NOT NULL,
    previous_score NUMERIC,
    score_change NUMERIC,

    -- Model details
    model_version TEXT NOT NULL,
    score_breakdown JSONB,

    -- Trigger for score change
    trigger_event TEXT,
    trigger_details JSONB,

    -- Timestamp
    scored_at TIMESTAMPTZ DEFAULT NOW(),

    FOREIGN KEY (person_unique_id) REFERENCES marketing.people_master(unique_id)
);

-- BIT Signal Events table for tracking actual signals
CREATE TABLE IF NOT EXISTS marketing.bit_signal_events (
    id SERIAL PRIMARY KEY,
    signal_name TEXT NOT NULL,
    company_unique_id TEXT,
    person_unique_id TEXT,

    -- Signal details
    signal_strength NUMERIC DEFAULT 50,
    signal_data JSONB,
    source TEXT,

    -- Processing status
    processed BOOLEAN DEFAULT false,
    campaign_triggered BOOLEAN DEFAULT false,
    campaign_id TEXT,

    -- Timestamps
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,

    FOREIGN KEY (signal_name) REFERENCES marketing.bit_signal_weights(signal_name),
    FOREIGN KEY (campaign_id) REFERENCES marketing.campaigns(campaign_id)
);

-- Attribution Feedback table for optimization
CREATE TABLE IF NOT EXISTS marketing.attribution_feedback (
    id SERIAL PRIMARY KEY,
    person_unique_id TEXT NOT NULL,
    company_unique_id TEXT NOT NULL,

    -- Outcome
    outcome TEXT CHECK (outcome IN ('closed_won', 'closed_lost', 'qualified', 'disqualified')),
    deal_value NUMERIC,

    -- Associated scores and signals at time of outcome
    ple_score_at_outcome NUMERIC,
    bit_signals_triggered TEXT[],
    campaign_ids TEXT[],

    -- Model versions for tracking
    ple_model_version TEXT,
    bit_model_version TEXT,

    -- Timestamps
    outcome_date TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    FOREIGN KEY (person_unique_id) REFERENCES marketing.people_master(unique_id),
    FOREIGN KEY (company_unique_id) REFERENCES marketing.company_master(unique_id)
);

-- Indexes for performance
CREATE INDEX idx_ple_scoring_company ON marketing.ple_lead_scoring(company_unique_id);
CREATE INDEX idx_ple_scoring_score ON marketing.ple_lead_scoring(score DESC);
CREATE INDEX idx_ple_scoring_updated ON marketing.ple_lead_scoring(updated_at DESC);
CREATE INDEX idx_bit_signal_weights_category ON marketing.bit_signal_weights(signal_category);
CREATE INDEX idx_bit_signal_events_company ON marketing.bit_signal_events(company_unique_id);
CREATE INDEX idx_bit_signal_events_processed ON marketing.bit_signal_events(processed);
CREATE INDEX idx_scoring_history_person ON marketing.scoring_history(person_unique_id);
CREATE INDEX idx_scoring_history_date ON marketing.scoring_history(scored_at DESC);
CREATE INDEX idx_attribution_feedback_outcome ON marketing.attribution_feedback(outcome);

-- Insert default BIT signal weights (version 1.0.0)
INSERT INTO marketing.bit_signal_weights (signal_name, weight, signal_category, signal_description, model_version)
VALUES
    ('funding_series_a_plus', 85, 'funding', 'Series A or later funding round announced', '1.0.0'),
    ('funding_seed', 65, 'funding', 'Seed funding round announced', '1.0.0'),
    ('hiring_surge', 75, 'hiring', 'Significant increase in job postings (>20%)', '1.0.0'),
    ('executive_change', 70, 'hiring', 'C-level or VP hire in relevant department', '1.0.0'),
    ('tech_stack_match', 80, 'technology', 'Adopted technology in our integration ecosystem', '1.0.0'),
    ('competitor_switch', 90, 'competitor', 'Publicly switched from competitor', '1.0.0'),
    ('expansion_announcement', 75, 'news', 'Geographic or product expansion announced', '1.0.0'),
    ('website_surge', 60, 'engagement', 'Multiple website visits in short period', '1.0.0'),
    ('content_download', 55, 'engagement', 'Downloaded high-value content', '1.0.0'),
    ('pricing_page_visit', 65, 'engagement', 'Visited pricing page multiple times', '1.0.0'),
    ('demo_request', 95, 'engagement', 'Requested product demo', '1.0.0'),
    ('regulatory_change', 70, 'regulatory', 'New regulation affects their industry', '1.0.0'),
    ('earnings_growth', 60, 'financial', 'Strong quarterly earnings reported', '1.0.0'),
    ('ipo_filing', 80, 'financial', 'IPO filing or announcement', '1.0.0')
ON CONFLICT (signal_name) DO NOTHING;

-- Insert initial PLE scoring model version
INSERT INTO marketing.scoring_model_versions (
    model_type,
    version,
    model_config,
    is_active,
    activated_at,
    created_by
)
VALUES
(
    'PLE',
    '1.0.0',
    '{
        "weights": {
            "firmographics": {
                "company_size": 15,
                "industry_fit": 10,
                "geography": 5,
                "technology_stack": 10
            },
            "engagement": {
                "email_opens": 10,
                "email_clicks": 15,
                "website_visits": 10,
                "content_downloads": 5
            },
            "intent": {
                "search_intent": 10,
                "competitor_research": 10,
                "pricing_interest": 10
            }
        },
        "thresholds": {
            "hot": 85,
            "warm": 70,
            "cool": 50
        }
    }'::JSONB,
    true,
    NOW(),
    'system'
),
(
    'BIT',
    '1.0.0',
    '{
        "signal_threshold": 70,
        "aggregation_window": "7 days",
        "max_signals_per_company": 5,
        "decay_rate": 0.1
    }'::JSONB,
    true,
    NOW(),
    'system'
);

-- Function to calculate PLE lead score
CREATE OR REPLACE FUNCTION marketing.calculate_ple_score(
    p_person_id TEXT,
    p_features JSONB,
    p_model_version TEXT DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    v_model_config JSONB;
    v_firmographics_score NUMERIC := 0;
    v_engagement_score NUMERIC := 0;
    v_intent_score NUMERIC := 0;
    v_attribution_score NUMERIC := 0;
    v_total_score NUMERIC;
    v_model_version TEXT;
BEGIN
    -- Get active model configuration
    IF p_model_version IS NULL THEN
        SELECT version, model_config INTO v_model_version, v_model_config
        FROM marketing.scoring_model_versions
        WHERE model_type = 'PLE' AND is_active = true
        LIMIT 1;
    ELSE
        SELECT version, model_config INTO v_model_version, v_model_config
        FROM marketing.scoring_model_versions
        WHERE model_type = 'PLE' AND version = p_model_version;
    END IF;

    -- Calculate firmographics score
    v_firmographics_score := LEAST(40,
        COALESCE((p_features->>'company_size')::NUMERIC * 0.01, 0) +
        CASE WHEN p_features->>'industry' IN ('SaaS', 'Technology', 'Finance') THEN 10 ELSE 5 END +
        CASE WHEN p_features->>'geography' = 'North America' THEN 5 ELSE 3 END
    );

    -- Calculate engagement score
    v_engagement_score := LEAST(30,
        COALESCE((p_features->>'email_open_rate')::NUMERIC * 0.3, 0) +
        COALESCE((p_features->>'website_visits')::NUMERIC * 2, 0) +
        COALESCE((p_features->>'content_downloads')::NUMERIC * 5, 0)
    );

    -- Calculate intent score
    v_intent_score := LEAST(30,
        CASE WHEN p_features->>'funding_event' = 'true' THEN 15 ELSE 0 END +
        CASE WHEN p_features->>'hiring_surge' = 'true' THEN 10 ELSE 0 END +
        CASE WHEN p_features->>'tech_adoption' = 'true' THEN 10 ELSE 0 END
    );

    -- Get attribution score from historical performance
    SELECT COALESCE(AVG(
        CASE outcome
            WHEN 'closed_won' THEN 20
            WHEN 'qualified' THEN 10
            WHEN 'closed_lost' THEN -5
            ELSE 0
        END
    ), 0) INTO v_attribution_score
    FROM marketing.attribution_feedback
    WHERE person_unique_id = p_person_id
    AND outcome_date > NOW() - INTERVAL '6 months';

    -- Calculate total score
    v_total_score := LEAST(100,
        v_firmographics_score +
        v_engagement_score +
        v_intent_score +
        v_attribution_score
    );

    RETURN jsonb_build_object(
        'score', v_total_score,
        'firmographics_score', v_firmographics_score,
        'engagement_score', v_engagement_score,
        'intent_score', v_intent_score,
        'attribution_score', v_attribution_score,
        'model_version', v_model_version
    );
END;
$$ LANGUAGE plpgsql;

-- Function to optimize BIT signal weights based on attribution
CREATE OR REPLACE FUNCTION marketing.optimize_bit_weights()
RETURNS void AS $$
DECLARE
    v_signal RECORD;
    v_new_weight NUMERIC;
    v_conversion_rate NUMERIC;
    v_new_version TEXT;
BEGIN
    -- Generate new version number
    SELECT 'v' || TO_CHAR(NOW(), 'YYYYMMDD.HH24MI') INTO v_new_version;

    -- Loop through each signal
    FOR v_signal IN
        SELECT signal_name, weight
        FROM marketing.bit_signal_weights
    LOOP
        -- Calculate conversion rate for this signal
        SELECT
            COUNT(DISTINCT af.person_unique_id) FILTER (WHERE af.outcome = 'closed_won') * 100.0 /
            NULLIF(COUNT(DISTINCT bse.person_unique_id), 0)
        INTO v_conversion_rate
        FROM marketing.bit_signal_events bse
        LEFT JOIN marketing.attribution_feedback af
            ON af.person_unique_id = bse.person_unique_id
            AND af.outcome_date > bse.detected_at
        WHERE bse.signal_name = v_signal.signal_name
        AND bse.detected_at > NOW() - INTERVAL '3 months';

        -- Calculate new weight based on conversion rate
        IF v_conversion_rate IS NOT NULL THEN
            -- Adjust weight: increase if conversion > 10%, decrease if < 5%
            v_new_weight := v_signal.weight;
            IF v_conversion_rate > 10 THEN
                v_new_weight := LEAST(100, v_signal.weight * 1.1);
            ELSIF v_conversion_rate < 5 THEN
                v_new_weight := GREATEST(10, v_signal.weight * 0.9);
            END IF;

            -- Update signal weight
            UPDATE marketing.bit_signal_weights
            SET weight = v_new_weight,
                conversion_rate = v_conversion_rate,
                model_version = v_new_version,
                last_optimized = NOW(),
                effectiveness_score = LEAST(100, v_conversion_rate * 10)
            WHERE signal_name = v_signal.signal_name;
        END IF;
    END LOOP;

    -- Create new model version record
    INSERT INTO marketing.scoring_model_versions (
        model_type,
        version,
        model_config,
        created_by
    )
    SELECT
        'BIT',
        v_new_version,
        jsonb_build_object(
            'weights', jsonb_object_agg(signal_name, weight),
            'optimized_at', NOW()
        ),
        'auto_optimizer'
    FROM marketing.bit_signal_weights;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update timestamps
CREATE OR REPLACE FUNCTION marketing.update_scoring_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_ple_scoring_timestamp
    BEFORE UPDATE ON marketing.ple_lead_scoring
    FOR EACH ROW
    EXECUTE FUNCTION marketing.update_scoring_timestamp();

-- View for lead scoring analytics
CREATE OR REPLACE VIEW marketing.lead_scoring_analytics AS
SELECT
    pls.person_unique_id,
    pls.company_unique_id,
    pls.score,
    pls.model_version,
    pm.first_name,
    pm.last_name,
    pm.email,
    cm.company_name,
    cm.industry,
    cm.employee_count,
    CASE
        WHEN pls.score >= 85 THEN 'Hot'
        WHEN pls.score >= 70 THEN 'Warm'
        WHEN pls.score >= 50 THEN 'Cool'
        ELSE 'Cold'
    END as lead_temperature,
    pls.firmographics_score,
    pls.engagement_score,
    pls.intent_score,
    pls.attribution_score,
    pls.last_scored_at
FROM marketing.ple_lead_scoring pls
JOIN marketing.people_master pm ON pm.unique_id = pls.person_unique_id
JOIN marketing.company_master cm ON cm.unique_id = pls.company_unique_id
ORDER BY pls.score DESC;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA marketing TO authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA marketing TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA marketing TO authenticated;
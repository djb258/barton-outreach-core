-- ============================================================================
-- Migration: Create marketing.company_intelligence
-- Date: 2025-10-22
-- Purpose: Track company intelligence signals for BIT (Buyer Intent Tool)
-- Barton ID: 04.04.03.XX.XXXXX.XXX (segment3=03 for company intelligence)
-- ============================================================================

-- Ensure marketing schema exists
CREATE SCHEMA IF NOT EXISTS marketing;

-- ============================================================================
-- HELPER FUNCTION: Generate Company Intelligence Barton ID
-- ============================================================================
CREATE OR REPLACE FUNCTION marketing.generate_company_intelligence_barton_id()
RETURNS TEXT AS $$
DECLARE
    segment1 VARCHAR(2);
    segment2 VARCHAR(2);
    segment3 VARCHAR(2);
    segment4 VARCHAR(2);
    segment5 VARCHAR(5);
    segment6 VARCHAR(3);
    barton_id TEXT;
BEGIN
    -- Barton ID Format: 04.04.03.XX.XXXXX.XXX
    segment1 := '04'; -- Database layer
    segment2 := '04'; -- Marketing subhive
    segment3 := '03'; -- Company intelligence microprocess
    segment4 := LPAD((EXTRACT(EPOCH FROM NOW())::BIGINT % 100)::TEXT, 2, '0');
    segment5 := LPAD((RANDOM() * 100000)::INT::TEXT, 5, '0');
    segment6 := LPAD((RANDOM() * 1000)::INT::TEXT, 3, '0');

    barton_id := segment1 || '.' || segment2 || '.' || segment3 || '.' ||
                 segment4 || '.' || segment5 || '.' || segment6;

    RETURN barton_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TABLE: marketing.company_intelligence
-- ============================================================================
CREATE TABLE IF NOT EXISTS marketing.company_intelligence (
    id SERIAL,

    -- Barton ID (Primary Key)
    intel_unique_id TEXT PRIMARY KEY
        CHECK (intel_unique_id ~ '^04\\.04\\.03\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$'),

    -- Foreign Key to Company Master
    company_unique_id TEXT NOT NULL
        REFERENCES marketing.company_master(company_unique_id) ON DELETE CASCADE,

    -- Intelligence Classification
    intelligence_type TEXT NOT NULL
        CHECK (intelligence_type IN (
            'leadership_change',
            'funding_round',
            'merger_acquisition',
            'tech_stack_update',
            'expansion',
            'restructuring',
            'news_mention'
        )),

    -- Event Details
    event_date DATE,
    event_description TEXT,

    -- Source Information
    source_url TEXT,
    source_type TEXT
        CHECK (source_type IN ('linkedin', 'news', 'website', 'apify', 'manual')),

    -- Quality Metrics
    confidence_score NUMERIC(3,2)
        CHECK (confidence_score >= 0.00 AND confidence_score <= 1.00),
    impact_level TEXT
        CHECK (impact_level IN ('critical', 'high', 'medium', 'low')),

    -- Flexible Metadata
    metadata JSONB DEFAULT '{}',

    -- Audit Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_company_intel_company_id
    ON marketing.company_intelligence(company_unique_id);

CREATE INDEX IF NOT EXISTS idx_company_intel_type
    ON marketing.company_intelligence(intelligence_type);

CREATE INDEX IF NOT EXISTS idx_company_intel_impact
    ON marketing.company_intelligence(impact_level);

CREATE INDEX IF NOT EXISTS idx_company_intel_event_date
    ON marketing.company_intelligence(event_date DESC);

CREATE INDEX IF NOT EXISTS idx_company_intel_created_at
    ON marketing.company_intelligence(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_company_intel_source_type
    ON marketing.company_intelligence(source_type);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_company_intel_company_type_date
    ON marketing.company_intelligence(company_unique_id, intelligence_type, event_date DESC);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION marketing.update_company_intelligence_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_company_intelligence_updated_at
    BEFORE UPDATE ON marketing.company_intelligence
    FOR EACH ROW
    EXECUTE FUNCTION marketing.update_company_intelligence_timestamp();

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

/**
 * Insert company intelligence with auto-generated Barton ID
 *
 * Example:
 *   SELECT marketing.insert_company_intelligence(
 *       '04.04.01.84.48151.001',
 *       'funding_round',
 *       '2025-10-20',
 *       'Series B funding round of $50M',
 *       'https://techcrunch.com/...',
 *       'news',
 *       0.95,
 *       'high',
 *       '{"amount": "$50M", "investors": ["Acme Ventures"]}'::jsonb
 *   );
 */
CREATE OR REPLACE FUNCTION marketing.insert_company_intelligence(
    p_company_unique_id TEXT,
    p_intelligence_type TEXT,
    p_event_date DATE DEFAULT NULL,
    p_event_description TEXT DEFAULT NULL,
    p_source_url TEXT DEFAULT NULL,
    p_source_type TEXT DEFAULT 'apify',
    p_confidence_score NUMERIC(3,2) DEFAULT 0.75,
    p_impact_level TEXT DEFAULT 'medium',
    p_metadata JSONB DEFAULT '{}'
)
RETURNS TEXT AS $$
DECLARE
    v_intel_id TEXT;
BEGIN
    -- Generate Barton ID
    v_intel_id := marketing.generate_company_intelligence_barton_id();

    -- Insert intelligence record
    INSERT INTO marketing.company_intelligence (
        intel_unique_id,
        company_unique_id,
        intelligence_type,
        event_date,
        event_description,
        source_url,
        source_type,
        confidence_score,
        impact_level,
        metadata
    ) VALUES (
        v_intel_id,
        p_company_unique_id,
        p_intelligence_type,
        p_event_date,
        p_event_description,
        p_source_url,
        p_source_type,
        p_confidence_score,
        p_impact_level,
        p_metadata
    );

    RETURN v_intel_id;
END;
$$ LANGUAGE plpgsql;

/**
 * Get recent intelligence for a company
 *
 * Example:
 *   SELECT * FROM marketing.get_company_intelligence('04.04.01.84.48151.001', 30);
 */
CREATE OR REPLACE FUNCTION marketing.get_company_intelligence(
    p_company_unique_id TEXT,
    p_days_back INTEGER DEFAULT 90
)
RETURNS TABLE (
    intel_unique_id TEXT,
    intelligence_type TEXT,
    event_date DATE,
    event_description TEXT,
    impact_level TEXT,
    confidence_score NUMERIC,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ci.intel_unique_id,
        ci.intelligence_type,
        ci.event_date,
        ci.event_description,
        ci.impact_level,
        ci.confidence_score,
        ci.created_at
    FROM marketing.company_intelligence ci
    WHERE ci.company_unique_id = p_company_unique_id
      AND ci.created_at >= NOW() - (p_days_back || ' days')::INTERVAL
    ORDER BY ci.event_date DESC NULLS LAST, ci.created_at DESC;
END;
$$ LANGUAGE plpgsql;

/**
 * Get high-impact intelligence signals for BIT engine
 *
 * Example:
 *   SELECT * FROM marketing.get_high_impact_signals(7);
 */
CREATE OR REPLACE FUNCTION marketing.get_high_impact_signals(
    p_days_back INTEGER DEFAULT 7
)
RETURNS TABLE (
    intel_unique_id TEXT,
    company_unique_id TEXT,
    company_name TEXT,
    intelligence_type TEXT,
    event_description TEXT,
    impact_level TEXT,
    confidence_score NUMERIC,
    event_date DATE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ci.intel_unique_id,
        ci.company_unique_id,
        cm.company_name,
        ci.intelligence_type,
        ci.event_description,
        ci.impact_level,
        ci.confidence_score,
        ci.event_date
    FROM marketing.company_intelligence ci
    JOIN marketing.company_master cm ON ci.company_unique_id = cm.company_unique_id
    WHERE ci.impact_level IN ('critical', 'high')
      AND ci.confidence_score >= 0.70
      AND ci.created_at >= NOW() - (p_days_back || ' days')::INTERVAL
    ORDER BY
        CASE ci.impact_level
            WHEN 'critical' THEN 1
            WHEN 'high' THEN 2
            ELSE 3
        END,
        ci.confidence_score DESC,
        ci.event_date DESC NULLS LAST;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE marketing.company_intelligence IS
    'Company intelligence tracking for BIT (Buyer Intent Tool). Barton ID: 04.04.03.XX.XXXXX.XXX';

COMMENT ON COLUMN marketing.company_intelligence.intel_unique_id IS
    'Barton ID format: 04.04.03.XX.XXXXX.XXX (segment3=03 for company intelligence)';

COMMENT ON COLUMN marketing.company_intelligence.intelligence_type IS
    'Type of intelligence signal: leadership_change, funding_round, merger_acquisition, tech_stack_update, expansion, restructuring, news_mention';

COMMENT ON COLUMN marketing.company_intelligence.confidence_score IS
    'Confidence score 0.00-1.00 indicating reliability of intelligence';

COMMENT ON COLUMN marketing.company_intelligence.impact_level IS
    'Business impact level: critical, high, medium, low';

-- ============================================================================
-- GRANTS (adjust as needed for your security model)
-- ============================================================================
-- GRANT SELECT, INSERT, UPDATE ON marketing.company_intelligence TO authenticated;
-- GRANT USAGE, SELECT ON SEQUENCE marketing.company_intelligence_id_seq TO authenticated;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Table: marketing.company_intelligence
-- Barton ID: 04.04.03.XX.XXXXX.XXX
-- Status: Ready for BIT integration
-- ============================================================================

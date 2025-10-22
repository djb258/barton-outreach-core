-- ============================================================================
-- Migration: Create marketing.people_intelligence
-- Date: 2025-10-22
-- Purpose: Track executive movements for PLE (Promoted Lead Enrichment)
-- Barton ID: 04.04.04.XX.XXXXX.XXX (segment3=04 for people intelligence)
-- ============================================================================

-- Ensure marketing schema exists
CREATE SCHEMA IF NOT EXISTS marketing;

-- ============================================================================
-- HELPER FUNCTION: Generate People Intelligence Barton ID
-- ============================================================================
CREATE OR REPLACE FUNCTION marketing.generate_people_intelligence_barton_id()
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
    -- Barton ID Format: 04.04.04.XX.XXXXX.XXX
    segment1 := '04'; -- Database layer
    segment2 := '04'; -- Marketing subhive
    segment3 := '04'; -- People intelligence microprocess
    segment4 := LPAD((EXTRACT(EPOCH FROM NOW())::BIGINT % 100)::TEXT, 2, '0');
    segment5 := LPAD((RANDOM() * 100000)::INT::TEXT, 5, '0');
    segment6 := LPAD((RANDOM() * 1000)::INT::TEXT, 3, '0');

    barton_id := segment1 || '.' || segment2 || '.' || segment3 || '.' ||
                 segment4 || '.' || segment5 || '.' || segment6;

    RETURN barton_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TABLE: marketing.people_intelligence
-- ============================================================================
CREATE TABLE IF NOT EXISTS marketing.people_intelligence (
    id SERIAL,

    -- Barton ID (Primary Key)
    intel_unique_id TEXT PRIMARY KEY
        CHECK (intel_unique_id ~ '^04\\.04\\.04\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$'),

    -- Foreign Keys
    person_unique_id TEXT NOT NULL
        REFERENCES marketing.people_master(unique_id) ON DELETE CASCADE,
    company_unique_id TEXT NOT NULL
        REFERENCES marketing.company_master(company_unique_id) ON DELETE CASCADE,

    -- Change Classification
    change_type TEXT NOT NULL
        CHECK (change_type IN (
            'promotion',
            'job_change',
            'role_change',
            'left_company',
            'new_company'
        )),

    -- Change Details
    previous_title TEXT,
    new_title TEXT,
    previous_company TEXT,
    new_company TEXT,

    -- Timing
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    effective_date TIMESTAMPTZ,

    -- Verification
    verified BOOLEAN DEFAULT FALSE,
    verification_method TEXT
        CHECK (verification_method IS NULL OR verification_method IN (
            'linkedin_confirmed',
            'apify_verified',
            'manual_verified',
            'company_website',
            'press_release'
        )),

    -- Audit Trail
    audit_log_id INTEGER,

    -- Audit Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_people_intel_person_id
    ON marketing.people_intelligence(person_unique_id);

CREATE INDEX IF NOT EXISTS idx_people_intel_company_id
    ON marketing.people_intelligence(company_unique_id);

CREATE INDEX IF NOT EXISTS idx_people_intel_change_type
    ON marketing.people_intelligence(change_type);

CREATE INDEX IF NOT EXISTS idx_people_intel_detected_at
    ON marketing.people_intelligence(detected_at DESC);

CREATE INDEX IF NOT EXISTS idx_people_intel_effective_date
    ON marketing.people_intelligence(effective_date DESC NULLS LAST);

CREATE INDEX IF NOT EXISTS idx_people_intel_verified
    ON marketing.people_intelligence(verified);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_people_intel_person_change_date
    ON marketing.people_intelligence(person_unique_id, change_type, detected_at DESC);

CREATE INDEX IF NOT EXISTS idx_people_intel_company_change_date
    ON marketing.people_intelligence(company_unique_id, change_type, detected_at DESC);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

/**
 * Insert people intelligence with auto-generated Barton ID
 *
 * Example:
 *   SELECT marketing.insert_people_intelligence(
 *       '04.04.02.84.48151.001',
 *       '04.04.01.84.48151.001',
 *       'promotion',
 *       'VP of Sales',
 *       'Chief Revenue Officer',
 *       NULL,
 *       NULL,
 *       '2025-10-01'::timestamptz,
 *       TRUE,
 *       'linkedin_confirmed'
 *   );
 */
CREATE OR REPLACE FUNCTION marketing.insert_people_intelligence(
    p_person_unique_id TEXT,
    p_company_unique_id TEXT,
    p_change_type TEXT,
    p_previous_title TEXT DEFAULT NULL,
    p_new_title TEXT DEFAULT NULL,
    p_previous_company TEXT DEFAULT NULL,
    p_new_company TEXT DEFAULT NULL,
    p_effective_date TIMESTAMPTZ DEFAULT NULL,
    p_verified BOOLEAN DEFAULT FALSE,
    p_verification_method TEXT DEFAULT NULL,
    p_audit_log_id INTEGER DEFAULT NULL
)
RETURNS TEXT AS $$
DECLARE
    v_intel_id TEXT;
BEGIN
    -- Generate Barton ID
    v_intel_id := marketing.generate_people_intelligence_barton_id();

    -- Insert intelligence record
    INSERT INTO marketing.people_intelligence (
        intel_unique_id,
        person_unique_id,
        company_unique_id,
        change_type,
        previous_title,
        new_title,
        previous_company,
        new_company,
        effective_date,
        verified,
        verification_method,
        audit_log_id
    ) VALUES (
        v_intel_id,
        p_person_unique_id,
        p_company_unique_id,
        p_change_type,
        p_previous_title,
        p_new_title,
        p_previous_company,
        p_new_company,
        p_effective_date,
        p_verified,
        p_verification_method,
        p_audit_log_id
    );

    RETURN v_intel_id;
END;
$$ LANGUAGE plpgsql;

/**
 * Get recent intelligence for a person
 *
 * Example:
 *   SELECT * FROM marketing.get_people_intelligence('04.04.02.84.48151.001', 180);
 */
CREATE OR REPLACE FUNCTION marketing.get_people_intelligence(
    p_person_unique_id TEXT,
    p_days_back INTEGER DEFAULT 180
)
RETURNS TABLE (
    intel_unique_id TEXT,
    change_type TEXT,
    previous_title TEXT,
    new_title TEXT,
    effective_date TIMESTAMPTZ,
    verified BOOLEAN,
    detected_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        pi.intel_unique_id,
        pi.change_type,
        pi.previous_title,
        pi.new_title,
        pi.effective_date,
        pi.verified,
        pi.detected_at
    FROM marketing.people_intelligence pi
    WHERE pi.person_unique_id = p_person_unique_id
      AND pi.detected_at >= NOW() - (p_days_back || ' days')::INTERVAL
    ORDER BY pi.effective_date DESC NULLS LAST, pi.detected_at DESC;
END;
$$ LANGUAGE plpgsql;

/**
 * Get recent executive movements for PLE engine
 *
 * Example:
 *   SELECT * FROM marketing.get_recent_executive_movements(30);
 */
CREATE OR REPLACE FUNCTION marketing.get_recent_executive_movements(
    p_days_back INTEGER DEFAULT 30
)
RETURNS TABLE (
    intel_unique_id TEXT,
    person_unique_id TEXT,
    person_name TEXT,
    company_unique_id TEXT,
    company_name TEXT,
    change_type TEXT,
    previous_title TEXT,
    new_title TEXT,
    detected_at TIMESTAMPTZ,
    verified BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        pi.intel_unique_id,
        pi.person_unique_id,
        pm.full_name,
        pi.company_unique_id,
        cm.company_name,
        pi.change_type,
        pi.previous_title,
        pi.new_title,
        pi.detected_at,
        pi.verified
    FROM marketing.people_intelligence pi
    JOIN marketing.people_master pm ON pi.person_unique_id = pm.unique_id
    JOIN marketing.company_master cm ON pi.company_unique_id = cm.company_unique_id
    WHERE pi.detected_at >= NOW() - (p_days_back || ' days')::INTERVAL
      AND pi.change_type IN ('promotion', 'new_company')
    ORDER BY pi.detected_at DESC;
END;
$$ LANGUAGE plpgsql;

/**
 * Detect title changes by comparing current people_master to intelligence history
 *
 * Example:
 *   SELECT * FROM marketing.detect_title_changes();
 */
CREATE OR REPLACE FUNCTION marketing.detect_title_changes()
RETURNS TABLE (
    person_unique_id TEXT,
    person_name TEXT,
    current_title TEXT,
    last_known_title TEXT,
    title_changed BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    WITH latest_intel AS (
        SELECT DISTINCT ON (person_unique_id)
            person_unique_id,
            new_title,
            detected_at
        FROM marketing.people_intelligence
        WHERE change_type IN ('promotion', 'role_change', 'job_change')
          AND new_title IS NOT NULL
        ORDER BY person_unique_id, detected_at DESC
    )
    SELECT
        pm.unique_id,
        pm.full_name,
        pm.title AS current_title,
        li.new_title AS last_known_title,
        CASE
            WHEN pm.title IS DISTINCT FROM li.new_title THEN TRUE
            ELSE FALSE
        END AS title_changed
    FROM marketing.people_master pm
    LEFT JOIN latest_intel li ON pm.unique_id = li.person_unique_id
    WHERE pm.title IS NOT NULL
      AND (
          li.new_title IS NULL
          OR pm.title IS DISTINCT FROM li.new_title
      );
END;
$$ LANGUAGE plpgsql;

/**
 * Get unverified intelligence that needs review
 *
 * Example:
 *   SELECT * FROM marketing.get_unverified_intelligence(7);
 */
CREATE OR REPLACE FUNCTION marketing.get_unverified_intelligence(
    p_days_back INTEGER DEFAULT 7
)
RETURNS TABLE (
    intel_unique_id TEXT,
    person_name TEXT,
    company_name TEXT,
    change_type TEXT,
    new_title TEXT,
    detected_at TIMESTAMPTZ,
    days_unverified INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        pi.intel_unique_id,
        pm.full_name,
        cm.company_name,
        pi.change_type,
        pi.new_title,
        pi.detected_at,
        EXTRACT(DAY FROM NOW() - pi.detected_at)::INTEGER AS days_unverified
    FROM marketing.people_intelligence pi
    JOIN marketing.people_master pm ON pi.person_unique_id = pm.unique_id
    JOIN marketing.company_master cm ON pi.company_unique_id = cm.company_unique_id
    WHERE pi.verified = FALSE
      AND pi.detected_at >= NOW() - (p_days_back || ' days')::INTERVAL
    ORDER BY pi.detected_at ASC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE marketing.people_intelligence IS
    'Executive movement tracking for PLE (Promoted Lead Enrichment). Barton ID: 04.04.04.XX.XXXXX.XXX';

COMMENT ON COLUMN marketing.people_intelligence.intel_unique_id IS
    'Barton ID format: 04.04.04.XX.XXXXX.XXX (segment3=04 for people intelligence)';

COMMENT ON COLUMN marketing.people_intelligence.change_type IS
    'Type of career change: promotion, job_change, role_change, left_company, new_company';

COMMENT ON COLUMN marketing.people_intelligence.detected_at IS
    'When the intelligence was first detected in the system';

COMMENT ON COLUMN marketing.people_intelligence.effective_date IS
    'When the change actually occurred (may be backdated if detected after the fact)';

COMMENT ON COLUMN marketing.people_intelligence.verified IS
    'Whether the intelligence has been verified through a reliable source';

-- ============================================================================
-- GRANTS (adjust as needed for your security model)
-- ============================================================================
-- GRANT SELECT, INSERT, UPDATE ON marketing.people_intelligence TO authenticated;
-- GRANT USAGE, SELECT ON SEQUENCE marketing.people_intelligence_id_seq TO authenticated;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Table: marketing.people_intelligence
-- Barton ID: 04.04.04.XX.XXXXX.XXX
-- Status: Ready for PLE integration
-- ============================================================================

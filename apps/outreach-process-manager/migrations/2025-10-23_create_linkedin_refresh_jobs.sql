-- ============================================================================
-- Migration: Create marketing.linkedin_refresh_jobs
-- Date: 2025-10-23
-- Purpose: Track LinkedIn monthly enrichment jobs with run status and metrics
-- Barton Doctrine: LinkedIn refresh job tracking (04.04.06.XX.XXXXX.XXX)
-- ============================================================================

-- ============================================================================
-- FUNCTION: generate_linkedin_job_barton_id()
-- ============================================================================
-- Generates Barton ID for LinkedIn refresh jobs
-- Format: 04.04.06.XX.XXXXX.XXX
--   04 = Database layer
--   04 = Marketing subhive
--   06 = LinkedIn refresh microprocess
--   XX = Epoch modulo 100 (temporal component)
--   XXXXX = Random 5-digit identifier
--   XXX = Random 3-digit step
-- ============================================================================

CREATE OR REPLACE FUNCTION marketing.generate_linkedin_job_barton_id()
RETURNS TEXT AS $$
DECLARE
    segment1 TEXT := '04';  -- Database layer
    segment2 TEXT := '04';  -- Marketing subhive
    segment3 TEXT := '06';  -- LinkedIn refresh microprocess
    segment4 TEXT;          -- Epoch % 100
    segment5 TEXT;          -- Random 5-digit
    segment6 TEXT;          -- Random 3-digit
    barton_id TEXT;
BEGIN
    -- Generate temporal component (00-99)
    segment4 := LPAD((EXTRACT(EPOCH FROM NOW())::BIGINT % 100)::TEXT, 2, '0');

    -- Generate random identifier components
    segment5 := LPAD((RANDOM() * 100000)::INT::TEXT, 5, '0');
    segment6 := LPAD((RANDOM() * 1000)::INT::TEXT, 3, '0');

    -- Assemble Barton ID
    barton_id := segment1 || '.' || segment2 || '.' || segment3 || '.' ||
                 segment4 || '.' || segment5 || '.' || segment6;

    RETURN barton_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION marketing.generate_linkedin_job_barton_id() IS
    'Generates Barton ID for LinkedIn refresh jobs in format 04.04.06.XX.XXXXX.XXX.
    Used to uniquely identify each monthly LinkedIn enrichment run.';

-- ============================================================================
-- TABLE: marketing.linkedin_refresh_jobs
-- ============================================================================
-- Tracks LinkedIn monthly enrichment jobs with execution metadata
-- Purpose: Monitor LinkedIn profile updates, track changes, audit runs
-- Integration: Apify Leads Finder monthly refresh workflow
-- ============================================================================

CREATE TABLE IF NOT EXISTS marketing.linkedin_refresh_jobs (
    id SERIAL PRIMARY KEY,

    -- Barton ID (unique identifier)
    job_unique_id TEXT NOT NULL UNIQUE
        CHECK (job_unique_id ~ '^04\\.04\\.06\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$'),

    -- Run timing
    run_started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    run_completed_at TIMESTAMPTZ,

    -- Job metrics
    total_profiles INTEGER DEFAULT 0
        CHECK (total_profiles >= 0),
    profiles_changed INTEGER DEFAULT 0
        CHECK (profiles_changed >= 0),
    profiles_skipped INTEGER DEFAULT 0
        CHECK (profiles_skipped >= 0),

    -- Job status
    status TEXT DEFAULT 'pending'
        CHECK (status IN ('pending', 'running', 'completed', 'failed')),

    -- Apify integration
    actor_id TEXT,                     -- Apify actor used (e.g., code_crafter~leads-finder)
    dataset_id TEXT,                   -- Returned dataset ID from Apify
    run_id TEXT,                       -- Apify run ID for tracking

    -- Error handling
    error_message TEXT,

    -- Additional metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- TABLE COMMENTS
-- ============================================================================

COMMENT ON TABLE marketing.linkedin_refresh_jobs IS
    'LinkedIn monthly refresh job tracking table.
    Records each LinkedIn enrichment run with status, metrics, and Apify metadata.
    Barton ID format: 04.04.06.XX.XXXXX.XXX

    Use Cases:
    - Track monthly LinkedIn profile updates
    - Monitor job execution status and timing
    - Audit Apify actor runs and dataset generation
    - Calculate profile change rates over time
    - Debug failed enrichment jobs';

COMMENT ON COLUMN marketing.linkedin_refresh_jobs.job_unique_id IS
    'Barton ID for this LinkedIn refresh job (format: 04.04.06.XX.XXXXX.XXX).
    Generated via generate_linkedin_job_barton_id() function.';

COMMENT ON COLUMN marketing.linkedin_refresh_jobs.run_started_at IS
    'Timestamp when LinkedIn refresh job started execution.';

COMMENT ON COLUMN marketing.linkedin_refresh_jobs.run_completed_at IS
    'Timestamp when LinkedIn refresh job completed (success or failure).
    NULL indicates job is still running.';

COMMENT ON COLUMN marketing.linkedin_refresh_jobs.total_profiles IS
    'Total number of LinkedIn profiles processed in this job.';

COMMENT ON COLUMN marketing.linkedin_refresh_jobs.profiles_changed IS
    'Number of profiles that had updated data from LinkedIn.';

COMMENT ON COLUMN marketing.linkedin_refresh_jobs.profiles_skipped IS
    'Number of profiles skipped (rate limited, unavailable, etc).';

COMMENT ON COLUMN marketing.linkedin_refresh_jobs.status IS
    'Current job status: pending, running, completed, failed.';

COMMENT ON COLUMN marketing.linkedin_refresh_jobs.actor_id IS
    'Apify actor ID used for this enrichment run (e.g., code_crafter~leads-finder).';

COMMENT ON COLUMN marketing.linkedin_refresh_jobs.dataset_id IS
    'Apify dataset ID containing LinkedIn profile results.';

COMMENT ON COLUMN marketing.linkedin_refresh_jobs.run_id IS
    'Apify run ID for tracking execution in Apify console.';

COMMENT ON COLUMN marketing.linkedin_refresh_jobs.error_message IS
    'Error message if job failed. NULL for successful jobs.';

COMMENT ON COLUMN marketing.linkedin_refresh_jobs.metadata IS
    'Additional job metadata (JSONB): API versions, filters used, rate limits, etc.';

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index on job_unique_id (already covered by UNIQUE constraint)
CREATE INDEX IF NOT EXISTS idx_linkedin_refresh_jobs_job_id
    ON marketing.linkedin_refresh_jobs(job_unique_id);

-- Index on status for filtering active/pending jobs
CREATE INDEX IF NOT EXISTS idx_linkedin_refresh_jobs_status
    ON marketing.linkedin_refresh_jobs(status);

-- Index on run_started_at for chronological queries
CREATE INDEX IF NOT EXISTS idx_linkedin_refresh_jobs_started_at
    ON marketing.linkedin_refresh_jobs(run_started_at DESC);

-- Index on run_completed_at for completion tracking
CREATE INDEX IF NOT EXISTS idx_linkedin_refresh_jobs_completed_at
    ON marketing.linkedin_refresh_jobs(run_completed_at DESC NULLS LAST);

-- Index on actor_id for Apify actor filtering
CREATE INDEX IF NOT EXISTS idx_linkedin_refresh_jobs_actor_id
    ON marketing.linkedin_refresh_jobs(actor_id);

-- Composite index on status + run_started_at for dashboard queries
CREATE INDEX IF NOT EXISTS idx_linkedin_refresh_jobs_status_started
    ON marketing.linkedin_refresh_jobs(status, run_started_at DESC);

-- ============================================================================
-- TRIGGER: Auto-update updated_at timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION marketing.update_linkedin_refresh_jobs_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_linkedin_refresh_jobs_updated_at
    BEFORE UPDATE ON marketing.linkedin_refresh_jobs
    FOR EACH ROW
    EXECUTE FUNCTION marketing.update_linkedin_refresh_jobs_timestamp();

COMMENT ON TRIGGER trg_linkedin_refresh_jobs_updated_at ON marketing.linkedin_refresh_jobs IS
    'Automatically updates updated_at timestamp on row modification.';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- ============================================================================
-- FUNCTION: insert_linkedin_refresh_job()
-- ============================================================================
-- Creates a new LinkedIn refresh job with auto-generated Barton ID
-- ============================================================================

CREATE OR REPLACE FUNCTION marketing.insert_linkedin_refresh_job(
    p_actor_id TEXT DEFAULT NULL,
    p_total_profiles INTEGER DEFAULT 0,
    p_metadata JSONB DEFAULT '{}'
)
RETURNS TEXT AS $$
DECLARE
    v_job_id TEXT;
BEGIN
    -- Generate Barton ID
    v_job_id := marketing.generate_linkedin_job_barton_id();

    -- Insert job record
    INSERT INTO marketing.linkedin_refresh_jobs (
        job_unique_id,
        actor_id,
        total_profiles,
        status,
        metadata
    ) VALUES (
        v_job_id,
        p_actor_id,
        p_total_profiles,
        'pending',
        p_metadata
    );

    RETURN v_job_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION marketing.insert_linkedin_refresh_job(TEXT, INTEGER, JSONB) IS
    'Creates new LinkedIn refresh job with auto-generated Barton ID.
    Returns the generated job_unique_id for tracking.';

-- ============================================================================
-- FUNCTION: update_linkedin_job_status()
-- ============================================================================
-- Updates job status and completion timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION marketing.update_linkedin_job_status(
    p_job_unique_id TEXT,
    p_status TEXT,
    p_total_profiles INTEGER DEFAULT NULL,
    p_profiles_changed INTEGER DEFAULT NULL,
    p_profiles_skipped INTEGER DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_completed_at TIMESTAMPTZ;
BEGIN
    -- Set completion timestamp if status is completed or failed
    IF p_status IN ('completed', 'failed') THEN
        v_completed_at := NOW();
    ELSE
        v_completed_at := NULL;
    END IF;

    -- Update job record
    UPDATE marketing.linkedin_refresh_jobs
    SET
        status = p_status,
        run_completed_at = v_completed_at,
        total_profiles = COALESCE(p_total_profiles, total_profiles),
        profiles_changed = COALESCE(p_profiles_changed, profiles_changed),
        profiles_skipped = COALESCE(p_profiles_skipped, profiles_skipped),
        error_message = p_error_message
    WHERE job_unique_id = p_job_unique_id;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION marketing.update_linkedin_job_status(TEXT, TEXT, INTEGER, INTEGER, INTEGER, TEXT) IS
    'Updates LinkedIn job status and metrics.
    Automatically sets run_completed_at when status is completed or failed.';

-- ============================================================================
-- FUNCTION: get_recent_linkedin_jobs()
-- ============================================================================
-- Retrieves recent LinkedIn refresh jobs with metrics
-- ============================================================================

CREATE OR REPLACE FUNCTION marketing.get_recent_linkedin_jobs(
    p_days_back INTEGER DEFAULT 30,
    p_status TEXT DEFAULT NULL
)
RETURNS TABLE (
    job_unique_id TEXT,
    run_started_at TIMESTAMPTZ,
    run_completed_at TIMESTAMPTZ,
    duration_minutes NUMERIC,
    total_profiles INTEGER,
    profiles_changed INTEGER,
    profiles_skipped INTEGER,
    change_rate_pct NUMERIC,
    status TEXT,
    actor_id TEXT,
    error_message TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        lrj.job_unique_id,
        lrj.run_started_at,
        lrj.run_completed_at,
        CASE
            WHEN lrj.run_completed_at IS NOT NULL THEN
                ROUND(EXTRACT(EPOCH FROM (lrj.run_completed_at - lrj.run_started_at)) / 60.0, 2)
            ELSE NULL
        END AS duration_minutes,
        lrj.total_profiles,
        lrj.profiles_changed,
        lrj.profiles_skipped,
        CASE
            WHEN lrj.total_profiles > 0 THEN
                ROUND((lrj.profiles_changed::NUMERIC / lrj.total_profiles) * 100, 2)
            ELSE 0
        END AS change_rate_pct,
        lrj.status,
        lrj.actor_id,
        lrj.error_message
    FROM marketing.linkedin_refresh_jobs lrj
    WHERE lrj.run_started_at >= NOW() - (p_days_back || ' days')::INTERVAL
      AND (p_status IS NULL OR lrj.status = p_status)
    ORDER BY lrj.run_started_at DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION marketing.get_recent_linkedin_jobs(INTEGER, TEXT) IS
    'Retrieves recent LinkedIn refresh jobs with calculated metrics.
    Includes duration, change rates, and status filtering.';

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

-- Example 1: Create new LinkedIn refresh job
-- SELECT marketing.insert_linkedin_refresh_job(
--     'code_crafter~leads-finder',
--     1500,
--     '{"batch_size": 50, "rate_limit": "5/second"}'::jsonb
-- );

-- Example 2: Update job status after completion
-- SELECT marketing.update_linkedin_job_status(
--     '04.04.06.84.48151.001',
--     'completed',
--     1500,
--     342,
--     12
-- );

-- Example 3: Get jobs from last 30 days
-- SELECT * FROM marketing.get_recent_linkedin_jobs(30);

-- Example 4: Get only failed jobs
-- SELECT * FROM marketing.get_recent_linkedin_jobs(30, 'failed');

-- Example 5: Calculate average change rate
-- SELECT
--     AVG(CASE WHEN total_profiles > 0
--         THEN (profiles_changed::NUMERIC / total_profiles) * 100
--         ELSE 0 END) as avg_change_rate_pct
-- FROM marketing.linkedin_refresh_jobs
-- WHERE status = 'completed'
--   AND run_started_at >= NOW() - INTERVAL '90 days';

-- ============================================================================
-- GRANTS (adjust as needed for your security model)
-- ============================================================================
-- GRANT SELECT, INSERT, UPDATE ON marketing.linkedin_refresh_jobs TO authenticated;
-- GRANT USAGE, SELECT ON SEQUENCE marketing.linkedin_refresh_jobs_id_seq TO authenticated;
-- GRANT EXECUTE ON FUNCTION marketing.generate_linkedin_job_barton_id() TO authenticated;
-- GRANT EXECUTE ON FUNCTION marketing.insert_linkedin_refresh_job(TEXT, INTEGER, JSONB) TO authenticated;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Table: marketing.linkedin_refresh_jobs (created)
-- Function: generate_linkedin_job_barton_id() (created)
-- Helper Functions: insert_linkedin_refresh_job(), update_linkedin_job_status(), get_recent_linkedin_jobs() (created)
-- Indexes: 6 performance indexes (created)
-- Trigger: Auto-update updated_at timestamp (created)
-- Barton ID Format: 04.04.06.XX.XXXXX.XXX (validated via CHECK constraint)
-- Purpose: Monthly LinkedIn enrichment job tracking
-- Integration: Apify Leads Finder monthly refresh workflow
-- ============================================================================

-- ============================================================================
-- IMPLEMENTATION NOTES
-- ============================================================================
--
-- 1. Barton ID Structure:
--    - 04.04.06.XX.XXXXX.XXX
--    - Segment 3 = 06 (LinkedIn refresh microprocess)
--    - Unique per job run
--    - Validated via CHECK constraint
--
-- 2. Job Lifecycle:
--    - Create job: insert_linkedin_refresh_job() → status='pending'
--    - Start run: update status to 'running'
--    - Complete: update_linkedin_job_status() → status='completed', sets run_completed_at
--    - Fail: update_linkedin_job_status() → status='failed', sets error_message
--
-- 3. Metrics Tracked:
--    - total_profiles: Number of profiles in refresh batch
--    - profiles_changed: Profiles with updated LinkedIn data
--    - profiles_skipped: Profiles not processed (rate limits, unavailable, etc)
--    - change_rate_pct: Calculated in get_recent_linkedin_jobs()
--
-- 4. Apify Integration:
--    - actor_id: Tracks which Apify actor was used
--    - dataset_id: Links to Apify dataset with results
--    - run_id: Links to Apify run for console debugging
--
-- 5. Indexes:
--    - job_unique_id (UNIQUE + indexed)
--    - status (for filtering active jobs)
--    - run_started_at DESC (chronological queries)
--    - run_completed_at DESC NULLS LAST (completion tracking)
--    - actor_id (Apify actor filtering)
--    - (status, run_started_at) composite (dashboard queries)
--
-- 6. Future Enhancements:
--    - Add foreign key to marketing.people_master for profile tracking
--    - Create materialized view for monthly aggregates
--    - Add rate limiting metadata in JSONB
--    - Track API credits consumed per job
--    - Link to unified_audit_log for detailed step tracking
--
-- ============================================================================

-- ============================================================================
-- Migration 002: Add Phase Tracking to Company Master
-- ============================================================================
--
-- Purpose: Track current phase and phase completion history for each company
-- Doctrine ID: 04.04.02.04.ple.validation_pipeline
-- Date: 2025-11-17
-- Author: Barton Outreach Core Team
--
-- Changes:
-- 1. Add current_phase column to marketing.company_master
-- 2. Create marketing.phase_completion_log table
-- 3. Add indexes for performance
-- 4. Create trigger to auto-update current_phase
--
-- Rollback: See rollback section at bottom
-- ============================================================================

BEGIN;

-- ============================================================================
-- STEP 1: Add current_phase column to company_master
-- ============================================================================

-- Add current_phase column (tracks which phase company is currently in)
ALTER TABLE marketing.company_master
ADD COLUMN IF NOT EXISTS current_phase DECIMAL(3,1) DEFAULT 0;

COMMENT ON COLUMN marketing.company_master.current_phase IS
'Current phase in outreach pipeline (0=intake, 1=company validation, 1.1=people validation, 2=person validation, 3=outreach readiness, 4=BIT trigger, 5=BIT score, 6=promotion)';

-- Add last_phase_completed_at timestamp
ALTER TABLE marketing.company_master
ADD COLUMN IF NOT EXISTS last_phase_completed_at TIMESTAMPTZ;

COMMENT ON COLUMN marketing.company_master.last_phase_completed_at IS
'Timestamp of last successful phase completion';

-- Create index on current_phase for quick filtering
CREATE INDEX IF NOT EXISTS idx_company_master_current_phase
ON marketing.company_master(current_phase);

-- ============================================================================
-- STEP 2: Create phase_completion_log table
-- ============================================================================

CREATE TABLE IF NOT EXISTS marketing.phase_completion_log (
    log_id SERIAL PRIMARY KEY,
    company_unique_id TEXT NOT NULL,
    phase_id DECIMAL(3,1) NOT NULL,
    phase_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('complete', 'failed', 'skipped', 'running')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_seconds DECIMAL(10,2),
    error_message TEXT,
    result_summary JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Foreign key to company_master
    CONSTRAINT fk_phase_completion_company
        FOREIGN KEY (company_unique_id)
        REFERENCES marketing.company_master(company_unique_id)
        ON DELETE CASCADE
);

-- Add table comment
COMMENT ON TABLE marketing.phase_completion_log IS
'Phase execution history for each company in the outreach pipeline';

-- Add column comments
COMMENT ON COLUMN marketing.phase_completion_log.log_id IS
'Auto-incrementing primary key';

COMMENT ON COLUMN marketing.phase_completion_log.company_unique_id IS
'Reference to company_master.company_unique_id (Barton ID format: 04.04.02.04.30000.###)';

COMMENT ON COLUMN marketing.phase_completion_log.phase_id IS
'Phase identifier (0, 1, 1.1, 2, 3, 4, 5, 6)';

COMMENT ON COLUMN marketing.phase_completion_log.phase_name IS
'Human-readable phase name (e.g., "Phase 1b: People Validation Trigger")';

COMMENT ON COLUMN marketing.phase_completion_log.status IS
'Execution status: complete, failed, skipped, running';

COMMENT ON COLUMN marketing.phase_completion_log.started_at IS
'Timestamp when phase execution started';

COMMENT ON COLUMN marketing.phase_completion_log.completed_at IS
'Timestamp when phase execution completed (NULL if still running)';

COMMENT ON COLUMN marketing.phase_completion_log.duration_seconds IS
'Phase execution duration in seconds';

COMMENT ON COLUMN marketing.phase_completion_log.error_message IS
'Error message if status=failed';

COMMENT ON COLUMN marketing.phase_completion_log.result_summary IS
'Summarized result data as JSON (e.g., {"valid": 120, "invalid": 30})';

-- ============================================================================
-- STEP 3: Create indexes for performance
-- ============================================================================

-- Index on company_unique_id for quick lookup
CREATE INDEX IF NOT EXISTS idx_phase_log_company
ON marketing.phase_completion_log(company_unique_id);

-- Index on phase_id for phase-specific queries
CREATE INDEX IF NOT EXISTS idx_phase_log_phase_id
ON marketing.phase_completion_log(phase_id);

-- Index on status for filtering failed/complete phases
CREATE INDEX IF NOT EXISTS idx_phase_log_status
ON marketing.phase_completion_log(status);

-- Composite index for common query pattern (company + phase)
CREATE INDEX IF NOT EXISTS idx_phase_log_company_phase
ON marketing.phase_completion_log(company_unique_id, phase_id);

-- Index on completed_at for time-based queries
CREATE INDEX IF NOT EXISTS idx_phase_log_completed_at
ON marketing.phase_completion_log(completed_at DESC);

-- ============================================================================
-- STEP 4: Create trigger to auto-update current_phase
-- ============================================================================

-- Trigger function to update current_phase when phase completes
CREATE OR REPLACE FUNCTION marketing.update_company_current_phase()
RETURNS TRIGGER AS $$
BEGIN
    -- Only update if phase completed successfully
    IF NEW.status = 'complete' AND NEW.completed_at IS NOT NULL THEN
        -- Update company_master.current_phase to the highest completed phase
        UPDATE marketing.company_master
        SET
            current_phase = NEW.phase_id,
            last_phase_completed_at = NEW.completed_at,
            updated_at = NOW()
        WHERE company_unique_id = NEW.company_unique_id
          AND (current_phase IS NULL OR current_phase < NEW.phase_id);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS trg_update_company_current_phase ON marketing.phase_completion_log;

CREATE TRIGGER trg_update_company_current_phase
AFTER INSERT OR UPDATE ON marketing.phase_completion_log
FOR EACH ROW
WHEN (NEW.status = 'complete')
EXECUTE FUNCTION marketing.update_company_current_phase();

COMMENT ON FUNCTION marketing.update_company_current_phase() IS
'Auto-update company_master.current_phase when a phase completes successfully';

-- ============================================================================
-- STEP 5: Create helper views for phase tracking
-- ============================================================================

-- View: Companies by current phase
CREATE OR REPLACE VIEW marketing.v_companies_by_phase AS
SELECT
    current_phase,
    COUNT(*) as company_count,
    COUNT(*) FILTER (WHERE validation_status = 'valid') as validated_count,
    COUNT(*) FILTER (WHERE outreach_ready = true) as ready_count,
    MAX(last_phase_completed_at) as latest_completion
FROM marketing.company_master
GROUP BY current_phase
ORDER BY current_phase;

COMMENT ON VIEW marketing.v_companies_by_phase IS
'Summary of companies grouped by current phase in pipeline';

-- View: Recent phase completions (last 24 hours)
CREATE OR REPLACE VIEW marketing.v_recent_phase_completions AS
SELECT
    pcl.log_id,
    pcl.company_unique_id,
    cm.company_name,
    pcl.phase_id,
    pcl.phase_name,
    pcl.status,
    pcl.duration_seconds,
    pcl.completed_at,
    pcl.error_message
FROM marketing.phase_completion_log pcl
LEFT JOIN marketing.company_master cm ON pcl.company_unique_id = cm.company_unique_id
WHERE pcl.completed_at >= NOW() - INTERVAL '24 hours'
ORDER BY pcl.completed_at DESC;

COMMENT ON VIEW marketing.v_recent_phase_completions IS
'Recent phase completions in last 24 hours with company details';

-- View: Failed phases (need retry)
CREATE OR REPLACE VIEW marketing.v_failed_phases AS
SELECT
    pcl.log_id,
    pcl.company_unique_id,
    cm.company_name,
    pcl.phase_id,
    pcl.phase_name,
    pcl.error_message,
    pcl.completed_at as failed_at,
    cm.current_phase as company_current_phase
FROM marketing.phase_completion_log pcl
LEFT JOIN marketing.company_master cm ON pcl.company_unique_id = cm.company_unique_id
WHERE pcl.status = 'failed'
  AND pcl.completed_at >= NOW() - INTERVAL '7 days'  -- Last 7 days only
ORDER BY pcl.completed_at DESC;

COMMENT ON VIEW marketing.v_failed_phases IS
'Failed phases in last 7 days that may need retry';

-- ============================================================================
-- STEP 6: Insert sample data (for testing only - remove in production)
-- ============================================================================

-- This section is commented out by default
-- Uncomment to insert sample phase completion logs for testing

/*
INSERT INTO marketing.phase_completion_log (
    company_unique_id,
    phase_id,
    phase_name,
    status,
    started_at,
    completed_at,
    duration_seconds,
    result_summary
)
SELECT
    company_unique_id,
    1,
    'Company Validation',
    'complete',
    NOW() - INTERVAL '1 hour',
    NOW() - INTERVAL '59 minutes',
    60,
    '{"valid": true}'::jsonb
FROM marketing.company_master
WHERE validation_status = 'valid'
LIMIT 10;
*/

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify current_phase column exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'marketing'
          AND table_name = 'company_master'
          AND column_name = 'current_phase'
    ) THEN
        RAISE EXCEPTION 'Migration failed: current_phase column not created';
    END IF;
END $$;

-- Verify phase_completion_log table exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'marketing'
          AND table_name = 'phase_completion_log'
    ) THEN
        RAISE EXCEPTION 'Migration failed: phase_completion_log table not created';
    END IF;
END $$;

-- Print success message
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 002 completed successfully';
    RAISE NOTICE '   - Added current_phase column to company_master';
    RAISE NOTICE '   - Created phase_completion_log table';
    RAISE NOTICE '   - Created 5 indexes';
    RAISE NOTICE '   - Created auto-update trigger';
    RAISE NOTICE '   - Created 3 helper views';
END $$;

COMMIT;

-- ============================================================================
-- ROLLBACK SCRIPT (run separately if needed)
-- ============================================================================

/*
BEGIN;

-- Drop trigger
DROP TRIGGER IF EXISTS trg_update_company_current_phase ON marketing.phase_completion_log;
DROP FUNCTION IF EXISTS marketing.update_company_current_phase();

-- Drop views
DROP VIEW IF EXISTS marketing.v_failed_phases;
DROP VIEW IF EXISTS marketing.v_recent_phase_completions;
DROP VIEW IF EXISTS marketing.v_companies_by_phase;

-- Drop table (CASCADE will drop indexes automatically)
DROP TABLE IF EXISTS marketing.phase_completion_log CASCADE;

-- Drop columns from company_master
ALTER TABLE marketing.company_master DROP COLUMN IF EXISTS current_phase;
ALTER TABLE marketing.company_master DROP COLUMN IF EXISTS last_phase_completed_at;

COMMIT;

-- Verify rollback
SELECT 'Rollback complete' as status;
*/

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================

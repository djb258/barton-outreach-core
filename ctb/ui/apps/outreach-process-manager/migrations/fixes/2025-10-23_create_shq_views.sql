-- ============================================================================
-- Migration: Create shq Schema Views
-- Date: 2025-10-23
-- Issue: FINAL_COLUMN_COMPLIANCE_REPORT flagged missing shq.audit_log and shq.validation_queue
-- Fix: Create Doctrine-compliant views aliasing authoritative source tables
-- Doctrine Segment: shq schema (Schema HQ)
-- ============================================================================

/**
 * ISSUE CONTEXT:
 *
 * The Barton Doctrine requires shq.audit_log and shq.validation_queue views
 * to exist as standardized interfaces to audit and validation data.
 *
 * These views are ALIASES to the authoritative source tables:
 * - shq.audit_log → marketing.unified_audit_log
 * - shq.validation_queue → intake.validation_failed
 *
 * The views exist for Doctrine compliance; all writes should go to the
 * authoritative source tables, not these views.
 */

-- ==============================================================================
-- STEP 1: Ensure shq schema exists
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS shq;

COMMENT ON SCHEMA shq IS
    'Schema HQ (shq): Barton Doctrine-compliant schema for audit logs and validation queues.
    Contains doctrine-mandated views that alias tables from other schemas.';

-- ==============================================================================
-- STEP 2: Create shq.audit_log view
-- ==============================================================================

/**
 * Authoritative Source: marketing.unified_audit_log
 * Purpose: Central audit trail for all pipeline actions (Steps 1-4)
 * Barton ID segment4='05' for audit records
 */

CREATE OR REPLACE VIEW shq.audit_log AS
SELECT
    id,
    unique_id,
    audit_id,
    process_id,
    status,
    actor,
    timestamp,
    source,
    action,
    step,
    sub_action,
    record_type,
    record_id,
    before_values,
    after_values,
    field_changes,
    error_log,
    error_code
FROM marketing.unified_audit_log;

COMMENT ON VIEW shq.audit_log IS
    'Doctrine-compliant alias for marketing.unified_audit_log (created 2025-10-23).
    The authoritative source remains marketing.unified_audit_log.
    This view exists to satisfy Barton Doctrine schema naming requirements.
    ALL audit logging should write to marketing.unified_audit_log, not this view.';

-- ==============================================================================
-- STEP 3: Create shq.validation_queue view
-- ==============================================================================

/**
 * Authoritative Source: intake.validation_failed
 * Purpose: Tracks records that failed validation and need retry/review
 * Used by Step 2A validation console
 */

CREATE OR REPLACE VIEW shq.validation_queue AS
SELECT *
FROM intake.validation_failed;

COMMENT ON VIEW shq.validation_queue IS
    'Doctrine-compliant alias for intake.validation_failed (created 2025-10-23).
    The authoritative source remains intake.validation_failed.
    This view exists to satisfy Barton Doctrine schema naming requirements.
    Records failing validation checks are inserted into intake.validation_failed.';

-- ==============================================================================
-- STEP 4: Verify views exist and are functional
-- ==============================================================================

/**
 * Test query to confirm views are accessible:
 *
 * SELECT
 *     table_schema,
 *     table_name,
 *     table_type
 * FROM information_schema.tables
 * WHERE table_schema = 'shq'
 *     AND table_name IN ('audit_log', 'validation_queue');
 *
 * Expected Result: 2 rows
 *   - shq.audit_log (VIEW)
 *   - shq.validation_queue (VIEW)
 *
 * Test data accessibility:
 *
 * SELECT COUNT(*) as audit_log_rows FROM shq.audit_log;
 * SELECT COUNT(*) as validation_queue_rows FROM shq.validation_queue;
 *
 * Expected: Both queries return without error (counts may be 0 or >0)
 */

-- ==============================================================================
-- STEP 5: Grant permissions (adjust as needed)
-- ==============================================================================

/**
 * Uncomment if you need to grant read access to specific roles:
 *
 * GRANT SELECT ON shq.audit_log TO authenticated;
 * GRANT SELECT ON shq.validation_queue TO authenticated;
 * GRANT SELECT ON shq.audit_log TO analytics_role;
 * GRANT SELECT ON shq.validation_queue TO validator_role;
 */

-- ==============================================================================
-- VERIFICATION QUERY FOR DEPENDENT TABLES
-- ==============================================================================

/**
 * Verify authoritative source tables exist:
 *
 * SELECT
 *     table_schema,
 *     table_name,
 *     table_type
 * FROM information_schema.tables
 * WHERE (table_schema = 'marketing' AND table_name = 'unified_audit_log')
 *    OR (table_schema = 'intake' AND table_name = 'validation_failed');
 *
 * Expected Result: 2 rows
 *   - marketing.unified_audit_log (TABLE)
 *   - intake.validation_failed (TABLE)
 *
 * If either table is missing, the views will fail with error:
 *   "relation does not exist"
 */

-- ==============================================================================
-- MIGRATION COMPLETE
-- ==============================================================================
-- Schema: shq (created/verified)
-- Views: shq.audit_log, shq.validation_queue (created via CREATE OR REPLACE)
-- Authoritative Sources: marketing.unified_audit_log, intake.validation_failed
-- Status: ✅ Views created per Doctrine requirement
-- Note: Views will fail if source tables don't exist yet
-- ============================================================================

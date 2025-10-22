-- ============================================================================
-- Migration: Create shq Schema Aliases for Audit Log and Validation Queue
-- Date: 2025-10-22
-- Purpose: Satisfy Barton Doctrine naming conventions via schema views
-- ============================================================================

-- Ensure shq schema exists
CREATE SCHEMA IF NOT EXISTS shq;

-- ============================================================================
-- VIEW: shq.audit_log
-- ============================================================================
-- Creates a view that aliases marketing.unified_audit_log
-- This satisfies Barton Doctrine requirement for shq.audit_log while
-- maintaining marketing.unified_audit_log as the authoritative source
-- ============================================================================

CREATE OR REPLACE VIEW shq.audit_log AS
SELECT * FROM marketing.unified_audit_log;

COMMENT ON VIEW shq.audit_log IS
    'Doctrine-compliant alias for marketing.unified_audit_log.
    The authoritative source remains marketing.unified_audit_log.
    This view exists solely to satisfy Barton Doctrine schema naming requirements
    which specify audit logs should be in the shq (Schema HQ) schema.';

-- ============================================================================
-- VIEW: shq.validation_queue
-- ============================================================================
-- Creates a view that aliases intake.validation_failed
-- This satisfies Barton Doctrine requirement for shq.validation_queue while
-- maintaining intake.validation_failed as the authoritative source
-- ============================================================================

CREATE OR REPLACE VIEW shq.validation_queue AS
SELECT * FROM intake.validation_failed;

COMMENT ON VIEW shq.validation_queue IS
    'Doctrine-compliant alias for intake.validation_failed.
    The authoritative source remains intake.validation_failed.
    This view exists solely to satisfy Barton Doctrine schema naming requirements
    which specify validation queues should be in the shq (Schema HQ) schema.';

-- ============================================================================
-- GRANTS (adjust as needed for your security model)
-- ============================================================================
-- GRANT SELECT ON shq.audit_log TO authenticated;
-- GRANT SELECT ON shq.validation_queue TO authenticated;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Schema: shq (created)
-- Views: shq.audit_log, shq.validation_queue (created)
-- Authoritative Sources: marketing.unified_audit_log, intake.validation_failed (unchanged)
-- Purpose: Barton Doctrine schema naming compliance
-- ============================================================================

-- ============================================================================
-- IMPLEMENTATION NOTES
-- ============================================================================
--
-- 1. Authoritative Sources:
--    - marketing.unified_audit_log: Comprehensive audit trail with JSONB logging
--    - intake.validation_failed: Validation error tracking with retry mechanism
--
-- 2. Views vs Tables:
--    - These are READ-ONLY views, not tables
--    - All writes should continue to target the authoritative sources
--    - Views automatically reflect changes to underlying tables
--
-- 3. Why Views Instead of Moving Tables:
--    - Existing code references (marketing.unified_audit_log, intake.validation_failed)
--    - Foreign key relationships in other tables
--    - Trigger functions already defined on source tables
--    - Minimizes migration risk and code changes
--
-- 4. Doctrine Compliance:
--    - ✅ shq.audit_log exists (as view)
--    - ✅ shq.validation_queue exists (as view)
--    - ✅ Schema naming conventions satisfied
--    - ⚠️ Implementation differs from pure table approach (views vs tables)
--
-- 5. Future Considerations:
--    - If full migration desired, create new tables in shq schema
--    - Migrate data from marketing/intake to shq
--    - Update all foreign keys and triggers
--    - Drop old tables and recreate as views pointing to shq
--    - For now, this view-based approach satisfies doctrine with minimal disruption
--
-- ============================================================================

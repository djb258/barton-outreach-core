-- =============================================================================
-- P0 ROLLBACK: BLOG PRODUCTION ENABLEMENT
-- =============================================================================
-- Migration ID: P0_005
-- Date: 2026-01-08
-- Author: Claude Code (Schema Remediation Engineer)
--
-- PURPOSE:
--   Rollback P0_005_blog_production_enablement.sql
--   Removes blog production control infrastructure
--
-- WARNING: This removes ingress control. Blog worker will need code update.
-- =============================================================================

-- Drop helper functions
DROP FUNCTION IF EXISTS outreach.should_fetch_blog_url(UUID, TEXT);
DROP FUNCTION IF EXISTS outreach.get_blog_ingress_config();
DROP FUNCTION IF EXISTS outreach.blog_ingress_enabled();

-- Drop views
DROP VIEW IF EXISTS outreach.v_blog_ingestion_queue;
DROP VIEW IF EXISTS outreach.v_blog_ready;

-- Drop social guard trigger and function
DROP TRIGGER IF EXISTS trg_blog_no_social ON outreach.blog;
DROP FUNCTION IF EXISTS outreach.guard_blog_no_social();

-- Drop source_type_enum column from blog
ALTER TABLE outreach.blog
DROP COLUMN IF EXISTS source_type_enum;

-- Drop enum type
DROP TYPE IF EXISTS outreach.blog_source_type;

-- Drop control table
DROP TRIGGER IF EXISTS set_updated_at ON outreach.blog_ingress_control;
DROP TABLE IF EXISTS outreach.blog_ingress_control;

-- =============================================================================
-- ROLLBACK P0_005 COMPLETE
-- =============================================================================
-- Verify rollback:
--
-- 1. Check control table removed:
-- SELECT * FROM outreach.blog_ingress_control;
-- Expected: ERROR - relation does not exist
--
-- 2. Check enum removed:
-- SELECT enumlabel FROM pg_enum WHERE enumtypid = 'outreach.blog_source_type'::regtype;
-- Expected: 0 rows
--
-- 3. Check views removed:
-- SELECT viewname FROM pg_views WHERE schemaname = 'outreach' AND viewname LIKE '%blog%';
-- Expected: 0 rows (or only pre-existing views)
-- =============================================================================

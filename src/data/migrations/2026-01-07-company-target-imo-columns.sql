-- =============================================================================
-- COMPANY TARGET IMO COLUMNS MIGRATION
-- =============================================================================
-- Date: 2026-01-07
-- Purpose: Add columns required for Company Target IMO (execution prep gate)
--
-- PRD: Company Target (Execution Prep Sub-Hub) v3.0
-- Doctrine: Spine-First Architecture
-- =============================================================================

-- =============================================================================
-- PHASE 1: ADD DOMAIN TO SPINE
-- =============================================================================
-- Domain is denormalized into spine for query performance.
-- Company Target reads from spine, NEVER touches CL directly.

ALTER TABLE outreach.outreach
ADD COLUMN IF NOT EXISTS domain VARCHAR(255);

COMMENT ON COLUMN outreach.outreach.domain IS
'OUT.SPINE.DOMAIN | Company domain, denormalized from CL for query performance.
Company Target reads this - it NEVER touches CL tables directly.';

-- Populate domain from CL (one-time backfill)
-- This is the ONLY time we touch CL from Outreach
UPDATE outreach.outreach o
SET domain = ci.website_url
FROM cl.company_identity ci
WHERE o.sovereign_id = ci.company_unique_id
  AND o.domain IS NULL
  AND ci.website_url IS NOT NULL;

-- =============================================================================
-- PHASE 2: ADD EMAIL METHOD COLUMNS TO COMPANY_TARGET
-- =============================================================================

ALTER TABLE outreach.company_target
ADD COLUMN IF NOT EXISTS email_method VARCHAR(100);

ALTER TABLE outreach.company_target
ADD COLUMN IF NOT EXISTS method_type VARCHAR(50);

ALTER TABLE outreach.company_target
ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(5,4);

ALTER TABLE outreach.company_target
ADD COLUMN IF NOT EXISTS execution_status VARCHAR(50) DEFAULT 'pending';

ALTER TABLE outreach.company_target
ADD COLUMN IF NOT EXISTS imo_completed_at TIMESTAMPTZ;

ALTER TABLE outreach.company_target
ADD COLUMN IF NOT EXISTS is_catchall BOOLEAN DEFAULT FALSE;

-- Add constraint for execution_status
ALTER TABLE outreach.company_target
DROP CONSTRAINT IF EXISTS chk_execution_status;

ALTER TABLE outreach.company_target
ADD CONSTRAINT chk_execution_status
CHECK (execution_status IN ('pending', 'ready', 'failed', 'blocked'));

-- Comments
COMMENT ON COLUMN outreach.company_target.email_method IS
'OUT.TARGET.EMAIL | Discovered email pattern (e.g., first.last@domain.com)';

COMMENT ON COLUMN outreach.company_target.method_type IS
'OUT.TARGET.TYPE | Pattern type: first.last, firstlast, f.last, first.l, first, last, info, contact';

COMMENT ON COLUMN outreach.company_target.confidence_score IS
'OUT.TARGET.CONF | Confidence score 0.0000 to 1.0000';

COMMENT ON COLUMN outreach.company_target.execution_status IS
'OUT.TARGET.STATUS | IMO result: pending (not run), ready (PASS), failed (FAIL), blocked (error)';

COMMENT ON COLUMN outreach.company_target.imo_completed_at IS
'OUT.TARGET.IMO_TS | Timestamp when IMO pass completed (PASS or FAIL)';

COMMENT ON COLUMN outreach.company_target.is_catchall IS
'OUT.TARGET.CATCHALL | True if domain is catch-all (accept all, lower confidence)';

-- =============================================================================
-- PHASE 3: INDEX FOR IMO QUERIES
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_company_target_execution_status
    ON outreach.company_target(execution_status);

CREATE INDEX IF NOT EXISTS idx_company_target_pending
    ON outreach.company_target(outreach_id)
    WHERE execution_status = 'pending';

-- =============================================================================
-- PHASE 4: VERIFY CONSTRAINTS
-- =============================================================================

-- Ensure company_target_errors has correct columns for IMO
ALTER TABLE outreach.company_target_errors
ADD COLUMN IF NOT EXISTS imo_stage VARCHAR(10);

COMMENT ON COLUMN outreach.company_target_errors.imo_stage IS
'OUT.CT_ERR.STAGE | IMO stage where failure occurred: I (input) or M (middle)';

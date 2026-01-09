-- =============================================================================
-- OUTREACH SPINE BUILD MIGRATION
-- =============================================================================
-- Date: 2026-01-06
-- Purpose: Implement master spine architecture per Locked Decisions
--
-- LOCKED DECISIONS IMPLEMENTED:
--   1. Create outreach.outreach as master spine
--   2. outreach_id is THE identity for Outreach (not outreach_context_id)
--   3. sovereign_id is receipt back to CL - sub-hubs don't see it
--   4. All sub-hub tables FK to outreach_id
--   5. Error tables in outreach schema (outreach.*_errors)
--
-- WATERFALL ORDER:
--   CL (sovereign_id, identity_status='PASS')
--     -> outreach.outreach (mints outreach_id)
--       -> Company Target -> DOL -> People -> Blog -> Execution
--
-- =============================================================================

-- =============================================================================
-- PHASE 1: CREATE MASTER SPINE TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach.outreach (
    -- Primary identity for all of Outreach
    outreach_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Receipt back to CL (sub-hubs DO NOT see this directly)
    sovereign_id UUID NOT NULL,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Foreign key to CL (sovereign identity)
    CONSTRAINT fk_outreach_sovereign
        FOREIGN KEY (sovereign_id)
        REFERENCES cl.company_identity(company_unique_id)
        ON DELETE RESTRICT
);

-- Unique constraint: one outreach record per sovereign company
CREATE UNIQUE INDEX IF NOT EXISTS idx_outreach_sovereign_unique
    ON outreach.outreach(sovereign_id);

-- Index for lookups
CREATE INDEX IF NOT EXISTS idx_outreach_created
    ON outreach.outreach(created_at);

-- Table comment
COMMENT ON TABLE outreach.outreach IS
'OUT.SPINE.001 | Master spine table for Outreach program.
outreach_id is THE identity for all Outreach operations.
sovereign_id is the receipt back to CL - sub-hubs do NOT access this directly.

Gate: Only companies with identity_status = ''PASS'' in CL get an outreach_id minted.

All sub-hub tables (company_target, dol, people, blog) FK to outreach_id.';

COMMENT ON COLUMN outreach.outreach.outreach_id IS
'OUT.SPINE.PK | Primary identity for Outreach. All sub-hubs FK to this.
Minted when company passes CL identity gate (identity_status = PASS).';

COMMENT ON COLUMN outreach.outreach.sovereign_id IS
'OUT.SPINE.FK | Receipt back to cl.company_identity.company_unique_id.
Sub-hubs do NOT see this - they only use outreach_id.
ON DELETE RESTRICT - cannot delete CL identity if Outreach exists.';

-- =============================================================================
-- PHASE 2: POPULATE SPINE FROM EXISTING COMPANY_TARGET
-- =============================================================================
-- Note: This assumes company_unique_id in company_target maps to sovereign_id

INSERT INTO outreach.outreach (sovereign_id, created_at)
SELECT DISTINCT
    company_unique_id::UUID as sovereign_id,
    MIN(created_at) as created_at
FROM outreach.company_target
WHERE company_unique_id IS NOT NULL
GROUP BY company_unique_id
ON CONFLICT (sovereign_id) DO NOTHING;

-- =============================================================================
-- PHASE 3: ADD outreach_id FK TO COMPANY_TARGET
-- =============================================================================

-- Add outreach_id column
ALTER TABLE outreach.company_target
ADD COLUMN IF NOT EXISTS outreach_id UUID;

-- Populate outreach_id from spine
UPDATE outreach.company_target ct
SET outreach_id = o.outreach_id
FROM outreach.outreach o
WHERE ct.company_unique_id::UUID = o.sovereign_id
  AND ct.outreach_id IS NULL;

-- Add FK constraint
ALTER TABLE outreach.company_target
ADD CONSTRAINT fk_target_outreach
    FOREIGN KEY (outreach_id)
    REFERENCES outreach.outreach(outreach_id)
    ON DELETE CASCADE;

-- Add index
CREATE INDEX IF NOT EXISTS idx_company_target_outreach
    ON outreach.company_target(outreach_id);

-- Update column comment
COMMENT ON COLUMN outreach.company_target.outreach_id IS
'OUT.TARGET.FK | Foreign key to outreach.outreach.outreach_id.
This is the ONLY FK sub-hubs use. They do NOT directly access sovereign_id.';

-- =============================================================================
-- PHASE 4: ADD outreach_id FK TO PEOPLE TABLE
-- =============================================================================

-- Add outreach_id column
ALTER TABLE outreach.people
ADD COLUMN IF NOT EXISTS outreach_id UUID;

-- Populate outreach_id through company_target
UPDATE outreach.people p
SET outreach_id = ct.outreach_id
FROM outreach.company_target ct
WHERE p.target_id = ct.target_id
  AND p.outreach_id IS NULL;

-- Add FK constraint
ALTER TABLE outreach.people
ADD CONSTRAINT fk_people_outreach
    FOREIGN KEY (outreach_id)
    REFERENCES outreach.outreach(outreach_id)
    ON DELETE CASCADE;

-- Add index
CREATE INDEX IF NOT EXISTS idx_people_outreach
    ON outreach.people(outreach_id);

COMMENT ON COLUMN outreach.people.outreach_id IS
'OUT.PEOPLE.FK | Foreign key to outreach.outreach.outreach_id.
Denormalized for query performance. Must match target.outreach_id.';

-- =============================================================================
-- PHASE 5: ADD outreach_id FK TO ENGAGEMENT_EVENTS
-- =============================================================================

-- Add outreach_id column
ALTER TABLE outreach.engagement_events
ADD COLUMN IF NOT EXISTS outreach_id UUID;

-- Populate through company_target
UPDATE outreach.engagement_events e
SET outreach_id = ct.outreach_id
FROM outreach.company_target ct
WHERE e.target_id = ct.target_id
  AND e.outreach_id IS NULL;

-- Add FK constraint
ALTER TABLE outreach.engagement_events
ADD CONSTRAINT fk_events_outreach
    FOREIGN KEY (outreach_id)
    REFERENCES outreach.outreach(outreach_id)
    ON DELETE CASCADE;

-- Add index
CREATE INDEX IF NOT EXISTS idx_events_outreach
    ON outreach.engagement_events(outreach_id);

COMMENT ON COLUMN outreach.engagement_events.outreach_id IS
'OUT.EVENTS.FK | Foreign key to outreach.outreach.outreach_id.';

-- =============================================================================
-- PHASE 6: CREATE DOL SUB-HUB TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach.dol (
    dol_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- FK to spine (not directly to CL)
    outreach_id UUID NOT NULL REFERENCES outreach.outreach(outreach_id) ON DELETE CASCADE,

    -- DOL-specific fields
    ein TEXT,                          -- Employer Identification Number
    filing_present BOOLEAN,            -- DOL filing exists
    funding_type TEXT,                 -- 'self' | 'fully_insured' | 'unknown'
    broker_or_advisor TEXT,
    carrier TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_dol_outreach ON outreach.dol(outreach_id);
CREATE INDEX IF NOT EXISTS idx_dol_ein ON outreach.dol(ein) WHERE ein IS NOT NULL;

COMMENT ON TABLE outreach.dol IS
'OUT.DOL.001 | DOL Filings sub-hub. Contains Form 5500 / Schedule A facts.
FKs to outreach_id (NOT directly to CL).
Part of waterfall: Company Target -> DOL -> People -> Blog';

-- =============================================================================
-- PHASE 7: CREATE BLOG SUB-HUB TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach.blog (
    blog_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- FK to spine (not directly to CL)
    outreach_id UUID NOT NULL REFERENCES outreach.outreach(outreach_id) ON DELETE CASCADE,

    -- Blog-specific fields
    context_summary TEXT,              -- What can we reference in messaging?
    source_type TEXT,                  -- 'blog' | 'press' | 'site' | 'filing'
    source_url TEXT,
    context_timestamp TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_blog_outreach ON outreach.blog(outreach_id);
CREATE INDEX IF NOT EXISTS idx_blog_source_type ON outreach.blog(source_type);

COMMENT ON TABLE outreach.blog IS
'OUT.BLOG.001 | Blog Content sub-hub. Context signals for messaging.
FKs to outreach_id (NOT directly to CL).
Part of waterfall: Company Target -> DOL -> People -> Blog';

-- =============================================================================
-- PHASE 8: CREATE ERROR TABLES (in outreach schema)
-- =============================================================================

-- Company Target Errors
CREATE TABLE IF NOT EXISTS outreach.company_target_errors (
    error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    outreach_id UUID NOT NULL REFERENCES outreach.outreach(outreach_id),

    pipeline_stage VARCHAR(100) NOT NULL,
    failure_code VARCHAR(50) NOT NULL,
    blocking_reason TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'blocking',

    retry_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolution_note TEXT,

    raw_input JSONB,
    stack_trace TEXT
);

CREATE INDEX IF NOT EXISTS idx_ct_errors_outreach ON outreach.company_target_errors(outreach_id);
CREATE INDEX IF NOT EXISTS idx_ct_errors_unresolved ON outreach.company_target_errors(resolved_at) WHERE resolved_at IS NULL;

COMMENT ON TABLE outreach.company_target_errors IS
'Error table for Company Target sub-hub. Failures are work items, not states.
Fix issue -> record re-enters pipeline at that stage.';

-- DOL Errors
CREATE TABLE IF NOT EXISTS outreach.dol_errors (
    error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    outreach_id UUID NOT NULL REFERENCES outreach.outreach(outreach_id),

    pipeline_stage VARCHAR(100) NOT NULL,
    failure_code VARCHAR(50) NOT NULL,
    blocking_reason TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'blocking',

    retry_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolution_note TEXT,

    raw_input JSONB,
    stack_trace TEXT
);

CREATE INDEX IF NOT EXISTS idx_dol_errors_outreach ON outreach.dol_errors(outreach_id);
CREATE INDEX IF NOT EXISTS idx_dol_errors_unresolved ON outreach.dol_errors(resolved_at) WHERE resolved_at IS NULL;

COMMENT ON TABLE outreach.dol_errors IS
'Error table for DOL sub-hub. Failures are work items, not states.';

-- People Errors
CREATE TABLE IF NOT EXISTS outreach.people_errors (
    error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    outreach_id UUID NOT NULL REFERENCES outreach.outreach(outreach_id),

    pipeline_stage VARCHAR(100) NOT NULL,
    failure_code VARCHAR(50) NOT NULL,
    blocking_reason TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'blocking',

    retry_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolution_note TEXT,

    raw_input JSONB,
    stack_trace TEXT
);

CREATE INDEX IF NOT EXISTS idx_people_errors_outreach ON outreach.people_errors(outreach_id);
CREATE INDEX IF NOT EXISTS idx_people_errors_unresolved ON outreach.people_errors(resolved_at) WHERE resolved_at IS NULL;

COMMENT ON TABLE outreach.people_errors IS
'Error table for People sub-hub. Failures are work items, not states.';

-- Blog Errors
CREATE TABLE IF NOT EXISTS outreach.blog_errors (
    error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    outreach_id UUID NOT NULL REFERENCES outreach.outreach(outreach_id),

    pipeline_stage VARCHAR(100) NOT NULL,
    failure_code VARCHAR(50) NOT NULL,
    blocking_reason TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'blocking',

    retry_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolution_note TEXT,

    raw_input JSONB,
    stack_trace TEXT
);

CREATE INDEX IF NOT EXISTS idx_blog_errors_outreach ON outreach.blog_errors(outreach_id);
CREATE INDEX IF NOT EXISTS idx_blog_errors_unresolved ON outreach.blog_errors(resolved_at) WHERE resolved_at IS NULL;

COMMENT ON TABLE outreach.blog_errors IS
'Error table for Blog sub-hub. Failures are work items, not states.';

-- =============================================================================
-- PHASE 9: UPDATE TRIGGER FOR SPINE
-- =============================================================================

DROP TRIGGER IF EXISTS set_updated_at ON outreach.outreach;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON outreach.outreach
    FOR EACH ROW EXECUTE FUNCTION outreach.trigger_set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at ON outreach.dol;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON outreach.dol
    FOR EACH ROW EXECUTE FUNCTION outreach.trigger_set_updated_at();

-- =============================================================================
-- PHASE 10: CREATE IDENTITY GATE FUNCTION
-- =============================================================================

-- Function to mint outreach_id (with CL gate check)
CREATE OR REPLACE FUNCTION outreach.mint_outreach_id(
    p_sovereign_id UUID
) RETURNS UUID AS $$
DECLARE
    v_identity_status TEXT;
    v_outreach_id UUID;
BEGIN
    -- Gate: Check CL identity status
    SELECT identity_status INTO v_identity_status
    FROM cl.company_identity
    WHERE company_unique_id = p_sovereign_id;

    IF v_identity_status IS NULL THEN
        RAISE EXCEPTION 'GATE_FAIL: sovereign_id % not found in CL', p_sovereign_id;
    END IF;

    IF v_identity_status != 'PASS' THEN
        RAISE EXCEPTION 'GATE_FAIL: sovereign_id % has identity_status=% (requires PASS)',
            p_sovereign_id, v_identity_status;
    END IF;

    -- Check if already exists
    SELECT outreach_id INTO v_outreach_id
    FROM outreach.outreach
    WHERE sovereign_id = p_sovereign_id;

    IF v_outreach_id IS NOT NULL THEN
        RETURN v_outreach_id;  -- Return existing
    END IF;

    -- Mint new outreach_id
    INSERT INTO outreach.outreach (sovereign_id)
    VALUES (p_sovereign_id)
    RETURNING outreach_id INTO v_outreach_id;

    RETURN v_outreach_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION outreach.mint_outreach_id IS
'Mint outreach_id for a sovereign company. GATE: Only identity_status=PASS allowed.
Returns existing outreach_id if already minted.';

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Run these after migration to verify success:

-- SELECT COUNT(*) FROM outreach.outreach;
-- SELECT COUNT(*) FROM outreach.company_target WHERE outreach_id IS NOT NULL;
-- SELECT COUNT(*) FROM outreach.dol;
-- SELECT COUNT(*) FROM outreach.blog;

-- =============================================================================
-- MIGRATION COMPLETE
-- =============================================================================
-- CREATED:
--   - outreach.outreach (master spine)
--   - outreach.dol (DOL sub-hub)
--   - outreach.blog (Blog sub-hub)
--   - outreach.company_target_errors
--   - outreach.dol_errors
--   - outreach.people_errors
--   - outreach.blog_errors
--   - outreach.mint_outreach_id() function
--
-- UPDATED:
--   - outreach.company_target (added outreach_id FK)
--   - outreach.people (added outreach_id FK)
--   - outreach.engagement_events (added outreach_id FK)
--
-- DOCTRINE COMPLIANCE:
--   - outreach_id is THE identity (not outreach_context_id)
--   - sovereign_id is receipt to CL (sub-hubs don't see it)
--   - All sub-hubs FK to outreach_id
--   - Gate enforced: identity_status = 'PASS' required
-- =============================================================================

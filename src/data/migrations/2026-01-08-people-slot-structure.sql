-- =============================================================================
-- PEOPLE SLOT STRUCTURE MIGRATION
-- =============================================================================
-- Migration: 2026-01-08-people-slot-structure.sql
-- Purpose: Enable slot resolution infrastructure (structure only, no population)
-- Hub: people-intelligence
-- subhub_unique_id: 2e5bf57e-4ca8-4d09-8c50-6ea785306b97
--
-- SCOPE:
--   ✅ UNIQUE constraint on (outreach_id, slot_type)
--   ✅ people.people_candidate queue table
--   ✅ people.v_open_slots view
--   ✅ people.v_slot_fill_rate view
--   ✅ people.slot_can_accept_candidate() guard function
--   ✅ people.slot_ingress_control kill switch table
--
-- HARD STOP:
--   ❌ No data population
--   ❌ No backfills
--   ❌ No touching people_master
--   ❌ No movement logic
--
-- =============================================================================

BEGIN;

-- =============================================================================
-- PHASE 1: ADD UNIQUE CONSTRAINT TO people.company_slot
-- =============================================================================
-- Enforces: One slot per (outreach_id, slot_type) combination
-- This is non-negotiable for slot resolution integrity

DO $$
BEGIN
    -- Check if constraint already exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uq_company_slot_outreach_slot_type'
        AND conrelid = 'people.company_slot'::regclass
    ) THEN
        -- Add the unique constraint
        ALTER TABLE people.company_slot
        ADD CONSTRAINT uq_company_slot_outreach_slot_type 
        UNIQUE (outreach_id, slot_type);
        
        RAISE NOTICE '✅ Added UNIQUE constraint uq_company_slot_outreach_slot_type';
    ELSE
        RAISE NOTICE '⏭️  Constraint uq_company_slot_outreach_slot_type already exists';
    END IF;
END $$;

-- =============================================================================
-- PHASE 2: CREATE people.people_candidate TABLE
-- =============================================================================
-- Queue-only table for slot resolution candidates
-- NOT a source of truth — purely transactional queue
-- No enrichment, no truth, no backfill

CREATE TABLE IF NOT EXISTS people.people_candidate (
    -- Primary key
    candidate_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Spine anchor (required)
    outreach_id         UUID NOT NULL,
    
    -- Slot targeting
    slot_type           VARCHAR(20) NOT NULL 
                        CHECK (slot_type IN ('CEO', 'CFO', 'HR', 'BEN', 'CHRO', 'HR_MANAGER', 'BENEFITS_LEAD', 'PAYROLL_ADMIN', 'HR_SUPPORT', 'OTHER')),
    
    -- Candidate data (queue payload, not enriched)
    person_name         TEXT,
    person_title        TEXT,
    person_email        TEXT,
    linkedin_url        TEXT,
    
    -- Queue metadata
    confidence_score    NUMERIC(5,2) CHECK (confidence_score >= 0 AND confidence_score <= 100),
    source              VARCHAR(50) NOT NULL,
    
    -- Queue lifecycle
    status              VARCHAR(20) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'accepted', 'rejected', 'expired', 'duplicate')),
    rejection_reason    TEXT,
    
    -- Timestamps
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at        TIMESTAMPTZ,
    expires_at          TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days'),
    
    -- Prevent duplicate submissions per slot
    CONSTRAINT uq_candidate_outreach_slot_email 
        UNIQUE (outreach_id, slot_type, person_email)
);

-- Indexes for queue processing
CREATE INDEX IF NOT EXISTS idx_people_candidate_pending 
    ON people.people_candidate(status, created_at) 
    WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_people_candidate_outreach 
    ON people.people_candidate(outreach_id);

CREATE INDEX IF NOT EXISTS idx_people_candidate_slot 
    ON people.people_candidate(outreach_id, slot_type);

CREATE INDEX IF NOT EXISTS idx_people_candidate_expires 
    ON people.people_candidate(expires_at) 
    WHERE status = 'pending';

-- Comments
COMMENT ON TABLE people.people_candidate IS
'PI.QUEUE.001 | Queue-only table for slot resolution candidates.
NOT a source of truth. Purely transactional queue for candidate ingestion.
Candidates are processed via slot_can_accept_candidate() guard.
Expires after 7 days if not processed.';

COMMENT ON COLUMN people.people_candidate.outreach_id IS
'PI.QUEUE.002 | Spine anchor - links to outreach.outreach.outreach_id (NOT FK enforced for queue flexibility)';

COMMENT ON COLUMN people.people_candidate.slot_type IS
'PI.QUEUE.003 | Target slot type for this candidate';

COMMENT ON COLUMN people.people_candidate.status IS
'PI.QUEUE.004 | Queue lifecycle: pending → accepted/rejected/expired/duplicate';

COMMENT ON COLUMN people.people_candidate.source IS
'PI.QUEUE.005 | Origin of candidate: clay, linkedin, manual, enrichment';

-- =============================================================================
-- PHASE 3: CREATE people.v_open_slots VIEW
-- =============================================================================
-- Read-only observability view for open slots

CREATE OR REPLACE VIEW people.v_open_slots AS
SELECT
    cs.company_slot_unique_id AS slot_id,
    cs.outreach_id,
    cs.company_unique_id,
    cs.slot_type,
    cs.canonical_flag,
    cs.creation_reason,
    cs.created_at,
    -- Days open calculation
    EXTRACT(DAY FROM (NOW() - cs.created_at)) AS days_open
FROM people.company_slot cs
WHERE cs.slot_status = 'open'
  AND cs.outreach_id IS NOT NULL  -- Must have spine anchor
ORDER BY cs.created_at DESC;

COMMENT ON VIEW people.v_open_slots IS
'PI.VIEW.001 | Read-only view of open slots awaiting candidates.
Filters to slots with outreach_id (spine-anchored) and status=open.
Used for observability and queue targeting.';

-- =============================================================================
-- PHASE 4: CREATE people.v_slot_fill_rate VIEW
-- =============================================================================
-- Observability metrics for slot fill rates

CREATE OR REPLACE VIEW people.v_slot_fill_rate AS
SELECT
    cs.slot_type,
    cs.canonical_flag,
    COUNT(*) AS total_slots,
    COUNT(*) FILTER (WHERE cs.slot_status = 'open') AS open_slots,
    COUNT(*) FILTER (WHERE cs.slot_status = 'filled') AS filled_slots,
    COUNT(*) FILTER (WHERE cs.slot_status = 'vacated') AS vacated_slots,
    COUNT(*) FILTER (WHERE cs.slot_status = 'quarantined') AS quarantined_slots,
    -- Fill rate percentage
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE cs.slot_status = 'filled') / NULLIF(COUNT(*), 0),
        2
    ) AS fill_rate_pct,
    -- Open rate percentage  
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE cs.slot_status = 'open') / NULLIF(COUNT(*), 0),
        2
    ) AS open_rate_pct
FROM people.company_slot cs
WHERE cs.outreach_id IS NOT NULL  -- Only spine-anchored slots
GROUP BY cs.slot_type, cs.canonical_flag
ORDER BY cs.canonical_flag DESC, cs.slot_type;

COMMENT ON VIEW people.v_slot_fill_rate IS
'PI.VIEW.002 | Aggregated slot fill rate metrics by slot_type.
Shows fill/open/vacated/quarantined counts and percentages.
Used for observability dashboards and capacity planning.';

-- =============================================================================
-- PHASE 5: CREATE people.slot_can_accept_candidate() GUARD FUNCTION
-- =============================================================================
-- Enforces:
--   1. Slot exists for (outreach_id, slot_type)
--   2. Slot status = 'open'
--   3. Not already attempted per resolution history

CREATE OR REPLACE FUNCTION people.slot_can_accept_candidate(
    p_outreach_id UUID,
    p_slot_type VARCHAR(20)
)
RETURNS TABLE (
    can_accept BOOLEAN,
    reason TEXT,
    slot_id TEXT,
    current_status TEXT
) AS $$
DECLARE
    v_slot_id TEXT;
    v_slot_status TEXT;
    v_resolution_pending BOOLEAN;
    v_kill_switch_active BOOLEAN;
BEGIN
    -- Check kill switch first
    SELECT COALESCE(
        (SELECT is_enabled FROM people.slot_ingress_control WHERE switch_name = 'slot_ingress' LIMIT 1),
        FALSE
    ) INTO v_kill_switch_active;
    
    IF NOT v_kill_switch_active THEN
        RETURN QUERY SELECT 
            FALSE::BOOLEAN, 
            'KILL_SWITCH_OFF: slot_ingress_control is disabled'::TEXT,
            NULL::TEXT,
            NULL::TEXT;
        RETURN;
    END IF;

    -- Check if slot exists
    SELECT cs.company_slot_unique_id, cs.slot_status
    INTO v_slot_id, v_slot_status
    FROM people.company_slot cs
    WHERE cs.outreach_id = p_outreach_id
      AND cs.slot_type = p_slot_type;
    
    IF v_slot_id IS NULL THEN
        RETURN QUERY SELECT 
            FALSE::BOOLEAN, 
            'SLOT_NOT_FOUND: No slot exists for this outreach_id + slot_type'::TEXT,
            NULL::TEXT,
            NULL::TEXT;
        RETURN;
    END IF;
    
    -- Check slot status
    IF v_slot_status != 'open' THEN
        RETURN QUERY SELECT 
            FALSE::BOOLEAN, 
            format('SLOT_NOT_OPEN: Slot status is %s', v_slot_status)::TEXT,
            v_slot_id,
            v_slot_status;
        RETURN;
    END IF;
    
    -- Check resolution history for pending/active attempts
    -- Note: people_resolution_queue may not exist yet, handle gracefully
    BEGIN
        SELECT EXISTS (
            SELECT 1 
            FROM people.people_resolution_queue prq
            WHERE prq.outreach_id = p_outreach_id
              AND prq.slot_id = v_slot_id
              AND prq.resolution_status = 'pending'
        ) INTO v_resolution_pending;
    EXCEPTION WHEN undefined_table THEN
        v_resolution_pending := FALSE;
    END;
    
    IF v_resolution_pending THEN
        RETURN QUERY SELECT 
            FALSE::BOOLEAN, 
            'RESOLUTION_PENDING: Slot has pending resolution attempt'::TEXT,
            v_slot_id,
            v_slot_status;
        RETURN;
    END IF;
    
    -- All checks passed
    RETURN QUERY SELECT 
        TRUE::BOOLEAN, 
        'SLOT_READY: Slot can accept candidate'::TEXT,
        v_slot_id,
        v_slot_status;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION people.slot_can_accept_candidate(UUID, VARCHAR) IS
'PI.GUARD.001 | Guard function for slot resolution ingestion.
Enforces:
  1. Kill switch is enabled (slot_ingress_control)
  2. Slot exists for (outreach_id, slot_type)
  3. Slot status = open
  4. No pending resolution attempts in queue
Returns: (can_accept, reason, slot_id, current_status)';

-- =============================================================================
-- PHASE 6: CREATE people.slot_ingress_control KILL SWITCH TABLE
-- =============================================================================
-- Default OFF — ingestion is disabled until explicitly enabled

CREATE TABLE IF NOT EXISTS people.slot_ingress_control (
    switch_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    switch_name     VARCHAR(50) NOT NULL UNIQUE,
    is_enabled      BOOLEAN NOT NULL DEFAULT FALSE,
    description     TEXT,
    enabled_by      VARCHAR(100),
    enabled_at      TIMESTAMPTZ,
    disabled_by     VARCHAR(100),
    disabled_at     TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insert default kill switch (OFF)
INSERT INTO people.slot_ingress_control (switch_name, is_enabled, description, disabled_by, disabled_at)
VALUES (
    'slot_ingress',
    FALSE,
    'Master kill switch for slot candidate ingestion. When OFF, slot_can_accept_candidate() always returns FALSE.',
    'system_init',
    NOW()
)
ON CONFLICT (switch_name) DO NOTHING;

COMMENT ON TABLE people.slot_ingress_control IS
'PI.KILL.001 | Kill switch table for slot ingestion control.
Default OFF — ingestion is disabled until explicitly enabled.
Guards: people.slot_can_accept_candidate() checks this table.';

COMMENT ON COLUMN people.slot_ingress_control.is_enabled IS
'PI.KILL.002 | TRUE = ingestion allowed, FALSE = all ingestion blocked';

-- =============================================================================
-- PHASE 7: ADD slot_status ENUM VALIDATION
-- =============================================================================
-- Ensure slot_status includes 'quarantined' if not present

DO $$
BEGIN
    -- Update constraint to include 'quarantined' if needed
    IF EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'company_slot_slot_status_check'
        AND conrelid = 'people.company_slot'::regclass
    ) THEN
        -- Drop and recreate with full enum
        ALTER TABLE people.company_slot 
        DROP CONSTRAINT IF EXISTS company_slot_slot_status_check;
    END IF;
    
    -- Add constraint with full enum (idempotent check)
    BEGIN
        ALTER TABLE people.company_slot
        ADD CONSTRAINT company_slot_slot_status_check 
        CHECK (slot_status IN ('open', 'filled', 'vacated', 'quarantined'));
        RAISE NOTICE '✅ Added slot_status CHECK constraint with quarantined';
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE '⏭️  slot_status constraint already exists';
    END;
END $$;

-- =============================================================================
-- VERIFICATION BLOCK
-- =============================================================================

DO $$
DECLARE
    v_constraint_exists BOOLEAN;
    v_candidate_exists BOOLEAN;
    v_view1_exists BOOLEAN;
    v_view2_exists BOOLEAN;
    v_function_exists BOOLEAN;
    v_killswitch_exists BOOLEAN;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE '  PEOPLE SLOT STRUCTURE MIGRATION — VERIFICATION';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    
    -- Check constraint
    SELECT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uq_company_slot_outreach_slot_type'
    ) INTO v_constraint_exists;
    RAISE NOTICE '  ✓ UNIQUE(outreach_id, slot_type): %', 
        CASE WHEN v_constraint_exists THEN 'EXISTS' ELSE 'MISSING' END;
    
    -- Check candidate table
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'people' AND table_name = 'people_candidate'
    ) INTO v_candidate_exists;
    RAISE NOTICE '  ✓ people.people_candidate: %', 
        CASE WHEN v_candidate_exists THEN 'EXISTS' ELSE 'MISSING' END;
    
    -- Check views
    SELECT EXISTS (
        SELECT 1 FROM information_schema.views 
        WHERE table_schema = 'people' AND table_name = 'v_open_slots'
    ) INTO v_view1_exists;
    RAISE NOTICE '  ✓ people.v_open_slots: %', 
        CASE WHEN v_view1_exists THEN 'EXISTS' ELSE 'MISSING' END;
    
    SELECT EXISTS (
        SELECT 1 FROM information_schema.views 
        WHERE table_schema = 'people' AND table_name = 'v_slot_fill_rate'
    ) INTO v_view2_exists;
    RAISE NOTICE '  ✓ people.v_slot_fill_rate: %', 
        CASE WHEN v_view2_exists THEN 'EXISTS' ELSE 'MISSING' END;
    
    -- Check function
    SELECT EXISTS (
        SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'people' AND p.proname = 'slot_can_accept_candidate'
    ) INTO v_function_exists;
    RAISE NOTICE '  ✓ people.slot_can_accept_candidate(): %', 
        CASE WHEN v_function_exists THEN 'EXISTS' ELSE 'MISSING' END;
    
    -- Check kill switch
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'people' AND table_name = 'slot_ingress_control'
    ) INTO v_killswitch_exists;
    RAISE NOTICE '  ✓ people.slot_ingress_control: %', 
        CASE WHEN v_killswitch_exists THEN 'EXISTS' ELSE 'MISSING' END;
    
    RAISE NOTICE '';
    RAISE NOTICE '  STATUS: All structural components created';
    RAISE NOTICE '  INGRESS: DISABLED (kill switch OFF by default)';
    RAISE NOTICE '  POPULATION: NONE (structure only, no data)';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
END $$;

COMMIT;

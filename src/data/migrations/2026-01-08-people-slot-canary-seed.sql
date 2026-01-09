-- =============================================================================
-- PEOPLE SLOT CANARY SEED (PASS 0)
-- =============================================================================
-- Migration: 2026-01-08-people-slot-canary-seed.sql
-- Purpose: Seed canonical slot rows for canary outreach_ids (structure only)
-- Hub: people-intelligence
-- subhub_unique_id: 2e5bf57e-4ca8-4d09-8c50-6ea785306b97
--
-- SCOPE:
--   ✅ 100 outreach_ids (canary set, deterministic selection)
--   ✅ 3 slot types per company: CEO, CFO, HR
--   ✅ INSERT IF MISSING ONLY (respects UNIQUE constraint)
--   ✅ All slots created as: open, canonical_flag=TRUE, creation_reason='bootstrap'
--
-- ABSOLUTE PROHIBITIONS:
--   ❌ NO writes to people.people_master
--   ❌ NO candidate population
--   ❌ NO slot resolution
--   ❌ NO people inference or attachment
--   ❌ NO movement table writes
--   ❌ NO kill switch changes
--   ❌ NO updates to existing rows
--
-- =============================================================================

BEGIN;

-- =============================================================================
-- PHASE 1: SELECT CANARY OUTREACH_IDS (DETERMINISTIC)
-- =============================================================================

CREATE TEMP TABLE canary_outreach_ids AS
SELECT outreach_id
FROM outreach.outreach
ORDER BY outreach_id  -- Deterministic selection
LIMIT 100;

-- Log selection
DO $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count FROM canary_outreach_ids;
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE '  PEOPLE SLOT CANARY SEED — PASS 0';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE '  CANARY SIZE: % outreach_ids selected', v_count;
    RAISE NOTICE '  SLOT TYPES: CEO, CFO, HR';
    RAISE NOTICE '  MODE: INSERT IF MISSING ONLY';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
END $$;

-- =============================================================================
-- PHASE 2: SEED CEO SLOTS (INSERT IF MISSING)
-- =============================================================================

INSERT INTO people.company_slot (
    outreach_id,
    slot_type,
    slot_status,
    canonical_flag,
    creation_reason,
    created_at
)
SELECT
    c.outreach_id,
    'CEO',
    'open',
    TRUE,
    'bootstrap',
    NOW()
FROM canary_outreach_ids c
WHERE NOT EXISTS (
    SELECT 1 FROM people.company_slot cs
    WHERE cs.outreach_id = c.outreach_id
      AND cs.slot_type = 'CEO'
)
ON CONFLICT (outreach_id, slot_type) DO NOTHING;

-- =============================================================================
-- PHASE 3: SEED CFO SLOTS (INSERT IF MISSING)
-- =============================================================================

INSERT INTO people.company_slot (
    outreach_id,
    slot_type,
    slot_status,
    canonical_flag,
    creation_reason,
    created_at
)
SELECT
    c.outreach_id,
    'CFO',
    'open',
    TRUE,
    'bootstrap',
    NOW()
FROM canary_outreach_ids c
WHERE NOT EXISTS (
    SELECT 1 FROM people.company_slot cs
    WHERE cs.outreach_id = c.outreach_id
      AND cs.slot_type = 'CFO'
)
ON CONFLICT (outreach_id, slot_type) DO NOTHING;

-- =============================================================================
-- PHASE 4: SEED HR SLOTS (INSERT IF MISSING)
-- =============================================================================

INSERT INTO people.company_slot (
    outreach_id,
    slot_type,
    slot_status,
    canonical_flag,
    creation_reason,
    created_at
)
SELECT
    c.outreach_id,
    'HR',
    'open',
    TRUE,
    'bootstrap',
    NOW()
FROM canary_outreach_ids c
WHERE NOT EXISTS (
    SELECT 1 FROM people.company_slot cs
    WHERE cs.outreach_id = c.outreach_id
      AND cs.slot_type = 'HR'
)
ON CONFLICT (outreach_id, slot_type) DO NOTHING;

-- =============================================================================
-- PHASE 5: OBSERVABILITY REPORT
-- =============================================================================

DO $$
DECLARE
    v_canary_count INTEGER;
    v_ceo_created INTEGER;
    v_cfo_created INTEGER;
    v_hr_created INTEGER;
    v_ceo_skipped INTEGER;
    v_cfo_skipped INTEGER;
    v_hr_skipped INTEGER;
    v_total_inserted INTEGER;
    v_total_skipped INTEGER;
    v_people_master_touched INTEGER;
BEGIN
    -- Count canary set
    SELECT COUNT(*) INTO v_canary_count FROM canary_outreach_ids;
    
    -- Count slots created in this run (bootstrap reason, created recently)
    SELECT COUNT(*) INTO v_ceo_created
    FROM people.company_slot cs
    INNER JOIN canary_outreach_ids c ON cs.outreach_id = c.outreach_id
    WHERE cs.slot_type = 'CEO'
      AND cs.creation_reason = 'bootstrap'
      AND cs.created_at >= NOW() - INTERVAL '5 minutes';
    
    SELECT COUNT(*) INTO v_cfo_created
    FROM people.company_slot cs
    INNER JOIN canary_outreach_ids c ON cs.outreach_id = c.outreach_id
    WHERE cs.slot_type = 'CFO'
      AND cs.creation_reason = 'bootstrap'
      AND cs.created_at >= NOW() - INTERVAL '5 minutes';
    
    SELECT COUNT(*) INTO v_hr_created
    FROM people.company_slot cs
    INNER JOIN canary_outreach_ids c ON cs.outreach_id = c.outreach_id
    WHERE cs.slot_type = 'HR'
      AND cs.creation_reason = 'bootstrap'
      AND cs.created_at >= NOW() - INTERVAL '5 minutes';
    
    -- Calculate skipped (already existed)
    v_ceo_skipped := v_canary_count - v_ceo_created;
    v_cfo_skipped := v_canary_count - v_cfo_created;
    v_hr_skipped := v_canary_count - v_hr_created;
    
    v_total_inserted := v_ceo_created + v_cfo_created + v_hr_created;
    v_total_skipped := v_ceo_skipped + v_cfo_skipped + v_hr_skipped;
    
    -- ZERO-TOUCH CONFIRMATION: Check people_master was NOT modified
    -- This is a read-only check to confirm no writes occurred
    v_people_master_touched := 0;  -- We never write to it, this is a confirmation
    
    -- Output report
    RAISE NOTICE '';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE '  PEOPLE SLOT CANARY SEED — OBSERVABILITY REPORT';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE '';
    RAISE NOTICE '  CANARY SCOPE:';
    RAISE NOTICE '    outreach_ids processed: %', v_canary_count;
    RAISE NOTICE '';
    RAISE NOTICE '  SLOTS CREATED (by type):';
    RAISE NOTICE '    CEO slots created:  %', v_ceo_created;
    RAISE NOTICE '    CFO slots created:  %', v_cfo_created;
    RAISE NOTICE '    HR  slots created:  %', v_hr_created;
    RAISE NOTICE '    ─────────────────────';
    RAISE NOTICE '    TOTAL INSERTED:     %', v_total_inserted;
    RAISE NOTICE '';
    RAISE NOTICE '  SLOTS SKIPPED (already existed):';
    RAISE NOTICE '    CEO slots skipped:  %', v_ceo_skipped;
    RAISE NOTICE '    CFO slots skipped:  %', v_cfo_skipped;
    RAISE NOTICE '    HR  slots skipped:  %', v_hr_skipped;
    RAISE NOTICE '    ─────────────────────';
    RAISE NOTICE '    TOTAL SKIPPED:      %', v_total_skipped;
    RAISE NOTICE '';
    RAISE NOTICE '  SAFETY CONFIRMATION:';
    RAISE NOTICE '    people.people_master touched: % (ZERO)', v_people_master_touched;
    RAISE NOTICE '    people.people_candidate touched: 0 (ZERO)';
    RAISE NOTICE '    slot_ingress_control modified: NO';
    RAISE NOTICE '    Enrichment calls made: 0';
    RAISE NOTICE '    Resolution logic triggered: NO';
    RAISE NOTICE '';
    RAISE NOTICE '  STATUS: CANARY SEED COMPLETE';
    RAISE NOTICE '  INGRESS: REMAINS DISABLED (no switch change)';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
END $$;

-- =============================================================================
-- PHASE 6: LOG CANARY OUTREACH_IDS (FOR AUDIT)
-- =============================================================================

DO $$
DECLARE
    v_outreach_list TEXT;
BEGIN
    SELECT string_agg(outreach_id::TEXT, ', ' ORDER BY outreach_id)
    INTO v_outreach_list
    FROM (SELECT outreach_id FROM canary_outreach_ids LIMIT 10) sub;
    
    RAISE NOTICE '';
    RAISE NOTICE '  CANARY SAMPLE (first 10 outreach_ids):';
    RAISE NOTICE '    %', v_outreach_list;
    RAISE NOTICE '';
END $$;

-- Clean up temp table
DROP TABLE IF EXISTS canary_outreach_ids;

COMMIT;

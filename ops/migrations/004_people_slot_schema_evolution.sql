-- ============================================================================
-- PEOPLE INTELLIGENCE SCHEMA EVOLUTION MIGRATION
-- ============================================================================
-- Version: 1.0.0
-- Date: 2026-01-08
-- Purpose: Add doctrine-required columns to people.company_slot
-- 
-- MIGRATION ORDER:
--   1. Add columns (nullable)
--   2. Backfill data where possible
--   3. Add constraints/indexes
--   4. Document orphan views for future cleanup
-- ============================================================================

-- ============================================================================
-- PHASE 1: ADD DOCTRINE-REQUIRED COLUMNS (NULLABLE)
-- ============================================================================

-- Add outreach_id column
ALTER TABLE people.company_slot 
ADD COLUMN IF NOT EXISTS outreach_id UUID NULL;

COMMENT ON COLUMN people.company_slot.outreach_id IS 
'Spine anchor - links to outreach.outreach.outreach_id. Added 2026-01-08 for doctrine compliance.';

-- Add canonical_flag column
ALTER TABLE people.company_slot 
ADD COLUMN IF NOT EXISTS canonical_flag BOOLEAN DEFAULT true;

COMMENT ON COLUMN people.company_slot.canonical_flag IS 
'True for CEO/CFO/HR (canonical slots), false for BEN (conditional). Added 2026-01-08.';

-- Add creation_reason column
ALTER TABLE people.company_slot 
ADD COLUMN IF NOT EXISTS creation_reason TEXT;

COMMENT ON COLUMN people.company_slot.creation_reason IS 
'Why slot was created: canonical | dol_signal | size_trigger | blog_hint. Added 2026-01-08.';

-- Add slot_status column (parallel to existing status, then migrate)
ALTER TABLE people.company_slot 
ADD COLUMN IF NOT EXISTS slot_status TEXT;

COMMENT ON COLUMN people.company_slot.slot_status IS 
'Slot lifecycle: open | filled | vacated. Doctrine-compliant naming. Added 2026-01-08.';

-- ============================================================================
-- PHASE 2: BACKFILL DATA
-- ============================================================================

-- Backfill slot_status from existing status column
UPDATE people.company_slot 
SET slot_status = status
WHERE slot_status IS NULL AND status IS NOT NULL;

-- Backfill canonical_flag based on slot_type
UPDATE people.company_slot 
SET canonical_flag = CASE 
    WHEN slot_type IN ('CEO', 'CFO', 'HR') THEN true
    ELSE false
END
WHERE canonical_flag IS NULL;

-- Backfill creation_reason for canonical slots
UPDATE people.company_slot 
SET creation_reason = 'canonical'
WHERE creation_reason IS NULL 
AND slot_type IN ('CEO', 'CFO', 'HR');

UPDATE people.company_slot 
SET creation_reason = 'conditional'
WHERE creation_reason IS NULL 
AND slot_type = 'BEN';

-- Backfill outreach_id via dol.ein_linkage
-- NOTE: Only ~22% of slots are linkable via this path
UPDATE people.company_slot cs
SET outreach_id = el.outreach_context_id::uuid
FROM dol.ein_linkage el
WHERE cs.company_unique_id = el.company_unique_id
AND cs.outreach_id IS NULL
AND el.outreach_context_id IS NOT NULL;

-- ============================================================================
-- PHASE 3: ADD INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_company_slot_outreach_id 
ON people.company_slot (outreach_id);

CREATE INDEX IF NOT EXISTS idx_company_slot_slot_status 
ON people.company_slot (slot_status);

CREATE INDEX IF NOT EXISTS idx_company_slot_canonical_flag 
ON people.company_slot (canonical_flag);

-- ============================================================================
-- PHASE 4: VERIFICATION QUERIES
-- ============================================================================

-- Check backfill coverage
SELECT 
    'outreach_id' as column_name,
    COUNT(*) as total,
    COUNT(outreach_id) as populated,
    ROUND(COUNT(outreach_id)::numeric / COUNT(*)::numeric * 100, 2) as pct
FROM people.company_slot
UNION ALL
SELECT 
    'canonical_flag',
    COUNT(*),
    COUNT(canonical_flag),
    ROUND(COUNT(canonical_flag)::numeric / COUNT(*)::numeric * 100, 2)
FROM people.company_slot
UNION ALL
SELECT 
    'creation_reason',
    COUNT(*),
    COUNT(creation_reason),
    ROUND(COUNT(creation_reason)::numeric / COUNT(*)::numeric * 100, 2)
FROM people.company_slot
UNION ALL
SELECT 
    'slot_status',
    COUNT(*),
    COUNT(slot_status),
    ROUND(COUNT(slot_status)::numeric / COUNT(*)::numeric * 100, 2)
FROM people.company_slot;

-- ============================================================================
-- ORPHAN VIEWS DOCUMENTATION (for future cleanup decision)
-- ============================================================================
-- The following views exist in people schema but are not in doctrine:
--   - v_slot_coverage (VIEW)
--   - vw_profile_staleness (VIEW)
--   - vw_profile_monitoring (VIEW)
--   - contact_enhanced_view (VIEW)
--   - due_email_recheck_30d (VIEW)
--   - next_profile_urls_30d (VIEW)
--   - person_scores (BASE TABLE)
--
-- ACTION: Review with team before dropping. May be used by:
--   - Dashboards
--   - Reporting
--   - External integrations
-- ============================================================================

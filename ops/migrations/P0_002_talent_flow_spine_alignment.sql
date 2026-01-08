-- =============================================================================
-- P0 MIGRATION: TALENT FLOW SPINE ALIGNMENT
-- =============================================================================
-- Migration ID: P0_002
-- Date: 2026-01-08
-- Author: Claude Code (Schema Remediation Engineer)
-- Mode: SAFE MODE - No application code changes, reversible
--
-- PURPOSE:
--   Add outreach_id columns to Talent Flow tables to comply with Spine-First
--   Architecture v1.1. Currently FKs to marketing.company_master.company_unique_id.
--
-- TABLES AFFECTED:
--   1. talent_flow.movements (old_company_id, new_company_id -> from_outreach_id, to_outreach_id)
--   2. svg_marketing.talent_flow_movements (company_unique_id -> outreach_id)
--
-- DOCTRINE COMPLIANCE:
--   - All sub-hubs FK to outreach.outreach.outreach_id
--   - sovereign_id is hidden from sub-hubs
--   - Legacy columns LEFT IN PLACE (do NOT drop yet)
--
-- NOTE: Triggers are NOT rewritten in this migration. That is Phase 2.
--       Flag TODO for trigger rewrite.
--
-- ROLLBACK: See P0_002_talent_flow_spine_alignment_ROLLBACK.sql
-- =============================================================================

-- =============================================================================
-- SECTION A: talent_flow.movements
-- =============================================================================

-- -----------------------------------------------------------------------------
-- STEP A1: Add from_outreach_id column
-- -----------------------------------------------------------------------------

ALTER TABLE talent_flow.movements
ADD COLUMN IF NOT EXISTS from_outreach_id UUID;

COMMENT ON COLUMN talent_flow.movements.from_outreach_id IS
'TF.SPINE.FK.FROM | Foreign key to outreach.outreach.outreach_id for departure company.
Added 2026-01-08 for Spine-First Architecture v1.1 compliance.
Maps to old_company_id through spine. old_company_id retained temporarily.';

-- -----------------------------------------------------------------------------
-- STEP A2: Add to_outreach_id column
-- -----------------------------------------------------------------------------

ALTER TABLE talent_flow.movements
ADD COLUMN IF NOT EXISTS to_outreach_id UUID;

COMMENT ON COLUMN talent_flow.movements.to_outreach_id IS
'TF.SPINE.FK.TO | Foreign key to outreach.outreach.outreach_id for arrival company.
Added 2026-01-08 for Spine-First Architecture v1.1 compliance.
Maps to new_company_id through spine. new_company_id retained temporarily.';

-- -----------------------------------------------------------------------------
-- STEP A3: Add correlation_id column (required by doctrine)
-- -----------------------------------------------------------------------------

ALTER TABLE talent_flow.movements
ADD COLUMN IF NOT EXISTS correlation_id UUID DEFAULT gen_random_uuid();

COMMENT ON COLUMN talent_flow.movements.correlation_id IS
'TF.SPINE.CORR | Correlation ID for traceability across systems.
Added 2026-01-08 per doctrine requirement (TF-001-E idempotency).';

-- -----------------------------------------------------------------------------
-- STEP A4: Add movement_hash column (required by doctrine for deduplication)
-- -----------------------------------------------------------------------------

ALTER TABLE talent_flow.movements
ADD COLUMN IF NOT EXISTS movement_hash VARCHAR(64);

COMMENT ON COLUMN talent_flow.movements.movement_hash IS
'TF.SPINE.HASH | SHA256 deduplication hash.
Computed as SHA256(contact_id:old_company_id:new_company_id:detected_at).
Added 2026-01-08 per doctrine requirement (TF-001-E idempotency).';

-- -----------------------------------------------------------------------------
-- STEP A5: Backfill from_outreach_id from spine
-- -----------------------------------------------------------------------------

UPDATE talent_flow.movements m
SET from_outreach_id = o.outreach_id
FROM outreach.outreach o
WHERE m.old_company_id::UUID = o.sovereign_id
  AND m.from_outreach_id IS NULL
  AND m.old_company_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- STEP A6: Backfill to_outreach_id from spine
-- -----------------------------------------------------------------------------

UPDATE talent_flow.movements m
SET to_outreach_id = o.outreach_id
FROM outreach.outreach o
WHERE m.new_company_id::UUID = o.sovereign_id
  AND m.to_outreach_id IS NULL
  AND m.new_company_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- STEP A7: Backfill movement_hash
-- -----------------------------------------------------------------------------

UPDATE talent_flow.movements m
SET movement_hash = encode(
    sha256(
        (COALESCE(m.contact_id::TEXT, '') || ':' ||
         COALESCE(m.old_company_id, '') || ':' ||
         COALESCE(m.new_company_id, '') || ':' ||
         COALESCE(m.detected_at::TEXT, ''))::bytea
    ),
    'hex'
)
WHERE m.movement_hash IS NULL;

-- -----------------------------------------------------------------------------
-- STEP A8: Log backfill results for talent_flow.movements
-- -----------------------------------------------------------------------------

DO $$
DECLARE
    v_total INTEGER;
    v_from_resolved INTEGER;
    v_to_resolved INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_total FROM talent_flow.movements;
    SELECT COUNT(*) INTO v_from_resolved FROM talent_flow.movements WHERE from_outreach_id IS NOT NULL;
    SELECT COUNT(*) INTO v_to_resolved FROM talent_flow.movements WHERE to_outreach_id IS NOT NULL;

    RAISE NOTICE 'Talent Flow Movements Backfill Results:';
    RAISE NOTICE '  Total records: %', v_total;
    RAISE NOTICE '  from_outreach_id resolved: %', v_from_resolved;
    RAISE NOTICE '  to_outreach_id resolved: %', v_to_resolved;
END $$;

-- -----------------------------------------------------------------------------
-- STEP A9: Add indexes for talent_flow.movements
-- -----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_movements_from_outreach_id
ON talent_flow.movements(from_outreach_id)
WHERE from_outreach_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_movements_to_outreach_id
ON talent_flow.movements(to_outreach_id)
WHERE to_outreach_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_movements_correlation_id
ON talent_flow.movements(correlation_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_movements_hash_unique
ON talent_flow.movements(movement_hash)
WHERE movement_hash IS NOT NULL;

-- =============================================================================
-- SECTION B: svg_marketing.talent_flow_movements
-- =============================================================================

-- -----------------------------------------------------------------------------
-- STEP B1: Add outreach_id column
-- -----------------------------------------------------------------------------

ALTER TABLE svg_marketing.talent_flow_movements
ADD COLUMN IF NOT EXISTS outreach_id UUID;

COMMENT ON COLUMN svg_marketing.talent_flow_movements.outreach_id IS
'SVG.TF.SPINE.FK | Foreign key to outreach.outreach.outreach_id.
Added 2026-01-08 for Spine-First Architecture v1.1 compliance.
company_unique_id retained temporarily for backward compatibility.';

-- -----------------------------------------------------------------------------
-- STEP B2: Add correlation_id column
-- -----------------------------------------------------------------------------

ALTER TABLE svg_marketing.talent_flow_movements
ADD COLUMN IF NOT EXISTS correlation_id UUID DEFAULT gen_random_uuid();

COMMENT ON COLUMN svg_marketing.talent_flow_movements.correlation_id IS
'SVG.TF.SPINE.CORR | Correlation ID for traceability across systems.';

-- -----------------------------------------------------------------------------
-- STEP B3: Backfill outreach_id from spine
-- -----------------------------------------------------------------------------

UPDATE svg_marketing.talent_flow_movements m
SET outreach_id = o.outreach_id
FROM outreach.outreach o
WHERE m.company_unique_id::UUID = o.sovereign_id
  AND m.outreach_id IS NULL;

-- -----------------------------------------------------------------------------
-- STEP B4: Log backfill results for svg_marketing.talent_flow_movements
-- -----------------------------------------------------------------------------

DO $$
DECLARE
    v_total INTEGER;
    v_resolved INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_total FROM svg_marketing.talent_flow_movements;
    SELECT COUNT(*) INTO v_resolved FROM svg_marketing.talent_flow_movements WHERE outreach_id IS NOT NULL;

    RAISE NOTICE 'SVG Marketing Talent Flow Backfill Results:';
    RAISE NOTICE '  Total records: %', v_total;
    RAISE NOTICE '  outreach_id resolved: %', v_resolved;
    RAISE NOTICE '  Missing: %', v_total - v_resolved;
END $$;

-- -----------------------------------------------------------------------------
-- STEP B5: Add indexes for svg_marketing.talent_flow_movements
-- -----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_svg_talent_flow_outreach_id
ON svg_marketing.talent_flow_movements(outreach_id)
WHERE outreach_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_svg_talent_flow_correlation_id
ON svg_marketing.talent_flow_movements(correlation_id);

-- =============================================================================
-- SECTION C: Create talent_flow_errors table (required by doctrine)
-- =============================================================================

CREATE TABLE IF NOT EXISTS talent_flow.talent_flow_errors (
    error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Spine reference (optional - may fail before outreach_id is known)
    outreach_id UUID,

    -- Pipeline context
    pipeline_stage VARCHAR(50) NOT NULL,
    failure_code VARCHAR(50) NOT NULL,
    blocking_reason TEXT,

    -- Outcome per binary doctrine
    outcome VARCHAR(20) CHECK (outcome IN ('PROMOTED', 'QUARANTINED')),

    -- Reference to movement
    movement_id BIGINT,

    -- Traceability
    correlation_id UUID,

    -- Error details
    severity VARCHAR(20) DEFAULT 'ERROR' CHECK (severity IN ('ERROR', 'WARNING', 'CRITICAL')),
    retry_allowed BOOLEAN DEFAULT FALSE,
    raw_input JSONB,
    stack_trace TEXT,

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolution_note TEXT,

    -- FK to spine (deferred until outreach_id is reliably populated)
    -- CONSTRAINT fk_tf_errors_outreach
    --     FOREIGN KEY (outreach_id)
    --     REFERENCES outreach.outreach(outreach_id)
    --     ON DELETE SET NULL

    -- FK to movement
    CONSTRAINT fk_tf_errors_movement
        FOREIGN KEY (movement_id)
        REFERENCES talent_flow.movements(movement_id)
        ON DELETE SET NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_tf_errors_outreach_id
ON talent_flow.talent_flow_errors(outreach_id)
WHERE outreach_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_tf_errors_pipeline_stage
ON talent_flow.talent_flow_errors(pipeline_stage);

CREATE INDEX IF NOT EXISTS idx_tf_errors_failure_code
ON talent_flow.talent_flow_errors(failure_code);

CREATE INDEX IF NOT EXISTS idx_tf_errors_unresolved
ON talent_flow.talent_flow_errors(resolved_at)
WHERE resolved_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_tf_errors_correlation_id
ON talent_flow.talent_flow_errors(correlation_id);

-- Table comment
COMMENT ON TABLE talent_flow.talent_flow_errors IS
'TF.ERRORS.001 | Error persistence table for Talent Flow sensor.
Per Error Persistence Doctrine: failures are work items, not states.
Binary outcomes: PROMOTED or QUARANTINED only.
Added 2026-01-08 per P0 migration requirements.';

-- =============================================================================
-- SECTION D: Create views for spine resolution tracking
-- =============================================================================

CREATE OR REPLACE VIEW talent_flow.v_movements_pending_spine AS
SELECT
    m.movement_id,
    m.contact_id,
    m.old_company_id,
    m.new_company_id,
    m.movement_type,
    m.from_outreach_id,
    m.to_outreach_id,
    m.correlation_id,
    m.detected_at,
    CASE
        WHEN m.old_company_id IS NULL THEN 'N/A'
        WHEN m.from_outreach_id IS NOT NULL THEN 'RESOLVED'
        WHEN o_from.outreach_id IS NOT NULL THEN 'RESOLVABLE'
        ELSE 'NO_SPINE_RECORD'
    END AS from_resolution_status,
    CASE
        WHEN m.new_company_id IS NULL THEN 'N/A'
        WHEN m.to_outreach_id IS NOT NULL THEN 'RESOLVED'
        WHEN o_to.outreach_id IS NOT NULL THEN 'RESOLVABLE'
        ELSE 'NO_SPINE_RECORD'
    END AS to_resolution_status
FROM talent_flow.movements m
LEFT JOIN outreach.outreach o_from ON m.old_company_id::UUID = o_from.sovereign_id
LEFT JOIN outreach.outreach o_to ON m.new_company_id::UUID = o_to.sovereign_id
ORDER BY m.detected_at DESC;

COMMENT ON VIEW talent_flow.v_movements_pending_spine IS
'P0_002 | View showing movement records and their spine resolution status.
RESOLVED = outreach_id populated
RESOLVABLE = spine record exists, can backfill
NO_SPINE_RECORD = company not in spine, needs investigation
N/A = company_id is NULL (e.g., hire from unknown, departure to unknown)';

-- =============================================================================
-- SECTION E: TODO Flag for Trigger Rewrite (Phase 2)
-- =============================================================================

-- TODO: Phase 2 - Rewrite trg_movements_create_bit_event trigger
-- Current: Inserts to bit.events with company_unique_id
-- Target: Insert to outreach.bit_signals with outreach_id
-- Location: talent_flow-schema.sql lines 264-346
-- Blocked until: BIT spine alignment complete

COMMENT ON TRIGGER trg_movements_create_bit_event ON talent_flow.movements IS
'TODO P0_002: This trigger needs rewrite in Phase 2.
Currently writes to bit.events with company_unique_id.
Should write to outreach.bit_signals with outreach_id.
DO NOT MODIFY UNTIL Phase 2 BIT alignment complete.';

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================
-- Run these after migration:
--
-- 1. Check talent_flow.movements columns added:
-- SELECT column_name FROM information_schema.columns
-- WHERE table_schema = 'talent_flow' AND table_name = 'movements'
-- AND column_name IN ('from_outreach_id', 'to_outreach_id', 'correlation_id', 'movement_hash');
--
-- 2. Check svg_marketing.talent_flow_movements columns added:
-- SELECT column_name FROM information_schema.columns
-- WHERE table_schema = 'svg_marketing' AND table_name = 'talent_flow_movements'
-- AND column_name IN ('outreach_id', 'correlation_id');
--
-- 3. Check backfill coverage for talent_flow.movements:
-- SELECT from_resolution_status, to_resolution_status, COUNT(*)
-- FROM talent_flow.v_movements_pending_spine
-- GROUP BY 1, 2;
--
-- 4. Check talent_flow_errors table exists:
-- SELECT tablename FROM pg_tables WHERE schemaname = 'talent_flow' AND tablename = 'talent_flow_errors';
--
-- 5. Check indexes created:
-- SELECT indexname FROM pg_indexes WHERE schemaname = 'talent_flow';

-- =============================================================================
-- MIGRATION P0_002 COMPLETE
-- =============================================================================
-- CREATED:
--   - talent_flow.movements.from_outreach_id column
--   - talent_flow.movements.to_outreach_id column
--   - talent_flow.movements.correlation_id column
--   - talent_flow.movements.movement_hash column
--   - svg_marketing.talent_flow_movements.outreach_id column
--   - svg_marketing.talent_flow_movements.correlation_id column
--   - talent_flow.talent_flow_errors table
--   - talent_flow.v_movements_pending_spine view
--   - 8 new indexes
--
-- BACKFILLED:
--   - from_outreach_id from spine
--   - to_outreach_id from spine
--   - outreach_id from spine (svg_marketing)
--   - movement_hash computed
--
-- DEFERRED (Phase 2):
--   - FK constraints (pending full backfill)
--   - Trigger rewrite (trg_movements_create_bit_event)
--   - Dropping legacy columns
--
-- NEXT STEPS:
--   1. Review v_movements_pending_spine for NO_SPINE_RECORD entries
--   2. Resolve missing spine records
--   3. Phase 2: Add FK constraints and rewrite triggers
-- =============================================================================

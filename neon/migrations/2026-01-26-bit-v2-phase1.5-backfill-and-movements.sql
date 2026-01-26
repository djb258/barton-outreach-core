-- ═══════════════════════════════════════════════════════════════════════════════
-- BIT Authorization System v2.0 - Phase 1.5: DOL Backfill + Talent Flow Movements
--
-- Authority: ADR-017
-- Date: 2026-01-26
-- Status: ACTIVE
--
-- PURPOSE:
--   1. Create idempotent backfill function for DOL renewal signals
--   2. Create talent_flow.movements table for bridge function
--   3. Attach bridge trigger to movements table
--
-- ARCHITECTURE:
--   DOL Hub ──────► dol.pressure_signals ────────┐
--   People Hub ───► people.pressure_signals ─────┼──► company_target.vw_all_pressure_signals
--   Blog Hub ─────► blog.pressure_signals ───────┘
--
-- ═══════════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 1: SCHEMA CREATION
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE SCHEMA IF NOT EXISTS talent_flow;

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 2: DOL BACKFILL FUNCTION
-- ═══════════════════════════════════════════════════════════════════════════════
-- Idempotent function to backfill dol.pressure_signals from dol.renewal_calendar
-- Uses same magnitude calculation as dol.bridge_renewal_calendar() trigger

CREATE OR REPLACE FUNCTION dol.backfill_renewal_signals()
RETURNS TABLE (
    processed INTEGER,
    skipped INTEGER,
    errors INTEGER
) AS $$
DECLARE
    v_processed INTEGER := 0;
    v_skipped INTEGER := 0;
    v_errors INTEGER := 0;
    v_magnitude INTEGER;
    r RECORD;
BEGIN
    FOR r IN
        SELECT
            rc.renewal_id,
            rc.company_unique_id,
            rc.renewal_date,
            rc.days_until_renewal,
            rc.plan_name,
            rc.carrier_name
        FROM dol.renewal_calendar rc
        WHERE rc.company_unique_id IS NOT NULL
    LOOP
        BEGIN
            -- Check if already processed (idempotent)
            IF EXISTS (
                SELECT 1 FROM dol.pressure_signals
                WHERE source_record_id = r.renewal_id::TEXT
            ) THEN
                v_skipped := v_skipped + 1;
                CONTINUE;
            END IF;

            -- Calculate magnitude (same logic as bridge function)
            v_magnitude := CASE
                WHEN r.days_until_renewal <= 30 THEN 70
                WHEN r.days_until_renewal <= 60 THEN 55
                WHEN r.days_until_renewal <= 90 THEN 45
                WHEN r.days_until_renewal <= 120 THEN 35
                ELSE 25
            END;

            -- Insert pressure signal
            INSERT INTO dol.pressure_signals (
                company_unique_id,
                signal_type,
                pressure_domain,
                pressure_class,
                signal_value,
                magnitude,
                detected_at,
                expires_at,
                source_record_id
            ) VALUES (
                r.company_unique_id,
                'renewal_proximity',
                'STRUCTURAL_PRESSURE',
                'DEADLINE_PROXIMITY',
                jsonb_build_object(
                    'renewal_id', r.renewal_id,
                    'renewal_date', r.renewal_date,
                    'days_until_renewal', r.days_until_renewal,
                    'plan_name', r.plan_name,
                    'carrier_name', r.carrier_name,
                    'backfill', true
                ),
                v_magnitude,
                NOW(),
                COALESCE(r.renewal_date, NOW()) + INTERVAL '30 days',
                r.renewal_id::TEXT
            );

            v_processed := v_processed + 1;

        EXCEPTION WHEN OTHERS THEN
            v_errors := v_errors + 1;
            RAISE WARNING 'Error processing renewal_id %: %', r.renewal_id, SQLERRM;
        END;
    END LOOP;

    RETURN QUERY SELECT v_processed, v_skipped, v_errors;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION dol.backfill_renewal_signals() IS
'Idempotent backfill function for DOL renewal signals.
Processes dol.renewal_calendar rows into dol.pressure_signals.
Uses same magnitude calculation as bridge trigger.
Safe to run multiple times - skips already processed records.
Authority: ADR-017';

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 3: TALENT FLOW MOVEMENTS TABLE
-- ═══════════════════════════════════════════════════════════════════════════════
-- Table structure matches expectations of people.bridge_talent_flow_movement()
--
-- AI-Ready Data Metadata (per Canonical Architecture Doctrine §12):
--   table_unique_id: TBL-TF-MOVEMENTS-001
--   owning_hub_unique_id: HUB-TF-001
--   owning_subhub_unique_id: SUBHUB-TF-001
--   description: Executive movement tracking for BIT pressure signals
--   source_of_truth: Talent Flow detection processes
--   row_identity_strategy: UUID primary key (movement_id)

CREATE TABLE IF NOT EXISTS talent_flow.movements (
    -- Primary key
    -- column_unique_id: COL-TF-MV-001
    -- semantic_role: identifier
    -- format: UUID
    movement_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Person reference
    -- column_unique_id: COL-TF-MV-002
    -- semantic_role: foreign_key
    -- format: UUID
    contact_id          UUID NOT NULL,

    -- Movement classification
    -- column_unique_id: COL-TF-MV-003
    -- semantic_role: attribute
    -- format: ENUM (hire, departure, promotion, lateral)
    movement_type       VARCHAR(20) NOT NULL CHECK (movement_type IN ('hire', 'departure', 'promotion', 'lateral')),

    -- Company references
    -- column_unique_id: COL-TF-MV-004
    -- semantic_role: foreign_key
    -- format: TEXT (company_unique_id)
    old_company_id      TEXT,  -- nullable for hires

    -- column_unique_id: COL-TF-MV-005
    -- semantic_role: foreign_key
    -- format: TEXT (company_unique_id)
    new_company_id      TEXT,  -- nullable for departures

    -- Title tracking
    -- column_unique_id: COL-TF-MV-006
    -- semantic_role: attribute
    -- format: TEXT
    old_title           TEXT,

    -- column_unique_id: COL-TF-MV-007
    -- semantic_role: attribute
    -- format: TEXT
    new_title           TEXT,

    -- Detection metadata
    -- column_unique_id: COL-TF-MV-008
    -- semantic_role: metric
    -- format: INTEGER (0-100)
    confidence_score    INTEGER NOT NULL DEFAULT 0 CHECK (confidence_score >= 0 AND confidence_score <= 100),

    -- column_unique_id: COL-TF-MV-009
    -- semantic_role: attribute
    -- format: ISO-8601
    detected_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- column_unique_id: COL-TF-MV-010
    -- semantic_role: attribute
    -- format: ENUM
    detected_source     VARCHAR(50) NOT NULL DEFAULT 'manual',

    -- Audit columns
    -- column_unique_id: COL-TF-MV-011
    -- semantic_role: attribute
    -- format: ISO-8601
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- column_unique_id: COL-TF-MV-012
    -- semantic_role: attribute
    -- format: ISO-8601
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_company_reference CHECK (
        -- At least one company must be referenced
        old_company_id IS NOT NULL OR new_company_id IS NOT NULL
    )
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_tf_movements_contact ON talent_flow.movements(contact_id);
CREATE INDEX IF NOT EXISTS idx_tf_movements_type ON talent_flow.movements(movement_type);
CREATE INDEX IF NOT EXISTS idx_tf_movements_old_company ON talent_flow.movements(old_company_id) WHERE old_company_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tf_movements_new_company ON talent_flow.movements(new_company_id) WHERE new_company_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tf_movements_detected ON talent_flow.movements(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_tf_movements_confidence ON talent_flow.movements(confidence_score DESC);

COMMENT ON TABLE talent_flow.movements IS
'Executive movement tracking for BIT pressure signal generation.
Captures hires, departures, promotions, and lateral moves.
Bridge trigger emits DECISION_SURFACE signals to people.pressure_signals.

AI-Ready Metadata:
- table_unique_id: TBL-TF-MOVEMENTS-001
- owning_hub_unique_id: HUB-TF-001
- source_of_truth: Talent Flow detection processes

Authority: ADR-017';

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 4: ATTACH BRIDGE TRIGGER
-- ═══════════════════════════════════════════════════════════════════════════════
-- The bridge function was created in Phase 1, now attach to new table

DROP TRIGGER IF EXISTS trg_bridge_to_pressure_signals ON talent_flow.movements;

CREATE TRIGGER trg_bridge_to_pressure_signals
    AFTER INSERT ON talent_flow.movements
    FOR EACH ROW
    EXECUTE FUNCTION people.bridge_talent_flow_movement();

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 5: EXECUTE DOL BACKFILL
-- ═══════════════════════════════════════════════════════════════════════════════

DO $$
DECLARE
    v_result RECORD;
BEGIN
    SELECT * INTO v_result FROM dol.backfill_renewal_signals();

    RAISE NOTICE '════════════════════════════════════════════════════════════';
    RAISE NOTICE 'DOL Backfill Results';
    RAISE NOTICE '════════════════════════════════════════════════════════════';
    RAISE NOTICE '  Processed: %', v_result.processed;
    RAISE NOTICE '  Skipped (duplicates): %', v_result.skipped;
    RAISE NOTICE '  Errors: %', v_result.errors;
    RAISE NOTICE '════════════════════════════════════════════════════════════';
END $$;

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 6: VERIFICATION
-- ═══════════════════════════════════════════════════════════════════════════════

DO $$
DECLARE
    v_movements_table BOOLEAN;
    v_backfill_func BOOLEAN;
    v_trigger_attached BOOLEAN;
    v_dol_signal_count INTEGER;
BEGIN
    -- Check movements table
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'talent_flow' AND table_name = 'movements'
    ) INTO v_movements_table;

    -- Check backfill function
    SELECT EXISTS (
        SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'dol' AND p.proname = 'backfill_renewal_signals'
    ) INTO v_backfill_func;

    -- Check trigger
    SELECT EXISTS (
        SELECT 1 FROM information_schema.triggers
        WHERE trigger_name = 'trg_bridge_to_pressure_signals'
          AND event_object_schema = 'talent_flow'
          AND event_object_table = 'movements'
    ) INTO v_trigger_attached;

    -- Count DOL signals
    SELECT COUNT(*) INTO v_dol_signal_count FROM dol.pressure_signals;

    RAISE NOTICE '';
    RAISE NOTICE '════════════════════════════════════════════════════════════';
    RAISE NOTICE 'BIT v2 Phase 1.5 Migration Complete';
    RAISE NOTICE '════════════════════════════════════════════════════════════';
    RAISE NOTICE '';
    RAISE NOTICE 'Components:';
    RAISE NOTICE '  talent_flow.movements table:     %', CASE WHEN v_movements_table THEN 'OK' ELSE 'MISSING' END;
    RAISE NOTICE '  dol.backfill_renewal_signals():  %', CASE WHEN v_backfill_func THEN 'OK' ELSE 'MISSING' END;
    RAISE NOTICE '  Bridge trigger on movements:     %', CASE WHEN v_trigger_attached THEN 'ATTACHED' ELSE 'MISSING' END;
    RAISE NOTICE '';
    RAISE NOTICE 'Signal Counts:';
    RAISE NOTICE '  dol.pressure_signals:            %', v_dol_signal_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Authority: ADR-017';
    RAISE NOTICE '════════════════════════════════════════════════════════════';
END $$;

-- ═══════════════════════════════════════════════════════════════════════════════
-- END MIGRATION
-- ═══════════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════════
-- ROLLBACK SCRIPT (DO NOT EXECUTE UNLESS REQUIRED)
-- ═══════════════════════════════════════════════════════════════════════════════
/*
-- To rollback this migration, execute the following:

-- 1. Drop trigger
DROP TRIGGER IF EXISTS trg_bridge_to_pressure_signals ON talent_flow.movements;

-- 2. Drop movements table (CAUTION: Data loss)
DROP TABLE IF EXISTS talent_flow.movements;

-- 3. Drop backfill function
DROP FUNCTION IF EXISTS dol.backfill_renewal_signals();

-- 4. Delete backfilled signals (optional - only if you want to re-run backfill)
-- DELETE FROM dol.pressure_signals WHERE (signal_value->>'backfill')::boolean = true;

-- Note: Schema is NOT dropped as it may contain other objects.
*/
-- ═══════════════════════════════════════════════════════════════════════════════

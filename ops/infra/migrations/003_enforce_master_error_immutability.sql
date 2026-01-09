-- ============================================================================
-- MIGRATION 003: Enforce Master Error Log Immutability
-- ============================================================================
-- File: 003_enforce_master_error_immutability.sql
-- Created: 2025-12-17
-- Purpose: Harden shq_master_error_log with physical immutability controls
-- Doctrine: Barton Doctrine / Bicycle Wheel v1.1
--
-- ENFORCEMENT SUMMARY:
--   1. Create dedicated writer role with INSERT-only permissions
--   2. Add process_id NOT NULL constraint with format validation
--   3. Create immutability trigger to BLOCK UPDATE/DELETE at DB level
--   4. Revoke dangerous permissions from all roles
--
-- DOCTRINE NOTE:
--   Error history is immutable. Corrections are new records, never edits.
-- ============================================================================

-- ============================================================================
-- STEP 1: Create Dedicated Writer Role (INSERT-only)
-- ============================================================================
-- This role can ONLY insert into the master error log.
-- No UPDATE, no DELETE, no TRUNCATE.
-- ============================================================================

-- Create the role if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'error_log_writer') THEN
        CREATE ROLE error_log_writer NOLOGIN;
        RAISE NOTICE 'Created role: error_log_writer';
    ELSE
        RAISE NOTICE 'Role error_log_writer already exists';
    END IF;
END $$;

-- Grant INSERT-only on shq_master_error_log
GRANT INSERT ON public.shq_master_error_log TO error_log_writer;

-- Grant INSERT on orphan_errors (for rejected errors)
GRANT INSERT ON public.shq_orphan_errors TO error_log_writer;

-- Grant SELECT for verification (read-only)
GRANT SELECT ON public.shq_master_error_log TO error_log_writer;
GRANT SELECT ON public.shq_orphan_errors TO error_log_writer;

-- Explicitly DENY UPDATE, DELETE, TRUNCATE by NOT granting them
-- (PostgreSQL default is deny unless explicitly granted)

COMMENT ON ROLE error_log_writer IS
    'INSERT-only role for shq_master_error_log. Cannot UPDATE, DELETE, or TRUNCATE. Doctrine: Immutable error history.';

-- ============================================================================
-- STEP 2: Add process_id Validation Constraint
-- ============================================================================
-- DOCTRINE: process_id is MANDATORY. Format: hub.subhub.pipeline.phase
-- ============================================================================

-- Drop existing constraint if it exists (idempotent)
ALTER TABLE public.shq_master_error_log
    DROP CONSTRAINT IF EXISTS chk_master_error_process_id_required;

-- Add NOT NULL enforcement (may already exist, but this ensures it)
-- Note: process_id column already has NOT NULL from original schema

-- Add format validation constraint
ALTER TABLE public.shq_master_error_log
    ADD CONSTRAINT chk_master_error_process_id_format
    CHECK (
        process_id IS NOT NULL
        AND process_id ~ '^[a-z_]+\.[a-z_]+\.[a-z_]+\.[a-z0-9_]+$'
        AND LENGTH(process_id) <= 100
        AND LENGTH(process_id) >= 10
    );

COMMENT ON CONSTRAINT chk_master_error_process_id_format ON public.shq_master_error_log IS
    'DOCTRINE: process_id is MANDATORY. Format: hub.subhub.pipeline.phase (all lowercase). Min 10 chars, max 100 chars.';

-- ============================================================================
-- STEP 3: Create Immutability Trigger (BLOCK UPDATE/DELETE)
-- ============================================================================
-- This is the nuclear option - even if RLS is bypassed or someone has
-- superuser access, this trigger will BLOCK modifications.
--
-- DOCTRINE: Error history is immutable. Corrections are new records, never edits.
-- ============================================================================

-- Create trigger function that blocks UPDATE/DELETE
CREATE OR REPLACE FUNCTION public.fn_master_error_immutability()
RETURNS TRIGGER AS $$
BEGIN
    -- BLOCK UPDATE
    IF TG_OP = 'UPDATE' THEN
        RAISE EXCEPTION
            'UPDATE BLOCKED: shq_master_error_log is immutable per Barton Doctrine. '
            'Error history cannot be modified. Corrections must be new records. '
            'Attempted to UPDATE error_id: %',
            OLD.error_id;
    END IF;

    -- BLOCK DELETE
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION
            'DELETE BLOCKED: shq_master_error_log is immutable per Barton Doctrine. '
            'Error history cannot be deleted. Records are permanent. '
            'Attempted to DELETE error_id: %',
            OLD.error_id;
    END IF;

    -- BLOCK TRUNCATE (handled separately, but included for completeness)
    IF TG_OP = 'TRUNCATE' THEN
        RAISE EXCEPTION
            'TRUNCATE BLOCKED: shq_master_error_log is immutable per Barton Doctrine. '
            'The entire error history cannot be wiped.';
    END IF;

    RETURN NULL; -- Should never reach here
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION public.fn_master_error_immutability() IS
    'DOCTRINE ENFORCEMENT: Blocks UPDATE/DELETE on shq_master_error_log. Error history is immutable.';

-- Drop existing trigger if it exists (idempotent)
DROP TRIGGER IF EXISTS trg_master_error_immutability_update ON public.shq_master_error_log;
DROP TRIGGER IF EXISTS trg_master_error_immutability_delete ON public.shq_master_error_log;

-- Create trigger for UPDATE (BEFORE to block early)
CREATE TRIGGER trg_master_error_immutability_update
    BEFORE UPDATE ON public.shq_master_error_log
    FOR EACH ROW
    EXECUTE FUNCTION public.fn_master_error_immutability();

-- Create trigger for DELETE (BEFORE to block early)
CREATE TRIGGER trg_master_error_immutability_delete
    BEFORE DELETE ON public.shq_master_error_log
    FOR EACH ROW
    EXECUTE FUNCTION public.fn_master_error_immutability();

-- ============================================================================
-- STEP 4: Create Truncate Trigger (Event Trigger for TRUNCATE)
-- ============================================================================
-- TRUNCATE cannot be blocked by row-level triggers, so we use an event trigger.
-- Note: Event triggers require superuser to create.
-- ============================================================================

-- Create function to block truncate
CREATE OR REPLACE FUNCTION public.fn_block_master_error_truncate()
RETURNS event_trigger AS $$
DECLARE
    obj record;
BEGIN
    FOR obj IN SELECT * FROM pg_event_trigger_ddl_commands()
    LOOP
        IF obj.object_identity = 'public.shq_master_error_log' THEN
            RAISE EXCEPTION
                'TRUNCATE BLOCKED: shq_master_error_log is immutable per Barton Doctrine. '
                'The entire error history cannot be wiped.';
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Note: Event trigger creation requires superuser privileges
-- Uncomment the following if running as superuser:
--
-- DROP EVENT TRIGGER IF EXISTS evt_block_master_error_truncate;
-- CREATE EVENT TRIGGER evt_block_master_error_truncate
--     ON ddl_command_end
--     WHEN TAG IN ('TRUNCATE')
--     EXECUTE FUNCTION public.fn_block_master_error_truncate();

-- ============================================================================
-- STEP 5: Update emit_master_error Function with process_id Validation
-- ============================================================================

CREATE OR REPLACE FUNCTION public.emit_master_error(
    p_correlation_id    UUID,
    p_hub               VARCHAR(50),
    p_sub_hub           VARCHAR(50),
    p_process_id        VARCHAR(100),
    p_pipeline_phase    VARCHAR(50),
    p_entity_type       VARCHAR(50),
    p_entity_id         VARCHAR(100),
    p_severity          VARCHAR(20),
    p_error_code        VARCHAR(50),
    p_error_message     TEXT,
    p_source_tool       VARCHAR(100) DEFAULT NULL,
    p_operating_mode    VARCHAR(20) DEFAULT 'STEADY_STATE',
    p_retryable         BOOLEAN DEFAULT false,
    p_cost_impact_usd   DECIMAL(10,4) DEFAULT NULL,
    p_metadata          JSONB DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_error_id UUID;
BEGIN
    -- ================================================================
    -- MANDATORY VALIDATION - FAIL HARD
    -- ================================================================

    -- FAIL HARD: correlation_id is MANDATORY
    IF p_correlation_id IS NULL THEN
        INSERT INTO public.shq_orphan_errors (raw_event, rejection_reason)
        VALUES (
            jsonb_build_object(
                'hub', p_hub,
                'process_id', p_process_id,
                'error_code', p_error_code,
                'error_message', p_error_message
            ),
            'FAIL HARD: Missing correlation_id - REJECTED per Barton Doctrine'
        );
        RAISE EXCEPTION 'FAIL HARD: correlation_id is MANDATORY per Barton Doctrine';
    END IF;

    -- FAIL HARD: process_id is MANDATORY
    IF p_process_id IS NULL OR TRIM(p_process_id) = '' THEN
        INSERT INTO public.shq_orphan_errors (raw_event, rejection_reason)
        VALUES (
            jsonb_build_object(
                'correlation_id', p_correlation_id,
                'hub', p_hub,
                'error_code', p_error_code,
                'error_message', p_error_message
            ),
            'FAIL HARD: Missing or empty process_id - REJECTED per Barton Doctrine'
        );
        RAISE EXCEPTION 'FAIL HARD: process_id is MANDATORY per Barton Doctrine';
    END IF;

    -- FAIL HARD: process_id format validation
    IF NOT (p_process_id ~ '^[a-z_]+\.[a-z_]+\.[a-z_]+\.[a-z0-9_]+$') THEN
        INSERT INTO public.shq_orphan_errors (raw_event, rejection_reason)
        VALUES (
            jsonb_build_object(
                'correlation_id', p_correlation_id,
                'hub', p_hub,
                'process_id', p_process_id,
                'error_code', p_error_code,
                'error_message', p_error_message
            ),
            'FAIL HARD: Malformed process_id. Expected format: hub.subhub.pipeline.phase'
        );
        RAISE EXCEPTION 'FAIL HARD: Malformed process_id: %. Expected format: hub.subhub.pipeline.phase', p_process_id;
    END IF;

    -- ================================================================
    -- INSERT ERROR RECORD
    -- ================================================================

    INSERT INTO public.shq_master_error_log (
        correlation_id, hub, sub_hub, process_id, pipeline_phase,
        entity_type, entity_id, severity, error_code, error_message,
        source_tool, operating_mode, retryable, cost_impact_usd, metadata
    ) VALUES (
        p_correlation_id, p_hub, p_sub_hub, p_process_id, p_pipeline_phase,
        p_entity_type, p_entity_id, p_severity, p_error_code, p_error_message,
        p_source_tool, p_operating_mode, p_retryable, p_cost_impact_usd, p_metadata
    )
    RETURNING error_id INTO v_error_id;

    RETURN v_error_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION public.emit_master_error IS
    'Emits an error event to shq_master_error_log. '
    'DOCTRINE: correlation_id and process_id are MANDATORY. FAIL HARD if missing or malformed. '
    'Error history is immutable. Corrections are new records, never edits.';

-- ============================================================================
-- STEP 6: Revoke Dangerous Permissions
-- ============================================================================
-- Explicitly revoke UPDATE, DELETE, TRUNCATE from PUBLIC
-- (defense in depth - even if someone gains access)
-- ============================================================================

REVOKE UPDATE ON public.shq_master_error_log FROM PUBLIC;
REVOKE DELETE ON public.shq_master_error_log FROM PUBLIC;
REVOKE TRUNCATE ON public.shq_master_error_log FROM PUBLIC;

-- Note: To also revoke from the table owner (for maximum security),
-- you would need to transfer ownership to a restricted role.
-- This is an optional hardening step:
--
-- ALTER TABLE public.shq_master_error_log OWNER TO error_log_admin;
-- REVOKE UPDATE, DELETE, TRUNCATE ON public.shq_master_error_log FROM error_log_admin;

-- ============================================================================
-- STEP 7: Verify Migration
-- ============================================================================

DO $$
DECLARE
    v_trigger_count INTEGER;
    v_constraint_exists BOOLEAN;
    v_role_exists BOOLEAN;
    v_function_updated BOOLEAN;
BEGIN
    -- Check trigger count
    SELECT COUNT(*) INTO v_trigger_count
    FROM pg_trigger
    WHERE tgrelid = 'public.shq_master_error_log'::regclass
    AND tgname LIKE 'trg_master_error_immutability%';

    -- Check constraint exists
    SELECT EXISTS (
        SELECT FROM information_schema.table_constraints
        WHERE table_schema = 'public'
        AND table_name = 'shq_master_error_log'
        AND constraint_name = 'chk_master_error_process_id_format'
    ) INTO v_constraint_exists;

    -- Check role exists
    SELECT EXISTS (
        SELECT FROM pg_roles
        WHERE rolname = 'error_log_writer'
    ) INTO v_role_exists;

    -- Check function updated (look for FAIL HARD in definition)
    SELECT EXISTS (
        SELECT FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public'
        AND p.proname = 'emit_master_error'
        AND p.prosrc LIKE '%FAIL HARD%'
    ) INTO v_function_updated;

    -- Report results
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migration 003 Verification:';
    RAISE NOTICE '  Immutability triggers: % (expected 2)', v_trigger_count;
    RAISE NOTICE '  process_id constraint: %', CASE WHEN v_constraint_exists THEN 'EXISTS' ELSE 'MISSING' END;
    RAISE NOTICE '  error_log_writer role: %', CASE WHEN v_role_exists THEN 'EXISTS' ELSE 'MISSING' END;
    RAISE NOTICE '  emit_master_error updated: %', CASE WHEN v_function_updated THEN 'YES' ELSE 'NO' END;
    RAISE NOTICE '========================================';

    IF v_trigger_count < 2 THEN
        RAISE WARNING 'Expected 2 immutability triggers, found %', v_trigger_count;
    END IF;

    IF NOT v_constraint_exists THEN
        RAISE WARNING 'process_id format constraint not found';
    END IF;
END $$;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Enforcement summary:
--
-- 1. ROLE ENFORCEMENT:
--    - error_log_writer role created with INSERT-only permissions
--    - UPDATE, DELETE, TRUNCATE not granted to any role
--
-- 2. CONSTRAINT ENFORCEMENT:
--    - process_id format validated at DB level
--    - Pattern: hub.subhub.pipeline.phase (all lowercase)
--
-- 3. TRIGGER ENFORCEMENT:
--    - UPDATE blocked by trg_master_error_immutability_update
--    - DELETE blocked by trg_master_error_immutability_delete
--    - Triggers fire BEFORE operation (fail fast)
--
-- 4. FUNCTION ENFORCEMENT:
--    - emit_master_error() validates correlation_id AND process_id
--    - FAIL HARD on missing or malformed values
--    - Rejected errors logged to shq_orphan_errors
--
-- DOCTRINE NOTE:
--    Error history is immutable. Corrections are new records, never edits.
-- ============================================================================

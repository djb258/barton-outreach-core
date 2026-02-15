-- ============================================================================
-- DOL Tables Read-Only Lock
--
-- Purpose: Lock down DOL reference tables to prevent accidental modifications.
--          Data comes from DOL (authoritative source) and should only be
--          modified during annual import operations.
--
-- Tables Affected:
--   - dol.form_5500
--   - dol.form_5500_sf
--   - dol.schedule_a
--   - dol.renewal_calendar
--
-- Bypass Mechanism:
--   SET session dol.import_mode = 'active';
--   -- run import operations --
--   RESET dol.import_mode;
--
-- Created: 2026-01-15
-- ============================================================================

-- Create the custom GUC parameter for import mode bypass
DO $$
BEGIN
    -- Create custom parameter if it doesn't exist
    PERFORM set_config('dol.import_mode', 'inactive', false);
EXCEPTION
    WHEN OTHERS THEN NULL;
END $$;

-- ============================================================================
-- FORM 5500 - Read-Only Lock
-- ============================================================================

-- Drop existing triggers if they exist
DROP TRIGGER IF EXISTS dol_form_5500_readonly_insert ON dol.form_5500;
DROP TRIGGER IF EXISTS dol_form_5500_readonly_update ON dol.form_5500;
DROP TRIGGER IF EXISTS dol_form_5500_readonly_delete ON dol.form_5500;

-- Create the trigger function for form_5500
CREATE OR REPLACE FUNCTION dol.form_5500_readonly_guard()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if import mode is active (bypass for annual imports)
    IF current_setting('dol.import_mode', true) = 'active' THEN
        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        ELSE
            RETURN NEW;
        END IF;
    END IF;

    -- Block the operation
    RAISE EXCEPTION 'DOL_READONLY_VIOLATION: dol.form_5500 is read-only. '
        'Data originates from DOL and cannot be modified. '
        'For annual imports, use: SET session dol.import_mode = ''active'';'
        USING ERRCODE = 'P0001';
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
CREATE TRIGGER dol_form_5500_readonly_insert
    BEFORE INSERT ON dol.form_5500
    FOR EACH ROW EXECUTE FUNCTION dol.form_5500_readonly_guard();

CREATE TRIGGER dol_form_5500_readonly_update
    BEFORE UPDATE ON dol.form_5500
    FOR EACH ROW EXECUTE FUNCTION dol.form_5500_readonly_guard();

CREATE TRIGGER dol_form_5500_readonly_delete
    BEFORE DELETE ON dol.form_5500
    FOR EACH ROW EXECUTE FUNCTION dol.form_5500_readonly_guard();

-- ============================================================================
-- FORM 5500-SF - Read-Only Lock
-- ============================================================================

DROP TRIGGER IF EXISTS dol_form_5500_sf_readonly_insert ON dol.form_5500_sf;
DROP TRIGGER IF EXISTS dol_form_5500_sf_readonly_update ON dol.form_5500_sf;
DROP TRIGGER IF EXISTS dol_form_5500_sf_readonly_delete ON dol.form_5500_sf;

CREATE OR REPLACE FUNCTION dol.form_5500_sf_readonly_guard()
RETURNS TRIGGER AS $$
BEGIN
    IF current_setting('dol.import_mode', true) = 'active' THEN
        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        ELSE
            RETURN NEW;
        END IF;
    END IF;

    RAISE EXCEPTION 'DOL_READONLY_VIOLATION: dol.form_5500_sf is read-only. '
        'Data originates from DOL and cannot be modified. '
        'For annual imports, use: SET session dol.import_mode = ''active'';'
        USING ERRCODE = 'P0001';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER dol_form_5500_sf_readonly_insert
    BEFORE INSERT ON dol.form_5500_sf
    FOR EACH ROW EXECUTE FUNCTION dol.form_5500_sf_readonly_guard();

CREATE TRIGGER dol_form_5500_sf_readonly_update
    BEFORE UPDATE ON dol.form_5500_sf
    FOR EACH ROW EXECUTE FUNCTION dol.form_5500_sf_readonly_guard();

CREATE TRIGGER dol_form_5500_sf_readonly_delete
    BEFORE DELETE ON dol.form_5500_sf
    FOR EACH ROW EXECUTE FUNCTION dol.form_5500_sf_readonly_guard();

-- ============================================================================
-- SCHEDULE A - Read-Only Lock
-- ============================================================================

DROP TRIGGER IF EXISTS dol_schedule_a_readonly_insert ON dol.schedule_a;
DROP TRIGGER IF EXISTS dol_schedule_a_readonly_update ON dol.schedule_a;
DROP TRIGGER IF EXISTS dol_schedule_a_readonly_delete ON dol.schedule_a;

CREATE OR REPLACE FUNCTION dol.schedule_a_readonly_guard()
RETURNS TRIGGER AS $$
BEGIN
    IF current_setting('dol.import_mode', true) = 'active' THEN
        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        ELSE
            RETURN NEW;
        END IF;
    END IF;

    RAISE EXCEPTION 'DOL_READONLY_VIOLATION: dol.schedule_a is read-only. '
        'Data originates from DOL and cannot be modified. '
        'For annual imports, use: SET session dol.import_mode = ''active'';'
        USING ERRCODE = 'P0001';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER dol_schedule_a_readonly_insert
    BEFORE INSERT ON dol.schedule_a
    FOR EACH ROW EXECUTE FUNCTION dol.schedule_a_readonly_guard();

CREATE TRIGGER dol_schedule_a_readonly_update
    BEFORE UPDATE ON dol.schedule_a
    FOR EACH ROW EXECUTE FUNCTION dol.schedule_a_readonly_guard();

CREATE TRIGGER dol_schedule_a_readonly_delete
    BEFORE DELETE ON dol.schedule_a
    FOR EACH ROW EXECUTE FUNCTION dol.schedule_a_readonly_guard();

-- ============================================================================
-- RENEWAL CALENDAR - Read-Only Lock (if exists)
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_schema = 'dol' AND table_name = 'renewal_calendar') THEN

        DROP TRIGGER IF EXISTS dol_renewal_calendar_readonly_insert ON dol.renewal_calendar;
        DROP TRIGGER IF EXISTS dol_renewal_calendar_readonly_update ON dol.renewal_calendar;
        DROP TRIGGER IF EXISTS dol_renewal_calendar_readonly_delete ON dol.renewal_calendar;

        CREATE OR REPLACE FUNCTION dol.renewal_calendar_readonly_guard()
        RETURNS TRIGGER AS $func$
        BEGIN
            IF current_setting('dol.import_mode', true) = 'active' THEN
                IF TG_OP = 'DELETE' THEN
                    RETURN OLD;
                ELSE
                    RETURN NEW;
                END IF;
            END IF;

            RAISE EXCEPTION 'DOL_READONLY_VIOLATION: dol.renewal_calendar is read-only. '
                'Data originates from DOL and cannot be modified. '
                'For annual imports, use: SET session dol.import_mode = ''active'';'
                USING ERRCODE = 'P0001';
        END;
        $func$ LANGUAGE plpgsql;

        EXECUTE 'CREATE TRIGGER dol_renewal_calendar_readonly_insert
            BEFORE INSERT ON dol.renewal_calendar
            FOR EACH ROW EXECUTE FUNCTION dol.renewal_calendar_readonly_guard()';

        EXECUTE 'CREATE TRIGGER dol_renewal_calendar_readonly_update
            BEFORE UPDATE ON dol.renewal_calendar
            FOR EACH ROW EXECUTE FUNCTION dol.renewal_calendar_readonly_guard()';

        EXECUTE 'CREATE TRIGGER dol_renewal_calendar_readonly_delete
            BEFORE DELETE ON dol.renewal_calendar
            FOR EACH ROW EXECUTE FUNCTION dol.renewal_calendar_readonly_guard()';
    END IF;
END $$;

-- ============================================================================
-- Add comments documenting the lock
-- ============================================================================

COMMENT ON FUNCTION dol.form_5500_readonly_guard() IS
    'Enforces read-only access on dol.form_5500. Bypass with SET dol.import_mode = ''active''';

COMMENT ON FUNCTION dol.form_5500_sf_readonly_guard() IS
    'Enforces read-only access on dol.form_5500_sf. Bypass with SET dol.import_mode = ''active''';

COMMENT ON FUNCTION dol.schedule_a_readonly_guard() IS
    'Enforces read-only access on dol.schedule_a. Bypass with SET dol.import_mode = ''active''';

-- ============================================================================
-- Verification: List all DOL readonly triggers
-- ============================================================================

DO $$
DECLARE
    trigger_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO trigger_count
    FROM information_schema.triggers
    WHERE trigger_schema = 'dol'
      AND trigger_name LIKE '%readonly%';

    RAISE NOTICE 'DOL Read-Only Lock: % triggers installed', trigger_count;
END $$;

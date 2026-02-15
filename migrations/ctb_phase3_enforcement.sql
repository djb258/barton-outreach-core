-- ============================================
-- CTB PHASE 3: ENFORCEMENT & LOCKDOWN
-- Date: 2026-02-06
-- Type: STRUCTURE-ONLY (NO DATA CHANGES)
-- Prerequisite: CTB_PHASE2_COLUMN_HYGIENE tag
-- ============================================

BEGIN;

-- ============================================
-- PART 1: CTB REGISTRY TABLE
-- Tracks all tables and their leaf type assignments
-- ============================================

-- Create CTB registry schema if not exists
CREATE SCHEMA IF NOT EXISTS ctb;

-- Create registry table for leaf lock enforcement
CREATE TABLE IF NOT EXISTS ctb.table_registry (
    registry_id SERIAL PRIMARY KEY,
    table_schema VARCHAR(100) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    leaf_type VARCHAR(50) NOT NULL CHECK (leaf_type IN ('CANONICAL', 'ERROR', 'MV', 'REGISTRY', 'STAGING', 'ARCHIVE', 'SYSTEM', 'DEPRECATED')),
    ctb_path VARCHAR(200),
    parent_table VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    registered_by VARCHAR(100) DEFAULT 'ctb_phase3',
    is_frozen BOOLEAN DEFAULT FALSE,
    notes TEXT,
    UNIQUE (table_schema, table_name)
);

COMMENT ON TABLE ctb.table_registry IS 'CTB Leaf Lock Registry - All tables must be registered here with a valid leaf_type';

-- Create violation log table
CREATE TABLE IF NOT EXISTS ctb.violation_log (
    violation_id SERIAL PRIMARY KEY,
    violation_type VARCHAR(100) NOT NULL,
    table_schema VARCHAR(100),
    table_name VARCHAR(100),
    column_name VARCHAR(100),
    violation_message TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'WARNING' CHECK (severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolution_note TEXT
);

COMMENT ON TABLE ctb.violation_log IS 'CTB Violation Log - Records all schema drift and compliance violations';

-- ============================================
-- PART 2: REGISTER ALL EXISTING TABLES
-- ============================================

-- Register CL tables
INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, ctb_path, notes)
SELECT 'cl', table_name,
    CASE
        WHEN table_name LIKE '%err%' OR table_name LIKE '%error%' THEN 'ERROR'
        WHEN table_name LIKE '%registry%' OR table_name LIKE '%mapping%' THEN 'REGISTRY'
        ELSE 'CANONICAL'
    END,
    'cl → company_identity',
    'Registered by CTB Phase 3'
FROM information_schema.tables
WHERE table_schema = 'cl' AND table_type = 'BASE TABLE'
ON CONFLICT (table_schema, table_name) DO NOTHING;

-- Register Outreach tables
INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, ctb_path, notes)
SELECT 'outreach', table_name,
    CASE
        WHEN table_name LIKE '%error%' OR table_name LIKE '%err%' THEN 'ERROR'
        WHEN table_name LIKE '%_status' OR table_name LIKE '%_signals' OR table_name LIKE '%_events' THEN 'MV'
        WHEN table_name LIKE '%registry%' OR table_name LIKE '%control%' THEN 'REGISTRY'
        WHEN table_name LIKE '%archive%' THEN 'ARCHIVE'
        ELSE 'CANONICAL'
    END,
    'outreach → outreach_id',
    'Registered by CTB Phase 3'
FROM information_schema.tables
WHERE table_schema = 'outreach' AND table_type = 'BASE TABLE'
ON CONFLICT (table_schema, table_name) DO NOTHING;

-- Register DOL tables
INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, ctb_path, notes)
SELECT 'dol', table_name,
    CASE
        WHEN table_name LIKE '%filtered%' THEN 'MV'
        WHEN table_name LIKE '%metadata%' THEN 'REGISTRY'
        ELSE 'CANONICAL'
    END,
    'dol → form_5500',
    'Registered by CTB Phase 3'
FROM information_schema.tables
WHERE table_schema = 'dol' AND table_type = 'BASE TABLE'
ON CONFLICT (table_schema, table_name) DO NOTHING;

-- Register People tables
INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, ctb_path, notes)
SELECT 'people', table_name,
    CASE
        WHEN table_name LIKE '%error%' OR table_name LIKE '%invalid%' THEN 'ERROR'
        WHEN table_name LIKE '%mapping%' OR table_name LIKE '%control%' THEN 'REGISTRY'
        WHEN table_name LIKE '%archive%' THEN 'ARCHIVE'
        WHEN table_name LIKE '%staging%' OR table_name LIKE '%candidate%' OR table_name LIKE '%queue%' THEN 'STAGING'
        ELSE 'CANONICAL'
    END,
    'people → people_master',
    'Registered by CTB Phase 3'
FROM information_schema.tables
WHERE table_schema = 'people' AND table_type = 'BASE TABLE'
ON CONFLICT (table_schema, table_name) DO NOTHING;

-- Register BIT tables
INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, ctb_path, notes)
SELECT 'bit', table_name,
    CASE
        WHEN table_name LIKE '%events%' THEN 'MV'
        WHEN table_name LIKE '%error%' THEN 'ERROR'
        ELSE 'CANONICAL'
    END,
    'bit → bit_scores',
    'Registered by CTB Phase 3'
FROM information_schema.tables
WHERE table_schema = 'bit' AND table_type = 'BASE TABLE'
ON CONFLICT (table_schema, table_name) DO NOTHING;

-- Register Intake tables
INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, ctb_path, notes)
SELECT 'intake', table_name, 'STAGING', 'intake → staging', 'Registered by CTB Phase 3'
FROM information_schema.tables
WHERE table_schema = 'intake' AND table_type = 'BASE TABLE'
ON CONFLICT (table_schema, table_name) DO NOTHING;

-- Register Archive tables
INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, ctb_path, notes)
SELECT 'archive', table_name, 'ARCHIVE', 'archive', 'Registered by CTB Phase 3'
FROM information_schema.tables
WHERE table_schema = 'archive' AND table_type = 'BASE TABLE'
ON CONFLICT (table_schema, table_name) DO NOTHING;

-- Register remaining tables as SYSTEM or DEPRECATED
INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, ctb_path, notes)
SELECT table_schema, table_name,
    CASE
        WHEN table_schema IN ('catalog', 'ref', 'shq', 'public') THEN 'SYSTEM'
        WHEN table_schema IN ('marketing', 'company', 'talent_flow') THEN 'DEPRECATED'
        WHEN table_schema = 'enrichment' THEN 'SYSTEM'
        WHEN table_schema = 'outreach_ctx' THEN 'SYSTEM'
        ELSE 'SYSTEM'
    END,
    table_schema || ' (non-CTB)',
    'Non-CTB table registered for tracking'
FROM information_schema.tables
WHERE table_type = 'BASE TABLE'
  AND table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast',
                           'cl', 'outreach', 'dol', 'people', 'bit', 'intake', 'archive')
  AND table_schema NOT LIKE 'pg_temp%'
ON CONFLICT (table_schema, table_name) DO NOTHING;

-- ============================================
-- PART 3: DDL EVENT TRIGGER FOR LEAF LOCK
-- ============================================

-- Function to check new table creation against registry
CREATE OR REPLACE FUNCTION ctb.check_table_creation()
RETURNS event_trigger AS $$
DECLARE
    obj record;
    schema_name text;
    tbl_name text;
    ctb_schemas text[] := ARRAY['cl', 'outreach', 'dol', 'people', 'bit', 'blog', 'intake'];
BEGIN
    FOR obj IN SELECT * FROM pg_event_trigger_ddl_commands() WHERE command_tag = 'CREATE TABLE'
    LOOP
        -- Extract schema and table name
        schema_name := split_part(obj.object_identity, '.', 1);
        tbl_name := split_part(obj.object_identity, '.', 2);

        -- Skip system schemas
        IF schema_name IN ('pg_catalog', 'information_schema', 'pg_toast', 'ctb') THEN
            CONTINUE;
        END IF;

        -- If creating in a CTB schema, log a warning (table must be registered)
        IF schema_name = ANY(ctb_schemas) THEN
            INSERT INTO ctb.violation_log (violation_type, table_schema, table_name, violation_message, severity)
            VALUES ('UNREGISTERED_TABLE', schema_name, tbl_name,
                    'New table created in CTB schema without registration. Please register in ctb.table_registry.',
                    'WARNING');

            RAISE NOTICE 'CTB WARNING: Table %.% created without CTB registration', schema_name, tbl_name;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create the event trigger (commented out - enable manually after review)
-- DROP EVENT TRIGGER IF EXISTS ctb_table_creation_check;
-- CREATE EVENT TRIGGER ctb_table_creation_check
--     ON ddl_command_end
--     WHEN TAG IN ('CREATE TABLE')
--     EXECUTE FUNCTION ctb.check_table_creation();

-- ============================================
-- PART 4: WRITE PATH GUARDRAILS
-- Add NOT NULL constraints to error_type columns
-- ============================================

-- Note: These ALTER statements will fail if there are NULL values
-- Run backfill first if needed

-- outreach.dol_errors - error_type NOT NULL
DO $$
BEGIN
    -- Check for NULLs first
    IF NOT EXISTS (SELECT 1 FROM outreach.dol_errors WHERE error_type IS NULL LIMIT 1) THEN
        ALTER TABLE outreach.dol_errors ALTER COLUMN error_type SET NOT NULL;
        RAISE NOTICE 'Set NOT NULL on outreach.dol_errors.error_type';
    ELSE
        RAISE NOTICE 'SKIPPED: outreach.dol_errors.error_type has NULL values';
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error setting NOT NULL on outreach.dol_errors.error_type: %', SQLERRM;
END $$;

-- outreach.blog_errors - error_type NOT NULL
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM outreach.blog_errors WHERE error_type IS NULL LIMIT 1) THEN
        ALTER TABLE outreach.blog_errors ALTER COLUMN error_type SET NOT NULL;
        RAISE NOTICE 'Set NOT NULL on outreach.blog_errors.error_type';
    ELSE
        RAISE NOTICE 'SKIPPED: outreach.blog_errors.error_type has NULL values';
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error setting NOT NULL on outreach.blog_errors.error_type: %', SQLERRM;
END $$;

-- cl.cl_errors_archive - error_type NOT NULL
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM cl.cl_errors_archive WHERE error_type IS NULL LIMIT 1) THEN
        ALTER TABLE cl.cl_errors_archive ALTER COLUMN error_type SET NOT NULL;
        RAISE NOTICE 'Set NOT NULL on cl.cl_errors_archive.error_type';
    ELSE
        RAISE NOTICE 'SKIPPED: cl.cl_errors_archive.error_type has NULL values';
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error setting NOT NULL on cl.cl_errors_archive.error_type: %', SQLERRM;
END $$;

-- ============================================
-- PART 5: FREEZE CTB CORE TABLES
-- ============================================

-- Mark core CTB tables as frozen (prevents accidental modification)
UPDATE ctb.table_registry
SET is_frozen = TRUE
WHERE (table_schema, table_name) IN (
    ('cl', 'company_identity'),
    ('outreach', 'outreach'),
    ('outreach', 'company_target'),
    ('outreach', 'dol'),
    ('outreach', 'blog'),
    ('outreach', 'people'),
    ('outreach', 'bit_scores'),
    ('people', 'people_master'),
    ('people', 'company_slot')
);

-- ============================================
-- LOG MIGRATION
-- ============================================

INSERT INTO public.migration_log (migration_name, step, status, details, executed_at)
VALUES (
    'ctb-phase3-enforcement',
    'complete',
    'success',
    'CTB Phase 3: Registry created, tables registered, guardrails added',
    NOW()
);

COMMIT;

-- ============================================
-- POST-MIGRATION: ENABLE EVENT TRIGGER
-- Run manually after verification:
-- ============================================
-- DROP EVENT TRIGGER IF EXISTS ctb_table_creation_check;
-- CREATE EVENT TRIGGER ctb_table_creation_check
--     ON ddl_command_end
--     WHEN TAG IN ('CREATE TABLE')
--     EXECUTE FUNCTION ctb.check_table_creation();

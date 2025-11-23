-- Create Lovable.dev Role for Edge Functions
-- Date: 2025-11-19
-- Purpose: Create a role without spaces in the name to avoid SCRAM auth issues

-- Step 1: Create role with LOGIN capability
-- Password: G1wkzJLlpYdIb3Hq0YOZX2Z4m67uveb
CREATE ROLE marketing_db_owner WITH LOGIN PASSWORD 'G1wkzJLlpYdIb3Hq0YOZX2Z4m67uveb';

-- Step 2: Grant USAGE on all schemas
GRANT USAGE ON SCHEMA public TO marketing_db_owner;
GRANT USAGE ON SCHEMA marketing TO marketing_db_owner;
GRANT USAGE ON SCHEMA intake TO marketing_db_owner;
GRANT USAGE ON SCHEMA bit TO marketing_db_owner;
GRANT USAGE ON SCHEMA shq TO marketing_db_owner;

-- Step 3: Grant table permissions on all schemas
-- PUBLIC schema
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO marketing_db_owner;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO marketing_db_owner;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO marketing_db_owner;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO marketing_db_owner;

-- MARKETING schema (main schema for invalid tables)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA marketing TO marketing_db_owner;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA marketing TO marketing_db_owner;
ALTER DEFAULT PRIVILEGES IN SCHEMA marketing GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO marketing_db_owner;
ALTER DEFAULT PRIVILEGES IN SCHEMA marketing GRANT USAGE, SELECT ON SEQUENCES TO marketing_db_owner;

-- INTAKE schema
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA intake TO marketing_db_owner;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA intake TO marketing_db_owner;
ALTER DEFAULT PRIVILEGES IN SCHEMA intake GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO marketing_db_owner;
ALTER DEFAULT PRIVILEGES IN SCHEMA intake GRANT USAGE, SELECT ON SEQUENCES TO marketing_db_owner;

-- BIT schema
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA bit TO marketing_db_owner;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA bit TO marketing_db_owner;
ALTER DEFAULT PRIVILEGES IN SCHEMA bit GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO marketing_db_owner;
ALTER DEFAULT PRIVILEGES IN SCHEMA bit GRANT USAGE, SELECT ON SEQUENCES TO marketing_db_owner;

-- SHQ schema
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA shq TO marketing_db_owner;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA shq TO marketing_db_owner;
ALTER DEFAULT PRIVILEGES IN SCHEMA shq GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO marketing_db_owner;
ALTER DEFAULT PRIVILEGES IN SCHEMA shq GRANT USAGE, SELECT ON SEQUENCES TO marketing_db_owner;

-- Step 4: Grant EXECUTE on all functions
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO marketing_db_owner;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA marketing TO marketing_db_owner;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA intake TO marketing_db_owner;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA bit TO marketing_db_owner;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA shq TO marketing_db_owner;

-- Step 5: Allow role to create temporary tables (for complex queries)
ALTER ROLE marketing_db_owner SET temp_tablespaces = '';
GRANT TEMP ON DATABASE "Marketing DB" TO marketing_db_owner;

-- Verification queries
SELECT 'Role created successfully' as status;
SELECT rolname, rolcanlogin FROM pg_roles WHERE rolname = 'marketing_db_owner';

-- Test table access
SELECT schemaname, tablename
FROM pg_tables
WHERE schemaname IN ('public', 'marketing', 'intake', 'bit', 'shq')
ORDER BY schemaname, tablename;

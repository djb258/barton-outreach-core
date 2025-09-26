-- Neon User Setup for MCP Integration
-- Run this after executing neon.sql to create the MCP user

-- Step 1: Create the MCP user (run as superuser)
-- Replace 'your_secure_password' with a strong password
CREATE USER mcp_user WITH PASSWORD 'your_secure_password';

-- Step 2: Grant the required roles to the MCP user
GRANT mcp_ingest, mcp_promote TO mcp_user;

-- Step 3: Grant connection privileges
GRANT CONNECT ON DATABASE your_database_name TO mcp_user;

-- Step 4: Ensure schema access (already granted in main script, but verify)
GRANT USAGE ON SCHEMA intake, vault TO mcp_user;

-- Step 5: Verify role membership
SELECT 
    r.rolname as role,
    ARRAY_AGG(m.rolname ORDER BY m.rolname) as members
FROM pg_roles r
JOIN pg_auth_members am ON r.oid = am.roleid
JOIN pg_roles m ON am.member = m.oid
WHERE r.rolname IN ('mcp_ingest', 'mcp_promote')
GROUP BY r.rolname;

-- Step 6: Test the user's permissions (run as mcp_user)
-- Switch to mcp_user:
-- SET ROLE mcp_user;

-- Try to directly insert (should fail due to RLS):
-- INSERT INTO intake.raw_loads (batch_id, source, raw_data) 
-- VALUES ('test', 'test', '{"email":"test@test.com"}'::jsonb);
-- Expected: ERROR - new row violates row-level security policy

-- Try using the secure function (should succeed):
-- SELECT * FROM intake.f_ingest_json(
--     ARRAY['{"email":"test@example.com","name":"Test User"}'::jsonb],
--     'test-source',
--     'test-batch-001'
-- );
-- Expected: Success with result message

-- Step 7: Connection string format for environment variables
-- DATABASE_URL=postgresql://mcp_user:your_secure_password@your-neon-host.neon.tech/your_database_name?sslmode=require
-- NEON_DATABASE_URL=postgresql://mcp_user:your_secure_password@your-neon-host.neon.tech/your_database_name?sslmode=require

-- Step 8: Verify the setup
DO $$
DECLARE
    v_user_exists boolean;
    v_has_ingest boolean;
    v_has_promote boolean;
BEGIN
    -- Check if user exists
    SELECT EXISTS(SELECT 1 FROM pg_user WHERE usename = 'mcp_user') INTO v_user_exists;
    
    -- Check role memberships
    SELECT EXISTS(
        SELECT 1 FROM pg_auth_members am
        JOIN pg_roles r ON am.roleid = r.oid
        JOIN pg_roles m ON am.member = m.oid
        WHERE r.rolname = 'mcp_ingest' AND m.rolname = 'mcp_user'
    ) INTO v_has_ingest;
    
    SELECT EXISTS(
        SELECT 1 FROM pg_auth_members am
        JOIN pg_roles r ON am.roleid = r.oid
        JOIN pg_roles m ON am.member = m.oid
        WHERE r.rolname = 'mcp_promote' AND m.rolname = 'mcp_user'
    ) INTO v_has_promote;
    
    -- Report results
    RAISE NOTICE '=== MCP User Setup Verification ===';
    RAISE NOTICE 'User mcp_user exists: %', v_user_exists;
    RAISE NOTICE 'Has mcp_ingest role: %', v_has_ingest;
    RAISE NOTICE 'Has mcp_promote role: %', v_has_promote;
    
    IF v_user_exists AND v_has_ingest AND v_has_promote THEN
        RAISE NOTICE '✅ Setup complete! User is ready for MCP integration.';
    ELSE
        RAISE WARNING '❌ Setup incomplete. Please check user and role grants.';
    END IF;
END $$;
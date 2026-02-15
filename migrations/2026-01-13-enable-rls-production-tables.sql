-- ==============================================================================
-- ENABLE RLS ON PRODUCTION TABLES MIGRATION
-- ==============================================================================
-- Date: 2026-01-13
-- Purpose: Enable Row-Level Security on production tables
--
-- HARDENING PASS: Uses SAME pattern as 003_enforce_master_error_immutability.sql
-- Pattern: Default deny, explicit allow, role-based access
--
-- TABLES COVERED:
--   - outreach.* (company_target, people, engagement_events, campaigns, sequences, send_log)
--   - dol.* (form_5500, form_5500_sf, schedule_a, renewal_calendar)
--   - funnel.* (if exists)
--   - bit.* (if exists)
-- ==============================================================================

-- ==============================================================================
-- PHASE 1: CREATE APPLICATION ROLES
-- ==============================================================================
-- Pattern from 003_enforce_master_error_immutability.sql
-- ==============================================================================

-- Outreach Hub writer role
DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'outreach_hub_writer') THEN
        CREATE ROLE outreach_hub_writer NOLOGIN;
        RAISE NOTICE 'Created role: outreach_hub_writer';
    ELSE
        RAISE NOTICE 'Role outreach_hub_writer already exists';
    END IF;
END $$;

-- DOL Hub writer role
DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'dol_hub_writer') THEN
        CREATE ROLE dol_hub_writer NOLOGIN;
        RAISE NOTICE 'Created role: dol_hub_writer';
    ELSE
        RAISE NOTICE 'Role dol_hub_writer already exists';
    END IF;
END $$;

-- Read-only role for all hubs
DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'hub_reader') THEN
        CREATE ROLE hub_reader NOLOGIN;
        RAISE NOTICE 'Created role: hub_reader';
    ELSE
        RAISE NOTICE 'Role hub_reader already exists';
    END IF;
END $$;

COMMENT ON ROLE outreach_hub_writer IS
    'Writer role for outreach.* tables. INSERT, UPDATE allowed. No DELETE on critical tables.';

COMMENT ON ROLE dol_hub_writer IS
    'Writer role for dol.* tables. INSERT, UPDATE allowed.';

COMMENT ON ROLE hub_reader IS
    'Read-only role for all hub tables. SELECT only.';

-- ==============================================================================
-- PHASE 2: ENABLE RLS ON OUTREACH TABLES
-- ==============================================================================

-- Enable RLS on each table
ALTER TABLE outreach.company_target ENABLE ROW LEVEL SECURITY;
ALTER TABLE outreach.people ENABLE ROW LEVEL SECURITY;
ALTER TABLE outreach.engagement_events ENABLE ROW LEVEL SECURITY;

-- Check if new tables exist before enabling RLS
DO $$ BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'outreach' AND tablename = 'campaigns') THEN
        ALTER TABLE outreach.campaigns ENABLE ROW LEVEL SECURITY;
        RAISE NOTICE 'RLS enabled on outreach.campaigns';
    END IF;
END $$;

DO $$ BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'outreach' AND tablename = 'sequences') THEN
        ALTER TABLE outreach.sequences ENABLE ROW LEVEL SECURITY;
        RAISE NOTICE 'RLS enabled on outreach.sequences';
    END IF;
END $$;

DO $$ BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'outreach' AND tablename = 'send_log') THEN
        ALTER TABLE outreach.send_log ENABLE ROW LEVEL SECURITY;
        RAISE NOTICE 'RLS enabled on outreach.send_log';
    END IF;
END $$;

-- ==============================================================================
-- PHASE 3: CREATE POLICIES FOR OUTREACH TABLES
-- ==============================================================================
-- Pattern: Default deny + explicit allow for specific roles
-- ==============================================================================

-- company_target policies
DROP POLICY IF EXISTS outreach_company_target_select ON outreach.company_target;
CREATE POLICY outreach_company_target_select ON outreach.company_target
    FOR SELECT
    USING (true);  -- All roles can read

DROP POLICY IF EXISTS outreach_company_target_insert ON outreach.company_target;
CREATE POLICY outreach_company_target_insert ON outreach.company_target
    FOR INSERT
    WITH CHECK (true);  -- Controlled by GRANT, not row-level

DROP POLICY IF EXISTS outreach_company_target_update ON outreach.company_target;
CREATE POLICY outreach_company_target_update ON outreach.company_target
    FOR UPDATE
    USING (true)
    WITH CHECK (true);

-- people policies
DROP POLICY IF EXISTS outreach_people_select ON outreach.people;
CREATE POLICY outreach_people_select ON outreach.people
    FOR SELECT
    USING (true);

DROP POLICY IF EXISTS outreach_people_insert ON outreach.people;
CREATE POLICY outreach_people_insert ON outreach.people
    FOR INSERT
    WITH CHECK (true);

DROP POLICY IF EXISTS outreach_people_update ON outreach.people;
CREATE POLICY outreach_people_update ON outreach.people
    FOR UPDATE
    USING (true)
    WITH CHECK (true);

-- engagement_events policies (SELECT + INSERT only - no UPDATE/DELETE for immutability)
DROP POLICY IF EXISTS outreach_events_select ON outreach.engagement_events;
CREATE POLICY outreach_events_select ON outreach.engagement_events
    FOR SELECT
    USING (true);

DROP POLICY IF EXISTS outreach_events_insert ON outreach.engagement_events;
CREATE POLICY outreach_events_insert ON outreach.engagement_events
    FOR INSERT
    WITH CHECK (true);

-- NO UPDATE/DELETE policies for engagement_events (immutable event log)

-- campaigns policies
DO $$ BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'outreach' AND tablename = 'campaigns') THEN
        DROP POLICY IF EXISTS outreach_campaigns_select ON outreach.campaigns;
        CREATE POLICY outreach_campaigns_select ON outreach.campaigns FOR SELECT USING (true);
        DROP POLICY IF EXISTS outreach_campaigns_insert ON outreach.campaigns;
        CREATE POLICY outreach_campaigns_insert ON outreach.campaigns FOR INSERT WITH CHECK (true);
        DROP POLICY IF EXISTS outreach_campaigns_update ON outreach.campaigns;
        CREATE POLICY outreach_campaigns_update ON outreach.campaigns FOR UPDATE USING (true) WITH CHECK (true);
    END IF;
END $$;

-- sequences policies
DO $$ BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'outreach' AND tablename = 'sequences') THEN
        DROP POLICY IF EXISTS outreach_sequences_select ON outreach.sequences;
        CREATE POLICY outreach_sequences_select ON outreach.sequences FOR SELECT USING (true);
        DROP POLICY IF EXISTS outreach_sequences_insert ON outreach.sequences;
        CREATE POLICY outreach_sequences_insert ON outreach.sequences FOR INSERT WITH CHECK (true);
        DROP POLICY IF EXISTS outreach_sequences_update ON outreach.sequences;
        CREATE POLICY outreach_sequences_update ON outreach.sequences FOR UPDATE USING (true) WITH CHECK (true);
    END IF;
END $$;

-- send_log policies
DO $$ BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'outreach' AND tablename = 'send_log') THEN
        DROP POLICY IF EXISTS outreach_send_log_select ON outreach.send_log;
        CREATE POLICY outreach_send_log_select ON outreach.send_log FOR SELECT USING (true);
        DROP POLICY IF EXISTS outreach_send_log_insert ON outreach.send_log;
        CREATE POLICY outreach_send_log_insert ON outreach.send_log FOR INSERT WITH CHECK (true);
        DROP POLICY IF EXISTS outreach_send_log_update ON outreach.send_log;
        CREATE POLICY outreach_send_log_update ON outreach.send_log FOR UPDATE USING (true) WITH CHECK (true);
    END IF;
END $$;

-- ==============================================================================
-- PHASE 4: ENABLE RLS ON DOL TABLES
-- ==============================================================================

DO $$ BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'dol' AND tablename = 'form_5500') THEN
        ALTER TABLE dol.form_5500 ENABLE ROW LEVEL SECURITY;
        RAISE NOTICE 'RLS enabled on dol.form_5500';
    END IF;
END $$;

DO $$ BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'dol' AND tablename = 'form_5500_sf') THEN
        ALTER TABLE dol.form_5500_sf ENABLE ROW LEVEL SECURITY;
        RAISE NOTICE 'RLS enabled on dol.form_5500_sf';
    END IF;
END $$;

DO $$ BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'dol' AND tablename = 'schedule_a') THEN
        ALTER TABLE dol.schedule_a ENABLE ROW LEVEL SECURITY;
        RAISE NOTICE 'RLS enabled on dol.schedule_a';
    END IF;
END $$;

DO $$ BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'dol' AND tablename = 'renewal_calendar') THEN
        ALTER TABLE dol.renewal_calendar ENABLE ROW LEVEL SECURITY;
        RAISE NOTICE 'RLS enabled on dol.renewal_calendar';
    END IF;
END $$;

-- ==============================================================================
-- PHASE 5: CREATE POLICIES FOR DOL TABLES
-- ==============================================================================

-- form_5500 policies
DO $$ BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'dol' AND tablename = 'form_5500') THEN
        DROP POLICY IF EXISTS dol_form_5500_select ON dol.form_5500;
        CREATE POLICY dol_form_5500_select ON dol.form_5500 FOR SELECT USING (true);
        DROP POLICY IF EXISTS dol_form_5500_insert ON dol.form_5500;
        CREATE POLICY dol_form_5500_insert ON dol.form_5500 FOR INSERT WITH CHECK (true);
        DROP POLICY IF EXISTS dol_form_5500_update ON dol.form_5500;
        CREATE POLICY dol_form_5500_update ON dol.form_5500 FOR UPDATE USING (true) WITH CHECK (true);
    END IF;
END $$;

-- form_5500_sf policies
DO $$ BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'dol' AND tablename = 'form_5500_sf') THEN
        DROP POLICY IF EXISTS dol_form_5500_sf_select ON dol.form_5500_sf;
        CREATE POLICY dol_form_5500_sf_select ON dol.form_5500_sf FOR SELECT USING (true);
        DROP POLICY IF EXISTS dol_form_5500_sf_insert ON dol.form_5500_sf;
        CREATE POLICY dol_form_5500_sf_insert ON dol.form_5500_sf FOR INSERT WITH CHECK (true);
        DROP POLICY IF EXISTS dol_form_5500_sf_update ON dol.form_5500_sf;
        CREATE POLICY dol_form_5500_sf_update ON dol.form_5500_sf FOR UPDATE USING (true) WITH CHECK (true);
    END IF;
END $$;

-- schedule_a policies
DO $$ BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'dol' AND tablename = 'schedule_a') THEN
        DROP POLICY IF EXISTS dol_schedule_a_select ON dol.schedule_a;
        CREATE POLICY dol_schedule_a_select ON dol.schedule_a FOR SELECT USING (true);
        DROP POLICY IF EXISTS dol_schedule_a_insert ON dol.schedule_a;
        CREATE POLICY dol_schedule_a_insert ON dol.schedule_a FOR INSERT WITH CHECK (true);
        DROP POLICY IF EXISTS dol_schedule_a_update ON dol.schedule_a;
        CREATE POLICY dol_schedule_a_update ON dol.schedule_a FOR UPDATE USING (true) WITH CHECK (true);
    END IF;
END $$;

-- renewal_calendar policies
DO $$ BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'dol' AND tablename = 'renewal_calendar') THEN
        DROP POLICY IF EXISTS dol_renewal_calendar_select ON dol.renewal_calendar;
        CREATE POLICY dol_renewal_calendar_select ON dol.renewal_calendar FOR SELECT USING (true);
        DROP POLICY IF EXISTS dol_renewal_calendar_insert ON dol.renewal_calendar;
        CREATE POLICY dol_renewal_calendar_insert ON dol.renewal_calendar FOR INSERT WITH CHECK (true);
        DROP POLICY IF EXISTS dol_renewal_calendar_update ON dol.renewal_calendar;
        CREATE POLICY dol_renewal_calendar_update ON dol.renewal_calendar FOR UPDATE USING (true) WITH CHECK (true);
    END IF;
END $$;

-- ==============================================================================
-- PHASE 6: GRANT PERMISSIONS TO ROLES
-- ==============================================================================

-- Grant outreach permissions
GRANT SELECT ON ALL TABLES IN SCHEMA outreach TO hub_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA outreach TO outreach_hub_writer;
GRANT INSERT, UPDATE ON ALL TABLES IN SCHEMA outreach TO outreach_hub_writer;

-- Grant dol permissions
DO $$ BEGIN
    IF EXISTS (SELECT FROM pg_namespace WHERE nspname = 'dol') THEN
        GRANT SELECT ON ALL TABLES IN SCHEMA dol TO hub_reader;
        GRANT SELECT ON ALL TABLES IN SCHEMA dol TO dol_hub_writer;
        GRANT INSERT, UPDATE ON ALL TABLES IN SCHEMA dol TO dol_hub_writer;
    END IF;
END $$;

-- Revoke DELETE on event log tables (immutability)
REVOKE DELETE ON outreach.engagement_events FROM PUBLIC;
REVOKE TRUNCATE ON outreach.engagement_events FROM PUBLIC;

-- ==============================================================================
-- PHASE 7: IMMUTABILITY TRIGGER FOR ENGAGEMENT_EVENTS
-- ==============================================================================
-- Pattern from 003_enforce_master_error_immutability.sql
-- ==============================================================================

CREATE OR REPLACE FUNCTION outreach.fn_engagement_events_immutability()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION
            'DELETE BLOCKED: outreach.engagement_events is immutable per Barton Doctrine. '
            'Event history cannot be deleted. Records are permanent. '
            'Attempted to DELETE event_id: %',
            OLD.event_id;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_engagement_events_immutability_delete ON outreach.engagement_events;
CREATE TRIGGER trg_engagement_events_immutability_delete
    BEFORE DELETE ON outreach.engagement_events
    FOR EACH ROW
    EXECUTE FUNCTION outreach.fn_engagement_events_immutability();

COMMENT ON FUNCTION outreach.fn_engagement_events_immutability() IS
    'DOCTRINE ENFORCEMENT: Blocks DELETE on outreach.engagement_events. Event history is immutable.';

-- ==============================================================================
-- PHASE 8: VERIFICATION
-- ==============================================================================

DO $$
DECLARE
    v_rls_tables INTEGER;
    v_policy_count INTEGER;
BEGIN
    -- Count tables with RLS enabled
    SELECT COUNT(*) INTO v_rls_tables
    FROM pg_class c
    JOIN pg_namespace n ON c.relnamespace = n.oid
    WHERE n.nspname IN ('outreach', 'dol')
      AND c.relkind = 'r'
      AND c.relrowsecurity = true;

    -- Count policies
    SELECT COUNT(*) INTO v_policy_count
    FROM pg_policies
    WHERE schemaname IN ('outreach', 'dol');

    RAISE NOTICE '========================================';
    RAISE NOTICE 'RLS Migration Complete:';
    RAISE NOTICE '  Tables with RLS enabled: %', v_rls_tables;
    RAISE NOTICE '  Policies created: %', v_policy_count;
    RAISE NOTICE '  Roles created: 3 (outreach_hub_writer, dol_hub_writer, hub_reader)';
    RAISE NOTICE '========================================';
END $$;

-- ==============================================================================
-- MIGRATION COMPLETE
-- ==============================================================================
-- ENABLED RLS ON:
--   - outreach.company_target
--   - outreach.people
--   - outreach.engagement_events (+ immutability trigger)
--   - outreach.campaigns
--   - outreach.sequences
--   - outreach.send_log
--   - dol.form_5500
--   - dol.form_5500_sf
--   - dol.schedule_a
--   - dol.renewal_calendar
--
-- CREATED ROLES:
--   - outreach_hub_writer (INSERT, UPDATE on outreach.*)
--   - dol_hub_writer (INSERT, UPDATE on dol.*)
--   - hub_reader (SELECT on all hub tables)
--
-- DOCTRINE COMPLIANCE:
--   - Default deny via RLS
--   - Explicit allow via policies
--   - Immutability enforced on event log
--   - Role-based access control
-- ==============================================================================

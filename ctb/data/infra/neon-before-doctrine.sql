-- ─────────────────────────────────────────────
-- 📁 CTB Classification Metadata
-- ─────────────────────────────────────────────
-- CTB Branch: data/infra
-- Barton ID: 05.01.01
-- Unique ID: CTB-EFD49ECA
-- Blueprint Hash:
-- Last Updated: 2025-10-23
-- Enforcement: ORBT
-- ─────────────────────────────────────────────

-- Barton Outreach Core - Neon PostgreSQL Schema
-- Secure RLS-enabled schema with SECURITY DEFINER functions

-- Create schemas
CREATE SCHEMA IF NOT EXISTS intake;
CREATE SCHEMA IF NOT EXISTS vault;

-- Create roles (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mcp_ingest') THEN
        CREATE ROLE mcp_ingest;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mcp_promote') THEN
        CREATE ROLE mcp_promote;
    END IF;
END $$;

-- Create intake.raw_loads table
CREATE TABLE IF NOT EXISTS intake.raw_loads (
    load_id BIGSERIAL PRIMARY KEY,
    batch_id TEXT NOT NULL,
    source TEXT NOT NULL,
    raw_data JSONB NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'promoted', 'failed', 'duplicate')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    promoted_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_raw_loads_batch_id ON intake.raw_loads(batch_id);
CREATE INDEX IF NOT EXISTS idx_raw_loads_source ON intake.raw_loads(source);
CREATE INDEX IF NOT EXISTS idx_raw_loads_status ON intake.raw_loads(status);
CREATE INDEX IF NOT EXISTS idx_raw_loads_created_at ON intake.raw_loads(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_raw_loads_raw_data_email ON intake.raw_loads((raw_data->>'email'));

-- Create vault.contacts table
CREATE TABLE IF NOT EXISTS vault.contacts (
    contact_id BIGSERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    phone TEXT,
    company TEXT,
    title TEXT,
    source TEXT NOT NULL,
    tags JSONB DEFAULT '[]'::jsonb,
    custom_fields JSONB DEFAULT '{}'::jsonb,
    load_id BIGINT REFERENCES intake.raw_loads(load_id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity_at TIMESTAMPTZ,
    score NUMERIC(5,2) DEFAULT 0.00,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'bounced', 'unsubscribed'))
);

-- Create indexes for contacts
CREATE INDEX IF NOT EXISTS idx_contacts_email ON vault.contacts(email);
CREATE INDEX IF NOT EXISTS idx_contacts_source ON vault.contacts(source);
CREATE INDEX IF NOT EXISTS idx_contacts_created_at ON vault.contacts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_contacts_score ON vault.contacts(score DESC);
CREATE INDEX IF NOT EXISTS idx_contacts_status ON vault.contacts(status);
CREATE INDEX IF NOT EXISTS idx_contacts_company ON vault.contacts(company);

-- Enable Row Level Security
ALTER TABLE intake.raw_loads ENABLE ROW LEVEL SECURITY;
ALTER TABLE vault.contacts ENABLE ROW LEVEL SECURITY;

-- Create RLS policies denying direct DML
CREATE POLICY no_direct_insert ON intake.raw_loads FOR INSERT TO PUBLIC USING (false);
CREATE POLICY no_direct_update ON intake.raw_loads FOR UPDATE TO PUBLIC USING (false);
CREATE POLICY no_direct_delete ON intake.raw_loads FOR DELETE TO PUBLIC USING (false);

CREATE POLICY no_direct_insert ON vault.contacts FOR INSERT TO PUBLIC USING (false);
CREATE POLICY no_direct_update ON vault.contacts FOR UPDATE TO PUBLIC USING (false);
CREATE POLICY no_direct_delete ON vault.contacts FOR DELETE TO PUBLIC USING (false);

-- Allow SELECT for monitoring/debugging
CREATE POLICY allow_select ON intake.raw_loads FOR SELECT TO PUBLIC USING (true);
CREATE POLICY allow_select ON vault.contacts FOR SELECT TO PUBLIC USING (true);

-- Drop functions if they exist (for clean recreation)
DROP FUNCTION IF EXISTS intake.f_ingest_json(jsonb[], text, text);
DROP FUNCTION IF EXISTS vault.f_promote_contacts(bigint[]);

-- Create SECURITY DEFINER function for JSON ingestion
CREATE OR REPLACE FUNCTION intake.f_ingest_json(
    p_rows jsonb[],
    p_source text,
    p_batch_id text
) RETURNS TABLE (
    load_id bigint,
    status text,
    message text
) 
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = intake, pg_catalog
AS $$
DECLARE
    v_row jsonb;
    v_load_id bigint;
    v_email text;
    v_existing_count int;
    v_inserted_count int := 0;
    v_skipped_count int := 0;
BEGIN
    -- Validate inputs
    IF p_rows IS NULL OR array_length(p_rows, 1) IS NULL THEN
        RETURN QUERY SELECT 
            NULL::bigint,
            'error'::text, 
            'No rows provided'::text;
        RETURN;
    END IF;

    IF p_source IS NULL OR p_source = '' THEN
        p_source := 'unknown';
    END IF;

    IF p_batch_id IS NULL OR p_batch_id = '' THEN
        p_batch_id := 'batch-' || extract(epoch from now())::text;
    END IF;

    -- Process each row
    FOREACH v_row IN ARRAY p_rows
    LOOP
        -- Extract email for duplicate checking
        v_email := v_row->>'email';
        
        -- Skip if no email
        IF v_email IS NULL OR v_email = '' THEN
            v_skipped_count := v_skipped_count + 1;
            CONTINUE;
        END IF;

        -- Check for existing email in recent loads (last 30 days)
        SELECT COUNT(*) INTO v_existing_count
        FROM intake.raw_loads
        WHERE raw_data->>'email' = v_email
          AND created_at > NOW() - INTERVAL '30 days'
          AND status != 'failed';

        IF v_existing_count > 0 THEN
            -- Insert as duplicate
            INSERT INTO intake.raw_loads (batch_id, source, raw_data, status, metadata)
            VALUES (
                p_batch_id,
                p_source,
                v_row,
                'duplicate',
                jsonb_build_object(
                    'duplicate_of_email', v_email,
                    'timestamp', now()
                )
            ) RETURNING load_id INTO v_load_id;
            
            v_skipped_count := v_skipped_count + 1;
        ELSE
            -- Insert new record
            INSERT INTO intake.raw_loads (batch_id, source, raw_data, status)
            VALUES (
                p_batch_id,
                p_source,
                v_row,
                'pending'
            ) RETURNING load_id INTO v_load_id;
            
            v_inserted_count := v_inserted_count + 1;
        END IF;
    END LOOP;

    -- Return summary
    RETURN QUERY SELECT 
        NULL::bigint,
        'success'::text,
        format('Batch %s: Inserted %s, Skipped %s (duplicates)', 
               p_batch_id, v_inserted_count, v_skipped_count)::text;
END;
$$;

-- Create SECURITY DEFINER function for promoting contacts
CREATE OR REPLACE FUNCTION vault.f_promote_contacts(
    p_load_ids bigint[]
) RETURNS TABLE (
    promoted_count int,
    updated_count int,
    failed_count int,
    message text
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = vault, intake, pg_catalog
AS $$
DECLARE
    v_promoted int := 0;
    v_updated int := 0;
    v_failed int := 0;
    v_load_id bigint;
    v_raw_data jsonb;
    v_email text;
    v_existing_id bigint;
BEGIN
    -- If no IDs provided, promote all pending
    IF p_load_ids IS NULL OR array_length(p_load_ids, 1) IS NULL THEN
        SELECT array_agg(load_id) INTO p_load_ids
        FROM intake.raw_loads
        WHERE status = 'pending'
        LIMIT 1000; -- Process max 1000 at a time
    END IF;

    -- Process each load
    IF p_load_ids IS NOT NULL THEN
        FOREACH v_load_id IN ARRAY p_load_ids
        LOOP
            -- Get raw data
            SELECT raw_data, raw_data->>'email' 
            INTO v_raw_data, v_email
            FROM intake.raw_loads
            WHERE load_id = v_load_id
              AND status = 'pending';

            -- Skip if not found or not pending
            IF NOT FOUND OR v_email IS NULL THEN
                v_failed := v_failed + 1;
                CONTINUE;
            END IF;

            -- Check if contact exists
            SELECT contact_id INTO v_existing_id
            FROM vault.contacts
            WHERE email = v_email;

            IF v_existing_id IS NOT NULL THEN
                -- Update existing contact
                UPDATE vault.contacts
                SET 
                    name = COALESCE(v_raw_data->>'name', name),
                    phone = COALESCE(v_raw_data->>'phone', phone),
                    company = COALESCE(v_raw_data->>'company', company),
                    title = COALESCE(v_raw_data->>'title', title),
                    custom_fields = custom_fields || COALESCE(v_raw_data->'custom_fields', '{}'::jsonb),
                    updated_at = NOW()
                WHERE contact_id = v_existing_id;
                
                v_updated := v_updated + 1;
            ELSE
                -- Insert new contact
                INSERT INTO vault.contacts (
                    email,
                    name,
                    phone,
                    company,
                    title,
                    source,
                    tags,
                    custom_fields,
                    load_id
                ) VALUES (
                    v_email,
                    v_raw_data->>'name',
                    v_raw_data->>'phone',
                    v_raw_data->>'company',
                    v_raw_data->>'title',
                    COALESCE(v_raw_data->>'source', 'promoted'),
                    COALESCE(v_raw_data->'tags', '[]'::jsonb),
                    COALESCE(v_raw_data->'custom_fields', '{}'::jsonb),
                    v_load_id
                );
                
                v_promoted := v_promoted + 1;
            END IF;

            -- Mark load as promoted
            UPDATE intake.raw_loads
            SET status = 'promoted',
                promoted_at = NOW()
            WHERE load_id = v_load_id;

        END LOOP;
    END IF;

    -- Return summary
    RETURN QUERY SELECT 
        v_promoted,
        v_updated,
        v_failed,
        format('Promoted: %s new, %s updated, %s failed', 
               v_promoted, v_updated, v_failed)::text;
END;
$$;

-- Grant EXECUTE permissions to roles
GRANT EXECUTE ON FUNCTION intake.f_ingest_json(jsonb[], text, text) TO mcp_ingest;
GRANT EXECUTE ON FUNCTION vault.f_promote_contacts(bigint[]) TO mcp_promote;

-- Grant USAGE on schemas to roles
GRANT USAGE ON SCHEMA intake TO mcp_ingest, mcp_promote;
GRANT USAGE ON SCHEMA vault TO mcp_promote;

-- Grant USAGE on sequences (for RETURNING clauses in functions)
GRANT USAGE ON SEQUENCE intake.raw_loads_load_id_seq TO mcp_ingest;
GRANT USAGE ON SEQUENCE vault.contacts_contact_id_seq TO mcp_promote;

-- Create convenience view for latest loads
CREATE OR REPLACE VIEW intake.latest_100 AS
SELECT 
    load_id,
    batch_id,
    source,
    raw_data->>'email' as email,
    raw_data->>'name' as name,
    raw_data->>'company' as company,
    status,
    created_at,
    promoted_at
FROM intake.raw_loads
ORDER BY created_at DESC
LIMIT 100;

-- Grant SELECT on view
GRANT SELECT ON intake.latest_100 TO mcp_ingest, mcp_promote;

-- Create audit log table for tracking operations
CREATE TABLE IF NOT EXISTS intake.audit_log (
    audit_id BIGSERIAL PRIMARY KEY,
    operation TEXT NOT NULL,
    user_name TEXT DEFAULT CURRENT_USER,
    batch_id TEXT,
    record_count INT,
    result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_operation ON intake.audit_log(operation);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON intake.audit_log(created_at DESC);

-- Create function to log operations
CREATE OR REPLACE FUNCTION intake.log_operation(
    p_operation TEXT,
    p_batch_id TEXT,
    p_count INT,
    p_result JSONB
) RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO intake.audit_log (operation, batch_id, record_count, result)
    VALUES (p_operation, p_batch_id, p_count, p_result);
END;
$$;

-- Example usage comments
COMMENT ON FUNCTION intake.f_ingest_json IS 'Securely ingest JSON data into raw_loads table. Usage: SELECT * FROM intake.f_ingest_json(ARRAY[''{"email":"test@example.com","name":"Test User"}''::jsonb], ''composio.tool'', ''batch-123'');';
COMMENT ON FUNCTION vault.f_promote_contacts IS 'Securely promote contacts from intake to vault. Usage: SELECT * FROM vault.f_promote_contacts(ARRAY[1,2,3]::bigint[]);';

-- Grant all needed permissions summary
DO $$
BEGIN
    RAISE NOTICE 'Database setup complete. Required role grants:';
    RAISE NOTICE '  - GRANT mcp_ingest, mcp_promote TO <mcp_user>;';
    RAISE NOTICE '  - Connection string should use <mcp_user> credentials';
    RAISE NOTICE '  - No direct table DML permissions needed or granted';
END $$;
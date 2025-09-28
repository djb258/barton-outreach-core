-- ===================================================
-- NEON DATABASE SCHEMA: Company & People Integration
-- ===================================================

-- Enable Row Level Security and required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ===================================================
-- 1. SCHEMA CREATION
-- ===================================================

-- Create schemas if they don't exist
CREATE SCHEMA IF NOT EXISTS company;
CREATE SCHEMA IF NOT EXISTS people;
CREATE SCHEMA IF NOT EXISTS intake;
CREATE SCHEMA IF NOT EXISTS vault;

-- ===================================================
-- 2. COMPANY SCHEMA (Your Provided Schema)
-- ===================================================

-- Core company (lean)
CREATE TABLE IF NOT EXISTS company.company (
  company_id   BIGSERIAL PRIMARY KEY,
  company_name TEXT,
  ein          TEXT,
  website_url  TEXT,
  linkedin_url TEXT,
  news_url     TEXT,
  -- address (lean)
  address_line1 TEXT,
  address_line2 TEXT,
  city          TEXT,
  state         TEXT,
  postal_code   TEXT,
  country       TEXT,
  -- renewal (month-only; default 120d notice = 4 months)
  renewal_month SMALLINT CHECK (renewal_month BETWEEN 1 AND 12),
  renewal_notice_window_days INT DEFAULT 120,
  -- audit fields
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_company_renewal_month ON company.company(renewal_month);
CREATE INDEX IF NOT EXISTS ix_company_name ON company.company USING gin(company_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS ix_company_website ON company.company(website_url);
CREATE INDEX IF NOT EXISTS ix_company_linkedin ON company.company(linkedin_url);

-- Exactly 3 slots per company: CEO / CFO / HR
CREATE TABLE IF NOT EXISTS company.company_slot (
  company_slot_id BIGSERIAL PRIMARY KEY,
  company_id      BIGINT NOT NULL REFERENCES company.company(company_id) ON DELETE CASCADE,
  role_code       TEXT   NOT NULL CHECK (role_code IN ('CEO','CFO','HR')),
  contact_id      BIGINT,  -- FK to people.contact (nullable until assigned)
  assigned_at     TIMESTAMPTZ,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (company_id, role_code)
);

CREATE INDEX IF NOT EXISTS ix_company_slot_company ON company.company_slot(company_id);
CREATE INDEX IF NOT EXISTS ix_company_slot_contact ON company.company_slot(contact_id);
CREATE INDEX IF NOT EXISTS ix_company_slot_role ON company.company_slot(role_code);

-- ===================================================
-- 3. PEOPLE SCHEMA (Contact Management)
-- ===================================================

CREATE TABLE IF NOT EXISTS people.contact (
  contact_id    BIGSERIAL PRIMARY KEY,
  email         TEXT UNIQUE NOT NULL,
  first_name    TEXT,
  last_name     TEXT,
  full_name     TEXT GENERATED ALWAYS AS (
    CASE 
      WHEN first_name IS NOT NULL AND last_name IS NOT NULL 
      THEN first_name || ' ' || last_name
      WHEN first_name IS NOT NULL THEN first_name
      WHEN last_name IS NOT NULL THEN last_name
      ELSE NULL
    END
  ) STORED,
  phone         TEXT,
  linkedin_url  TEXT,
  title         TEXT,
  company_id    BIGINT REFERENCES company.company(company_id),
  -- email verification status with dot colors
  email_status  TEXT DEFAULT 'pending' CHECK (email_status IN ('verified', 'pending', 'invalid', 'bounced')),
  email_status_color TEXT GENERATED ALWAYS AS (
    CASE email_status
      WHEN 'verified' THEN 'green'
      WHEN 'pending' THEN 'yellow' 
      WHEN 'invalid' THEN 'red'
      WHEN 'bounced' THEN 'red'
      ELSE 'gray'
    END
  ) STORED,
  verification_date TIMESTAMPTZ,
  -- source and metadata
  source        TEXT DEFAULT 'manual',
  tags          JSONB DEFAULT '[]'::jsonb,
  custom_fields JSONB DEFAULT '{}'::jsonb,
  -- audit
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_contact_email ON people.contact(email);
CREATE INDEX IF NOT EXISTS ix_contact_full_name ON people.contact USING gin(full_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS ix_contact_company ON people.contact(company_id);
CREATE INDEX IF NOT EXISTS ix_contact_status ON people.contact(email_status);
CREATE INDEX IF NOT EXISTS ix_contact_source ON people.contact(source);
CREATE INDEX IF NOT EXISTS ix_contact_tags ON people.contact USING gin(tags);
CREATE INDEX IF NOT EXISTS ix_contact_created ON people.contact(created_at);

-- Now add the FK to company_slot after people.contact exists
ALTER TABLE company.company_slot 
ADD CONSTRAINT fk_company_slot_contact 
FOREIGN KEY (contact_id) REFERENCES people.contact(contact_id) ON DELETE SET NULL;

-- ===================================================
-- 4. INTAKE SCHEMA (Data Ingestion)
-- ===================================================

CREATE TABLE IF NOT EXISTS intake.raw_loads (
  load_id       BIGSERIAL PRIMARY KEY,
  batch_id      TEXT NOT NULL,
  source        TEXT NOT NULL DEFAULT 'manual',
  raw_data      JSONB NOT NULL,
  status        TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processed', 'failed')),
  processed_at  TIMESTAMPTZ,
  error_message TEXT,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_raw_loads_batch ON intake.raw_loads(batch_id);
CREATE INDEX IF NOT EXISTS ix_raw_loads_status ON intake.raw_loads(status);
CREATE INDEX IF NOT EXISTS ix_raw_loads_source ON intake.raw_loads(source);
CREATE INDEX IF NOT EXISTS ix_raw_loads_created ON intake.raw_loads(created_at);

-- ===================================================
-- 5. VAULT SCHEMA (Processed Data)
-- ===================================================

-- Contact promotion tracking
CREATE TABLE IF NOT EXISTS vault.contact_promotions (
  promotion_id  BIGSERIAL PRIMARY KEY,
  load_id       BIGINT NOT NULL REFERENCES intake.raw_loads(load_id),
  contact_id    BIGINT NOT NULL REFERENCES people.contact(contact_id),
  promoted_at   TIMESTAMPTZ DEFAULT NOW(),
  promotion_type TEXT DEFAULT 'standard' CHECK (promotion_type IN ('standard', 'bulk', 'automated'))
);

CREATE INDEX IF NOT EXISTS ix_promotions_load ON vault.contact_promotions(load_id);
CREATE INDEX IF NOT EXISTS ix_promotions_contact ON vault.contact_promotions(contact_id);
CREATE INDEX IF NOT EXISTS ix_promotions_date ON vault.contact_promotions(promoted_at);

-- ===================================================
-- 6. ROW LEVEL SECURITY (RLS)
-- ===================================================

-- Enable RLS on all tables
ALTER TABLE company.company ENABLE ROW LEVEL SECURITY;
ALTER TABLE company.company_slot ENABLE ROW LEVEL SECURITY;
ALTER TABLE people.contact ENABLE ROW LEVEL SECURITY;
ALTER TABLE intake.raw_loads ENABLE ROW LEVEL SECURITY;
ALTER TABLE vault.contact_promotions ENABLE ROW LEVEL SECURITY;

-- ===================================================
-- 7. SECURITY ROLES
-- ===================================================

-- MCP roles for secure operations
DO $$
BEGIN
    -- Create roles if they don't exist
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mcp_ingest') THEN
        CREATE ROLE mcp_ingest;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mcp_promote') THEN
        CREATE ROLE mcp_promote;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
        CREATE ROLE app_user;
    END IF;
END
$$;

-- Grant permissions for MCP operations
GRANT USAGE ON SCHEMA intake TO mcp_ingest;
GRANT INSERT, SELECT ON intake.raw_loads TO mcp_ingest;
GRANT USAGE ON SEQUENCE intake.raw_loads_load_id_seq TO mcp_ingest;

GRANT USAGE ON SCHEMA vault, people, company TO mcp_promote;
GRANT SELECT ON intake.raw_loads TO mcp_promote;
GRANT INSERT, SELECT, UPDATE ON people.contact TO mcp_promote;
GRANT INSERT ON vault.contact_promotions TO mcp_promote;
GRANT SELECT ON company.company, company.company_slot TO mcp_promote;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA people, vault TO mcp_promote;

-- Application user permissions
GRANT USAGE ON SCHEMA company, people, vault TO app_user;
GRANT SELECT ON ALL TABLES IN SCHEMA company, people, vault TO app_user;

-- ===================================================
-- 8. RLS POLICIES
-- ===================================================

-- Company policies - allow read for app users
CREATE POLICY company_select_policy ON company.company
    FOR SELECT TO app_user USING (true);

CREATE POLICY company_slot_select_policy ON company.company_slot  
    FOR SELECT TO app_user USING (true);

-- Contact policies - allow app users to see all contacts
CREATE POLICY contact_select_policy ON people.contact
    FOR SELECT TO app_user USING (true);

-- MCP promotion policy
CREATE POLICY contact_mcp_policy ON people.contact
    FOR ALL TO mcp_promote USING (true);

-- Intake policies - MCP ingest can insert
CREATE POLICY raw_loads_ingest_policy ON intake.raw_loads
    FOR INSERT TO mcp_ingest WITH CHECK (true);

CREATE POLICY raw_loads_promote_policy ON intake.raw_loads
    FOR SELECT TO mcp_promote USING (true);

-- Vault policies
CREATE POLICY promotions_policy ON vault.contact_promotions
    FOR ALL TO mcp_promote USING (true);

CREATE POLICY promotions_select_policy ON vault.contact_promotions
    FOR SELECT TO app_user USING (true);

-- ===================================================
-- 9. SECURE FUNCTIONS
-- ===================================================

-- Secure ingestion function (SECURITY DEFINER)
CREATE OR REPLACE FUNCTION intake.f_ingest_json(
    p_rows jsonb[],
    p_source text DEFAULT 'composio',
    p_batch_id text DEFAULT NULL
) RETURNS TABLE (
    load_id bigint,
    status text,
    message text
) LANGUAGE plpgsql SECURITY DEFINER
SET search_path = intake, pg_temp
AS $$
DECLARE
    v_batch_id text;
    v_row jsonb;
    v_load_id bigint;
BEGIN
    -- Generate batch ID if not provided
    v_batch_id := COALESCE(p_batch_id, 'batch_' || extract(epoch from now())::text || '_' || substr(gen_random_uuid()::text, 1, 8));
    
    -- Process each row
    FOREACH v_row IN ARRAY p_rows LOOP
        INSERT INTO intake.raw_loads (batch_id, source, raw_data)
        VALUES (v_batch_id, p_source, v_row)
        RETURNING intake.raw_loads.load_id INTO v_load_id;
        
        RETURN QUERY SELECT v_load_id, 'pending'::text, 'Ingested successfully'::text;
    END LOOP;
    
    -- Final summary
    RETURN QUERY SELECT 
        NULL::bigint,
        'batch_complete'::text, 
        format('Batch %s: %s rows ingested', v_batch_id, array_length(p_rows, 1))::text;
END;
$$;

-- Secure promotion function (SECURITY DEFINER)  
CREATE OR REPLACE FUNCTION vault.f_promote_contacts(
    p_load_ids bigint[] DEFAULT NULL
) RETURNS TABLE (
    contact_id bigint,
    email text,
    status text,
    message text
) LANGUAGE plpgsql SECURITY DEFINER
SET search_path = vault, people, intake, company, pg_temp
AS $$
DECLARE
    v_load record;
    v_contact_id bigint;
    v_company_id bigint;
    v_data jsonb;
BEGIN
    -- Get loads to process
    FOR v_load IN 
        SELECT rl.load_id, rl.raw_data 
        FROM intake.raw_loads rl
        WHERE (p_load_ids IS NULL OR rl.load_id = ANY(p_load_ids))
        AND rl.status = 'pending'
        ORDER BY rl.load_id
    LOOP
        v_data := v_load.raw_data;
        
        -- Skip if no email
        IF v_data->>'email' IS NULL THEN
            RETURN QUERY SELECT NULL::bigint, NULL::text, 'skipped'::text, 'No email provided'::text;
            CONTINUE;
        END IF;
        
        -- Find or create company if provided
        v_company_id := NULL;
        IF v_data->>'company_name' IS NOT NULL THEN
            SELECT comp.company_id INTO v_company_id
            FROM company.company comp
            WHERE comp.company_name ILIKE v_data->>'company_name'
            LIMIT 1;
            
            -- Create company if not found
            IF v_company_id IS NULL THEN
                INSERT INTO company.company (company_name, website_url)
                VALUES (
                    v_data->>'company_name',
                    v_data->>'company_website'
                )
                RETURNING company_id INTO v_company_id;
            END IF;
        END IF;
        
        -- Insert or update contact
        INSERT INTO people.contact (
            email, 
            first_name, 
            last_name,
            phone,
            linkedin_url,
            title,
            company_id,
            source,
            custom_fields
        ) VALUES (
            v_data->>'email',
            v_data->>'first_name',
            v_data->>'last_name', 
            v_data->>'phone',
            v_data->>'linkedin_url',
            v_data->>'title',
            v_company_id,
            v_data->>'source',
            v_data
        )
        ON CONFLICT (email) DO UPDATE SET
            first_name = COALESCE(EXCLUDED.first_name, people.contact.first_name),
            last_name = COALESCE(EXCLUDED.last_name, people.contact.last_name),
            phone = COALESCE(EXCLUDED.phone, people.contact.phone),
            linkedin_url = COALESCE(EXCLUDED.linkedin_url, people.contact.linkedin_url),
            title = COALESCE(EXCLUDED.title, people.contact.title),
            company_id = COALESCE(EXCLUDED.company_id, people.contact.company_id),
            custom_fields = EXCLUDED.custom_fields,
            updated_at = NOW()
        RETURNING people.contact.contact_id INTO v_contact_id;
        
        -- Track promotion
        INSERT INTO vault.contact_promotions (load_id, contact_id)
        VALUES (v_load.load_id, v_contact_id);
        
        -- Mark load as processed
        UPDATE intake.raw_loads 
        SET status = 'processed', processed_at = NOW()
        WHERE load_id = v_load.load_id;
        
        RETURN QUERY SELECT 
            v_contact_id,
            v_data->>'email',
            'promoted'::text,
            'Contact created/updated successfully'::text;
    END LOOP;
END;
$$;

-- ===================================================
-- 10. UPDATE TRIGGERS
-- ===================================================

-- Update triggers for timestamp management
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
CREATE TRIGGER update_company_updated_at BEFORE UPDATE ON company.company
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_company_slot_updated_at BEFORE UPDATE ON company.company_slot  
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contact_updated_at BEFORE UPDATE ON people.contact
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ===================================================
-- 11. UTILITY VIEWS
-- ===================================================

-- Company with contact counts
CREATE OR REPLACE VIEW company.v_company_summary AS
SELECT 
    c.company_id,
    c.company_name,
    c.website_url,
    c.linkedin_url,
    c.renewal_month,
    COUNT(pc.contact_id) as contact_count,
    COUNT(CASE WHEN pc.email_status = 'verified' THEN 1 END) as verified_contacts,
    COUNT(cs.company_slot_id) as filled_slots,
    ARRAY_AGG(cs.role_code ORDER BY cs.role_code) FILTER (WHERE cs.contact_id IS NOT NULL) as filled_roles
FROM company.company c
LEFT JOIN people.contact pc ON c.company_id = pc.company_id  
LEFT JOIN company.company_slot cs ON c.company_id = cs.company_id AND cs.contact_id IS NOT NULL
GROUP BY c.company_id, c.company_name, c.website_url, c.linkedin_url, c.renewal_month;

-- Contact with company info and slot assignments
CREATE OR REPLACE VIEW people.v_contact_details AS
SELECT 
    pc.contact_id,
    pc.email,
    pc.full_name,
    pc.first_name,
    pc.last_name,
    pc.phone,
    pc.title,
    pc.email_status,
    pc.email_status_color,
    pc.source,
    pc.created_at,
    pc.updated_at,
    -- company info
    c.company_name,
    c.website_url as company_website,
    c.linkedin_url as company_linkedin,
    -- slot assignment
    cs.role_code as assigned_role,
    cs.assigned_at as role_assigned_at
FROM people.contact pc
LEFT JOIN company.company c ON pc.company_id = c.company_id
LEFT JOIN company.company_slot cs ON pc.contact_id = cs.contact_id;

-- Grant view permissions
GRANT SELECT ON company.v_company_summary TO app_user;
GRANT SELECT ON people.v_contact_details TO app_user;

-- ===================================================
-- SCHEMA COMPLETE
-- ===================================================

-- Final summary
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Neon Database Schema Setup Complete!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Schemas: company, people, intake, vault';
    RAISE NOTICE 'Security: RLS enabled with MCP roles';
    RAISE NOTICE 'Functions: intake.f_ingest_json(), vault.f_promote_contacts()';
    RAISE NOTICE 'Ready for MCP integration!';
END $$;
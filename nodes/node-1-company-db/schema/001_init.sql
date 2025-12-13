-- Node 1 Company DB Schema - 30k Altitude
-- DDL for marketing.company, marketing.company_slot
-- UID generators and insert function

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS marketing;

-- Create sequence for company UIDs
CREATE SEQUENCE IF NOT EXISTS marketing.company_uid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO CYCLE;

-- Company table
CREATE TABLE IF NOT EXISTS marketing.company (
    company_uid text PRIMARY KEY,
    company_name text NOT NULL,
    website text,
    apollo_company_id text,
    ein_raw text,
    created_at timestamp DEFAULT NOW(),
    updated_at timestamp DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT uk_company_website UNIQUE(website),
    CONSTRAINT uk_company_apollo_id UNIQUE(apollo_company_id)
);

-- Company slot table (CEO/CFO/HR positions)
CREATE TABLE IF NOT EXISTS marketing.company_slot (
    slot_uid text PRIMARY KEY,
    company_uid text NOT NULL,
    role text NOT NULL,
    status text DEFAULT 'open',
    person_id text, -- NULL at 30k altitude (no people yet)
    created_at timestamp DEFAULT NOW(),
    updated_at timestamp DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT fk_company_slot_company 
        FOREIGN KEY (company_uid) 
        REFERENCES marketing.company(company_uid) 
        ON DELETE CASCADE,
    CONSTRAINT uk_company_role 
        UNIQUE(company_uid, role),
    CONSTRAINT chk_role 
        CHECK (role IN ('CEO', 'CFO', 'HR')),
    CONSTRAINT chk_status 
        CHECK (status IN ('open', 'filled', 'pending'))
);

-- Dead letter queue for failed imports
CREATE TABLE IF NOT EXISTS marketing.dead_letter_queue (
    id SERIAL PRIMARY KEY,
    source_file text,
    row_number integer,
    raw_data text,
    error_message text,
    created_at timestamp DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_company_website 
    ON marketing.company(LOWER(website));
CREATE INDEX IF NOT EXISTS idx_company_apollo_id 
    ON marketing.company(apollo_company_id);
CREATE INDEX IF NOT EXISTS idx_company_created 
    ON marketing.company(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_slot_company 
    ON marketing.company_slot(company_uid);
CREATE INDEX IF NOT EXISTS idx_slot_status 
    ON marketing.company_slot(status);

-- Function to generate company UID
CREATE OR REPLACE FUNCTION marketing.gen_company_uid()
RETURNS text AS $$
DECLARE
    date_part text;
    seq_num bigint;
    result text;
BEGIN
    date_part := TO_CHAR(CURRENT_DATE, 'YYYYMMDD');
    seq_num := nextval('marketing.company_uid_seq');
    result := 'CO-' || date_part || '-' || LPAD(seq_num::text, 6, '0');
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to generate slot UID
CREATE OR REPLACE FUNCTION marketing.gen_slot_uid(
    company_uid text, 
    role text
)
RETURNS text AS $$
BEGIN
    RETURN 'SL-' || company_uid || '-' || UPPER(role);
END;
$$ LANGUAGE plpgsql;

-- Main function to insert company with slots (idempotent)
CREATE OR REPLACE FUNCTION marketing.insert_company_with_slots(
    p_company_name text,
    p_website text,
    p_apollo_company_id text DEFAULT NULL,
    p_ein_raw text DEFAULT NULL
)
RETURNS json AS $$
DECLARE
    v_company_uid text;
    v_existing_uid text;
    v_role text;
    v_roles text[] := ARRAY['CEO', 'CFO', 'HR'];
    v_slot_count integer := 0;
BEGIN
    -- Normalize website
    p_website := LOWER(TRIM(p_website));
    
    -- Check for existing company by website
    IF p_website IS NOT NULL THEN
        SELECT company_uid INTO v_existing_uid
        FROM marketing.company
        WHERE LOWER(website) = p_website
        LIMIT 1;
        
        IF v_existing_uid IS NOT NULL THEN
            -- Company exists, ensure slots exist
            FOREACH v_role IN ARRAY v_roles LOOP
                INSERT INTO marketing.company_slot (
                    slot_uid, 
                    company_uid, 
                    role, 
                    status
                ) VALUES (
                    marketing.gen_slot_uid(v_existing_uid, v_role),
                    v_existing_uid,
                    v_role,
                    'open'
                ) ON CONFLICT (company_uid, role) DO NOTHING;
                
                GET DIAGNOSTICS v_slot_count = ROW_COUNT;
                v_slot_count := v_slot_count + v_slot_count;
            END LOOP;
            
            RETURN json_build_object(
                'status', 'exists',
                'company_uid', v_existing_uid,
                'message', 'Company already exists',
                'slots_ensured', v_slot_count
            );
        END IF;
    END IF;
    
    -- Check for existing by Apollo ID
    IF p_apollo_company_id IS NOT NULL THEN
        SELECT company_uid INTO v_existing_uid
        FROM marketing.company
        WHERE apollo_company_id = p_apollo_company_id
        LIMIT 1;
        
        IF v_existing_uid IS NOT NULL THEN
            RETURN json_build_object(
                'status', 'exists',
                'company_uid', v_existing_uid,
                'message', 'Company exists with same Apollo ID'
            );
        END IF;
    END IF;
    
    -- Generate new company UID
    v_company_uid := marketing.gen_company_uid();
    
    -- Insert new company
    INSERT INTO marketing.company (
        company_uid,
        company_name,
        website,
        apollo_company_id,
        ein_raw,
        created_at,
        updated_at
    ) VALUES (
        v_company_uid,
        p_company_name,
        p_website,
        p_apollo_company_id,
        p_ein_raw,
        NOW(),
        NOW()
    );
    
    -- Create slots for each role
    FOREACH v_role IN ARRAY v_roles LOOP
        INSERT INTO marketing.company_slot (
            slot_uid,
            company_uid,
            role,
            status,
            created_at,
            updated_at
        ) VALUES (
            marketing.gen_slot_uid(v_company_uid, v_role),
            v_company_uid,
            v_role,
            'open',
            NOW(),
            NOW()
        );
    END LOOP;
    
    RETURN json_build_object(
        'status', 'created',
        'company_uid', v_company_uid,
        'company_name', p_company_name,
        'slots_created', 3
    );
    
EXCEPTION
    WHEN unique_violation THEN
        RETURN json_build_object(
            'status', 'error',
            'message', 'Unique constraint violation',
            'detail', SQLERRM
        );
    WHEN OTHERS THEN
        -- Log to dead letter queue would go here
        RETURN json_build_object(
            'status', 'error',
            'message', 'Unexpected error',
            'detail', SQLERRM
        );
END;
$$ LANGUAGE plpgsql;

-- Helper function to log dead letters
CREATE OR REPLACE FUNCTION marketing.log_dead_letter(
    p_source_file text,
    p_row_number integer,
    p_raw_data text,
    p_error_message text
)
RETURNS void AS $$
BEGIN
    INSERT INTO marketing.dead_letter_queue (
        source_file,
        row_number,
        raw_data,
        error_message,
        created_at
    ) VALUES (
        p_source_file,
        p_row_number,
        p_raw_data,
        p_error_message,
        NOW()
    );
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed)
-- GRANT USAGE ON SCHEMA marketing TO your_app_user;
-- GRANT ALL ON ALL TABLES IN SCHEMA marketing TO your_app_user;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA marketing TO your_app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA marketing TO your_app_user;
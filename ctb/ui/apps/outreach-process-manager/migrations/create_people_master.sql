
-- Updated At Trigger Function
CREATE OR REPLACE FUNCTION trigger_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Barton ID Generator Function
-- Generates format: NN.NN.NN.NN.NNNNN.NNN
CREATE OR REPLACE FUNCTION generate_barton_id()
RETURNS VARCHAR(23) AS $$
DECLARE
    segment1 VARCHAR(2);
    segment2 VARCHAR(2);
    segment3 VARCHAR(2);
    segment4 VARCHAR(2);
    segment5 VARCHAR(5);
    segment6 VARCHAR(3);
BEGIN
    -- Use timestamp and random for uniqueness
    segment1 := LPAD((EXTRACT(EPOCH FROM NOW())::BIGINT % 100)::TEXT, 2, '0');
    segment2 := LPAD((EXTRACT(MICROSECONDS FROM NOW()) % 100)::TEXT, 2, '0');
    segment3 := LPAD((RANDOM() * 100)::INT::TEXT, 2, '0');
    segment4 := '07'; -- Fixed segment for database records
    segment5 := LPAD((RANDOM() * 100000)::INT::TEXT, 5, '0');
    segment6 := LPAD((RANDOM() * 1000)::INT::TEXT, 3, '0');

    RETURN segment1 || '.' || segment2 || '.' || segment3 || '.' || segment4 || '.' || segment5 || '.' || segment6;
END;
$$ LANGUAGE plpgsql;

-- Barton Doctrine Migration
-- File: create_people_master
-- Purpose: Database schema migration with Barton ID compliance
-- Requirements: All tables must have unique_id (Barton ID) and audit columns
-- MCP: All access via Composio bridge, no direct connections

/**
 * Step 4 Promotion Console - People Master Table
 *
 * This table stores promoted people records that have successfully
 * passed Step 2A validation, Step 2B enrichment (if needed), and
 * Step 3 adjustment (if needed).
 *
 * Barton Doctrine Rules:
 * - Only validated records can be promoted from people_raw_intake
 * - Barton IDs remain intact during promotion
 * - Every promotion must be logged in people_audit_log
 * - Master tables are the final destination for clean, validated data
 */

CREATE TABLE IF NOT EXISTS marketing.people_master (unique_id TEXT PRIMARY KEY,
    company_unique_id TEXT NOT NULL,
    company_slot_unique_id TEXT NOT NULL,

    -- Core person data
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    full_name TEXT GENERATED ALWAYS AS (
        TRIM(first_name || ' ' || last_name)
    ) STORED,

    -- Professional data
    title TEXT,
    seniority TEXT,
    department TEXT,

    -- Contact information
    email TEXT,
    work_phone_e164 TEXT,
    personal_phone_e164 TEXT,

    -- Social profiles
    linkedin_url TEXT,
    twitter_url TEXT,
    facebook_url TEXT,

    -- Additional professional data
    bio TEXT,
    skills TEXT[],
    education TEXT,
    certifications TEXT[],

    -- Source tracking
    source_system TEXT NOT NULL,
    source_record_id TEXT,

    -- Promotion metadata
    promoted_from_intake_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    promotion_audit_log_id INTEGER,

    -- Standard timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT people_master_barton_id_format
        CHECK (unique_id ~ '^04\.04\.02\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'),
    CONSTRAINT people_master_company_barton_id_format
        CHECK (company_unique_id ~ '^04\.04\.01\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'),
    CONSTRAINT people_master_slot_barton_id_format
        CHECK (company_slot_unique_id ~ '^04\.04\.05\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'),
    CONSTRAINT people_master_email_format
        CHECK (email IS NULL OR email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_people_master_company_id ON marketing.people_master(company_unique_id);
CREATE INDEX IF NOT EXISTS idx_people_master_slot_id ON marketing.people_master(company_slot_unique_id);
CREATE INDEX IF NOT EXISTS idx_people_master_full_name ON marketing.people_master(full_name);
CREATE INDEX IF NOT EXISTS idx_people_master_email ON marketing.people_master(email);
CREATE INDEX IF NOT EXISTS idx_people_master_title ON marketing.people_master(title);
CREATE INDEX IF NOT EXISTS idx_people_master_source_system ON marketing.people_master(source_system);
CREATE INDEX IF NOT EXISTS idx_people_master_promoted_at ON marketing.people_master(promoted_from_intake_at);

-- Foreign key relationships (if company_master exists)
-- ALTER TABLE marketing.people_master
-- ADD CONSTRAINT fk_people_master_company
-- FOREIGN KEY (company_unique_id) REFERENCES marketing.company_master(company_unique_id);

-- Comments for documentation
COMMENT ON TABLE marketing.people_master IS 'Master table for validated and promoted people records from the Barton Doctrine pipeline';
COMMENT ON COLUMN marketing.people_master.unique_id IS 'Barton ID format: 04.04.02.XX.XXXXX.XXX (immutable during promotion)';
COMMENT ON COLUMN marketing.people_master.company_unique_id IS 'Reference to parent company Barton ID';
COMMENT ON COLUMN marketing.people_master.company_slot_unique_id IS 'Reference to company slot Barton ID';
COMMENT ON COLUMN marketing.people_master.promoted_from_intake_at IS 'Timestamp when record was promoted from people_raw_intake';
COMMENT ON COLUMN marketing.people_master.promotion_audit_log_id IS 'Reference to the audit log entry for this promotion';

-- Trigger for auto-updating updated_at timestamp
DROP TRIGGER IF EXISTS trigger_people_master_updated_at ON marketing.people_master;
CREATE TRIGGER trigger_people_master_updated_at
    BEFORE UPDATE ON marketing.people_master
    FOR EACH ROW
    EXECUTE FUNCTION trigger_updated_at();

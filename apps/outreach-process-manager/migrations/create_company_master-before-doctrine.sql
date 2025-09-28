/**
 * Step 4 Promotion Console - Company Master Table
 *
 * This table stores promoted company records that have successfully
 * passed Step 2A validation, Step 2B enrichment (if needed), and
 * Step 3 adjustment (if needed).
 *
 * Barton Doctrine Rules:
 * - Only validated records can be promoted from company_raw_intake
 * - Barton IDs remain intact during promotion
 * - Every promotion must be logged in company_audit_log
 * - Master tables are the final destination for clean, validated data
 */

CREATE TABLE IF NOT EXISTS marketing.company_master (
    company_unique_id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    website_url TEXT NOT NULL,
    industry TEXT,
    employee_count INTEGER,
    company_phone TEXT,
    address_street TEXT,
    address_city TEXT,
    address_state TEXT,
    address_zip TEXT,
    address_country TEXT,
    linkedin_url TEXT,
    facebook_url TEXT,
    twitter_url TEXT,
    sic_codes TEXT,
    founded_year INTEGER,
    keywords TEXT[],
    description TEXT,

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
    CONSTRAINT company_master_barton_id_format
        CHECK (company_unique_id ~ '^04\.04\.01\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'),
    CONSTRAINT company_master_employee_count_positive
        CHECK (employee_count IS NULL OR employee_count >= 0),
    CONSTRAINT company_master_founded_year_reasonable
        CHECK (founded_year IS NULL OR (founded_year >= 1800 AND founded_year <= EXTRACT(YEAR FROM NOW())))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_company_master_company_name ON marketing.company_master(company_name);
CREATE INDEX IF NOT EXISTS idx_company_master_industry ON marketing.company_master(industry);
CREATE INDEX IF NOT EXISTS idx_company_master_source_system ON marketing.company_master(source_system);
CREATE INDEX IF NOT EXISTS idx_company_master_promoted_at ON marketing.company_master(promoted_from_intake_at);

-- Comments for documentation
COMMENT ON TABLE marketing.company_master IS 'Master table for validated and promoted company records from the Barton Doctrine pipeline';
COMMENT ON COLUMN marketing.company_master.company_unique_id IS 'Barton ID format: 04.04.01.XX.XXXXX.XXX (immutable during promotion)';
COMMENT ON COLUMN marketing.company_master.promoted_from_intake_at IS 'Timestamp when record was promoted from company_raw_intake';
COMMENT ON COLUMN marketing.company_master.promotion_audit_log_id IS 'Reference to the audit log entry for this promotion';
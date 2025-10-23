-- ─────────────────────────────────────────────
-- 📁 CTB Classification Metadata
-- ─────────────────────────────────────────────
-- CTB Branch: data/migrations
-- Barton ID: 05.01.02
-- Unique ID: CTB-42E4AED3
-- Blueprint Hash:
-- Last Updated: 2025-10-23
-- Enforcement: HEIR
-- ─────────────────────────────────────────────

/**
 * Company Tables Migration - Barton Doctrine Ingestion Build
 * Creates marketing.company_raw_intake and marketing.company_audit_log
 * Enforces 6-part Barton ID specification and audit logging requirements
 *
 * Barton Doctrine Rules:
 * - All inserts must carry Barton 6-part unique_id + audit log entry
 * - Intake tables must remain minimal, normalized, and NULL-safe
 * - Audit logs mirror people/company pattern exactly
 *
 * Barton ID Format: [database].[subhive].[microprocess].[tool].[altitude].[step]
 * Example: 04.04.01.08.10000.001 (marketing.marketing.company_intake.DBeaver.execution.001)
 */

-- ==============================================================================
-- MARKETING.COMPANY_RAW_INTAKE - Doctrine Minimums Table
-- ==============================================================================

/**
 * Company Raw Intake Table - Minimal, Normalized, NULL-safe
 * Stores validated company records with Barton unique_id
 * All optional fields are explicitly nullable for doctrine compliance
 */
CREATE TABLE IF NOT EXISTS marketing.company_raw_intake (
    id SERIAL PRIMARY KEY,

    -- BARTON DOCTRINE: 6-part unique identifier (REQUIRED)
    company_unique_id TEXT NOT NULL UNIQUE,

    -- CORE REQUIRED FIELDS (Doctrine minimums)
    company_name TEXT NOT NULL CHECK (company_name != ''),
    website_url TEXT NOT NULL CHECK (website_url != ''),
    industry TEXT NOT NULL CHECK (industry != ''),
    employee_count INTEGER NOT NULL CHECK (employee_count > 0 AND employee_count <= 10000000),
    company_phone TEXT NOT NULL CHECK (company_phone ~ '^\+[1-9][0-9]{1,15}$'), -- E.164 format enforced

    -- ADDRESS FIELDS (All required)
    address_street TEXT NOT NULL CHECK (address_street != ''),
    address_city TEXT NOT NULL CHECK (address_city != ''),
    address_state TEXT NOT NULL CHECK (address_state != ''),
    address_zip TEXT NOT NULL CHECK (address_zip != ''),
    address_country TEXT NOT NULL CHECK (address_country != ''),

    -- OPTIONAL FIELDS (NULL-safe for doctrine compliance)
    facebook_url TEXT,
    x_url TEXT, -- formerly twitter_url
    linkedin_url TEXT,
    keywords TEXT, -- comma-separated tags
    seo_description TEXT,

    -- SOURCE TRACKING (for audit trail)
    source_system TEXT, -- Apollo, Apify, DBeaver, Manual, etc.
    source_record_id TEXT, -- external system's ID reference

    -- BARTON DOCTRINE: Timestamp requirements
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- VALIDATION STATUS (for pipeline tracking)
    validation_status TEXT DEFAULT 'pending' CHECK (validation_status IN ('pending', 'validated', 'failed', 'enriched')),
    validation_errors JSONB DEFAULT NULL, -- structured error details

    -- BARTON DOCTRINE: Altitude and process tracking
    altitude INTEGER DEFAULT 10000, -- execution level
    process_step TEXT DEFAULT 'company_intake'
);

-- ==============================================================================
-- MARKETING.COMPANY_AUDIT_LOG - Doctrine Audit Requirements
-- ==============================================================================

/**
 * Company Audit Log - Mirrors people/company pattern exactly
 * Every company operation must log here for doctrine compliance
 * Provides full traceability for all company data operations
 */
CREATE TABLE IF NOT EXISTS marketing.company_audit_log (
    id SERIAL PRIMARY KEY,

    -- BARTON DOCTRINE: Link to company record
    company_unique_id TEXT NOT NULL, -- references company_raw_intake.company_unique_id

    -- AUDIT DETAILS
    action TEXT NOT NULL CHECK (action IN ('insert', 'update', 'validate', 'enrich', 'delete')),
    status TEXT NOT NULL CHECK (status IN ('success', 'failed', 'warning')),
    source TEXT NOT NULL, -- validator name, API endpoint, manual user, etc.

    -- ERROR TRACKING (NULL-safe)
    error_log JSONB DEFAULT NULL, -- structured error details when status = 'failed'

    -- CHANGE TRACKING
    previous_values JSONB DEFAULT NULL, -- before state for updates
    new_values JSONB DEFAULT NULL, -- after state for updates

    -- BARTON DOCTRINE: Full metadata
    altitude INTEGER DEFAULT 10000,
    process_id TEXT, -- specific process identifier
    session_id TEXT, -- batch/session grouping

    -- TIMING
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==============================================================================
-- INDEXES FOR PERFORMANCE - Doctrine Requirements
-- ==============================================================================

-- Primary lookup indexes
CREATE INDEX IF NOT EXISTS idx_company_raw_intake_unique_id
    ON marketing.company_raw_intake(company_unique_id);

CREATE INDEX IF NOT EXISTS idx_company_raw_intake_name
    ON marketing.company_raw_intake(company_name);

CREATE INDEX IF NOT EXISTS idx_company_raw_intake_website
    ON marketing.company_raw_intake(website_url);

CREATE INDEX IF NOT EXISTS idx_company_raw_intake_validation_status
    ON marketing.company_raw_intake(validation_status);

CREATE INDEX IF NOT EXISTS idx_company_raw_intake_source
    ON marketing.company_raw_intake(source_system, source_record_id);

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_company_audit_log_unique_id
    ON marketing.company_audit_log(company_unique_id);

CREATE INDEX IF NOT EXISTS idx_company_audit_log_created_at
    ON marketing.company_audit_log(created_at);

CREATE INDEX IF NOT EXISTS idx_company_audit_log_action_status
    ON marketing.company_audit_log(action, status);

-- ==============================================================================
-- TRIGGERS - Automatic Timestamp Management
-- ==============================================================================

/**
 * Automatic updated_at timestamp trigger
 * Ensures doctrine compliance for change tracking
 */
CREATE OR REPLACE FUNCTION update_company_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_company_raw_intake_updated_at
    BEFORE UPDATE ON marketing.company_raw_intake
    FOR EACH ROW EXECUTE FUNCTION update_company_updated_at_column();

-- ==============================================================================
-- BARTON ID GENERATION FUNCTIONS
-- ==============================================================================

/**
 * Generate Barton 6-part unique ID for companies
 * Format: [database].[subhive].[microprocess].[tool].[altitude].[step]
 *
 * Parameters:
 *   tool_code: 04=Neon, 07=Apify, 08=DBeaver
 *
 * Returns: Complete Barton ID (e.g., "04.04.01.08.10000.001")
 */
CREATE OR REPLACE FUNCTION generate_company_barton_id(tool_code TEXT DEFAULT '04')
RETURNS TEXT AS $$
DECLARE
    database_code TEXT := '04'; -- marketing database
    subhive_code TEXT := '04';  -- marketing subhive
    microprocess_code TEXT := '01'; -- company intake pipeline
    altitude_code TEXT := '10000'; -- execution level
    step_number INTEGER;
    step_padded TEXT;
    barton_id TEXT;
BEGIN
    -- Validate tool_code
    IF tool_code NOT IN ('04', '07', '08') THEN
        RAISE EXCEPTION 'Invalid tool_code: %. Must be 04 (Neon), 07 (Apify), or 08 (DBeaver)', tool_code;
    END IF;

    -- Get next step number for this tool
    SELECT COALESCE(MAX(
        CAST(SPLIT_PART(company_unique_id, '.', 6) AS INTEGER)
    ), 0) + 1
    INTO step_number
    FROM marketing.company_raw_intake
    WHERE company_unique_id LIKE database_code || '.' || subhive_code || '.' || microprocess_code || '.' || tool_code || '.' || altitude_code || '.%';

    -- Pad step number to 3 digits
    step_padded := LPAD(step_number::TEXT, 3, '0');

    -- Construct full Barton ID
    barton_id := database_code || '.' || subhive_code || '.' || microprocess_code || '.' || tool_code || '.' || altitude_code || '.' || step_padded;

    RETURN barton_id;
END;
$$ LANGUAGE plpgsql;

/**
 * Validate Barton ID format
 * Ensures all IDs conform to 6-part specification
 */
CREATE OR REPLACE FUNCTION validate_barton_id(barton_id TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    -- Check format: XX.XX.XX.XX.XXXXX.XXX
    IF barton_id !~ '^[0-9]{2}\.[0-9]{2}\.[0-9]{2}\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$' THEN
        RETURN FALSE;
    END IF;

    -- Additional validation: must start with 04.04.01 for company intake
    IF NOT barton_id LIKE '04.04.01.%' THEN
        RETURN FALSE;
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- SAMPLE DATA VALIDATION CONSTRAINTS
-- ==============================================================================

/**
 * Add check constraint to ensure Barton ID format compliance
 */
ALTER TABLE marketing.company_raw_intake
    ADD CONSTRAINT chk_company_barton_id_format
    CHECK (validate_barton_id(company_unique_id));

-- ==============================================================================
-- INITIAL AUDIT LOG ENTRY - Schema Creation
-- ==============================================================================

/**
 * Log schema creation for doctrine compliance
 * Every major operation must be audited
 */
INSERT INTO marketing.company_audit_log (
    company_unique_id,
    action,
    status,
    source,
    error_log,
    altitude,
    process_id,
    session_id
) VALUES (
    '04.04.01.04.10000.000', -- system/schema creation ID
    'insert',
    'success',
    'schema_migration',
    '{"message": "Company tables created successfully", "schema_version": "1.0.0"}'::jsonb,
    10000,
    'create_company_tables_migration',
    'schema_init_' || EXTRACT(epoch FROM NOW())::TEXT
);

-- ==============================================================================
-- GRANT PERMISSIONS - Doctrine Access Control
-- ==============================================================================

-- Grant appropriate permissions for application access
-- GRANT SELECT, INSERT, UPDATE ON marketing.company_raw_intake TO app_user;
-- GRANT SELECT, INSERT ON marketing.company_audit_log TO app_user;
-- GRANT USAGE ON SEQUENCE marketing.company_raw_intake_id_seq TO app_user;
-- GRANT USAGE ON SEQUENCE marketing.company_audit_log_id_seq TO app_user;

-- ==============================================================================
-- MIGRATION COMPLETE
-- ==============================================================================

/**
 * Company Tables Migration Complete
 *
 * Created:
 * - marketing.company_raw_intake (with Barton ID enforcement)
 * - marketing.company_audit_log (with full audit trail)
 * - Barton ID generation functions
 * - Performance indexes
 * - Validation constraints
 * - Automatic triggers
 *
 * Next Steps:
 * 1. Create company slot tables (create_company_slot.sql)
 * 2. Build validator agents (/api/validate-company.ts)
 * 3. Update validation console UI
 */
-- ─────────────────────────────────────────────
-- 📁 CTB Classification Metadata
-- ─────────────────────────────────────────────
-- CTB Branch: data/migrations
-- Barton ID: 05.01.02
-- Unique ID: CTB-69E223A7
-- Blueprint Hash:
-- Last Updated: 2025-10-23
-- Enforcement: HEIR
-- ─────────────────────────────────────────────


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
-- File: create_people_tables
-- Purpose: Database schema migration with Barton ID compliance
-- Requirements: All tables must have unique_id (Barton ID) and audit columns
-- MCP: All access via Composio bridge, no direct connections

/**
 * People Tables Migration - Barton Doctrine Ingestion Build
 * Creates marketing.people_raw_intake and marketing.people_audit_log
 * Enforces Company → Slot → Person linkage with Barton IDs
 *
 * Barton Doctrine Rules:
 * - All inserts must carry Barton 6-part unique_id + audit log entry
 * - People must link to company_unique_id and company_slot_unique_id
 * - Audit logs mirror people/company pattern exactly
 *
 * People Barton ID Format: 04.04.02.XX.10000.XXX (microprocess 02 = people intake)
 */

-- ==============================================================================
-- MARKETING.PEOPLE_RAW_INTAKE - People Intake Table
-- ==============================================================================

/**
 * People Raw Intake Table - Links to companies and slots
 * Each person must be assigned to a specific company slot (CEO, CFO, HR, etc.)
 */
CREATE TABLE IF NOT EXISTS marketing.people_raw_intake (id SERIAL PRIMARY KEY,

    -- BARTON DOCTRINE: 6-part unique identifier (REQUIRED)
    unique_id TEXT NOT NULL UNIQUE,

    -- COMPANY LINKAGE: References company and slot
    company_unique_id TEXT NOT NULL, -- FK to company_raw_intake.company_unique_id
    company_slot_unique_id TEXT NOT NULL, -- FK to company_slot.company_slot_unique_id

    -- CORE PERSON FIELDS
    first_name TEXT NOT NULL CHECK (first_name != ''),
    last_name TEXT NOT NULL CHECK (last_name != ''),
    full_name TEXT GENERATED ALWAYS AS (first_name || ' ' || last_name) STORED,

    -- JOB DETAILS
    title TEXT, -- job title (e.g., "Chief Executive Officer")
    seniority TEXT CHECK (seniority IN ('C-Level', 'VP-Level', 'Director-Level', 'Manager-Level', 'Individual Contributor', 'Entry-Level')),
    department TEXT, -- Executive, Sales, Marketing, Engineering, etc.

    -- CONTACT INFORMATION
    email TEXT, -- work email
    work_phone_e164 TEXT CHECK (work_phone_e164 IS NULL OR work_phone_e164 ~ '^\+[1-9][0-9]{1,15}$'), -- E.164 format
    personal_phone_e164 TEXT CHECK (personal_phone_e164 IS NULL OR personal_phone_e164 ~ '^\+[1-9][0-9]{1,15}$'),

    -- SOCIAL PROFILES (Optional)
    linkedin_url TEXT,
    twitter_url TEXT,
    facebook_url TEXT,

    -- ADDITIONAL DATA (Optional)
    bio TEXT, -- professional biography
    skills TEXT, -- comma-separated skills
    education TEXT, -- education background
    certifications TEXT, -- professional certifications

    -- SOURCE TRACKING (for audit trail)
    source_system TEXT, -- Apify, Apollo, Manual, etc.
    source_record_id TEXT, -- external system's ID reference

    -- BARTON DOCTRINE: Timestamp requirements
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- VALIDATION STATUS (for pipeline tracking)
    validation_status TEXT DEFAULT 'pending' CHECK (validation_status IN ('pending', 'validated', 'failed', 'enriched')),
    validation_errors JSONB DEFAULT NULL, -- structured error details

    -- BARTON DOCTRINE: Altitude and process tracking
    altitude INTEGER DEFAULT 10000, -- execution level
    process_step TEXT DEFAULT 'people_intake',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW());

-- ==============================================================================
-- MARKETING.PEOPLE_AUDIT_LOG - People Audit Trail
-- ==============================================================================

/**
 * People Audit Log - Mirrors company audit pattern exactly
 * Every people operation must log here for doctrine compliance
 */
CREATE TABLE IF NOT EXISTS marketing.people_audit_log (id SERIAL PRIMARY KEY,

    -- BARTON DOCTRINE: Link to person record
    unique_id TEXT NOT NULL, -- references people_raw_intake.unique_id

    -- COMPANY CONTEXT
    company_unique_id TEXT NOT NULL, -- for cross-reference
    company_slot_unique_id TEXT, -- slot assignment tracking

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
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW());

-- ==============================================================================
-- INDEXES FOR PERFORMANCE - People Lookups
-- ==============================================================================

-- Primary lookup indexes
CREATE INDEX IF NOT EXISTS idx_people_raw_intake_unique_id
    ON marketing.people_raw_intake(unique_id);

CREATE INDEX IF NOT EXISTS idx_people_raw_intake_company_id
    ON marketing.people_raw_intake(company_unique_id);

CREATE INDEX IF NOT EXISTS idx_people_raw_intake_slot_id
    ON marketing.people_raw_intake(company_slot_unique_id);

CREATE INDEX IF NOT EXISTS idx_people_raw_intake_name
    ON marketing.people_raw_intake(first_name, last_name);

CREATE INDEX IF NOT EXISTS idx_people_raw_intake_email
    ON marketing.people_raw_intake(email);

CREATE INDEX IF NOT EXISTS idx_people_raw_intake_validation_status
    ON marketing.people_raw_intake(validation_status);

CREATE INDEX IF NOT EXISTS idx_people_raw_intake_source
    ON marketing.people_raw_intake(source_system, source_record_id);

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_people_audit_log_unique_id
    ON marketing.people_audit_log(unique_id);

CREATE INDEX IF NOT EXISTS idx_people_audit_log_company_id
    ON marketing.people_audit_log(company_unique_id);

CREATE INDEX IF NOT EXISTS idx_people_audit_log_created_at
    ON marketing.people_audit_log(created_at);

CREATE INDEX IF NOT EXISTS idx_people_audit_log_action_status
    ON marketing.people_audit_log(action, status);

-- ==============================================================================
-- FOREIGN KEY CONSTRAINTS - Company/Slot Linkage
-- ==============================================================================

/**
 * Enforce referential integrity between people, companies, and slots
 * NOTE: Requires company_tables.sql and create_company_slot.sql to run first
 */
ALTER TABLE marketing.people_raw_intake
    ADD CONSTRAINT fk_people_company
    FOREIGN KEY (company_unique_id)
    REFERENCES marketing.company_raw_intake(company_unique_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE;

ALTER TABLE marketing.people_raw_intake
    ADD CONSTRAINT fk_people_company_slot
    FOREIGN KEY (company_slot_unique_id)
    REFERENCES marketing.company_slot(company_slot_unique_id)
    ON DELETE RESTRICT  -- Don't allow slot deletion if people assigned
    ON UPDATE CASCADE;

-- ==============================================================================
-- TRIGGERS - Automatic Timestamp Management
-- ==============================================================================

/**
 * Automatic updated_at timestamp trigger for people
 * Ensures doctrine compliance for change tracking
 */
CREATE OR REPLACE FUNCTION update_people_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_people_raw_intake_updated_at
    BEFORE UPDATE ON marketing.people_raw_intake
    FOR EACH ROW EXECUTE FUNCTION update_people_updated_at_column();

-- ==============================================================================
-- BARTON ID GENERATION FOR PEOPLE
-- ==============================================================================

/**
 * Generate Barton 6-part unique ID for people
 * Format: [database].[subhive].[microprocess].[tool].[altitude].[step]
 * Microprocess 02 = people intake pipeline
 *
 * Parameters:
 *   tool_code: 04=Neon, 07=Apify, 08=DBeaver
 *
 * Returns: Complete Barton ID (e.g., "04.04.02.07.10000.001")
 */
CREATE OR REPLACE FUNCTION generate_people_barton_id(tool_code TEXT DEFAULT '04')
RETURNS TEXT AS $$
DECLARE
    database_code TEXT := '04'; -- marketing database
    subhive_code TEXT := '04';  -- marketing subhive
    microprocess_code TEXT := '02'; -- people intake pipeline
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
        CAST(SPLIT_PART(unique_id, '.', 6) AS INTEGER)
    ), 0) + 1
    INTO step_number
    FROM marketing.people_raw_intake
    WHERE unique_id LIKE database_code || '.' || subhive_code || '.' || microprocess_code || '.' || tool_code || '.' || altitude_code || '.%';

    -- Pad step number to 3 digits
    step_padded := LPAD(step_number::TEXT, 3, '0');

    -- Construct full Barton ID
    barton_id := database_code || '.' || subhive_code || '.' || microprocess_code || '.' || tool_code || '.' || altitude_code || '.' || step_padded;

    RETURN barton_id;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- SLOT ASSIGNMENT HELPER FUNCTIONS
-- ==============================================================================

/**
 * Assign person to company slot by slot type
 * Resolves company + slot_type → company_slot_unique_id
 */
CREATE OR REPLACE FUNCTION assign_person_to_slot(
    p_company_unique_id TEXT,
    p_slot_type TEXT
)
RETURNS TEXT AS $$
DECLARE
    slot_id TEXT;
BEGIN
    -- Get the slot ID for this company and slot type
    SELECT company_slot_unique_id
    INTO slot_id
    FROM marketing.company_slot
    WHERE company_unique_id = p_company_unique_id
      AND slot_type = p_slot_type
      AND slot_status = 'active';

    IF slot_id IS NULL THEN
        RAISE EXCEPTION 'No active slot found for company % with slot type %', p_company_unique_id, p_slot_type;
    END IF;

    RETURN slot_id;
END;
$$ LANGUAGE plpgsql;

/**
 * Mark slot as filled when person is assigned
 * Updates company_slot.is_filled = TRUE
 */
CREATE OR REPLACE FUNCTION mark_slot_filled(p_slot_unique_id TEXT)
RETURNS VOID AS $$
BEGIN
    UPDATE marketing.company_slot
    SET is_filled = TRUE,
        updated_at = NOW()
    WHERE company_slot_unique_id = p_slot_unique_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Slot % not found', p_slot_unique_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- VALIDATION CONSTRAINTS
-- ==============================================================================

/**
 * Ensure valid Barton ID format for people
 */
CREATE OR REPLACE FUNCTION validate_people_barton_id(barton_id TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    -- Check format: XX.XX.XX.XX.XXXXX.XXX
    IF barton_id !~ '^[0-9]{2}\.[0-9]{2}\.[0-9]{2}\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$' THEN
        RETURN FALSE;
    END IF;

    -- Additional validation: must start with 04.04.02 for people intake
    IF NOT barton_id LIKE '04.04.02.%' THEN
        RETURN FALSE;
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Add check constraint for Barton ID format
ALTER TABLE marketing.people_raw_intake
    ADD CONSTRAINT chk_people_barton_id_format
    CHECK (validate_people_barton_id(unique_id));

-- ==============================================================================
-- VIEWS FOR EASIER QUERYING
-- ==============================================================================

/**
 * Complete people view with company and slot details
 * Joins all related tables for easy reporting
 */
CREATE OR REPLACE VIEW marketing.people_complete AS
SELECT
    p.unique_id,
    p.first_name,
    p.last_name,
    p.full_name,
    p.title,
    p.seniority,
    p.department,
    p.email,
    p.work_phone_e164,
    p.linkedin_url,

    -- Company details
    c.company_name,
    c.company_unique_id,
    c.website_url as company_website,
    c.industry as company_industry,

    -- Slot details
    s.company_slot_unique_id,
    s.slot_type,
    s.slot_title,

    -- Status
    p.validation_status,
    p.created_at,
    p.updated_at

FROM marketing.people_raw_intake p
JOIN marketing.company_raw_intake c ON p.company_unique_id = c.company_unique_id
JOIN marketing.company_slot s ON p.company_slot_unique_id = s.company_slot_unique_id;

-- ==============================================================================
-- INITIAL AUDIT LOG ENTRY - Schema Creation
-- ==============================================================================

/**
 * Log schema creation for doctrine compliance
 */
INSERT INTO marketing.people_audit_log (
    unique_id,
    company_unique_id,
    action,
    status,
    source,
    error_log,
    altitude,
    process_id,
    session_id
) VALUES (
    '04.04.02.04.10000.000', -- system/schema creation ID
    '04.04.01.04.10000.000', -- link to system company ID
    'insert',
    'success',
    'schema_migration',
    '{"message": "People tables created successfully", "schema_version": "1.0.0"}'::jsonb,
    10000,
    'create_people_tables_migration',
    'schema_init_' || EXTRACT(epoch FROM NOW())::TEXT
);

-- ==============================================================================
-- GRANT PERMISSIONS - Doctrine Access Control
-- ==============================================================================

-- Grant appropriate permissions for application access
-- GRANT SELECT, INSERT, UPDATE ON marketing.people_raw_intake TO app_user;
-- GRANT SELECT, INSERT ON marketing.people_audit_log TO app_user;
-- GRANT USAGE ON SEQUENCE marketing.people_raw_intake_id_seq TO app_user;
-- GRANT USAGE ON SEQUENCE marketing.people_audit_log_id_seq TO app_user;
-- GRANT SELECT ON marketing.people_complete TO app_user;

-- ==============================================================================
-- MIGRATION COMPLETE
-- ==============================================================================

/**
 * People Tables Migration Complete
 *
 * Created:
 * - marketing.people_raw_intake (with Company → Slot → Person linkage)
 * - marketing.people_audit_log (with full audit trail)
 * - People Barton ID generation functions
 * - Slot assignment helper functions
 * - Performance indexes
 * - Validation constraints
 * - Automatic triggers
 * - people_complete view for easy reporting
 *
 * Company → Slot → Person Linkage:
 * 1. Companies auto-generate CEO/CFO/HR slots on insert
 * 2. People must be assigned to existing company slots
 * 3. All IDs use Barton 6-part specification
 * 4. Full audit trail maintained for all operations
 *
 * Next Steps:
 * 1. Build validator agent (/api/validate-people.ts)
 * 2. Update validation console UI with company/people toggle
 * 3. Test complete pipeline with sample data
 */
-- Trigger for IF
CREATE TRIGGER trigger_IF_updated_at
    BEFORE UPDATE ON IF
    FOR EACH ROW
    EXECUTE FUNCTION trigger_updated_at();

-- Trigger for IF
CREATE TRIGGER trigger_IF_updated_at
    BEFORE UPDATE ON IF
    FOR EACH ROW
    EXECUTE FUNCTION trigger_updated_at();

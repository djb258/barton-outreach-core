
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
-- File: create_company_slot
-- Purpose: Database schema migration with Barton ID compliance
-- Requirements: All tables must have unique_id (Barton ID) and audit columns
-- MCP: All access via Composio bridge, no direct connections

/**
 * Company Slot Migration - Barton Doctrine Ingestion Build
 * Creates marketing.company_slot with auto-generation of CEO/CFO/HR slots
 * Enforces Company → Slot → Person linkage with Barton IDs
 *
 * Barton Doctrine Rules:
 * - Company → Slot → Person linkage must be enforced with Barton IDs
 * - Auto-generate 3 default slots (CEO/CFO/HR) on company insert via trigger
 * - All slots carry Barton 6-part unique_id specification
 *
 * Slot Barton ID Format: 04.04.03.XX.10000.XXX (microprocess 03 = slot management)
 */

-- ==============================================================================
-- MARKETING.COMPANY_SLOT - Slot Management Table
-- ==============================================================================

/**
 * Company Slot Table - Links companies to organizational positions
 * Each company automatically gets CEO, CFO, HR slots on creation
 * People records attach to specific slots via company_slot_unique_id
 */
CREATE TABLE IF NOT EXISTS marketing.company_slot (id SERIAL PRIMARY KEY,

    -- BARTON DOCTRINE: 6-part unique identifier for slot
    company_slot_unique_id TEXT NOT NULL UNIQUE,

    -- COMPANY LINKAGE: References company_raw_intake.company_unique_id
    company_unique_id TEXT NOT NULL,

    -- SLOT DEFINITION
    slot_type TEXT NOT NULL CHECK (slot_type IN ('CEO', 'CFO', 'HR', 'CTO', 'CMO', 'COO', 'VP_SALES', 'VP_MARKETING', 'DIRECTOR', 'MANAGER')),

    -- SLOT METADATA
    slot_title TEXT, -- custom title if different from slot_type
    slot_description TEXT, -- additional context about the role
    is_filled BOOLEAN DEFAULT FALSE, -- whether someone is assigned to this slot
    priority_order INTEGER DEFAULT 100, -- for UI ordering (CEO=1, CFO=2, HR=3, etc.)

    -- STATUS TRACKING
    slot_status TEXT DEFAULT 'active' CHECK (slot_status IN ('active', 'inactive', 'deprecated')),

    -- BARTON DOCTRINE: Timestamp requirements
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- BARTON DOCTRINE: Altitude and process tracking
    altitude INTEGER DEFAULT 10000, -- execution level
    process_step TEXT DEFAULT 'slot_management',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW());

-- ==============================================================================
-- INDEXES FOR PERFORMANCE - Slot Lookups
-- ==============================================================================

-- Primary lookup indexes
CREATE INDEX IF NOT EXISTS idx_company_slot_unique_id
    ON marketing.company_slot(company_slot_unique_id);

CREATE INDEX IF NOT EXISTS idx_company_slot_company_id
    ON marketing.company_slot(company_unique_id);

CREATE INDEX IF NOT EXISTS idx_company_slot_type
    ON marketing.company_slot(slot_type);

CREATE INDEX IF NOT EXISTS idx_company_slot_company_type
    ON marketing.company_slot(company_unique_id, slot_type);

CREATE INDEX IF NOT EXISTS idx_company_slot_status
    ON marketing.company_slot(slot_status);

-- ==============================================================================
-- FOREIGN KEY CONSTRAINTS - Company Linkage
-- ==============================================================================

/**
 * Enforce referential integrity between companies and slots
 * NOTE: This creates dependency - company_tables.sql must run first
 */
ALTER TABLE marketing.company_slot
    ADD CONSTRAINT fk_company_slot_company
    FOREIGN KEY (company_unique_id)
    REFERENCES marketing.company_raw_intake(company_unique_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE;

-- ==============================================================================
-- TRIGGERS - Automatic Timestamp Management
-- ==============================================================================

/**
 * Automatic updated_at timestamp trigger for slots
 * Ensures doctrine compliance for change tracking
 */
CREATE OR REPLACE FUNCTION update_company_slot_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_company_slot_updated_at
    BEFORE UPDATE ON marketing.company_slot
    FOR EACH ROW EXECUTE FUNCTION update_company_slot_updated_at_column();

-- ==============================================================================
-- BARTON ID GENERATION FOR SLOTS
-- ==============================================================================

/**
 * Generate Barton 6-part unique ID for company slots
 * Format: [database].[subhive].[microprocess].[tool].[altitude].[step]
 * Microprocess 03 = slot management
 *
 * Parameters:
 *   tool_code: 04=Neon, 07=Apify, 08=DBeaver
 *
 * Returns: Complete Barton ID (e.g., "04.04.03.04.10000.001")
 */
CREATE OR REPLACE FUNCTION generate_slot_barton_id(tool_code TEXT DEFAULT '04')
RETURNS TEXT AS $$
DECLARE
    database_code TEXT := '04'; -- marketing database
    subhive_code TEXT := '04';  -- marketing subhive
    microprocess_code TEXT := '03'; -- slot management pipeline
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
        CAST(SPLIT_PART(company_slot_unique_id, '.', 6) AS INTEGER)
    ), 0) + 1
    INTO step_number
    FROM marketing.company_slot
    WHERE company_slot_unique_id LIKE database_code || '.' || subhive_code || '.' || microprocess_code || '.' || tool_code || '.' || altitude_code || '.%';

    -- Pad step number to 3 digits
    step_padded := LPAD(step_number::TEXT, 3, '0');

    -- Construct full Barton ID
    barton_id := database_code || '.' || subhive_code || '.' || microprocess_code || '.' || tool_code || '.' || altitude_code || '.' || step_padded;

    RETURN barton_id;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- AUTO-SLOT GENERATION TRIGGER FUNCTION
-- ==============================================================================

/**
 * Trigger Function: trgfn_ensure_company_slots()
 * Auto-generates 3 default slots (CEO/CFO/HR) when company is inserted
 * Enforces Barton Doctrine requirement for Company → Slot → Person linkage
 */
CREATE OR REPLACE FUNCTION trgfn_ensure_company_slots()
RETURNS TRIGGER AS $$
DECLARE
    slot_types TEXT[] := ARRAY['CEO', 'CFO', 'HR'];
    slot_type TEXT;
    slot_priorities INTEGER[] := ARRAY[1, 2, 3]; -- CEO=1, CFO=2, HR=3
    slot_priority INTEGER;
    slot_barton_id TEXT;
    i INTEGER;
BEGIN
    -- Generate default slots for the new company
    FOR i IN 1..array_length(slot_types, 1) LOOP
        slot_type := slot_types[i];
        slot_priority := slot_priorities[i];

        -- Generate unique Barton ID for this slot
        slot_barton_id := generate_slot_barton_id('04'); -- Neon tool code

        -- Insert the slot
        INSERT INTO marketing.company_slot (
            company_slot_unique_id,
            company_unique_id,
            slot_type,
            slot_title,
            slot_description,
            priority_order,
            slot_status,
            altitude,
            process_step
        ) VALUES (
            slot_barton_id,
            NEW.company_unique_id,
            slot_type,
            slot_type, -- title same as type for default slots
            'Auto-generated ' || slot_type || ' slot for ' || NEW.company_name,
            slot_priority,
            'active',
            10000,
            'auto_slot_generation'
        );

        -- Log slot creation in company audit log
        INSERT INTO marketing.company_audit_log (
            company_unique_id,
            action,
            status,
            source,
            error_log,
            new_values,
            altitude,
            process_id,
            session_id
        ) VALUES (
            NEW.company_unique_id,
            'insert',
            'success',
            'auto_slot_trigger',
            NULL,
            jsonb_build_object(
                'slot_type', slot_type,
                'company_slot_unique_id', slot_barton_id,
                'action', 'auto_generated_slot'
            ),
            10000,
            'auto_slot_generation',
            'slot_gen_' || NEW.company_unique_id
        );
    END LOOP;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- AUTO-SLOT GENERATION TRIGGER
-- ==============================================================================

/**
 * AFTER INSERT Trigger: Auto-generate slots when company is created
 * Fires after company insertion to ensure company record exists first
 */
CREATE TRIGGER trigger_ensure_company_slots
    AFTER INSERT ON marketing.company_raw_intake
    FOR EACH ROW EXECUTE FUNCTION trgfn_ensure_company_slots();

-- ==============================================================================
-- SLOT LOOKUP HELPER FUNCTIONS
-- ==============================================================================

/**
 * Get company slot ID by company and slot type
 * Used by people validation to find correct slot for assignment
 */
CREATE OR REPLACE FUNCTION get_company_slot_id(
    p_company_unique_id TEXT,
    p_slot_type TEXT
)
RETURNS TEXT AS $$
DECLARE
    slot_id TEXT;
BEGIN
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
 * Create additional slot for company (beyond default CEO/CFO/HR)
 * Used when companies need custom slots like CTO, CMO, etc.
 */
CREATE OR REPLACE FUNCTION create_company_slot(
    p_company_unique_id TEXT,
    p_slot_type TEXT,
    p_slot_title TEXT DEFAULT NULL,
    p_slot_description TEXT DEFAULT NULL,
    p_tool_code TEXT DEFAULT '04'
)
RETURNS TEXT AS $$
DECLARE
    slot_barton_id TEXT;
BEGIN
    -- Validate company exists
    IF NOT EXISTS (
        SELECT 1 FROM marketing.company_raw_intake
        WHERE company_unique_id = p_company_unique_id
    ) THEN
        RAISE EXCEPTION 'Company % does not exist', p_company_unique_id;
    END IF;

    -- Validate slot type
    IF p_slot_type NOT IN ('CEO', 'CFO', 'HR', 'CTO', 'CMO', 'COO', 'VP_SALES', 'VP_MARKETING', 'DIRECTOR', 'MANAGER') THEN
        RAISE EXCEPTION 'Invalid slot type: %', p_slot_type;
    END IF;

    -- Check if slot already exists
    IF EXISTS (
        SELECT 1 FROM marketing.company_slot
        WHERE company_unique_id = p_company_unique_id
          AND slot_type = p_slot_type
          AND slot_status = 'active'
    ) THEN
        RAISE EXCEPTION 'Active slot of type % already exists for company %', p_slot_type, p_company_unique_id;
    END IF;

    -- Generate Barton ID
    slot_barton_id := generate_slot_barton_id(p_tool_code);

    -- Insert new slot
    INSERT INTO marketing.company_slot (
        company_slot_unique_id,
        company_unique_id,
        slot_type,
        slot_title,
        slot_description,
        priority_order,
        slot_status,
        altitude,
        process_step
    ) VALUES (
        slot_barton_id,
        p_company_unique_id,
        p_slot_type,
        COALESCE(p_slot_title, p_slot_type),
        COALESCE(p_slot_description, 'Custom slot: ' || p_slot_type),
        100, -- default priority for custom slots
        'active',
        10000,
        'manual_slot_creation'
    );

    RETURN slot_barton_id;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- VALIDATION CONSTRAINTS
-- ==============================================================================

/**
 * Ensure unique slot types per company (no duplicate CEO, CFO, etc.)
 */
CREATE UNIQUE INDEX IF NOT EXISTS idx_company_slot_unique_type_per_company
    ON marketing.company_slot(company_unique_id, slot_type)
    WHERE slot_status = 'active';

-- ==============================================================================
-- SAMPLE DATA - Test Company Slots (Optional)
-- ==============================================================================

/**
 * Insert sample company for testing slot auto-generation
 * Uncomment to test the trigger functionality
 */
/*
INSERT INTO marketing.company_raw_intake (
    company_unique_id,
    company_name,
    website_url,
    industry,
    employee_count,
    company_phone,
    address_street,
    address_city,
    address_state,
    address_zip,
    address_country,
    source_system,
    source_record_id
) VALUES (
    generate_company_barton_id('08'), -- DBeaver tool code
    'Test University',
    'https://test.edu',
    'Higher Education',
    1500,
    '+15551234567',
    '123 University Ave',
    'Test City',
    'CA',
    '90210',
    'USA',
    'manual_test',
    'test_001'
);
*/

-- ==============================================================================
-- MIGRATION COMPLETE
-- ==============================================================================

/**
 * Company Slot Migration Complete
 *
 * Created:
 * - marketing.company_slot (with Barton ID enforcement)
 * - Auto-generation trigger for CEO/CFO/HR slots
 * - Slot Barton ID generation functions
 * - Foreign key constraints to company_raw_intake
 * - Helper functions for slot lookup and creation
 * - Performance indexes
 * - Unique constraints for slot types per company
 *
 * Auto-Generation Behavior:
 * - Every new company automatically gets 3 slots: CEO, CFO, HR
 * - Each slot has unique Barton ID (04.04.03.04.10000.XXX)
 * - Slots are logged in company_audit_log
 * - People records will attach to these slots via company_slot_unique_id
 *
 * Next Steps:
 * 1. Create people_raw_intake table (if needed)
 * 2. Build validator agents (/api/validate-company.ts, /api/validate-people.ts)
 * 3. Update validation console UI
 */
-- Trigger for IF
CREATE TRIGGER trigger_IF_updated_at
    BEFORE UPDATE ON IF
    FOR EACH ROW
    EXECUTE FUNCTION trigger_updated_at();

-- ============================================
-- People Schema DDL for Barton Outreach Core
-- ============================================

-- Create people schema
CREATE SCHEMA IF NOT EXISTS people;

-- ============================================
-- Core People Table
-- ============================================
CREATE TABLE IF NOT EXISTS people.marketing_people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id TEXT, -- For tracking external system IDs (Apollo, etc.)
    company_id UUID, -- References company.marketing_company.id
    
    -- Contact Information
    first_name TEXT,
    last_name TEXT,
    full_name TEXT,
    email TEXT,
    phone TEXT,
    
    -- Professional Information
    title TEXT,
    department TEXT,
    seniority_level TEXT, -- C-Level, VP, Director, Manager, Individual Contributor
    role_type TEXT, -- CEO, CFO, HR, etc.
    
    -- Social/Web Presence
    linkedin_url TEXT,
    personal_website TEXT,
    
    -- Validation Status
    email_validation_status TEXT DEFAULT 'unverified', -- unverified, valid, invalid, risky
    email_validation_score NUMERIC(3,2), -- 0.00 to 1.00
    email_validation_provider TEXT, -- MillionVerifier, ZeroBounce, etc.
    email_validated_at TIMESTAMP,
    
    -- Outreach Status
    outreach_phase INTEGER DEFAULT 0, -- 0=not contacted, 1=initial, 2=follow-up, etc.
    lead_pipeline_status TEXT DEFAULT 'new', -- new, qualified, contacted, replied, scheduled, closed
    lead_score NUMERIC(5,2), -- 0.00 to 100.00
    
    -- Contact Preferences & Compliance
    opt_out_status BOOLEAN DEFAULT false,
    opt_out_date TIMESTAMP,
    gdpr_consent BOOLEAN DEFAULT false,
    contact_preferences JSONB, -- {email: true, linkedin: false, phone: false}
    
    -- Data Sources & Tracking
    source TEXT DEFAULT 'manual', -- manual, apollo, apify, import, etc.
    source_campaign TEXT, -- Which campaign/scrape this came from
    scrape_session_id TEXT, -- Links to the specific scrape session
    
    -- Metadata
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    created_by TEXT DEFAULT current_user,
    modified_by TEXT,
    
    -- Data Quality & Enrichment
    data_quality_score INTEGER DEFAULT 0, -- 0-100
    enrichment_status TEXT DEFAULT 'basic', -- basic, enriched, premium
    last_enriched_at TIMESTAMP,
    
    -- Barton Doctrine Fields
    unique_id TEXT, -- Barton unique identifier
    process_id TEXT, -- Process that created/modified this record
    blueprint_version_hash TEXT,
    
    -- Additional metadata
    notes TEXT,
    tags JSONB, -- Flexible tagging system
    custom_fields JSONB -- For additional data that doesn't fit standard fields
);

-- ============================================
-- Contact History Table (History-First Writes)
-- ============================================
CREATE TABLE IF NOT EXISTS people.contact_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL, -- References people.marketing_people.id
    
    -- Change Tracking
    change_type TEXT NOT NULL, -- created, updated, email_validated, outreach_status_changed, etc.
    old_values JSONB, -- Previous state
    new_values JSONB, -- New state
    changed_fields TEXT[], -- Array of field names that changed
    
    -- Source Information
    source_system TEXT, -- apify, validator, manual, campaign, etc.
    source_session_id TEXT,
    initiated_by TEXT, -- user_id or system_process
    
    -- Barton Doctrine Fields
    process_id TEXT,
    unique_id TEXT,
    blueprint_version_hash TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT now(),
    notes TEXT
);

-- ============================================
-- Validation Status Table (For detailed email validation tracking)
-- ============================================
CREATE TABLE IF NOT EXISTS people.validation_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL, -- References people.marketing_people.id
    email TEXT NOT NULL,
    
    -- Validation Results
    validation_provider TEXT NOT NULL, -- MillionVerifier, ZeroBounce, etc.
    validation_status TEXT NOT NULL, -- valid, invalid, risky, unknown
    validation_score NUMERIC(3,2), -- 0.00 to 1.00
    validation_reason TEXT, -- catch_all, disposable, role_based, syntax_error, etc.
    
    -- Detailed Results (Provider-specific)
    provider_response JSONB, -- Full response from validation service
    
    -- Metadata
    validated_at TIMESTAMP DEFAULT now(),
    validation_cost NUMERIC(10,4), -- Cost in credits/dollars
    
    -- Barton Doctrine Fields
    process_id TEXT,
    unique_id TEXT,
    blueprint_version_hash TEXT
);

-- ============================================
-- Role Slots Table (For tracking company role requirements)
-- ============================================
CREATE TABLE IF NOT EXISTS people.company_role_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL, -- References company.marketing_company.id
    
    -- Role Definition
    role_type TEXT NOT NULL, -- CEO, CFO, HR, CTO, etc.
    target_count INTEGER DEFAULT 1, -- How many of this role we want
    priority_level INTEGER DEFAULT 1, -- 1=highest, 5=lowest
    
    -- Status
    slot_status TEXT DEFAULT 'open', -- open, filled, paused, closed
    filled_count INTEGER DEFAULT 0,
    
    -- Requirements
    seniority_requirements TEXT[], -- ['C-Level', 'VP']
    department_preferences TEXT[], -- ['Finance', 'Operations']
    title_keywords TEXT[], -- Keywords to match in titles
    
    -- Barton Doctrine Fields
    process_id TEXT,
    unique_id TEXT,
    blueprint_version_hash TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    created_by TEXT DEFAULT current_user
);

-- ============================================
-- Slot History Table (Track role slot changes)
-- ============================================
CREATE TABLE IF NOT EXISTS people.slot_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slot_id UUID NOT NULL, -- References people.company_role_slots.id
    person_id UUID, -- References people.marketing_people.id (if person assigned)
    
    -- Action Tracking
    action_type TEXT NOT NULL, -- slot_created, person_assigned, person_removed, slot_filled, etc.
    old_status TEXT,
    new_status TEXT,
    
    -- Source Information
    source_system TEXT, -- apify, manual, validator, etc.
    scrape_session_id TEXT,
    
    -- Barton Doctrine Fields
    process_id TEXT,
    unique_id TEXT,
    blueprint_version_hash TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT now(),
    initiated_by TEXT,
    notes TEXT
);

-- ============================================
-- Indexes for Performance
-- ============================================

-- Primary lookup indexes
CREATE INDEX IF NOT EXISTS idx_marketing_people_email ON people.marketing_people(email);
CREATE INDEX IF NOT EXISTS idx_marketing_people_company_id ON people.marketing_people(company_id);
CREATE INDEX IF NOT EXISTS idx_marketing_people_external_id ON people.marketing_people(external_id);
CREATE INDEX IF NOT EXISTS idx_marketing_people_role_type ON people.marketing_people(role_type);
CREATE INDEX IF NOT EXISTS idx_marketing_people_pipeline_status ON people.marketing_people(lead_pipeline_status);

-- History table indexes
CREATE INDEX IF NOT EXISTS idx_contact_history_person_id ON people.contact_history(person_id);
CREATE INDEX IF NOT EXISTS idx_contact_history_created_at ON people.contact_history(created_at);
CREATE INDEX IF NOT EXISTS idx_contact_history_change_type ON people.contact_history(change_type);

-- Validation indexes
CREATE INDEX IF NOT EXISTS idx_validation_status_person_id ON people.validation_status(person_id);
CREATE INDEX IF NOT EXISTS idx_validation_status_email ON people.validation_status(email);
CREATE INDEX IF NOT EXISTS idx_validation_status_provider ON people.validation_status(validation_provider);

-- Role slots indexes
CREATE INDEX IF NOT EXISTS idx_company_role_slots_company_id ON people.company_role_slots(company_id);
CREATE INDEX IF NOT EXISTS idx_company_role_slots_role_type ON people.company_role_slots(role_type);
CREATE INDEX IF NOT EXISTS idx_company_role_slots_status ON people.company_role_slots(slot_status);

-- Slot history indexes
CREATE INDEX IF NOT EXISTS idx_slot_history_slot_id ON people.slot_history(slot_id);
CREATE INDEX IF NOT EXISTS idx_slot_history_person_id ON people.slot_history(person_id);
CREATE INDEX IF NOT EXISTS idx_slot_history_created_at ON people.slot_history(created_at);

-- ============================================
-- Foreign Key Constraints (Optional - depends on your setup)
-- ============================================
-- Note: Uncomment these if you want strict referential integrity
-- You may need to adjust table references based on your exact schema

-- ALTER TABLE people.marketing_people 
-- ADD CONSTRAINT fk_marketing_people_company 
-- FOREIGN KEY (company_id) REFERENCES company.marketing_company(id);

-- ALTER TABLE people.contact_history 
-- ADD CONSTRAINT fk_contact_history_person 
-- FOREIGN KEY (person_id) REFERENCES people.marketing_people(id);

-- ALTER TABLE people.validation_status 
-- ADD CONSTRAINT fk_validation_status_person 
-- FOREIGN KEY (person_id) REFERENCES people.marketing_people(id);

-- ALTER TABLE people.company_role_slots 
-- ADD CONSTRAINT fk_company_role_slots_company 
-- FOREIGN KEY (company_id) REFERENCES company.marketing_company(id);

-- ALTER TABLE people.slot_history 
-- ADD CONSTRAINT fk_slot_history_slot 
-- FOREIGN KEY (slot_id) REFERENCES people.company_role_slots(id);

-- ALTER TABLE people.slot_history 
-- ADD CONSTRAINT fk_slot_history_person 
-- FOREIGN KEY (person_id) REFERENCES people.marketing_people(id);

-- ============================================
-- Triggers for Updated At
-- ============================================
CREATE OR REPLACE FUNCTION people.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_marketing_people_updated_at 
    BEFORE UPDATE ON people.marketing_people 
    FOR EACH ROW EXECUTE FUNCTION people.update_updated_at_column();

CREATE TRIGGER update_company_role_slots_updated_at 
    BEFORE UPDATE ON people.company_role_slots 
    FOR EACH ROW EXECUTE FUNCTION people.update_updated_at_column();

-- ============================================
-- Comments for Documentation
-- ============================================
COMMENT ON SCHEMA people IS 'Schema for managing people/contacts in the marketing outreach system';
COMMENT ON TABLE people.marketing_people IS 'Main table for storing contact/people information with validation and outreach tracking';
COMMENT ON TABLE people.contact_history IS 'History-first writes - tracks all changes to people records';
COMMENT ON TABLE people.validation_status IS 'Detailed email validation results from various providers';
COMMENT ON TABLE people.company_role_slots IS 'Defines role requirements for companies (CEO, CFO, HR slots)';
COMMENT ON TABLE people.slot_history IS 'Tracks changes to role slots and person assignments';

COMMENT ON COLUMN people.marketing_people.lead_pipeline_status IS 'Tracks progression through outreach pipeline: new -> qualified -> contacted -> replied -> scheduled -> closed';
COMMENT ON COLUMN people.marketing_people.email_validation_status IS 'Email validation status: unverified, valid, invalid, risky';
COMMENT ON COLUMN people.marketing_people.unique_id IS 'Barton Doctrine unique identifier for this record';
COMMENT ON COLUMN people.marketing_people.process_id IS 'Barton Doctrine process that created/modified this record';
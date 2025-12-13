-- =====================================================
-- Migration: Create field_mappings table
-- Barton ID: 04.04.02.04.10000.003 (Mapper)
-- Description: Stores field mapping configurations
-- =====================================================

-- Create config schema if not exists
CREATE SCHEMA IF NOT EXISTS config;

-- Create field_mappings table
CREATE TABLE IF NOT EXISTS config.field_mappings (
    mapping_id SERIAL PRIMARY KEY,
    mapping_name VARCHAR(255) NOT NULL,
    source_format VARCHAR(50) NOT NULL, -- csv, json, api, etc.
    target_schema VARCHAR(100) NOT NULL DEFAULT 'marketing',
    target_table VARCHAR(100) NOT NULL,
    mapping_rules JSONB NOT NULL, -- {source_field: target_field} pairs
    transformation_logic JSONB, -- Optional transformation functions
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100) DEFAULT 'system'
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_field_mappings_format ON config.field_mappings(source_format);
CREATE INDEX IF NOT EXISTS idx_field_mappings_table ON config.field_mappings(target_table);
CREATE INDEX IF NOT EXISTS idx_field_mappings_enabled ON config.field_mappings(enabled);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_field_mappings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER field_mappings_updated_at
    BEFORE UPDATE ON config.field_mappings
    FOR EACH ROW
    EXECUTE FUNCTION update_field_mappings_updated_at();

-- Insert sample mappings
INSERT INTO config.field_mappings (mapping_name, source_format, target_table, mapping_rules) VALUES
('CSV to Company Master', 'csv', 'company_master', '{
    "Company Name": "company_name",
    "Industry": "industry",
    "Employee Count": "employee_count",
    "Website": "website",
    "Address": "address"
}'::jsonb),
('API to People Master', 'api', 'people_master', '{
    "fullName": "full_name",
    "email": "email",
    "linkedinUrl": "linkedin_url",
    "jobTitle": "title",
    "companyId": "company_unique_id"
}'::jsonb);

-- Grant permissions
GRANT ALL ON SCHEMA config TO "Marketing DB_owner";
GRANT SELECT, INSERT, UPDATE ON config.field_mappings TO "Marketing DB_owner";
GRANT USAGE, SELECT ON SEQUENCE config.field_mappings_mapping_id_seq TO "Marketing DB_owner";

-- Log migration
INSERT INTO shq.audit_log (event_type, event_data, barton_id, created_at)
VALUES (
    'migration.executed',
    '{"migration": "002_create_field_mappings", "tool": "mapper", "barton_id": "04.04.02.04.10000.003"}',
    '04.04.02.04.10000.003',
    NOW()
);

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Migration 002_create_field_mappings completed successfully';
END $$;

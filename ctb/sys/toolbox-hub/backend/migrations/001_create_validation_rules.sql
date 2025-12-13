-- =====================================================
-- Migration: Create validation_rules table
-- Barton ID: 04.04.02.04.10000.002 (Validator)
-- Description: Stores validation rules for Validator tool
-- =====================================================

-- Create validation_rules table
CREATE TABLE IF NOT EXISTS marketing.validation_rules (
    rule_id SERIAL PRIMARY KEY,
    rule_name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- field_required, field_format, field_range, cross_field
    table_name VARCHAR(100) NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    validation_logic JSONB NOT NULL, -- Stores pattern, min/max values, etc.
    severity VARCHAR(20) NOT NULL DEFAULT 'warning', -- info, warning, error, critical
    error_message TEXT NOT NULL,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100) DEFAULT 'system'
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_validation_rules_table ON marketing.validation_rules(table_name);
CREATE INDEX IF NOT EXISTS idx_validation_rules_enabled ON marketing.validation_rules(enabled);
CREATE INDEX IF NOT EXISTS idx_validation_rules_type ON marketing.validation_rules(rule_type);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_validation_rules_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER validation_rules_updated_at
    BEFORE UPDATE ON marketing.validation_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_validation_rules_updated_at();

-- Insert sample validation rules
INSERT INTO marketing.validation_rules (rule_name, rule_type, table_name, field_name, validation_logic, severity, error_message) VALUES
('Company Name Required', 'field_required', 'company_master', 'company_name', '{}', 'critical', 'Company name is required'),
('Email Format', 'field_format', 'people_master', 'email', '{"pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"}', 'error', 'Invalid email format'),
('Employee Count Range', 'field_range', 'company_master', 'employee_count', '{"min": 1, "max": 1000000}', 'warning', 'Employee count must be between 1 and 1,000,000'),
('LinkedIn URL Format', 'field_format', 'people_master', 'linkedin_url', '{"pattern": "^https?://([a-z]{2,3}\\.)?linkedin\\.com/.*$"}', 'warning', 'Invalid LinkedIn URL format');

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON marketing.validation_rules TO "Marketing DB_owner";
GRANT USAGE, SELECT ON SEQUENCE marketing.validation_rules_rule_id_seq TO "Marketing DB_owner";

-- Log migration
INSERT INTO shq.audit_log (event_type, event_data, barton_id, created_at)
VALUES (
    'migration.executed',
    '{"migration": "001_create_validation_rules", "tool": "validator", "barton_id": "04.04.02.04.10000.002"}',
    '04.04.02.04.10000.002',
    NOW()
);

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Migration 001_create_validation_rules completed successfully';
END $$;

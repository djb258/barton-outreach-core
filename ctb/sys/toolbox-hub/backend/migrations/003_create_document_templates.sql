-- =====================================================
-- Migration: Create document_templates table
-- Barton ID: 04.04.02.04.10000.005 (DocFiller)
-- Description: Stores document templates for DocFiller
-- =====================================================

-- Create document_templates table
CREATE TABLE IF NOT EXISTS config.document_templates (
    template_id SERIAL PRIMARY KEY,
    template_name VARCHAR(255) NOT NULL,
    template_type VARCHAR(50) NOT NULL, -- email, letter, report, contract
    template_content TEXT NOT NULL, -- Jinja2 template syntax
    template_variables JSONB, -- List of expected variables
    google_docs_template_id VARCHAR(255), -- Optional Google Docs template ID
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100) DEFAULT 'system'
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_document_templates_type ON config.document_templates(template_type);
CREATE INDEX IF NOT EXISTS idx_document_templates_enabled ON config.document_templates(enabled);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_document_templates_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER document_templates_updated_at
    BEFORE UPDATE ON config.document_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_document_templates_updated_at();

-- Insert sample templates
INSERT INTO config.document_templates (template_name, template_type, template_content, template_variables) VALUES
('Outreach Email Template', 'email',
'Dear {{ person_name }},

We are reaching out regarding {{ company_name }} and their {{ industry }} operations.

Best regards,
The Barton Team',
'["person_name", "company_name", "industry"]'::jsonb),

('Company Report Template', 'report',
'# Company Report: {{ company_name }}

**Industry:** {{ industry }}
**Employees:** {{ employee_count }}
**CEO:** {{ ceo_name }}

Generated: {{ generated_date }}',
'["company_name", "industry", "employee_count", "ceo_name", "generated_date"]'::jsonb);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON config.document_templates TO "Marketing DB_owner";
GRANT USAGE, SELECT ON SEQUENCE config.document_templates_template_id_seq TO "Marketing DB_owner";

-- Log migration
INSERT INTO shq.audit_log (event_type, event_data, barton_id, created_at)
VALUES (
    'migration.executed',
    '{"migration": "003_create_document_templates", "tool": "docfiller", "barton_id": "04.04.02.04.10000.005"}',
    '04.04.02.04.10000.005',
    NOW()
);

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Migration 003_create_document_templates completed successfully';
END $$;

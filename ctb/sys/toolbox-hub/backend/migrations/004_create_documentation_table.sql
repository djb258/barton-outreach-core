-- =====================================================
-- Migration: Create documentation table
-- Barton ID: 04.04.02.04.10000.007 (Documentation)
-- Description: Stores self-documentation for toolbox
-- =====================================================

-- Create documentation table
CREATE TABLE IF NOT EXISTS config.documentation (
    doc_id SERIAL PRIMARY KEY,
    tool_id VARCHAR(50), -- NULL for system-wide docs
    doc_category VARCHAR(100) NOT NULL, -- setup, api, integration, troubleshooting
    doc_title VARCHAR(255) NOT NULL,
    doc_content TEXT NOT NULL, -- Markdown format
    doc_keywords TEXT[], -- Searchable keywords
    doc_order INTEGER DEFAULT 0, -- Display order
    visible BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100) DEFAULT 'system'
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_documentation_tool ON config.documentation(tool_id);
CREATE INDEX IF NOT EXISTS idx_documentation_category ON config.documentation(doc_category);
CREATE INDEX IF NOT EXISTS idx_documentation_visible ON config.documentation(visible);
CREATE INDEX IF NOT EXISTS idx_documentation_keywords ON config.documentation USING GIN(doc_keywords);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_documentation_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER documentation_updated_at
    BEFORE UPDATE ON config.documentation
    FOR EACH ROW
    EXECUTE FUNCTION update_documentation_updated_at();

-- Insert sample documentation
INSERT INTO config.documentation (tool_id, doc_category, doc_title, doc_content, doc_keywords) VALUES
(NULL, 'setup', 'Getting Started with Barton Toolbox Hub',
'# Getting Started

This guide will help you set up and configure the Barton Toolbox Hub.

## Prerequisites
- Neon PostgreSQL database access
- Environment variables configured
- N8N webhook access

## Installation
1. Clone the repository
2. Copy .env.template to .env
3. Configure environment variables
4. Run database migrations
5. Start the tools

For detailed instructions, see the README.md',
ARRAY['setup', 'getting-started', 'installation']),

('router', 'troubleshooting', 'Router Tool - Common Issues',
'# Router Tool Troubleshooting

## Issue: Google Sheets not creating
**Solution:** Check GOOGLE_SHEETS_API_KEY and service account permissions

## Issue: Kill switch triggered
**Solution:** Error rate exceeded 50%. Check recent errors in shq.error_master',
ARRAY['router', 'troubleshooting', 'google-sheets', 'kill-switch']),

('validator', 'api', 'Validator API Reference',
'# Validator API

## Endpoints

### POST /api/validator/validate
Validate a record against stored rules

**Request:**
```json
{
  "table_name": "company_master",
  "record_id": "04.04.02.04.30000.001"
}
```

**Response:**
```json
{
  "validation_passed": true,
  "failures": []
}
```',
ARRAY['validator', 'api', 'reference']);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON config.documentation TO "Marketing DB_owner";
GRANT USAGE, SELECT ON SEQUENCE config.documentation_doc_id_seq TO "Marketing DB_owner";

-- Log migration
INSERT INTO shq.audit_log (event_type, event_data, barton_id, created_at)
VALUES (
    'migration.executed',
    '{"migration": "004_create_documentation_table", "tool": "documentation", "barton_id": "04.04.02.04.10000.007"}',
    '04.04.02.04.10000.007',
    NOW()
);

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Migration 004_create_documentation_table completed successfully';
END $$;

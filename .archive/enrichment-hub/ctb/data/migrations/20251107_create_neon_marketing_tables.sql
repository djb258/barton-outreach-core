-- Migration: Create Neon Marketing Tables
-- Created: 2025-11-07
-- Database: Neon PostgreSQL
-- Purpose: Production tables for validated and promoted marketing data

-- ============================================
-- Create Schemas
-- ============================================

CREATE SCHEMA IF NOT EXISTS marketing;
CREATE SCHEMA IF NOT EXISTS shq;

-- ============================================
-- Company Master Table
-- ============================================

CREATE TABLE IF NOT EXISTS marketing.company_master (
  id SERIAL PRIMARY KEY,

  -- Basic company information
  company_name VARCHAR(255) NOT NULL,
  domain VARCHAR(255) UNIQUE,
  industry VARCHAR(100),
  employee_count INTEGER,
  revenue DECIMAL(15,2),
  location VARCHAR(255),
  linkedin_url TEXT,

  -- Enrichment metadata
  enrichment_source VARCHAR(50) DEFAULT 'enrichment_hub',
  enriched_at TIMESTAMP,
  validation_status VARCHAR(50) DEFAULT 'PASSED',
  metadata JSONB,

  -- Audit fields
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  -- Constraints
  CONSTRAINT chk_company_validation_status CHECK (
    validation_status IN ('PASSED', 'VALIDATED', 'FLAGGED', 'ARCHIVED')
  ),
  CONSTRAINT chk_company_enrichment_source CHECK (
    enrichment_source IN ('enrichment_hub', 'manual', 'import', 'api', 'integration')
  )
);

-- ============================================
-- People Master Table
-- ============================================

CREATE TABLE IF NOT EXISTS marketing.people_master (
  id SERIAL PRIMARY KEY,

  -- Basic person information
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  email VARCHAR(255) UNIQUE,
  phone VARCHAR(50),
  title VARCHAR(255),

  -- Company association
  company_id INTEGER REFERENCES marketing.company_master(id) ON DELETE SET NULL,
  company_name VARCHAR(255),
  linkedin_url TEXT,

  -- Enrichment metadata
  enrichment_source VARCHAR(50) DEFAULT 'enrichment_hub',
  enriched_at TIMESTAMP,
  validation_status VARCHAR(50) DEFAULT 'PASSED',
  metadata JSONB,

  -- Audit fields
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  -- Constraints
  CONSTRAINT chk_people_validation_status CHECK (
    validation_status IN ('PASSED', 'VALIDATED', 'FLAGGED', 'ARCHIVED')
  ),
  CONSTRAINT chk_people_enrichment_source CHECK (
    enrichment_source IN ('enrichment_hub', 'manual', 'import', 'api', 'integration')
  )
);

-- ============================================
-- Validation Log Table (SHQ Schema)
-- ============================================

CREATE TABLE IF NOT EXISTS shq.validation_log (
  id SERIAL PRIMARY KEY,

  -- Workflow information
  workflow_name VARCHAR(100) NOT NULL,
  entity_type VARCHAR(50) NOT NULL,
  action VARCHAR(50) NOT NULL,

  -- Metrics
  record_count INTEGER DEFAULT 0,
  status VARCHAR(50) NOT NULL,

  -- Additional data
  metadata JSONB,

  -- Timestamps
  timestamp TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW(),

  -- Constraints
  CONSTRAINT chk_log_entity_type CHECK (
    entity_type IN ('company', 'people', 'contact', 'account', 'other')
  ),
  CONSTRAINT chk_log_action CHECK (
    action IN ('promotion', 'validation', 'enrichment', 'cleanup', 'import', 'export', 'update', 'delete')
  ),
  CONSTRAINT chk_log_status CHECK (
    status IN ('success', 'failure', 'partial', 'warning', 'info')
  )
);

-- ============================================
-- Indexes for Performance
-- ============================================

-- Company master indexes
CREATE INDEX IF NOT EXISTS idx_company_master_domain
  ON marketing.company_master(domain)
  WHERE domain IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_company_master_industry
  ON marketing.company_master(industry)
  WHERE industry IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_company_master_enrichment_source
  ON marketing.company_master(enrichment_source, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_company_master_validation_status
  ON marketing.company_master(validation_status);

CREATE INDEX IF NOT EXISTS idx_company_master_created_at
  ON marketing.company_master(created_at DESC);

-- People master indexes
CREATE INDEX IF NOT EXISTS idx_people_master_email
  ON marketing.people_master(email)
  WHERE email IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_people_master_company_id
  ON marketing.people_master(company_id)
  WHERE company_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_people_master_name
  ON marketing.people_master(last_name, first_name);

CREATE INDEX IF NOT EXISTS idx_people_master_enrichment_source
  ON marketing.people_master(enrichment_source, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_people_master_validation_status
  ON marketing.people_master(validation_status);

CREATE INDEX IF NOT EXISTS idx_people_master_created_at
  ON marketing.people_master(created_at DESC);

-- Validation log indexes
CREATE INDEX IF NOT EXISTS idx_validation_log_workflow
  ON shq.validation_log(workflow_name, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_validation_log_entity_type
  ON shq.validation_log(entity_type, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_validation_log_status
  ON shq.validation_log(status, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_validation_log_timestamp
  ON shq.validation_log(timestamp DESC);

-- ============================================
-- Triggers for Updated At
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for company master
DROP TRIGGER IF EXISTS update_company_master_updated_at ON marketing.company_master;
CREATE TRIGGER update_company_master_updated_at
  BEFORE UPDATE ON marketing.company_master
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Trigger for people master
DROP TRIGGER IF EXISTS update_people_master_updated_at ON marketing.people_master;
CREATE TRIGGER update_people_master_updated_at
  BEFORE UPDATE ON marketing.people_master
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Monitoring Views
-- ============================================

-- Enrichment promotion statistics
CREATE OR REPLACE VIEW shq.enrichment_promotion_stats AS
SELECT
  DATE(timestamp) as promotion_date,
  entity_type,
  SUM(record_count) as total_promoted,
  COUNT(*) as execution_count,
  SUM(CASE WHEN status = 'success' THEN record_count ELSE 0 END) as successful_promotions,
  SUM(CASE WHEN status = 'failure' THEN record_count ELSE 0 END) as failed_promotions
FROM shq.validation_log
WHERE workflow_name = 'Pull from Enrichment Hub'
  AND action = 'promotion'
GROUP BY DATE(timestamp), entity_type
ORDER BY promotion_date DESC;

-- Company enrichment summary
CREATE OR REPLACE VIEW marketing.company_enrichment_summary AS
SELECT
  enrichment_source,
  validation_status,
  COUNT(*) as company_count,
  COUNT(DISTINCT industry) as unique_industries,
  AVG(employee_count) as avg_employees,
  MIN(created_at) as first_created,
  MAX(created_at) as last_created
FROM marketing.company_master
GROUP BY enrichment_source, validation_status;

-- People enrichment summary
CREATE OR REPLACE VIEW marketing.people_enrichment_summary AS
SELECT
  enrichment_source,
  validation_status,
  COUNT(*) as people_count,
  COUNT(DISTINCT company_id) as unique_companies,
  COUNT(DISTINCT title) as unique_titles,
  MIN(created_at) as first_created,
  MAX(created_at) as last_created
FROM marketing.people_master
GROUP BY enrichment_source, validation_status;

-- ============================================
-- Functions for Data Quality
-- ============================================

-- Function to check for duplicate companies by domain
CREATE OR REPLACE FUNCTION marketing.check_duplicate_companies()
RETURNS TABLE(domain VARCHAR, duplicate_count BIGINT) AS $$
BEGIN
  RETURN QUERY
  SELECT
    c.domain,
    COUNT(*) as duplicate_count
  FROM marketing.company_master c
  WHERE c.domain IS NOT NULL
  GROUP BY c.domain
  HAVING COUNT(*) > 1
  ORDER BY duplicate_count DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to check for duplicate people by email
CREATE OR REPLACE FUNCTION marketing.check_duplicate_people()
RETURNS TABLE(email VARCHAR, duplicate_count BIGINT) AS $$
BEGIN
  RETURN QUERY
  SELECT
    p.email,
    COUNT(*) as duplicate_count
  FROM marketing.people_master p
  WHERE p.email IS NOT NULL
  GROUP BY p.email
  HAVING COUNT(*) > 1
  ORDER BY duplicate_count DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Comments for Documentation
-- ============================================

COMMENT ON SCHEMA marketing IS
  'Schema containing production marketing data (companies and people)';

COMMENT ON SCHEMA shq IS
  'Schema for Sales Headquarters (SHQ) operations and audit logs';

COMMENT ON TABLE marketing.company_master IS
  'Master table for all validated company records from various enrichment sources';

COMMENT ON TABLE marketing.people_master IS
  'Master table for all validated people/contact records from various enrichment sources';

COMMENT ON TABLE shq.validation_log IS
  'Audit log for all validation, enrichment, and promotion workflows';

COMMENT ON VIEW shq.enrichment_promotion_stats IS
  'Daily statistics for enrichment hub data promotion workflow';

COMMENT ON VIEW marketing.company_enrichment_summary IS
  'Summary statistics for companies by enrichment source and validation status';

COMMENT ON VIEW marketing.people_enrichment_summary IS
  'Summary statistics for people by enrichment source and validation status';

-- ============================================
-- Sample Data for Testing (Optional)
-- ============================================

-- Uncomment to insert test data:
/*
INSERT INTO marketing.company_master
  (company_name, domain, industry, enrichment_source, metadata)
VALUES
  ('Acme Corporation', 'acme.com', 'Technology', 'enrichment_hub', '{"source_system": "n8n", "confidence": "high"}'::jsonb),
  ('Beta Industries', 'betaindustries.com', 'Manufacturing', 'enrichment_hub', '{"source_system": "n8n", "confidence": "medium"}'::jsonb);

INSERT INTO marketing.people_master
  (first_name, last_name, email, title, company_id, enrichment_source, metadata)
VALUES
  ('John', 'Doe', 'john.doe@acme.com', 'CEO', 1, 'enrichment_hub', '{"source_system": "n8n", "verified": true}'::jsonb),
  ('Jane', 'Smith', 'jane.smith@betaindustries.com', 'CTO', 2, 'enrichment_hub', '{"source_system": "n8n", "verified": true}'::jsonb);

INSERT INTO shq.validation_log
  (workflow_name, entity_type, action, record_count, status, metadata)
VALUES
  ('Pull from Enrichment Hub', 'company', 'promotion', 2, 'success', '{"execution_time_ms": 1234}'::jsonb),
  ('Pull from Enrichment Hub', 'people', 'promotion', 2, 'success', '{"execution_time_ms": 987}'::jsonb);
*/

-- ============================================
-- Verification Queries
-- ============================================

-- Verify schemas were created
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name IN ('marketing', 'shq');

-- Verify tables were created
SELECT
  schemaname,
  tablename,
  (SELECT COUNT(*) FROM information_schema.columns
   WHERE table_name = t.tablename AND table_schema = t.schemaname) as column_count
FROM pg_tables t
WHERE schemaname IN ('marketing', 'shq')
ORDER BY schemaname, tablename;

-- Verify indexes were created
SELECT
  schemaname,
  tablename,
  indexname
FROM pg_indexes
WHERE schemaname IN ('marketing', 'shq')
ORDER BY schemaname, tablename, indexname;

-- Verify views were created
SELECT
  schemaname,
  viewname
FROM pg_views
WHERE schemaname IN ('marketing', 'shq')
ORDER BY schemaname, viewname;

-- Test monitoring views
SELECT * FROM shq.enrichment_promotion_stats LIMIT 5;
SELECT * FROM marketing.company_enrichment_summary;
SELECT * FROM marketing.people_enrichment_summary;

-- ============================================
-- Grants and Permissions (Adjust as needed)
-- ============================================

-- Grant permissions to application user
-- GRANT USAGE ON SCHEMA marketing TO your_app_user;
-- GRANT USAGE ON SCHEMA shq TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA marketing TO your_app_user;
-- GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA shq TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA marketing TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA shq TO your_app_user;

-- ============================================
-- Rollback Script (if needed)
-- ============================================

/*
-- To rollback this migration:

DROP VIEW IF EXISTS marketing.people_enrichment_summary;
DROP VIEW IF EXISTS marketing.company_enrichment_summary;
DROP VIEW IF EXISTS shq.enrichment_promotion_stats;

DROP FUNCTION IF EXISTS marketing.check_duplicate_people();
DROP FUNCTION IF EXISTS marketing.check_duplicate_companies();

DROP TRIGGER IF EXISTS update_company_master_updated_at ON marketing.company_master;
DROP TRIGGER IF EXISTS update_people_master_updated_at ON marketing.people_master;
DROP FUNCTION IF EXISTS update_updated_at_column();

DROP TABLE IF EXISTS shq.validation_log;
DROP TABLE IF EXISTS marketing.people_master;
DROP TABLE IF EXISTS marketing.company_master;

DROP SCHEMA IF EXISTS shq CASCADE;
DROP SCHEMA IF EXISTS marketing CASCADE;
*/

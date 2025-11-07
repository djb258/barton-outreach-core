-- ============================================================================
-- Supabase Validation Framework - Initial Setup
-- ============================================================================
-- Purpose: Create core tables for validation, logging, and enrichment tracking
-- Database: Supabase (workspace)
-- Last Updated: 2025-11-07
-- ============================================================================

-- ============================================================================
-- 1. Global Validation Log
-- ============================================================================
-- Tracks every validation attempt across all entities

CREATE TABLE IF NOT EXISTS public.validation_log (
  id BIGSERIAL PRIMARY KEY,
  entity TEXT NOT NULL,              -- 'company', 'person', etc.
  record_id TEXT NOT NULL,           -- unique_id from source
  status TEXT NOT NULL CHECK (status IN ('PENDING', 'PASSED', 'FAILED', 'ENRICHING')),
  error_summary TEXT,                -- High-level error description
  error_details JSONB,               -- Detailed error breakdown
  validator_name TEXT,               -- Which validator ran this
  validation_rules_applied JSONB,    -- Rules that were checked
  timestamp TIMESTAMP DEFAULT now(),
  processing_time_ms INTEGER,        -- How long validation took
  cost_usd DECIMAL(10, 6),          -- Cost tracking

  -- Metadata
  batch_id TEXT,                     -- For batch processing tracking
  retry_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_validation_log_entity ON public.validation_log(entity);
CREATE INDEX idx_validation_log_record_id ON public.validation_log(record_id);
CREATE INDEX idx_validation_log_status ON public.validation_log(status);
CREATE INDEX idx_validation_log_timestamp ON public.validation_log(timestamp DESC);
CREATE INDEX idx_validation_log_batch_id ON public.validation_log(batch_id);

-- ============================================================================
-- 2. Audit Trail
-- ============================================================================
-- Complete audit log of all framework operations

CREATE TABLE IF NOT EXISTS public.audit_trail (
  id BIGSERIAL PRIMARY KEY,
  operation TEXT NOT NULL,           -- 'fetch', 'validate', 'promote', 'enrich'
  entity TEXT NOT NULL,
  record_id TEXT,
  status TEXT NOT NULL,
  details JSONB,
  user_id TEXT,                      -- Who/what triggered this
  source TEXT,                       -- 'n8n', 'manual', 'cron', etc.
  timestamp TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_audit_trail_operation ON public.audit_trail(operation);
CREATE INDEX idx_audit_trail_entity ON public.audit_trail(entity);
CREATE INDEX idx_audit_trail_timestamp ON public.audit_trail(timestamp DESC);

-- ============================================================================
-- 3. Generic Workspace Table Template
-- ============================================================================
-- This is a TEMPLATE - actual tables are created per-entity
-- Use this as reference when creating new entity workspace tables

/*
CREATE TABLE IF NOT EXISTS public.${workspace_table} (
  id BIGSERIAL PRIMARY KEY,
  unique_id TEXT UNIQUE NOT NULL,      -- Source record ID
  payload JSONB NOT NULL,               -- Full record data

  -- Validation Status
  validation_status TEXT DEFAULT 'PENDING' CHECK (
    validation_status IN ('PENDING', 'PASSED', 'FAILED', 'ENRICHING', 'PROMOTED')
  ),
  validation_errors JSONB,              -- Array of error objects
  validation_warnings JSONB,            -- Array of warning objects
  last_validated_at TIMESTAMP,

  -- Enrichment Status
  enrichment_status TEXT,               -- 'pending', 'running', 'completed', 'failed'
  enrichment_agent TEXT,                -- Which agent is enriching
  enrichment_attempts INTEGER DEFAULT 0,
  last_enrichment_at TIMESTAMP,

  -- Promotion Status
  promoted BOOLEAN DEFAULT false,
  promoted_at TIMESTAMP,
  promotion_error TEXT,

  -- Metadata
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now(),
  processed_by TEXT                     -- Batch ID or user ID
);

CREATE INDEX idx_${workspace_table}_unique_id ON public.${workspace_table}(unique_id);
CREATE INDEX idx_${workspace_table}_validation_status ON public.${workspace_table}(validation_status);
CREATE INDEX idx_${workspace_table}_promoted ON public.${workspace_table}(promoted);
CREATE INDEX idx_${workspace_table}_created_at ON public.${workspace_table}(created_at DESC);
*/

-- ============================================================================
-- 4. Company Workspace Table (Example)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.company_needs_enrichment (
  id BIGSERIAL PRIMARY KEY,
  unique_id TEXT UNIQUE NOT NULL,
  payload JSONB NOT NULL,

  -- Validation Status
  validation_status TEXT DEFAULT 'PENDING' CHECK (
    validation_status IN ('PENDING', 'PASSED', 'FAILED', 'ENRICHING', 'PROMOTED')
  ),
  validation_errors JSONB,
  validation_warnings JSONB,
  last_validated_at TIMESTAMP,

  -- Enrichment Status
  enrichment_status TEXT,
  enrichment_agent TEXT,
  enrichment_attempts INTEGER DEFAULT 0,
  last_enrichment_at TIMESTAMP,

  -- Promotion Status
  promoted BOOLEAN DEFAULT false,
  promoted_at TIMESTAMP,
  promotion_error TEXT,

  -- Metadata
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now(),
  processed_by TEXT
);

CREATE INDEX idx_company_enrichment_unique_id ON public.company_needs_enrichment(unique_id);
CREATE INDEX idx_company_enrichment_validation_status ON public.company_needs_enrichment(validation_status);
CREATE INDEX idx_company_enrichment_promoted ON public.company_needs_enrichment(promoted);
CREATE INDEX idx_company_enrichment_created_at ON public.company_needs_enrichment(created_at DESC);

-- ============================================================================
-- 5. People Workspace Table (Example)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.people_needs_enrichment (
  id BIGSERIAL PRIMARY KEY,
  unique_id TEXT UNIQUE NOT NULL,
  payload JSONB NOT NULL,

  -- Validation Status
  validation_status TEXT DEFAULT 'PENDING' CHECK (
    validation_status IN ('PENDING', 'PASSED', 'FAILED', 'ENRICHING', 'PROMOTED')
  ),
  validation_errors JSONB,
  validation_warnings JSONB,
  last_validated_at TIMESTAMP,

  -- Enrichment Status
  enrichment_status TEXT,
  enrichment_agent TEXT,
  enrichment_attempts INTEGER DEFAULT 0,
  last_enrichment_at TIMESTAMP,

  -- Promotion Status
  promoted BOOLEAN DEFAULT false,
  promoted_at TIMESTAMP,
  promotion_error TEXT,

  -- Metadata
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now(),
  processed_by TEXT
);

CREATE INDEX idx_people_enrichment_unique_id ON public.people_needs_enrichment(unique_id);
CREATE INDEX idx_people_enrichment_validation_status ON public.people_needs_enrichment(validation_status);
CREATE INDEX idx_people_enrichment_promoted ON public.people_needs_enrichment(promoted);
CREATE INDEX idx_people_enrichment_created_at ON public.people_needs_enrichment(created_at DESC);

-- ============================================================================
-- 6. Auto-Update Triggers
-- ============================================================================

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all workspace tables
CREATE TRIGGER update_company_enrichment_updated_at
  BEFORE UPDATE ON public.company_needs_enrichment
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_people_enrichment_updated_at
  BEFORE UPDATE ON public.people_needs_enrichment
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 7. Helper Views
-- ============================================================================

-- View: Pending Validations (across all entities)
CREATE OR REPLACE VIEW public.vw_pending_validations AS
SELECT 'company' AS entity, unique_id, created_at
FROM public.company_needs_enrichment
WHERE validation_status = 'PENDING'
UNION ALL
SELECT 'person' AS entity, unique_id, created_at
FROM public.people_needs_enrichment
WHERE validation_status = 'PENDING'
ORDER BY created_at ASC;

-- View: Failed Validations (needs review)
CREATE OR REPLACE VIEW public.vw_failed_validations AS
SELECT 'company' AS entity, unique_id, validation_errors, created_at
FROM public.company_needs_enrichment
WHERE validation_status = 'FAILED'
UNION ALL
SELECT 'person' AS entity, unique_id, validation_errors, created_at
FROM public.people_needs_enrichment
WHERE validation_status = 'FAILED'
ORDER BY created_at DESC;

-- View: Ready for Promotion
CREATE OR REPLACE VIEW public.vw_ready_for_promotion AS
SELECT 'company' AS entity, unique_id, payload, last_validated_at
FROM public.company_needs_enrichment
WHERE validation_status = 'PASSED' AND promoted = false
UNION ALL
SELECT 'person' AS entity, unique_id, payload, last_validated_at
FROM public.people_needs_enrichment
WHERE validation_status = 'PASSED' AND promoted = false
ORDER BY last_validated_at ASC;

-- ============================================================================
-- 8. Maintenance Functions
-- ============================================================================

-- Function to clean old logs (keep last 90 days)
CREATE OR REPLACE FUNCTION cleanup_old_logs()
RETURNS void AS $$
BEGIN
  DELETE FROM public.validation_log
  WHERE timestamp < now() - INTERVAL '90 days';

  DELETE FROM public.audit_trail
  WHERE timestamp < now() - INTERVAL '90 days';
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Setup Complete
-- ============================================================================

-- Insert initial audit record
INSERT INTO public.audit_trail (operation, entity, status, details, source)
VALUES (
  'init',
  'framework',
  'SUCCESS',
  '{"message": "Supabase validation framework initialized", "version": "1.0.0"}',
  'sql_migration'
);

COMMENT ON TABLE public.validation_log IS 'Tracks all validation attempts across entities';
COMMENT ON TABLE public.audit_trail IS 'Complete audit log of framework operations';
COMMENT ON TABLE public.company_needs_enrichment IS 'Workspace for company data validation and enrichment';
COMMENT ON TABLE public.people_needs_enrichment IS 'Workspace for people data validation and enrichment';

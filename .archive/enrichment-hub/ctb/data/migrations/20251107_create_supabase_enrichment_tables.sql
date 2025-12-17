-- Migration: Create Supabase Enrichment Tables
-- Created: 2025-11-07
-- Database: Supabase PostgreSQL
-- Purpose: Tables for storing enriched data awaiting validation and promotion

-- ============================================
-- Company Enrichment Table
-- ============================================

CREATE TABLE IF NOT EXISTS public.company_needs_enrichment (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Basic company information
  company_name VARCHAR(255) NOT NULL,
  domain VARCHAR(255),
  industry VARCHAR(100),
  employee_count INTEGER,
  revenue DECIMAL(15,2),
  location VARCHAR(255),
  linkedin_url TEXT,

  -- Enrichment data (flexible JSON storage)
  enrichment_data JSONB,

  -- Workflow tracking
  validation_status VARCHAR(50) DEFAULT 'PENDING',
  enriched_at TIMESTAMP DEFAULT NOW(),
  enriched_by VARCHAR(100),

  -- Promotion tracking
  promoted_at TIMESTAMP,
  promoted_to_neon BOOLEAN DEFAULT FALSE,

  -- Audit fields
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  -- Constraints
  CONSTRAINT chk_validation_status CHECK (
    validation_status IN ('PENDING', 'READY', 'PASSED', 'FAILED', 'REJECTED')
  )
);

-- ============================================
-- People Enrichment Table
-- ============================================

CREATE TABLE IF NOT EXISTS public.people_needs_enrichment (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Basic person information
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  email VARCHAR(255),
  phone VARCHAR(50),
  title VARCHAR(255),

  -- Company association
  company_id UUID,
  company_name VARCHAR(255),
  linkedin_url TEXT,

  -- Enrichment data (flexible JSON storage)
  enrichment_data JSONB,

  -- Workflow tracking
  validation_status VARCHAR(50) DEFAULT 'PENDING',
  enriched_at TIMESTAMP DEFAULT NOW(),
  enriched_by VARCHAR(100),

  -- Promotion tracking
  promoted_at TIMESTAMP,
  promoted_to_neon BOOLEAN DEFAULT FALSE,

  -- Audit fields
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  -- Constraints
  CONSTRAINT chk_people_validation_status CHECK (
    validation_status IN ('PENDING', 'READY', 'PASSED', 'FAILED', 'REJECTED')
  )
);

-- ============================================
-- Indexes for Performance
-- ============================================

-- Indexes for company enrichment
CREATE INDEX IF NOT EXISTS idx_company_validation_status
  ON public.company_needs_enrichment(validation_status, enriched_at);

CREATE INDEX IF NOT EXISTS idx_company_domain
  ON public.company_needs_enrichment(domain)
  WHERE domain IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_company_promoted
  ON public.company_needs_enrichment(promoted_at)
  WHERE promoted_to_neon = TRUE;

CREATE INDEX IF NOT EXISTS idx_company_created_at
  ON public.company_needs_enrichment(created_at DESC);

-- Indexes for people enrichment
CREATE INDEX IF NOT EXISTS idx_people_validation_status
  ON public.people_needs_enrichment(validation_status, enriched_at);

CREATE INDEX IF NOT EXISTS idx_people_email
  ON public.people_needs_enrichment(email)
  WHERE email IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_people_company_id
  ON public.people_needs_enrichment(company_id)
  WHERE company_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_people_promoted
  ON public.people_needs_enrichment(promoted_at)
  WHERE promoted_to_neon = TRUE;

CREATE INDEX IF NOT EXISTS idx_people_created_at
  ON public.people_needs_enrichment(created_at DESC);

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

-- Trigger for company enrichment
DROP TRIGGER IF EXISTS update_company_enrichment_updated_at ON public.company_needs_enrichment;
CREATE TRIGGER update_company_enrichment_updated_at
  BEFORE UPDATE ON public.company_needs_enrichment
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Trigger for people enrichment
DROP TRIGGER IF EXISTS update_people_enrichment_updated_at ON public.people_needs_enrichment;
CREATE TRIGGER update_people_enrichment_updated_at
  BEFORE UPDATE ON public.people_needs_enrichment
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Comments for Documentation
-- ============================================

COMMENT ON TABLE public.company_needs_enrichment IS
  'Staging table for enriched company data awaiting validation and promotion to Neon';

COMMENT ON TABLE public.people_needs_enrichment IS
  'Staging table for enriched people data awaiting validation and promotion to Neon';

COMMENT ON COLUMN public.company_needs_enrichment.validation_status IS
  'PENDING: Awaiting validation, READY: Ready for promotion, PASSED: Successfully promoted, FAILED: Validation failed, REJECTED: Manually rejected';

COMMENT ON COLUMN public.people_needs_enrichment.validation_status IS
  'PENDING: Awaiting validation, READY: Ready for promotion, PASSED: Successfully promoted, FAILED: Validation failed, REJECTED: Manually rejected';

COMMENT ON COLUMN public.company_needs_enrichment.enrichment_data IS
  'JSON object containing all enriched data from various sources (Apollo, Clay, LinkedIn, etc.)';

COMMENT ON COLUMN public.people_needs_enrichment.enrichment_data IS
  'JSON object containing all enriched data from various sources (Apollo, Clay, LinkedIn, etc.)';

-- ============================================
-- Sample Data for Testing (Optional)
-- ============================================

-- Uncomment to insert test data:
/*
INSERT INTO public.company_needs_enrichment
  (company_name, domain, industry, validation_status, enrichment_data)
VALUES
  ('Acme Corporation', 'acme.com', 'Technology', 'READY', '{"linkedin_followers": 10000, "website_traffic": "high"}'::jsonb),
  ('Beta Industries', 'betaindustries.com', 'Manufacturing', 'PENDING', '{"revenue_range": "10M-50M"}'::jsonb);

INSERT INTO public.people_needs_enrichment
  (first_name, last_name, email, title, company_name, validation_status, enrichment_data)
VALUES
  ('John', 'Doe', 'john.doe@acme.com', 'CEO', 'Acme Corporation', 'READY', '{"linkedin_connections": 500, "seniority": "executive"}'::jsonb),
  ('Jane', 'Smith', 'jane.smith@betaindustries.com', 'CTO', 'Beta Industries', 'PENDING', '{"years_experience": 15}'::jsonb);
*/

-- ============================================
-- Verification Queries
-- ============================================

-- Verify tables were created
SELECT
  table_name,
  (SELECT COUNT(*) FROM information_schema.columns
   WHERE table_name = t.table_name AND table_schema = 'public') as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
  AND table_name IN ('company_needs_enrichment', 'people_needs_enrichment');

-- Verify indexes were created
SELECT
  schemaname,
  tablename,
  indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('company_needs_enrichment', 'people_needs_enrichment')
ORDER BY tablename, indexname;

-- ============================================
-- Rollback Script (if needed)
-- ============================================

/*
-- To rollback this migration:

DROP TRIGGER IF EXISTS update_company_enrichment_updated_at ON public.company_needs_enrichment;
DROP TRIGGER IF EXISTS update_people_enrichment_updated_at ON public.people_needs_enrichment;
DROP FUNCTION IF EXISTS update_updated_at_column();
DROP TABLE IF EXISTS public.people_needs_enrichment;
DROP TABLE IF EXISTS public.company_needs_enrichment;
*/

-- ============================================================================
-- Talent Engine Failure Tables Migration
-- ============================================================================
-- Creates dedicated failure tables for the Hub-and-Spoke ETL system
-- Each node/agent has its own failure "bay" for repair workflows
--
-- Schema: marketing
-- Purpose: Enable SELECT → REPROCESS repair workflow
-- ============================================================================

-- 1. Company Fuzzy Match Failures
-- Bay: COMPANY_HUB / CompanyFuzzyMatchAgent
-- Captures: Companies that couldn't be matched to canonical list
CREATE TABLE IF NOT EXISTS marketing.company_fuzzy_failures (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slot_row_id TEXT NOT NULL,
  slot_row JSONB NOT NULL,
  raw_company_input TEXT,
  best_match TEXT,
  match_score NUMERIC(5,2),
  match_status TEXT, -- UNMATCHED, MANUAL_REVIEW
  reason TEXT NOT NULL,
  candidates JSONB, -- Top N candidates with scores
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  repaired_at TIMESTAMP WITH TIME ZONE,
  repair_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_company_fuzzy_failures_created
  ON marketing.company_fuzzy_failures(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_company_fuzzy_failures_status
  ON marketing.company_fuzzy_failures(match_status);
CREATE INDEX IF NOT EXISTS idx_company_fuzzy_failures_unrepaired
  ON marketing.company_fuzzy_failures(repaired_at) WHERE repaired_at IS NULL;

-- 2. Person-Company Mismatch Failures
-- Bay: PEOPLE_NODE / TitleCompanyAgent
-- Captures: People whose scraped employer doesn't match canonical company
CREATE TABLE IF NOT EXISTS marketing.person_company_mismatch (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slot_row_id TEXT NOT NULL,
  slot_row JSONB NOT NULL,
  person_name TEXT,
  canonical_company TEXT NOT NULL,
  detected_employer TEXT,
  match_score NUMERIC(5,4),
  threshold NUMERIC(5,4),
  linkedin_url TEXT,
  reason TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  repaired_at TIMESTAMP WITH TIME ZONE,
  repair_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_person_company_mismatch_created
  ON marketing.person_company_mismatch(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_person_company_mismatch_company
  ON marketing.person_company_mismatch(canonical_company);
CREATE INDEX IF NOT EXISTS idx_person_company_mismatch_unrepaired
  ON marketing.person_company_mismatch(repaired_at) WHERE repaired_at IS NULL;

-- 3. Email Pattern Failures
-- Bay: COMPANY_HUB / PatternAgent
-- Captures: Companies where email pattern couldn't be discovered
CREATE TABLE IF NOT EXISTS marketing.email_pattern_failures (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slot_row_id TEXT NOT NULL,
  slot_row JSONB NOT NULL,
  company_name TEXT NOT NULL,
  company_domain TEXT,
  attempted_sources JSONB, -- List of sources tried
  fallback_used BOOLEAN DEFAULT FALSE,
  reason TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  repaired_at TIMESTAMP WITH TIME ZONE,
  repair_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_email_pattern_failures_created
  ON marketing.email_pattern_failures(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_email_pattern_failures_company
  ON marketing.email_pattern_failures(company_name);
CREATE INDEX IF NOT EXISTS idx_email_pattern_failures_unrepaired
  ON marketing.email_pattern_failures(repaired_at) WHERE repaired_at IS NULL;

-- 4. Email Generation Failures
-- Bay: COMPANY_HUB / EmailGeneratorAgent
-- Captures: Email generation/verification failures
CREATE TABLE IF NOT EXISTS marketing.email_generation_failures (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slot_row_id TEXT NOT NULL,
  slot_row JSONB NOT NULL,
  person_name TEXT,
  company_name TEXT NOT NULL,
  company_domain TEXT,
  email_pattern TEXT,
  attempted_email TEXT,
  verification_status TEXT, -- invalid, unknown, catch_all, etc.
  reason TEXT NOT NULL,
  validation_flags JSONB, -- company_valid, person_company_valid, etc.
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  repaired_at TIMESTAMP WITH TIME ZONE,
  repair_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_email_generation_failures_created
  ON marketing.email_generation_failures(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_email_generation_failures_company
  ON marketing.email_generation_failures(company_name);
CREATE INDEX IF NOT EXISTS idx_email_generation_failures_unrepaired
  ON marketing.email_generation_failures(repaired_at) WHERE repaired_at IS NULL;

-- 5. LinkedIn Resolution Failures
-- Bay: PEOPLE_NODE / LinkedInFinderAgent
-- Captures: Failed LinkedIn URL lookups
CREATE TABLE IF NOT EXISTS marketing.linkedin_resolution_failures (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slot_row_id TEXT NOT NULL,
  slot_row JSONB NOT NULL,
  person_name TEXT NOT NULL,
  company_name TEXT NOT NULL,
  slot_type TEXT,
  attempted_sources JSONB, -- primary, fallback, etc.
  reason TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  repaired_at TIMESTAMP WITH TIME ZONE,
  repair_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_linkedin_resolution_failures_created
  ON marketing.linkedin_resolution_failures(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_linkedin_resolution_failures_person
  ON marketing.linkedin_resolution_failures(person_name);
CREATE INDEX IF NOT EXISTS idx_linkedin_resolution_failures_unrepaired
  ON marketing.linkedin_resolution_failures(repaired_at) WHERE repaired_at IS NULL;

-- 6. Missing Slot Discovery Failures
-- Bay: COMPANY_HUB / MissingSlotAgent
-- Captures: Failed slot discovery attempts
CREATE TABLE IF NOT EXISTS marketing.slot_discovery_failures (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id TEXT NOT NULL,
  company_name TEXT NOT NULL,
  slot_type TEXT NOT NULL,
  discovery_method TEXT,
  reason TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  repaired_at TIMESTAMP WITH TIME ZONE,
  repair_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_slot_discovery_failures_created
  ON marketing.slot_discovery_failures(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_slot_discovery_failures_company
  ON marketing.slot_discovery_failures(company_id);
CREATE INDEX IF NOT EXISTS idx_slot_discovery_failures_slot
  ON marketing.slot_discovery_failures(slot_type);
CREATE INDEX IF NOT EXISTS idx_slot_discovery_failures_unrepaired
  ON marketing.slot_discovery_failures(repaired_at) WHERE repaired_at IS NULL;

-- 7. DOL Sync Failures
-- Bay: DOL_NODE / DOLSyncAgent
-- Captures: Failed DOL data sync attempts
CREATE TABLE IF NOT EXISTS marketing.dol_sync_failures (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id TEXT NOT NULL,
  company_name TEXT NOT NULL,
  ein TEXT,
  sync_type TEXT, -- single_company, batch, etc.
  reason TEXT NOT NULL,
  api_response JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  repaired_at TIMESTAMP WITH TIME ZONE,
  repair_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_dol_sync_failures_created
  ON marketing.dol_sync_failures(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_dol_sync_failures_company
  ON marketing.dol_sync_failures(company_id);
CREATE INDEX IF NOT EXISTS idx_dol_sync_failures_unrepaired
  ON marketing.dol_sync_failures(repaired_at) WHERE repaired_at IS NULL;

-- 8. Generic Agent Failures (catch-all)
-- Bay: ANY / Any agent that doesn't have a dedicated table
-- Captures: Unexpected errors, edge cases
CREATE TABLE IF NOT EXISTS marketing.agent_failures (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  node_id TEXT NOT NULL, -- COMPANY_HUB, PEOPLE_NODE, DOL_NODE, BIT_NODE
  agent_type TEXT NOT NULL,
  slot_row_id TEXT,
  slot_row JSONB,
  task_id TEXT,
  error_type TEXT, -- validation, api, timeout, unknown
  reason TEXT NOT NULL,
  stack_trace TEXT,
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  repaired_at TIMESTAMP WITH TIME ZONE,
  repair_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_agent_failures_created
  ON marketing.agent_failures(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_failures_node
  ON marketing.agent_failures(node_id);
CREATE INDEX IF NOT EXISTS idx_agent_failures_agent
  ON marketing.agent_failures(agent_type);
CREATE INDEX IF NOT EXISTS idx_agent_failures_unrepaired
  ON marketing.agent_failures(repaired_at) WHERE repaired_at IS NULL;

-- ============================================================================
-- Failure Summary View
-- ============================================================================
-- Aggregates failure counts across all bays for monitoring

CREATE OR REPLACE VIEW marketing.failure_summary AS
SELECT
  'company_fuzzy_failures' AS bay,
  'COMPANY_HUB' AS node,
  'CompanyFuzzyMatchAgent' AS agent,
  COUNT(*) AS total_failures,
  COUNT(*) FILTER (WHERE repaired_at IS NULL) AS pending_repairs,
  MAX(created_at) AS last_failure
FROM marketing.company_fuzzy_failures

UNION ALL

SELECT
  'person_company_mismatch' AS bay,
  'PEOPLE_NODE' AS node,
  'TitleCompanyAgent' AS agent,
  COUNT(*) AS total_failures,
  COUNT(*) FILTER (WHERE repaired_at IS NULL) AS pending_repairs,
  MAX(created_at) AS last_failure
FROM marketing.person_company_mismatch

UNION ALL

SELECT
  'email_pattern_failures' AS bay,
  'COMPANY_HUB' AS node,
  'PatternAgent' AS agent,
  COUNT(*) AS total_failures,
  COUNT(*) FILTER (WHERE repaired_at IS NULL) AS pending_repairs,
  MAX(created_at) AS last_failure
FROM marketing.email_pattern_failures

UNION ALL

SELECT
  'email_generation_failures' AS bay,
  'COMPANY_HUB' AS node,
  'EmailGeneratorAgent' AS agent,
  COUNT(*) AS total_failures,
  COUNT(*) FILTER (WHERE repaired_at IS NULL) AS pending_repairs,
  MAX(created_at) AS last_failure
FROM marketing.email_generation_failures

UNION ALL

SELECT
  'linkedin_resolution_failures' AS bay,
  'PEOPLE_NODE' AS node,
  'LinkedInFinderAgent' AS agent,
  COUNT(*) AS total_failures,
  COUNT(*) FILTER (WHERE repaired_at IS NULL) AS pending_repairs,
  MAX(created_at) AS last_failure
FROM marketing.linkedin_resolution_failures

UNION ALL

SELECT
  'slot_discovery_failures' AS bay,
  'COMPANY_HUB' AS node,
  'MissingSlotAgent' AS agent,
  COUNT(*) AS total_failures,
  COUNT(*) FILTER (WHERE repaired_at IS NULL) AS pending_repairs,
  MAX(created_at) AS last_failure
FROM marketing.slot_discovery_failures

UNION ALL

SELECT
  'dol_sync_failures' AS bay,
  'DOL_NODE' AS node,
  'DOLSyncAgent' AS agent,
  COUNT(*) AS total_failures,
  COUNT(*) FILTER (WHERE repaired_at IS NULL) AS pending_repairs,
  MAX(created_at) AS last_failure
FROM marketing.dol_sync_failures

UNION ALL

SELECT
  'agent_failures' AS bay,
  node_id AS node,
  agent_type AS agent,
  COUNT(*) AS total_failures,
  COUNT(*) FILTER (WHERE repaired_at IS NULL) AS pending_repairs,
  MAX(created_at) AS last_failure
FROM marketing.agent_failures
GROUP BY node_id, agent_type;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE marketing.company_fuzzy_failures IS
  'Captures company fuzzy match failures for repair workflow';
COMMENT ON TABLE marketing.person_company_mismatch IS
  'Captures person-company employer mismatch failures';
COMMENT ON TABLE marketing.email_pattern_failures IS
  'Captures email pattern discovery failures';
COMMENT ON TABLE marketing.email_generation_failures IS
  'Captures email generation/verification failures';
COMMENT ON TABLE marketing.linkedin_resolution_failures IS
  'Captures LinkedIn URL resolution failures';
COMMENT ON TABLE marketing.slot_discovery_failures IS
  'Captures slot discovery failures';
COMMENT ON TABLE marketing.dol_sync_failures IS
  'Captures DOL data sync failures';
COMMENT ON TABLE marketing.agent_failures IS
  'Generic catch-all for unexpected agent failures';
COMMENT ON VIEW marketing.failure_summary IS
  'Aggregated failure counts across all bays';

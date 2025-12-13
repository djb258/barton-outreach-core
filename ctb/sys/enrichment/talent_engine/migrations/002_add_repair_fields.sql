-- ============================================================================
-- Talent Engine Failure Tables - Repair Fields Migration
-- ============================================================================
-- Adds repair/resume fields to all failure tables for the
-- failure → repair → resume execution loop
--
-- Schema: marketing
-- Purpose: Enable SELECT → FIX → REQUEUE → RESUME workflow
-- ============================================================================

-- 1. Company Fuzzy Match Failures
ALTER TABLE marketing.company_fuzzy_failures
ADD COLUMN IF NOT EXISTS resolved BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS resume_node TEXT DEFAULT 'COMPANY_HUB',
ADD COLUMN IF NOT EXISTS resume_agent TEXT DEFAULT 'CompanyFuzzyMatchAgent',
ADD COLUMN IF NOT EXISTS attempts INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_attempt_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS fixed_slot_row JSONB;

CREATE INDEX IF NOT EXISTS idx_company_fuzzy_failures_resolved
  ON marketing.company_fuzzy_failures(resolved) WHERE resolved = false;

-- 2. Person-Company Mismatch
ALTER TABLE marketing.person_company_mismatch
ADD COLUMN IF NOT EXISTS resolved BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS resume_node TEXT DEFAULT 'PEOPLE_NODE',
ADD COLUMN IF NOT EXISTS resume_agent TEXT DEFAULT 'PeopleFuzzyMatchAgent',
ADD COLUMN IF NOT EXISTS attempts INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_attempt_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS fixed_slot_row JSONB;

CREATE INDEX IF NOT EXISTS idx_person_company_mismatch_resolved
  ON marketing.person_company_mismatch(resolved) WHERE resolved = false;

-- 3. Email Pattern Failures
ALTER TABLE marketing.email_pattern_failures
ADD COLUMN IF NOT EXISTS resolved BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS resume_node TEXT DEFAULT 'COMPANY_HUB',
ADD COLUMN IF NOT EXISTS resume_agent TEXT DEFAULT 'PatternAgent',
ADD COLUMN IF NOT EXISTS attempts INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_attempt_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS fixed_slot_row JSONB;

CREATE INDEX IF NOT EXISTS idx_email_pattern_failures_resolved
  ON marketing.email_pattern_failures(resolved) WHERE resolved = false;

-- 4. Email Generation Failures
ALTER TABLE marketing.email_generation_failures
ADD COLUMN IF NOT EXISTS resolved BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS resume_node TEXT DEFAULT 'COMPANY_HUB',
ADD COLUMN IF NOT EXISTS resume_agent TEXT DEFAULT 'EmailGeneratorAgent',
ADD COLUMN IF NOT EXISTS attempts INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_attempt_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS fixed_slot_row JSONB;

CREATE INDEX IF NOT EXISTS idx_email_generation_failures_resolved
  ON marketing.email_generation_failures(resolved) WHERE resolved = false;

-- 5. LinkedIn Resolution Failures
ALTER TABLE marketing.linkedin_resolution_failures
ADD COLUMN IF NOT EXISTS resolved BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS resume_node TEXT DEFAULT 'PEOPLE_NODE',
ADD COLUMN IF NOT EXISTS resume_agent TEXT DEFAULT 'LinkedInFinderAgent',
ADD COLUMN IF NOT EXISTS attempts INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_attempt_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS fixed_slot_row JSONB;

CREATE INDEX IF NOT EXISTS idx_linkedin_resolution_failures_resolved
  ON marketing.linkedin_resolution_failures(resolved) WHERE resolved = false;

-- 6. Slot Discovery Failures
ALTER TABLE marketing.slot_discovery_failures
ADD COLUMN IF NOT EXISTS resolved BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS resume_node TEXT DEFAULT 'COMPANY_HUB',
ADD COLUMN IF NOT EXISTS resume_agent TEXT DEFAULT 'MissingSlotAgent',
ADD COLUMN IF NOT EXISTS attempts INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_attempt_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS fixed_slot_row JSONB;

CREATE INDEX IF NOT EXISTS idx_slot_discovery_failures_resolved
  ON marketing.slot_discovery_failures(resolved) WHERE resolved = false;

-- 7. DOL Sync Failures
ALTER TABLE marketing.dol_sync_failures
ADD COLUMN IF NOT EXISTS resolved BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS resume_node TEXT DEFAULT 'DOL_NODE',
ADD COLUMN IF NOT EXISTS resume_agent TEXT DEFAULT 'DOLSyncAgent',
ADD COLUMN IF NOT EXISTS attempts INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_attempt_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS fixed_slot_row JSONB;

CREATE INDEX IF NOT EXISTS idx_dol_sync_failures_resolved
  ON marketing.dol_sync_failures(resolved) WHERE resolved = false;

-- 8. Generic Agent Failures
ALTER TABLE marketing.agent_failures
ADD COLUMN IF NOT EXISTS resolved BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS resume_node TEXT,
ADD COLUMN IF NOT EXISTS resume_agent TEXT,
ADD COLUMN IF NOT EXISTS attempts INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_attempt_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS fixed_slot_row JSONB;

CREATE INDEX IF NOT EXISTS idx_agent_failures_resolved
  ON marketing.agent_failures(resolved) WHERE resolved = false;

-- ============================================================================
-- Updated Failure Summary View (includes repair stats)
-- ============================================================================

CREATE OR REPLACE VIEW marketing.failure_repair_summary AS
SELECT
  'company_fuzzy_failures' AS bay,
  'COMPANY_HUB' AS node,
  'CompanyFuzzyMatchAgent' AS agent,
  COUNT(*) AS total_failures,
  COUNT(*) FILTER (WHERE resolved = false) AS pending,
  COUNT(*) FILTER (WHERE resolved = true) AS resolved,
  SUM(attempts) AS total_attempts,
  MAX(last_attempt_at) AS last_attempt
FROM marketing.company_fuzzy_failures

UNION ALL

SELECT
  'person_company_mismatch' AS bay,
  'PEOPLE_NODE' AS node,
  'PeopleFuzzyMatchAgent' AS agent,
  COUNT(*) AS total_failures,
  COUNT(*) FILTER (WHERE resolved = false) AS pending,
  COUNT(*) FILTER (WHERE resolved = true) AS resolved,
  SUM(attempts) AS total_attempts,
  MAX(last_attempt_at) AS last_attempt
FROM marketing.person_company_mismatch

UNION ALL

SELECT
  'email_pattern_failures' AS bay,
  'COMPANY_HUB' AS node,
  'PatternAgent' AS agent,
  COUNT(*) AS total_failures,
  COUNT(*) FILTER (WHERE resolved = false) AS pending,
  COUNT(*) FILTER (WHERE resolved = true) AS resolved,
  SUM(attempts) AS total_attempts,
  MAX(last_attempt_at) AS last_attempt
FROM marketing.email_pattern_failures

UNION ALL

SELECT
  'email_generation_failures' AS bay,
  'COMPANY_HUB' AS node,
  'EmailGeneratorAgent' AS agent,
  COUNT(*) AS total_failures,
  COUNT(*) FILTER (WHERE resolved = false) AS pending,
  COUNT(*) FILTER (WHERE resolved = true) AS resolved,
  SUM(attempts) AS total_attempts,
  MAX(last_attempt_at) AS last_attempt
FROM marketing.email_generation_failures

UNION ALL

SELECT
  'linkedin_resolution_failures' AS bay,
  'PEOPLE_NODE' AS node,
  'LinkedInFinderAgent' AS agent,
  COUNT(*) AS total_failures,
  COUNT(*) FILTER (WHERE resolved = false) AS pending,
  COUNT(*) FILTER (WHERE resolved = true) AS resolved,
  SUM(attempts) AS total_attempts,
  MAX(last_attempt_at) AS last_attempt
FROM marketing.linkedin_resolution_failures

UNION ALL

SELECT
  'slot_discovery_failures' AS bay,
  'COMPANY_HUB' AS node,
  'MissingSlotAgent' AS agent,
  COUNT(*) AS total_failures,
  COUNT(*) FILTER (WHERE resolved = false) AS pending,
  COUNT(*) FILTER (WHERE resolved = true) AS resolved,
  SUM(attempts) AS total_attempts,
  MAX(last_attempt_at) AS last_attempt
FROM marketing.slot_discovery_failures

UNION ALL

SELECT
  'dol_sync_failures' AS bay,
  'DOL_NODE' AS node,
  'DOLSyncAgent' AS agent,
  COUNT(*) AS total_failures,
  COUNT(*) FILTER (WHERE resolved = false) AS pending,
  COUNT(*) FILTER (WHERE resolved = true) AS resolved,
  SUM(attempts) AS total_attempts,
  MAX(last_attempt_at) AS last_attempt
FROM marketing.dol_sync_failures

UNION ALL

SELECT
  'agent_failures' AS bay,
  COALESCE(node_id, 'UNKNOWN') AS node,
  COALESCE(agent_type, 'Unknown') AS agent,
  COUNT(*) AS total_failures,
  COUNT(*) FILTER (WHERE resolved = false) AS pending,
  COUNT(*) FILTER (WHERE resolved = true) AS resolved,
  SUM(attempts) AS total_attempts,
  MAX(last_attempt_at) AS last_attempt
FROM marketing.agent_failures
GROUP BY node_id, agent_type;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON COLUMN marketing.company_fuzzy_failures.resolved IS
  'Whether this failure has been resolved via repair workflow';
COMMENT ON COLUMN marketing.company_fuzzy_failures.resolved_at IS
  'Timestamp when failure was resolved';
COMMENT ON COLUMN marketing.company_fuzzy_failures.resume_node IS
  'Node to resume execution from after repair';
COMMENT ON COLUMN marketing.company_fuzzy_failures.resume_agent IS
  'Agent to resume execution from within the node';
COMMENT ON COLUMN marketing.company_fuzzy_failures.attempts IS
  'Number of retry attempts made';
COMMENT ON COLUMN marketing.company_fuzzy_failures.fixed_slot_row IS
  'Fixed/updated slot row data for re-processing';

COMMENT ON VIEW marketing.failure_repair_summary IS
  'Aggregated failure and repair statistics across all bays';

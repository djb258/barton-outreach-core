-- ═══════════════════════════════════════════════════════════════════════════
-- Migration: Company Target EIN Error Routing for Enrichment
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Version: 1.0.0
-- Date: 2025-01-01
-- Doctrine: /doctrine/ple/COMPANY_TARGET_IDENTITY.md
--
-- Purpose:
--   Create indexes and views for Company Target EIN resolution failures
--   that require ENRICHMENT remediation before DOL execution.
--
-- CANONICAL RULE:
--   If Company Target cannot fuzzy-resolve an EIN:
--   - Record MUST NOT proceed to DOL
--   - MUST be written to shq.error_master for enrichment remediation
--   - This is a PRE-DOL failure, not a DOL error
--
-- ═══════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════
-- INDEX: Company Target EIN_NOT_RESOLVED errors
-- ═══════════════════════════════════════════════════════════════════════════

-- Index for querying Company Target failures by process ID
CREATE INDEX IF NOT EXISTS idx_error_master_company_target
ON shq.error_master (process_id, created_at DESC)
WHERE process_id = '01.04.02.04.21000';

-- Index for querying by agent name
CREATE INDEX IF NOT EXISTS idx_error_master_company_target_agent
ON shq.error_master (agent_name, created_at DESC)
WHERE agent_name = 'COMPANY_TARGET';

-- Index for querying EIN_NOT_RESOLVED errors specifically
CREATE INDEX IF NOT EXISTS idx_error_master_ein_not_resolved
ON shq.error_master (error_type, created_at DESC)
WHERE error_type = 'EIN_NOT_RESOLVED';

-- Index for querying errors requiring ENRICHMENT remediation
CREATE INDEX IF NOT EXISTS idx_error_master_enrichment_remediation
ON shq.error_master (created_at DESC)
WHERE context::jsonb->>'remediation_required' = 'ENRICHMENT';

-- ═══════════════════════════════════════════════════════════════════════════
-- VIEW: Pending Enrichment Queue
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Purpose:
--   Provides a queue of records that failed EIN resolution and need
--   enrichment before DOL can proceed.
--
-- Consumers:
--   - Enrichment tools
--   - Operations dashboard
--   - Remediation workflows

CREATE OR REPLACE VIEW shq.v_pending_enrichment_queue AS
SELECT
    error_id,
    occurred_at,
    process_id,
    agent_name,
    error_type,
    message,
    context::jsonb->>'company_unique_id' AS company_unique_id,
    context::jsonb->>'outreach_context_id' AS outreach_context_id,
    context::jsonb->'payload'->>'company_name' AS company_name,
    context::jsonb->'payload'->>'company_domain' AS company_domain,
    context::jsonb->'payload'->>'linkedin_company_url' AS linkedin_company_url,
    context::jsonb->'payload'->>'state' AS state,
    context::jsonb->'payload'->>'fuzzy_method' AS fuzzy_method,
    context::jsonb->'payload'->>'threshold_used' AS threshold_used,
    context::jsonb->'payload'->'fuzzy_candidates' AS fuzzy_candidates,
    context::jsonb->>'air_event_id' AS air_event_id,
    context::jsonb->>'remediation_required' AS remediation_required,
    created_at
FROM shq.error_master
WHERE error_type = 'EIN_NOT_RESOLVED'
  AND (resolved IS NULL OR resolved = FALSE)
ORDER BY occurred_at DESC;

COMMENT ON VIEW shq.v_pending_enrichment_queue IS 
'Queue of records that failed EIN resolution in Company Target and require enrichment before DOL execution. Doctrine: Company Target must resolve EIN; DOL never sees fuzzy logic.';

-- ═══════════════════════════════════════════════════════════════════════════
-- VIEW: Company Target to DOL Handoff Status
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Purpose:
--   Shows the execution flow from Company Target to DOL,
--   highlighting blocked records.

CREATE OR REPLACE VIEW shq.v_company_target_dol_handoff AS
SELECT
    company_unique_id,
    CASE
        WHEN ein_error.error_id IS NOT NULL THEN 'BLOCKED_EIN_NOT_RESOLVED'
        WHEN target_error.error_id IS NOT NULL THEN 'BLOCKED_COMPANY_TARGET_FAIL'
        ELSE 'READY_FOR_DOL'
    END AS handoff_status,
    ein_error.error_id AS ein_error_id,
    ein_error.occurred_at AS ein_error_at,
    target_error.error_id AS target_error_id,
    target_error.occurred_at AS target_error_at
FROM (
    SELECT DISTINCT context::jsonb->>'company_unique_id' AS company_unique_id
    FROM shq.error_master
    WHERE process_id IN ('01.04.02.04.21000', '01.04.02.04.22000')
) companies
LEFT JOIN LATERAL (
    SELECT error_id, occurred_at
    FROM shq.error_master
    WHERE context::jsonb->>'company_unique_id' = companies.company_unique_id
      AND error_type = 'EIN_NOT_RESOLVED'
      AND (resolved IS NULL OR resolved = FALSE)
    ORDER BY occurred_at DESC
    LIMIT 1
) ein_error ON TRUE
LEFT JOIN LATERAL (
    SELECT error_id, occurred_at
    FROM shq.error_master
    WHERE context::jsonb->>'company_unique_id' = companies.company_unique_id
      AND process_id = '01.04.02.04.21000'
      AND error_type != 'EIN_NOT_RESOLVED'
      AND (resolved IS NULL OR resolved = FALSE)
    ORDER BY occurred_at DESC
    LIMIT 1
) target_error ON TRUE;

COMMENT ON VIEW shq.v_company_target_dol_handoff IS 
'Shows handoff status from Company Target to DOL. Records with EIN_NOT_RESOLVED are blocked until enrichment resolves the EIN.';

-- ═══════════════════════════════════════════════════════════════════════════
-- GRANT: Read access for enrichment tools
-- ═══════════════════════════════════════════════════════════════════════════

-- (Uncomment and adjust as needed for your database user setup)
-- GRANT SELECT ON shq.v_pending_enrichment_queue TO enrichment_service;
-- GRANT SELECT ON shq.v_company_target_dol_handoff TO enrichment_service;

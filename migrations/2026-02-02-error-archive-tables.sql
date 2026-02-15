-- =============================================================================
-- ERROR ARCHIVE TABLES MIGRATION
-- =============================================================================
--
-- PURPOSE:
--   Create archive tables for error records that have exceeded their TTL
--   or have been manually archived
--
-- ARCHIVE TABLES CREATED:
--   - outreach.dol_errors_archive
--   - outreach.company_target_errors_archive
--   - people.people_errors_archive
--   - company.url_discovery_failures_archive
--   - shq.error_master_archive
--
-- RETENTION:
--   - Hub-owned archives: 1 year
--   - Global archives: 2 years
--
-- AUTHORITY: ERROR_TTL_PARKING_POLICY.md v1.0.0
-- =============================================================================

-- =============================================================================
-- STEP 1: Create archive table for outreach.dol_errors
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach.dol_errors_archive (
    -- Original columns (copy from dol_errors)
    error_id UUID PRIMARY KEY,
    outreach_id UUID,
    pipeline_stage VARCHAR(50),
    failure_code VARCHAR(50),
    blocking_reason TEXT,
    severity VARCHAR(20),
    retry_allowed BOOLEAN,
    raw_input JSONB,
    stack_trace TEXT,
    created_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    resolution_note TEXT,

    -- Governance columns
    disposition error_disposition,
    retry_count INTEGER,
    max_retries INTEGER,
    parked_at TIMESTAMPTZ,
    parked_by TEXT,
    park_reason TEXT,
    escalation_level INTEGER,
    escalated_at TIMESTAMPTZ,
    ttl_tier ttl_tier,
    last_retry_at TIMESTAMPTZ,
    retry_exhausted BOOLEAN,

    -- Archive metadata
    archived_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_by TEXT DEFAULT 'system',
    archive_reason TEXT DEFAULT 'TTL_EXPIRED',
    final_disposition error_disposition,

    -- Archive retention (will be cleaned after this date)
    retention_expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '1 year')
);

CREATE INDEX IF NOT EXISTS idx_dol_errors_archive_outreach_id ON outreach.dol_errors_archive (outreach_id);
CREATE INDEX IF NOT EXISTS idx_dol_errors_archive_archived_at ON outreach.dol_errors_archive (archived_at);
CREATE INDEX IF NOT EXISTS idx_dol_errors_archive_retention ON outreach.dol_errors_archive (retention_expires_at);

-- =============================================================================
-- STEP 2: Create archive table for outreach.company_target_errors
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach.company_target_errors_archive (
    -- Original columns (copy from company_target_errors)
    error_id UUID PRIMARY KEY,
    outreach_id UUID,
    pipeline_stage VARCHAR(50),
    imo_stage VARCHAR(50),
    failure_code VARCHAR(50),
    blocking_reason TEXT,
    severity VARCHAR(20),
    retry_allowed BOOLEAN,
    raw_input JSONB,
    stack_trace TEXT,
    created_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    resolution_note TEXT,

    -- Governance columns
    disposition error_disposition,
    retry_count INTEGER,
    max_retries INTEGER,
    parked_at TIMESTAMPTZ,
    parked_by TEXT,
    park_reason TEXT,
    escalation_level INTEGER,
    escalated_at TIMESTAMPTZ,
    ttl_tier ttl_tier,
    last_retry_at TIMESTAMPTZ,
    retry_exhausted BOOLEAN,

    -- Archive metadata
    archived_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_by TEXT DEFAULT 'system',
    archive_reason TEXT DEFAULT 'TTL_EXPIRED',
    final_disposition error_disposition,
    retention_expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '1 year')
);

CREATE INDEX IF NOT EXISTS idx_company_target_errors_archive_outreach_id ON outreach.company_target_errors_archive (outreach_id);
CREATE INDEX IF NOT EXISTS idx_company_target_errors_archive_archived_at ON outreach.company_target_errors_archive (archived_at);
CREATE INDEX IF NOT EXISTS idx_company_target_errors_archive_retention ON outreach.company_target_errors_archive (retention_expires_at);

-- =============================================================================
-- STEP 3: Create archive table for people.people_errors
-- =============================================================================

CREATE TABLE IF NOT EXISTS people.people_errors_archive (
    -- Original columns (copy from people_errors)
    error_id UUID PRIMARY KEY,
    outreach_id UUID,
    person_id UUID,
    slot_id UUID,
    error_stage VARCHAR(50),
    error_type VARCHAR(50),
    error_code VARCHAR(50),
    error_message TEXT,
    raw_payload JSONB,
    retry_strategy VARCHAR(50),
    source_hints_used JSONB,
    status VARCHAR(20),
    created_at TIMESTAMPTZ,
    last_updated_at TIMESTAMPTZ,

    -- Governance columns
    disposition error_disposition,
    retry_count INTEGER,
    max_retries INTEGER,
    parked_at TIMESTAMPTZ,
    parked_by TEXT,
    park_reason TEXT,
    escalation_level INTEGER,
    escalated_at TIMESTAMPTZ,
    ttl_tier ttl_tier,
    last_retry_at TIMESTAMPTZ,
    retry_exhausted BOOLEAN,

    -- Archive metadata
    archived_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_by TEXT DEFAULT 'system',
    archive_reason TEXT DEFAULT 'TTL_EXPIRED',
    final_disposition error_disposition,
    retention_expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '1 year')
);

CREATE INDEX IF NOT EXISTS idx_people_errors_archive_outreach_id ON people.people_errors_archive (outreach_id);
CREATE INDEX IF NOT EXISTS idx_people_errors_archive_archived_at ON people.people_errors_archive (archived_at);
CREATE INDEX IF NOT EXISTS idx_people_errors_archive_retention ON people.people_errors_archive (retention_expires_at);

-- =============================================================================
-- STEP 4: Create archive table for company.url_discovery_failures
-- =============================================================================

CREATE TABLE IF NOT EXISTS company.url_discovery_failures_archive (
    -- Original columns
    failure_id UUID PRIMARY KEY,
    company_unique_id UUID,
    domain VARCHAR(255),
    failure_reason VARCHAR(50),
    created_at TIMESTAMPTZ,

    -- Governance columns
    disposition error_disposition,
    retry_count INTEGER,
    max_retries INTEGER,
    parked_at TIMESTAMPTZ,
    parked_by TEXT,
    park_reason TEXT,
    escalation_level INTEGER,
    escalated_at TIMESTAMPTZ,
    ttl_tier ttl_tier,
    last_retry_at TIMESTAMPTZ,
    retry_exhausted BOOLEAN,

    -- Archive metadata
    archived_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_by TEXT DEFAULT 'system',
    archive_reason TEXT DEFAULT 'TTL_EXPIRED',
    final_disposition error_disposition,
    retention_expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '1 year')
);

CREATE INDEX IF NOT EXISTS idx_url_discovery_failures_archive_company_id ON company.url_discovery_failures_archive (company_unique_id);
CREATE INDEX IF NOT EXISTS idx_url_discovery_failures_archive_archived_at ON company.url_discovery_failures_archive (archived_at);
CREATE INDEX IF NOT EXISTS idx_url_discovery_failures_archive_retention ON company.url_discovery_failures_archive (retention_expires_at);

-- =============================================================================
-- STEP 5: Create archive table for shq.error_master
-- =============================================================================

CREATE TABLE IF NOT EXISTS shq.error_master_archive (
    -- Original columns (based on existing shq_error_log structure)
    id SERIAL,
    error_id UUID PRIMARY KEY,
    process_id TEXT,
    agent_id TEXT,
    severity TEXT,
    error_type TEXT,
    message TEXT,
    company_unique_id TEXT,
    outreach_context_id TEXT,
    air_event_id TEXT,
    context JSONB,
    created_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    resolution_type TEXT,

    -- Governance columns
    disposition error_disposition,
    ttl_tier ttl_tier,

    -- Archive metadata
    archived_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_by TEXT DEFAULT 'system',
    archive_reason TEXT DEFAULT 'TTL_EXPIRED',
    final_disposition error_disposition,
    retention_expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '2 years')  -- Global: 2 year retention
);

CREATE INDEX IF NOT EXISTS idx_shq_error_log_archive_process_id ON shq.error_master_archive (process_id);
CREATE INDEX IF NOT EXISTS idx_shq_error_log_archive_archived_at ON shq.error_master_archive (archived_at);
CREATE INDEX IF NOT EXISTS idx_shq_error_log_archive_retention ON shq.error_master_archive (retention_expires_at);

-- =============================================================================
-- STEP 6: Comments
-- =============================================================================

COMMENT ON TABLE outreach.dol_errors_archive IS 'Archive for DOL errors that have exceeded TTL. Retention: 1 year.';
COMMENT ON TABLE outreach.company_target_errors_archive IS 'Archive for Company Target errors that have exceeded TTL. Retention: 1 year.';
COMMENT ON TABLE people.people_errors_archive IS 'Archive for People errors that have exceeded TTL. Retention: 1 year.';
COMMENT ON TABLE company.url_discovery_failures_archive IS 'Archive for URL discovery failures that have exceeded TTL. Retention: 1 year.';
COMMENT ON TABLE shq.error_master_archive IS 'Archive for global error log. Retention: 2 years.';

COMMENT ON COLUMN outreach.dol_errors_archive.archive_reason IS 'Why the error was archived: TTL_EXPIRED, MANUAL, RESOLVED, SUPERSEDED';
COMMENT ON COLUMN outreach.dol_errors_archive.final_disposition IS 'Disposition at time of archive';
COMMENT ON COLUMN outreach.dol_errors_archive.retention_expires_at IS 'When this archive record can be permanently deleted';

-- =============================================================================
-- USAGE NOTES
-- =============================================================================
--
-- Archive tables store:
--   1. All original error data
--   2. Governance state at time of archive
--   3. Archive metadata (when, why, by whom)
--   4. Retention expiration date
--
-- Archive cleanup job should delete records where retention_expires_at < NOW()
--
-- =============================================================================

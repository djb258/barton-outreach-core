-- Fix url_discovery_failures archive table and function
-- Run with: doppler run -- psql $DATABASE_URL -f scripts/fix_url_discovery_schema.sql

-- Fix archive table - add website_url column, drop domain if exists
ALTER TABLE company.url_discovery_failures_archive
ADD COLUMN IF NOT EXISTS website_url TEXT;

ALTER TABLE company.url_discovery_failures_archive
DROP COLUMN IF EXISTS domain;

-- Recreate the archive function with correct column (website_url instead of domain)
CREATE OR REPLACE FUNCTION shq.fn_archive_expired_errors()
RETURNS TABLE (
    source_table TEXT,
    archived_count INTEGER
) AS $$
DECLARE
    v_count INTEGER;
BEGIN
    -- Archive DOL errors
    WITH to_archive AS (
        SELECT error_id
        FROM outreach.dol_errors
        WHERE archived_at IS NULL
          AND ttl_tier != 'INFINITE'
          AND NOW() > created_at + shq.fn_get_ttl_interval(ttl_tier)
    ),
    archived AS (
        INSERT INTO outreach.dol_errors_archive (
            error_id, outreach_id, pipeline_stage, failure_code, blocking_reason,
            severity, retry_allowed, raw_input, stack_trace, created_at,
            resolved_at, resolution_note, disposition, retry_count, max_retries,
            parked_at, parked_by, park_reason, escalation_level, escalated_at,
            ttl_tier, last_retry_at, retry_exhausted,
            archived_at, archived_by, archive_reason, final_disposition
        )
        SELECT
            e.error_id, e.outreach_id, e.pipeline_stage, e.failure_code, e.blocking_reason,
            e.severity, e.retry_allowed, e.raw_input, e.stack_trace, e.created_at,
            e.resolved_at, e.resolution_note, e.disposition, e.retry_count, e.max_retries,
            e.parked_at, e.parked_by, e.park_reason, e.escalation_level, e.escalated_at,
            e.ttl_tier, e.last_retry_at, e.retry_exhausted,
            NOW(), 'ttl_archive_job', 'TTL_EXPIRED', e.disposition
        FROM outreach.dol_errors e
        WHERE e.error_id IN (SELECT error_id FROM to_archive)
        ON CONFLICT (error_id) DO NOTHING
        RETURNING error_id
    ),
    deleted AS (
        DELETE FROM outreach.dol_errors
        WHERE error_id IN (SELECT error_id FROM archived)
        RETURNING error_id
    )
    SELECT COUNT(*) INTO v_count FROM deleted;

    source_table := 'outreach.dol_errors';
    archived_count := v_count;
    RETURN NEXT;

    -- Archive Company Target errors
    WITH to_archive AS (
        SELECT error_id
        FROM outreach.company_target_errors
        WHERE archived_at IS NULL
          AND ttl_tier != 'INFINITE'
          AND NOW() > created_at + shq.fn_get_ttl_interval(ttl_tier)
    ),
    archived AS (
        INSERT INTO outreach.company_target_errors_archive (
            error_id, outreach_id, pipeline_stage, imo_stage, failure_code, blocking_reason,
            severity, retry_allowed, raw_input, stack_trace, created_at,
            resolved_at, resolution_note, disposition, retry_count, max_retries,
            parked_at, parked_by, park_reason, escalation_level, escalated_at,
            ttl_tier, last_retry_at, retry_exhausted,
            archived_at, archived_by, archive_reason, final_disposition
        )
        SELECT
            e.error_id, e.outreach_id, e.pipeline_stage, e.imo_stage, e.failure_code, e.blocking_reason,
            e.severity, e.retry_allowed, e.raw_input, e.stack_trace, e.created_at,
            e.resolved_at, e.resolution_note, e.disposition, e.retry_count, e.max_retries,
            e.parked_at, e.parked_by, e.park_reason, e.escalation_level, e.escalated_at,
            e.ttl_tier, e.last_retry_at, e.retry_exhausted,
            NOW(), 'ttl_archive_job', 'TTL_EXPIRED', e.disposition
        FROM outreach.company_target_errors e
        WHERE e.error_id IN (SELECT error_id FROM to_archive)
        ON CONFLICT (error_id) DO NOTHING
        RETURNING error_id
    ),
    deleted AS (
        DELETE FROM outreach.company_target_errors
        WHERE error_id IN (SELECT error_id FROM archived)
        RETURNING error_id
    )
    SELECT COUNT(*) INTO v_count FROM deleted;

    source_table := 'outreach.company_target_errors';
    archived_count := v_count;
    RETURN NEXT;

    -- Archive People errors
    WITH to_archive AS (
        SELECT error_id
        FROM people.people_errors
        WHERE archived_at IS NULL
          AND ttl_tier != 'INFINITE'
          AND NOW() > created_at + shq.fn_get_ttl_interval(ttl_tier)
    ),
    archived AS (
        INSERT INTO people.people_errors_archive (
            error_id, outreach_id, person_id, slot_id, error_stage, error_type,
            error_code, error_message, raw_payload, retry_strategy, source_hints_used,
            status, created_at, last_updated_at, disposition, retry_count, max_retries,
            parked_at, parked_by, park_reason, escalation_level, escalated_at,
            ttl_tier, last_retry_at, retry_exhausted,
            archived_at, archived_by, archive_reason, final_disposition
        )
        SELECT
            e.error_id, e.outreach_id, e.person_id, e.slot_id, e.error_stage, e.error_type,
            e.error_code, e.error_message, e.raw_payload, e.retry_strategy, e.source_hints_used,
            e.status, e.created_at, e.last_updated_at, e.disposition, e.retry_count, e.max_retries,
            e.parked_at, e.parked_by, e.park_reason, e.escalation_level, e.escalated_at,
            e.ttl_tier, e.last_retry_at, e.retry_exhausted,
            NOW(), 'ttl_archive_job', 'TTL_EXPIRED', e.disposition
        FROM people.people_errors e
        WHERE e.error_id IN (SELECT error_id FROM to_archive)
        ON CONFLICT (error_id) DO NOTHING
        RETURNING error_id
    ),
    deleted AS (
        DELETE FROM people.people_errors
        WHERE error_id IN (SELECT error_id FROM archived)
        RETURNING error_id
    )
    SELECT COUNT(*) INTO v_count FROM deleted;

    source_table := 'people.people_errors';
    archived_count := v_count;
    RETURN NEXT;

    -- Archive URL discovery failures (FIXED: website_url)
    WITH to_archive AS (
        SELECT failure_id
        FROM company.url_discovery_failures
        WHERE archived_at IS NULL
          AND ttl_tier != 'INFINITE'
          AND NOW() > created_at + shq.fn_get_ttl_interval(ttl_tier)
    ),
    archived AS (
        INSERT INTO company.url_discovery_failures_archive (
            failure_id, company_unique_id, website_url, failure_reason, created_at,
            disposition, retry_count, max_retries,
            parked_at, parked_by, park_reason, escalation_level, escalated_at,
            ttl_tier, last_retry_at, retry_exhausted,
            archived_at, archived_by, archive_reason, final_disposition
        )
        SELECT
            e.failure_id, e.company_unique_id, e.website_url, e.failure_reason, e.created_at,
            e.disposition, e.retry_count, e.max_retries,
            e.parked_at, e.parked_by, e.park_reason, e.escalation_level, e.escalated_at,
            e.ttl_tier, e.last_retry_at, e.retry_exhausted,
            NOW(), 'ttl_archive_job', 'TTL_EXPIRED', e.disposition
        FROM company.url_discovery_failures e
        WHERE e.failure_id IN (SELECT failure_id FROM to_archive)
        ON CONFLICT (failure_id) DO NOTHING
        RETURNING failure_id
    ),
    deleted AS (
        DELETE FROM company.url_discovery_failures
        WHERE failure_id IN (SELECT failure_id FROM archived)
        RETURNING failure_id
    )
    SELECT COUNT(*) INTO v_count FROM deleted;

    source_table := 'company.url_discovery_failures';
    archived_count := v_count;
    RETURN NEXT;

    RETURN;
END;
$$ LANGUAGE plpgsql;

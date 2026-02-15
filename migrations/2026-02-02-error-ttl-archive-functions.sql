-- =============================================================================
-- ERROR TTL + ARCHIVE FUNCTIONS
-- =============================================================================
--
-- PURPOSE:
--   Functions for TTL-based archival of errors and automatic parking
--   when retry limits are exceeded
--
-- FUNCTIONS CREATED:
--   - shq.fn_get_ttl_interval(ttl_tier) -> INTERVAL
--   - shq.fn_archive_expired_errors() -> TABLE (for scheduled job)
--   - shq.fn_auto_park_exhausted_retries() -> TABLE (for scheduled job)
--   - shq.fn_escalate_stale_parked_errors() -> TABLE (for scheduled job)
--   - shq.fn_cleanup_expired_archives() -> TABLE (for scheduled job)
--
-- AUTHORITY: ERROR_TTL_PARKING_POLICY.md v1.0.0
-- =============================================================================

-- =============================================================================
-- HELPER: Convert TTL tier to interval
-- =============================================================================

CREATE OR REPLACE FUNCTION shq.fn_get_ttl_interval(p_ttl_tier ttl_tier)
RETURNS INTERVAL AS $$
BEGIN
    RETURN CASE p_ttl_tier
        WHEN 'SHORT' THEN INTERVAL '7 days'
        WHEN 'MEDIUM' THEN INTERVAL '30 days'
        WHEN 'LONG' THEN INTERVAL '90 days'
        WHEN 'INFINITE' THEN INTERVAL '100 years'  -- Effectively infinite
        ELSE INTERVAL '30 days'  -- Default to MEDIUM
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION shq.fn_get_ttl_interval IS 'Converts TTL tier to actual interval. SHORT=7d, MEDIUM=30d, LONG=90d, INFINITE=100y';

-- =============================================================================
-- MAIN: Archive expired errors
-- =============================================================================

CREATE OR REPLACE FUNCTION shq.fn_archive_expired_errors()
RETURNS TABLE (
    source_table TEXT,
    archived_count INTEGER
) AS $$
DECLARE
    v_count INTEGER;
BEGIN
    -- ==========================================================================
    -- Archive DOL errors that have exceeded TTL
    -- ==========================================================================
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

    -- ==========================================================================
    -- Archive Company Target errors that have exceeded TTL
    -- ==========================================================================
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

    -- ==========================================================================
    -- Archive People errors that have exceeded TTL
    -- ==========================================================================
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

    -- ==========================================================================
    -- Archive URL discovery failures that have exceeded TTL
    -- ==========================================================================
    WITH to_archive AS (
        SELECT failure_id
        FROM company.url_discovery_failures
        WHERE archived_at IS NULL
          AND ttl_tier != 'INFINITE'
          AND NOW() > created_at + shq.fn_get_ttl_interval(ttl_tier)
    ),
    archived AS (
        INSERT INTO company.url_discovery_failures_archive (
            failure_id, company_unique_id, domain, failure_reason, created_at,
            disposition, retry_count, max_retries,
            parked_at, parked_by, park_reason, escalation_level, escalated_at,
            ttl_tier, last_retry_at, retry_exhausted,
            archived_at, archived_by, archive_reason, final_disposition
        )
        SELECT
            e.failure_id, e.company_unique_id, e.domain, e.failure_reason, e.created_at,
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

COMMENT ON FUNCTION shq.fn_archive_expired_errors IS 'Archives errors that have exceeded their TTL. Run daily via scheduled job.';

-- =============================================================================
-- AUTO-PARK: Park errors that have exhausted retries
-- =============================================================================

CREATE OR REPLACE FUNCTION shq.fn_auto_park_exhausted_retries()
RETURNS TABLE (
    source_table TEXT,
    parked_count INTEGER
) AS $$
DECLARE
    v_count INTEGER;
BEGIN
    -- DOL errors
    UPDATE outreach.dol_errors
    SET disposition = 'PARKED',
        parked_at = NOW(),
        parked_by = 'system',
        park_reason = 'MAX_RETRIES_EXCEEDED',
        retry_exhausted = TRUE
    WHERE disposition = 'RETRY'
      AND retry_count >= max_retries
      AND parked_at IS NULL;

    GET DIAGNOSTICS v_count = ROW_COUNT;
    source_table := 'outreach.dol_errors';
    parked_count := v_count;
    RETURN NEXT;

    -- Company Target errors
    UPDATE outreach.company_target_errors
    SET disposition = 'PARKED',
        parked_at = NOW(),
        parked_by = 'system',
        park_reason = 'MAX_RETRIES_EXCEEDED',
        retry_exhausted = TRUE
    WHERE disposition = 'RETRY'
      AND retry_count >= max_retries
      AND parked_at IS NULL;

    GET DIAGNOSTICS v_count = ROW_COUNT;
    source_table := 'outreach.company_target_errors';
    parked_count := v_count;
    RETURN NEXT;

    -- People errors
    UPDATE people.people_errors
    SET disposition = 'PARKED',
        parked_at = NOW(),
        parked_by = 'system',
        park_reason = 'MAX_RETRIES_EXCEEDED',
        retry_exhausted = TRUE
    WHERE disposition = 'RETRY'
      AND retry_count >= max_retries
      AND parked_at IS NULL;

    GET DIAGNOSTICS v_count = ROW_COUNT;
    source_table := 'people.people_errors';
    parked_count := v_count;
    RETURN NEXT;

    RETURN;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION shq.fn_auto_park_exhausted_retries IS 'Parks errors that have exceeded max retries. Run after each retry batch.';

-- =============================================================================
-- ESCALATION: Escalate stale parked errors
-- =============================================================================

CREATE OR REPLACE FUNCTION shq.fn_escalate_stale_parked_errors()
RETURNS TABLE (
    source_table TEXT,
    tier_1_escalated INTEGER,
    tier_2_escalated INTEGER,
    tier_3_escalated INTEGER
) AS $$
DECLARE
    v_tier1 INTEGER;
    v_tier2 INTEGER;
    v_tier3 INTEGER;
BEGIN
    -- ==========================================================================
    -- DOL Errors Escalation
    -- ==========================================================================

    -- Tier 1: Parked > 24 hours, escalation_level = 0
    UPDATE outreach.dol_errors
    SET escalation_level = 1,
        escalated_at = NOW()
    WHERE disposition = 'PARKED'
      AND escalation_level = 0
      AND parked_at < NOW() - INTERVAL '24 hours';
    GET DIAGNOSTICS v_tier1 = ROW_COUNT;

    -- Tier 2: Parked > 48 hours, escalation_level = 1
    UPDATE outreach.dol_errors
    SET escalation_level = 2,
        escalated_at = NOW()
    WHERE disposition = 'PARKED'
      AND escalation_level = 1
      AND parked_at < NOW() - INTERVAL '48 hours';
    GET DIAGNOSTICS v_tier2 = ROW_COUNT;

    -- Tier 3: Parked > 7 days, escalation_level = 2
    UPDATE outreach.dol_errors
    SET escalation_level = 3,
        escalated_at = NOW()
    WHERE disposition = 'PARKED'
      AND escalation_level = 2
      AND parked_at < NOW() - INTERVAL '7 days';
    GET DIAGNOSTICS v_tier3 = ROW_COUNT;

    source_table := 'outreach.dol_errors';
    tier_1_escalated := v_tier1;
    tier_2_escalated := v_tier2;
    tier_3_escalated := v_tier3;
    RETURN NEXT;

    -- ==========================================================================
    -- Company Target Errors Escalation
    -- ==========================================================================

    UPDATE outreach.company_target_errors
    SET escalation_level = 1, escalated_at = NOW()
    WHERE disposition = 'PARKED' AND escalation_level = 0 AND parked_at < NOW() - INTERVAL '24 hours';
    GET DIAGNOSTICS v_tier1 = ROW_COUNT;

    UPDATE outreach.company_target_errors
    SET escalation_level = 2, escalated_at = NOW()
    WHERE disposition = 'PARKED' AND escalation_level = 1 AND parked_at < NOW() - INTERVAL '48 hours';
    GET DIAGNOSTICS v_tier2 = ROW_COUNT;

    UPDATE outreach.company_target_errors
    SET escalation_level = 3, escalated_at = NOW()
    WHERE disposition = 'PARKED' AND escalation_level = 2 AND parked_at < NOW() - INTERVAL '7 days';
    GET DIAGNOSTICS v_tier3 = ROW_COUNT;

    source_table := 'outreach.company_target_errors';
    tier_1_escalated := v_tier1;
    tier_2_escalated := v_tier2;
    tier_3_escalated := v_tier3;
    RETURN NEXT;

    -- ==========================================================================
    -- People Errors Escalation
    -- ==========================================================================

    UPDATE people.people_errors
    SET escalation_level = 1, escalated_at = NOW()
    WHERE disposition = 'PARKED' AND escalation_level = 0 AND parked_at < NOW() - INTERVAL '24 hours';
    GET DIAGNOSTICS v_tier1 = ROW_COUNT;

    UPDATE people.people_errors
    SET escalation_level = 2, escalated_at = NOW()
    WHERE disposition = 'PARKED' AND escalation_level = 1 AND parked_at < NOW() - INTERVAL '48 hours';
    GET DIAGNOSTICS v_tier2 = ROW_COUNT;

    UPDATE people.people_errors
    SET escalation_level = 3, escalated_at = NOW()
    WHERE disposition = 'PARKED' AND escalation_level = 2 AND parked_at < NOW() - INTERVAL '7 days';
    GET DIAGNOSTICS v_tier3 = ROW_COUNT;

    source_table := 'people.people_errors';
    tier_1_escalated := v_tier1;
    tier_2_escalated := v_tier2;
    tier_3_escalated := v_tier3;
    RETURN NEXT;

    RETURN;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION shq.fn_escalate_stale_parked_errors IS 'Escalates parked errors based on time thresholds. Run daily.';

-- =============================================================================
-- CLEANUP: Delete expired archive records
-- =============================================================================

CREATE OR REPLACE FUNCTION shq.fn_cleanup_expired_archives()
RETURNS TABLE (
    archive_table TEXT,
    deleted_count INTEGER
) AS $$
DECLARE
    v_count INTEGER;
BEGIN
    -- DOL errors archive
    DELETE FROM outreach.dol_errors_archive
    WHERE retention_expires_at < NOW();
    GET DIAGNOSTICS v_count = ROW_COUNT;
    archive_table := 'outreach.dol_errors_archive';
    deleted_count := v_count;
    RETURN NEXT;

    -- Company Target errors archive
    DELETE FROM outreach.company_target_errors_archive
    WHERE retention_expires_at < NOW();
    GET DIAGNOSTICS v_count = ROW_COUNT;
    archive_table := 'outreach.company_target_errors_archive';
    deleted_count := v_count;
    RETURN NEXT;

    -- People errors archive
    DELETE FROM people.people_errors_archive
    WHERE retention_expires_at < NOW();
    GET DIAGNOSTICS v_count = ROW_COUNT;
    archive_table := 'people.people_errors_archive';
    deleted_count := v_count;
    RETURN NEXT;

    -- URL discovery failures archive
    DELETE FROM company.url_discovery_failures_archive
    WHERE retention_expires_at < NOW();
    GET DIAGNOSTICS v_count = ROW_COUNT;
    archive_table := 'company.url_discovery_failures_archive';
    deleted_count := v_count;
    RETURN NEXT;

    -- SHQ error log archive
    DELETE FROM public.shq_error_log_archive
    WHERE retention_expires_at < NOW();
    GET DIAGNOSTICS v_count = ROW_COUNT;
    archive_table := 'public.shq_error_log_archive';
    deleted_count := v_count;
    RETURN NEXT;

    RETURN;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION shq.fn_cleanup_expired_archives IS 'Deletes archive records past retention. Run weekly or monthly.';

-- =============================================================================
-- VIEWS: Governance dashboards
-- =============================================================================

-- View: Current error governance state across all tables
CREATE OR REPLACE VIEW shq.vw_error_governance_summary AS
SELECT
    'outreach.dol_errors' AS error_table,
    disposition,
    ttl_tier,
    escalation_level,
    COUNT(*) AS error_count,
    MIN(created_at) AS oldest_error,
    MAX(created_at) AS newest_error,
    COUNT(*) FILTER (WHERE archived_at IS NULL AND NOW() > created_at + shq.fn_get_ttl_interval(ttl_tier)) AS ttl_expired_count
FROM outreach.dol_errors
GROUP BY disposition, ttl_tier, escalation_level

UNION ALL

SELECT
    'outreach.company_target_errors',
    disposition,
    ttl_tier,
    escalation_level,
    COUNT(*),
    MIN(created_at),
    MAX(created_at),
    COUNT(*) FILTER (WHERE archived_at IS NULL AND NOW() > created_at + shq.fn_get_ttl_interval(ttl_tier))
FROM outreach.company_target_errors
GROUP BY disposition, ttl_tier, escalation_level

UNION ALL

SELECT
    'people.people_errors',
    disposition,
    ttl_tier,
    escalation_level,
    COUNT(*),
    MIN(created_at),
    MAX(created_at),
    COUNT(*) FILTER (WHERE archived_at IS NULL AND NOW() > created_at + shq.fn_get_ttl_interval(ttl_tier))
FROM people.people_errors
GROUP BY disposition, ttl_tier, escalation_level

ORDER BY error_table, disposition, escalation_level;

-- View: Blocking errors (RETRY or PARKED) by outreach_id
CREATE OR REPLACE VIEW shq.vw_blocking_errors_by_outreach AS
SELECT
    outreach_id,
    ARRAY_AGG(DISTINCT error_table) AS blocking_tables,
    SUM(error_count) AS total_blocking_errors
FROM (
    SELECT outreach_id, 'outreach.dol_errors' AS error_table, COUNT(*) AS error_count
    FROM outreach.dol_errors
    WHERE disposition IN ('RETRY', 'PARKED') AND archived_at IS NULL
    GROUP BY outreach_id

    UNION ALL

    SELECT outreach_id, 'outreach.company_target_errors', COUNT(*)
    FROM outreach.company_target_errors
    WHERE disposition IN ('RETRY', 'PARKED') AND archived_at IS NULL
    GROUP BY outreach_id

    UNION ALL

    SELECT outreach_id, 'people.people_errors', COUNT(*)
    FROM people.people_errors
    WHERE disposition IN ('RETRY', 'PARKED') AND archived_at IS NULL
    GROUP BY outreach_id
) sub
GROUP BY outreach_id;

COMMENT ON VIEW shq.vw_error_governance_summary IS 'Summary of error governance state across all hub error tables';
COMMENT ON VIEW shq.vw_blocking_errors_by_outreach IS 'Shows outreach_ids that have blocking errors (RETRY or PARKED)';

-- =============================================================================
-- SCHEDULED JOB RUNNER (Call this from cron/scheduler)
-- =============================================================================

CREATE OR REPLACE FUNCTION shq.fn_run_error_governance_jobs()
RETURNS TABLE (
    job_name TEXT,
    result_summary JSONB
) AS $$
DECLARE
    v_archive_result JSONB;
    v_park_result JSONB;
    v_escalate_result JSONB;
    v_cleanup_result JSONB;
BEGIN
    -- Job 1: Archive expired errors
    SELECT jsonb_agg(jsonb_build_object('table', source_table, 'archived', archived_count))
    INTO v_archive_result
    FROM shq.fn_archive_expired_errors();

    job_name := 'archive_expired_errors';
    result_summary := v_archive_result;
    RETURN NEXT;

    -- Job 2: Auto-park exhausted retries
    SELECT jsonb_agg(jsonb_build_object('table', source_table, 'parked', parked_count))
    INTO v_park_result
    FROM shq.fn_auto_park_exhausted_retries();

    job_name := 'auto_park_exhausted_retries';
    result_summary := v_park_result;
    RETURN NEXT;

    -- Job 3: Escalate stale parked errors
    SELECT jsonb_agg(jsonb_build_object('table', source_table, 'tier1', tier_1_escalated, 'tier2', tier_2_escalated, 'tier3', tier_3_escalated))
    INTO v_escalate_result
    FROM shq.fn_escalate_stale_parked_errors();

    job_name := 'escalate_stale_parked_errors';
    result_summary := v_escalate_result;
    RETURN NEXT;

    -- Job 4: Cleanup expired archives (only run weekly)
    -- Uncomment if running from weekly job
    -- SELECT jsonb_agg(jsonb_build_object('table', archive_table, 'deleted', deleted_count))
    -- INTO v_cleanup_result
    -- FROM shq.fn_cleanup_expired_archives();
    --
    -- job_name := 'cleanup_expired_archives';
    -- result_summary := v_cleanup_result;
    -- RETURN NEXT;

    RETURN;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION shq.fn_run_error_governance_jobs IS 'Master runner for all error governance jobs. Call daily from scheduler.';

-- =============================================================================
-- USAGE
-- =============================================================================
--
-- Run all governance jobs daily:
--   SELECT * FROM shq.fn_run_error_governance_jobs();
--
-- Run archive cleanup weekly:
--   SELECT * FROM shq.fn_cleanup_expired_archives();
--
-- Check governance state:
--   SELECT * FROM shq.vw_error_governance_summary;
--
-- Find outreach_ids blocked by errors:
--   SELECT * FROM shq.vw_blocking_errors_by_outreach;
--
-- =============================================================================

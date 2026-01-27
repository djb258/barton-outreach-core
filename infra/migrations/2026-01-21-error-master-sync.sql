-- =============================================================================
-- ERROR MASTER BIDIRECTIONAL SYNC
-- =============================================================================
--
-- PURPOSE:
--   Automatically sync errors between hub-specific error tables and
--   shq.error_master. Bidirectional sync ensures:
--   1. New errors in any table → auto-insert into error_master
--   2. Resolution in either table → sync resolved_at to the other
--   3. Cleanup in either table → cleanup in the other
--
-- TABLES SYNCED:
--   - outreach.company_target_errors
--   - outreach.dol_errors
--   - outreach.people_errors
--   - outreach.blog_errors
--   - outreach.bit_errors
--   - cl.cl_errors
--   - people.people_errors
--
-- =============================================================================

-- =============================================================================
-- HELPER: Get company_unique_id from outreach_id
-- =============================================================================

CREATE OR REPLACE FUNCTION shq.fn_get_company_id_from_outreach(p_outreach_id UUID)
RETURNS UUID AS $$
DECLARE
    v_company_id UUID;
BEGIN
    SELECT company_unique_id INTO v_company_id
    FROM outreach.company_target
    WHERE outreach_id = p_outreach_id
    LIMIT 1;

    RETURN v_company_id;
END;
$$ LANGUAGE plpgsql STABLE;

-- =============================================================================
-- MAIN SYNC FUNCTION: Insert into error_master
-- =============================================================================

CREATE OR REPLACE FUNCTION shq.fn_sync_to_error_master(
    p_error_id UUID,
    p_source_table TEXT,
    p_agent_id TEXT,
    p_severity TEXT,
    p_error_type TEXT,
    p_message TEXT,
    p_company_unique_id UUID,
    p_outreach_context_id UUID,
    p_context JSONB,
    p_created_at TIMESTAMPTZ,
    p_resolved_at TIMESTAMPTZ DEFAULT NULL,
    p_resolution_type TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_master_error_id UUID;
    v_mapped_severity TEXT;
    v_mapped_resolution TEXT;
BEGIN
    -- Map severity to allowed values (HARD_FAIL, SOFT_FAIL, WARNING)
    v_mapped_severity := CASE LOWER(COALESCE(p_severity, 'HARD_FAIL'))
        WHEN 'blocking' THEN 'HARD_FAIL'
        WHEN 'error' THEN 'HARD_FAIL'
        WHEN 'hard_fail' THEN 'HARD_FAIL'
        WHEN 'soft_fail' THEN 'SOFT_FAIL'
        WHEN 'warning' THEN 'WARNING'
        ELSE 'HARD_FAIL'
    END;

    -- Map resolution_type to allowed values
    v_mapped_resolution := CASE
        WHEN p_resolution_type IS NULL THEN NULL
        WHEN UPPER(p_resolution_type) IN ('ENRICHMENT_RESOLVED', 'MANUAL_OVERRIDE', 'AUTO_RETRY_SUCCESS', 'MARKED_INVALID', 'SUPERSEDED')
            THEN UPPER(p_resolution_type)
        WHEN LOWER(p_resolution_type) LIKE '%manual%' THEN 'MANUAL_OVERRIDE'
        WHEN LOWER(p_resolution_type) LIKE '%retry%' THEN 'AUTO_RETRY_SUCCESS'
        WHEN LOWER(p_resolution_type) LIKE '%resolved%' THEN 'ENRICHMENT_RESOLVED'
        ELSE 'MANUAL_OVERRIDE'
    END;

    -- Check if already exists (idempotent)
    SELECT error_id INTO v_master_error_id
    FROM shq.error_master
    WHERE error_id = p_error_id;

    IF v_master_error_id IS NOT NULL THEN
        -- Already exists, update if resolved
        IF p_resolved_at IS NOT NULL THEN
            UPDATE shq.error_master
            SET resolved_at = p_resolved_at,
                resolution_type = v_mapped_resolution
            WHERE error_id = p_error_id
            AND resolved_at IS NULL;
        END IF;
        RETURN v_master_error_id;
    END IF;

    -- Insert new error
    INSERT INTO shq.error_master (
        error_id,
        process_id,
        agent_id,
        severity,
        error_type,
        message,
        company_unique_id,
        outreach_context_id,
        air_event_id,
        context,
        created_at,
        resolved_at,
        resolution_type
    ) VALUES (
        p_error_id,
        p_source_table,
        p_agent_id,
        v_mapped_severity,
        COALESCE(p_error_type, 'UNKNOWN'),
        COALESCE(p_message, 'No message provided'),
        p_company_unique_id::TEXT,
        p_outreach_context_id::TEXT,
        NULL,  -- AIR event ID generated separately if needed
        COALESCE(p_context, '{}'::JSONB),
        COALESCE(p_created_at, NOW()),
        p_resolved_at,
        v_mapped_resolution
    )
    ON CONFLICT (error_id) DO UPDATE SET
        resolved_at = COALESCE(EXCLUDED.resolved_at, shq.error_master.resolved_at),
        resolution_type = COALESCE(EXCLUDED.resolution_type, shq.error_master.resolution_type);

    RETURN p_error_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- REVERSE SYNC: Update source table when error_master is resolved
-- =============================================================================

CREATE OR REPLACE FUNCTION shq.fn_sync_resolution_from_master()
RETURNS TRIGGER AS $$
BEGIN
    -- Only act on resolution updates
    IF NEW.resolved_at IS NOT NULL AND OLD.resolved_at IS NULL THEN
        -- Update outreach error tables based on process_id (source table)
        CASE NEW.process_id
            WHEN 'outreach.company_target_errors' THEN
                UPDATE outreach.company_target_errors
                SET resolved_at = NEW.resolved_at,
                    resolution_note = NEW.resolution_type
                WHERE error_id = NEW.error_id
                AND resolved_at IS NULL;

            WHEN 'outreach.dol_errors' THEN
                UPDATE outreach.dol_errors
                SET resolved_at = NEW.resolved_at,
                    resolution_note = NEW.resolution_type
                WHERE error_id = NEW.error_id
                AND resolved_at IS NULL;

            WHEN 'outreach.people_errors' THEN
                UPDATE outreach.people_errors
                SET resolved_at = NEW.resolved_at,
                    resolution_note = NEW.resolution_type
                WHERE error_id = NEW.error_id
                AND resolved_at IS NULL;

            WHEN 'outreach.blog_errors' THEN
                UPDATE outreach.blog_errors
                SET resolved_at = NEW.resolved_at,
                    resolution_note = NEW.resolution_type
                WHERE error_id = NEW.error_id
                AND resolved_at IS NULL;

            WHEN 'cl.cl_errors' THEN
                UPDATE cl.cl_errors
                SET resolved_at = NEW.resolved_at
                WHERE error_id = NEW.error_id
                AND resolved_at IS NULL;

            WHEN 'people.people_errors' THEN
                UPDATE people.people_errors
                SET status = 'resolved',
                    last_updated_at = NEW.resolved_at
                WHERE error_id = NEW.error_id
                AND status != 'resolved';

            ELSE
                -- Unknown source, skip
                NULL;
        END CASE;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on error_master for reverse sync
DROP TRIGGER IF EXISTS trg_error_master_resolution_sync ON shq.error_master;
CREATE TRIGGER trg_error_master_resolution_sync
AFTER UPDATE ON shq.error_master
FOR EACH ROW
WHEN (NEW.resolved_at IS DISTINCT FROM OLD.resolved_at)
EXECUTE FUNCTION shq.fn_sync_resolution_from_master();

-- =============================================================================
-- TRIGGER FUNCTIONS FOR EACH ERROR TABLE
-- =============================================================================

-- Company Target Errors
CREATE OR REPLACE FUNCTION outreach.fn_sync_company_target_errors()
RETURNS TRIGGER AS $$
DECLARE
    v_company_id UUID;
BEGIN
    IF TG_OP = 'INSERT' THEN
        v_company_id := shq.fn_get_company_id_from_outreach(NEW.outreach_id);

        PERFORM shq.fn_sync_to_error_master(
            NEW.error_id,
            'outreach.company_target_errors',
            'company-target',
            NEW.severity,
            NEW.failure_code,
            NEW.blocking_reason,
            v_company_id,
            NEW.outreach_id,
            COALESCE(NEW.raw_input, '{}'::JSONB) ||
                jsonb_build_object(
                    'pipeline_stage', NEW.pipeline_stage,
                    'imo_stage', NEW.imo_stage,
                    'retry_allowed', NEW.retry_allowed
                ),
            NEW.created_at,
            NEW.resolved_at,
            NEW.resolution_note
        );
        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        -- Sync resolution to master
        IF NEW.resolved_at IS NOT NULL AND OLD.resolved_at IS NULL THEN
            UPDATE shq.error_master
            SET resolved_at = NEW.resolved_at,
                resolution_type = NEW.resolution_note
            WHERE error_id = NEW.error_id
            AND resolved_at IS NULL;
        END IF;
        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        -- Optional: Delete from master or mark as deleted
        DELETE FROM shq.error_master WHERE error_id = OLD.error_id;
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_company_target_errors ON outreach.company_target_errors;
CREATE TRIGGER trg_sync_company_target_errors
AFTER INSERT OR UPDATE OR DELETE ON outreach.company_target_errors
FOR EACH ROW EXECUTE FUNCTION outreach.fn_sync_company_target_errors();

-- DOL Errors
CREATE OR REPLACE FUNCTION outreach.fn_sync_dol_errors()
RETURNS TRIGGER AS $$
DECLARE
    v_company_id UUID;
BEGIN
    IF TG_OP = 'INSERT' THEN
        v_company_id := shq.fn_get_company_id_from_outreach(NEW.outreach_id);

        PERFORM shq.fn_sync_to_error_master(
            NEW.error_id,
            'outreach.dol_errors',
            'dol-filings',
            NEW.severity,
            NEW.failure_code,
            NEW.blocking_reason,
            v_company_id,
            NEW.outreach_id,
            COALESCE(NEW.raw_input, '{}'::JSONB) ||
                jsonb_build_object(
                    'pipeline_stage', NEW.pipeline_stage,
                    'retry_allowed', NEW.retry_allowed
                ),
            NEW.created_at,
            NEW.resolved_at,
            NEW.resolution_note
        );
        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        IF NEW.resolved_at IS NOT NULL AND OLD.resolved_at IS NULL THEN
            UPDATE shq.error_master
            SET resolved_at = NEW.resolved_at,
                resolution_type = NEW.resolution_note
            WHERE error_id = NEW.error_id
            AND resolved_at IS NULL;
        END IF;
        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        DELETE FROM shq.error_master WHERE error_id = OLD.error_id;
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_dol_errors ON outreach.dol_errors;
CREATE TRIGGER trg_sync_dol_errors
AFTER INSERT OR UPDATE OR DELETE ON outreach.dol_errors
FOR EACH ROW EXECUTE FUNCTION outreach.fn_sync_dol_errors();

-- People Errors (outreach schema)
CREATE OR REPLACE FUNCTION outreach.fn_sync_people_errors()
RETURNS TRIGGER AS $$
DECLARE
    v_company_id UUID;
BEGIN
    IF TG_OP = 'INSERT' THEN
        v_company_id := shq.fn_get_company_id_from_outreach(NEW.outreach_id);

        PERFORM shq.fn_sync_to_error_master(
            NEW.error_id,
            'outreach.people_errors',
            'people-intelligence',
            NEW.severity,
            NEW.failure_code,
            NEW.blocking_reason,
            v_company_id,
            NEW.outreach_id,
            COALESCE(NEW.raw_input, '{}'::JSONB) ||
                jsonb_build_object(
                    'pipeline_stage', NEW.pipeline_stage,
                    'retry_allowed', NEW.retry_allowed
                ),
            NEW.created_at,
            NEW.resolved_at,
            NEW.resolution_note
        );
        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        IF NEW.resolved_at IS NOT NULL AND OLD.resolved_at IS NULL THEN
            UPDATE shq.error_master
            SET resolved_at = NEW.resolved_at,
                resolution_type = NEW.resolution_note
            WHERE error_id = NEW.error_id
            AND resolved_at IS NULL;
        END IF;
        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        DELETE FROM shq.error_master WHERE error_id = OLD.error_id;
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_people_errors ON outreach.people_errors;
CREATE TRIGGER trg_sync_people_errors
AFTER INSERT OR UPDATE OR DELETE ON outreach.people_errors
FOR EACH ROW EXECUTE FUNCTION outreach.fn_sync_people_errors();

-- Blog Errors
CREATE OR REPLACE FUNCTION outreach.fn_sync_blog_errors()
RETURNS TRIGGER AS $$
DECLARE
    v_company_id UUID;
BEGIN
    IF TG_OP = 'INSERT' THEN
        v_company_id := shq.fn_get_company_id_from_outreach(NEW.outreach_id);

        PERFORM shq.fn_sync_to_error_master(
            NEW.error_id,
            'outreach.blog_errors',
            'blog-content',
            NEW.severity,
            NEW.failure_code,
            NEW.blocking_reason,
            v_company_id,
            NEW.outreach_id,
            COALESCE(NEW.raw_input, '{}'::JSONB) ||
                jsonb_build_object(
                    'pipeline_stage', NEW.pipeline_stage,
                    'retry_allowed', NEW.retry_allowed
                ),
            NEW.created_at,
            NEW.resolved_at,
            NEW.resolution_note
        );
        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        IF NEW.resolved_at IS NOT NULL AND OLD.resolved_at IS NULL THEN
            UPDATE shq.error_master
            SET resolved_at = NEW.resolved_at,
                resolution_type = NEW.resolution_note
            WHERE error_id = NEW.error_id
            AND resolved_at IS NULL;
        END IF;
        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        DELETE FROM shq.error_master WHERE error_id = OLD.error_id;
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_blog_errors ON outreach.blog_errors;
CREATE TRIGGER trg_sync_blog_errors
AFTER INSERT OR UPDATE OR DELETE ON outreach.blog_errors
FOR EACH ROW EXECUTE FUNCTION outreach.fn_sync_blog_errors();

-- BIT Errors
CREATE OR REPLACE FUNCTION outreach.fn_sync_bit_errors()
RETURNS TRIGGER AS $$
DECLARE
    v_company_id UUID;
BEGIN
    IF TG_OP = 'INSERT' THEN
        v_company_id := shq.fn_get_company_id_from_outreach(NEW.outreach_id);

        PERFORM shq.fn_sync_to_error_master(
            NEW.error_id,
            'outreach.bit_errors',
            'bit-engine',
            NEW.severity,
            NEW.failure_code,
            NEW.blocking_reason,
            v_company_id,
            NEW.outreach_id,
            COALESCE(NEW.raw_input, '{}'::JSONB) ||
                jsonb_build_object(
                    'pipeline_stage', NEW.pipeline_stage,
                    'correlation_id', NEW.correlation_id
                ),
            NEW.created_at,
            NULL,
            NULL
        );
        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        DELETE FROM shq.error_master WHERE error_id = OLD.error_id;
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_bit_errors ON outreach.bit_errors;
CREATE TRIGGER trg_sync_bit_errors
AFTER INSERT OR DELETE ON outreach.bit_errors
FOR EACH ROW EXECUTE FUNCTION outreach.fn_sync_bit_errors();

-- CL Errors
CREATE OR REPLACE FUNCTION cl.fn_sync_cl_errors()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        PERFORM shq.fn_sync_to_error_master(
            NEW.error_id,
            'cl.cl_errors',
            'company-lifecycle',
            'HARD_FAIL',
            NEW.failure_reason_code,
            NEW.failure_reason_code || ' in pass: ' || COALESCE(NEW.pass_name, 'unknown'),
            NEW.company_unique_id,
            NULL,
            COALESCE(NEW.inputs_snapshot, '{}'::JSONB) ||
                jsonb_build_object(
                    'pass_name', NEW.pass_name,
                    'lifecycle_run_id', NEW.lifecycle_run_id
                ),
            NEW.created_at,
            NEW.resolved_at,
            NULL
        );
        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        IF NEW.resolved_at IS NOT NULL AND OLD.resolved_at IS NULL THEN
            UPDATE shq.error_master
            SET resolved_at = NEW.resolved_at
            WHERE error_id = NEW.error_id
            AND resolved_at IS NULL;
        END IF;
        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        DELETE FROM shq.error_master WHERE error_id = OLD.error_id;
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_cl_errors ON cl.cl_errors;
CREATE TRIGGER trg_sync_cl_errors
AFTER INSERT OR UPDATE OR DELETE ON cl.cl_errors
FOR EACH ROW EXECUTE FUNCTION cl.fn_sync_cl_errors();

-- People Errors (people schema)
CREATE OR REPLACE FUNCTION people.fn_sync_people_errors()
RETURNS TRIGGER AS $$
DECLARE
    v_company_id UUID;
BEGIN
    IF TG_OP = 'INSERT' THEN
        v_company_id := shq.fn_get_company_id_from_outreach(NEW.outreach_id);

        PERFORM shq.fn_sync_to_error_master(
            NEW.error_id,
            'people.people_errors',
            'people-enrichment',
            CASE NEW.error_type
                WHEN 'HARD_FAIL' THEN 'HARD_FAIL'
                WHEN 'SOFT_FAIL' THEN 'SOFT_FAIL'
                ELSE 'ERROR'
            END,
            NEW.error_code,
            NEW.error_message,
            v_company_id,
            NEW.outreach_id,
            COALESCE(NEW.raw_payload, '{}'::JSONB) ||
                jsonb_build_object(
                    'error_stage', NEW.error_stage,
                    'slot_id', NEW.slot_id,
                    'person_id', NEW.person_id,
                    'retry_strategy', NEW.retry_strategy
                ),
            NEW.created_at,
            CASE WHEN NEW.status = 'resolved' THEN NEW.last_updated_at ELSE NULL END,
            NEW.status
        );
        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        IF NEW.status = 'resolved' AND OLD.status != 'resolved' THEN
            UPDATE shq.error_master
            SET resolved_at = NEW.last_updated_at,
                resolution_type = 'resolved'
            WHERE error_id = NEW.error_id
            AND resolved_at IS NULL;
        END IF;
        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        DELETE FROM shq.error_master WHERE error_id = OLD.error_id;
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_people_schema_errors ON people.people_errors;
CREATE TRIGGER trg_sync_people_schema_errors
AFTER INSERT OR UPDATE OR DELETE ON people.people_errors
FOR EACH ROW EXECUTE FUNCTION people.fn_sync_people_errors();

-- =============================================================================
-- BACKFILL FUNCTION: Sync existing errors to error_master
-- =============================================================================

CREATE OR REPLACE FUNCTION shq.fn_backfill_error_master()
RETURNS TABLE (
    source_table TEXT,
    synced_count INTEGER,
    skipped_count INTEGER
) AS $$
DECLARE
    v_synced INTEGER;
    v_skipped INTEGER;
    v_company_id UUID;
    r RECORD;
BEGIN
    -- Company Target Errors
    v_synced := 0;
    v_skipped := 0;
    FOR r IN SELECT * FROM outreach.company_target_errors WHERE error_id NOT IN (SELECT error_id FROM shq.error_master)
    LOOP
        v_company_id := shq.fn_get_company_id_from_outreach(r.outreach_id);
        PERFORM shq.fn_sync_to_error_master(
            r.error_id, 'outreach.company_target_errors', 'company-target',
            r.severity, r.failure_code, r.blocking_reason, v_company_id, r.outreach_id,
            COALESCE(r.raw_input, '{}'::JSONB), r.created_at, r.resolved_at, r.resolution_note
        );
        v_synced := v_synced + 1;
    END LOOP;
    source_table := 'outreach.company_target_errors';
    synced_count := v_synced;
    skipped_count := v_skipped;
    RETURN NEXT;

    -- DOL Errors
    v_synced := 0;
    FOR r IN SELECT * FROM outreach.dol_errors WHERE error_id NOT IN (SELECT error_id FROM shq.error_master)
    LOOP
        v_company_id := shq.fn_get_company_id_from_outreach(r.outreach_id);
        PERFORM shq.fn_sync_to_error_master(
            r.error_id, 'outreach.dol_errors', 'dol-filings',
            r.severity, r.failure_code, r.blocking_reason, v_company_id, r.outreach_id,
            COALESCE(r.raw_input, '{}'::JSONB), r.created_at, r.resolved_at, r.resolution_note
        );
        v_synced := v_synced + 1;
    END LOOP;
    source_table := 'outreach.dol_errors';
    synced_count := v_synced;
    skipped_count := 0;
    RETURN NEXT;

    -- Blog Errors
    v_synced := 0;
    FOR r IN SELECT * FROM outreach.blog_errors WHERE error_id NOT IN (SELECT error_id FROM shq.error_master)
    LOOP
        v_company_id := shq.fn_get_company_id_from_outreach(r.outreach_id);
        PERFORM shq.fn_sync_to_error_master(
            r.error_id, 'outreach.blog_errors', 'blog-content',
            r.severity, r.failure_code, r.blocking_reason, v_company_id, r.outreach_id,
            COALESCE(r.raw_input, '{}'::JSONB), r.created_at, r.resolved_at, r.resolution_note
        );
        v_synced := v_synced + 1;
    END LOOP;
    source_table := 'outreach.blog_errors';
    synced_count := v_synced;
    skipped_count := 0;
    RETURN NEXT;

    -- CL Errors
    v_synced := 0;
    FOR r IN SELECT * FROM cl.cl_errors WHERE error_id NOT IN (SELECT error_id FROM shq.error_master)
    LOOP
        PERFORM shq.fn_sync_to_error_master(
            r.error_id, 'cl.cl_errors', 'company-lifecycle',
            'HARD_FAIL', r.failure_reason_code, r.failure_reason_code,
            r.company_unique_id, NULL,
            COALESCE(r.inputs_snapshot, '{}'::JSONB), r.created_at, r.resolved_at, NULL
        );
        v_synced := v_synced + 1;
    END LOOP;
    source_table := 'cl.cl_errors';
    synced_count := v_synced;
    skipped_count := 0;
    RETURN NEXT;

    -- People Errors (people schema)
    v_synced := 0;
    FOR r IN SELECT * FROM people.people_errors WHERE error_id NOT IN (SELECT error_id FROM shq.error_master)
    LOOP
        v_company_id := shq.fn_get_company_id_from_outreach(r.outreach_id);
        PERFORM shq.fn_sync_to_error_master(
            r.error_id, 'people.people_errors', 'people-enrichment',
            COALESCE(r.error_type, 'ERROR'), r.error_code, r.error_message,
            v_company_id, r.outreach_id,
            COALESCE(r.raw_payload, '{}'::JSONB), r.created_at,
            CASE WHEN r.status = 'resolved' THEN r.last_updated_at ELSE NULL END, r.status
        );
        v_synced := v_synced + 1;
    END LOOP;
    source_table := 'people.people_errors';
    synced_count := v_synced;
    skipped_count := 0;
    RETURN NEXT;

    RETURN;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- CONVENIENCE VIEWS
-- =============================================================================

-- View: All unresolved errors with source info
CREATE OR REPLACE VIEW shq.vw_unresolved_errors_by_source AS
SELECT
    process_id AS source_table,
    agent_id,
    COUNT(*) AS error_count,
    MIN(created_at) AS oldest_error,
    MAX(created_at) AS newest_error
FROM shq.error_master
WHERE resolved_at IS NULL
GROUP BY process_id, agent_id
ORDER BY error_count DESC;

-- View: Error resolution rate by source
CREATE OR REPLACE VIEW shq.vw_error_resolution_rate AS
SELECT
    process_id AS source_table,
    COUNT(*) AS total_errors,
    COUNT(*) FILTER (WHERE resolved_at IS NOT NULL) AS resolved_errors,
    COUNT(*) FILTER (WHERE resolved_at IS NULL) AS unresolved_errors,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE resolved_at IS NOT NULL) / NULLIF(COUNT(*), 0),
        2
    ) AS resolution_rate_pct
FROM shq.error_master
GROUP BY process_id
ORDER BY unresolved_errors DESC;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON FUNCTION shq.fn_sync_to_error_master IS
'Syncs an error from any source table to shq.error_master. Idempotent - safe to call multiple times.';

COMMENT ON FUNCTION shq.fn_backfill_error_master IS
'Backfills existing errors from all source tables into shq.error_master. Run once after migration.';

COMMENT ON FUNCTION shq.fn_sync_resolution_from_master IS
'Reverse sync - when error_master is resolved, sync resolution to source table.';

COMMENT ON VIEW shq.vw_unresolved_errors_by_source IS
'Shows unresolved error counts grouped by source table and agent.';

COMMENT ON VIEW shq.vw_error_resolution_rate IS
'Shows error resolution rates by source table.';

-- =============================================================================
-- USAGE INSTRUCTIONS
-- =============================================================================
--
-- After running this migration:
--
-- 1. BACKFILL EXISTING ERRORS:
--    SELECT * FROM shq.fn_backfill_error_master();
--
-- 2. VERIFY SYNC:
--    SELECT * FROM shq.vw_error_resolution_rate;
--
-- 3. CHECK UNRESOLVED:
--    SELECT * FROM shq.vw_unresolved_errors_by_source;
--
-- 4. RESOLVE AN ERROR (will sync to source table):
--    UPDATE shq.error_master
--    SET resolved_at = NOW(), resolution_type = 'manual_fix'
--    WHERE error_id = '...';
--
-- =============================================================================

-- ============================================================================
-- MIGRATION: Completeness Contract Schema Enhancement
-- Version: 1.0.0
-- Date: 2026-01-28
-- Purpose: Add structured blocker classification to company_hub_status
-- ============================================================================

-- STEP 1: Create blocker_type enum
-- This replaces free-text status_reason with closed classification

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'blocker_type_enum') THEN
        CREATE TYPE blocker_type_enum AS ENUM (
            'DATA_MISSING',            -- Required data not present
            'DATA_UNDISCOVERABLE',     -- Data cannot be found via available methods
            'DATA_CONFLICT',           -- Conflicting data, cannot resolve
            'SOURCE_UNAVAILABLE',      -- External source not responding
            'NOT_APPLICABLE',          -- Sub-hub does not apply to this entity
            'HUMAN_DECISION_REQUIRED', -- Ambiguous, needs human review
            'UPSTREAM_BLOCKED',        -- Previous hub in waterfall not complete
            'THRESHOLD_NOT_MET',       -- Metric below required threshold
            'EXPIRED'                  -- Data exists but is stale
        );
        RAISE NOTICE 'Created blocker_type_enum';
    ELSE
        RAISE NOTICE 'blocker_type_enum already exists';
    END IF;
END $$;

-- STEP 2: Add structured columns to company_hub_status

ALTER TABLE outreach.company_hub_status
ADD COLUMN IF NOT EXISTS blocker_type blocker_type_enum,
ADD COLUMN IF NOT EXISTS blocker_evidence JSONB;

COMMENT ON COLUMN outreach.company_hub_status.blocker_type IS 'Closed ENUM classification of why hub is incomplete. NULL when status=PASS.';
COMMENT ON COLUMN outreach.company_hub_status.blocker_evidence IS 'Structured evidence: { missing_fields[], checked_sources[], etc. }';

-- STEP 3: Create index for blocker_type queries

CREATE INDEX IF NOT EXISTS idx_company_hub_status_blocker_type
ON outreach.company_hub_status (blocker_type)
WHERE blocker_type IS NOT NULL;

-- STEP 4: Migrate existing status_reason to blocker_type (best effort)

UPDATE outreach.company_hub_status
SET blocker_type = CASE
    WHEN status = 'PASS' THEN NULL
    WHEN status = 'IN_PROGRESS' THEN NULL
    WHEN status_reason IS NULL THEN 'DATA_MISSING'
    WHEN status_reason ILIKE '%missing%' THEN 'DATA_MISSING'::blocker_type_enum
    WHEN status_reason ILIKE '%not found%' THEN 'DATA_UNDISCOVERABLE'::blocker_type_enum
    WHEN status_reason ILIKE '%conflict%' THEN 'DATA_CONFLICT'::blocker_type_enum
    WHEN status_reason ILIKE '%unavailable%' THEN 'SOURCE_UNAVAILABLE'::blocker_type_enum
    WHEN status_reason ILIKE '%not applicable%' THEN 'NOT_APPLICABLE'::blocker_type_enum
    WHEN status_reason ILIKE '%n/a%' THEN 'NOT_APPLICABLE'::blocker_type_enum
    WHEN status_reason ILIKE '%human%' THEN 'HUMAN_DECISION_REQUIRED'::blocker_type_enum
    WHEN status_reason ILIKE '%review%' THEN 'HUMAN_DECISION_REQUIRED'::blocker_type_enum
    WHEN status_reason ILIKE '%upstream%' THEN 'UPSTREAM_BLOCKED'::blocker_type_enum
    WHEN status_reason ILIKE '%blocked%' THEN 'UPSTREAM_BLOCKED'::blocker_type_enum
    WHEN status_reason ILIKE '%threshold%' THEN 'THRESHOLD_NOT_MET'::blocker_type_enum
    WHEN status_reason ILIKE '%below%' THEN 'THRESHOLD_NOT_MET'::blocker_type_enum
    WHEN status_reason ILIKE '%expired%' THEN 'EXPIRED'::blocker_type_enum
    WHEN status_reason ILIKE '%stale%' THEN 'EXPIRED'::blocker_type_enum
    WHEN status_reason ILIKE '%old%' THEN 'EXPIRED'::blocker_type_enum
    ELSE 'DATA_MISSING'::blocker_type_enum  -- Default fallback
END
WHERE status IN ('FAIL', 'BLOCKED')
  AND blocker_type IS NULL;

-- STEP 5: Create canonical completeness view

CREATE OR REPLACE VIEW outreach.vw_entity_completeness AS
SELECT
    chs.company_unique_id AS entity_id,
    hr.hub_id AS sub_hub_name,
    hr.hub_name AS sub_hub_display_name,
    hr.waterfall_order,
    hr.gates_completion AS is_required,
    hr.classification AS hub_classification,
    chs.status AS completeness_status,
    chs.blocker_type,
    chs.blocker_evidence,
    chs.status_reason AS legacy_reason,  -- Keep for backwards compatibility
    chs.metric_value,
    hr.metric_critical_threshold AS required_threshold,
    hr.metric_healthy_threshold AS healthy_threshold,
    CASE
        WHEN chs.metric_value IS NOT NULL AND hr.metric_critical_threshold IS NOT NULL
        THEN chs.metric_value >= hr.metric_critical_threshold
        ELSE NULL
    END AS meets_critical_threshold,
    chs.last_processed_at AS last_checked_at,
    CASE
        WHEN chs.status = 'PASS' THEN 'COMPLETE'
        WHEN chs.status = 'BLOCKED' AND chs.blocker_type = 'NOT_APPLICABLE' THEN 'NOT_APPLICABLE'
        WHEN chs.status = 'IN_PROGRESS' THEN 'PROCESSING'
        ELSE 'INCOMPLETE'
    END AS simple_status,
    CASE
        WHEN chs.status = 'PASS' THEN 0
        WHEN chs.status = 'BLOCKED' AND chs.blocker_type = 'NOT_APPLICABLE' THEN 0
        WHEN chs.status = 'IN_PROGRESS' THEN 1
        WHEN chs.status = 'FAIL' THEN 2
        WHEN chs.status = 'BLOCKED' THEN 3
        ELSE 4
    END AS severity_rank
FROM outreach.company_hub_status chs
JOIN outreach.hub_registry hr ON hr.hub_id = chs.hub_id;

COMMENT ON VIEW outreach.vw_entity_completeness IS 'Canonical completeness view: per-entity, per-hub evaluation with blocker classification';

-- STEP 6: Create aggregated entity status view

CREATE OR REPLACE VIEW outreach.vw_entity_overall_status AS
SELECT
    entity_id,
    COUNT(*) AS total_hubs,
    COUNT(*) FILTER (WHERE is_required) AS required_hubs,
    COUNT(*) FILTER (WHERE completeness_status = 'PASS') AS pass_count,
    COUNT(*) FILTER (WHERE completeness_status = 'PASS' AND is_required) AS required_pass_count,
    COUNT(*) FILTER (WHERE completeness_status = 'FAIL') AS fail_count,
    COUNT(*) FILTER (WHERE completeness_status = 'BLOCKED') AS blocked_count,
    COUNT(*) FILTER (WHERE completeness_status = 'IN_PROGRESS') AS in_progress_count,
    CASE
        WHEN COUNT(*) FILTER (WHERE is_required AND completeness_status != 'PASS' AND blocker_type != 'NOT_APPLICABLE') = 0
        THEN 'COMPLETE'
        WHEN COUNT(*) FILTER (WHERE completeness_status = 'IN_PROGRESS') > 0
        THEN 'PROCESSING'
        ELSE 'INCOMPLETE'
    END AS overall_status,
    ARRAY_AGG(sub_hub_name ORDER BY waterfall_order) FILTER (
        WHERE completeness_status NOT IN ('PASS') AND blocker_type != 'NOT_APPLICABLE' AND is_required
    ) AS blocking_hubs,
    ARRAY_AGG(DISTINCT blocker_type ORDER BY blocker_type) FILTER (
        WHERE blocker_type IS NOT NULL
    ) AS blocker_types,
    MAX(last_checked_at) AS last_checked_at
FROM outreach.vw_entity_completeness
GROUP BY entity_id;

COMMENT ON VIEW outreach.vw_entity_overall_status IS 'Aggregated entity completeness: one row per entity with overall status';

-- STEP 7: Create blocker analysis view

CREATE OR REPLACE VIEW outreach.vw_blocker_analysis AS
SELECT
    sub_hub_name,
    blocker_type,
    COUNT(*) AS entity_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY sub_hub_name), 2) AS pct_of_hub,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(DISTINCT entity_id) FROM outreach.vw_entity_completeness), 2) AS pct_of_total
FROM outreach.vw_entity_completeness
WHERE completeness_status IN ('FAIL', 'BLOCKED')
  AND blocker_type IS NOT NULL
GROUP BY sub_hub_name, blocker_type
ORDER BY sub_hub_name, entity_count DESC;

COMMENT ON VIEW outreach.vw_blocker_analysis IS 'Blocker distribution analysis by sub-hub and blocker type';

-- STEP 8: Verify migration

DO $$
DECLARE
    v_enum_exists BOOLEAN;
    v_column_exists BOOLEAN;
    v_view_exists BOOLEAN;
BEGIN
    SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'blocker_type_enum') INTO v_enum_exists;
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'outreach' AND table_name = 'company_hub_status' AND column_name = 'blocker_type'
    ) INTO v_column_exists;
    SELECT EXISTS (
        SELECT 1 FROM information_schema.views
        WHERE table_schema = 'outreach' AND table_name = 'vw_entity_completeness'
    ) INTO v_view_exists;

    IF v_enum_exists AND v_column_exists AND v_view_exists THEN
        RAISE NOTICE '✓ Migration complete: blocker_type_enum, blocker_type column, vw_entity_completeness view all exist';
    ELSE
        RAISE EXCEPTION 'Migration verification failed: enum=%, column=%, view=%', v_enum_exists, v_column_exists, v_view_exists;
    END IF;
END $$;

-- ============================================================================
-- END MIGRATION
-- ============================================================================

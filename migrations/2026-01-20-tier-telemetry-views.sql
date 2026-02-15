-- =============================================================================
-- !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
--                         DO NOT MODIFY WITHOUT CHANGE REQUEST
-- !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
--
-- STATUS: FROZEN (v1.0 Operational Baseline)
-- FREEZE DATE: 2026-01-20
-- REFERENCE: docs/GO-LIVE_STATE_v1.0.md
--
-- This file contains tier analytics views that are FROZEN at v1.0.
-- These views are READ-ONLY and depend on authoritative sources.
-- Any modification requires:
--   1. Formal Change Request with justification
--   2. Impact analysis on all dashboards and reports
--   3. Full re-certification after changes
--   4. Technical lead sign-off
--
-- FROZEN COMPONENTS IN THIS FILE:
--   - outreach.vw_tier_distribution (Tier breakdown)
--   - outreach.vw_hub_block_analysis (Hub blocking metrics)
--   - outreach.vw_freshness_analysis (Freshness decay tracking)
--   - outreach.vw_signal_gap_analysis (Signal coverage gaps)
--   - outreach.vw_tier_telemetry_summary (Dashboard summary)
--   - outreach.tier_snapshot_history (Historical snapshots)
--   - outreach.fn_capture_tier_snapshot() (Snapshot capture)
--
-- =============================================================================
-- TIER TELEMETRY VIEWS - Read-Only Analytics
-- =============================================================================
--
-- PURPOSE:
--   Provide visibility into tier distribution and drift without touching
--   tier computation logic. These views are READ-ONLY and do not affect
--   any business logic.
--
-- VIEWS:
--   1. vw_tier_distribution - Overall tier breakdown
--   2. vw_hub_block_analysis - % blocked by each hub
--   3. vw_freshness_analysis - % failing freshness checks
--   4. vw_signal_gap_analysis - % lacking signals per hub
--   5. vw_tier_telemetry_summary - Aggregated telemetry dashboard
--
-- DOCTRINE:
--   - READ-ONLY: No triggers, no mutations
--   - Does NOT touch tier computation logic
--   - Does NOT touch kill switches
--   - Does NOT touch hub status logic
--
-- =============================================================================

-- =============================================================================
-- VIEW 1: TIER DISTRIBUTION
-- =============================================================================
-- Shows count and percentage of companies at each tier

CREATE OR REPLACE VIEW outreach.vw_tier_distribution AS
WITH tier_counts AS (
    SELECT
        marketing_tier,
        COUNT(*) as company_count
    FROM outreach.vw_marketing_eligibility
    GROUP BY marketing_tier
),
total AS (
    SELECT COUNT(*) as total_companies
    FROM outreach.vw_marketing_eligibility
)
SELECT
    tc.marketing_tier,
    CASE tc.marketing_tier
        WHEN -1 THEN 'INELIGIBLE'
        WHEN 0 THEN 'Tier 0 (Cold)'
        WHEN 1 THEN 'Tier 1 (Persona)'
        WHEN 2 THEN 'Tier 2 (Trigger)'
        WHEN 3 THEN 'Tier 3 (Aggressive)'
        ELSE 'Unknown'
    END as tier_name,
    tc.company_count,
    t.total_companies,
    ROUND((tc.company_count::numeric / NULLIF(t.total_companies, 0)) * 100, 2) as percentage
FROM tier_counts tc
CROSS JOIN total t
ORDER BY tc.marketing_tier;

COMMENT ON VIEW outreach.vw_tier_distribution IS
'Read-only view showing count and percentage of companies at each marketing tier.';

-- =============================================================================
-- VIEW 2: HUB BLOCK ANALYSIS
-- =============================================================================
-- Shows which hubs are causing the most blocks (% blocked by each hub)

CREATE OR REPLACE VIEW outreach.vw_hub_block_analysis AS
WITH hub_status_counts AS (
    SELECT
        hub_id,
        status,
        COUNT(*) as count
    FROM outreach.company_hub_status
    GROUP BY hub_id, status
),
hub_totals AS (
    SELECT
        hub_id,
        SUM(count) as total_companies
    FROM hub_status_counts
    GROUP BY hub_id
),
blocked_counts AS (
    SELECT
        hub_id,
        SUM(count) as blocked_count
    FROM hub_status_counts
    WHERE status IN ('FAIL', 'BLOCKED')
    GROUP BY hub_id
)
SELECT
    hr.hub_id,
    hr.hub_name,
    hr.waterfall_order,
    hr.classification,
    COALESCE(ht.total_companies, 0) as total_companies,
    COALESCE(bc.blocked_count, 0) as blocked_count,
    ROUND(
        (COALESCE(bc.blocked_count, 0)::numeric / NULLIF(ht.total_companies, 0)) * 100,
        2
    ) as blocked_percentage,
    -- Status breakdown
    COALESCE((SELECT count FROM hub_status_counts hsc WHERE hsc.hub_id = hr.hub_id AND hsc.status = 'PASS'), 0) as pass_count,
    COALESCE((SELECT count FROM hub_status_counts hsc WHERE hsc.hub_id = hr.hub_id AND hsc.status = 'IN_PROGRESS'), 0) as in_progress_count,
    COALESCE((SELECT count FROM hub_status_counts hsc WHERE hsc.hub_id = hr.hub_id AND hsc.status = 'FAIL'), 0) as fail_count,
    COALESCE((SELECT count FROM hub_status_counts hsc WHERE hsc.hub_id = hr.hub_id AND hsc.status = 'BLOCKED'), 0) as blocked_by_upstream_count
FROM outreach.hub_registry hr
LEFT JOIN hub_totals ht ON hr.hub_id = ht.hub_id
LEFT JOIN blocked_counts bc ON hr.hub_id = bc.hub_id
ORDER BY hr.waterfall_order;

COMMENT ON VIEW outreach.vw_hub_block_analysis IS
'Read-only view showing which hubs are causing blocks. Shows % blocked by each hub.';

-- =============================================================================
-- VIEW 3: FRESHNESS ANALYSIS
-- =============================================================================
-- Shows % of companies failing freshness checks per hub

CREATE OR REPLACE VIEW outreach.vw_freshness_analysis AS
WITH freshness_config AS (
    -- Freshness windows per hub (from hub_status.py implementations)
    SELECT 'people-intelligence' as hub_id, 90 as freshness_days UNION ALL
    SELECT 'blog-content', 30 UNION ALL
    SELECT 'talent-flow', 60 UNION ALL
    SELECT 'company-target', 365 UNION ALL  -- Company target rarely expires
    SELECT 'dol-filings', 365  -- DOL filings are annual
),
hub_freshness AS (
    SELECT
        chs.hub_id,
        fc.freshness_days,
        COUNT(*) as total_records,
        COUNT(*) FILTER (
            WHERE chs.last_processed_at >= NOW() - (fc.freshness_days || ' days')::interval
        ) as fresh_count,
        COUNT(*) FILTER (
            WHERE chs.last_processed_at < NOW() - (fc.freshness_days || ' days')::interval
            OR chs.last_processed_at IS NULL
        ) as stale_count
    FROM outreach.company_hub_status chs
    JOIN freshness_config fc ON chs.hub_id = fc.hub_id
    GROUP BY chs.hub_id, fc.freshness_days
)
SELECT
    hr.hub_id,
    hr.hub_name,
    hf.freshness_days,
    hf.total_records,
    hf.fresh_count,
    hf.stale_count,
    ROUND((hf.fresh_count::numeric / NULLIF(hf.total_records, 0)) * 100, 2) as fresh_percentage,
    ROUND((hf.stale_count::numeric / NULLIF(hf.total_records, 0)) * 100, 2) as stale_percentage
FROM outreach.hub_registry hr
LEFT JOIN hub_freshness hf ON hr.hub_id = hf.hub_id
ORDER BY hr.waterfall_order;

COMMENT ON VIEW outreach.vw_freshness_analysis IS
'Read-only view showing % of companies failing freshness checks per hub.';

-- =============================================================================
-- VIEW 4: SIGNAL GAP ANALYSIS
-- =============================================================================
-- Shows % of companies lacking signals (IN_PROGRESS with no data)

CREATE OR REPLACE VIEW outreach.vw_signal_gap_analysis AS
WITH signal_counts AS (
    -- Count actual signals per hub
    SELECT 'company-target' as hub_id, COUNT(DISTINCT company_unique_id) as with_signals
    FROM outreach.company_target WHERE company_unique_id IS NOT NULL
    UNION ALL
    SELECT 'dol-filings', COUNT(DISTINCT company_unique_id)
    FROM outreach.dol WHERE company_unique_id IS NOT NULL
    UNION ALL
    SELECT 'people-intelligence', COUNT(DISTINCT company_unique_id)
    FROM outreach.people WHERE company_unique_id IS NOT NULL
    UNION ALL
    SELECT 'blog-content', COUNT(DISTINCT company_unique_id)
    FROM outreach.blog WHERE company_unique_id IS NOT NULL
),
total_companies AS (
    SELECT COUNT(DISTINCT company_unique_id) as total
    FROM outreach.company_target
    WHERE company_unique_id IS NOT NULL
),
in_progress_counts AS (
    SELECT
        hub_id,
        COUNT(*) as in_progress_count
    FROM outreach.company_hub_status
    WHERE status = 'IN_PROGRESS'
    GROUP BY hub_id
)
SELECT
    hr.hub_id,
    hr.hub_name,
    tc.total as total_companies,
    COALESCE(sc.with_signals, 0) as companies_with_signals,
    (tc.total - COALESCE(sc.with_signals, 0)) as companies_lacking_signals,
    ROUND(
        ((tc.total - COALESCE(sc.with_signals, 0))::numeric / NULLIF(tc.total, 0)) * 100,
        2
    ) as lacking_signals_percentage,
    COALESCE(ipc.in_progress_count, 0) as in_progress_count,
    ROUND(
        (COALESCE(ipc.in_progress_count, 0)::numeric / NULLIF(tc.total, 0)) * 100,
        2
    ) as in_progress_percentage
FROM outreach.hub_registry hr
CROSS JOIN total_companies tc
LEFT JOIN signal_counts sc ON hr.hub_id = sc.hub_id
LEFT JOIN in_progress_counts ipc ON hr.hub_id = ipc.hub_id
ORDER BY hr.waterfall_order;

COMMENT ON VIEW outreach.vw_signal_gap_analysis IS
'Read-only view showing % of companies lacking signals per hub.';

-- =============================================================================
-- VIEW 5: TIER TELEMETRY SUMMARY
-- =============================================================================
-- Aggregated dashboard view combining all telemetry

CREATE OR REPLACE VIEW outreach.vw_tier_telemetry_summary AS
WITH tier_stats AS (
    SELECT
        COUNT(*) as total_companies,
        COUNT(*) FILTER (WHERE marketing_tier = -1) as tier_neg1,
        COUNT(*) FILTER (WHERE marketing_tier = 0) as tier_0,
        COUNT(*) FILTER (WHERE marketing_tier = 1) as tier_1,
        COUNT(*) FILTER (WHERE marketing_tier = 2) as tier_2,
        COUNT(*) FILTER (WHERE marketing_tier = 3) as tier_3,
        COUNT(*) FILTER (WHERE overall_status = 'BLOCKED') as blocked_total,
        COUNT(*) FILTER (WHERE overall_status = 'COMPLETE') as complete_total,
        COUNT(*) FILTER (WHERE overall_status = 'IN_PROGRESS') as in_progress_total
    FROM outreach.vw_marketing_eligibility
),
hub_pass_rates AS (
    SELECT
        hub_id,
        ROUND(
            (COUNT(*) FILTER (WHERE status = 'PASS')::numeric / NULLIF(COUNT(*), 0)) * 100,
            2
        ) as pass_rate
    FROM outreach.company_hub_status
    GROUP BY hub_id
)
SELECT
    ts.total_companies,
    -- Tier distribution
    ts.tier_neg1 as ineligible_count,
    ts.tier_0 as tier_0_count,
    ts.tier_1 as tier_1_count,
    ts.tier_2 as tier_2_count,
    ts.tier_3 as tier_3_count,
    -- Percentages
    ROUND((ts.tier_neg1::numeric / NULLIF(ts.total_companies, 0)) * 100, 2) as ineligible_pct,
    ROUND((ts.tier_0::numeric / NULLIF(ts.total_companies, 0)) * 100, 2) as tier_0_pct,
    ROUND((ts.tier_1::numeric / NULLIF(ts.total_companies, 0)) * 100, 2) as tier_1_pct,
    ROUND((ts.tier_2::numeric / NULLIF(ts.total_companies, 0)) * 100, 2) as tier_2_pct,
    ROUND((ts.tier_3::numeric / NULLIF(ts.total_companies, 0)) * 100, 2) as tier_3_pct,
    -- Overall status
    ts.blocked_total,
    ts.complete_total,
    ts.in_progress_total,
    -- Hub pass rates (as JSONB for easy consumption)
    (
        SELECT jsonb_object_agg(hub_id, pass_rate)
        FROM hub_pass_rates
    ) as hub_pass_rates,
    -- Timestamp
    NOW() as computed_at
FROM tier_stats ts;

COMMENT ON VIEW outreach.vw_tier_telemetry_summary IS
'Read-only aggregated telemetry dashboard combining tier distribution and hub pass rates.';

-- =============================================================================
-- TABLE: TIER SNAPSHOT HISTORY
-- =============================================================================
-- Stores daily snapshots for trend analysis

CREATE TABLE IF NOT EXISTS outreach.tier_snapshot_history (
    snapshot_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,

    -- Tier distribution
    total_companies INTEGER NOT NULL,
    ineligible_count INTEGER NOT NULL DEFAULT 0,
    tier_0_count INTEGER NOT NULL DEFAULT 0,
    tier_1_count INTEGER NOT NULL DEFAULT 0,
    tier_2_count INTEGER NOT NULL DEFAULT 0,
    tier_3_count INTEGER NOT NULL DEFAULT 0,

    -- Status distribution
    blocked_count INTEGER NOT NULL DEFAULT 0,
    complete_count INTEGER NOT NULL DEFAULT 0,
    in_progress_count INTEGER NOT NULL DEFAULT 0,

    -- Hub pass rates (JSONB)
    hub_pass_rates JSONB NOT NULL DEFAULT '{}'::JSONB,

    -- Hub block rates (JSONB)
    hub_block_rates JSONB NOT NULL DEFAULT '{}'::JSONB,

    -- Freshness stats (JSONB)
    freshness_stats JSONB NOT NULL DEFAULT '{}'::JSONB,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- One snapshot per day
    CONSTRAINT tier_snapshot_unique_date UNIQUE (snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_tier_snapshot_date
ON outreach.tier_snapshot_history(snapshot_date DESC);

COMMENT ON TABLE outreach.tier_snapshot_history IS
'Daily snapshots of tier distribution and hub metrics for trend analysis.';

-- =============================================================================
-- FUNCTION: Capture daily snapshot
-- =============================================================================

CREATE OR REPLACE FUNCTION outreach.fn_capture_tier_snapshot()
RETURNS UUID AS $$
DECLARE
    v_snapshot_id UUID;
    v_hub_pass_rates JSONB;
    v_hub_block_rates JSONB;
    v_freshness_stats JSONB;
BEGIN
    -- Get hub pass rates
    SELECT jsonb_object_agg(hub_id, pass_rate)
    INTO v_hub_pass_rates
    FROM (
        SELECT
            hub_id,
            ROUND((COUNT(*) FILTER (WHERE status = 'PASS')::numeric / NULLIF(COUNT(*), 0)) * 100, 2) as pass_rate
        FROM outreach.company_hub_status
        GROUP BY hub_id
    ) hr;

    -- Get hub block rates
    SELECT jsonb_object_agg(hub_id, block_rate)
    INTO v_hub_block_rates
    FROM (
        SELECT
            hub_id,
            ROUND((COUNT(*) FILTER (WHERE status IN ('FAIL', 'BLOCKED'))::numeric / NULLIF(COUNT(*), 0)) * 100, 2) as block_rate
        FROM outreach.company_hub_status
        GROUP BY hub_id
    ) br;

    -- Get freshness stats
    SELECT jsonb_object_agg(hub_id, stale_pct)
    INTO v_freshness_stats
    FROM outreach.vw_freshness_analysis;

    -- Insert snapshot
    INSERT INTO outreach.tier_snapshot_history (
        snapshot_date,
        total_companies,
        ineligible_count,
        tier_0_count,
        tier_1_count,
        tier_2_count,
        tier_3_count,
        blocked_count,
        complete_count,
        in_progress_count,
        hub_pass_rates,
        hub_block_rates,
        freshness_stats
    )
    SELECT
        CURRENT_DATE,
        total_companies,
        ineligible_count,
        tier_0_count,
        tier_1_count,
        tier_2_count,
        tier_3_count,
        blocked_total,
        complete_total,
        in_progress_total,
        COALESCE(v_hub_pass_rates, '{}'::JSONB),
        COALESCE(v_hub_block_rates, '{}'::JSONB),
        COALESCE(v_freshness_stats, '{}'::JSONB)
    FROM outreach.vw_tier_telemetry_summary
    ON CONFLICT (snapshot_date) DO UPDATE SET
        total_companies = EXCLUDED.total_companies,
        ineligible_count = EXCLUDED.ineligible_count,
        tier_0_count = EXCLUDED.tier_0_count,
        tier_1_count = EXCLUDED.tier_1_count,
        tier_2_count = EXCLUDED.tier_2_count,
        tier_3_count = EXCLUDED.tier_3_count,
        blocked_count = EXCLUDED.blocked_count,
        complete_count = EXCLUDED.complete_count,
        in_progress_count = EXCLUDED.in_progress_count,
        hub_pass_rates = EXCLUDED.hub_pass_rates,
        hub_block_rates = EXCLUDED.hub_block_rates,
        freshness_stats = EXCLUDED.freshness_stats,
        created_at = NOW()
    RETURNING snapshot_id INTO v_snapshot_id;

    RETURN v_snapshot_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION outreach.fn_capture_tier_snapshot() IS
'Captures a daily snapshot of tier distribution and hub metrics. Can be called multiple times per day (upserts).';

-- =============================================================================
-- VIEW 6: TIER DRIFT ANALYSIS
-- =============================================================================
-- Shows day-over-day changes in tier distribution

CREATE OR REPLACE VIEW outreach.vw_tier_drift_analysis AS
WITH recent_snapshots AS (
    SELECT *
    FROM outreach.tier_snapshot_history
    ORDER BY snapshot_date DESC
    LIMIT 7
),
with_lag AS (
    SELECT
        snapshot_date,
        total_companies,
        ineligible_count,
        tier_0_count,
        tier_1_count,
        tier_2_count,
        tier_3_count,
        LAG(ineligible_count) OVER (ORDER BY snapshot_date) as prev_ineligible,
        LAG(tier_0_count) OVER (ORDER BY snapshot_date) as prev_tier_0,
        LAG(tier_1_count) OVER (ORDER BY snapshot_date) as prev_tier_1,
        LAG(tier_2_count) OVER (ORDER BY snapshot_date) as prev_tier_2,
        LAG(tier_3_count) OVER (ORDER BY snapshot_date) as prev_tier_3,
        hub_pass_rates,
        hub_block_rates
    FROM recent_snapshots
)
SELECT
    snapshot_date,
    total_companies,
    -- Current counts
    ineligible_count,
    tier_0_count,
    tier_1_count,
    tier_2_count,
    tier_3_count,
    -- Day-over-day changes
    (ineligible_count - COALESCE(prev_ineligible, ineligible_count)) as ineligible_delta,
    (tier_0_count - COALESCE(prev_tier_0, tier_0_count)) as tier_0_delta,
    (tier_1_count - COALESCE(prev_tier_1, tier_1_count)) as tier_1_delta,
    (tier_2_count - COALESCE(prev_tier_2, tier_2_count)) as tier_2_delta,
    (tier_3_count - COALESCE(prev_tier_3, tier_3_count)) as tier_3_delta,
    -- Hub metrics
    hub_pass_rates,
    hub_block_rates
FROM with_lag
ORDER BY snapshot_date DESC;

COMMENT ON VIEW outreach.vw_tier_drift_analysis IS
'Read-only view showing day-over-day changes in tier distribution (last 7 days).';

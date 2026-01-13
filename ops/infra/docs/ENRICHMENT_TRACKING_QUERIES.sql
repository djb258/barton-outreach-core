-- ═══════════════════════════════════════════════════════════
-- ENRICHMENT TRACKING QUERIES FOR GRAFANA
-- ═══════════════════════════════════════════════════════════
-- Purpose: Monitor executive enrichment jobs (CFO/CEO/HR)
-- Tables: company_slot, data_enrichment_log, linkedin_refresh_jobs
-- Use: Copy these queries into Grafana panels
-- ═══════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════
-- QUERY 1: Executive Slots Pending Enrichment
-- ═══════════════════════════════════════════════════════════
-- Shows: Unfilled or unenriched executive slots that need attention
-- Panel Type: Table
-- Refresh: 30 seconds

SELECT
    cm.company_name AS "Company",
    cs.slot_type AS "Role",
    cs.is_filled AS "Is Filled",
    cs.filled_at AS "Filled Date",
    cs.last_refreshed_at AS "Last Refreshed",
    CASE
        WHEN cs.last_refreshed_at IS NULL THEN 'Never Enriched'
        WHEN cs.last_refreshed_at < NOW() - INTERVAL '7 days' THEN 'Stale (7+ days)'
        WHEN cs.last_refreshed_at < NOW() - INTERVAL '3 days' THEN 'Needs Refresh (3+ days)'
        ELSE 'Recent'
    END AS "Freshness Status",
    EXTRACT(DAY FROM NOW() - cs.last_refreshed_at)::INTEGER AS "Days Since Last Refresh",
    pm.full_name AS "Executive Name",
    pm.linkedin_url AS "LinkedIn URL",
    cm.company_unique_id AS "Company ID"
FROM marketing.company_slot cs
JOIN marketing.company_master cm ON cs.company_unique_id = cm.company_unique_id
LEFT JOIN marketing.people_master pm ON cs.person_unique_id = pm.unique_id
WHERE
    -- Focus on executive roles
    cs.slot_type IN ('CEO', 'CFO', 'HR')
    AND (
        -- Never enriched
        cs.last_refreshed_at IS NULL
        -- Or stale (>3 days old)
        OR cs.last_refreshed_at < NOW() - INTERVAL '3 days'
    )
ORDER BY
    CASE
        WHEN cs.last_refreshed_at IS NULL THEN 1
        ELSE 2
    END,
    cs.last_refreshed_at ASC NULLS FIRST,
    cm.company_name,
    cs.slot_type
LIMIT 100;

-- ═══════════════════════════════════════════════════════════
-- QUERY 2: Enrichment Jobs in Progress
-- ═══════════════════════════════════════════════════════════
-- Shows: Currently running enrichment jobs with duration
-- Panel Type: Table
-- Refresh: 10 seconds

SELECT
    cm.company_name AS "Company",
    del.agent_name AS "Agent",
    del.enrichment_type AS "Type",
    del.status AS "Status",
    del.started_at AS "Started",
    EXTRACT(MINUTE FROM NOW() - del.started_at)::INTEGER AS "Minutes Running",
    CASE
        WHEN NOW() - del.started_at > INTERVAL '10 minutes' THEN '⚠️ Slow'
        WHEN NOW() - del.started_at > INTERVAL '5 minutes' THEN '⚡ Normal'
        ELSE '✅ Fast'
    END AS "Performance",
    del.enrichment_id AS "Job ID"
FROM marketing.data_enrichment_log del
JOIN marketing.company_master cm ON del.company_unique_id = cm.company_unique_id
WHERE
    del.status IN ('pending', 'running')
    AND del.enrichment_type IN ('executive', 'linkedin', 'profile')
ORDER BY del.started_at ASC
LIMIT 50;

-- ═══════════════════════════════════════════════════════════
-- QUERY 3: Failed Enrichment Jobs (Last 24 Hours)
-- ═══════════════════════════════════════════════════════════
-- Shows: Failed enrichments that need retry
-- Panel Type: Table with red highlighting
-- Refresh: 1 minute

SELECT
    cm.company_name AS "Company",
    del.agent_name AS "Agent",
    del.enrichment_type AS "Type",
    del.status AS "Status",
    del.error_message AS "Error",
    del.started_at AS "Attempted At",
    EXTRACT(HOUR FROM NOW() - del.started_at)::INTEGER AS "Hours Ago",
    del.cost_credits AS "Credits Wasted",
    del.enrichment_id AS "Job ID",
    cm.company_unique_id AS "Company ID"
FROM marketing.data_enrichment_log del
JOIN marketing.company_master cm ON del.company_unique_id = cm.company_unique_id
WHERE
    del.status IN ('failed', 'timeout', 'rate_limited')
    AND del.created_at >= NOW() - INTERVAL '24 hours'
    AND del.enrichment_type IN ('executive', 'linkedin', 'profile')
ORDER BY del.created_at DESC
LIMIT 100;

-- ═══════════════════════════════════════════════════════════
-- QUERY 4: Enrichment Performance by Agent (Last 7 Days)
-- ═══════════════════════════════════════════════════════════
-- Shows: Agent success rates and average duration
-- Panel Type: Table or Bar Chart
-- Refresh: 5 minutes

SELECT
    del.agent_name AS "Agent",
    COUNT(*) AS "Total Jobs",
    COUNT(*) FILTER (WHERE del.status = 'success') AS "Successful",
    COUNT(*) FILTER (WHERE del.status = 'failed') AS "Failed",
    COUNT(*) FILTER (WHERE del.status = 'timeout') AS "Timeouts",
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE del.status = 'success') / NULLIF(COUNT(*), 0),
        1
    ) AS "Success Rate %",
    ROUND(
        AVG(EXTRACT(EPOCH FROM (del.completed_at - del.started_at)) / 60.0)
        FILTER (WHERE del.status = 'success' AND del.completed_at IS NOT NULL),
        1
    ) AS "Avg Duration (min)",
    ROUND(SUM(del.cost_credits), 2) AS "Total Credits",
    ROUND(
        SUM(del.cost_credits) / NULLIF(COUNT(*) FILTER (WHERE del.status = 'success'), 0),
        2
    ) AS "Credits Per Success",
    MAX(del.created_at) AS "Last Used"
FROM marketing.data_enrichment_log del
WHERE
    del.created_at >= NOW() - INTERVAL '7 days'
    AND del.enrichment_type IN ('executive', 'linkedin', 'profile')
GROUP BY del.agent_name
ORDER BY "Success Rate %" DESC, "Total Jobs" DESC;

-- ═══════════════════════════════════════════════════════════
-- QUERY 5: Executive Enrichment Timeline (Last 24 Hours)
-- ═══════════════════════════════════════════════════════════
-- Shows: Hourly enrichment volume and success rate
-- Panel Type: Time Series (Line Chart)
-- Refresh: 1 minute

SELECT
    DATE_TRUNC('hour', del.created_at) AS "time",
    COUNT(*) AS "Total Jobs",
    COUNT(*) FILTER (WHERE del.status = 'success') AS "Successful",
    COUNT(*) FILTER (WHERE del.status = 'failed') AS "Failed",
    COUNT(*) FILTER (WHERE del.status = 'running') AS "Running",
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE del.status = 'success') / NULLIF(COUNT(*), 0),
        1
    ) AS "Success Rate %"
FROM marketing.data_enrichment_log del
WHERE
    del.created_at >= NOW() - INTERVAL '24 hours'
    AND del.enrichment_type IN ('executive', 'linkedin', 'profile')
GROUP BY DATE_TRUNC('hour', del.created_at)
ORDER BY "time" ASC;

-- ═══════════════════════════════════════════════════════════
-- QUERY 6: Slow Enrichment Jobs (Currently Running > 5 min)
-- ═══════════════════════════════════════════════════════════
-- Shows: Jobs that are taking too long
-- Panel Type: Table with warning colors
-- Refresh: 30 seconds

SELECT
    cm.company_name AS "Company",
    del.agent_name AS "Agent",
    del.enrichment_type AS "Type",
    del.started_at AS "Started",
    EXTRACT(MINUTE FROM NOW() - del.started_at)::INTEGER AS "Minutes Running",
    CASE
        WHEN NOW() - del.started_at > INTERVAL '15 minutes' THEN '🔴 Critical'
        WHEN NOW() - del.started_at > INTERVAL '10 minutes' THEN '🟠 Warning'
        ELSE '🟡 Monitor'
    END AS "Urgency",
    del.enrichment_id AS "Job ID",
    cm.company_unique_id AS "Company ID"
FROM marketing.data_enrichment_log del
JOIN marketing.company_master cm ON del.company_unique_id = cm.company_unique_id
WHERE
    del.status IN ('pending', 'running')
    AND del.started_at < NOW() - INTERVAL '5 minutes'
    AND del.enrichment_type IN ('executive', 'linkedin', 'profile')
ORDER BY del.started_at ASC;

-- ═══════════════════════════════════════════════════════════
-- QUERY 7: LinkedIn Refresh Jobs Status
-- ═══════════════════════════════════════════════════════════
-- Shows: LinkedIn-specific refresh jobs (if using linkedin_refresh_jobs table)
-- Panel Type: Table
-- Refresh: 1 minute

SELECT
    pm.full_name AS "Executive",
    lrj.status AS "Status",
    lrj.requested_at AS "Requested",
    lrj.started_at AS "Started",
    lrj.completed_at AS "Completed",
    CASE
        WHEN lrj.status = 'completed' THEN
            EXTRACT(MINUTE FROM (lrj.completed_at - lrj.started_at))::INTEGER
        WHEN lrj.status IN ('pending', 'running') THEN
            EXTRACT(MINUTE FROM (NOW() - lrj.started_at))::INTEGER
        ELSE NULL
    END AS "Duration (min)",
    lrj.apify_run_id AS "Apify Run ID",
    lrj.error_message AS "Error",
    lrj.job_id AS "Job ID"
FROM public.linkedin_refresh_jobs lrj
JOIN marketing.people_master pm ON lrj.person_unique_id = pm.unique_id
WHERE lrj.requested_at >= NOW() - INTERVAL '24 hours'
ORDER BY lrj.requested_at DESC
LIMIT 100;

-- ═══════════════════════════════════════════════════════════
-- QUERY 8: Companies Without Any Executive Data
-- ═══════════════════════════════════════════════════════════
-- Shows: Companies that have never been enriched
-- Panel Type: Table (Priority Queue)
-- Refresh: 5 minutes

SELECT
    cm.company_name AS "Company",
    cm.industry AS "Industry",
    cm.employee_count AS "Employees",
    cm.created_at AS "Added On",
    EXTRACT(DAY FROM NOW() - cm.created_at)::INTEGER AS "Days in System",
    COUNT(cs.company_slot_unique_id) AS "Total Slots",
    COUNT(cs.company_slot_unique_id) FILTER (WHERE cs.is_filled = true) AS "Filled Slots",
    COUNT(cs.company_slot_unique_id) FILTER (WHERE cs.is_filled = false) AS "Empty Slots",
    CASE
        WHEN cm.created_at < NOW() - INTERVAL '7 days' THEN '🔴 Urgent'
        WHEN cm.created_at < NOW() - INTERVAL '3 days' THEN '🟠 High Priority'
        ELSE '🟢 Normal'
    END AS "Priority",
    cm.company_unique_id AS "Company ID"
FROM marketing.company_master cm
LEFT JOIN marketing.company_slot cs ON cm.company_unique_id = cs.company_unique_id
WHERE NOT EXISTS (
    SELECT 1
    FROM marketing.data_enrichment_log del
    WHERE del.company_unique_id = cm.company_unique_id
    AND del.enrichment_type IN ('executive', 'linkedin', 'profile')
)
GROUP BY cm.company_unique_id, cm.company_name, cm.industry, cm.employee_count, cm.created_at
ORDER BY
    CASE
        WHEN cm.created_at < NOW() - INTERVAL '7 days' THEN 1
        WHEN cm.created_at < NOW() - INTERVAL '3 days' THEN 2
        ELSE 3
    END,
    cm.created_at ASC
LIMIT 50;

-- ═══════════════════════════════════════════════════════════
-- QUERY 9: Enrichment Queue Summary (Real-Time Metrics)
-- ═══════════════════════════════════════════════════════════
-- Shows: High-level stats for monitoring
-- Panel Type: Stat panels (multiple single-value panels)
-- Refresh: 10 seconds

-- Total Pending Enrichments
SELECT COUNT(*) AS "Pending Jobs"
FROM marketing.data_enrichment_log
WHERE status = 'pending'
AND enrichment_type IN ('executive', 'linkedin', 'profile');

-- Currently Running
SELECT COUNT(*) AS "Running Jobs"
FROM marketing.data_enrichment_log
WHERE status = 'running'
AND enrichment_type IN ('executive', 'linkedin', 'profile');

-- Failed Last Hour
SELECT COUNT(*) AS "Failed (1h)"
FROM marketing.data_enrichment_log
WHERE status IN ('failed', 'timeout')
AND created_at >= NOW() - INTERVAL '1 hour'
AND enrichment_type IN ('executive', 'linkedin', 'profile');

-- Success Rate Today
SELECT
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0),
        1
    ) AS "Success Rate % (Today)"
FROM marketing.data_enrichment_log
WHERE created_at >= DATE_TRUNC('day', NOW())
AND enrichment_type IN ('executive', 'linkedin', 'profile');

-- Average Duration (Successful, Last Hour)
SELECT
    ROUND(
        AVG(EXTRACT(EPOCH FROM (completed_at - started_at)) / 60.0),
        1
    ) AS "Avg Duration (min)"
FROM marketing.data_enrichment_log
WHERE status = 'success'
AND completed_at >= NOW() - INTERVAL '1 hour'
AND enrichment_type IN ('executive', 'linkedin', 'profile');

-- ═══════════════════════════════════════════════════════════
-- QUERY 10: Executive Movement Detection (BIT Integration)
-- ═══════════════════════════════════════════════════════════
-- Shows: Enrichments that detected executive changes
-- Panel Type: Table with highlighting
-- Refresh: 1 minute

SELECT
    cm.company_name AS "Company",
    del.agent_name AS "Agent",
    del.movement_type AS "Movement Type",
    del.data_quality_score AS "Quality Score",
    del.completed_at AS "Detected At",
    EXTRACT(HOUR FROM NOW() - del.completed_at)::INTEGER AS "Hours Ago",
    del.result_data->>'executive' AS "Executive Name",
    del.result_data->>'title' AS "New Title",
    CASE
        WHEN EXISTS (
            SELECT 1 FROM bit.events be
            WHERE be.company_unique_id = cm.company_unique_id
            AND be.event_payload->>'movement_type' = del.movement_type
            AND be.detected_at >= del.completed_at - INTERVAL '5 minutes'
        ) THEN '✅ BIT Event Created'
        ELSE '⚠️ No BIT Event'
    END AS "BIT Status",
    del.enrichment_id AS "Job ID"
FROM marketing.data_enrichment_log del
JOIN marketing.company_master cm ON del.company_unique_id = cm.company_unique_id
WHERE
    del.movement_detected = true
    AND del.completed_at >= NOW() - INTERVAL '7 days'
ORDER BY del.completed_at DESC
LIMIT 50;

-- ═══════════════════════════════════════════════════════════
-- END OF ENRICHMENT TRACKING QUERIES
-- ═══════════════════════════════════════════════════════════
--
-- USAGE:
-- 1. Copy desired query
-- 2. Open Grafana panel editor
-- 3. Paste into SQL query field
-- 4. Select "Table" or "Time Series" visualization
-- 5. Configure refresh interval
-- 6. Save panel
--
-- RECOMMENDED DASHBOARD LAYOUT:
-- Row 1: Stat panels (Query 9 - real-time metrics)
-- Row 2: Query 1 (Pending enrichments) + Query 2 (In progress)
-- Row 3: Query 3 (Failed jobs) + Query 4 (Agent performance)
-- Row 4: Query 5 (Timeline chart - full width)
-- Row 5: Query 6 (Slow jobs) + Query 7 (LinkedIn jobs)
-- Row 6: Query 8 (Never enriched) + Query 10 (Movement detection)
--
-- ═══════════════════════════════════════════════════════════

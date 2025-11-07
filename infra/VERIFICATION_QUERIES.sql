-- ═══════════════════════════════════════════════════════════
-- SVG-PLE BIT + ENRICHMENT — VERIFICATION QUERIES
-- ═══════════════════════════════════════════════════════════
--
-- Purpose: Verify successful migration and test data flow
-- Run after: 2025-11-06-bit-enrichment.sql migration
-- Database: Neon PostgreSQL 15+
--
-- ═══════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════
-- 1. SCHEMA & TABLE VERIFICATION
-- ═══════════════════════════════════════════════════════════

-- Verify bit schema exists
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name = 'bit';
-- Expected: 1 row (bit)

-- Verify all tables created
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema IN ('bit', 'marketing')
  AND table_name IN ('rule_reference', 'events', 'data_enrichment_log')
ORDER BY table_schema, table_name;
-- Expected: 3 rows

-- Verify all views created
SELECT table_schema, table_name
FROM information_schema.views
WHERE table_schema IN ('bit', 'marketing')
  AND table_name IN ('scores', 'data_enrichment_summary')
ORDER BY table_schema, table_name;
-- Expected: 2 rows

-- ═══════════════════════════════════════════════════════════
-- 2. INDEX VERIFICATION
-- ═══════════════════════════════════════════════════════════

-- Verify bit.events indexes (should have 7)
SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'bit' AND tablename = 'events'
ORDER BY indexname;
-- Expected: 7 rows

-- Verify marketing.data_enrichment_log indexes (should have 9)
SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'marketing' AND tablename = 'data_enrichment_log'
ORDER BY indexname;
-- Expected: 9 rows

-- ═══════════════════════════════════════════════════════════
-- 3. SEED DATA VERIFICATION
-- ═══════════════════════════════════════════════════════════

-- Verify BIT rules seeded (should have 15)
SELECT
    rule_id,
    rule_name,
    category,
    weight,
    is_active
FROM bit.rule_reference
ORDER BY category, weight DESC;
-- Expected: 15 rows

-- Count rules by category
SELECT
    category,
    COUNT(*) as rule_count,
    SUM(weight) as total_weight,
    COUNT(*) FILTER (WHERE is_active = true) as active_rules
FROM bit.rule_reference
GROUP BY category
ORDER BY total_weight DESC;
-- Expected: 6 categories (renewal, executive, funding, hiring, growth, technology)

-- ═══════════════════════════════════════════════════════════
-- 4. FUNCTION & TRIGGER VERIFICATION
-- ═══════════════════════════════════════════════════════════

-- Verify functions exist
SELECT
    routine_schema,
    routine_name,
    routine_type
FROM information_schema.routines
WHERE routine_schema = 'bit'
  AND routine_name = 'trigger_movement_event';
-- Expected: 1 row

-- Verify triggers exist on data_enrichment_log
SELECT
    trigger_name,
    event_manipulation,
    event_object_table
FROM information_schema.triggers
WHERE event_object_schema = 'marketing'
  AND event_object_table = 'data_enrichment_log'
ORDER BY trigger_name;
-- Expected: 2 rows (updated_at trigger + movement trigger)

-- ═══════════════════════════════════════════════════════════
-- 5. TEST DATA INSERTION
-- ═══════════════════════════════════════════════════════════

-- Insert test company (if not exists)
INSERT INTO marketing.company_master (
    company_unique_id,
    company_name,
    website_url,
    industry,
    employee_count,
    source_system
)
VALUES (
    '04.04.01.01.00001.001',
    'Acme Corporation',
    'https://acme.example.com',
    'Software',
    500,
    'test'
)
ON CONFLICT (company_unique_id) DO NOTHING;

-- Insert test enrichment log entry WITH movement detection
INSERT INTO marketing.data_enrichment_log (
    company_unique_id,
    agent_name,
    enrichment_type,
    status,
    data_quality_score,
    cost_credits,
    cost_usd,
    movement_detected,
    movement_type,
    result_data,
    started_at,
    completed_at
)
VALUES (
    '04.04.01.01.00001.001',
    'linkedin_enrichment_agent',
    'executive',
    'success',
    95.00,
    2.5,
    0.25,
    true,  -- This should trigger BIT event creation
    'New CEO hired',
    '{"executive": "John Smith", "title": "CEO", "start_date": "2025-11-01"}',
    NOW() - INTERVAL '1 hour',
    NOW() - INTERVAL '30 minutes'
);

-- Verify trigger created BIT event automatically
SELECT
    e.event_id,
    e.company_unique_id,
    r.rule_name,
    e.weight,
    e.detection_source,
    e.detected_at,
    e.event_payload
FROM bit.events e
JOIN bit.rule_reference r ON e.rule_id = r.rule_id
WHERE e.company_unique_id = '04.04.01.01.00001.001'
ORDER BY e.detected_at DESC;
-- Expected: At least 1 row (executive_movement event auto-created)

-- ═══════════════════════════════════════════════════════════
-- 6. VIEW VERIFICATION
-- ═══════════════════════════════════════════════════════════

-- Test bit.scores view
SELECT
    company_unique_id,
    company_name,
    total_score,
    score_tier,
    signal_count,
    renewal_signals,
    hiring_signals,
    last_signal_at
FROM bit.scores
WHERE company_unique_id = '04.04.01.01.00001.001';
-- Expected: 1 row with total_score > 0

-- Test marketing.data_enrichment_summary view
SELECT
    agent_name,
    enrichment_type,
    total_attempts,
    successful_attempts,
    success_rate_pct,
    avg_cost_per_success_usd,
    avg_quality_score,
    movement_detection_count
FROM marketing.data_enrichment_summary
WHERE agent_name = 'linkedin_enrichment_agent';
-- Expected: 1 row with success_rate_pct = 100.00

-- ═══════════════════════════════════════════════════════════
-- 7. SCORING LOGIC VERIFICATION
-- ═══════════════════════════════════════════════════════════

-- Insert multiple BIT events to test scoring
INSERT INTO bit.events (company_unique_id, rule_id, weight, event_payload, detection_source)
SELECT
    '04.04.01.01.00001.001',
    rule_id,
    weight,
    '{"test": true}',
    'manual_test'
FROM bit.rule_reference
WHERE rule_name IN ('renewal_window_120d', 'funding_announced', 'hiring_spike')
  AND is_active = true;

-- Verify score calculation (90-day rolling window)
SELECT
    company_name,
    total_score,
    score_tier,
    signal_count,
    renewal_signals,
    hiring_signals
FROM bit.scores
WHERE company_unique_id = '04.04.01.01.00001.001';
-- Expected: total_score should be sum of weights from inserted events

-- ═══════════════════════════════════════════════════════════
-- 8. PERFORMANCE VERIFICATION
-- ═══════════════════════════════════════════════════════════

-- Test index usage on bit.events
EXPLAIN ANALYZE
SELECT * FROM bit.events
WHERE company_unique_id = '04.04.01.01.00001.001'
  AND detected_at >= NOW() - INTERVAL '90 days';
-- Expected: Should use idx_events_company_detected index

-- Test index usage on data_enrichment_log
EXPLAIN ANALYZE
SELECT * FROM marketing.data_enrichment_log
WHERE company_unique_id = '04.04.01.01.00001.001'
  AND status = 'success';
-- Expected: Should use idx_enrichment_company_status index

-- Test JSONB GIN index usage
EXPLAIN ANALYZE
SELECT * FROM bit.events
WHERE event_payload @> '{"test": true}';
-- Expected: Should use idx_events_payload_gin index

-- ═══════════════════════════════════════════════════════════
-- 9. GRAFANA DASHBOARD QUERIES
-- ═══════════════════════════════════════════════════════════

-- Panel 1: BIT Heatmap (Top 100 scored companies)
SELECT
    company_name,
    cm.industry,
    total_score,
    score_tier,
    signal_count,
    renewal_signals,
    hiring_signals,
    last_signal_at
FROM bit.scores s
JOIN marketing.company_master cm ON s.company_unique_id = cm.company_unique_id
WHERE total_score > 0
ORDER BY total_score DESC
LIMIT 100;

-- Panel 2: Enrichment ROI (Cost per success by agent)
SELECT
    agent_name,
    enrichment_type,
    total_attempts,
    successful_attempts,
    success_rate_pct,
    avg_cost_per_success_usd,
    total_cost_usd,
    avg_quality_score,
    movement_detection_count
FROM marketing.data_enrichment_summary
WHERE successful_attempts > 0
ORDER BY avg_cost_per_success_usd ASC;

-- Panel 3: Renewal Pipeline (Next 120 days)
WITH renewal_calc AS (
    SELECT
        cm.company_unique_id,
        cm.company_name,
        cm.created_at,
        cm.created_at + INTERVAL '1 year' AS next_renewal_date,
        EXTRACT(DAY FROM (cm.created_at + INTERVAL '1 year') - NOW()) AS days_until_renewal,
        COUNT(cs.company_slot_unique_id) AS total_slots,
        COUNT(cs.company_slot_unique_id) FILTER (WHERE cs.is_filled = true) AS filled_slots,
        s.total_score,
        s.score_tier
    FROM marketing.company_master cm
    LEFT JOIN marketing.company_slot cs ON cm.company_unique_id = cs.company_unique_id
    LEFT JOIN bit.scores s ON cm.company_unique_id = s.company_unique_id
    GROUP BY cm.company_unique_id, cm.company_name, cm.created_at, s.total_score, s.score_tier
)
SELECT
    company_name,
    next_renewal_date,
    ROUND(days_until_renewal::numeric, 0) AS days_until_renewal,
    filled_slots || '/' || total_slots AS slots_filled,
    COALESCE(total_score, 0) AS bit_score,
    COALESCE(score_tier, 'unscored') AS score_tier,
    CASE
        WHEN days_until_renewal <= 30 THEN 'urgent'
        WHEN days_until_renewal <= 60 THEN 'high'
        WHEN days_until_renewal <= 90 THEN 'medium'
        ELSE 'low'
    END AS urgency
FROM renewal_calc
WHERE days_until_renewal <= 120
ORDER BY days_until_renewal ASC;

-- Panel 4: Score Distribution (donut chart)
SELECT
    score_tier,
    COUNT(*) AS company_count
FROM bit.scores
GROUP BY score_tier
ORDER BY
    CASE score_tier
        WHEN 'hot' THEN 1
        WHEN 'warm' THEN 2
        WHEN 'cold' THEN 3
        WHEN 'unscored' THEN 4
    END;

-- Panel 5: Hot Companies (gauge)
SELECT COUNT(*) AS hot_company_count
FROM bit.scores
WHERE score_tier = 'hot';

-- Panel 6: Signal Types (bar chart)
SELECT
    rr.category AS signal_type,
    COUNT(e.event_id) AS signal_count
FROM bit.events e
JOIN bit.rule_reference rr ON e.rule_id = rr.rule_id
WHERE e.detected_at >= NOW() - INTERVAL '90 days'
GROUP BY rr.category
ORDER BY signal_count DESC;

-- ═══════════════════════════════════════════════════════════
-- 10. CLEANUP TEST DATA (OPTIONAL)
-- ═══════════════════════════════════════════════════════════

-- Uncomment to remove test data
-- DELETE FROM bit.events WHERE company_unique_id = '04.04.01.01.00001.001';
-- DELETE FROM marketing.data_enrichment_log WHERE company_unique_id = '04.04.01.01.00001.001';
-- DELETE FROM marketing.company_master WHERE company_unique_id = '04.04.01.01.00001.001';

-- ═══════════════════════════════════════════════════════════
-- ✅ VERIFICATION COMPLETE
-- ═══════════════════════════════════════════════════════════
--
-- Expected Results Summary:
-- • bit schema: 1 table (rule_reference), 1 table (events), 1 view (scores)
-- • marketing schema: 1 table (data_enrichment_log), 1 view (data_enrichment_summary)
-- • Total indexes: 16 (7 on events, 9 on enrichment_log)
-- • Total rules seeded: 15
-- • Total functions: 1 (trigger_movement_event)
-- • Total triggers: 2 (updated_at + movement detection)
-- • Grafana queries: All 6 panels operational
--
-- 🎯 Next Steps:
-- 1. Import Grafana dashboard: infra/grafana/svg-ple-dashboard.json
-- 2. Configure Neon datasource in Grafana
-- 3. Set dashboard refresh to 30 seconds
-- 4. Monitor BIT scores and enrichment ROI
--
-- ═══════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════
-- Migration: Form 5500 Projection Layer (READ-ONLY VIEWS)
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Version: 1.0.0
-- Date: 2025-01-01
-- Doctrine: /doctrine/ple/5500_PROJECTION_LAYER.md
--
-- Purpose:
--   Create read-only projection views for Form 5500 / 5500-EZ data.
--   Allows downstream systems (Renewal, Outreach, Analytics) to pull
--   renewal month signals and Schedule A / EZ facts ON DEMAND.
--
-- DOCTRINE RULES (LOCKED):
--   ❌ Do NOT modify the DOL Subhub
--   ❌ Do NOT write new tables
--   ❌ Do NOT infer beyond filed dates
--   ❌ Do NOT guess renewal logic
--   ✅ Use SQL views only
--   ✅ All derived values explicitly tagged
--   ✅ Ambiguity → NULL, not assumptions
--
-- JOIN DISCIPLINE:
--   EIN linkage → 5500 filings → Projection views
--   No reverse joins. No lateral enrichment.
--
-- ═══════════════════════════════════════════════════════════════════════════

-- Create analytics schema if not exists
CREATE SCHEMA IF NOT EXISTS analytics;

COMMENT ON SCHEMA analytics IS 'Read-only projection views for downstream analytics and campaign targeting';

-- ═══════════════════════════════════════════════════════════════════════════
-- VIEW 1: analytics.v_5500_renewal_month
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Purpose: Extract renewal month from Form 5500 filings
--
-- Renewal Month Logic (MANDATORY):
--   Priority 1: Schedule A → insurance contract / coverage period end date
--               confidence = 'DECLARED'
--   Priority 2: 5500-EZ → plan year end date
--               confidence = 'INFERRED'
--   Priority 3: Multiple conflicting dates in same filing year
--               renewal_month = NULL
--               confidence = 'AMBIGUOUS'
--
-- Derivation rule:
--   renewal_month = EXTRACT(MONTH FROM coverage_end_date)
--   No offsets. No +1 month logic. No smoothing.
--
-- ═══════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW analytics.v_5500_renewal_month AS
WITH schedule_a_dates AS (
    -- Priority 1: Schedule A insurance contract end dates (DECLARED)
    SELECT
        el.company_unique_id,
        el.ein,
        sa.filing_year,
        'SCHEDULE_A' AS source_form,
        sa.coverage_end_date,
        EXTRACT(MONTH FROM sa.coverage_end_date)::INTEGER AS renewal_month,
        'DECLARED' AS confidence,
        sa.record_id AS source_record_id,
        ROW_NUMBER() OVER (
            PARTITION BY el.company_unique_id, sa.filing_year
            ORDER BY sa.coverage_end_date DESC
        ) AS rn,
        COUNT(*) OVER (
            PARTITION BY el.company_unique_id, sa.filing_year
        ) AS date_count
    FROM dol.ein_linkage el
    INNER JOIN dol.form_5500_schedule_a sa ON el.ein = sa.ein
    WHERE sa.coverage_end_date IS NOT NULL
),
ez_dates AS (
    -- Priority 2: 5500-EZ plan year end dates (INFERRED)
    SELECT
        el.company_unique_id,
        el.ein,
        ez.filing_year,
        'EZ' AS source_form,
        ez.plan_year_end_date AS coverage_end_date,
        EXTRACT(MONTH FROM ez.plan_year_end_date)::INTEGER AS renewal_month,
        'INFERRED' AS confidence,
        ez.record_id AS source_record_id,
        ROW_NUMBER() OVER (
            PARTITION BY el.company_unique_id, ez.filing_year
            ORDER BY ez.plan_year_end_date DESC
        ) AS rn,
        COUNT(*) OVER (
            PARTITION BY el.company_unique_id, ez.filing_year
        ) AS date_count
    FROM dol.ein_linkage el
    INNER JOIN dol.form_5500_ez ez ON el.ein = ez.ein
    WHERE ez.plan_year_end_date IS NOT NULL
      -- Only include EZ if no Schedule A exists for same company/year
      AND NOT EXISTS (
          SELECT 1 FROM dol.form_5500_schedule_a sa
          WHERE sa.ein = el.ein
            AND sa.filing_year = ez.filing_year
            AND sa.coverage_end_date IS NOT NULL
      )
),
combined AS (
    SELECT * FROM schedule_a_dates
    UNION ALL
    SELECT * FROM ez_dates
)
SELECT
    company_unique_id,
    ein,
    filing_year,
    source_form,
    coverage_end_date,
    -- If multiple conflicting dates, set renewal_month to NULL
    CASE
        WHEN date_count > 1 AND rn > 1 THEN NULL
        WHEN date_count > 1 THEN renewal_month  -- Keep first, mark ambiguous
        ELSE renewal_month
    END AS renewal_month,
    -- Confidence flag
    CASE
        WHEN date_count > 1 THEN 'AMBIGUOUS'
        ELSE confidence
    END AS confidence,
    source_record_id,
    NOW() AS created_at
FROM combined
WHERE rn = 1  -- Only first record per company/year
ORDER BY company_unique_id, filing_year DESC;

COMMENT ON VIEW analytics.v_5500_renewal_month IS 'READ-ONLY: Renewal month extracted from Form 5500 filings. Confidence flags MUST be respected by consumers.';
COMMENT ON COLUMN analytics.v_5500_renewal_month.company_unique_id IS 'From EIN linkage (dol.ein_linkage)';
COMMENT ON COLUMN analytics.v_5500_renewal_month.renewal_month IS 'INTEGER 1-12 derived from coverage_end_date. NULL if ambiguous.';
COMMENT ON COLUMN analytics.v_5500_renewal_month.confidence IS 'DECLARED (Schedule A) | INFERRED (EZ) | AMBIGUOUS (conflicting dates)';

-- ═══════════════════════════════════════════════════════════════════════════
-- VIEW 2: analytics.v_5500_insurance_facts
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Purpose: General-purpose projection view for Schedule A / EZ fields
--          Allows ANY downstream system to pull insurance facts ON DEMAND
--          without touching raw tables.
--
-- No transformations. No scoring. No enrichment.
--
-- ═══════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW analytics.v_5500_insurance_facts AS
-- Schedule A facts
SELECT
    el.company_unique_id,
    el.ein,
    sa.filing_year,
    'SCHEDULE_A' AS source_form,
    sa.insurer_name,
    sa.insurer_ein,
    sa.policy_number,
    sa.coverage_start_date,
    sa.coverage_end_date,
    sa.funding_type,
    sa.commissions,
    sa.record_id AS source_record_id,
    NOW() AS created_at
FROM dol.ein_linkage el
INNER JOIN dol.form_5500_schedule_a sa ON el.ein = sa.ein

UNION ALL

-- 5500-EZ facts (limited fields)
SELECT
    el.company_unique_id,
    el.ein,
    ez.filing_year,
    'EZ' AS source_form,
    NULL AS insurer_name,       -- EZ does not have insurer details
    NULL AS insurer_ein,
    NULL AS policy_number,
    ez.plan_year_start_date AS coverage_start_date,
    ez.plan_year_end_date AS coverage_end_date,
    ez.funding_type,
    NULL AS commissions,        -- EZ does not have commissions
    ez.record_id AS source_record_id,
    NOW() AS created_at
FROM dol.ein_linkage el
INNER JOIN dol.form_5500_ez ez ON el.ein = ez.ein

ORDER BY company_unique_id, filing_year DESC, source_form;

COMMENT ON VIEW analytics.v_5500_insurance_facts IS 'READ-ONLY: General-purpose projection of Schedule A and 5500-EZ insurance facts. No transformations, no scoring.';
COMMENT ON COLUMN analytics.v_5500_insurance_facts.source_form IS 'SCHEDULE_A or EZ - determines which fields are populated';
COMMENT ON COLUMN analytics.v_5500_insurance_facts.insurer_name IS 'From Schedule A only. NULL for EZ filings.';
COMMENT ON COLUMN analytics.v_5500_insurance_facts.commissions IS 'Raw value as filed. NULL if not present or EZ filing.';

-- ═══════════════════════════════════════════════════════════════════════════
-- VERIFICATION QUERIES
-- ═══════════════════════════════════════════════════════════════════════════

-- Verify views created
-- SELECT viewname FROM pg_views WHERE schemaname = 'analytics' AND viewname LIKE 'v_5500%';
-- Expected: v_5500_renewal_month, v_5500_insurance_facts

-- Sample renewal month query (campaigns can target renewal_month = 6)
-- SELECT * FROM analytics.v_5500_renewal_month
-- WHERE renewal_month = 6
--   AND confidence IN ('DECLARED', 'INFERRED')
--   AND filing_year >= EXTRACT(YEAR FROM NOW()) - 2;

-- Sample insurance facts query (carrier + coverage windows)
-- SELECT * FROM analytics.v_5500_insurance_facts
-- WHERE company_unique_id = '04.04.02.04.30000.042'
-- ORDER BY filing_year DESC;

-- ═══════════════════════════════════════════════════════════════════════════
-- SOURCE TABLE STUBS (REQUIRED IF NOT EXISTS)
-- ═══════════════════════════════════════════════════════════════════════════
-- NOTE: These are stub definitions. Replace with actual table references
-- based on your 5500 corpus ingestion. The views above assume these exist.
--
-- If your 5500 data is in different tables, update the view JOINs accordingly.
-- The column names are based on standard DOL EFAST2 field mappings.
-- ═══════════════════════════════════════════════════════════════════════════

-- Stub: dol.form_5500_schedule_a (if not exists)
-- CREATE TABLE IF NOT EXISTS dol.form_5500_schedule_a (
--     record_id VARCHAR(50) PRIMARY KEY,
--     ein VARCHAR(10) NOT NULL,
--     filing_year INTEGER NOT NULL,
--     insurer_name TEXT,
--     insurer_ein VARCHAR(10),
--     policy_number TEXT,
--     coverage_start_date DATE,
--     coverage_end_date DATE,
--     funding_type TEXT,
--     commissions NUMERIC,
--     created_at TIMESTAMPTZ DEFAULT NOW()
-- );

-- Stub: dol.form_5500_ez (if not exists)
-- CREATE TABLE IF NOT EXISTS dol.form_5500_ez (
--     record_id VARCHAR(50) PRIMARY KEY,
--     ein VARCHAR(10) NOT NULL,
--     filing_year INTEGER NOT NULL,
--     plan_year_start_date DATE,
--     plan_year_end_date DATE,
--     funding_type TEXT,
--     created_at TIMESTAMPTZ DEFAULT NOW()
-- );

-- ═══════════════════════════════════════════════════════════════════════════
-- END OF MIGRATION
-- ═══════════════════════════════════════════════════════════════════════════

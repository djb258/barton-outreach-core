-- Migration: CT Postal Code Repair via DOL Evidence
-- Date: 2026-02-10
-- ADR: docs/adr/ADR-CT-ZIP-REPAIR-VIA-DOL-EVIDENCE.md
-- Purpose: Add tracking columns to CT, create evidence + repair candidate views.
--          DOL ZIPs are evidence, not authority. CT remains sole ZIP authority.

-- ============================================================================
-- Step 1: Add tracking columns to outreach.company_target
-- These track WHERE a postal_code came from and WHEN it was repaired.
-- ============================================================================
ALTER TABLE outreach.company_target
    ADD COLUMN IF NOT EXISTS postal_code_source TEXT,
    ADD COLUMN IF NOT EXISTS postal_code_updated_at TIMESTAMPTZ;

COMMENT ON COLUMN outreach.company_target.postal_code_source IS 'Provenance of postal_code: HUNTER (original enrichment), DOL_5500 (repaired from Form 5500 sponsor ZIP), MANUAL';
COMMENT ON COLUMN outreach.company_target.postal_code_updated_at IS 'Timestamp of last postal_code update (NULL for original load values)';

-- ============================================================================
-- Step 2: Evidence aggregation view
-- Groups DOL sponsor ZIPs by outreach_id from THREE sources:
--   1. form_5500 sponsor MAILING ZIP (99.9% filled, 432K rows)
--   2. form_5500 sponsor LOCATION ZIP (3.5% filled, 15K rows)
--   3. form_5500_sf sponsor ZIP (100% filled, 1.5M rows — small plans)
-- READ-ONLY. Not registered in CTB.
-- ============================================================================
CREATE OR REPLACE VIEW outreach.v_dol_zip_evidence AS
WITH raw_evidence AS (
    -- Source 1: form_5500 sponsor MAILING ZIP (primary — 99.9% fill)
    SELECT
        d.outreach_id,
        LEFT(TRIM(f.spons_dfe_mail_us_zip), 5) AS zip_candidate,
        f.spons_dfe_loc_us_city AS dol_city,
        f.spons_dfe_loc_us_state AS dol_state,
        f.form_year,
        'F5500_MAIL' AS evidence_source
    FROM outreach.dol d
    JOIN dol.form_5500 f ON f.spons_dfe_ein = d.ein
    WHERE f.spons_dfe_mail_us_zip IS NOT NULL
      AND LEFT(TRIM(f.spons_dfe_mail_us_zip), 5) ~ '^\d{5}$'

    UNION ALL

    -- Source 2: form_5500 sponsor LOCATION ZIP (3.5% fill — higher trust)
    SELECT
        d.outreach_id,
        LEFT(TRIM(f.spons_dfe_loc_us_zip), 5) AS zip_candidate,
        f.spons_dfe_loc_us_city AS dol_city,
        f.spons_dfe_loc_us_state AS dol_state,
        f.form_year,
        'F5500_LOC' AS evidence_source
    FROM outreach.dol d
    JOIN dol.form_5500 f ON f.spons_dfe_ein = d.ein
    WHERE f.spons_dfe_loc_us_zip IS NOT NULL
      AND LEFT(TRIM(f.spons_dfe_loc_us_zip), 5) ~ '^\d{5}$'

    UNION ALL

    -- Source 3: form_5500_sf sponsor ZIP (100% fill — small plans)
    SELECT
        d.outreach_id,
        LEFT(TRIM(sf.sf_spons_us_zip), 5) AS zip_candidate,
        sf.sf_spons_us_city AS dol_city,
        sf.sf_spons_us_state AS dol_state,
        sf.form_year,
        'F5500_SF' AS evidence_source
    FROM outreach.dol d
    JOIN dol.form_5500_sf sf ON sf.sf_spons_ein = d.ein
    WHERE sf.sf_spons_us_zip IS NOT NULL
      AND LEFT(TRIM(sf.sf_spons_us_zip), 5) ~ '^\d{5}$'
)
SELECT
    outreach_id,
    zip_candidate,
    -- Pick city/state from most common evidence row per group
    (ARRAY_AGG(dol_city ORDER BY form_year DESC NULLS LAST))[1] AS dol_city,
    (ARRAY_AGG(dol_state ORDER BY form_year DESC NULLS LAST))[1] AS dol_state,
    COUNT(*) AS occurrence_count,
    MIN(form_year) AS first_year_seen,
    MAX(form_year) AS last_year_seen,
    COUNT(DISTINCT form_year) AS years_seen,
    COUNT(DISTINCT evidence_source) AS source_count
FROM raw_evidence
GROUP BY outreach_id, zip_candidate;

COMMENT ON VIEW outreach.v_dol_zip_evidence IS 'DOL sponsor ZIP evidence from form_5500 (mailing + location) and form_5500_sf, aggregated per outreach_id. READ-ONLY. Not a CTB truth surface.';

-- ============================================================================
-- Step 3: Repair candidate view
-- CT companies missing postal_code WHERE DOL evidence exists.
-- Picks the best ZIP candidate per company using occurrence + recency.
-- READ-ONLY. Not registered in CTB.
-- ============================================================================
CREATE OR REPLACE VIEW outreach.v_ct_zip_repair_candidates AS
WITH ranked AS (
    SELECT
        e.outreach_id,
        e.zip_candidate,
        e.dol_city,
        e.dol_state,
        e.occurrence_count,
        e.first_year_seen,
        e.last_year_seen,
        e.years_seen,
        -- Confidence: 1 point per occurrence + 2 points per year seen + 3 if last year >= 2024
        (e.occurrence_count + (e.years_seen * 2) +
         CASE WHEN e.last_year_seen::int >= 2024 THEN 3 ELSE 0 END
        ) AS confidence_score,
        ROW_NUMBER() OVER (
            PARTITION BY e.outreach_id
            ORDER BY
                e.years_seen DESC,
                e.last_year_seen DESC,
                e.occurrence_count DESC
        ) AS rank
    FROM outreach.v_dol_zip_evidence e
    JOIN outreach.company_target ct ON ct.outreach_id = e.outreach_id
    WHERE ct.postal_code IS NULL
       OR TRIM(ct.postal_code) = ''
)
SELECT
    r.outreach_id,
    r.zip_candidate AS proposed_postal_code,
    r.dol_city,
    r.dol_state,
    r.confidence_score,
    r.occurrence_count,
    r.first_year_seen,
    r.last_year_seen,
    r.years_seen,
    r.occurrence_count || ' filing(s), ' ||
        r.years_seen || ' year(s): ' ||
        r.first_year_seen ||
        CASE WHEN r.first_year_seen != r.last_year_seen
             THEN '-' || r.last_year_seen ELSE '' END
    AS evidence_summary
FROM ranked r
WHERE r.rank = 1;

COMMENT ON VIEW outreach.v_ct_zip_repair_candidates IS 'CT companies missing postal_code with DOL ZIP evidence. Best candidate per company ranked by recency + occurrence. READ-ONLY.';

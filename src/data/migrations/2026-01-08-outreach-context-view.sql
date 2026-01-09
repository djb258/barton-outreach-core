-- =============================================================================
-- OUTREACH CONTEXT VIEW (READ-ONLY WATERFALL)
-- =============================================================================
-- Date: 2026-01-08
-- Purpose: Cumulative, read-only view of outreach execution state
--
-- DOCTRINE:
--   - outreach_id is minted once (by Outreach Spine)
--   - Subhubs write append-only rows keyed by outreach_id
--   - No subhub mutates another subhub's data
--   - This view exposes the latest known outreach footprint
--
-- HARD LAW:
--   - SELECT only. No INSERT, UPDATE, DELETE.
--   - Subhubs may READ this view.
--   - Subhubs may NOT WRITE to it.
--   - Views are cumulative, not authoritative for business logic.
-- =============================================================================

-- =============================================================================
-- VIEW: outreach.v_context_current
-- =============================================================================
-- Returns the current execution context for each outreach_id.
-- Joins spine + all subhub outputs into a single read-only snapshot.

CREATE OR REPLACE VIEW outreach.v_context_current AS
SELECT
    -- =========================================================================
    -- SPINE (Identity + Base Context)
    -- =========================================================================
    o.outreach_id,
    o.sovereign_id,                    -- Receipt to CL (subhubs DON'T use this)
    o.domain,                          -- Denormalized from CL
    o.created_at AS spine_created_at,
    o.updated_at AS spine_updated_at,

    -- =========================================================================
    -- COMPANY TARGET (Execution Readiness)
    -- =========================================================================
    ct.execution_status AS ct_status,
    ct.email_method AS ct_email_method,
    ct.method_type AS ct_method_type,
    ct.confidence_score AS ct_confidence,
    ct.is_catchall AS ct_is_catchall,
    ct.imo_completed_at AS ct_completed_at,

    -- =========================================================================
    -- DOL FILINGS (EIN + Filing Signals)
    -- =========================================================================
    dol.ein AS dol_ein,
    dol.filing_year AS dol_filing_year,
    dol.total_participants AS dol_participants,
    dol.total_assets AS dol_assets,
    dol.created_at AS dol_created_at,

    -- =========================================================================
    -- PEOPLE INTELLIGENCE (Slot State)
    -- =========================================================================
    (SELECT COUNT(*) FROM outreach.people p WHERE p.outreach_id = o.outreach_id) AS people_count,
    (SELECT COUNT(*) FROM outreach.people p WHERE p.outreach_id = o.outreach_id AND p.email_verified = true) AS people_verified_count,

    -- =========================================================================
    -- BLOG CONTENT (Content Signals)
    -- =========================================================================
    (SELECT COUNT(*) FROM outreach.blog b WHERE b.outreach_id = o.outreach_id) AS blog_signal_count,

    -- =========================================================================
    -- WATERFALL STATE (Derived)
    -- =========================================================================
    CASE
        WHEN ct.execution_status IS NULL THEN 'PENDING_CT'
        WHEN ct.execution_status = 'failed' THEN 'BLOCKED_CT'
        WHEN dol.ein IS NULL THEN 'PENDING_DOL'
        WHEN (SELECT COUNT(*) FROM outreach.people p WHERE p.outreach_id = o.outreach_id) = 0 THEN 'PENDING_PEOPLE'
        ELSE 'READY'
    END AS waterfall_state,

    -- =========================================================================
    -- TIMESTAMPS
    -- =========================================================================
    GREATEST(
        o.updated_at,
        ct.imo_completed_at,
        dol.created_at,
        (SELECT MAX(created_at) FROM outreach.people p WHERE p.outreach_id = o.outreach_id),
        (SELECT MAX(created_at) FROM outreach.blog b WHERE b.outreach_id = o.outreach_id)
    ) AS last_activity_at

FROM outreach.outreach o
LEFT JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
LEFT JOIN outreach.dol dol ON dol.outreach_id = o.outreach_id;

-- =============================================================================
-- COMMENT ON VIEW
-- =============================================================================
COMMENT ON VIEW outreach.v_context_current IS
'OUT.VIEW.CONTEXT | Read-only cumulative view of outreach execution state.
SELECT ONLY. Subhubs may read this view but MUST NOT attempt to write.
This view is observational, not authoritative for business logic.';

-- =============================================================================
-- GRANT SELECT ONLY
-- =============================================================================
-- Revoke any write permissions (belt and suspenders)
REVOKE INSERT, UPDATE, DELETE ON outreach.v_context_current FROM PUBLIC;

-- =============================================================================
-- VERIFICATION QUERY
-- =============================================================================
-- Run this after migration to verify the view works:
--
-- SELECT
--     outreach_id,
--     domain,
--     ct_status,
--     waterfall_state,
--     last_activity_at
-- FROM outreach.v_context_current
-- LIMIT 10;

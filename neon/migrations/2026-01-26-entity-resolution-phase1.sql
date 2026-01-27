-- ============================================================================
-- Entity Resolution Phase 1: CL outreach_id Backfill + Domain Normalization
-- ============================================================================
-- Authority: ADR-017 (BIT v2.0)
-- Purpose: Fix entity resolution gaps blocking BIT pressure signal generation
-- Impact: Enable 73% of outreach records to reach EIN data
--
-- SAFETY: All operations are idempotent (safe to re-run)
-- ============================================================================

BEGIN;

-- ============================================================================
-- STEP 1: Backfill cl.company_identity.outreach_id
-- ============================================================================
-- Per CL doctrine, outreach_id should be written ONCE to CL when outreach
-- mints the ID. This was not happening, leaving 51,910 records without linkage.
--
-- This backfill writes outreach_id for companies that:
-- 1. Have a sovereign_company_id matching outreach.outreach.sovereign_id
-- 2. Don't already have an outreach_id (idempotent)
-- ============================================================================

DO $$
DECLARE
    v_updated INTEGER;
BEGIN
    RAISE NOTICE 'STEP 1: Backfilling cl.company_identity.outreach_id...';

    UPDATE cl.company_identity ci
    SET
        outreach_id = o.outreach_id,
        outreach_attached_at = COALESCE(ci.outreach_attached_at, NOW())
    FROM outreach.outreach o
    WHERE ci.sovereign_company_id = o.sovereign_id
      AND ci.outreach_id IS NULL;

    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RAISE NOTICE 'CL outreach_id backfilled: % records', v_updated;
END $$;

-- ============================================================================
-- STEP 2: Create domain normalization function
-- ============================================================================
-- CL stores domains with protocol (http://domain.com)
-- Outreach stores bare domains (domain.com)
-- This function normalizes to bare domain format
-- ============================================================================

CREATE OR REPLACE FUNCTION public.normalize_domain(p_domain TEXT)
RETURNS TEXT AS $$
BEGIN
    IF p_domain IS NULL THEN
        RETURN NULL;
    END IF;

    -- Remove protocol prefixes
    RETURN LOWER(
        REGEXP_REPLACE(
            REGEXP_REPLACE(
                REGEXP_REPLACE(p_domain, '^https?://', ''),
                '^www\.', ''
            ),
            '/.*$', ''  -- Remove path
        )
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION public.normalize_domain(TEXT) IS
    'Normalizes domain to bare format (e.g., http://www.example.com/path -> example.com)';

-- ============================================================================
-- STEP 3: Add normalized_domain column to cl.company_identity
-- ============================================================================

DO $$
BEGIN
    -- Add column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'cl'
          AND table_name = 'company_identity'
          AND column_name = 'normalized_domain'
    ) THEN
        ALTER TABLE cl.company_identity
        ADD COLUMN normalized_domain TEXT;

        RAISE NOTICE 'Added normalized_domain column to cl.company_identity';
    END IF;
END $$;

-- Populate normalized_domain for all records
UPDATE cl.company_identity
SET normalized_domain = public.normalize_domain(company_domain)
WHERE normalized_domain IS NULL
  AND company_domain IS NOT NULL;

-- Create index for fast lookups
CREATE INDEX IF NOT EXISTS idx_cl_company_identity_normalized_domain
ON cl.company_identity(normalized_domain)
WHERE normalized_domain IS NOT NULL;

-- ============================================================================
-- STEP 4: Verify linkage improvements
-- ============================================================================

DO $$
DECLARE
    v_cl_with_outreach INTEGER;
    v_domain_match INTEGER;
BEGIN
    -- Count CL records with outreach_id
    SELECT COUNT(*) INTO v_cl_with_outreach
    FROM cl.company_identity
    WHERE outreach_id IS NOT NULL;

    -- Count domain matches after normalization
    SELECT COUNT(DISTINCT o.outreach_id) INTO v_domain_match
    FROM outreach.outreach o
    JOIN cl.company_identity ci ON ci.normalized_domain = public.normalize_domain(o.domain)
    WHERE o.domain IS NOT NULL;

    RAISE NOTICE '=== ENTITY RESOLUTION VERIFICATION ===';
    RAISE NOTICE 'CL records with outreach_id: %', v_cl_with_outreach;
    RAISE NOTICE 'Domain matches after normalization: %', v_domain_match;
END $$;

COMMIT;

-- ============================================================================
-- Post-migration verification query (run manually)
-- ============================================================================
/*
-- Verify CL linkage
SELECT
    COUNT(*) as total_cl,
    COUNT(outreach_id) as with_outreach_id,
    ROUND(COUNT(outreach_id)::numeric / COUNT(*)::numeric * 100, 2) as pct
FROM cl.company_identity;

-- Verify domain normalization
SELECT
    COUNT(DISTINCT o.outreach_id) as outreach_with_domain_match
FROM outreach.outreach o
JOIN cl.company_identity ci ON ci.normalized_domain = public.normalize_domain(o.domain);
*/

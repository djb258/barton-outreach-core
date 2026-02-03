-- ============================================================================
-- DONE STATE VERIFICATION QUERIES
-- ============================================================================
-- Purpose: Production-ready queries to determine DONE status for each sub-hub
-- Generated: 2026-02-02
-- Database: Neon PostgreSQL (Marketing DB)
-- ============================================================================

-- ============================================================================
-- 1. COMPANY TARGET: Email Pattern Discovery Complete
-- ============================================================================

-- Check if Company Target is DONE for a single company
SELECT
  ct.outreach_id,
  ct.execution_status,
  ct.email_method,
  ct.confidence_score,
  ct.imo_completed_at,
  CASE
    WHEN ct.execution_status = 'ready'
      AND ct.email_method IS NOT NULL
      AND ct.confidence_score IS NOT NULL
      AND ct.imo_completed_at IS NOT NULL
    THEN TRUE
    ELSE FALSE
  END AS is_done
FROM outreach.company_target ct
WHERE ct.outreach_id = :outreach_id;

-- Get all DONE Company Target records
SELECT
  outreach_id,
  email_method,
  method_type,
  confidence_score,
  imo_completed_at
FROM outreach.company_target
WHERE execution_status = 'ready'
  AND email_method IS NOT NULL
  AND confidence_score IS NOT NULL
  AND imo_completed_at IS NOT NULL;

-- Get DONE count and percentage
SELECT
  COUNT(*) FILTER (WHERE execution_status = 'ready' AND email_method IS NOT NULL) AS done_count,
  COUNT(*) AS total_count,
  ROUND(100.0 * COUNT(*) FILTER (WHERE execution_status = 'ready' AND email_method IS NOT NULL) / COUNT(*), 2) AS done_percentage
FROM outreach.company_target;

-- ============================================================================
-- 2. PEOPLE INTELLIGENCE: Slot Fill Complete
-- ============================================================================

-- Check if People Intelligence is DONE for a single company (slot-level)
SELECT
  cs.outreach_id,
  COUNT(*) AS total_slots,
  COUNT(*) FILTER (WHERE cs.is_filled = TRUE) AS filled_slots,
  ARRAY_AGG(cs.slot_type ORDER BY cs.slot_type) FILTER (WHERE cs.is_filled = TRUE) AS filled_slot_types,
  CASE
    WHEN COUNT(*) FILTER (WHERE cs.is_filled = TRUE) >= 3  -- At least 3 filled slots
    THEN TRUE
    ELSE FALSE
  END AS is_done
FROM people.company_slot cs
WHERE cs.outreach_id = :outreach_id
GROUP BY cs.outreach_id;

-- Get companies with minimum slot requirements met
SELECT
  cs.outreach_id,
  COUNT(*) FILTER (WHERE cs.is_filled = TRUE) AS filled_count,
  ARRAY_AGG(DISTINCT cs.slot_type) FILTER (WHERE cs.is_filled = TRUE) AS filled_slots
FROM people.company_slot cs
GROUP BY cs.outreach_id
HAVING COUNT(*) FILTER (WHERE cs.is_filled = TRUE) >= 3;  -- Customize threshold

-- Get person-level DONE status (email verified)
SELECT
  p.outreach_id,
  p.person_id,
  p.email,
  p.email_verified,
  p.slot_type,
  CASE
    WHEN p.email_verified = TRUE
      AND p.contact_status NOT IN ('bounced', 'unsubscribed')
    THEN TRUE
    ELSE FALSE
  END AS is_done
FROM outreach.people p
WHERE p.outreach_id = :outreach_id;

-- Get slot fill statistics
SELECT
  COUNT(*) FILTER (WHERE is_filled = TRUE) AS filled_count,
  COUNT(*) AS total_slots,
  ROUND(100.0 * COUNT(*) FILTER (WHERE is_filled = TRUE) / COUNT(*), 2) AS fill_percentage
FROM people.company_slot;

-- ============================================================================
-- 3. DOL FILINGS: EIN Resolution + Filing Match Complete
-- ============================================================================

-- Check if DOL Filings are DONE for a single company
SELECT
  d.outreach_id,
  d.ein,
  d.filing_present,
  d.funding_type,
  d.broker_or_advisor,
  CASE
    WHEN d.ein IS NOT NULL
      AND d.filing_present = TRUE
    THEN TRUE
    ELSE FALSE
  END AS is_done
FROM outreach.dol d
WHERE d.outreach_id = :outreach_id;

-- Get all DONE DOL records
SELECT
  outreach_id,
  ein,
  filing_present,
  funding_type,
  broker_or_advisor,
  carrier
FROM outreach.dol
WHERE ein IS NOT NULL
  AND filing_present = TRUE;

-- Get DOL coverage statistics
SELECT
  COUNT(*) AS total_dol_records,
  COUNT(*) FILTER (WHERE ein IS NOT NULL) AS has_ein,
  COUNT(*) FILTER (WHERE filing_present = TRUE) AS has_filing,
  COUNT(*) FILTER (WHERE ein IS NOT NULL AND filing_present = TRUE) AS done_count,
  ROUND(100.0 * COUNT(*) FILTER (WHERE ein IS NOT NULL AND filing_present = TRUE) /
    (SELECT COUNT(*) FROM outreach.outreach), 2) AS done_percentage_vs_spine
FROM outreach.dol;

-- ============================================================================
-- 4. BLOG CONTENT: Content Signal Present
-- ============================================================================

-- Check if Blog Content exists for a single company
SELECT
  b.outreach_id,
  b.blog_id,
  b.context_summary,
  b.source_type,
  b.created_at,
  CASE
    WHEN b.outreach_id IS NOT NULL
    THEN TRUE
    ELSE FALSE
  END AS is_done
FROM outreach.blog b
WHERE b.outreach_id = :outreach_id;

-- Get all companies with blog content
SELECT
  outreach_id,
  blog_id,
  context_summary,
  source_type,
  created_at
FROM outreach.blog;

-- Get blog coverage statistics
SELECT
  COUNT(*) AS total_blog_records,
  (SELECT COUNT(*) FROM outreach.outreach) AS total_spine_records,
  ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM outreach.outreach), 2) AS coverage_percentage
FROM outreach.blog;

-- ============================================================================
-- 5. BIT SCORES: Signal-Based Scoring Complete
-- ============================================================================

-- Check if BIT Score is DONE for a single company
SELECT
  bs.outreach_id,
  bs.score,
  bs.score_tier,
  bs.signal_count,
  bs.people_score,
  bs.dol_score,
  bs.blog_score,
  bs.talent_flow_score,
  bs.last_scored_at,
  CASE
    WHEN bs.score IS NOT NULL
      AND bs.signal_count > 0
    THEN TRUE
    ELSE FALSE
  END AS is_done
FROM outreach.bit_scores bs
WHERE bs.outreach_id = :outreach_id;

-- Get all DONE BIT Score records
SELECT
  outreach_id,
  score,
  score_tier,
  signal_count,
  people_score,
  dol_score,
  blog_score,
  talent_flow_score,
  last_scored_at
FROM outreach.bit_scores
WHERE score IS NOT NULL
  AND signal_count > 0;

-- Get BIT Score coverage statistics
SELECT
  COUNT(*) AS total_bit_scores,
  (SELECT COUNT(*) FROM outreach.outreach) AS total_spine_records,
  ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM outreach.outreach), 2) AS coverage_percentage,
  AVG(score) AS avg_score,
  MIN(score) AS min_score,
  MAX(score) AS max_score
FROM outreach.bit_scores;

-- ============================================================================
-- 6. COMPOSITE DONE STATES: Multi-Hub Requirements
-- ============================================================================

-- Tier 1: Marketing-Ready (Company Target + Blog)
SELECT
  o.outreach_id,
  o.sovereign_id,
  o.domain,
  ct.email_method,
  ct.confidence_score,
  b.blog_id IS NOT NULL AS has_blog
FROM outreach.outreach o
JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
WHERE ct.execution_status = 'ready'
  AND ct.email_method IS NOT NULL
  AND ct.confidence_score >= 0.8;  -- High confidence threshold

-- Tier 2: Enrichment Complete (All Sub-Hubs Pass)
SELECT
  o.outreach_id,
  o.sovereign_id,
  o.domain,
  ct.execution_status AS company_target_status,
  b.blog_id IS NOT NULL AS has_blog,
  d.filing_present AS has_dol_filing,
  bs.score AS bit_score
FROM outreach.outreach o
JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
LEFT JOIN outreach.bit_scores bs ON o.outreach_id = bs.outreach_id
WHERE ct.execution_status = 'ready'
  AND b.blog_id IS NOT NULL
  AND d.filing_present = TRUE
  AND bs.score IS NOT NULL;

-- Tier 3: Campaign-Ready (People + Email Verified)
SELECT
  o.outreach_id,
  o.sovereign_id,
  o.domain,
  COUNT(DISTINCT cs.slot_id) FILTER (WHERE cs.is_filled = TRUE) AS filled_slots,
  COUNT(DISTINCT p.person_id) FILTER (WHERE p.email_verified = TRUE) AS verified_people
FROM outreach.outreach o
LEFT JOIN people.company_slot cs ON o.outreach_id = cs.outreach_id
LEFT JOIN outreach.people p ON o.outreach_id = p.outreach_id
GROUP BY o.outreach_id, o.sovereign_id, o.domain
HAVING COUNT(DISTINCT cs.slot_id) FILTER (WHERE cs.is_filled = TRUE) >= 3
   AND COUNT(DISTINCT p.person_id) FILTER (WHERE p.email_verified = TRUE) >= 1;

-- ============================================================================
-- 7. OVERALL COMPLETION DASHBOARD
-- ============================================================================

SELECT
  'Company Target' AS sub_hub,
  COUNT(*) FILTER (WHERE ct.execution_status = 'ready' AND ct.email_method IS NOT NULL) AS done_count,
  (SELECT COUNT(*) FROM outreach.outreach) AS total_spine,
  ROUND(100.0 * COUNT(*) FILTER (WHERE ct.execution_status = 'ready' AND ct.email_method IS NOT NULL) /
    (SELECT COUNT(*) FROM outreach.outreach), 2) AS completion_percentage
FROM outreach.company_target ct

UNION ALL

SELECT
  'Blog Content' AS sub_hub,
  COUNT(*) AS done_count,
  (SELECT COUNT(*) FROM outreach.outreach) AS total_spine,
  ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM outreach.outreach), 2) AS completion_percentage
FROM outreach.blog

UNION ALL

SELECT
  'DOL Filings' AS sub_hub,
  COUNT(*) FILTER (WHERE ein IS NOT NULL AND filing_present = TRUE) AS done_count,
  (SELECT COUNT(*) FROM outreach.outreach) AS total_spine,
  ROUND(100.0 * COUNT(*) FILTER (WHERE ein IS NOT NULL AND filing_present = TRUE) /
    (SELECT COUNT(*) FROM outreach.outreach), 2) AS completion_percentage
FROM outreach.dol

UNION ALL

SELECT
  'BIT Scores' AS sub_hub,
  COUNT(*) AS done_count,
  (SELECT COUNT(*) FROM outreach.outreach) AS total_spine,
  ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM outreach.outreach), 2) AS completion_percentage
FROM outreach.bit_scores

UNION ALL

SELECT
  'People Intelligence (Slots)' AS sub_hub,
  COUNT(*) FILTER (WHERE is_filled = TRUE) AS done_count,
  COUNT(*) AS total_spine,
  ROUND(100.0 * COUNT(*) FILTER (WHERE is_filled = TRUE) / COUNT(*), 2) AS completion_percentage
FROM people.company_slot

UNION ALL

SELECT
  'People Intelligence (People)' AS sub_hub,
  COUNT(*) AS done_count,
  (SELECT COUNT(*) FROM outreach.outreach) AS total_spine,
  ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM outreach.outreach), 2) AS completion_percentage
FROM outreach.people

ORDER BY sub_hub;

-- ============================================================================
-- 8. ERROR TRACKING
-- ============================================================================

-- Get error counts by sub-hub
SELECT
  COUNT(*) AS total_errors,
  'Company Target' AS sub_hub
FROM outreach.company_target_errors;

-- Get execution status breakdown including failures
SELECT
  execution_status,
  COUNT(*) AS count,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM outreach.company_target
GROUP BY execution_status
ORDER BY count DESC;

-- ============================================================================
-- 9. CL ALIGNMENT VERIFICATION
-- ============================================================================

-- Verify perfect alignment between CL and Outreach spine
SELECT
  (SELECT COUNT(*) FROM outreach.outreach) AS outreach_spine_count,
  (SELECT COUNT(*) FROM cl.company_identity WHERE outreach_id IS NOT NULL) AS cl_with_outreach_id,
  CASE
    WHEN (SELECT COUNT(*) FROM outreach.outreach) =
         (SELECT COUNT(*) FROM cl.company_identity WHERE outreach_id IS NOT NULL)
    THEN 'ALIGNED'
    ELSE 'MISALIGNED'
  END AS alignment_status;

-- Find any orphaned outreach_ids (should be empty)
SELECT o.outreach_id
FROM outreach.outreach o
WHERE NOT EXISTS (
  SELECT 1
  FROM cl.company_identity ci
  WHERE ci.outreach_id = o.outreach_id
);

-- ============================================================================
-- END OF DONE STATE QUERIES
-- ============================================================================

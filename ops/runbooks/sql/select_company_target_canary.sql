-- =============================================================================
-- Company Target IMO Canary Selection
-- =============================================================================
-- Purpose: Select mixed-quality outreach_ids for execution verification
-- Usage: Run before full production run to validate plumbing
--
-- Selection criteria:
--   - 40 .com domains (most common)
--   - 20 .io domains (tech companies)
--   - 20 .org domains (non-profits)
--   - 20 random domains (edge cases)
--   - Total: 100 outreach_ids
--
-- PRD: Company Target (Execution Prep Sub-Hub) v3.0
-- Doctrine: Spine-First Architecture
-- =============================================================================

WITH base AS (
    SELECT outreach_id, domain
    FROM outreach.v_context_current
    WHERE domain IS NOT NULL
      AND ct_status IS NULL  -- Not yet processed
),
sample AS (
    -- 40 .com domains (most common)
    (
        SELECT outreach_id FROM base
        WHERE domain LIKE '%.com'
        ORDER BY RANDOM()
        LIMIT 40
    )
    UNION ALL
    -- 20 .io domains (tech companies)
    (
        SELECT outreach_id FROM base
        WHERE domain LIKE '%.io'
        ORDER BY RANDOM()
        LIMIT 20
    )
    UNION ALL
    -- 20 .org domains (non-profits)
    (
        SELECT outreach_id FROM base
        WHERE domain LIKE '%.org'
        ORDER BY RANDOM()
        LIMIT 20
    )
    UNION ALL
    -- 20 random domains (edge cases)
    (
        SELECT outreach_id FROM base
        WHERE domain NOT LIKE '%.com'
          AND domain NOT LIKE '%.io'
          AND domain NOT LIKE '%.org'
        ORDER BY RANDOM()
        LIMIT 20
    )
)
SELECT DISTINCT outreach_id
FROM sample
LIMIT 100;

-- =============================================================================
-- VERIFICATION QUERY (Run after canary execution)
-- =============================================================================
-- Check canary results:
--
-- SELECT
--     ct_status,
--     COUNT(*) as count,
--     ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as pct
-- FROM outreach.v_context_current
-- WHERE outreach_id IN (
--     SELECT outreach_id FROM canary_ids  -- Replace with actual canary IDs
-- )
-- GROUP BY ct_status;

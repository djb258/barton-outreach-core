-- ═══════════════════════════════════════════════════════════════
-- Talent Flow — LinkedIn Monitor: Seed Script
-- ═══════════════════════════════════════════════════════════════
-- Work Packet: wp-20260306-talent-flow-linkedin-monitor
-- ORBT: Build
-- Direction: FORWARD
-- Sample Gate: 100 records
-- Vendor Tier: field_monitor.* (same tier as vendor.people)
--
-- Seeds LinkedIn URLs from people.people_master into the
-- field_monitor vendor tier (url_registry + field_state).
-- Cloudflare Workers then monitor these URLs for changes.
--
-- Prerequisites:
--   field_monitor schema DEPLOYED (wp-20260305-field-monitor-phase1-bootstrap-r2)
--   people.people_master has linkedin_url column
--
-- Idempotent: ON CONFLICT DO NOTHING on all INSERTs.
-- ═══════════════════════════════════════════════════════════════

BEGIN;

-- ─── Step 1: Seed url_registry with LinkedIn URLs ─────────────
-- Normalize all LinkedIn URL formats to domain + path

INSERT INTO field_monitor.url_registry (domain, path, check_interval_minutes, is_active)
SELECT DISTINCT
    'www.linkedin.com' AS domain,
    CASE
        WHEN linkedin_url LIKE 'https://www.linkedin.com/%'
            THEN SUBSTRING(linkedin_url FROM 'https://www\.linkedin\.com(/[^ ?#]*)')
        WHEN linkedin_url LIKE 'https://linkedin.com/%'
            THEN SUBSTRING(linkedin_url FROM 'https://linkedin\.com(/[^ ?#]*)')
        WHEN linkedin_url LIKE 'http://www.linkedin.com/%'
            THEN SUBSTRING(linkedin_url FROM 'http://www\.linkedin\.com(/[^ ?#]*)')
        WHEN linkedin_url LIKE 'http://linkedin.com/%'
            THEN SUBSTRING(linkedin_url FROM 'http://linkedin\.com(/[^ ?#]*)')
        WHEN linkedin_url LIKE '/in/%'
            THEN linkedin_url
        ELSE '/in/' || linkedin_url
    END AS path,
    1440 AS check_interval_minutes,
    true AS is_active
FROM people.people_master
WHERE linkedin_url IS NOT NULL
    AND linkedin_url <> ''
    AND linkedin_url LIKE '%linkedin.com%'
ORDER BY path
LIMIT 100
ON CONFLICT (domain, path) DO NOTHING;

-- ─── Step 2: Seed field_state for title + company tracking ────
-- 2 rows per URL: current_title and current_company

INSERT INTO field_monitor.field_state (url_id, field_name, status, promotion_status)
SELECT
    ur.url_id,
    field.field_name,
    'ACTIVE' AS status,
    'DRAFT' AS promotion_status
FROM field_monitor.url_registry ur
CROSS JOIN (
    VALUES ('current_title'), ('current_company')
) AS field(field_name)
WHERE ur.domain = 'www.linkedin.com'
    AND ur.is_active = true
ON CONFLICT (url_id, field_name) DO NOTHING;

COMMIT;

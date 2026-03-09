-- Talent Flow LinkedIn Monitor — Seed Script
-- WP: wp-20260306-talent-flow-linkedin-monitor
-- Sample gate: LIMIT 100
-- Source: people.people_master (linkedin_url column)
-- Kill switch: KILL_TALENT_FLOW_MONITOR, KILL_LINKEDIN_SEED
--
-- Seeds field_monitor.url_registry + field_monitor.field_state
-- from people.people_master LinkedIn URLs.
-- Idempotent: ON CONFLICT DO NOTHING.

BEGIN;

-- Step 1: Seed url_registry from people_master LinkedIn URLs
INSERT INTO field_monitor.url_registry (url_id, domain, path, check_interval_minutes, is_active)
SELECT
  gen_random_uuid(),
  'linkedin.com',
  regexp_replace(pm.linkedin_url, '^https?://[^/]+', ''),
  1440,  -- daily check (LinkedIn rate-sensitive)
  true
FROM people.people_master pm
WHERE pm.linkedin_url IS NOT NULL
  AND pm.linkedin_url <> ''
  AND pm.linkedin_url LIKE '%linkedin.com%'
ORDER BY pm.last_verified_at DESC NULLS LAST
LIMIT 100
ON CONFLICT DO NOTHING;

-- Step 2: Seed field_state for each new url_registry row
-- Monitor 'title' field (job title changes = movement signal)
INSERT INTO field_monitor.field_state (field_id, url_id, field_name, current_value, status, promotion_status)
SELECT
  gen_random_uuid(),
  ur.url_id,
  'title',
  NULL,
  'ACTIVE',
  'DRAFT'
FROM field_monitor.url_registry ur
WHERE ur.domain = 'linkedin.com'
  AND NOT EXISTS (
    SELECT 1 FROM field_monitor.field_state fs
    WHERE fs.url_id = ur.url_id AND fs.field_name = 'title'
  );

COMMIT;

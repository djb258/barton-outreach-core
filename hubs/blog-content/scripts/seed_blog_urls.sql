-- Signal Sweep Blog Monitor — Seed Script
-- WP: wp-20260306-signal-sweep-blog-monitor
-- Repair: wp-20260306-blog-content-seed-bridge-repair (SEED-001)
-- Sample gate: LIMIT 100
-- Source: vendor.blog
-- Kill switch: KILL_SIGNAL_SWEEP, KILL_BLOG_URL_SEED
-- Depends on: wp-20260306-talent-flow-linkedin-monitor
--
-- Prerequisites:
--   vendor schema and vendor.blog table must exist before running.
--   See vendor_blog_ddl.sql for schema creation.
--
-- Seeds field_monitor.url_registry + field_monitor.field_state
-- from vendor.blog URLs.
-- Idempotent: ON CONFLICT DO NOTHING.

BEGIN;

-- Step 1: Seed url_registry from vendor.blog
-- Uses actual vendor.blog columns: domain, source_url, is_accessible, original_created_at
INSERT INTO field_monitor.url_registry (url_id, domain, path, check_interval_minutes, is_active)
SELECT
  gen_random_uuid(),
  vb.domain,
  regexp_replace(vb.source_url, '^https?://[^/]+', ''),
  60,  -- hourly check for blog content
  true
FROM vendor.blog vb
WHERE vb.is_accessible = true
ORDER BY vb.original_created_at DESC NULLS LAST
LIMIT 100
ON CONFLICT DO NOTHING;

-- Step 2: Seed field_state for each new url_registry row
-- Monitor 'content_hash' field (blog content changes = signal sweep trigger)
INSERT INTO field_monitor.field_state (field_id, url_id, field_name, current_value, status, promotion_status)
SELECT
  gen_random_uuid(),
  ur.url_id,
  'content_hash',
  NULL,
  'ACTIVE',
  'DRAFT'
FROM field_monitor.url_registry ur
JOIN vendor.blog vb
  ON ur.domain = vb.domain
  AND ur.path = regexp_replace(vb.source_url, '^https?://[^/]+', '')
WHERE NOT EXISTS (
  SELECT 1 FROM field_monitor.field_state fs
  WHERE fs.url_id = ur.url_id AND fs.field_name = 'content_hash'
);

COMMIT;

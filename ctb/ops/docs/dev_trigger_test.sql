-- ════════════════════════════════════════════════════════════════════════════════
-- Developer Trigger Test
-- ════════════════════════════════════════════════════════════════════════════════
-- Purpose: Quick trigger verification for event-driven pipeline
-- Usage: psql "$NEON_DATABASE_URL" -f ops/dev_trigger_test.sql
-- ════════════════════════════════════════════════════════════════════════════════

-- Clean up any previous test data
DELETE FROM marketing.pipeline_events WHERE payload->>'company' = 'Trigger Test Co';
DELETE FROM intake.company_raw_intake WHERE company = 'Trigger Test Co';

-- Test 1: INSERT should fire company_created event
\echo '================================================'
\echo 'TEST 1: Insert company (should fire company_created)'
\echo '================================================'

INSERT INTO intake.company_raw_intake(company, website, import_batch_id)
VALUES ('Trigger Test Co', 'https://trigger-test.com', 'TEST-01');

\echo ''
\echo 'Events created (should show company_created):'
SELECT
  id,
  event_type,
  payload->>'company' as company,
  payload->>'website' as website,
  status,
  created_at
FROM marketing.pipeline_events
WHERE payload->>'company' = 'Trigger Test Co'
ORDER BY id DESC
LIMIT 5;

-- Wait a moment for trigger to complete
SELECT pg_sleep(1);

-- Test 2: UPDATE should fire company_updated event
\echo ''
\echo '================================================'
\echo 'TEST 2: Update company (should fire company_updated)'
\echo '================================================'

UPDATE intake.company_raw_intake
SET website = 'https://trigger-test-updated.com'
WHERE company = 'Trigger Test Co';

\echo ''
\echo 'All events for Trigger Test Co (should show both created + updated):'
SELECT
  id,
  event_type,
  payload->>'company' as company,
  payload->>'website' as website,
  status,
  created_at
FROM marketing.pipeline_events
WHERE payload->>'company' = 'Trigger Test Co'
ORDER BY created_at;

-- Summary
\echo ''
\echo '================================================'
\echo 'SUMMARY'
\echo '================================================'

SELECT
  event_type,
  COUNT(*) as count
FROM marketing.pipeline_events
WHERE payload->>'company' = 'Trigger Test Co'
GROUP BY event_type;

\echo ''
\echo '✅ Test complete!'
\echo 'Expected: 2 events (1 company_created, 1 company_updated)'
\echo ''
\echo 'Cleanup: Run this to delete test data:'
\echo "  DELETE FROM marketing.pipeline_events WHERE payload->>'company' = 'Trigger Test Co';"
\echo "  DELETE FROM intake.company_raw_intake WHERE company = 'Trigger Test Co';"

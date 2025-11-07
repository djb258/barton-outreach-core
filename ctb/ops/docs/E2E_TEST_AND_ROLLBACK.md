# 🧪 End-to-End Test & Rollback Guide

**System:** Barton Outreach Event-Driven Pipeline
**Version:** 1.0.0
**Last Updated:** 2025-10-24

---

## 📋 Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Test Steps](#2-test-steps)
3. [Live Checks](#3-live-checks)
4. [Rollback Procedures](#4-rollback)
5. [Operator Checklist](#5-operator-checklist)

---

## 1️⃣ Prerequisites

### Environment Variables

```bash
export NEON_DATABASE_URL="postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/Marketing%20DB?sslmode=require"

export N8N_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
export N8N_BASE_URL="https://dbarton.app.n8n.cloud"
```

### Required Components

- [x] n8n workflows deployed (7 workflows)
- [x] `/webhook/log-to-neon` URL active
- [x] Database migrations 007, 008, 009 applied
- [x] `psql` CLI installed
- [x] `curl` or equivalent HTTP client

### Verify Prerequisites

```bash
# Test database connection
psql "$NEON_DATABASE_URL" -c "SELECT NOW();"

# Test n8n API
curl -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "$N8N_BASE_URL/api/v1/workflows" | jq '.data[].name'

# Check migrations
psql "$NEON_DATABASE_URL" -c "SELECT COUNT(*) FROM marketing.pipeline_events;"
```

Expected outputs:
- ✅ Database returns current timestamp
- ✅ n8n returns list of workflow names
- ✅ pipeline_events table exists

---

## 2️⃣ Test Steps

### Step 1: Test Database Triggers

```bash
# Run trigger test script
psql "$NEON_DATABASE_URL" -f ops/dev_trigger_test.sql
```

**Expected Output:**
```
TEST 1: Insert company (should fire company_created)
================================================
Events created (should show company_created):
 id | event_type      | company          | website                      | status  | created_at
----+-----------------+------------------+------------------------------+---------+------------
  1 | company_created | Trigger Test Co  | https://trigger-test.com     | pending | 2025-10-24...

TEST 2: Update company (should fire company_updated)
================================================
All events for Trigger Test Co (should show both created + updated):
 id | event_type      | company          | website                         | status  | created_at
----+-----------------+------------------+---------------------------------+---------+------------
  1 | company_created | Trigger Test Co  | https://trigger-test.com        | pending | 2025-10-24...
  2 | company_updated | Trigger Test Co  | https://trigger-test-updated... | pending | 2025-10-24...

SUMMARY
================================================
 event_type      | count
-----------------+-------
 company_created |     1
 company_updated |     1
```

✅ **Pass Criteria:** 2 events created (1 company_created, 1 company_updated)

---

### Step 2: Verify Events in Pipeline Table

```sql
SELECT
  id,
  event_type,
  payload->>'company' as company,
  status,
  created_at
FROM marketing.pipeline_events
WHERE payload->>'company' = 'Trigger Test Co'
ORDER BY id;
```

**Expected:**
- ✅ Both events present
- ✅ status = 'pending'
- ✅ payload contains company data

---

### Step 3: Test n8n Webhook (Manual)

```bash
# Get event payload
psql "$NEON_DATABASE_URL" -t -c "
SELECT payload::text
FROM marketing.pipeline_events
WHERE payload->>'company' = 'Trigger Test Co'
LIMIT 1;
" > /tmp/event_payload.json

# POST to validation webhook
curl -X POST \
  -H "Content-Type: application/json" \
  -d @/tmp/event_payload.json \
  "$N8N_BASE_URL/webhook/validate-company"
```

**Expected Output:**
```json
{
  "status": "ok",
  "workflow_name": "Validate_Company",
  "record_id": 450
}
```

✅ **Pass Criteria:** HTTP 200 response with status "ok"

---

### Step 4: Verify LogToNeon Workflow

```bash
# Send log event
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "workflowName": "Test_Workflow",
    "status": "ok",
    "triggerSource": "manual_test",
    "recordId": "999"
  }' \
  "$N8N_BASE_URL/webhook/log-to-neon"
```

**Check database:**
```sql
SELECT * FROM marketing.workflow_stats
WHERE workflow_name = 'Test_Workflow'
ORDER BY created_at DESC
LIMIT 5;
```

**Expected:**
- ✅ New row inserted
- ✅ workflow_name = 'Test_Workflow'
- ✅ status = 'ok'

---

### Step 5: Test Error Logging

```sql
-- Insert test error
INSERT INTO marketing.pipeline_errors(event_type, record_id, error_message, created_at)
VALUES ('test_event', '999', 'Test error message', NOW());

-- Verify
SELECT * FROM marketing.pipeline_errors
WHERE event_type = 'test_event';
```

**Expected:**
- ✅ Error inserted successfully
- ✅ Default severity = 'error'
- ✅ resolved = FALSE

---

### Step 6: Test Dashboard Views

```sql
-- Test phase stats view
SELECT * FROM marketing.v_phase_stats;

-- Test error view
SELECT * FROM marketing.v_error_recent LIMIT 10;

-- Test workflow health
SELECT * FROM marketing.v_workflow_health;

-- Test event queue
SELECT * FROM marketing.v_event_queue_status;
```

**Expected:**
- ✅ All views return results (may be empty if no data)
- ✅ No SQL errors

---

## 3️⃣ Live Checks

### Check n8n Workflow Status

```bash
# Get all workflows
curl -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "$N8N_BASE_URL/api/v1/workflows" | jq '.data[] | {name, active}'

# Get recent executions
curl -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "$N8N_BASE_URL/api/v1/executions?limit=10" | jq '.data[] | {workflowName, status, startedAt}'

# Get error executions
curl -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "$N8N_BASE_URL/api/v1/executions?status=error" | jq '.data[] | {workflowName, error, startedAt}'
```

**Expected:**
- ✅ All 7 workflows listed
- ✅ At least 3 workflows active
- ✅ No critical errors

---

### Check Neon Database Health

```sql
-- Check trigger count
SELECT COUNT(*) as trigger_count
FROM information_schema.triggers
WHERE trigger_schema IN ('marketing', 'intake')
  AND trigger_name LIKE '%_event';

-- Check pending events
SELECT event_type, COUNT(*) as pending_count
FROM marketing.pipeline_events
WHERE status = 'pending'
GROUP BY event_type;

-- Check recent errors
SELECT event_type, COUNT(*) as error_count
FROM marketing.pipeline_errors
WHERE created_at > NOW() - INTERVAL '1 hour'
  AND resolved = FALSE
GROUP BY event_type;

-- Check workflow stats
SELECT * FROM marketing.v_phase_stats;
```

**Expected:**
- ✅ Trigger count >= 6
- ✅ Pending events < 100 (or 0 if no activity)
- ✅ Error count = 0 or low
- ✅ Phase stats showing data

---

### Monitor Real-Time Events

**Terminal 1: Listen to PostgreSQL NOTIFY**
```bash
psql "$NEON_DATABASE_URL"
```
```sql
LISTEN pipeline_event;
```

**Terminal 2: Insert test data**
```sql
INSERT INTO intake.company_raw_intake(company, website, import_batch_id)
VALUES ('Live Monitor Test', 'https://livetest.com', 'LIVE-MONITOR-01');
```

**Expected in Terminal 1:**
```
Asynchronous notification "pipeline_event" received from server process with PID 12345.
Payload: {"table":"intake.company_raw_intake","event_type":"company_created",...}
```

✅ **Pass Criteria:** Notification received within 1 second

---

## 4️⃣ Rollback

### Rollback Scenario 1: Disable Trigger Notifications

If triggers are causing issues but you want to keep event logging:

```sql
-- Temporarily disable pg_notify (keep INSERT to pipeline_events)
CREATE OR REPLACE FUNCTION marketing.notify_pipeline_event(
  p_table_name TEXT,
  p_event_type TEXT,
  p_payload JSONB
)
RETURNS VOID AS $$
BEGIN
  -- Insert event into pipeline_events table (keep this)
  INSERT INTO marketing.pipeline_events (event_type, payload, status, created_at)
  VALUES (p_event_type, p_payload, 'pending', NOW());

  -- DISABLED: pg_notify for troubleshooting
  -- PERFORM pg_notify('pipeline_event', json_build_object(...)::text);
END;
$$ LANGUAGE plpgsql;
```

**Restore:**
```bash
psql "$NEON_DATABASE_URL" -f migrations/007_fix_event_triggers.sql
```

---

### Rollback Scenario 2: Drop and Recreate Specific Trigger

```sql
-- Drop problematic trigger
DROP TRIGGER IF EXISTS trigger_company_raw_intake_event ON intake.company_raw_intake;

-- Recreate from migration
-- (Copy CREATE TRIGGER statement from 007_fix_event_triggers.sql)
```

---

### Rollback Scenario 3: Disable All Triggers Temporarily

```sql
-- List all triggers
SELECT
  trigger_name,
  event_object_table
FROM information_schema.triggers
WHERE trigger_schema IN ('marketing', 'intake')
  AND trigger_name LIKE '%_event';

-- Disable triggers (PostgreSQL doesn't support DISABLE TRIGGER, so we drop them)
DROP TRIGGER IF EXISTS trigger_company_raw_intake_event ON intake.company_raw_intake;
DROP TRIGGER IF EXISTS trigger_company_master_event ON marketing.company_master;
DROP TRIGGER IF EXISTS trigger_company_slots_event ON marketing.company_slots;
-- ... etc

-- Re-enable by running migration
psql "$NEON_DATABASE_URL" -f migrations/007_fix_event_triggers.sql
```

---

### Rollback Scenario 4: Revert to Schedule-Based Workflows

If event-driven approach has issues:

1. **Deactivate webhook workflows** in n8n UI
2. **Reactivate old schedule-based workflows** (15 min polling)
3. **Keep triggers running** (for future transition back)
4. **Monitor via schedule** instead of events

**No data loss** - events still logged to `marketing.pipeline_events`

---

### Rollback Scenario 5: Full Database Rollback

**Warning:** This removes all event-driven infrastructure

```sql
-- Drop views (migration 009)
DROP VIEW IF EXISTS marketing.v_phase_stats CASCADE;
DROP VIEW IF EXISTS marketing.v_error_recent CASCADE;
DROP VIEW IF EXISTS marketing.v_sniper_targets CASCADE;
DROP VIEW IF EXISTS marketing.v_workflow_health CASCADE;
DROP VIEW IF EXISTS marketing.v_event_queue_status CASCADE;
DROP VIEW IF EXISTS marketing.v_daily_throughput CASCADE;

-- Drop tables (migration 008)
DROP TABLE IF EXISTS marketing.workflow_stats CASCADE;

-- Drop triggers and functions (migration 007)
DROP TRIGGER IF EXISTS trigger_company_raw_intake_event ON intake.company_raw_intake;
DROP TRIGGER IF EXISTS trigger_company_master_event ON marketing.company_master;
DROP TRIGGER IF EXISTS trigger_company_slots_event ON marketing.company_slots;
DROP TRIGGER IF EXISTS trigger_people_raw_intake_event ON marketing.people_raw_intake;
DROP TRIGGER IF EXISTS trigger_email_verification_event ON marketing.email_verification;
DROP TRIGGER IF EXISTS trigger_messages_outbound_event ON marketing.messages_outbound;

DROP FUNCTION IF EXISTS marketing.notify_pipeline_event(TEXT, TEXT, JSONB);
DROP FUNCTION IF EXISTS marketing.mark_event_processed(INT);
DROP FUNCTION IF EXISTS marketing.log_pipeline_error(TEXT, BIGINT, TEXT, JSONB);

-- Optionally drop event tables
-- DROP TABLE IF EXISTS marketing.pipeline_events CASCADE;
-- DROP TABLE IF EXISTS marketing.pipeline_errors CASCADE;
```

**Restore:**
```bash
psql "$NEON_DATABASE_URL" -f migrations/007_fix_event_triggers.sql
psql "$NEON_DATABASE_URL" -f migrations/008_workflow_stats.sql
psql "$NEON_DATABASE_URL" -f migrations/009_dashboard_views.sql
```

---

## 5️⃣ Operator Checklist

### Pre-Deployment Checks

- [ ] Database migrations 007, 008, 009 reviewed
- [ ] n8n workflows tested in staging
- [ ] Environment variables configured
- [ ] Backup of production database created
- [ ] Rollback plan documented

### Post-Deployment Verification

- [ ] ✅ Triggers fire on INSERT/UPDATE
- [ ] ✅ n8n receives POST requests
- [ ] ✅ LogToNeon workflow writes rows
- [ ] ✅ Dashboard views return data
- [ ] ✅ Error Console empty (or expected errors only)
- [ ] ✅ Real-time NOTIFY working
- [ ] ✅ No performance degradation

### Monitoring (First 24 Hours)

- [ ] Check error rate every hour
- [ ] Verify event queue not growing
- [ ] Monitor n8n execution logs
- [ ] Check database performance
- [ ] Review workflow durations
- [ ] Validate data integrity

### Success Criteria

| Metric | Target | Status |
|--------|--------|--------|
| Event creation latency | <1 second | ☐ |
| Webhook response time | <2 seconds | ☐ |
| Error rate | <1% | ☐ |
| Pending events | <100 | ☐ |
| Workflow success rate | >99% | ☐ |
| Dashboard load time | <2 seconds | ☐ |

---

## 🚨 Emergency Contacts

| Role | Contact | Escalation |
|------|---------|------------|
| Database Admin | DBA Team | Critical errors in Neon |
| n8n Admin | n8n Support | Workflow failures |
| System Owner | Project Lead | Architecture decisions |
| On-Call Engineer | PagerDuty | Production incidents |

---

## 📚 Related Documentation

- **ops/dev_trigger_test.sql** - Quick trigger test
- **ops/psql_listen_guide.md** - Real-time monitoring
- **ops/README_OUTREACH_OPS.md** - Operational guide
- **docs/PIPELINE_EVENT_FLOW.md** - Event architecture
- **migrations/007_fix_event_triggers.sql** - Trigger definitions

---

**Last Updated:** 2025-10-24
**Version:** 1.0.0
**Status:** ✅ Ready for Production

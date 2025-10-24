# 📡 Listening to Neon NOTIFY Events

**Purpose:** Real-time monitoring of PostgreSQL NOTIFY events from pipeline triggers

---

## 🎯 Quick Start

### Step 1: Open PostgreSQL Session

```bash
psql "$NEON_DATABASE_URL"
```

Or with explicit connection:

```bash
psql "postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/Marketing%20DB?sslmode=require"
```

### Step 2: Start Listening

```sql
LISTEN pipeline_event;
```

You should see:
```
LISTEN
```

### Step 3: Trigger Events (in another terminal)

**Option A: Run test script**
```bash
psql "$NEON_DATABASE_URL" -f ops/dev_trigger_test.sql
```

**Option B: Manual INSERT**
```sql
INSERT INTO intake.company_raw_intake(company, website, import_batch_id)
VALUES ('Live Test Co', 'https://livetest.com', 'LIVE-01');
```

### Step 4: Watch for Notifications

You should see output like:

```
Asynchronous notification "pipeline_event" with payload:
{
  "table": "intake.company_raw_intake",
  "event_type": "company_created",
  "payload": {
    "id": 449,
    "company": "Live Test Co",
    "website": "https://livetest.com",
    "import_batch_id": "LIVE-01",
    "validated": null,
    "created_at": "2025-10-24T12:00:00Z"
  },
  "timestamp": "2025-10-24T12:00:00.123456"
}
```

---

## 🔧 Advanced Usage

### Listen to Multiple Channels

```sql
LISTEN pipeline_event;
LISTEN workflow_event;
LISTEN error_event;
```

### Stop Listening

```sql
UNLISTEN pipeline_event;
-- Or stop all:
UNLISTEN *;
```

### Check Active Listeners

```sql
SELECT * FROM pg_stat_activity WHERE state = 'idle in transaction';
```

---

## 🧪 Testing All Event Types

### Test company_created

```sql
INSERT INTO intake.company_raw_intake(company, website, import_batch_id)
VALUES ('Event Test 1', 'https://test1.com', 'TEST-01');
```

Expected notification:
```json
{
  "event_type": "company_created",
  "payload": {"id": 450, "company": "Event Test 1", ...}
}
```

### Test company_updated

```sql
UPDATE intake.company_raw_intake
SET website = 'https://test1-updated.com'
WHERE company = 'Event Test 1';
```

Expected notification:
```json
{
  "event_type": "company_updated",
  "payload": {"id": 450, "company": "Event Test 1", "website": "https://test1-updated.com", ...}
}
```

### Test company_promoted

```sql
INSERT INTO marketing.company_master(
  company_unique_id, company_name, website_url,
  import_batch_id, source_system, promoted_from_intake_at
)
VALUES (
  '04.04.01.84.99999.001', 'Event Test Promoted', 'https://promoted.com',
  'TEST-01', 'manual-test', NOW()
);
```

### Test slots_created

```sql
INSERT INTO marketing.company_slots(
  company_slot_unique_id, company_unique_id,
  slot_type, slot_label
)
VALUES (
  '04.04.01.84.99999.001', '04.04.01.84.99999.001',
  'executive', 'CEO'
);
```

---

## 📊 Monitoring Dashboard (CLI)

Create a simple monitoring script:

```bash
#!/bin/bash
# monitor_events.sh

psql "$NEON_DATABASE_URL" << EOF
LISTEN pipeline_event;

-- Print header
\echo '================================================'
\echo 'MONITORING PIPELINE EVENTS (Press Ctrl+C to stop)'
\echo '================================================'
\echo ''

-- This will keep connection open and show notifications
SELECT pg_sleep(3600); -- Keep alive for 1 hour
EOF
```

Run it:
```bash
chmod +x monitor_events.sh
./monitor_events.sh
```

---

## 🐛 Troubleshooting

### No Notifications Appearing

1. **Check trigger exists:**
   ```sql
   SELECT trigger_name, event_object_table
   FROM information_schema.triggers
   WHERE trigger_name LIKE '%_event'
     AND trigger_schema IN ('intake', 'marketing');
   ```

2. **Check function is being called:**
   ```sql
   -- Enable logging (if you have permissions)
   SET log_statement = 'all';

   -- Then run INSERT and check logs
   INSERT INTO intake.company_raw_intake(company, website, import_batch_id)
   VALUES ('Debug Test', 'https://debug.com', 'DEBUG-01');
   ```

3. **Verify pg_notify is enabled:**
   ```sql
   SELECT pg_notify('test_channel', 'test_message');
   ```

   You should see:
   ```
   Asynchronous notification "test_channel" received from server process with PID 12345.
   Payload: test_message
   ```

### Connection Timeout

If your LISTEN session disconnects:

```bash
# Use with keepalive
psql "$NEON_DATABASE_URL" \
  -v ON_ERROR_STOP=1 \
  -c "LISTEN pipeline_event; SELECT pg_sleep(3600);"
```

### Too Many Notifications

Filter by event type in your application layer, or create separate channels:

```sql
-- In trigger function, use different channels per event type
PERFORM pg_notify('pipeline_event_' || event_type, payload);
```

Then listen selectively:
```sql
LISTEN pipeline_event_company_created;
LISTEN pipeline_event_company_promoted;
```

---

## 🔗 Integration with n8n

n8n doesn't natively support PostgreSQL LISTEN/NOTIFY, but you can:

1. **Poll the events table** (current approach):
   ```sql
   SELECT * FROM marketing.pipeline_events
   WHERE status = 'pending'
   ORDER BY created_at
   LIMIT 10;
   ```

2. **Use a webhook bridge** (future enhancement):
   - Node.js service listens to NOTIFY
   - Forwards to n8n webhook on each event
   - Example: `pg-notify-to-webhook.js`

3. **Use NOTIFY for monitoring only**:
   - Keep event-driven architecture (triggers → events table)
   - Use NOTIFY for ops dashboard real-time updates
   - n8n polls events table

---

## 📝 Sample Monitoring Script (Node.js)

```javascript
// monitor_notify.js
const { Client } = require('pg');

const client = new Client({
  connectionString: process.env.NEON_DATABASE_URL
});

async function monitor() {
  await client.connect();

  await client.query('LISTEN pipeline_event');

  console.log('🎧 Listening for pipeline events...\n');

  client.on('notification', (msg) => {
    const data = JSON.parse(msg.payload);
    console.log(`📬 ${data.event_type} | ${data.table}`);
    console.log(`   Record ID: ${data.payload.id}`);
    console.log(`   Timestamp: ${data.timestamp}\n`);
  });

  // Keep alive
  setInterval(() => {
    client.query('SELECT 1');
  }, 30000);
}

monitor().catch(console.error);
```

Run:
```bash
node monitor_notify.js
```

---

## 🎯 Best Practices

1. **Use LISTEN for development/debugging** - Real-time visibility into trigger execution
2. **Use events table for production** - Reliable, queryable, supports retries
3. **Keep LISTEN sessions short** - Reconnect periodically to avoid stale connections
4. **Log all notifications** - Useful for auditing and debugging
5. **Combine LISTEN + polling** - Best of both worlds for monitoring

---

## 🚀 Quick Commands Reference

```sql
-- Start listening
LISTEN pipeline_event;

-- Check for events (manual query)
SELECT * FROM marketing.pipeline_events
ORDER BY created_at DESC LIMIT 10;

-- Stop listening
UNLISTEN pipeline_event;

-- Exit psql
\q
```

---

**Next Steps:**
- Run `ops/dev_trigger_test.sql` to verify NOTIFY is working
- Create a monitoring dashboard that displays live events
- Set up alerting for critical event types

**Related Docs:**
- `ops/E2E_TEST_AND_ROLLBACK.md` - End-to-end testing
- `ops/README_OUTREACH_OPS.md` - Operational guide
- `docs/PIPELINE_EVENT_FLOW.md` - Event architecture

# Error Handling Guide
## Barton Outreach Core - Comprehensive Error Management

**Version**: 1.0
**Last Updated**: January 2025
**Related**: See `/docs/outreach-doctrine-a2z.md` Section 12 & 13

---

## Overview

This guide provides comprehensive documentation for error handling, logging, and monitoring across the Barton Outreach system. All errors must be logged to the centralized `shq_error_log` table and automatically synced to Firebase for real-time visibility.

---

## Error Handling Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Error Handling Flow                        │
└──────────────────────────────────────────────────────────────┘

[1] Error Occurs
    ↓
[2] Try/Catch Block
    ↓
[3] Log to shq_error_log (Neon)
    ├─ error_id: gen_random_uuid()
    ├─ agent_name: "Apify Orchestrator"
    ├─ process_id: "Enrich Contacts"
    ├─ unique_id: "04.01.02.05.10000.001"
    ├─ severity: "error"
    ├─ message: Context-rich description
    └─ stack_trace: Full stack
    ↓
[4] Sync to Firebase (every 60s)
    ↓
[5] Dashboard Alert (if critical)
    ↓
[6] Operator Investigation
    ↓
[7] Resolution & Notes
```

---

## Standard Error Codes

### **Database Errors (NEON_*)**

| Code | Description | Severity | Recovery Action |
|------|-------------|----------|-----------------|
| `NEON_CONN_ERR` | Database connection failed | critical | Verify connection string, check network, restart connection pool |
| `NEON_QUERY_ERR` | SQL query execution failed | error | Review query syntax, validate parameters, check schema compatibility |
| `NEON_TIMEOUT` | Query exceeded timeout (30s) | error | Optimize query, add indexes, increase timeout limit |
| `NEON_DEADLOCK` | Transaction deadlock detected | warning | Retry with exponential backoff, reorder operations |
| `NEON_CONSTRAINT_VIOLATION` | Unique/FK constraint violated | error | Validate data before insert, handle duplicates gracefully |
| `NEON_POOL_EXHAUSTED` | Connection pool exhausted | critical | Increase pool size, investigate connection leaks |

### **Apify Integration Errors (APIFY_*)**

| Code | Description | Severity | Recovery Action |
|------|-------------|----------|-----------------|
| `APIFY_TIMEOUT` | Scrape exceeded timeout (30s default) | error | Increase timeout to 60s, retry with backoff |
| `APIFY_RATE_LIMIT` | API rate limit exceeded (100 req/min) | warning | Implement rate limiter, wait 60s before retry |
| `APIFY_AUTH_FAIL` | Authentication failed (invalid token) | critical | Check API key, rotate if compromised |
| `APIFY_QUOTA_EXCEED` | Monthly quota exceeded | critical | Upgrade plan or pause scraping until reset |
| `APIFY_ACTOR_FAIL` | Actor execution failed | error | Check actor logs, validate input parameters |
| `APIFY_PARSE_ERR` | Failed to parse scrape results | error | Validate HTML structure, update selectors |
| `APIFY_NO_RESULTS` | Scrape returned zero results | warning | Verify URL accessibility, check selector accuracy |

### **Email Verification Errors (MV_*)**

| Code | Description | Severity | Recovery Action |
|------|-------------|----------|-----------------|
| `MV_AUTH_FAIL` | MillionVerifier authentication failed | critical | Verify API key, check account status |
| `MV_QUOTA_EXCEED` | Verification quota exceeded | warning | Upgrade plan or throttle verification requests |
| `MV_INVALID_EMAIL` | Email format validation failed | info | Skip verification, mark as gray status |
| `MV_API_ERROR` | MillionVerifier API returned error | error | Check API status page, retry after 5 minutes |
| `MV_TIMEOUT` | Verification request timed out | error | Retry with exponential backoff (max 3 attempts) |

### **Buyer Intent Tool Errors (BIT_*)**

| Code | Description | Severity | Recovery Action |
|------|-------------|----------|-----------------|
| `BIT_PARSE_FAIL` | Failed to parse intent signal JSON | error | Validate JSON format, check schema version |
| `BIT_RULE_INVALID` | Intent rule definition invalid | error | Review rule syntax, check field names |
| `BIT_NO_SIGNAL` | No intent signals detected | info | Normal operation, no action needed |
| `BIT_DB_WRITE_ERR` | Failed to write signal to database | error | Check database connection, verify permissions |

### **Pipeline Logic Engine Errors (PLE_*)**

| Code | Description | Severity | Recovery Action |
|------|-------------|----------|-----------------|
| `PLE_RULE_ERR` | Rule evaluation failed | error | Validate rule logic, check field availability |
| `PLE_STATE_INVALID` | Invalid pipeline state transition | error | Review state machine definition, check transitions |
| `PLE_QUEUE_FULL` | Lead queue capacity exceeded | warning | Increase queue size or process backlog |
| `PLE_CYCLE_DETECTED` | Infinite loop detected in rules | critical | Review rule dependencies, add cycle detection |

### **Composio Integration Errors (COMPOSIO_*)**

| Code | Description | Severity | Recovery Action |
|------|-------------|----------|-----------------|
| `COMPOSIO_TIMEOUT` | MCP request exceeded timeout | error | Retry with exponential backoff, increase timeout |
| `COMPOSIO_AUTH_FAIL` | MCP authentication failed | critical | Check API key, verify token expiration |
| `COMPOSIO_RATE_LIMIT` | MCP rate limit exceeded | warning | Implement rate limiting, queue requests |
| `COMPOSIO_SERVICE_DOWN` | Composio service unavailable | critical | Check status page, wait for service recovery |
| `COMPOSIO_INVALID_PAYLOAD` | Request payload validation failed | error | Verify HEIR/ORBT format, check required fields |

### **Firebase Sync Errors (FIREBASE_*)**

| Code | Description | Severity | Recovery Action |
|------|-------------|----------|-----------------|
| `FIREBASE_WRITE_ERR` | Failed to write to Firestore | error | Check token permissions, verify collection name |
| `FIREBASE_AUTH_ERR` | Firebase authentication failed | critical | Verify service account credentials, rotate keys |
| `FIREBASE_QUOTA_ERR` | Firestore quota exceeded | warning | Optimize writes, increase quota limits |
| `FIREBASE_RULE_ERR` | Security rule denied operation | error | Review firestore.rules, update permissions |

### **General System Errors (SYS_*)**

| Code | Description | Severity | Recovery Action |
|------|-------------|----------|-----------------|
| `SYS_MEMORY_ERR` | Out of memory condition | critical | Increase memory allocation, optimize data structures |
| `SYS_DISK_FULL` | Disk space exhausted | critical | Clean up logs, archive old data, expand storage |
| `SYS_NETWORK_ERR` | Network connectivity lost | critical | Check network status, verify DNS resolution |
| `SYS_CONFIG_ERR` | Configuration file invalid | critical | Validate JSON/YAML syntax, restore from backup |

### **Doctrine Compliance Errors (DOCTRINE_*)**

| Code | Description | Severity | Recovery Action |
|------|-------------|----------|-----------------|
| `DOCTRINE_ID_INVALID` | unique_id format validation failed | error | Validate 6-part dotted format, check altitude values |
| `DOCTRINE_PROCESS_INVALID` | process_id format invalid | error | Ensure Verb+Object+Context format, max 60 chars |
| `DOCTRINE_MISSING_FIELD` | Required doctrine field missing | error | Add missing field (agent_name, process_id, etc.) |

---

## Error Logging Best Practices

### **1. Always Include Context**

```javascript
// ❌ Bad: Generic error message
throw new Error('Scrape failed');

// ✅ Good: Context-rich error message
throw new Error(
  `Apify scrape failed for company_id=${companyId}, ` +
  `url=${url}, reason=timeout, duration=35000ms, ` +
  `actor=${actorName}, run_id=${runId}`
);
```

### **2. Use Appropriate Severity Levels**

```javascript
// Info: Expected behavior, no action needed
logError({ severity: 'info', message: 'Contact already exists, skipping' });

// Warning: Degraded service, review within 24h
logError({ severity: 'warning', message: 'Email confidence 75% (below 80% threshold)' });

// Error: Operation failed, retry possible, investigate within 4h
logError({ severity: 'error', message: 'Apify timeout, will retry in 60s' });

// Critical: System failure, immediate action required (15 min response)
logError({ severity: 'critical', message: 'Database connection pool exhausted' });
```

### **3. Include Stack Traces**

```javascript
try {
  await scrapeCompany(url);
} catch (error) {
  await logError({
    agentName: 'Apify Orchestrator',
    processId: 'Enrich Contacts from Apify',
    uniqueId: '04.01.02.05.10000.001',
    severity: 'error',
    message: `Scrape failed: ${error.message}`,
    error // <-- Automatically captures stack trace
  });
  throw error;
}
```

### **4. Implement Retry Logic**

```javascript
async function retryWithLogging(operation, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      const severity = attempt === maxRetries ? 'error' : 'warning';

      await logError({
        agentName: 'Retry Handler',
        processId: operation.name,
        uniqueId: operation.uniqueId,
        severity,
        message: `Attempt ${attempt}/${maxRetries} failed: ${error.message}`,
        error
      });

      if (attempt === maxRetries) throw error;

      // Exponential backoff: 2^attempt seconds
      await sleep(Math.pow(2, attempt) * 1000);
    }
  }
}
```

### **5. Add Error Code Tags**

```javascript
class ApifyTimeoutError extends Error {
  constructor(message, context) {
    super(message);
    this.code = 'APIFY_TIMEOUT';
    this.context = context;
  }
}

// Usage
try {
  await scrape(url, { timeout: 30000 });
} catch (error) {
  if (error.code === 'APIFY_TIMEOUT') {
    // Handle timeout specifically
    await retryWithLongerTimeout(url, { timeout: 60000 });
  }
}
```

---

## Firebase Sync Configuration

### **Automatic Sync Schedule**

The error sync script runs automatically every **60 seconds** to transfer new errors from Neon to Firebase.

**Sync Behavior**:
- Queries `shq_error_log` WHERE `firebase_synced` IS FALSE
- Batch size: 100 errors per run
- Transforms to Firestore document format
- Writes via Composio MCP Firebase connector
- Marks synced rows with `firebase_synced = TRUE`

### **Manual Sync**

```bash
# Run sync once
npm run sync:errors

# Expected output:
# 🔄 Starting error sync to Firebase...
# 📊 Found 12 errors to sync
# ✅ Success: 12
# ❌ Failed: 0
# 📊 Total: 12
```

### **Sync Health Monitoring**

```sql
-- Check last successful sync time
SELECT MAX(last_touched) as last_sync_time
FROM shq_error_log
WHERE firebase_synced = TRUE;

-- Count pending errors
SELECT COUNT(*) as pending_count
FROM shq_error_log
WHERE firebase_synced IS FALSE OR firebase_synced IS NULL;

-- Sync failure rate (last 24h)
SELECT
  COUNT(*) FILTER (WHERE firebase_synced = TRUE) as success,
  COUNT(*) FILTER (WHERE firebase_synced IS FALSE) as failed,
  ROUND(100.0 * COUNT(*) FILTER (WHERE firebase_synced = FALSE) / COUNT(*), 2) as failure_rate
FROM shq_error_log
WHERE timestamp > NOW() - INTERVAL '24 hours';
```

---

## Composio Credential Handling

### **Environment Variables**

The sync script requires Composio MCP credentials to write to Firebase. Configure these in your environment or CI secrets:

```bash
# .env file or CI secrets
NEON_DATABASE_URL=postgresql://user:pass@host/db
COMPOSIO_MCP_URL=http://localhost:3001
COMPOSIO_SERVICE=firebase
COMPOSIO_CRED_SCOPE=firebase.write
COMPOSIO_API_KEY=your_composio_api_key_here
FIREBASE_PROJECT_ID=barton-outreach
```

### **Credential Retrieval**

Composio automatically retrieves Firebase credentials when configured properly:

```bash
# Verify Composio has Firebase access
curl -H "Authorization: Bearer ${COMPOSIO_API_KEY}" \
  https://backend.composio.dev/api/v3/integrations/firebase

# Check Firebase connection status
curl -X POST http://localhost:3001/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "firebase_health_check",
    "data": {},
    "unique_id": "04.01.99.10.01000.001",
    "process_id": "Check Firebase Connection",
    "orbt_layer": 1,
    "blueprint_version": "1.0"
  }'
```

### **Security Best Practices**

✅ **DO**:
- Store credentials in environment variables or CI secrets
- Use Composio MCP as the only Firebase write interface
- Rotate API keys every 90 days
- Grant minimal required permissions (firebase.write only)

❌ **DO NOT**:
- Store Firebase Admin SDK credentials locally
- Allow direct Firebase writes from client applications
- Commit API keys to version control
- Share credentials across multiple environments

### **Composio Configuration**

**Connect Firebase to Composio** (one-time setup):

```bash
# Using Composio CLI
composio integration add firebase \
  --project-id barton-outreach \
  --service-account-key /path/to/service-account.json

# Verify connection
composio integration list | grep firebase
```

**Expected Output**:
```
✅ firebase (connected)
   Project: barton-outreach
   Scopes: firestore.read, firestore.write
   Connected: 2025-01-15
```

---

## Automation Schedule

### **Sync Job Configuration**

The error sync script should run automatically every 60 seconds via a scheduled job. Multiple automation options are available:

#### **Option 1: Composio Cron Job (Recommended)**

Register a cron job with Composio MCP:

```bash
composio schedule create \
  --job "sync-outreach-errors" \
  --interval "*/1 * * * *" \
  --command "npm run sync:errors" \
  --working-dir "/path/to/barton-outreach-core" \
  --env-file ".env"
```

**Job Configuration**:
```json
{
  "job_name": "sync-outreach-errors",
  "schedule": "*/1 * * * *",
  "command": "npm run sync:errors",
  "working_directory": "/path/to/barton-outreach-core",
  "timeout_seconds": 30,
  "retry_on_failure": true,
  "max_retries": 3,
  "alert_on_failure": true,
  "alert_channels": ["slack", "email"]
}
```

#### **Option 2: Node.js Daemon**

Run as a persistent background process:

```typescript
// daemon/error-sync-daemon.ts
import { CronJob } from 'cron';
import { exec } from 'child_process';

const job = new CronJob('*/1 * * * *', () => {
  console.log(`[${new Date().toISOString()}] Running error sync...`);

  exec('npm run sync:errors', (error, stdout, stderr) => {
    if (error) {
      console.error(`❌ Sync failed: ${error.message}`);
      return;
    }
    console.log(stdout);
  });
});

job.start();
console.log('✅ Error sync daemon started (every 60 seconds)');
```

**Run daemon**:
```bash
npm install cron
tsx daemon/error-sync-daemon.ts &
```

#### **Option 3: Firebase Scheduled Function**

Deploy as a Firebase Cloud Function:

```typescript
// firebase/functions/src/scheduled-sync.ts
import * as functions from 'firebase-functions';
import { exec } from 'child_process';

export const scheduledErrorSync = functions.pubsub
  .schedule('every 1 minutes')
  .onRun(async (context) => {
    console.log('Running scheduled error sync...');

    return new Promise((resolve, reject) => {
      exec('npm run sync:errors', (error, stdout) => {
        if (error) {
          console.error('Sync failed:', error);
          reject(error);
        } else {
          console.log(stdout);
          resolve(stdout);
        }
      });
    });
  });
```

**Deploy**:
```bash
cd firebase/functions
npm install
firebase deploy --only functions:scheduledErrorSync
```

#### **Option 4: System Cron (Linux/macOS)**

Add to crontab:

```bash
# Edit crontab
crontab -e

# Add this line
* * * * * cd /path/to/barton-outreach-core && npm run sync:errors >> /var/log/error-sync.log 2>&1
```

### **Monitoring Automation**

**Check job status**:
```bash
# Composio
composio schedule status sync-outreach-errors

# System cron logs
tail -f /var/log/error-sync.log

# Firebase Functions logs
firebase functions:log --only scheduledErrorSync
```

**Expected healthy output (every 60 seconds)**:
```
[2025-01-20T15:30:00Z] 🚀 Starting Firebase Error Sync...
[2025-01-20T15:30:01Z] 📥 Fetched 5 unsynced errors from Neon...
[2025-01-20T15:30:03Z] ✅ Successfully synced 5 errors
[2025-01-20T15:30:03Z] 📊 SYNC SUMMARY: 5 fetched, 5 synced, 0 failed
```

---

## Dashboard Usage

### **Accessing Dashboards**

**Lovable.dev Dashboard**:
- URL: `https://lovable.dev/projects/{project_id}/dashboard`
- View: Real-time error widgets and filters
- Permissions: Read-only (viewer role)

**Firebase Console**:
- URL: `https://console.firebase.google.com/project/{project_id}/firestore/data/error_log`
- View: Raw Firestore documents
- Permissions: Admin access required

### **Common Dashboard Queries**

#### **1. Find All Unresolved Critical Errors**

```
Filter:
  severity = "critical"
  resolved = false

Sort by: timestamp DESC
```

#### **2. Agent Performance Analysis**

```
Widget: Agent Error Rates (Last 7 days)
Group by: agent_name
Time range: last-7d
```

#### **3. Error Trend Detection**

```
Widget: Error Timeline
Filters:
  timestamp >= last-30d
  severity IN ["error", "critical"]
Interval: 1 day
```

#### **4. Resolution Rate Tracking**

```
Widget: Resolution Rate Gauge
Time range: last-30d
Metric: (resolved = true) / (total errors) * 100
```

---

## Error Resolution Workflow

### **Step-by-Step Resolution Process**

#### **1. Detection**

```
Alert triggered → Slack notification → Ops team notified
```

#### **2. Triage**

```
1. Log into Firebase dashboard
2. Filter errors:
   - severity: "critical" OR "error"
   - resolved: false
   - timestamp: last 24h
3. Sort by severity (critical first)
4. Identify highest priority error
```

#### **3. Investigation**

```
1. Click error row → View full details
2. Review:
   - Error message
   - Stack trace
   - Process ID
   - Unique ID
   - Agent name
   - Timestamp
3. Correlate with:
   - Recent deployments
   - System logs
   - External service status
```

#### **4. Fix Implementation**

```
1. Identify root cause
2. Implement fix (code change, config update, or data correction)
3. Test fix in development
4. Deploy to production
5. Monitor error rate
```

#### **5. Resolution Documentation**

```
1. Mark error as resolved in dashboard
2. Add resolution notes:
   "Fixed by increasing Apify timeout from 30s to 60s.
    Deployed in commit abc123.
    Monitoring for 24h to confirm resolution."
3. Update runbook if new solution discovered
```

---

## Alerting Configuration

### **Severity-Based Alerts**

| Severity | Threshold | Notification | Escalation |
|----------|-----------|--------------|------------|
| Critical | Any single error | Immediate push + Slack + Email | Page on-call engineer after 15 min |
| Error | >10 in 1 hour | Slack | Email to team lead after 1 hour |
| Warning | >50 in 1 hour | Dashboard only | Email summary daily |
| Info | N/A | Dashboard only | Weekly digest |

### **Alert Channels**

**Slack Integration**:
```json
{
  "channel": "#ops-alerts",
  "webhook": "https://hooks.slack.com/services/...",
  "format": ":rotating_light: **Critical Error Detected**\n\nAgent: {agent_name}\nProcess: {process_id}\nMessage: {message}\n\n<{dashboard_url}|View in Dashboard>"
}
```

**Email Integration**:
```json
{
  "to": ["ops-team@example.com"],
  "from": "alerts@barton-outreach.com",
  "template": "error_alert",
  "subject": "[{severity}] Error in {agent_name}"
}
```

---

## Troubleshooting Common Issues

### **Issue 1: Sync Script Not Running**

**Symptoms**:
- Errors in Neon but not in Firebase
- Dashboard shows stale data

**Diagnosis**:
```bash
# Check if sync script is running
ps aux | grep sync-errors-to-firebase

# Check recent sync logs
tail -f logs/error-sync.log
```

**Resolution**:
```bash
# Restart sync script
npm run sync:errors

# Or restart as daemon
npm run sync:errors:watch
```

### **Issue 2: Firebase Write Permissions Denied**

**Symptoms**:
- Sync script reports "PERMISSION_DENIED" errors
- Firebase console shows no recent writes

**Diagnosis**:
```javascript
// Check Composio token permissions
curl -H "Authorization: Bearer ${COMPOSIO_TOKEN}" \
  https://backend.composio.dev/api/v3/permissions
```

**Resolution**:
```bash
# Update firestore.rules
# Add service role write permission
firebase deploy --only firestore:rules

# Verify token has firebase.firestore.write scope
```

### **Issue 3: High Error Volume**

**Symptoms**:
- Dashboard shows spike in errors
- Specific agent has >100 errors/hour

**Diagnosis**:
```sql
-- Find top error sources
SELECT
  agent_name,
  COUNT(*) as error_count,
  message
FROM shq_error_log
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY agent_name, message
ORDER BY error_count DESC
LIMIT 10;
```

**Resolution**:
1. Identify pattern (same error message repeating)
2. Pause affected agent if critical
3. Deploy fix
4. Resume agent
5. Monitor error rate drop

---

## API Reference

### **Error Logging Function**

```typescript
/**
 * Log an error to shq_error_log and optionally sync to Firebase
 */
async function logError(options: {
  agentName: string;
  processId: string;
  uniqueId: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  error?: Error;
  syncToFirebase?: boolean; // Default: false (sync script handles it)
}): Promise<{ errorId: string; neonId: number }>;
```

### **Error Sync Function**

```typescript
/**
 * Sync errors from Neon to Firebase
 */
async function syncErrors(options?: {
  batchSize?: number; // Default: 100
  dryRun?: boolean; // Default: false
}): Promise<{
  successCount: number;
  failCount: number;
  total: number;
}>;
```

---

## Maintenance Tasks

### **Daily Tasks**

- [ ] Review critical errors (should be 0)
- [ ] Check error sync health
- [ ] Verify dashboard accessibility

### **Weekly Tasks**

- [ ] Analyze error trends
- [ ] Review agent error rates
- [ ] Update error code glossary if needed
- [ ] Archive resolved errors >7 days old

### **Monthly Tasks**

- [ ] Review resolution SLA compliance
- [ ] Optimize error logging (reduce noise)
- [ ] Update alert thresholds
- [ ] Conduct error handling training

---

## Related Documentation

- **Outreach Doctrine A→Z**: `/docs/outreach-doctrine-a2z.md`
- **Database Schema**: `/docs/schema_map.json`
- **Agent Registry**: `/docs/outreach-doctrine-a2z.md#agent-registry`
- **Firebase Dashboard Spec**: `/firebase/error_dashboard_spec.json`

---

**Last Updated**: January 2025
**Maintained By**: Barton Outreach Core Team
**Contact**: ops-team@example.com

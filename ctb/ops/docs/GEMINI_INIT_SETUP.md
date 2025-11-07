# 🔮 Gemini AI Studio Initialization Guide

**System:** Barton Outreach Event-Driven Pipeline
**Target:** Google AI Studio (Gemini 2.5 Pro)
**Last Updated:** 2025-10-24

---

## 🎯 Purpose

Ensure seamless activation of all Outreach system components inside **Google AI Studio (Gemini 2.5 Pro)** for AI-assisted operations, monitoring, and automation.

---

## 1️⃣ Environment Variables Auto-Detection

Gemini reads from `.env` / `.env.example` files in your repository.

### Required Variables

Confirm these exist before importing to Gemini Studio:

```bash
# Database
NEON_DATABASE_URL=postgresql://Marketing%20DB_owner:password@host/Marketing%20DB?sslmode=require
NEON_PASSWORD=your_neon_password

# n8n Orchestration
N8N_BASE_URL=https://dbarton.app.n8n.cloud
N8N_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Firebase (Future - Phase 2/3)
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_PROJECT_ID=your_firebase_project

# Composio (Agent Automation)
COMPOSIO_API_KEY=your_composio_api_key

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key
GEMINI_PROJECT_ID=your_gcp_project_id

# External APIs
APIFY_TOKEN=your_apify_token
MILLIONVERIFIER_KEY=your_millionverifier_key
```

### Create .env.example

```bash
# Copy template
cp .env.example.template .env.example

# Or create manually
cat > .env.example << 'EOF'
NEON_DATABASE_URL=postgresql://user:password@host/database?sslmode=require
N8N_BASE_URL=https://your-instance.app.n8n.cloud
N8N_API_KEY=your_n8n_api_key
GEMINI_API_KEY=your_gemini_api_key
GEMINI_PROJECT_ID=your_gcp_project
EOF
```

---

## 2️⃣ Automatic Tool Linking

When Gemini imports the repo, it will automatically detect and link these tools:

| Tool | Method | Variable Source | Purpose |
|------|--------|-----------------|---------|
| **Neon** | `neon.query(sql)` | `NEON_DATABASE_URL` | Database queries & analytics |
| **n8n** | `n8n.trigger(workflowName, payload)` | `N8N_BASE_URL`, `N8N_API_KEY` | Trigger workflows & check status |
| **Firebase** | `firebase.write(collection, doc)` | `FIREBASE_API_KEY` | Cloud storage & real-time sync |
| **Composio** | `composio.run(task)` | `COMPOSIO_API_KEY` | Agent automation tasks |
| **HTTP** | `http.post(url, data)` | Built-in | External API calls |

### Tool Configuration File

Create `gemini_tools_config.json`:

```json
{
  "tools": [
    {
      "name": "neon",
      "type": "database",
      "connection": {
        "url": "env:NEON_DATABASE_URL",
        "ssl": true
      },
      "capabilities": ["query", "analytics", "monitoring"]
    },
    {
      "name": "n8n",
      "type": "automation",
      "baseURL": "env:N8N_BASE_URL",
      "auth": {
        "type": "header",
        "header": "X-N8N-API-KEY",
        "value": "env:N8N_API_KEY"
      },
      "endpoints": {
        "workflows": "/api/v1/workflows",
        "executions": "/api/v1/executions",
        "trigger": "/webhook/{workflowName}"
      }
    },
    {
      "name": "firebase",
      "type": "storage",
      "apiKey": "env:FIREBASE_API_KEY",
      "projectId": "env:FIREBASE_PROJECT_ID"
    },
    {
      "name": "composio",
      "type": "agent",
      "apiKey": "env:COMPOSIO_API_KEY",
      "baseURL": "https://backend.composio.dev"
    }
  ]
}
```

---

## 3️⃣ Gemini Studio Setup Steps

### Step 1: Prepare Repository

```bash
# Create .env.example (no secrets)
cat > .env.example << 'EOF'
NEON_DATABASE_URL=your_neon_url
N8N_BASE_URL=https://your-n8n.app.n8n.cloud
N8N_API_KEY=your_n8n_key
GEMINI_API_KEY=your_gemini_key
GEMINI_PROJECT_ID=your_gcp_project
EOF

# Create ZIP (or use GitHub link)
cd barton-outreach-core
zip -r ../barton-outreach.zip . -x "*.git*" "node_modules/*" ".env"
```

### Step 2: Upload to Gemini Studio

1. Go to **Google AI Studio** (https://aistudio.google.com)
2. Create new project: "Barton Outreach System"
3. Upload ZIP or connect GitHub repository
4. Wait for import to complete

### Step 3: Import Environment Variables

1. Navigate to **Environment → Project Variables**
2. Click **Import from .env**
3. Select `.env.example` (or paste manually)
4. Verify all variables appear:
   - ✅ NEON_DATABASE_URL
   - ✅ N8N_BASE_URL
   - ✅ N8N_API_KEY
   - ✅ GEMINI_API_KEY
   - ✅ GEMINI_PROJECT_ID

### Step 4: Enable Tools

In the **Tools** panel, enable:

- ✅ **Neon** → Database access (for queries)
- ✅ **HTTP** → External API calls (for n8n, Composio)
- ✅ **Firebase** → Cloud write access (future)
- ✅ **Code Interpreter** → Python/JavaScript execution

### Step 5: Configure Tool Permissions

```javascript
// In Gemini Studio Settings → Tool Permissions
{
  "neon": {
    "allowedOperations": ["SELECT", "INSERT", "UPDATE"],
    "restrictedOperations": ["DELETE", "DROP", "TRUNCATE"],
    "maxRowsPerQuery": 10000
  },
  "n8n": {
    "allowedEndpoints": ["/api/v1/workflows", "/api/v1/executions", "/webhook/*"],
    "rateLimits": {
      "requestsPerMinute": 60
    }
  },
  "http": {
    "allowedDomains": ["app.n8n.cloud", "composio.dev", "api.apify.com"],
    "maxRequestsPerMinute": 100
  }
}
```

---

## 4️⃣ Testing the Connection

### Test 1: Neon Database Connection

```javascript
// In Gemini's code console
const result = await neon.query("SELECT NOW() as current_time");
console.log(result);

// Expected output:
// { rows: [{ current_time: "2025-10-24T12:00:00Z" }] }
```

### Test 2: n8n Workflow Trigger

```javascript
const response = await n8n.trigger("WF_Validate_Company", {
  event_id: 1,
  event_type: "company_created",
  payload: {
    id: 123,
    company: "Test Company",
    website: "https://test.com"
  }
});

console.log(response);

// Expected output:
// { status: 200, data: { workflow_name: "Validate_Company", status: "ok" } }
```

### Test 3: Query Pipeline Stats

```javascript
const stats = await neon.query(`
  SELECT * FROM marketing.v_phase_stats
  ORDER BY phase
`);

console.log(stats.rows);

// Expected output:
// [
//   { phase: "enrichment", total_runs: 1247, error_rate: 1.2, ... },
//   { phase: "intelligence", total_runs: 42, error_rate: 0.0, ... },
//   ...
// ]
```

### Test 4: Check Error Queue

```javascript
const errors = await neon.query(`
  SELECT * FROM marketing.v_error_recent
  LIMIT 10
`);

if (errors.rows.length > 0) {
  console.log("⚠️ Found errors:", errors.rows);
} else {
  console.log("✅ No recent errors");
}
```

---

## 5️⃣ Security Notes

### Environment Variables

- ❌ **NEVER** commit `.env` to version control
- ✅ **ALWAYS** use `.env.example` as template (no secrets)
- ✅ Use **Vertex AI Secret Manager** in production
- ✅ Rotate keys every 90 days

### Key Rotation Audit

```bash
# Record rotation in ops/audit_log
echo "$(date): Rotated N8N_API_KEY (rotation_id: ROT-2025-001)" >> ops/audit_log
```

### Access Control

```javascript
// Gemini Studio → Settings → Access Control
{
  "roles": {
    "admin": ["read", "write", "execute", "delete"],
    "operator": ["read", "execute"],
    "viewer": ["read"]
  },
  "users": {
    "admin@example.com": "admin",
    "ops@example.com": "operator",
    "team@example.com": "viewer"
  }
}
```

### Rate Limiting

```javascript
{
  "rateLimits": {
    "neon": {
      "queriesPerMinute": 100,
      "maxQueryDuration": "30s"
    },
    "n8n": {
      "triggersPerMinute": 60,
      "executionsPerHour": 1000
    },
    "http": {
      "requestsPerMinute": 100
    }
  }
}
```

---

## 6️⃣ Gemini Watchdog (Optional)

### Automated Monitoring Function

Create `gemini_watchdog.yaml`:

```yaml
name: OutreachWatchdog
description: Monitor pipeline health and alert on errors
schedule: "*/15 * * * *" # Every 15 minutes

actions:
  - name: CheckPhaseStats
    query: |
      SELECT * FROM marketing.v_phase_stats
      WHERE error_rate > 5.0
    alert:
      condition: "rows.length > 0"
      message: "⚠️ High error rate detected in phase: {{phase}}"
      channels: ["slack", "email"]

  - name: CheckEventQueue
    query: |
      SELECT * FROM marketing.v_event_queue_status
      WHERE oldest_age_minutes > 30
    alert:
      condition: "rows.length > 0"
      message: "🚨 Events stuck in queue for {{oldest_age_minutes}} minutes"
      channels: ["slack", "pagerduty"]

  - name: CheckWorkflowHealth
    query: |
      SELECT * FROM marketing.v_workflow_health
      WHERE health_status = 'critical'
    alert:
      condition: "rows.length > 0"
      message: "🔴 Critical workflow failure: {{workflow_name}}"
      channels: ["slack", "pagerduty"]

notifications:
  slack:
    webhook: "env:SLACK_WEBHOOK_URL"
    channel: "#outreach-alerts"
  email:
    to: ["ops@example.com"]
    from: "gemini-watchdog@example.com"
  pagerduty:
    apiKey: "env:PAGERDUTY_API_KEY"
    serviceId: "PXXXXXX"
```

### Deploy Watchdog

```javascript
// In Gemini Studio → Functions → Create New
const watchdog = {
  name: "OutreachWatchdog",
  schedule: "*/15 * * * *",
  execute: async () => {
    // Check phase stats
    const stats = await neon.query(`
      SELECT * FROM marketing.v_phase_stats
      WHERE error_rate > 5.0
    `);

    if (stats.rows.length > 0) {
      await http.post(process.env.SLACK_WEBHOOK_URL, {
        text: `⚠️ High error rate detected!\n${JSON.stringify(stats.rows, null, 2)}`
      });
    }

    // Check event queue
    const queue = await neon.query(`
      SELECT * FROM marketing.v_event_queue_status
      WHERE oldest_age_minutes > 30
    `);

    if (queue.rows.length > 0) {
      await http.post(process.env.SLACK_WEBHOOK_URL, {
        text: `🚨 Events stuck in queue!\n${JSON.stringify(queue.rows, null, 2)}`
      });
    }

    return { status: "ok", checked_at: new Date().toISOString() };
  }
};
```

---

## 7️⃣ Gemini AI Prompts for Operations

### Pre-configured Prompts

Save these in Gemini Studio → Saved Prompts:

**1. Daily Health Check**
```
Check the outreach pipeline health:
1. Query marketing.v_phase_stats
2. Query marketing.v_workflow_health
3. Query marketing.v_event_queue_status
4. Summarize any issues and recommend actions
```

**2. Error Investigation**
```
Investigate recent errors:
1. Query marketing.v_error_recent (last 50)
2. Group by event_type
3. Identify root causes
4. Suggest fixes
```

**3. Performance Analysis**
```
Analyze pipeline performance:
1. Query marketing.v_daily_throughput (last 7 days)
2. Calculate trends
3. Identify bottlenecks
4. Recommend optimizations
```

**4. Trigger Workflow**
```
Trigger workflow {workflow_name} with:
- Record ID: {record_id}
- Event type: {event_type}
- Batch ID: {batch_id}

Then check execution status and report results.
```

---

## 8️⃣ Advanced Features

### AI-Assisted Query Building

```javascript
// Ask Gemini to build queries
const prompt = `
Generate a SQL query to:
1. Find all companies validated in the last 24 hours
2. Show their promotion status
3. Count slots created per company
4. Filter where error_rate > 0
`;

const query = await gemini.generateSQL(prompt);
const results = await neon.query(query);
```

### Automated Troubleshooting

```javascript
// Gemini can diagnose issues
const issue = {
  symptom: "High error rate in enrichment phase",
  errorRate: 15.3,
  affectedWorkflow: "WF_Enrich_Contacts"
};

const diagnosis = await gemini.diagnose(issue);
// Returns: {
//   rootCause: "Apify API rate limit exceeded",
//   recommendation: "Increase throttle delay from 5s to 10s",
//   action: "UPDATE workflow configuration..."
// }
```

### Predictive Analytics

```javascript
// Gemini can predict trends
const forecast = await gemini.forecast({
  metric: "daily_throughput",
  period: "next_7_days",
  data: await neon.query("SELECT * FROM marketing.v_daily_throughput")
});

console.log(forecast);
// { prediction: [1200, 1250, 1300, ...], confidence: 0.89 }
```

---

## 9️⃣ Troubleshooting

### Gemini Can't Connect to Neon

**Error:** `Connection refused` or `Authentication failed`

**Fix:**
1. Check NEON_DATABASE_URL format
2. Verify password is URL-encoded
3. Enable IP whitelist in Neon dashboard
4. Add Gemini's IP range to allowed connections

```bash
# Test connection manually
psql "$NEON_DATABASE_URL" -c "SELECT 1"
```

### n8n Webhooks Not Triggering

**Error:** `HTTP 404 Not Found` or `Webhook not registered`

**Fix:**
1. Verify webhook URLs in n8n UI
2. Check workflow is active
3. Update `n8n_webhook_registry.json`
4. Test with curl first

```bash
curl -X POST "$N8N_BASE_URL/webhook/validate-company" \
  -H "Content-Type: application/json" \
  -d '{"id": 123, "event_type": "test"}'
```

### Environment Variables Not Loading

**Error:** `undefined` when accessing `process.env.VARIABLE`

**Fix:**
1. Reload environment in Gemini Studio
2. Check variable names match exactly
3. Restart Gemini function
4. Use `env:VARIABLE` syntax in tool configs

---

## 🔟 Next Steps

### After Setup

1. ✅ Run all tests in section 4 (Testing the Connection)
2. ✅ Deploy Watchdog function (section 6)
3. ✅ Save operational prompts (section 7)
4. ✅ Set up Slack/email alerts
5. ✅ Schedule key rotation (every 90 days)

### Integration Checklist

- [ ] .env.example created with all variables
- [ ] gemini_tools_config.json configured
- [ ] Repository imported to Gemini Studio
- [ ] Environment variables verified
- [ ] Tools enabled and tested
- [ ] Neon connection successful
- [ ] n8n trigger tested
- [ ] Watchdog deployed
- [ ] Alerts configured
- [ ] Team access granted

---

## 📚 Related Documentation

- **ops/E2E_TEST_AND_ROLLBACK.md** - Testing procedures
- **ops/README_OUTREACH_OPS.md** - Operational guide
- **docs/PIPELINE_EVENT_FLOW.md** - Architecture overview
- **workflows/n8n_webhook_registry.json** - Webhook mappings

---

**Status:** 🟢 Ready for Gemini Integration
**Last Updated:** 2025-10-24
**Version:** 1.0.0

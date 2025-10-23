<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/analysis
Barton ID: 06.01.01
Unique ID: CTB-C61F5689
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
-->

# 💰 Apify Cost Governance & Usage Control Doctrine

**Date**: 2025-10-24
**Doctrine Segment**: 04.04.07 (Apify Cost Management)
**Status**: ✅ Active
**Version**: 2.0

---

## 📋 Purpose

The Apify Cost Governance system implements **four layers of protection** to prevent budget overruns and ensure responsible API usage for the Barton Outreach Core enrichment pipeline.

**Primary Objectives**:
1. **Prevent Cost Overruns**: Cap spending at $25/month maximum
2. **Enforce Usage Limits**: Prevent API abuse and rate limit violations
3. **Provide Visibility**: Track all actor runs with cost estimates
4. **Enable Forecasting**: Support budget planning and optimization
5. **Automate Safety**: Self-healing system with automatic pause mechanism

**Barton Doctrine Segment**: 04.04.07
- **04** = Database layer
- **04** = Marketing subhive
- **07** = Apify cost management microprocess

---

## 🛡️ Four-Layer Protection Architecture

### Layer 1: Pre-Flight Validation (Application Layer)

**File**: `apps/outreach-process-manager/utils/validateApifyInput.js`
**Purpose**: Client-side validation before MCP call
**Enforcement**: Immediate (throws errors)

#### Limits Enforced

**Leads Finder Actor**:
```javascript
{
  MAX_DOMAINS: 50,        // Max company domains per run
  MAX_LEADS: 500,         // Max leads per run
  MAX_TIMEOUT: 300,       // Max timeout (5 minutes)
  MAX_EST_COST: 1.50      // Max cost per run ($1.50)
}
```

**LinkedIn Scraper Actor**:
```javascript
{
  MAX_PROFILES: 2000,     // Max profiles per run
  MAX_TIMEOUT: 600,       // Max timeout (10 minutes)
  MAX_EST_COST: 5.00      // Max cost per run ($5.00)
}
```

#### Cost Estimation Formula

**Leads Finder**:
```
Cost = (max_leads × $0.002) + $0.02
Example: 100 leads = (100 × 0.002) + 0.02 = $0.22
```

**LinkedIn Scraper**:
```
Cost = (max_profiles × $0.0015) + $0.05
Example: 200 profiles = (200 × 0.0015) + 0.05 = $0.35
```

#### Validation Behavior

**Hard Limits (throws error)**:
- Domain count exceeds MAX_DOMAINS
- Estimated cost exceeds MAX_EST_COST

**Soft Limits (caps and warns)**:
- max_leads exceeds limit → capped to 500
- timeout exceeds limit → capped to 300s

#### Usage Example

```javascript
import { validateApifyInput } from './utils/validateApifyInput.js';

const input = {
  actorId: "code_crafter~leads-finder",
  runInput: {
    company_domain: ["advantage.tech", "valleyhealth.org"],
    max_leads: 100,
    timeout: 180
  }
};

try {
  const sanitized = validateApifyInput(input);
  // Returns: { ...input, estimated_cost: 0.22 }

  // Now safe to send to Composio MCP
  await postToComposioMCP(sanitized);
} catch (error) {
  console.error('❌ Validation failed:', error.message);
  // Error: "Too many domains (52) – max 50"
  // Error: "Estimated cost $1.75 exceeds limit $1.50"
}
```

---

### Layer 2: MCP Policy Firewall (Composio Layer)

**File**: `analysis/COMPOSIO_MCP_POLICY_APIFY_LIMITS.json`
**Purpose**: Server-side enforcement at MCP endpoint
**Enforcement**: Automatic (tool pause on limit reached)

#### Policy Configuration

```json
{
  "tool_name": "apify_run_actor_sync_get_dataset_items",
  "limits": {
    "max_daily_runs": 20,              // Maximum 20 runs per day
    "max_concurrent_runs": 3,          // Maximum 3 simultaneous runs
    "max_leads_per_run": 500,          // Maximum 500 leads per execution
    "max_runtime_seconds": 300,        // Maximum 5-minute timeout
    "max_monthly_cost_usd": 25         // Monthly budget cap: $25
  },
  "actions": {
    "on_limit_reached": "pause_tool",
    "on_warning": "log_to_mantis",
    "notify": "validator@bartonhq.com"
  }
}
```

#### Enforcement Points

**Daily Run Limit (20/day)**:
- Prevents runaway automation
- Resets at midnight UTC
- Pauses tool after 20th run

**Concurrent Run Limit (3 simultaneous)**:
- Prevents resource exhaustion
- Queues additional runs
- Ensures Apify actor availability

**Monthly Budget Cap ($25)**:
- Hard financial limit
- Tracked via actor_usage_log
- Triggers automatic tool pause

#### Actions on Limit Reached

1. **pause_tool**: Tool becomes unavailable
2. **log_to_mantis**: Alert logged to monitoring system
3. **notify**: Email sent to validator@bartonhq.com

**Notification Format**:
```
Subject: 🚨 Apify Tool Paused - Limit Reached

Tool: apify_run_actor_sync_get_dataset_items
Limit: max_daily_runs (20)
Current: 20 runs today
Status: PAUSED

Action Required:
1. Review usage via generate_actor_usage_report()
2. Verify no abuse or errors
3. Re-enable tool if appropriate
4. Consider adjusting limits if needed

View details: http://localhost:3001/tools/status
```

---

### Layer 3: Neon Ledger (Database Layer)

**Table**: `marketing.actor_usage_log`
**Migration**: `2025-10-24_create_actor_usage_log.sql`
**Purpose**: Historical tracking and cost reporting

#### Schema

```sql
CREATE TABLE marketing.actor_usage_log (
    id SERIAL PRIMARY KEY,
    run_id TEXT NOT NULL,                    -- Apify run ID
    actor_id TEXT NOT NULL,                  -- Actor identifier
    dataset_id TEXT,                         -- Result dataset
    tool_name TEXT,                          -- MCP tool used
    estimated_cost NUMERIC(6,2),             -- Cost in USD
    total_items INTEGER,                     -- Items processed
    run_started_at TIMESTAMPTZ,              -- Start time
    run_completed_at TIMESTAMPTZ,            -- Completion time
    status TEXT,                             -- running/success/failed/aborted
    notes TEXT,                              -- Human-readable notes
    metadata JSONB,                          -- Additional run data
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);
```

#### Logging Workflow

```
1. Actor Run Starts
   INSERT INTO actor_usage_log (
     run_id, actor_id, estimated_cost, status='running'
   )

2. Actor Completes
   UPDATE actor_usage_log
   SET status='success',
       run_completed_at=NOW(),
       total_items=1500,
       dataset_id='dataset_xyz'
   WHERE run_id='run_abc123'

3. Generate Reports
   SELECT * FROM generate_actor_usage_report('2025-10-01', '2025-10-31')
```

#### Helper Functions

**1. generate_actor_usage_report(start_date, end_date)**

Returns per-actor aggregates:
```sql
SELECT * FROM marketing.generate_actor_usage_report(
  '2025-10-01'::DATE,
  '2025-10-31'::DATE
);

-- Returns:
-- actor_id                        | total_runs | successful_runs | failed_runs | total_items | total_cost | avg_cost_per_run
-- code_crafter~leads-finder       | 15         | 14              | 1           | 1500        | 3.30       | 0.22
-- apify~linkedin-profile-scraper  | 1          | 1               | 0           | 2000        | 3.05       | 3.05
```

**2. get_monthly_cost_summary(months_back)**

Monthly breakdown:
```sql
SELECT * FROM marketing.get_monthly_cost_summary(6);

-- Returns:
-- month    | actor_id                        | total_runs | total_cost | total_items
-- 2025-10  | code_crafter~leads-finder       | 15         | 3.30       | 1500
-- 2025-10  | apify~linkedin-profile-scraper  | 1          | 3.05       | 2000
-- 2025-09  | code_crafter~leads-finder       | 20         | 4.40       | 2000
```

**3. get_actor_run_details(actor_id, days_back)**

Detailed run history:
```sql
SELECT * FROM marketing.get_actor_run_details(
  'code_crafter~leads-finder',
  30
);

-- Returns:
-- run_id      | dataset_id   | status  | total_items | estimated_cost | duration_minutes | notes
-- run_abc123  | dataset_xyz  | success | 100         | 0.22           | 3.5              | Trial enrichment
```

#### Indexes (6 total)

- `idx_actor_usage_log_run_id` - Run lookup
- `idx_actor_usage_log_actor_id` - Actor filtering
- `idx_actor_usage_log_status` - Status filtering
- `idx_actor_usage_log_started_at` - Chronological queries
- `idx_actor_usage_log_completed_at` - Completion tracking
- `idx_actor_usage_log_actor_started` - Composite queries

---

### Layer 4: Daily Cost Guard Job (Scheduled Enforcement)

**File**: `apps/outreach-process-manager/jobs/apify_cost_guard.json`
**Purpose**: End-of-day budget verification with automatic pause
**Schedule**: Daily at 11:00 PM (23:00)

#### Job Configuration

```json
{
  "name": "Apify Cost Guard",
  "description": "Daily check of Apify run costs; pauses tool if threshold exceeded.",
  "tool": "neon_execute_sql",
  "schedule": "RRULE:FREQ=DAILY;BYHOUR=23;BYMINUTE=0;BYSECOND=0",
  "query": "SELECT SUM(estimated_cost) AS total_cost FROM marketing.actor_usage_log WHERE date(run_started_at)=current_date;",
  "postProcess": {
    "condition": "$RESULT.total_cost > 25",
    "tool": "composio_pause_tool",
    "input": {
      "tool_name": "apify_run_actor_sync_get_dataset_items"
    }
  }
}
```

#### Execution Flow

```
Daily at 11:00 PM
    ↓
Query today's total cost
    ↓
SUM(estimated_cost) from actor_usage_log
WHERE date(run_started_at) = current_date
    ↓
Result: $18.75 (example)
    ↓
Condition: $RESULT.total_cost > 25
    ↓
┌────────────────────────────────────┐
│ FALSE ($18.75 ≤ $25)               │
│ → Continue normal operations       │
│ → Log: "Daily cost OK: $18.75/$25"│
└────────────────────────────────────┘

┌────────────────────────────────────┐
│ TRUE ($26.50 > $25)                │
│ → Execute composio_pause_tool      │
│ → Tool: apify_run_actor_sync_...   │
│ → Status: PAUSED                   │
│ → Notify: validator@bartonhq.com   │
└────────────────────────────────────┘
```

#### Safety Rationale

**Why 11:00 PM?**
- Final check before day ends
- Prevents next-day unauthorized runs
- Allows time for manual intervention before midnight

**Why pause vs alert?**
- Proactive protection (stops spending)
- Requires deliberate re-enable (prevents accidents)
- Forces usage review before continuation

---

### Layer 5: Apify Native Console Limits (Optional)

**Platform**: Apify Dashboard (https://console.apify.com)
**Purpose**: Platform-level spending caps
**Configuration**: Manual via Apify account settings

#### Recommended Settings

**Account Limits**:
- Monthly spending cap: $30 (buffer above $25 internal cap)
- Per-run timeout: 600 seconds (10 minutes)
- Email notifications: Enabled at 80% budget

**Actor-Specific Limits**:
- `code_crafter~leads-finder`: Max $2.00 per run
- `apify~linkedin-profile-scraper`: Max $6.00 per run

**Why external limits?**
- Defense-in-depth strategy
- Protects against MCP failures
- Platform-enforced hard stop
- Billing safety net

---

## 🔄 Example Workflow: Complete Run Lifecycle

### Scenario: Enrich 3 companies with 100 leads each

#### Step 1: Pre-Flight Validation

```javascript
// Application code
const input = {
  actorId: "code_crafter~leads-finder",
  runInput: {
    company_domain: ["advantage.tech", "valleyhealth.org", "tmctechnologies.com"],
    max_leads: 100,
    timeout: 180,
    contact_job_title: ["CEO", "CFO", "CHRO", "CTO"]
  }
};

// Layer 1: Pre-flight validation
const sanitized = validateApifyInput(input);
// Result: { ...input, estimated_cost: 0.22 }
console.log('✅ Pre-flight passed: $0.22 estimated');
```

#### Step 2: MCP Policy Check

```javascript
// POST to Composio MCP
const response = await fetch(
  'http://localhost:3001/tool?user_id=usr_barton_001',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      tool: 'apify_run_actor_sync_get_dataset_items',
      data: sanitized,
      unique_id: `HEIR-2025-10-ENRICHMENT-${Date.now()}`,
      process_id: `PRC-ENRICH-${Date.now()}`,
      orbt_layer: 2,
      blueprint_version: '1.0'
    })
  }
);

// Layer 2: MCP policy firewall
// Check 1: Daily runs = 15/20 ✅
// Check 2: Concurrent runs = 2/3 ✅
// Check 3: Monthly cost = $18.25/$25 ✅
// Check 4: Per-run cost = $0.22/$1.50 ✅
console.log('✅ MCP policy passed');
```

#### Step 3: Neon Logging (Before Run)

```javascript
// Layer 3: Log to actor_usage_log
const runId = response.data.run_id;

await executeSQL(`
  INSERT INTO marketing.actor_usage_log (
    run_id,
    actor_id,
    estimated_cost,
    status,
    notes
  ) VALUES (
    '${runId}',
    'code_crafter~leads-finder',
    0.22,
    'running',
    'Enrichment trial: 3 companies'
  )
`);

console.log('✅ Run logged: run_id =', runId);
```

#### Step 4: Apify Execution

```
Apify Actor: code_crafter~leads-finder
    ↓
Search LinkedIn for executives at:
  - advantage.tech
  - valleyhealth.org
  - tmctechnologies.com
    ↓
Target roles: CEO, CFO, CHRO, CTO
Max leads: 100 per company
    ↓
Duration: 3.5 minutes
Results: 87 executives found
    ↓
Dataset created: dataset_abc123xyz
```

#### Step 5: Neon Logging (After Run)

```javascript
// Update log with completion details
await executeSQL(`
  UPDATE marketing.actor_usage_log
  SET status = 'success',
      run_completed_at = NOW(),
      total_items = 87,
      dataset_id = 'dataset_abc123xyz',
      metadata = '{"companies": 3, "avg_per_company": 29}'::jsonb
  WHERE run_id = '${runId}'
`);

console.log('✅ Run completed: 87 items in 3.5 minutes');
```

#### Step 6: Daily Cost Guard (11:00 PM)

```
Scheduled Job: apify_cost_guard.json
    ↓
Query: SELECT SUM(estimated_cost) FROM actor_usage_log
       WHERE date(run_started_at) = current_date
    ↓
Result: $18.47 (includes this run: $18.25 + $0.22)
    ↓
Condition: $18.47 > $25 → FALSE ✅
    ↓
Action: None (continue normal operations)
    ↓
Log: "Daily cost OK: $18.47/$25 (73.9% used)"
```

---

## 🆘 Failsafe Procedure: Manual Tool Un-Pause

### When Tool Gets Paused

**Indicators**:
- API calls return: `{"error": "Tool paused: apify_run_actor_sync_get_dataset_items"}`
- Email notification received at validator@bartonhq.com
- Dashboard shows tool status: PAUSED

### Investigation Steps

#### 1. Check Daily Usage

```sql
-- Query today's runs
SELECT
  COUNT(*) as total_runs,
  SUM(estimated_cost) as total_cost,
  SUM(total_items) as total_items,
  COUNT(*) FILTER (WHERE status='failed') as failed_runs
FROM marketing.actor_usage_log
WHERE date(run_started_at) = current_date;

-- Expected output:
-- total_runs | total_cost | total_items | failed_runs
-- 20         | 26.50      | 2000        | 2
```

#### 2. Analyze Cost Breakdown

```sql
-- Get per-run details
SELECT * FROM marketing.get_actor_run_details(
  'code_crafter~leads-finder',
  1  -- Last 1 day
);

-- Identify expensive runs
SELECT
  run_id,
  estimated_cost,
  total_items,
  notes,
  ROUND(estimated_cost / NULLIF(total_items, 0), 4) as cost_per_item
FROM marketing.actor_usage_log
WHERE date(run_started_at) = current_date
ORDER BY estimated_cost DESC
LIMIT 10;
```

#### 3. Review for Anomalies

**Red Flags**:
- Multiple failed runs (indicates bug)
- High cost-per-item ratios (inefficient runs)
- Unusual run patterns (e.g., 20 runs in 1 hour)
- Large max_leads values (> 500)

**Green Flags**:
- Normal usage pattern (2-3 runs/day typical)
- Successful completion rates > 90%
- Cost-per-item in expected range ($0.001-$0.003)

### Un-Pause Procedure

#### Option 1: Via Composio MCP API

```javascript
// Re-enable tool via MCP endpoint
const response = await fetch(
  'http://localhost:3001/tools/resume',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      tool_name: 'apify_run_actor_sync_get_dataset_items',
      reason: 'Daily review completed - usage normal',
      authorized_by: 'validator@bartonhq.com'
    })
  }
);

console.log('✅ Tool re-enabled:', response.data);
```

#### Option 2: Via Composio Dashboard

```
1. Navigate to http://localhost:3001/tools
2. Find: apify_run_actor_sync_get_dataset_items
3. Status: PAUSED (red indicator)
4. Click: "Resume Tool"
5. Enter reason: "Budget reviewed - continuing operations"
6. Confirm action
7. Status changes to: ACTIVE (green indicator)
```

#### Option 3: Via Configuration File

```bash
# Edit policy file temporarily
nano analysis/COMPOSIO_MCP_POLICY_APIFY_LIMITS.json

# Increase max_monthly_cost_usd from 25 to 30
"max_monthly_cost_usd": 30

# Restart Composio MCP server
cd /path/to/imo-creator/mcp-servers/composio-mcp
node server.js

# Tool automatically resumes with new limits
```

### Post-Resumption Actions

1. **Document Incident**:
   ```sql
   INSERT INTO marketing.unified_audit_log (
     unique_id, process_id, action, notes
   ) VALUES (
     '04.04.07', 'PRC-TOOL-RESUME',
     'resume_apify_tool',
     'Tool paused at $26.50 daily cost. Reviewed usage, no anomalies. Resumed operations.'
   );
   ```

2. **Monitor Next Run**:
   - Watch for immediate failures
   - Verify cost estimates accurate
   - Check dataset quality

3. **Review Limits** (if needed):
   - Adjust max_daily_runs if legitimate usage
   - Increase max_monthly_cost_usd if budget allows
   - Update validateApifyInput.js limits if appropriate

---

## 📈 Expected Monthly Cost Curve

### Normal Operations Budget

**Target**: < $25/month
**Typical Usage**: $15-$20/month
**Reserve**: $5-$10 buffer for unexpected needs

### Monthly Cost Breakdown

#### Scenario 1: Conservative (Typical)

```
Leads Finder Actor:
  - 10 runs/month × 100 leads/run = 1,000 leads
  - Cost: 10 runs × $0.22 = $2.20

LinkedIn Scraper:
  - 1 run/month × 1,500 profiles = 1,500 profiles
  - Cost: 1 run × $2.30 = $2.30

Total: $4.50/month (18% of budget)
```

#### Scenario 2: Normal (Expected)

```
Leads Finder Actor:
  - 40 runs/month × 100 leads/run = 4,000 leads
  - Cost: 40 runs × $0.22 = $8.80

LinkedIn Scraper:
  - 1 run/month × 2,000 profiles = 2,000 profiles
  - Cost: 1 run × $3.05 = $3.05

Total: $11.85/month (47% of budget)
```

#### Scenario 3: Active (Near Limit)

```
Leads Finder Actor:
  - 80 runs/month × 100 leads/run = 8,000 leads
  - Cost: 80 runs × $0.22 = $17.60

LinkedIn Scraper:
  - 2 runs/month × 2,000 profiles = 4,000 profiles
  - Cost: 2 runs × $3.05 = $6.10

Total: $23.70/month (95% of budget)
```

#### Scenario 4: Over Budget (Triggers Pause)

```
Leads Finder Actor:
  - 100 runs/month × 100 leads/run = 10,000 leads
  - Cost: 100 runs × $0.22 = $22.00

LinkedIn Scraper:
  - 2 runs/month × 2,000 profiles = 4,000 profiles
  - Cost: 2 runs × $3.05 = $6.10

Total: $28.10/month (112% of budget) 🔴 PAUSED
```

### Cost Optimization Strategies

**1. Batch Efficiently**:
```javascript
// BAD: Many small runs
for (const company of companies) {
  await enrichCompany([company]);  // 100 runs × $0.22 = $22
}

// GOOD: Fewer large runs
const batches = chunkArray(companies, 50);
for (const batch of batches) {
  await enrichCompanies(batch);  // 2 runs × $0.62 = $1.24
}
```

**2. Filter Strategically**:
```javascript
// Only enrich companies likely to have target executives
const filteredCompanies = companies.filter(c =>
  c.employee_count >= 50 &&  // Has org structure
  c.industry !== 'non-profit' &&  // Less likely to have CFO/CRO
  c.website_url !== null  // Can be enriched
);
```

**3. Use Cached Data**:
```javascript
// Check if already enriched recently
const needsEnrichment = await checkLastEnrichment(company_id);
if (needsEnrichment) {
  await enrichCompany(company_id);
}
```

**4. Monitor and Adjust**:
```sql
-- Weekly cost review
SELECT * FROM marketing.get_monthly_cost_summary(1);

-- If trending over budget, reduce frequency or batch size
```

---

## 🎯 Summary: Defense-in-Depth

### Protection Layers Matrix

| Layer | Enforcement | Timing | Action | Override |
|-------|-------------|--------|--------|----------|
| **1. Pre-Flight** | Client-side | Before MCP call | Throw error | Code change |
| **2. MCP Policy** | Server-side | At MCP endpoint | Pause tool | Policy file |
| **3. Neon Ledger** | Database | During/after run | Log + report | Manual SQL |
| **4. Daily Guard** | Scheduled job | 11:00 PM daily | Pause tool | Job disable |
| **5. Apify Console** | Platform | Real-time | Hard stop | Dashboard |

### Key Files Reference

```
barton-outreach-core/
├── apps/outreach-process-manager/
│   ├── migrations/
│   │   └── 2025-10-24_create_actor_usage_log.sql
│   ├── utils/
│   │   └── validateApifyInput.js
│   └── jobs/
│       ├── linkedin_monthly_update.json
│       └── apify_cost_guard.json
└── analysis/
    ├── COMPOSIO_MCP_POLICY_APIFY_LIMITS.json
    └── APIFY_COST_GOVERNANCE.md (this file)
```

### Compliance Checklist

- [x] Pre-flight validation implemented (validateApifyInput.js)
- [x] MCP policy configured (COMPOSIO_MCP_POLICY_APIFY_LIMITS.json)
- [x] Database logging enabled (marketing.actor_usage_log)
- [x] Daily guard scheduled (apify_cost_guard.json)
- [x] Reporting functions available (3 SQL functions)
- [x] Documentation complete (APIFY_COST_GOVERNANCE.md)
- [x] Barton Doctrine segment assigned (04.04.07)
- [x] Manual override procedure documented
- [ ] Apify console limits configured (optional)
- [ ] Monitoring dashboard integrated (future)

### Quick Reference Commands

**Check today's cost**:
```sql
SELECT SUM(estimated_cost) FROM marketing.actor_usage_log
WHERE date(run_started_at) = current_date;
```

**Monthly cost report**:
```sql
SELECT * FROM marketing.generate_actor_usage_report(
  date_trunc('month', current_date)::DATE,
  current_date
);
```

**Resume paused tool**:
```bash
curl -X POST http://localhost:3001/tools/resume \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "apify_run_actor_sync_get_dataset_items"}'
```

---

## 📚 Related Documentation

- **COMPOSIO_MCP_GLOBAL_POLICY.md** - Global Composio MCP architecture
- **LINKEDIN_REFRESH_DOCTRINE.md** - LinkedIn monthly sync (04.04.06)
- **OUTREACH_CORE_FULL_PROCESS_VERIFICATION.md** - Complete system verification
- **FINAL_SCHEMA_COMPLIANCE_REPORT.md** - Schema compliance audit

---

**Status**: ✅ **Apify Cost Governance Active**
**Doctrine Segment**: 04.04.07
**Monthly Budget**: $25 (hard cap)
**Current Enforcement**: Four-layer protection enabled
**Last Updated**: 2025-10-24

# 🔄 LinkedIn Refresh Doctrine

**Date**: 2025-10-23
**Version**: 1.0
**Status**: ✅ Active
**Doctrine Segments**: 04.04.02 → 04.04.04 → 04.04.06

---

## 📋 Purpose

The LinkedIn Refresh Doctrine automates monthly updates to `marketing.people_master` by:

1. **Detecting Changes**: Comparing current LinkedIn profile data against stored records
2. **Logging Intelligence**: Recording title changes, promotions, and company moves in `people_intelligence`
3. **Triggering PLE**: Automatically launching Promoted Lead Enrichment campaigns for changed profiles
4. **Maintaining Accuracy**: Ensuring executive contact data remains current for outreach effectiveness

**Goal**: Keep `people_master` synchronized with LinkedIn's authoritative profile data through automated monthly checks, enabling timely outreach when executives change roles.

---

## 🎯 Barton Doctrine Segments

### 04.04.02 - People Master
**Purpose**: Executive contact records
**Table**: `marketing.people_master`
**Barton ID Format**: `04.04.02.XX.XXXXX.XXX`

**Key Fields**:
- `unique_id` - Person Barton ID
- `linkedin_url` - LinkedIn profile URL (lookup key)
- `title` - Current job title (comparison target)
- `company_unique_id` - Associated company

**Role in Refresh**: Source of truth for current data, updated after intelligence verification

### 04.04.04 - People Intelligence
**Purpose**: Executive movement tracking
**Table**: `marketing.people_intelligence`
**Barton ID Format**: `04.04.04.XX.XXXXX.XXX`

**Key Fields**:
- `intel_unique_id` - Intelligence Barton ID
- `person_unique_id` - FK to people_master
- `change_type` - promotion | role_change | job_change | new_company | left_company
- `previous_title` - Title before change
- `new_title` - Title after change
- `verified` - TRUE for LinkedIn-sourced data

**Role in Refresh**: Change detection log, triggers PLE workflow via INSERT trigger

### 04.04.06 - LinkedIn Refresh
**Purpose**: Monthly job tracking
**Table**: `marketing.linkedin_refresh_jobs`
**Barton ID Format**: `04.04.06.XX.XXXXX.XXX`

**Key Fields**:
- `job_unique_id` - Job Barton ID
- `run_started_at` - Job start timestamp
- `total_profiles` - Profiles checked
- `profiles_changed` - Changes detected
- `status` - pending | running | completed | failed
- `actor_id` - Apify actor used
- `dataset_id` - Apify dataset reference

**Role in Refresh**: Job execution tracking, audit trail, metrics collection

---

## 🔧 Composio-Only Execution Model

**Global Policy**: ALL tools MUST execute via Composio MCP
**Authority**: `imo-creator` repository global configuration
**Endpoint**: `http://localhost:3001/tool?user_id={COMPOSIO_USER_ID}`

### Execution Path

```
Composio MCP Scheduler
    ↓
linkedin_monthly_update.json (job manifest)
    ↓
Tool: apify_run_actor_sync_get_dataset_items
    ↓
Actor: apify~linkedin-profile-scraper
    ↓
Input: Dynamic SQL query → people_master.linkedin_url
    ↓
Output: JSONB array of LinkedIn profiles
    ↓
Post-Process Tool: neon_execute_sql
    ↓
Function: marketing.upsert_people_intelligence_changes()
    ↓
Trigger: after_people_intelligence_insert()
    ↓
1. INSERT unified_audit_log
2. NOTIFY composio_mcp_request
    ↓
External Worker Process
    ↓
POST to Composio MCP
    ↓
Tool: ple_enqueue_lead
    ↓
PLE Workflow Executes Campaign
```

### HEIR/ORBT Payload Format

All Composio MCP calls use standardized payload:

```json
{
  "tool": "neon_execute_sql",
  "data": {
    "sql": "SELECT marketing.upsert_people_intelligence_changes(...)",
    "database_url": "postgresql://..."
  },
  "unique_id": "HEIR-2025-10-LINKEDIN-REFRESH-1729651200",
  "process_id": "PRC-LINKEDIN-1729651200",
  "orbt_layer": 2,
  "blueprint_version": "1.0"
}
```

**No Direct Database Connections**: Direct use of `pg`, `@neondatabase/serverless`, or Composio SDK is FORBIDDEN.

---

## 📊 Schema References

### Table: marketing.linkedin_refresh_jobs

**Migration**: `2025-10-23_create_linkedin_refresh_jobs.sql`
**Purpose**: Track monthly LinkedIn refresh job execution

```sql
CREATE TABLE marketing.linkedin_refresh_jobs (
    id SERIAL PRIMARY KEY,
    job_unique_id TEXT NOT NULL UNIQUE
        CHECK (job_unique_id ~ '^04\\.04\\.06\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$'),
    run_started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    run_completed_at TIMESTAMPTZ,
    total_profiles INTEGER DEFAULT 0,
    profiles_changed INTEGER DEFAULT 0,
    profiles_skipped INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending'
        CHECK (status IN ('pending','running','completed','failed')),
    actor_id TEXT,
    dataset_id TEXT,
    run_id TEXT,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Indexes**:
- `idx_linkedin_refresh_jobs_status` - Status filtering
- `idx_linkedin_refresh_jobs_started_at` - Chronological queries
- `idx_linkedin_refresh_jobs_completed_at` - Completion tracking
- `idx_linkedin_refresh_jobs_actor_id` - Apify actor filtering

**Helper Functions**:
- `generate_linkedin_job_barton_id()` - Auto-generate job Barton ID
- `insert_linkedin_refresh_job()` - Create new job with defaults
- `update_linkedin_job_status()` - Update job status and metrics
- `get_recent_linkedin_jobs()` - Query recent jobs with calculated metrics

### Table: marketing.people_intelligence

**Migration**: `2025-10-22_create_marketing_people_intelligence.sql`
**Purpose**: Track executive title changes and movements

```sql
CREATE TABLE marketing.people_intelligence (
    id SERIAL PRIMARY KEY,
    intel_unique_id TEXT PRIMARY KEY
        CHECK (intel_unique_id ~ '^04\\.04\\.04\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$'),
    person_unique_id TEXT NOT NULL
        REFERENCES marketing.people_master(unique_id),
    company_unique_id TEXT NOT NULL
        REFERENCES marketing.company_master(company_unique_id),
    change_type TEXT NOT NULL
        CHECK (change_type IN ('promotion','job_change','role_change','left_company','new_company')),
    previous_title TEXT,
    new_title TEXT,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    verified BOOLEAN DEFAULT FALSE,
    verification_method TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Indexes**:
- `idx_people_intelligence_person_id` - Person lookup
- `idx_people_intelligence_company_id` - Company lookup
- `idx_people_intelligence_change_type` - Change type filtering
- `idx_people_intelligence_detected_at` - Time-based queries

**Helper Functions**:
- `generate_people_intelligence_barton_id()` - Auto-generate Barton ID
- `insert_people_intelligence()` - Create intelligence record
- `get_people_intelligence()` - Query by person
- `get_recent_executive_movements()` - Recent changes (PLE feed)
- `detect_title_changes()` - Identify title mismatches

### Function: marketing.upsert_people_intelligence_changes()

**Migration**: `2025-10-23_create_upsert_people_intelligence_changes.sql`
**Purpose**: Detect and log LinkedIn profile changes

**Signature**:
```sql
marketing.upsert_people_intelligence_changes(
    new_data JSONB,  -- Array of LinkedIn profiles
    job_id TEXT      -- linkedin_refresh_jobs.job_unique_id
)
RETURNS VOID
```

**Logic**:
1. Iterate through JSONB array of LinkedIn profiles
2. Lookup existing person by `linkedin_url`
3. Compare `current_title` vs `new_title` (NULL-safe)
4. Insert `people_intelligence` record if changed
5. Skip profiles not in `people_master`

**Input Format**:
```json
[
  {
    "linkedin_url": "https://linkedin.com/in/johndoe",
    "title": "Chief Revenue Officer",
    "company": "Acme Corp",
    "location": "San Francisco, CA"
  }
]
```

**Example Call**:
```sql
SELECT marketing.upsert_people_intelligence_changes(
    '[{"linkedin_url": "...", "title": "CRO"}]'::jsonb,
    '04.04.06.84.48151.001'
);
```

---

## 🔔 Trigger Description and Audit Flow

### Trigger: trg_after_people_intelligence_insert

**Migration**: `2025-10-23_create_people_intelligence_trigger.sql`
**Fires**: AFTER INSERT on `marketing.people_intelligence`
**Function**: `marketing.after_people_intelligence_insert()`

### Trigger Actions

#### 1. Audit Log Entry

**Target**: `marketing.unified_audit_log`

```sql
INSERT INTO marketing.unified_audit_log (
    unique_id,          -- person_unique_id
    process_id,         -- '04.04.04'
    status,             -- 'success'
    actor,              -- 'linkedin_sync'
    source,             -- 'linkedin'
    action,             -- 'update_person'
    step,               -- 'step_2b_enrich'
    record_type,        -- 'people'
    before_values,      -- NULL
    after_values        -- JSONB with change details
)
```

**Audit Fields**:
- `unique_id`: Links to person record
- `process_id`: '04.04.04' (people intelligence Barton segment)
- `after_values`: Contains new_title, change_type, previous_title, detected_at

#### 2. PLE Workflow Trigger

**Tool**: `ple_enqueue_lead`
**Method**: `marketing.composio_post_to_tool()`

**Payload**:
```json
{
  "person_id": "04.04.02.84.48151.001",
  "company_id": "04.04.01.84.48151.001",
  "change_type": "role_change",
  "source": "linkedin",
  "intel_id": "04.04.04.84.48151.001",
  "priority": "high"  // 'high' for promotion/new_company, 'medium' otherwise
}
```

**Execution**:
1. Trigger calls `composio_post_to_tool()`
2. Function sends PostgreSQL `NOTIFY` to `composio_mcp_request` channel
3. External worker process listens on channel
4. Worker receives notification with tool name and data
5. Worker POSTs to Composio MCP endpoint with HEIR/ORBT payload
6. Composio executes `ple_enqueue_lead` tool
7. PLE workflow creates campaign for changed executive

### Audit Flow Diagram

```
INSERT people_intelligence
    ↓
Trigger: after_people_intelligence_insert()
    ↓
┌─────────────────────────────────────┐
│ 1. INSERT unified_audit_log         │
│    - unique_id: person_id           │
│    - process_id: 04.04.04           │
│    - action: update_person          │
│    - after_values: change details   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 2. PERFORM composio_post_to_tool()  │
│    - tool: ple_enqueue_lead         │
│    - data: person_id, change_type   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 3. pg_notify('composio_mcp_request')│
│    - Non-blocking async message     │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 4. External Worker Receives NOTIFY  │
│    - Node.js/Python process         │
│    - LISTEN composio_mcp_request    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 5. Worker POSTs to Composio MCP     │
│    - URL: localhost:3001/tool       │
│    - Payload: HEIR/ORBT format      │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 6. PLE Workflow Executes            │
│    - Create campaign record         │
│    - Schedule execution steps       │
│    - Queue outreach messages        │
└─────────────────────────────────────┘
```

### Error Handling

- **Audit Log Failure**: Transaction rolls back, intelligence not inserted
- **MCP Call Failure**: Warning logged, transaction commits, intelligence persists
- **Worker Failure**: NOTIFY message queued for retry
- **PLE Failure**: Error logged in campaign execution, does not affect intelligence record

---

## 📅 Schedule RRULE Specification

### Job Manifest: linkedin_monthly_update.json

**Location**: `apps/outreach-process-manager/jobs/linkedin_monthly_update.json`

```json
{
  "name": "LinkedIn Monthly Update",
  "description": "Monthly LinkedIn title/company refresh for people_master",
  "version": "1.0",
  "tool": "apify_run_actor_sync_get_dataset_items",
  "schedule": "RRULE:FREQ=MONTHLY;BYMONTHDAY=1;BYHOUR=2;BYMINUTE=0;BYSECOND=0",
  "input": {
    "actorId": "apify~linkedin-profile-scraper",
    "runInput": {
      "linkedinUrls": "{{SELECT linkedin_url FROM marketing.people_master WHERE linkedin_url IS NOT NULL}}",
      "maxProfiles": 2000
    },
    "timeout": 600
  },
  "postProcess": {
    "tool": "neon_execute_sql",
    "query": "SELECT marketing.upsert_people_intelligence_changes($PROFILE_DATA, $JOB_ID)"
  },
  "metadata": {
    "doctrine_id": "04.04.06",
    "enforced_by": "Composio MCP Global Policy",
    "created_by": "Claude Code",
    "validated_by": "Validator GBT"
  }
}
```

### Schedule Breakdown

**RRULE**: `FREQ=MONTHLY;BYMONTHDAY=1;BYHOUR=2;BYMINUTE=0;BYSECOND=0`

| Component | Value | Meaning |
|-----------|-------|---------|
| `FREQ` | `MONTHLY` | Runs once per month |
| `BYMONTHDAY` | `1` | Executes on the 1st of each month |
| `BYHOUR` | `2` | Runs at 2:00 AM server time |
| `BYMINUTE` | `0` | Minute = 0 |
| `BYSECOND` | `0` | Second = 0 |

**Example Execution Times**:
- February 1, 2025 at 2:00:00 AM
- March 1, 2025 at 2:00:00 AM
- April 1, 2025 at 2:00:00 AM

**Rationale**:
- **Monthly frequency**: Balance between data freshness and API cost
- **1st of month**: Consistent cadence, post-month-end timing
- **2:00 AM**: Low-traffic period, minimal impact on production systems
- **Timezone**: Server timezone (UTC recommended for consistency)

### Alternative Schedules

**Weekly (aggressive)**:
```
RRULE:FREQ=WEEKLY;BYDAY=MO;BYHOUR=2;BYMINUTE=0;BYSECOND=0
```
- Higher API costs
- Better data freshness
- Use for high-priority segments

**Quarterly (conservative)**:
```
RRULE:FREQ=MONTHLY;BYMONTH=1,4,7,10;BYMONTHDAY=1;BYHOUR=2;BYMINUTE=0;BYSECOND=0
```
- Lower API costs
- Acceptable for stable executives
- Use for mature accounts

---

## 🛡️ Fallback Handling

### Failed Scrapes

**Scenario**: Apify actor fails to fetch LinkedIn data

**Detection**:
- Actor returns HTTP 4xx/5xx error
- Timeout exceeded (600 seconds)
- Dataset empty or malformed

**Handling**:
1. **Job Status**: Update `linkedin_refresh_jobs.status = 'failed'`
2. **Error Logging**: Store error in `error_message` field
3. **Metrics**: Set `profiles_changed = 0`, `profiles_skipped = total_profiles`
4. **Notification**: Alert via Composio MCP (if configured)
5. **Retry**: Manual retry via `insert_linkedin_refresh_job()` or wait for next scheduled run

**Query Failed Jobs**:
```sql
SELECT * FROM marketing.get_recent_linkedin_jobs(30, 'failed');
```

**Manual Retry**:
```sql
-- Create new job
SELECT marketing.insert_linkedin_refresh_job(
    'apify~linkedin-profile-scraper',
    1500,
    '{"retry": true, "previous_job_id": "04.04.06.84.48151.001"}'::jsonb
);

-- Execute via Composio MCP
-- (post to Composio with new job_id)
```

### Missing Profiles

**Scenario**: LinkedIn profile not found in Apify results

**Causes**:
- Profile deleted/deactivated
- Privacy settings prevent scraping
- LinkedIn URL incorrect in `people_master`
- Rate limiting by LinkedIn

**Detection**:
- Profile URL in `people_master.linkedin_url` not in Apify dataset
- HTTP 404 or profile unavailable error

**Handling**:
1. **Skip**: `upsert_people_intelligence_changes()` continues to next profile
2. **Count**: Increment `profiles_skipped` in job metrics
3. **Logging**: Log missing profiles in `metadata.skipped_urls`
4. **No Intelligence**: Do not create `people_intelligence` record
5. **No Audit**: Do not trigger audit log or PLE workflow

**Identify Missing Profiles**:
```sql
-- Profiles in people_master not checked in last run
SELECT
    pm.unique_id,
    pm.full_name,
    pm.linkedin_url,
    pm.updated_at
FROM marketing.people_master pm
LEFT JOIN marketing.people_intelligence pi
    ON pm.unique_id = pi.person_unique_id
    AND pi.detected_at >= NOW() - INTERVAL '35 days'
WHERE pm.linkedin_url IS NOT NULL
  AND pi.person_unique_id IS NULL
ORDER BY pm.updated_at DESC;
```

**Manual Update**:
```sql
-- Flag profile for manual review
UPDATE marketing.people_master
SET metadata = metadata || '{"linkedin_unavailable": true}'::jsonb
WHERE unique_id = '04.04.02.84.48151.001';
```

### Rate Limiting

**Scenario**: LinkedIn or Apify imposes rate limits

**Detection**:
- HTTP 429 (Too Many Requests)
- Apify actor returns rate limit error
- Partial dataset (fewer profiles than expected)

**Handling**:
1. **Job Status**: Mark as `failed` or `completed` with warning
2. **Retry Strategy**: Exponential backoff
   - First retry: +1 hour
   - Second retry: +6 hours
   - Third retry: +24 hours
3. **Partial Success**: Process available profiles, mark others as skipped
4. **Metadata**: Store rate limit details in `linkedin_refresh_jobs.metadata`

**Rate Limit Recovery**:
```json
{
  "rate_limit_hit": true,
  "retry_after_seconds": 3600,
  "profiles_attempted": 2000,
  "profiles_completed": 847,
  "profiles_rate_limited": 1153
}
```

### Stale Data Detection

**Scenario**: No LinkedIn refresh in 45+ days

**Query**:
```sql
-- Check last successful refresh
SELECT
    job_unique_id,
    run_started_at,
    run_completed_at,
    total_profiles,
    profiles_changed,
    status
FROM marketing.linkedin_refresh_jobs
WHERE status = 'completed'
ORDER BY run_completed_at DESC
LIMIT 1;

-- Alert if last refresh > 45 days ago
SELECT
    CASE
        WHEN MAX(run_completed_at) < NOW() - INTERVAL '45 days' THEN 'ALERT: Stale data'
        ELSE 'OK'
    END as data_freshness_status
FROM marketing.linkedin_refresh_jobs
WHERE status = 'completed';
```

**Handling**:
1. **Alert**: Dashboard warning or notification
2. **Manual Trigger**: Execute refresh immediately
3. **Investigation**: Check scheduler status, Composio MCP health

### Network/Database Failures

**Scenario**: Composio MCP unreachable or Neon database down

**Detection**:
- Connection timeout
- HTTP 503 (Service Unavailable)
- PostgreSQL connection error

**Handling**:
1. **Retry**: Automatic retry with exponential backoff (Composio MCP scheduler)
2. **Circuit Breaker**: Pause job after 3 consecutive failures
3. **Notification**: Alert ops team
4. **Graceful Degradation**: Queue messages for later processing

**Health Check Query**:
```sql
-- Verify database connectivity
SELECT 1 as db_health;

-- Check recent job success rate
SELECT
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    ROUND(
        COUNT(*) FILTER (WHERE status = 'completed')::NUMERIC /
        NULLIF(COUNT(*), 0) * 100,
        2
    ) as success_rate_pct
FROM marketing.linkedin_refresh_jobs
WHERE run_started_at >= NOW() - INTERVAL '90 days';
```

---

## 📈 Metrics and Monitoring

### Key Metrics

1. **Job Success Rate**: `completed / (completed + failed)`
2. **Change Detection Rate**: `profiles_changed / total_profiles`
3. **Skip Rate**: `profiles_skipped / total_profiles`
4. **Average Duration**: `AVG(run_completed_at - run_started_at)`
5. **Profiles per Hour**: `total_profiles / duration_hours`

**Dashboard Query**:
```sql
SELECT
    COUNT(*) as total_jobs,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_jobs,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_jobs,
    SUM(total_profiles) as total_profiles_checked,
    SUM(profiles_changed) as total_changes_detected,
    AVG(profiles_changed::NUMERIC / NULLIF(total_profiles, 0) * 100) as avg_change_rate_pct,
    AVG(EXTRACT(EPOCH FROM (run_completed_at - run_started_at)) / 60) as avg_duration_minutes
FROM marketing.linkedin_refresh_jobs
WHERE run_started_at >= NOW() - INTERVAL '90 days';
```

### Alert Thresholds

| Metric | Threshold | Alert Level |
|--------|-----------|-------------|
| Job failure rate | > 20% | Warning |
| Job failure rate | > 50% | Critical |
| Change detection | < 1% | Warning (possible scrape issue) |
| Skip rate | > 30% | Warning |
| Duration | > 15 minutes | Warning |
| Last successful run | > 45 days | Critical |

---

## 🔄 Workflow Summary

### Monthly Execution Flow

```
Day 1, 2:00 AM
    ↓
Composio MCP Scheduler activates linkedin_monthly_update.json
    ↓
1. Create job record
   job_id = insert_linkedin_refresh_job()
    ↓
2. Query people_master for LinkedIn URLs (via Composio MCP)
   SQL: SELECT linkedin_url FROM marketing.people_master WHERE linkedin_url IS NOT NULL
    ↓
3. Call Apify via Composio MCP
   Tool: apify_run_actor_sync_get_dataset_items
   Actor: apify~linkedin-profile-scraper
   Input: Array of LinkedIn URLs
   Timeout: 600 seconds
    ↓
4. Receive Apify dataset
   Format: JSONB array of profile objects
    ↓
5. Detect changes
   Function: marketing.upsert_people_intelligence_changes(dataset, job_id)
   - Compare titles
   - Insert people_intelligence records
    ↓
6. Trigger automation (per intelligence insert)
   Trigger: after_people_intelligence_insert()
   - INSERT unified_audit_log
   - NOTIFY composio_mcp_request
    ↓
7. External worker processes NOTIFY
   - Receives NOTIFY messages
   - POSTs to Composio MCP
   - Tool: ple_enqueue_lead
    ↓
8. PLE workflow executes
   - Creates campaigns for changed executives
   - Schedules outreach steps
    ↓
9. Update job metrics
   Function: update_linkedin_job_status(job_id, 'completed', ...)
    ↓
10. Generate summary report
    Function: get_linkedin_sync_summary(job_id)
```

**Duration**: ~10-15 minutes for 1500-2000 profiles
**API Costs**: Apify LinkedIn scraper credits
**PLE Campaigns**: Created automatically for all detected changes

---

## 📚 References

### Migration Files

1. `2025-10-23_create_linkedin_refresh_jobs.sql` - Job tracking table
2. `2025-10-23_create_upsert_people_intelligence_changes.sql` - Change detection function
3. `2025-10-23_create_people_intelligence_trigger.sql` - Auto audit + PLE trigger
4. `2025-10-22_create_marketing_people_intelligence.sql` - Intelligence table (prerequisite)

### Job Manifests

1. `apps/outreach-process-manager/jobs/linkedin_monthly_update.json` - Scheduler configuration

### Documentation

1. `COMPOSIO_MCP_GLOBAL_POLICY.md` - Mandatory Composio usage policy
2. `COMPOSIO_INTEGRATION.md` - Composio MCP setup and configuration
3. `DATA_FLOW_GUIDE.md` - 8-phase enrichment pipeline
4. `ENRICHMENT_DATA_SCHEMA.md` - Complete schema reference
5. `FINAL_SCHEMA_COMPLIANCE_REPORT.md` - Schema audit results

### External Dependencies

1. **Composio MCP Server**: `http://localhost:3001`
2. **Apify Actor**: `apify~linkedin-profile-scraper`
3. **External Worker**: Node.js/Python process for NOTIFY handling
4. **Neon Database**: PostgreSQL instance (Marketing DB)

---

## ✅ Compliance Checklist

- [x] Barton Doctrine segments defined (04.04.02, 04.04.04, 04.04.06)
- [x] Composio-only execution model enforced
- [x] HEIR/ORBT payload format compliance
- [x] Audit trail via unified_audit_log
- [x] Automated PLE trigger on intelligence insert
- [x] Error handling for failed scrapes
- [x] Fallback handling for missing profiles
- [x] Rate limiting recovery strategy
- [x] RRULE schedule specification
- [x] Metrics and monitoring queries
- [x] Migration files deployed
- [x] Job manifest configured
- [x] Documentation complete

---

**Status**: ✅ LinkedIn Refresh Doctrine Complete
**Deployment**: Ready for production via Composio MCP
**Maintenance**: Monthly automated execution
**Support**: External worker required for NOTIFY handling

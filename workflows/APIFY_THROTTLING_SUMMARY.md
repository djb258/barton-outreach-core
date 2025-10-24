# 🎉 Apify Enrichment Workflow - Throttling & Batching Update

**Date:** 2025-10-24
**Workflow ID:** euSD6SOXPrqnsFxc
**Status:** ✅ **UPDATED - Awaiting Activation**

---

## ✅ SUMMARY TABLE

| Component | Setting | Value |
|------------|----------|--------|
| **Batch size** | Companies per batch | **25** ✅ |
| **Delay** | Throttle between requests | **5s** ✅ |
| **Max retries** | Retry attempts on error | **3** ✅ |
| **Retry wait** | Wait between retries | **60s** ✅ |
| **Concurrency** | Parallel executions | **1** ✅ |
| **Trigger interval** | Poll frequency | **60 min** ✅ |
| **HTTP timeout** | Request timeout | **120s** ✅ |
| **Error handling** | Continue on error | **ON** ✅ |

---

## 🔄 CHANGES MADE

### BEFORE (Original Workflow)
```
Trigger: Manual ("When clicking 'Test workflow'")
Query Limit: 10 companies
Batching: None
Throttling: 30s wait after Apify call
Retry Logic: None
Error Handling: None
Concurrency: Unlimited
People Insertion: Not implemented
```

### AFTER (Updated Workflow)
```
Trigger: Schedule (every 60 minutes)
Query Limit: 25 companies
Batching: Batch controller (25 max)
Throttling: 5s delay between requests
Retry Logic: 3 attempts with 60s wait
Error Handling: Rate limit detection + logging
Concurrency: 1 execution at a time
People Insertion: Fully implemented
```

---

## 📋 WORKFLOW NODE STRUCTURE

### 1. Poll Every 60 Minutes
- **Type:** Schedule Trigger
- **Interval:** 60 minutes
- **Purpose:** Automatically check for companies needing enrichment

### 2. Get Companies Needing Enrichment
- **Type:** Postgres Query
- **Query:**
  ```sql
  SELECT company_unique_id, website_url
  FROM marketing.company_master
  WHERE company_unique_id NOT IN (
    SELECT DISTINCT company_unique_id
    FROM marketing.people_master
    WHERE company_unique_id IS NOT NULL
  )
  ORDER BY created_at DESC
  LIMIT 25
  ```
- **Purpose:** Fetch up to 25 companies without executive data
- **Credential:** Neon Marketing DB

### 3. Batch Controller
- **Type:** Function Node
- **Code:** JavaScript batch processor
- **Batch Size:** 25 items maximum
- **Metadata Added:**
  - `batch_number`: Current batch number
  - `batch_size`: Number of items in batch
  - `item_index`: Position in batch
  - `total_items`: Total items available
- **Purpose:** Control processing volume and add tracking metadata

### 4. Call Apify Actor
- **Type:** HTTP Request
- **Method:** POST
- **URL:**
  ```
  https://api.apify.com/v2/actor-tasks/code_crafter~leads-finder/run-sync-get-dataset-items?token={{APIFY_TOKEN}}&maxItems=25
  ```
- **Body:**
  ```json
  {
    "companyUrl": "{{website_url}}",
    "company_unique_id": "{{company_unique_id}}"
  }
  ```
- **Options:**
  - Timeout: 120,000ms (2 minutes)
  - Max Retries: 3
  - Wait Between Retries: 60,000ms (60 seconds)
- **Error Handling:** Continue to error output on failure
- **Purpose:** Call Apify actor to scrape LinkedIn for executives

### 5. Throttle Delay (5s)
- **Type:** Wait Node
- **Duration:** 5 seconds
- **Purpose:** Prevent API rate limiting by spacing requests

### 6. Check for Rate Limit
- **Type:** IF Node
- **Condition:** HTTP status code >= 429
- **True Branch:** Wait 60s then log error
- **False Branch:** Continue to log failed company
- **Purpose:** Detect and handle rate limit errors

### 7. Wait 60s on Error
- **Type:** Wait Node
- **Duration:** 60 seconds
- **Purpose:** Cooldown period before logging failure

### 8. Log Failed Companies
- **Type:** Postgres Insert
- **Query:**
  ```sql
  INSERT INTO marketing.company_missing (
    company_unique_id,
    reason,
    created_at
  ) VALUES (
    '{{company_unique_id}}',
    'Apify API error: Rate limit or network error',
    NOW()
  )
  ON CONFLICT (company_unique_id)
  DO UPDATE SET
    reason = EXCLUDED.reason,
    created_at = NOW()
  ```
- **Purpose:** Track companies that failed enrichment

### 9. Parse Apify Results
- **Type:** Function Node
- **Code:** JavaScript parser
- **Purpose:** Extract executive data from Apify response
- **Output Fields:**
  - `company_unique_id`
  - `full_name`
  - `title`
  - `email`
  - `linkedin_url`
  - `source`: 'apify-enrichment'
  - `enriched_at`: Current timestamp

### 10. Insert People Data
- **Type:** Postgres Insert
- **Query:**
  ```sql
  INSERT INTO marketing.people_master (
    company_unique_id,
    full_name,
    title,
    email,
    linkedin_url,
    source,
    created_at
  ) VALUES (
    '{{company_unique_id}}',
    '{{full_name}}',
    '{{title}}',
    '{{email}}',
    '{{linkedin_url}}',
    '{{source}}',
    NOW()
  )
  ON CONFLICT (email) DO NOTHING
  ```
- **Purpose:** Store executive contact information

### 11. Log Execution
- **Type:** Postgres Insert
- **Query:**
  ```sql
  INSERT INTO shq_validation_log (
    workflow_id,
    workflow_name,
    execution_time,
    record_count,
    status
  ) VALUES (
    'euSD6SOXPrqnsFxc',
    'Apify Enrichment',
    NOW(),
    {{batch_size}},
    'completed'
  )
  ```
- **Purpose:** Track workflow executions for monitoring

---

## 🔄 EXECUTION FLOW

```
1. Schedule Trigger (every 60 min)
   ↓
2. Get Companies Needing Enrichment (Postgres)
   ↓ (up to 25 companies)
3. Batch Controller (Function)
   ↓ (batch of 25)
4. Call Apify Actor (HTTP Request)
   ├─ SUCCESS → Throttle Delay (5s)
   │            ↓
   │            Parse Apify Results
   │            ↓
   │            Insert People Data
   │            ↓
   │            Log Execution
   │
   └─ ERROR → Check for Rate Limit (IF)
              ├─ Rate Limit (>=429) → Wait 60s → Log Failed Companies
              └─ Other Error → Log Failed Companies
```

---

## 🛡️ SAFETY FEATURES IMPLEMENTED

### 1. Batch Size Control
- **Limit:** 25 companies per execution
- **Prevents:** Database overload and excessive API calls
- **Benefit:** Predictable resource usage

### 2. Throttling (5-second delay)
- **Location:** After each Apify API call
- **Purpose:** Prevent rate limiting
- **Benefit:** Maintains API access without blocks

### 3. Retry Logic
- **Attempts:** 3 retries
- **Wait Time:** 60 seconds between retries
- **Triggers:** Network errors, timeouts
- **Benefit:** Handles transient failures automatically

### 4. Rate Limit Detection
- **Condition:** HTTP status >= 429
- **Action:** Wait 60s + log failure
- **Benefit:** Prevents cascading failures

### 5. Error Logging
- **Table:** `marketing.company_missing`
- **Data:** company_unique_id, reason, timestamp
- **Benefit:** Track problematic companies for manual review

### 6. Execution Logging
- **Table:** `shq_validation_log`
- **Data:** workflow_id, name, time, count, status
- **Benefit:** Monitor workflow performance and history

### 7. Concurrency Control
- **Mode:** Queue (1 execution at a time)
- **Benefit:** Prevents parallel executions from overwhelming API

### 8. Timeout Protection
- **HTTP Timeout:** 120 seconds
- **Benefit:** Prevents hung requests from blocking workflow

---

## 📊 PERFORMANCE EXPECTATIONS

### Throughput
- **Per Execution:** Up to 25 companies
- **Per Hour:** 25 companies (1 execution)
- **Per Day:** 600 companies (24 executions)
- **Per Month:** ~18,000 companies

### Timing
- **Query Time:** ~1-2 seconds
- **Batch Processing:** ~1 second
- **Apify API Call:** 30-90 seconds per company
- **Throttle Delay:** 5 seconds
- **Total per Company:** ~40-100 seconds
- **Total per Batch (25):** ~17-42 minutes

### API Usage
- **Apify Calls:** 25 per hour
- **Apify Credits:** Depends on actor pricing
- **Database Queries:** 3 per execution (fetch + insert + log)

---

## ⚙️ CONFIGURATION REQUIREMENTS

### Environment Variables (n8n)
Set these in n8n environment settings:

```bash
APIFY_TOKEN=your_apify_api_key_here
```

**How to set in n8n:**
1. Open n8n UI
2. Go to Settings → Environment Variables
3. Add `APIFY_TOKEN` with your Apify API key
4. Save changes

### Database Tables Required

#### marketing.company_missing
```sql
CREATE TABLE IF NOT EXISTS marketing.company_missing (
  company_unique_id VARCHAR(50) PRIMARY KEY,
  reason TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### marketing.people_master
(Should already exist from migrations)

#### shq_validation_log
(Should already exist from migrations)

---

## 🧪 TESTING INSTRUCTIONS

### Pre-Activation Testing

#### 1. Verify Apify Token
```bash
curl -X GET "https://api.apify.com/v2/actor-tasks/code_crafter~leads-finder?token=YOUR_TOKEN"
```

Expected: HTTP 200 with task details

#### 2. Test Batch Query
```sql
SELECT company_unique_id, website_url
FROM marketing.company_master
WHERE company_unique_id NOT IN (
  SELECT DISTINCT company_unique_id
  FROM marketing.people_master
  WHERE company_unique_id IS NOT NULL
)
ORDER BY created_at DESC
LIMIT 25;
```

Expected: Up to 25 companies without executive data

#### 3. Verify Tables Exist
```sql
-- Check company_missing table
SELECT COUNT(*) FROM marketing.company_missing;

-- Check shq_validation_log table
SELECT COUNT(*) FROM shq_validation_log;
```

Expected: Both queries succeed (count can be 0)

### Manual Test Run

1. Open n8n UI: https://dbarton.app.n8n.cloud
2. Navigate to "Apify Enrichment" workflow
3. Click "Execute Workflow" (manual test)
4. Monitor execution in real-time
5. Check results:
   ```sql
   -- Check people inserted
   SELECT COUNT(*)
   FROM marketing.people_master
   WHERE source = 'apify-enrichment'
   AND created_at > NOW() - INTERVAL '5 minutes';

   -- Check execution log
   SELECT *
   FROM shq_validation_log
   WHERE workflow_name = 'Apify Enrichment'
   ORDER BY execution_time DESC
   LIMIT 5;
   ```

---

## 🚀 ACTIVATION STEPS

### Prerequisites
- [ ] Apify account created
- [ ] Apify actor `code_crafter~leads-finder` configured
- [ ] APIFY_TOKEN set in n8n environment variables
- [ ] Database tables verified
- [ ] Manual test completed successfully

### Activation Process

1. **Review Workflow in n8n UI**
   - Open: https://dbarton.app.n8n.cloud
   - Navigate to: Apify Enrichment (euSD6SOXPrqnsFxc)
   - Review all nodes and connections
   - Verify Neon Marketing DB credential is selected

2. **Test with Small Batch**
   - Temporarily modify query LIMIT to 5
   - Run manual execution
   - Verify results in `marketing.people_master`
   - Restore LIMIT to 25

3. **Activate Workflow**
   - Toggle workflow switch to **ON**
   - Verify "Poll Every 60 Minutes" trigger is active
   - Check execution schedule

4. **Monitor First Executions**
   - Check n8n Executions tab after 1 hour
   - Verify successful completion
   - Review any errors in execution logs
   - Check database for new people records

---

## 🔍 MONITORING & TROUBLESHOOTING

### Monitor Workflow Execution

```sql
-- Check recent executions
SELECT *
FROM shq_validation_log
WHERE workflow_name = 'Apify Enrichment'
ORDER BY execution_time DESC
LIMIT 10;

-- Check failed companies
SELECT *
FROM marketing.company_missing
WHERE reason LIKE '%Apify%'
ORDER BY created_at DESC
LIMIT 20;

-- Check people enrichment rate
SELECT
  DATE(created_at) as date,
  COUNT(*) as people_added,
  COUNT(DISTINCT company_unique_id) as companies_enriched
FROM marketing.people_master
WHERE source = 'apify-enrichment'
GROUP BY DATE(created_at)
ORDER BY date DESC
LIMIT 7;
```

### Common Issues & Solutions

#### Issue: No companies being processed
**Check:**
```sql
SELECT COUNT(*)
FROM marketing.company_master
WHERE company_unique_id NOT IN (
  SELECT DISTINCT company_unique_id
  FROM marketing.people_master
  WHERE company_unique_id IS NOT NULL
);
```

**Solution:** If count is 0, all companies are already enriched

#### Issue: Apify API errors (429 Rate Limit)
**Check:** n8n execution logs for HTTP 429 errors
**Solution:**
- Increase delay from 5s to 10s
- Reduce batch size from 25 to 10
- Verify Apify subscription tier and limits

#### Issue: No people data inserted
**Check:**
- Apify actor configuration
- APIFY_TOKEN validity
- Actor output format matches parser expectations

**Solution:** Review Apify actor response in n8n execution logs

#### Issue: Workflow not running on schedule
**Check:**
- Workflow is activated (toggle ON)
- Schedule trigger is configured
- n8n instance is running

**Solution:** Check n8n system logs

---

## 📈 COST CONSIDERATIONS

### Apify Costs
- **Actor:** code_crafter~leads-finder
- **Pricing:** Per compute unit (varies by plan)
- **Estimate:** ~$0.01-0.05 per company (depends on actor)
- **Monthly (600 companies):** ~$6-30

### n8n Costs
- **Self-hosted:** Free (server costs only)
- **Cloud:** Varies by plan
- **Workflow executions:** 24 per day (720 per month)

### Database Costs
- **Neon:** Based on storage + compute
- **Storage Growth:** ~1-5 KB per person record
- **Monthly (600 companies × 3 people):** ~2-10 MB

---

## 📁 FILES CREATED/MODIFIED

### New Files
```
workflows/
├── 04-apify-enrichment-throttled.json    ← Updated workflow definition
├── update_apify_workflow.js               ← Update automation script
└── APIFY_THROTTLING_SUMMARY.md            ← This documentation
```

### Modified via n8n API
- Apify Enrichment (euSD6SOXPrqnsFxc)

---

## ✅ VERIFICATION CHECKLIST

- [x] Postgres trigger added (60min polling)
- [x] Query updated (25 companies, ORDER BY created_at DESC)
- [x] Batch controller implemented (25 max)
- [x] HTTP request modified (Apify actor with token)
- [x] Throttle delay added (5 seconds)
- [x] Retry logic implemented (3 attempts, 60s wait)
- [x] Error handling added (rate limit detection)
- [x] Failed company logging implemented
- [x] People data parsing and insertion added
- [x] Execution logging added
- [x] Concurrency controlled (workflow settings)
- [x] Workflow saved to n8n
- [x] Exported as JSON file
- [ ] **APIFY_TOKEN configured in n8n** (manual step)
- [ ] **Workflow activated** (manual step)
- [ ] **Test execution completed** (manual step)

---

## 🎯 EXPECTED BEHAVIOR

### After Activation

```
Every 60 minutes:
  1. Poll for companies without executive data
  2. Select up to 25 companies (newest first)
  3. Process batch through Apify actor
  4. Wait 5 seconds between requests (throttling)
  5. Parse executive data from Apify response
  6. Insert people into marketing.people_master
  7. Log execution to shq_validation_log

On Errors:
  - Retry up to 3 times with 60s wait
  - If rate limited (429): wait 60s then log
  - Log failed companies to marketing.company_missing
  - Continue processing next companies
```

---

## 🚧 LIMITATIONS & CONSIDERATIONS

### Current Limitations
1. **Apify Actor Dependency:** Requires specific actor format
2. **Single Batch:** Processes 25 companies per hour only
3. **No Parallel Processing:** Concurrency set to 1
4. **Manual Token Setup:** APIFY_TOKEN must be set manually

### Future Improvements
1. **Dynamic Batch Sizing:** Adjust based on API limits
2. **Smart Throttling:** Adaptive delay based on API response
3. **Priority Queue:** Enrich high-value companies first
4. **Webhook Trigger:** Start enrichment on new company import
5. **Multi-Actor Support:** Use different actors for different data types

---

## 📊 COMPARISON: BEFORE vs AFTER

| Aspect | Before | After |
|--------|--------|-------|
| **Trigger** | Manual | Automatic (60min) |
| **Batch Size** | 10 | 25 |
| **Throttling** | 30s wait | 5s delay |
| **Retry Logic** | None | 3 attempts |
| **Error Handling** | None | Full error detection |
| **Concurrency** | Unlimited | 1 (controlled) |
| **People Insertion** | Not implemented | Fully implemented |
| **Logging** | None | Execution + error logs |
| **Monitoring** | Manual | Automatic (database) |

---

## ✅ SUCCESS CRITERIA MET

- [x] Workflow updated with Postgres trigger
- [x] Batch controller added (25 max)
- [x] Throttling implemented (5s delay)
- [x] Retry logic added (3 attempts with 60s wait)
- [x] Concurrency controlled (1 execution at a time)
- [x] Error handling with rate limit detection
- [x] Failed company logging
- [x] Execution logging to shq_validation_log
- [x] Workflow remains disabled until review
- [x] Summary table generated
- [x] Workflow exported as JSON

---

**Status:** ✅ **UPDATE COMPLETE**

The Apify Enrichment workflow now includes controlled throttling, batching, and retry handling to ensure reliable and efficient LinkedIn executive data enrichment.

**Final Action Required:**
1. Set `APIFY_TOKEN` in n8n environment variables
2. Review workflow in n8n UI
3. Test with small batch
4. Activate workflow

**n8n URL:** https://dbarton.app.n8n.cloud
**Workflow ID:** euSD6SOXPrqnsFxc

# 🔍 Retroactive Neon Data Validation Guide

**Purpose:** Validate existing West Virginia company and people data in Neon database
**Method:** n8n webhook routing to Google Sheets (2 tabs, 1 sheet)
**Status:** ✅ Production Ready

---

## 📋 Overview

This guide documents the retroactive validation system for cleaning up existing data in the Neon database. Unlike the forward-looking pipeline (`run_live_pipeline.py`), this validator:

- ✅ Validates **existing** records in `marketing.company_master` and `marketing.people_master`
- ✅ Filters by state (default: West Virginia)
- ✅ Routes failures to Google Sheets via **n8n webhooks** (not direct API)
- ✅ Logs all actions to `shq.audit_log` and `marketing.pipeline_events`
- ✅ Updates `validation_status` field in database
- ✅ Generates JSON reports

---

## 🎯 Validation Rules

### Company Rules (Barton Doctrine Compliant)

| Field | Rule | Severity | Example Failure |
|-------|------|----------|-----------------|
| `company_name` | Must be present and > 3 chars | CRITICAL | "AB" → Too short |
| `website` | Must start with `http://` or `https://` | ERROR | "acme.com" → Missing protocol |
| `website` | Must contain a domain (with `.`) | ERROR | "http://acme" → No TLD |
| `employee_count` | Must be > 0 | ERROR | 0 → Invalid count |
| `postal_code` | Must start with 24 or 25 (WV only) | ERROR | "12345" → Not WV zip |

### People Rules (Barton Doctrine Compliant)

| Field | Rule | Severity | Example Failure |
|-------|------|----------|-----------------|
| `full_name` | Must contain a space (first + last) | CRITICAL | "John" → No last name |
| `email` | Must be valid email format | ERROR | "invalid-email" → Bad format |
| `title` | Must include "HR", "CFO", or "CEO" | ERROR | "Manager" → Not executive |
| `company_unique_id` | Must exist in `company_master` | CRITICAL | "bad-id" → Orphaned record |

---

## 🔧 Setup

### Prerequisites

1. **Environment Variables** (in `.env` file):
```bash
# Neon Database
NEON_CONNECTION_STRING=postgresql://Marketing_DB_owner:...@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing_DB?sslmode=require

# n8n Webhooks (REQUIRED)
N8N_COMPANY_FAILURE_WEBHOOK=https://n8n.barton.com/webhook/route-company-failure
N8N_PERSON_FAILURE_WEBHOOK=https://n8n.barton.com/webhook/route-person-failure

# Google Sheet (where failures will be routed)
GOOGLE_SHEET_ID=1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg
```

2. **Python Dependencies**:
```bash
pip install psycopg2-binary python-dotenv requests
```

3. **n8n Workflows** (must be configured):
   - Workflow 1: `route-company-failure` → Writes to `Invalid_Companies` tab
   - Workflow 2: `route-person-failure` → Writes to `Invalid_People` tab

---

## 📝 Usage Examples

### Basic Usage (Validate All WV Records)

```bash
python backend/validator/retro_validate_neon.py --state WV
```

**Expected Output:**
```
======================================================================
🚀 RETROACTIVE NEON DATA VALIDATOR
======================================================================
State: WV
Mode: LIVE
Limit: No limit
Pipeline ID: RETRO-VAL-20251117152030

✅ Loaded 150 companies from WV

============================================================
Validating 150 Companies
============================================================
✅ Acme Corp: VALID
✅ Example LLC: VALID
❌ Test Industries: 1 failure(s)
   Failures: postal_code: West Virginia postal codes must start with 24 or 25
...

📊 Company Validation Summary:
  Total: 150
  ✅ Valid: 145
  ❌ Invalid: 5
  📄 Routed to Sheets: 5

✅ Loaded 300 people from WV

============================================================
Validating 300 People
============================================================
✅ John Doe: VALID
❌ Jane Smith: 1 failure(s)
   Failures: title: Title must include HR, CFO, or CEO
...

📊 People Validation Summary:
  Total: 300
  ✅ Valid: 285
  ❌ Invalid: 15
  📄 Routed to Sheets: 15

======================================================================
📊 RETROACTIVE VALIDATION SUMMARY
======================================================================

🏢 COMPANIES:
  Total Validated:    150
  ✅ Valid:            145
  ❌ Invalid:          5
  📄 Routed to Sheets: 5

👤 PEOPLE:
  Total Validated:    300
  ✅ Valid:            285
  ❌ Invalid:          15
  📄 Routed to Sheets: 15

🌐 WEBHOOKS:
  ✅ Success:          20
  ❌ Failed:           0

⏱️  TIMING:
  Duration:           12.45s
======================================================================

✅ SUCCESS: Validated 450 total records
📊 Google Sheet ID: 1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg
   - Tab 'Invalid_Companies': 5 rows
   - Tab 'Invalid_People': 15 rows

📄 Report saved to: logs/retro_validation_report_20251117_152042.json
```

### Dry-Run Mode (Test Without Changes)

```bash
python backend/validator/retro_validate_neon.py --state WV --dry-run
```

**What This Does:**
- ✅ Loads rules and tests validation logic
- ❌ Does NOT update database
- ❌ Does NOT send webhooks to n8n
- ❌ Does NOT route to Google Sheets

### Batch Mode (Limit Records)

```bash
# Validate only 100 companies and 100 people
python backend/validator/retro_validate_neon.py --state WV --limit 100
```

### Custom Output Path

```bash
python backend/validator/retro_validate_neon.py --state WV --output custom_report.json
```

### Verbose Logging

```bash
python backend/validator/retro_validate_neon.py --state WV --verbose
```

---

## 🌐 n8n Webhook Integration

### How It Works

```
Invalid Record Detected
  ↓
POST to n8n Webhook
  ↓
n8n Workflow Executes
  ↓
Data Appended to Google Sheets
  (Tab: Invalid_Companies or Invalid_People)
```

### Webhook Payload Format

**Company Failure Payload:**
```json
{
  "type": "company",
  "reason_code": "postal_code: West Virginia postal codes must start with 24 or 25, website: Website must start with http:// or https://",
  "row_data": {
    "company_unique_id": "04.04.02.04.30000.001",
    "company_name": "Test Industries",
    "website": "test.com",
    "employee_count": 250,
    "postal_code": "12345",
    "state": "WV",
    ...
  },
  "state": "WV",
  "timestamp": "2025-11-17T15:20:30.123456",
  "pipeline_id": "RETRO-VAL-20251117152030",
  "failures": [
    {
      "field": "postal_code",
      "rule": "postal_code_wv_format",
      "message": "West Virginia postal codes must start with 24 or 25",
      "severity": "error",
      "current_value": "12345"
    }
  ],
  "sheet_id": "1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg",
  "sheet_tab": "Invalid_Companies"
}
```

**Person Failure Payload:**
```json
{
  "type": "person",
  "reason_code": "title: Title must include HR, CFO, or CEO",
  "row_data": {
    "unique_id": "04.04.02.04.20000.001",
    "full_name": "Jane Smith",
    "email": "jane@example.com",
    "title": "Senior Manager",
    "company_unique_id": "04.04.02.04.30000.001",
    ...
  },
  "state": "WV",
  "timestamp": "2025-11-17T15:20:35.789012",
  "pipeline_id": "RETRO-VAL-20251117152030",
  "failures": [
    {
      "field": "title",
      "rule": "title_executive",
      "message": "Title must include HR, CFO, or CEO",
      "severity": "error",
      "current_value": "Senior Manager"
    }
  ],
  "sheet_id": "1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg",
  "sheet_tab": "Invalid_People"
}
```

### Webhook Error Handling

- ✅ HTTP 2xx → Success (logged)
- ⚠️ HTTP 5xx → Retry once
- ❌ Timeout → Logged as failure
- ❌ Connection error → Logged as failure

---

## 📊 Database Logging

### 1. `marketing.pipeline_events` Table

**What Gets Logged:**
- Every validation check (pass or fail)
- Event type: `validation_check`
- Record type: `company` or `person`
- Record ID
- Pass/fail status
- Failure reason (if applicable)

**Example Query:**
```sql
SELECT *
FROM marketing.pipeline_events
WHERE event_type = 'validation_check'
  AND payload->>'pipeline_id' = 'RETRO-VAL-20251117152030'
ORDER BY created_at DESC;
```

### 2. `shq.audit_log` Table

**What Gets Logged:**
- Pipeline start event
- Pipeline completion event
- Component: `retro_validator`
- Event type: `retro_validation`
- Full statistics in `event_data` JSON

**Example Query:**
```sql
SELECT
  component,
  event_type,
  event_data,
  created_at
FROM shq.audit_log
WHERE component = 'retro_validator'
ORDER BY created_at DESC
LIMIT 10;
```

### 3. `validation_status` Field Updates

**Automatic Status Updates:**
- Valid records → `validation_status = 'valid'`
- Invalid records → `validation_status = 'invalid'`

**Check Validation Status:**
```sql
-- Companies by validation status
SELECT
  validation_status,
  COUNT(*) as count
FROM marketing.company_master
WHERE state = 'WV'
GROUP BY validation_status;

-- People by validation status
SELECT
  validation_status,
  COUNT(*) as count
FROM marketing.people_master p
JOIN marketing.company_master c ON p.company_unique_id = c.company_unique_id
WHERE c.state = 'WV'
GROUP BY validation_status;
```

---

## 📈 Monitoring Queries

### Check Recent Retroactive Validations

```sql
SELECT
  event_data->>'state' as state,
  (event_data->'companies'->>'total')::int as companies_checked,
  (event_data->'companies'->>'invalid')::int as companies_invalid,
  (event_data->'people'->>'total')::int as people_checked,
  (event_data->'people'->>'invalid')::int as people_invalid,
  created_at
FROM shq.audit_log
WHERE component = 'retro_validator'
  AND event_type = 'retro_validation'
ORDER BY created_at DESC
LIMIT 10;
```

### Check Webhook Success Rate

```sql
SELECT
  event_data->'webhooks'->>'success' as webhook_success,
  event_data->'webhooks'->>'failed' as webhook_failed,
  created_at
FROM shq.audit_log
WHERE component = 'retro_validator'
ORDER BY created_at DESC
LIMIT 10;
```

### Find All Invalid Records (Not Yet Fixed)

```sql
-- Invalid companies
SELECT
  company_unique_id,
  company_name,
  postal_code,
  website,
  employee_count
FROM marketing.company_master
WHERE state = 'WV'
  AND validation_status = 'invalid';

-- Invalid people
SELECT
  p.unique_id,
  p.full_name,
  p.email,
  p.title,
  c.company_name
FROM marketing.people_master p
JOIN marketing.company_master c ON p.company_unique_id = c.company_unique_id
WHERE c.state = 'WV'
  AND p.validation_status = 'invalid';
```

---

## 🔍 Google Sheets Review Workflow

### Step 1: Open Google Sheet

```bash
open "https://docs.google.com/spreadsheets/d/1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg"
```

### Step 2: Review Invalid Companies Tab

**Tab Name:** `Invalid_Companies`

**Columns (from webhook payload):**
- Company Unique ID
- Company Name
- Website
- Employee Count
- Postal Code
- State
- Failure Reason
- Timestamp
- Pipeline ID

### Step 3: Review Invalid People Tab

**Tab Name:** `Invalid_People`

**Columns (from webhook payload):**
- Unique ID
- Full Name
- Email
- Title
- Company Unique ID
- Failure Reason
- Timestamp
- Pipeline ID

### Step 4: Fix Records Manually

**Option A: Fix in Google Sheets (then re-import)**
- Correct the data in the sheet
- Export as CSV
- Re-import via `load_intake_data.py`

**Option B: Fix Directly in Neon**
```sql
-- Fix company postal code
UPDATE marketing.company_master
SET postal_code = '25301',
    validation_status = NULL
WHERE company_unique_id = '04.04.02.04.30000.001';

-- Fix person title
UPDATE marketing.people_master
SET title = 'Chief Financial Officer (CFO)',
    validation_status = NULL
WHERE unique_id = '04.04.02.04.20000.001';
```

### Step 5: Re-run Validation

```bash
# Re-validate records that were fixed (validation_status = NULL)
python backend/validator/retro_validate_neon.py --state WV
```

---

## 🚨 Troubleshooting

### Issue 1: "N8N_COMPANY_FAILURE_WEBHOOK not configured"

**Symptom:**
```
⚠️  N8N_COMPANY_FAILURE_WEBHOOK not configured - company routing will be skipped
```

**Solution:**
```bash
# Add to .env file
echo "N8N_COMPANY_FAILURE_WEBHOOK=https://n8n.barton.com/webhook/route-company-failure" >> .env
echo "N8N_PERSON_FAILURE_WEBHOOK=https://n8n.barton.com/webhook/route-person-failure" >> .env
```

### Issue 2: Webhook Returns HTTP 404

**Symptom:**
```
⚠️  n8n webhook returned HTTP 404
```

**Solution:**
1. Verify n8n workflow is activated
2. Check webhook URL is correct
3. Test webhook manually:
```bash
curl -X POST https://n8n.barton.com/webhook/route-company-failure \
  -H "Content-Type: application/json" \
  -d '{"type": "company", "test": true}'
```

### Issue 3: No Records Found

**Symptom:**
```
✅ Loaded 0 companies from WV
```

**Solution:**
```sql
-- Check if records exist
SELECT COUNT(*) FROM marketing.company_master WHERE state = 'WV';

-- Check if already validated
SELECT COUNT(*) FROM marketing.company_master
WHERE state = 'WV'
  AND validation_status IS NULL OR validation_status = 'pending';
```

### Issue 4: All Records Fail Validation

**Symptom:**
```
❌ Invalid: 150 (100% of records)
```

**Solution:**
1. Check validation rules are correct for your data
2. Review first 10 failures in detail:
```bash
python backend/validator/retro_validate_neon.py --state WV --limit 10 --verbose
```
3. Adjust rules in `validation_rules.py` if needed

---

## 📚 Related Documentation

- **Validation Rules Module:** `backend/validator/validation_rules.py`
- **Production Workflow Guide:** `docs/PRODUCTION_WORKFLOW_GUIDE.md`
- **Live Integrations Guide:** `docs/LIVE_INTEGRATIONS_GUIDE.md`
- **Main README:** `ctb/sys/toolbox-hub/README.md`

---

## 🎯 Best Practices

### 1. Always Dry-Run First
```bash
python backend/validator/retro_validate_neon.py --state WV --dry-run
```

### 2. Start with Small Batches
```bash
python backend/validator/retro_validate_neon.py --state WV --limit 50
```

### 3. Monitor Webhook Success Rate
```sql
SELECT * FROM shq.audit_log
WHERE component = 'retro_validator'
ORDER BY created_at DESC LIMIT 1;
```

### 4. Review Google Sheets After Each Run
```bash
open "https://docs.google.com/spreadsheets/d/1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg"
```

### 5. Clear `validation_status` After Fixes
```sql
UPDATE marketing.company_master
SET validation_status = NULL
WHERE company_unique_id IN ('id1', 'id2', 'id3');
```

---

**Last Updated:** 2025-11-17
**Version:** 1.0.0
**Status:** ✅ Production Ready
**Maintainer:** Barton Outreach Core Team

# 🚀 Production Workflow Guide - Barton Toolbox Hub

**Status:** ✅ Production Ready
**Last Updated:** 2025-11-17
**Complete Workflow:** CSV → Intake → Validation → Promotion → Enrichment

---

## 📋 Overview

This guide documents the complete end-to-end production workflow for processing outreach data through the Barton Toolbox Hub pipeline.

**Complete Flow:**
```
CSV File
  ↓
load_intake_data.py (Step 1)
  ↓
intake.company_raw_intake (Staging Table)
  ↓
run_live_pipeline.py (Step 2)
  ↓
├─ Valid Records → company_master + people_master
└─ Invalid Records → Google Sheets (Manual Review)
```

---

## 🎯 Two-Script Workflow

### Script 1: `load_intake_data.py` - CSV to Database

**Purpose:** Load CSV files into the intake staging table
**Location:** `ctb/sys/toolbox-hub/backend/scripts/load_intake_data.py`
**Input:** CSV file with company/contact data
**Output:** Records in `intake.company_raw_intake` table

**Features:**
- ✅ Flexible column mapping (auto-detects common column names)
- ✅ Data validation (required fields, email format, numeric checks)
- ✅ Duplicate detection (case-insensitive company name matching)
- ✅ Batch insert for performance (configurable batch size)
- ✅ Dry-run mode for testing
- ✅ Comprehensive statistics and error reporting

### Script 2: `run_live_pipeline.py` - Validation & Promotion

**Purpose:** Validate intake data and promote to production tables
**Location:** `ctb/sys/toolbox-hub/backend/scripts/run_live_pipeline.py`
**Input:** Records from `intake.company_raw_intake`
**Output:**
- Valid records → `marketing.company_master` + `marketing.people_master`
- Invalid records → Google Sheets (ID: `1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg`)

**Features:**
- ✅ 8-step pipeline (4 implemented, 4 placeholders)
- ✅ Validation with multiple rules
- ✅ Barton ID generation (04.04.02.04.30000.XXX for companies, 04.04.02.04.20000.XXX for people)
- ✅ Error routing to live Google Sheets
- ✅ HEIR/ORBT audit logging
- ✅ Dry-run mode for testing
- ✅ Comprehensive statistics and JSON reports

---

## 🔧 Setup

### Prerequisites

1. **Environment Variables** (in `.env` file):
```bash
# Neon Database
NEON_CONNECTION_STRING=postgresql://Marketing_DB_owner:...@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing_DB?sslmode=require

# Composio MCP
COMPOSIO_MCP_URL=http://localhost:3001
COMPOSIO_API_KEY=ak_t-F0AbvfZHUZSUrqAGNn

# Google Sheets
GOOGLE_SHEET_ID=1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg
GOOGLE_SHEET_TAB=Sheet1
```

2. **Python Dependencies**:
```bash
pip install psycopg2-binary python-dotenv
```

3. **Composio MCP Server** (REQUIRED for Google Sheets integration):
```bash
# From IMO Creator repository
cd "C:\Users\CUSTOM PC\Desktop\Cursor Builds\scraping-tool\imo-creator\mcp-servers\composio-mcp"
node server.js
```

4. **Verify MCP is Running**:
```bash
curl http://localhost:3001/mcp/health
# Should return: {"status": "healthy"}
```

---

## 📝 Complete Workflow Example

### Step 1: Prepare Your CSV File

**Example CSV (`companies.csv`):**
```csv
company_name,industry,employee_count,website,contact_name,contact_email,contact_title
Acme Corp,Technology,500,https://acme.com,John Doe,john@acme.com,CEO
Example LLC,Consulting,100,https://example.com,Jane Smith,jane@example.com,CFO
Test Industries,Manufacturing,250,https://test.com,Bob Johnson,bob@test.com,HR Director
```

**Supported Column Names (auto-detected):**
- **Company Name:** `company_name`, `company`, `name`, `organization`
- **Industry:** `industry`, `sector`, `vertical`
- **Employee Count:** `employee_count`, `employees`, `headcount`, `size`
- **Website:** `website`, `url`, `domain`
- **Contact Name:** `contact_name`, `contact`, `name`, `full_name`
- **Contact Email:** `contact_email`, `email`, `contact_email_address`
- **Contact Title:** `contact_title`, `title`, `job_title`, `position`

### Step 2: Load CSV to Intake Table (Dry-Run First)

```bash
# Test without making changes
python ctb/sys/toolbox-hub/backend/scripts/load_intake_data.py companies.csv --dry-run

# Expected Output:
# 📊 INTAKE DATA LOADER - BARTON TOOLBOX HUB
# CSV File: companies.csv
# Mode: DRY-RUN
#
# 📊 Step 1: Parsing CSV file...
# ✅ Parsed 3 rows: 3 valid, 0 invalid, 0 duplicates
#
# 💾 Step 2: Inserting 3 records to database...
# 🔍 [DRY-RUN] Would insert 3 records
#
# 📊 INTAKE LOADING SUMMARY
# Total Rows Processed:  3
# ✅ Valid Rows:          3
# ❌ Invalid Rows:        0
# ⏭️  Duplicate Rows:      0
# 💾 Inserted Rows:       3
# ⏱️  Duration:            0.12s
```

### Step 3: Load CSV to Intake Table (Live)

```bash
# Actually insert the data
python ctb/sys/toolbox-hub/backend/scripts/load_intake_data.py companies.csv

# Expected Output:
# 📊 INTAKE DATA LOADER - BARTON TOOLBOX HUB
# CSV File: companies.csv
# Mode: LIVE
#
# 📊 Step 1: Parsing CSV file...
# ✅ Parsed 3 rows: 3 valid, 0 invalid, 0 duplicates
#
# 💾 Step 2: Inserting 3 records to database...
# ✅ Inserted batch 1/1 (3 records)
# 🎉 Successfully inserted 3 records
#
# 📊 INTAKE LOADING SUMMARY
# Total Rows Processed:  3
# ✅ Valid Rows:          3
# ❌ Invalid Rows:        0
# ⏭️  Duplicate Rows:      0
# 💾 Inserted Rows:       3
# ⏱️  Duration:            0.45s
#
# ✅ SUCCESS: 3 records loaded into intake.company_raw_intake
# 🚀 Next step: Run pipeline with: python run_live_pipeline.py
```

### Step 4: Verify Data in Intake Table

```bash
# Connect to Neon database
psql "$NEON_CONNECTION_STRING"

# Check loaded records
SELECT * FROM intake.company_raw_intake
WHERE validation_status IS NULL
ORDER BY loaded_at DESC
LIMIT 10;
```

### Step 5: Run Pipeline (Dry-Run First)

```bash
# Test pipeline without making changes
python ctb/sys/toolbox-hub/backend/scripts/run_live_pipeline.py --dry-run --limit 10

# Expected Output:
# 🚀 BARTON TOOLBOX HUB - LIVE PRODUCTION PIPELINE
# Mode: DRY-RUN
# Record Limit: 10
#
# ──────────────────────────────────────────────────────────
# 📥 STEP 1: Loading Intake Data
# ──────────────────────────────────────────────────────────
# 🔍 [DRY-RUN] Would load 3 unvalidated records
#
# ──────────────────────────────────────────────────────────
# ✅ STEP 2: Validating Records
# ──────────────────────────────────────────────────────────
# ✅ Acme Corp: VALID
# ✅ Example LLC: VALID
# ✅ Test Industries: VALID
# Valid: 3 | Invalid: 0
#
# ──────────────────────────────────────────────────────────
# 🎯 STEP 3: Promoting Valid Records
# ──────────────────────────────────────────────────────────
# 🔍 [DRY-RUN] Would promote 3 companies and 3 people
#
# ──────────────────────────────────────────────────────────
# 📊 PIPELINE EXECUTION SUMMARY
# ──────────────────────────────────────────────────────────
# Total Records Processed: 3
# ✅ Validation Passed:     3
# ❌ Validation Failed:     0
# 🏢 Companies Promoted:    3
# 👤 People Promoted:       3
# 📄 Rows Routed to Sheet:  0
# ⏱️  Duration:              1.23s
```

### Step 6: Run Pipeline (Live)

```bash
# Actually process the data
python ctb/sys/toolbox-hub/backend/scripts/run_live_pipeline.py --limit 100

# Expected Output:
# 🚀 BARTON TOOLBOX HUB - LIVE PRODUCTION PIPELINE
# Mode: LIVE
# Record Limit: 100
#
# ──────────────────────────────────────────────────────────
# 📥 STEP 1: Loading Intake Data
# ──────────────────────────────────────────────────────────
# ✅ Loaded 3 unvalidated records from intake
#
# ──────────────────────────────────────────────────────────
# ✅ STEP 2: Validating Records
# ──────────────────────────────────────────────────────────
# ✅ Acme Corp: VALID
# ✅ Example LLC: VALID
# ❌ Test Industries: 1 validation failure(s)
#    - contact_email: Invalid email format
# Valid: 2 | Invalid: 1
#
# ──────────────────────────────────────────────────────────
# 🎯 STEP 3: Promoting Valid Records
# ──────────────────────────────────────────────────────────
# ✅ Promoted: Acme Corp (04.04.02.04.30000.001)
# ✅ Promoted: Example LLC (04.04.02.04.30000.002)
# ✅ Promoted 2 companies and 2 people to production tables
#
# ──────────────────────────────────────────────────────────
# 🔀 STEP 4: Routing Invalid Records to Google Sheets
# ──────────────────────────────────────────────────────────
# ✅ Routed 1 invalid record to Google Sheet
# Sheet ID: 1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg
#
# ──────────────────────────────────────────────────────────
# 📊 PIPELINE EXECUTION SUMMARY
# ──────────────────────────────────────────────────────────
# Total Records Processed: 3
# ✅ Validation Passed:     2
# ❌ Validation Failed:     1
# 🏢 Companies Promoted:    2
# 👤 People Promoted:       2
# 📄 Rows Routed to Sheet:  1
# ⏱️  Duration:              2.45s
#
# ✅ Pipeline completed successfully!
# 📄 Report saved: logs/pipeline_report_20251117_143022.json
```

### Step 7: Review Invalid Records in Google Sheets

```bash
# Open the Google Sheet
open "https://docs.google.com/spreadsheets/d/1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg"

# Invalid records will be appended to "Sheet1" tab with:
# - Company Name
# - Rule Failed
# - Field Name
# - Current Value
# - Error Message
# - Status
# - Corrected Value (empty - for manual correction)
```

### Step 8: Verify Promoted Records

```bash
# Check company_master
SELECT * FROM marketing.company_master
WHERE company_unique_id LIKE '04.04.02.04.30000.%'
ORDER BY created_at DESC;

# Check people_master
SELECT * FROM marketing.people_master
WHERE unique_id LIKE '04.04.02.04.20000.%'
ORDER BY created_at DESC;

# Check audit log
SELECT * FROM shq.audit_log
WHERE event_type LIKE 'pipeline.%'
ORDER BY created_at DESC
LIMIT 20;
```

---

## 🎛️ Advanced Usage

### Custom Column Mapping

**Create mapping file (`custom_mapping.json`):**
```json
{
  "company_name": "Client Name",
  "industry": "Business Sector",
  "employee_count": "Workforce Size",
  "website": "Company URL",
  "contact_name": "Primary Contact",
  "contact_email": "Email Address",
  "contact_title": "Job Position"
}
```

**Load with custom mapping:**
```bash
python load_intake_data.py companies.csv --mapping custom_mapping.json
```

### Batch Processing Large Files

```bash
# Process 1000 records at a time
python load_intake_data.py large_file.csv --batch-size 1000

# Then run pipeline in batches
python run_live_pipeline.py --limit 500
python run_live_pipeline.py --limit 500  # Run again for next batch
```

### Generate Reports

```bash
# Save intake loading report
python load_intake_data.py companies.csv --output intake_report.json

# Save pipeline execution report
python run_live_pipeline.py --output pipeline_report.json
```

### Verbose Logging

```bash
# Debug mode for troubleshooting
python load_intake_data.py companies.csv --verbose
python run_live_pipeline.py --verbose
```

---

## 🔍 Monitoring & Troubleshooting

### Check Intake Table Status

```sql
-- Total unvalidated records
SELECT COUNT(*) as pending_validation
FROM intake.company_raw_intake
WHERE validation_status IS NULL;

-- Recently loaded records
SELECT company_name, contact_name, contact_email, loaded_at
FROM intake.company_raw_intake
WHERE loaded_at >= NOW() - INTERVAL '24 hours'
ORDER BY loaded_at DESC;

-- Records with validation failures
SELECT company_name, validation_status, validation_errors
FROM intake.company_raw_intake
WHERE validation_status = 'failed'
ORDER BY loaded_at DESC;
```

### Check Pipeline Execution History

```sql
-- Recent pipeline runs
SELECT
    event_type,
    event_data->>'status' as status,
    event_data->>'records_processed' as records,
    created_at
FROM shq.audit_log
WHERE event_type LIKE 'pipeline.%'
ORDER BY created_at DESC
LIMIT 20;

-- Recent errors
SELECT
    error_code,
    error_message,
    severity,
    component,
    created_at
FROM shq.error_master
WHERE component = 'live_pipeline'
  AND created_at >= NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;
```

### Check Google Sheets Integration

```bash
# Test Composio MCP health
curl http://localhost:3001/mcp/health

# List connected Google accounts
curl -X POST http://localhost:3001/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "manage_connected_account",
    "data": {"action": "list"},
    "unique_id": "HEIR-2025-11-CHECK-01",
    "process_id": "PRC-CHECK-001",
    "orbt_layer": 2,
    "blueprint_version": "1.0"
  }'
```

---

## 🚨 Common Issues & Solutions

### Issue 1: "NEON_CONNECTION_STRING not set"

**Solution:**
```bash
# Check .env file exists
cat ctb/sys/toolbox-hub/.env

# Or set manually
export NEON_CONNECTION_STRING='postgresql://Marketing_DB_owner:...@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing_DB?sslmode=require'
```

### Issue 2: "Composio MCP not responding"

**Solution:**
```bash
# Start MCP server
cd "C:\Users\CUSTOM PC\Desktop\Cursor Builds\scraping-tool\imo-creator\mcp-servers\composio-mcp"
node server.js

# Verify it's running
curl http://localhost:3001/mcp/health
```

### Issue 3: "Duplicate company detected"

**Solution:**
```bash
# This is expected behavior - loader skips duplicates
# To force reload, delete from intake table first:
psql "$NEON_CONNECTION_STRING" -c "DELETE FROM intake.company_raw_intake WHERE company_name = 'Acme Corp';"
```

### Issue 4: "Google Sheet not updating"

**Solution:**
```bash
# 1. Check Composio MCP is running
curl http://localhost:3001/mcp/health

# 2. Verify Google Sheets connected account
# See: ctb/sys/toolbox-hub/docs/LIVE_INTEGRATIONS_GUIDE.md

# 3. Check GOOGLE_SHEET_ID in .env
grep GOOGLE_SHEET_ID ctb/sys/toolbox-hub/.env

# 4. Manually test sheet write
python ctb/sys/toolbox-hub/backend/lib/composio_client.py
```

### Issue 5: "Validation rules too strict"

**Solution:**
```python
# Edit validation rules in run_live_pipeline.py
# File: ctb/sys/toolbox-hub/backend/scripts/run_live_pipeline.py
# Method: validate_records()

# Example: Make email optional
if contact_email and "@" not in contact_email:
    # Changed from: failures.append(...)
    # To: Just log a warning
    logger.warning(f"Invalid email for {company_name}: {contact_email}")
```

---

## 📊 Production Best Practices

### 1. Always Dry-Run First
```bash
# Test both scripts in dry-run mode
python load_intake_data.py input.csv --dry-run
python run_live_pipeline.py --dry-run
```

### 2. Process in Batches
```bash
# For large datasets, process in batches
python load_intake_data.py large.csv --batch-size 1000
python run_live_pipeline.py --limit 500  # Multiple runs
```

### 3. Monitor Error Logs
```sql
-- Check for errors after each run
SELECT * FROM shq.error_master
WHERE created_at >= NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;
```

### 4. Save Reports
```bash
# Keep audit trail
python load_intake_data.py input.csv --output "reports/intake_$(date +%Y%m%d).json"
python run_live_pipeline.py --output "reports/pipeline_$(date +%Y%m%d).json"
```

### 5. Backup Before Large Runs
```bash
# Backup intake table before processing
pg_dump "$NEON_CONNECTION_STRING" \
  --schema=intake \
  --table=company_raw_intake \
  --file=backup_$(date +%Y%m%d).sql
```

---

## 📈 Performance Metrics

**Expected Performance:**
- **Intake Loading:** ~500 records/second (batch_size=100)
- **Pipeline Validation:** ~100 records/second
- **Google Sheets Writing:** ~50 records/second (batch_size=20)

**Optimizations:**
- Increase `--batch-size` for faster intake loading
- Increase `--limit` for faster pipeline processing
- Run during off-peak hours for large datasets

---

## 🔗 Related Documentation

- **Main README:** `ctb/sys/toolbox-hub/README.md`
- **Live Integrations Guide:** `ctb/sys/toolbox-hub/docs/LIVE_INTEGRATIONS_GUIDE.md`
- **Integration Summary:** `ctb/sys/toolbox-hub/docs/integration-summary.md`
- **Composio Client:** `ctb/sys/toolbox-hub/backend/lib/composio_client.py`
- **N8N Config:** `ctb/sys/toolbox-hub/config/n8n_endpoints.config.json`
- **Tools Registry:** `ctb/sys/toolbox-hub/config/tools_registry.json`

---

**Last Updated:** 2025-11-17
**Version:** 1.0.0
**Status:** ✅ Production Ready
**Maintainer:** Barton Outreach Core Team

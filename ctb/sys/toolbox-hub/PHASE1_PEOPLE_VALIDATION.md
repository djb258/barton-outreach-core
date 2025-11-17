# Phase 1 People Validation - Complete Guide

**Purpose:** Validate people records in `marketing.people_master` and route failures to Google Sheets via n8n
**Status:** ✅ Production Ready
**Date:** 2025-11-17
**Related:** Phase 1 Company Validation, Phase 2 Outreach Readiness

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Validation Rules](#validation-rules)
3. [Output Format](#output-format)
4. [n8n Webhook Integration](#n8n-webhook-integration)
5. [Database Updates](#database-updates)
6. [CLI Usage](#cli-usage)
7. [Code Integration](#code-integration)
8. [Troubleshooting](#troubleshooting)
9. [Production Deployment](#production-deployment)

---

## Overview

### What is Phase 1 People Validation?

Phase 1 People Validation checks the **structural integrity** of person records in `marketing.people_master` before they can be used for outreach. This is a **prerequisite** for Phase 2 Outreach Readiness.

**Key Concept:**
Phase 1 validates that basic required fields exist and are valid. Phase 2 (Outreach Readiness) validates that people have been enriched and verified.

### Validation Flow

```
                    PHASE 1 PEOPLE VALIDATION
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Input: marketing.people_master records                     │
│         (optionally filtered by state)                      │
│                                                             │
│                      ↓                                      │
│                                                             │
│  Validate: 7 rules (CRITICAL/ERROR/WARNING severity)        │
│  ├─ person_id not null (CRITICAL)                           │
│  ├─ full_name >= 3 characters (CRITICAL)                    │
│  ├─ email present and valid format (ERROR)                  │
│  ├─ title includes CEO/CFO/HR keywords (ERROR)              │
│  ├─ company_unique_id exists in company_master (CRITICAL)   │
│  ├─ linkedin_url includes "linkedin.com/in/" (ERROR)        │
│  └─ timestamp_last_updated present (WARNING)                │
│                                                             │
│                      ↓                                      │
│                                                             │
│  Route Failures:                                            │
│  ├─ n8n webhook: https://n8n.barton.com/webhook/...         │
│  └─ Google Sheet: Invalid_People tab                        │
│                                                             │
│                      ↓                                      │
│                                                             │
│  Database Updates:                                          │
│  ├─ people_master.validation_status = 'valid' or 'invalid'  │
│  ├─ Log to marketing.pipeline_events                        │
│  └─ Log to shq.audit_log                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### When to Use This Validator

**Use Phase 1 People Validation when:**
- You have new people records in `marketing.people_master`
- You need to clean up invalid people before enrichment
- You want to identify people with missing critical fields
- You need to route invalid records to manual review in Google Sheets

**Do NOT use this validator for:**
- Checking enrichment status (use Phase 2 Outreach Readiness)
- Checking email verification (use Phase 2 Outreach Readiness)
- Validating company structure (use Phase 1 Company Validation)

---

## Validation Rules

### Rule 1: Person ID Present (CRITICAL)

**Field:** `person_id` or `unique_id`
**Severity:** CRITICAL
**Validation:** Field must not be null or empty string

**Why Critical:**
Person ID is the primary key. Without it, we cannot track enrichment, email verification, or outreach history.

**Example Failure:**
```json
{
  "field": "person_id",
  "message": "Person ID is required"
}
```

---

### Rule 2: Full Name >= 3 Characters (CRITICAL)

**Field:** `full_name`
**Severity:** CRITICAL
**Validation:** String length >= 3 after trimming whitespace

**Why Critical:**
Full name is required for personalization in outreach emails. Names shorter than 3 characters are likely incomplete or invalid.

**Example Failures:**
```json
// Empty name
{
  "field": "full_name",
  "message": "Full name is required"
}

// Too short
{
  "field": "full_name",
  "message": "Full name must be at least 3 characters (got 2)"
}
```

---

### Rule 3: Email Present and Valid Format (ERROR)

**Field:** `email`
**Severity:** ERROR
**Validation:** Basic regex check `\S+@\S+\.\S+`

**Why Error (not Critical):**
Email is important but can be enriched later. Invalid format indicates data quality issues.

**Example Failures:**
```json
// Missing email
{
  "field": "email",
  "message": "Email is required"
}

// Invalid format
{
  "field": "email",
  "message": "Email format is invalid"
}
```

**Valid Examples:**
- john@acme.com ✅
- jane.smith@company.co.uk ✅
- ceo+work@startup.io ✅

**Invalid Examples:**
- john@acme ❌ (no TLD)
- @acme.com ❌ (no local part)
- john.acme.com ❌ (no @)

---

### Rule 4: Title Includes CEO/CFO/HR Keywords (ERROR)

**Field:** `title`
**Severity:** ERROR
**Validation:** Case-insensitive keyword matching

**Why Error:**
Title must match one of the 3 executive slots (CEO, CFO, HR) for outreach purposes. This is a data quality check.

**Accepted Keywords:**

| Slot Type | Keywords |
|-----------|----------|
| CEO | CEO, Chief Executive Officer, Chief Executive |
| CFO | CFO, Chief Financial Officer, Chief Financial |
| HR | HR, Human Resources, People, Talent |

**Example Failures:**
```json
// Missing title
{
  "field": "title",
  "message": "Title is required"
}

// Wrong title
{
  "field": "title",
  "message": "Title must include CEO, CFO, or HR-related keywords"
}
```

**Valid Examples:**
- Chief Executive Officer ✅ (CEO)
- CFO ✅ (CFO)
- Director of Human Resources ✅ (HR)
- VP of Talent Acquisition ✅ (HR - "Talent" keyword)
- Chief People Officer ✅ (HR - "People" keyword)
- Finance Manager ❌ (no CFO/CEO/HR keywords)

---

### Rule 5: Company Link Valid (CRITICAL)

**Field:** `company_unique_id`
**Severity:** CRITICAL
**Validation:** Field present AND exists in `marketing.company_master`

**Why Critical:**
Every person must belong to a valid company. This is a foreign key integrity check.

**Example Failures:**
```json
// Missing company_unique_id
{
  "field": "company_unique_id",
  "message": "Company unique ID is required"
}

// Company doesn't exist in company_master
{
  "field": "company_unique_id",
  "message": "Company unique ID 'xyz-456' does not exist in company_master"
}
```

**Database Check:**
```sql
SELECT company_unique_id
FROM marketing.company_master
WHERE company_unique_id = 'xyz-456';
-- Must return exactly 1 row
```

---

### Rule 6: LinkedIn URL Format (ERROR)

**Field:** `linkedin_url`
**Severity:** ERROR
**Validation:** Must include `linkedin.com/in/`

**Why Error:**
LinkedIn URL is important for enrichment but can be added later. Invalid format indicates data quality issues.

**Example Failures:**
```json
// Missing LinkedIn URL
{
  "field": "linkedin_url",
  "message": "LinkedIn URL is required"
}

// Wrong format (company URL instead of person URL)
{
  "field": "linkedin_url",
  "message": "LinkedIn URL must include 'linkedin.com/in/'"
}
```

**Valid Examples:**
- https://linkedin.com/in/johndoe ✅
- https://www.linkedin.com/in/jane-smith-12345 ✅
- linkedin.com/in/ceo-name ✅ (protocol optional)

**Invalid Examples:**
- https://linkedin.com/company/acme ❌ (company URL)
- https://twitter.com/johndoe ❌ (wrong platform)
- linkedin.com/johndoe ❌ (missing /in/)

---

### Rule 7: Timestamp Last Updated Present (WARNING)

**Field:** `timestamp_last_updated` or `updated_at`
**Severity:** WARNING
**Validation:** Field must not be null

**Why Warning (not Error):**
Timestamp is useful for tracking data freshness but doesn't prevent outreach. This is a data quality indicator.

**Example Failure:**
```json
{
  "field": "timestamp_last_updated",
  "message": "Last updated timestamp is required"
}
```

**Important:**
WARNING severity failures do NOT cause `validation_status = 'invalid'`. Record is still marked as valid if only WARNING failures exist.

---

## Output Format

### validate_person() Function Signature

```python
def validate_person(row: Dict, valid_company_ids: set = None) -> Dict:
    """
    Validate a person record for Phase 1 outreach validation

    Args:
        row: Dictionary from marketing.people_master
        valid_company_ids: Set of valid company IDs from company_master (optional)

    Returns:
        {
            "valid": True/False,
            "reason": "title: Does not match CEO/CFO/HR; email: Invalid format",
            "failures": [
                {"field": "title", "message": "Does not match CEO/CFO/HR"},
                {"field": "email", "message": "Invalid email format"}
            ],
            "person_id": "04.04.02.04.20000.001",
            "company_unique_id": "04.04.02.04.30000.001",
            "full_name": "Jane Smith",
            "email": "jane@acme.com",
            "title": "Finance Manager",
            "linkedin_url": "https://linkedin.com/in/janesmith",
            "validation_status": "invalid"
        }
    """
```

### Output Fields

| Field | Type | Description |
|-------|------|-------------|
| `valid` | boolean | `true` if no CRITICAL/ERROR failures, `false` otherwise |
| `reason` | string or null | Semicolon-separated list of CRITICAL/ERROR failure messages |
| `failures` | array | List of all failures (including WARNING) |
| `person_id` | string | Person's unique identifier |
| `company_unique_id` | string | Associated company identifier |
| `full_name` | string | Person's full name |
| `email` | string | Person's email address |
| `title` | string | Person's job title |
| `linkedin_url` | string | Person's LinkedIn profile URL |
| `validation_status` | string | "valid" or "invalid" |

### Example Outputs

#### Valid Person (All Rules Pass)

```json
{
  "valid": true,
  "reason": null,
  "failures": [],
  "person_id": "04.04.02.04.20000.001",
  "company_unique_id": "04.04.02.04.30000.001",
  "full_name": "John Doe",
  "email": "john@acme.com",
  "title": "Chief Executive Officer",
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "validation_status": "valid"
}
```

#### Invalid Person (Multiple Failures)

```json
{
  "valid": false,
  "reason": "title: Title must include CEO, CFO, or HR-related keywords; linkedin_url: LinkedIn URL must include 'linkedin.com/in/'",
  "failures": [
    {
      "field": "title",
      "message": "Title must include CEO, CFO, or HR-related keywords (HR, Human Resources, People, Talent)"
    },
    {
      "field": "linkedin_url",
      "message": "LinkedIn URL must include 'linkedin.com/in/'"
    }
  ],
  "person_id": "04.04.02.04.20000.002",
  "company_unique_id": "04.04.02.04.30000.001",
  "full_name": "Jane Smith",
  "email": "jane@acme.com",
  "title": "Finance Manager",
  "linkedin_url": "https://linkedin.com/company/acme",
  "validation_status": "invalid"
}
```

#### Person with WARNING Only (Still Valid)

```json
{
  "valid": true,
  "reason": null,
  "failures": [
    {
      "field": "timestamp_last_updated",
      "message": "Last updated timestamp is required"
    }
  ],
  "person_id": "04.04.02.04.20000.003",
  "company_unique_id": "04.04.02.04.30000.001",
  "full_name": "Alice Johnson",
  "email": "alice@acme.com",
  "title": "CFO",
  "linkedin_url": "https://linkedin.com/in/alicejohnson",
  "validation_status": "valid"
}
```

---

## n8n Webhook Integration

### Webhook Configuration

**Webhook URL:** `https://n8n.barton.com/webhook/route-person-failure`
**Method:** POST
**Content-Type:** application/json
**Timeout:** 30 seconds
**Retry Logic:** 3 attempts for 5xx errors, exponential backoff

### Webhook Payload Structure

```json
{
  "type": "person",
  "reason_code": "title: Does not match CEO/CFO/HR; email: Invalid format",
  "row_data": {
    "person_id": "04.04.02.04.20000.002",
    "full_name": "Jane Smith",
    "email": "jane@acme.com",
    "title": "Finance Manager",
    "company_unique_id": "04.04.02.04.30000.001",
    "linkedin_url": "https://linkedin.com/company/acme",
    "timestamp_last_updated": "2025-11-15T10:00:00Z",
    "validation_status": "invalid"
  },
  "state": "WV",
  "timestamp": "2025-11-17T12:00:00Z",
  "pipeline_id": "PRC-PV-RETRO-1731859200",
  "failures": [
    {
      "field": "title",
      "message": "Title must include CEO, CFO, or HR-related keywords"
    },
    {
      "field": "email",
      "message": "Invalid email format"
    }
  ],
  "sheet_id": "1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg",
  "sheet_tab": "Invalid_People"
}
```

### Payload Fields

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Always "person" for people validation |
| `reason_code` | string | Human-readable failure summary |
| `row_data` | object | Complete person record with all fields |
| `state` | string | State code (e.g., "WV") or "unknown" |
| `timestamp` | string | ISO 8601 timestamp of validation |
| `pipeline_id` | string | Unique pipeline run identifier |
| `failures` | array | List of validation failures |
| `sheet_id` | string | Google Sheet ID for routing |
| `sheet_tab` | string | Sheet tab name (always "Invalid_People") |

### Google Sheet Configuration

**Sheet ID:** `1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg`
**Tab Name:** `Invalid_People`
**URL:** `https://docs.google.com/spreadsheets/d/1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg/edit#gid=Invalid_People`

**Expected Columns:**
1. Person ID
2. Full Name
3. Email
4. Title
5. Company ID
6. LinkedIn URL
7. Failure Reason
8. Failures Count
9. State
10. Validated At
11. Pipeline ID

### Error Handling

**Retry Logic for 5xx Errors:**
```python
max_retries = 3
retry_delays = [2, 4, 8]  # seconds (exponential backoff)

for attempt in range(max_retries):
    response = requests.post(webhook_url, json=payload, timeout=30)

    if response.status_code == 200:
        return True  # Success

    elif 500 <= response.status_code < 600:
        # Server error - retry
        if attempt < max_retries - 1:
            time.sleep(retry_delays[attempt])
            continue
        else:
            logger.error(f"Webhook failed after {max_retries} retries")
            return False

    else:
        # 4xx client error - do not retry
        logger.error(f"Webhook rejected: {response.status_code}")
        return False
```

**No Retry for 4xx Errors:**
Client errors (400, 401, 403, 404, etc.) indicate a problem with the payload or authentication. Do not retry these.

---

## Database Updates

### people_master.validation_status

**Column:** `validation_status`
**Type:** VARCHAR
**Values:**
- `'valid'` - All 7 rules passed (or only WARNING failures)
- `'invalid'` - At least one CRITICAL or ERROR failure
- `'pending'` - Not yet validated (default)

**Update Query:**
```sql
UPDATE marketing.people_master
SET validation_status = 'valid'  -- or 'invalid'
WHERE unique_id = '04.04.02.04.20000.001';
```

### pipeline_events Table

**Table:** `marketing.pipeline_events`
**Event Type:** `person_validation_check`

**Sample Event (Valid Person):**
```json
{
  "event_id": "auto-generated-uuid",
  "event_type": "person_validation_check",
  "payload": {
    "person_id": "04.04.02.04.20000.001",
    "valid": true,
    "reason": null,
    "failures_count": 0,
    "validator": "PeopleValidator",
    "pipeline_id": "PRC-PV-RETRO-1731859200"
  },
  "created_at": "2025-11-17T12:00:00Z"
}
```

**Sample Event (Invalid Person):**
```json
{
  "event_id": "auto-generated-uuid",
  "event_type": "person_validation_check",
  "payload": {
    "person_id": "04.04.02.04.20000.002",
    "valid": false,
    "reason": "title: Does not match CEO/CFO/HR; email: Invalid format",
    "failures_count": 2,
    "validator": "PeopleValidator",
    "pipeline_id": "PRC-PV-RETRO-1731859200"
  },
  "created_at": "2025-11-17T12:00:15Z"
}
```

### audit_log Table

**Table:** `shq.audit_log`
**Component:** `retro_people_validator`
**Event Type:** `validation_complete`

**Sample Audit Log Entry:**
```json
{
  "audit_id": "auto-generated-uuid",
  "component": "retro_people_validator",
  "event_type": "validation_complete",
  "event_data": {
    "total": 150,
    "valid": 120,
    "invalid": 30,
    "routed_to_sheets": 28,
    "webhook_success": 26,
    "webhook_failed": 2,
    "state": "WV",
    "pipeline_id": "PRC-PV-RETRO-1731859200",
    "duration_seconds": 45
  },
  "created_at": "2025-11-17T12:05:00Z"
}
```

---

## CLI Usage

### Command Syntax

```bash
python backend/validator/retro_validate_people.py [OPTIONS]
```

### Available Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--state` | string | None | State code to filter records (e.g., WV) |
| `--limit` | integer | None | Limit number of records to process |
| `--dry-run` | flag | False | Test validation without making changes |
| `--output` | string | None | Path to save JSON report |
| `--verbose` | flag | False | Enable verbose logging |

### Usage Examples

#### Example 1: Dry-Run for Testing

```bash
# Test validation logic without database updates
python backend/validator/retro_validate_people.py \
  --state WV \
  --limit 10 \
  --dry-run \
  --verbose

# Output:
# ✅ Loaded 150 people from WV
# 🔍 DRY-RUN MODE: No database updates will be made
# ✅ John Doe: valid
# ❌ Jane Smith: 2 failure(s)
#   - title: Title must include CEO, CFO, or HR-related keywords
#   - email: Invalid email format
# ...
# 📊 Results: 8 valid, 2 invalid (0 routed to sheets in dry-run)
```

#### Example 2: Production Run with State Filter

```bash
# Validate all WV people and route failures
python backend/validator/retro_validate_people.py \
  --state WV

# Output:
# ✅ Loaded 150 people from WV
# ✅ Routed Jane Smith to Google Sheets (ID: 04.04.02.04.20000.002)
# ✅ Routed Bob Wilson to Google Sheets (ID: 04.04.02.04.20000.015)
# ...
# 📊 Results: 120 valid, 30 invalid (28 routed to sheets)
# ✅ Pipeline complete (PRC-PV-RETRO-1731859200)
```

#### Example 3: Batch Processing with Limit

```bash
# Validate first 50 people (for incremental processing)
python backend/validator/retro_validate_people.py \
  --state WV \
  --limit 50

# Output:
# ✅ Loaded 50 people from WV
# ...
# 📊 Results: 42 valid, 8 invalid (7 routed to sheets)
```

#### Example 4: Generate JSON Report

```bash
# Validate and save detailed JSON report
python backend/validator/retro_validate_people.py \
  --state WV \
  --output reports/wv_people_validation_2025-11-17.json

# Output:
# ✅ Loaded 150 people from WV
# ...
# 📊 Results: 120 valid, 30 invalid (28 routed to sheets)
# ✅ Report saved to: reports/wv_people_validation_2025-11-17.json
```

**JSON Report Structure:**
```json
{
  "pipeline_id": "PRC-PV-RETRO-1731859200",
  "started_at": "2025-11-17T12:00:00Z",
  "completed_at": "2025-11-17T12:05:00Z",
  "state": "WV",
  "statistics": {
    "total": 150,
    "valid": 120,
    "invalid": 30,
    "routed_to_sheets": 28,
    "webhook_success": 26,
    "webhook_failed": 2
  },
  "invalid_people": [
    {
      "person_id": "04.04.02.04.20000.002",
      "full_name": "Jane Smith",
      "failures": [
        {"field": "title", "message": "Title must include CEO, CFO, or HR-related keywords"},
        {"field": "email", "message": "Invalid email format"}
      ]
    }
  ]
}
```

#### Example 5: All People (No State Filter)

```bash
# Validate all people across all states
python backend/validator/retro_validate_people.py

# Output:
# ✅ Loaded 500 people from database
# ...
# 📊 Results: 450 valid, 50 invalid (48 routed to sheets)
```

---

## Code Integration

### Using validate_person() in Your Code

```python
from backend.validator.validation_rules import validate_person

# Load valid company IDs first
valid_company_ids = {
    "04.04.02.04.30000.001",
    "04.04.02.04.30000.002",
    "04.04.02.04.30000.003"
}

# Person record from database
person = {
    "person_id": "04.04.02.04.20000.001",
    "full_name": "John Doe",
    "email": "john@acme.com",
    "title": "Chief Executive Officer",
    "company_unique_id": "04.04.02.04.30000.001",
    "linkedin_url": "https://linkedin.com/in/johndoe",
    "timestamp_last_updated": "2025-11-17T10:00:00Z"
}

# Validate
result = validate_person(person, valid_company_ids)

# Check result
if result["valid"]:
    print(f"✅ {result['full_name']} is valid")
else:
    print(f"❌ {result['full_name']}: {result['reason']}")
    for failure in result["failures"]:
        print(f"  - {failure['field']}: {failure['message']}")
```

### Using PeopleValidator Class

```python
from backend.validator.retro_validate_people import PeopleValidator

# Initialize validator
validator = PeopleValidator(dry_run=False)

# Load people (with optional state filter)
people = validator.load_people(state="WV", limit=100)

# Load valid company IDs
valid_company_ids = validator.load_valid_company_ids()

# Validate all people
validator.validate_people(people, valid_company_ids, state="WV")

# Check statistics
stats = validator.stats
print(f"Total: {stats.total}")
print(f"Valid: {stats.valid}")
print(f"Invalid: {stats.invalid}")
print(f"Routed to Sheets: {stats.routed_to_sheets}")

# Generate report
report = validator.generate_report()
```

### Integration with Existing Validators

**Phase 1 Company Validation:**
```python
from backend.validator.retro_validate_neon import CompanyValidator
from backend.validator.retro_validate_people import PeopleValidator

# Step 1: Validate companies first
company_validator = CompanyValidator(dry_run=False)
companies = company_validator.load_companies(state="WV")
company_validator.validate_companies(companies, state="WV")

# Step 2: Validate people for valid companies only
people_validator = PeopleValidator(dry_run=False)
people = people_validator.load_people(state="WV")
valid_company_ids = people_validator.load_valid_company_ids()
people_validator.validate_people(people, valid_company_ids, state="WV")
```

**Phase 2 Outreach Readiness:**
```python
from backend.enrichment.evaluate_outreach_readiness import OutreachReadinessEvaluator

# Step 3: Evaluate outreach readiness (after Phase 1 validation)
evaluator = OutreachReadinessEvaluator(dry_run=False)
companies = evaluator.load_companies(state="WV", only_validated=True)
evaluator.evaluate_companies(companies, state="WV")
```

**Complete Pipeline:**
```bash
# Phase 1a: Validate company structure
python backend/validator/retro_validate_neon.py --state WV

# Phase 1b: Validate people structure
python backend/validator/retro_validate_people.py --state WV

# Phase 2: Check outreach readiness
python backend/enrichment/evaluate_outreach_readiness.py --state WV --only-validated
```

---

## Troubleshooting

### Issue 1: Database Connection Error

**Error:**
```
psycopg2.OperationalError: could not connect to server
```

**Cause:** Invalid or missing `NEON_CONNECTION_STRING` environment variable

**Solution:**
```bash
# Check if .env file exists
ls -la ctb/sys/toolbox-hub/.env

# Verify NEON_CONNECTION_STRING is set
cat ctb/sys/toolbox-hub/.env | grep NEON_CONNECTION_STRING

# Test connection manually
psql "$NEON_CONNECTION_STRING" -c "SELECT NOW();"
```

---

### Issue 2: No People Loaded

**Error:**
```
✅ Loaded 0 people from WV
```

**Cause:** State filter not matching any records, or database is empty

**Solution:**
```sql
-- Check if people exist in database
SELECT COUNT(*) as total_people
FROM marketing.people_master;

-- Check if state filter is correct
SELECT
    c.state,
    COUNT(*) as people_count
FROM marketing.people_master p
JOIN marketing.company_master c ON p.company_unique_id = c.company_unique_id
GROUP BY c.state
ORDER BY people_count DESC;
```

**Action:** Remove `--state` filter or use correct state code

---

### Issue 3: All People Failing Company Link Validation

**Error:**
```
❌ All people failing: company_unique_id does not exist in company_master
```

**Cause:** `valid_company_ids` set is empty or doesn't include the companies

**Solution:**
```sql
-- Check if companies exist
SELECT COUNT(*) as total_companies
FROM marketing.company_master;

-- Find people with invalid company links
SELECT
    p.unique_id,
    p.full_name,
    p.company_unique_id,
    CASE
        WHEN c.company_unique_id IS NULL THEN 'Company Not Found'
        ELSE 'Valid'
    END as status
FROM marketing.people_master p
LEFT JOIN marketing.company_master c ON p.company_unique_id = c.company_unique_id
WHERE c.company_unique_id IS NULL;
```

**Action:** Run Phase 1 Company Validation first to ensure companies are valid

---

### Issue 4: Webhook Failing (n8n Routing)

**Error:**
```
❌ Webhook failed: Connection refused
```

**Cause:** n8n webhook is not reachable or URL is incorrect

**Solution:**
```bash
# Test webhook connectivity
curl -X POST https://n8n.barton.com/webhook/route-person-failure \
  -H "Content-Type: application/json" \
  -d '{"type": "person", "test": true}'

# Check if URL is correct
echo $N8N_PEOPLE_WEBHOOK
```

**Temporary Workaround:** Use `--dry-run` mode to skip webhook routing

---

### Issue 5: Title Validation Too Strict

**Error:**
```
❌ "Chief People Officer" failing title validation
```

**Cause:** Title contains valid HR keywords but not matching

**Solution:** Check validation_rules.py line ~780 for keyword list

**Current HR Keywords:**
- HR
- Human Resources
- People
- Talent

**If you need to add more keywords:**
```python
# In validation_rules.py, update PersonValidator.validate_title()
hr_keywords = ["HR", "HUMAN RESOURCES", "PEOPLE", "TALENT", "RECRUITING"]
```

---

### Issue 6: validation_status Not Updating

**Error:**
```
✅ Validation complete but validation_status still 'pending'
```

**Cause:** Dry-run mode is enabled, or database update query failed

**Solution:**
```bash
# Check if dry-run mode is active
python backend/validator/retro_validate_people.py --state WV --verbose

# Verify database updates manually
psql "$NEON_CONNECTION_STRING" -c "
SELECT
    validation_status,
    COUNT(*) as count
FROM marketing.people_master
WHERE unique_id IN (
    SELECT unique_id FROM marketing.people_master LIMIT 10
)
GROUP BY validation_status;
"
```

**Action:** Remove `--dry-run` flag for production updates

---

## Production Deployment

### Pre-Deployment Checklist

**Environment:**
- [ ] `.env` file configured with `NEON_CONNECTION_STRING`
- [ ] n8n webhook accessible at `https://n8n.barton.com/webhook/route-person-failure`
- [ ] Google Sheet created with ID `1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg`
- [ ] Google Sheet has tab named `Invalid_People`
- [ ] Database tables exist: `marketing.people_master`, `marketing.company_master`, `marketing.pipeline_events`, `shq.audit_log`

**Testing:**
- [ ] Dry-run test completed with sample data
- [ ] Database connection verified
- [ ] Webhook routing verified (test payload sent)
- [ ] All 7 validation rules tested individually
- [ ] Title matching tested with CEO/CFO/HR variants

**Validation:**
- [ ] Run Phase 1 Company Validation first (to populate valid companies)
- [ ] Test with `--limit 10` before full run
- [ ] Verify `validation_status` updates in database
- [ ] Verify `pipeline_events` logging
- [ ] Verify `audit_log` entries

**Backup:**
- [ ] Create database backup before production run
- [ ] Save JSON report for audit trail
- [ ] Document any custom configurations

---

### Deployment Steps

#### Step 1: Run Phase 1 Company Validation (Prerequisite)

```bash
# Ensure companies are validated first
cd ctb/sys/toolbox-hub
python backend/validator/retro_validate_neon.py --state WV
```

**Expected Output:**
```
✅ Loaded 150 companies from WV
✅ Valid: 145 companies
❌ Invalid: 5 companies (routed to Google Sheets)
```

---

#### Step 2: Test with Dry-Run

```bash
# Test validation logic without database updates
python backend/validator/retro_validate_people.py \
  --state WV \
  --limit 10 \
  --dry-run \
  --verbose
```

**Expected Output:**
```
✅ Loaded 150 people from WV (limited to 10)
🔍 DRY-RUN MODE: No database updates will be made
✅ John Doe: valid
❌ Jane Smith: 2 failure(s)
...
📊 Results: 8 valid, 2 invalid (0 routed to sheets in dry-run)
```

---

#### Step 3: Small Batch Test (Production)

```bash
# Run production validation on small batch
python backend/validator/retro_validate_people.py \
  --state WV \
  --limit 10 \
  --output reports/wv_people_test_batch.json
```

**Verify:**
1. Database `validation_status` updated
2. `pipeline_events` logged
3. Invalid records routed to Google Sheets
4. JSON report generated

---

#### Step 4: Full Production Run

```bash
# Run validation on all WV people
python backend/validator/retro_validate_people.py \
  --state WV \
  --output reports/wv_people_validation_$(date +%Y%m%d).json \
  --verbose
```

**Expected Output:**
```
✅ Loaded 150 people from WV
✅ Routed 28 invalid people to Google Sheets
📊 Results: 120 valid, 30 invalid (28 routed to sheets)
✅ Report saved to: reports/wv_people_validation_20251117.json
✅ Pipeline complete (PRC-PV-RETRO-1731859200)
```

---

#### Step 5: Verify Results

```sql
-- Check validation status distribution
SELECT
    validation_status,
    COUNT(*) as count
FROM marketing.people_master
WHERE unique_id IN (
    SELECT p.unique_id
    FROM marketing.people_master p
    JOIN marketing.company_master c ON p.company_unique_id = c.company_unique_id
    WHERE c.state = 'WV'
)
GROUP BY validation_status
ORDER BY count DESC;

-- Expected result:
--  validation_status | count
-- -------------------+-------
--  valid             |   120
--  invalid           |    30
```

```sql
-- Check recent pipeline events
SELECT
    event_type,
    payload->>'person_id' as person_id,
    payload->>'valid' as valid,
    payload->>'reason' as reason,
    created_at
FROM marketing.pipeline_events
WHERE event_type = 'person_validation_check'
  AND created_at >= NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC
LIMIT 10;
```

```sql
-- Check audit log
SELECT
    component,
    event_type,
    event_data,
    created_at
FROM shq.audit_log
WHERE component = 'retro_people_validator'
  AND created_at >= NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC
LIMIT 5;
```

---

#### Step 6: Review Google Sheets

1. Open Google Sheet: https://docs.google.com/spreadsheets/d/1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg/edit#gid=Invalid_People
2. Verify `Invalid_People` tab contains routed records
3. Check failure reasons are clear and actionable
4. Assign records to team for manual review

---

### Post-Deployment Verification

**Success Criteria:**
- ✅ All people processed (count matches database)
- ✅ `validation_status` field updated for all people
- ✅ Invalid people routed to Google Sheets (match count)
- ✅ `pipeline_events` logged (1 event per person)
- ✅ `audit_log` entry created (1 summary entry)
- ✅ JSON report generated and saved
- ✅ No webhook failures (or < 5% failure rate)

**If Issues Occur:**
1. Check error logs in console output
2. Review `shq.audit_log` for failures
3. Verify webhook connectivity
4. Re-run with `--dry-run` to diagnose
5. Use `--limit` to process in smaller batches

---

## Related Documentation

### Phase 1 Company Validation
- **File:** `VALIDATE_COMPANY_FINAL.md`
- **Script:** `backend/validator/retro_validate_neon.py`
- **Purpose:** Validate company structure before people validation

### Phase 2 Outreach Readiness
- **File:** `PHASE2_OUTREACH_READINESS.md`
- **Script:** `backend/enrichment/evaluate_outreach_readiness.py`
- **Purpose:** Check slot fills, enrichment, email verification

### Validation Pipeline Quick Start
- **File:** `VALIDATION_PIPELINE_QUICKSTART.md`
- **Purpose:** End-to-end guide for Phase 1 + Phase 2

### Validation Rules Reference
- **File:** `backend/validator/validation_rules.py`
- **Purpose:** Shared validation logic for companies and people

---

**Last Updated:** 2025-11-17
**Status:** ✅ Production Ready
**Maintainer:** Barton Outreach Core Team
**Version:** 1.0.0

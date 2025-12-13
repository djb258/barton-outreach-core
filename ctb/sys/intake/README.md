# PLE Intake Validator - Two-Layer Validation System

**Purpose:** Catch garbage at the door, not when it hits the database wall.

**Architecture:**
1. **INTAKE GATE** (these scripts) - validates BEFORE insert, quarantines bad records
2. **DB CONSTRAINTS** (schema) - backstop if something slips through

---

## Files

| File | Purpose |
|------|---------|
| `intake_validator.py` | Main validation engine with batch processing |
| `review_quarantine.py` | Quarantine management and cleanup |
| `README.md` | This file - usage guide |

---

## Installation

```bash
# Install dependencies
pip install psycopg2-binary python-dotenv

# Verify .env has database connection
cat .env | grep NEON_CONNECTION_STRING

# Test connection
python intake_validator.py --help
```

---

## Usage Examples

### 1. Validate Company Records (Dry Run)

```bash
# Prepare input file: companies.json
cat > companies.json << 'EOF'
[
  {
    "company_name": "Widget Corp",
    "employee_count": 150,
    "address_state": "PA",
    "source_system": "clay",
    "website_url": "https://widgetcorp.com"
  },
  {
    "company_name": "Invalid Co",
    "employee_count": 25,
    "address_state": "NY",
    "source_system": "clay"
  }
]
EOF

# Run validation (dry run - no inserts)
python ctb/sys/intake/intake_validator.py \
  --input companies.json \
  --type company \
  --source clay \
  --mode validate
```

**Output:**
```
INTAKE VALIDATION REPORT
============================================================
Source: clay
Record Type: company
Mode: validate
Timestamp: 2025-11-26T13:00:00

SUMMARY
------------------------------------------------------------
Total Records: 2
Valid: 1 (50.0%)
Invalid: 1 (50.0%)
Duplicates: 0 (0.0%)

INVALID RECORDS (Quarantined)
------------------------------------------------------------
Record 2:
  Data: {
    "company_name": "Invalid Co",
    "employee_count": 25,
    "address_state": "NY",
    "source_system": "clay"
  }
  Errors:
    - employee_count: 25 below minimum 50
    - address_state: NY not in ['PA', 'VA', 'MD', 'OH', 'WV', 'KY']
```

### 2. Validate and Insert Valid Records

```bash
# Same input, but INSERT mode
python ctb/sys/intake/intake_validator.py \
  --input companies.json \
  --type company \
  --source clay \
  --mode insert
```

**What happens:**
- Valid records → inserted into `marketing.company_master`
- Invalid records → quarantined in `marketing.intake_quarantine`
- Duplicates → skipped (reported in output)

### 3. Validate People Records

```bash
cat > people.json << 'EOF'
[
  {
    "company_unique_id": "04.04.01.01.00001.001",
    "first_name": "John",
    "last_name": "Smith",
    "title": "CEO",
    "linkedin_url": "https://www.linkedin.com/in/johnsmith",
    "email": "john@company.com",
    "source_system": "phantombuster"
  },
  {
    "company_unique_id": "04.04.01.99.99999.999",
    "first_name": "Jane",
    "last_name": "Doe",
    "title": "CFO",
    "source_system": "phantombuster"
  }
]
EOF

python ctb/sys/intake/intake_validator.py \
  --input people.json \
  --type person \
  --source phantombuster \
  --mode validate
```

**Errors caught:**
- Record 1: No errors (has both linkedin_url and email)
- Record 2: `contact: must have linkedin_url OR email` (missing both)
- Record 2: `company_unique_id: 04.04.01.99.99999.999 does not exist in company_master`

### 4. Review Quarantine

```bash
# Get quarantine statistics
python ctb/sys/intake/review_quarantine.py --action stats
```

**Output:**
```
QUARANTINE STATISTICS
============================================================

UNRESOLVED RECORDS
------------------------------------------------------------
COMPANY: 15 records
  Oldest: 2025-11-20 10:30:00
  Newest: 2025-11-26 13:00:00
PERSON: 8 records
  Oldest: 2025-11-21 14:15:00
  Newest: 2025-11-26 13:00:00

RESOLVED RECORDS
------------------------------------------------------------
COMPANY - fixed: 5
PERSON - rejected: 2

MOST COMMON ERRORS
------------------------------------------------------------
  employee_count: X below minimum 50: 8 occurrences
  address_state: NY not in [...]: 6 occurrences
  contact: must have linkedin_url OR email: 4 occurrences
  company_unique_id: XXX does not exist: 3 occurrences
```

### 5. List Quarantined Records

```bash
# List all unresolved quarantined companies (max 50)
python ctb/sys/intake/review_quarantine.py \
  --action list \
  --type company \
  --limit 10
```

### 6. Export Quarantine to JSON

```bash
# Export for manual review/fixing
python ctb/sys/intake/review_quarantine.py \
  --action export \
  --type company \
  --output quarantine_companies.json

# Fix records in external tool (Excel, OpenRefine, etc.)
# Then re-run validator with --mode insert
```

### 7. Mark Quarantined Record as Resolved

```bash
# After manually fixing and inserting record
python ctb/sys/intake/review_quarantine.py \
  --action resolve \
  --id 123 \
  --resolution fixed

# Or mark as permanently rejected
python ctb/sys/intake/review_quarantine.py \
  --action resolve \
  --id 124 \
  --resolution rejected

# Or mark as merged with existing record
python ctb/sys/intake/review_quarantine.py \
  --action resolve \
  --id 125 \
  --resolution merged
```

### 8. Clean Up Old Resolved Records

```bash
# Delete resolved records older than 90 days
python ctb/sys/intake/review_quarantine.py \
  --action cleanup \
  --days 90
```

---

## Kill Switch

If **>20% of batch fails validation**, the script:

1. **HALTS** all inserts
2. **QUARANTINES** entire batch
3. **ALERTS**: `BATCH REJECTED - XX% failure rate exceeds 20% threshold`
4. **REQUIRES** manual review before retry

**Exit codes:**
- `0` = All valid
- `1` = Some invalid records (but <20%)
- `2` = Kill switch triggered (>20% failure rate)

**Example:**
```bash
python intake_validator.py --input bad_batch.json --type company --source clay --mode insert
echo $?  # Returns 2 if kill switch triggered
```

---

## Validation Rules Reference

### Company Rules

| Field | Rule | Action if Invalid |
|-------|------|-------------------|
| company_name | Required, not empty | REJECT → Quarantine |
| employee_count | Required, integer, >= 50 | REJECT → Quarantine |
| address_state | Required, IN ('PA','VA','MD','OH','WV','KY') | REJECT → Quarantine |
| source_system | Required, not empty | REJECT → Quarantine |
| website_url | Optional | PASS |
| industry | Optional | PASS |

**Auto-normalization:**
- State names converted: "West Virginia" → "WV"
- Uppercase applied: "pa" → "PA"

**Duplicate detection:**
- Match: `LOWER(company_name) = existing AND address_state = existing`
- Action: Skip insert, report in duplicate_matches

### Person Rules

| Field | Rule | Action if Invalid |
|-------|------|-------------------|
| company_unique_id | Required, must exist in company_master | REJECT → Quarantine |
| first_name | Required, not empty | REJECT → Quarantine |
| last_name | Required, not empty | REJECT → Quarantine |
| title | Required, not empty | REJECT → Quarantine |
| linkedin_url | Conditional: required if no email | REJECT if both missing |
| email | Conditional: required if no linkedin_url | REJECT if both missing |

**Contact validation:**
- Must have `linkedin_url` OR `email` (or both)
- LinkedIn format: Must start with `https://www.linkedin.com/`
- Email format: Must contain `@` and `.` in domain

**Validation status:**
- `full`: Has both linkedin_url and email
- `linkedin_only`: Has linkedin_url but no email
- `email_only`: Has email but no linkedin_url
- `invalid`: Has neither (REJECTED)

**Duplicate detection:**
1. First check: `linkedin_url = existing` (strongest match)
2. Second check: `email = existing`
3. Action: Skip insert, report in duplicate_matches

---

## Integration with Data Sources

### Clay.com

```bash
# 1. Export from Clay to JSON
# (Clay → Export → JSON format)

# 2. Validate
python intake_validator.py \
  --input clay_export.json \
  --type company \
  --source clay \
  --mode validate

# 3. Fix errors, re-export, validate again

# 4. Insert clean data
python intake_validator.py \
  --input clay_export_clean.json \
  --type company \
  --source clay \
  --mode insert
```

### PhantomBuster

```bash
# 1. Export from PhantomBuster
# (PhantomBuster → Download results → JSON)

# 2. Validate and insert
python intake_validator.py \
  --input pb_linkedin_scrape.json \
  --type person \
  --source phantombuster \
  --mode insert
```

### ScraperAPI / Custom Scripts

```bash
# 1. Format output as JSON array
# 2. Run validator
python intake_validator.py \
  --input scraper_output.json \
  --type company \
  --source scraperapi \
  --mode insert
```

---

## Quarantine Workflow

```
Data Source (Clay/PB/API)
    ↓
[INPUT JSON FILE]
    ↓
intake_validator.py --mode insert
    ↓
┌───────────────┬─────────────────────┬────────────────┐
│  VALID        │  INVALID            │  DUPLICATE     │
│  (insert)     │  (quarantine)       │  (skip)        │
└───────────────┴─────────────────────┴────────────────┘
                         ↓
              marketing.intake_quarantine
                         ↓
              review_quarantine.py --action list
                         ↓
              [MANUAL FIX]
                         ↓
              Re-run validator with fixed data
                         ↓
              Mark as resolved (--action resolve)
```

---

## Database Schema

### marketing.intake_quarantine

```sql
CREATE TABLE marketing.intake_quarantine (
    id SERIAL PRIMARY KEY,
    record_type VARCHAR NOT NULL CHECK (record_type IN ('company','person')),
    raw_payload JSONB NOT NULL,
    validation_errors JSONB NOT NULL,
    source VARCHAR,
    quarantined_at TIMESTAMP NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP,
    resolution_action VARCHAR CHECK (resolution_action IN ('fixed','rejected','merged'))
);
```

**Indexes:**
- `idx_quarantine_type` on (record_type)
- `idx_quarantine_date` on (quarantined_at)
- `idx_quarantine_unresolved` on (resolved_at) WHERE resolved_at IS NULL

**Queries:**

```sql
-- Get all unresolved companies
SELECT * FROM marketing.intake_quarantine
WHERE record_type = 'company'
AND resolved_at IS NULL
ORDER BY quarantined_at DESC;

-- Get error frequency
SELECT
    jsonb_array_elements_text(validation_errors) as error,
    COUNT(*) as count
FROM marketing.intake_quarantine
WHERE resolved_at IS NULL
GROUP BY error
ORDER BY count DESC;

-- Clean up old resolved records (>90 days)
DELETE FROM marketing.intake_quarantine
WHERE resolved_at IS NOT NULL
AND resolved_at < NOW() - INTERVAL '90 days';
```

---

## Benefits of Two-Layer Validation

### Layer 1: Intake Gate (This Script)

**Pros:**
- Meaningful error messages back to source
- Quarantine table for review instead of silent rejection
- Audit trail of what failed and why
- Faster feedback loop than waiting for DB errors
- Batch-level kill switch prevents mass contamination

**Cons:**
- Adds extra step in data pipeline
- Requires Python runtime

### Layer 2: DB Constraints (Schema)

**Pros:**
- Guarantees data integrity at DB level
- Protects against direct SQL inserts
- Enforces rules even if script bypassed
- Performance (constraint checks are fast)

**Cons:**
- Less friendly error messages
- No quarantine mechanism (just fails)
- Harder to debug bulk failures

### Together

**Result:** Rock-solid data quality with maximum visibility.

---

## Monitoring & Alerts

### Daily Checks

```bash
# Add to cron: daily quarantine report
0 9 * * * python /path/to/review_quarantine.py --action stats | mail -s "PLE Quarantine Report" dave@example.com
```

### Grafana Alerts

```sql
-- Alert if >10 unresolved records for >7 days
SELECT COUNT(*)
FROM marketing.intake_quarantine
WHERE resolved_at IS NULL
AND quarantined_at < NOW() - INTERVAL '7 days';

-- Alert on high failure rate (track in separate metrics table)
```

---

## Next Steps

1. **Test validator** with sample data from Clay/PhantomBuster
2. **Integrate into n8n workflow** (n8n → download → validate → insert)
3. **Set up daily quarantine review** (automated report)
4. **Add Grafana panel** for quarantine metrics
5. **Document common errors** and how to fix them

---

**Ready to validate!** 🚀

No more garbage hitting the database wall.

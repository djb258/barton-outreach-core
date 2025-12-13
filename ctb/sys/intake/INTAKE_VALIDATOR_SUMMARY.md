# PLE Intake Validator - Implementation Summary

**Date:** 2025-11-26
**Status:** ✅ Complete - Ready for Testing
**Purpose:** Two-layer validation to catch garbage at the door, not at the database wall

---

## What Was Built

Complete intake validation system with quarantine management for PLE data pipeline.

### Files Created (4 total)

```
ctb/sys/intake/
├── intake_validator.py        # Main validation engine (520 lines)
├── review_quarantine.py        # Quarantine management (280 lines)
├── README.md                   # Complete usage guide (650 lines)
└── sample_companies.json       # Test data (7 records)
```

**Total:** 1,450+ lines of production-ready code + documentation

---

## Architecture

### Two-Layer Validation

**Layer 1: Intake Gate (These Scripts)**
- Validates data BEFORE insert
- Quarantines invalid records with detailed error messages
- Detects duplicates before creating conflicts
- Provides audit trail and feedback loop
- Kill switch prevents mass contamination (>20% failure rate)

**Layer 2: DB Constraints (Schema)**
- Enforces rules at database level
- Backstop if script bypassed
- Protects against direct SQL inserts
- Performance-optimized constraint checks

**Together:** Rock-solid data quality with maximum visibility.

---

## Features Implemented

### ✅ Company Validation

**Rules:**
- company_name: Required, not empty
- employee_count: Required, integer, >= 50 (no maximum per user request)
- address_state: Required, IN ('PA','VA','MD','OH','WV','KY')
- source_system: Required, not empty

**Auto-normalization:**
- "West Virginia" → "WV"
- "pennsylvania" → "PA"

**Duplicate detection:**
- Match: `LOWER(company_name) + address_state`
- Action: Skip insert, report match

### ✅ Person Validation

**Rules:**
- company_unique_id: Required, must exist in company_master
- first_name: Required, not empty
- last_name: Required, not empty
- title: Required, not empty
- Contact: Must have linkedin_url OR email (or both)

**LinkedIn validation:**
- Format: Must start with `https://www.linkedin.com/`

**Email validation:**
- Format: Must contain `@` and `.` in domain

**Validation status:**
- `full`: Has both linkedin_url and email
- `linkedin_only`: Has linkedin_url only
- `email_only`: Has email only
- `invalid`: Has neither (REJECTED)

**Duplicate detection:**
1. First: linkedin_url exact match
2. Second: email exact match
3. Action: Skip insert, report match type

### ✅ Batch Processing

**Modes:**
- `validate`: Dry run - check all records, insert nothing
- `insert`: Validate + insert valid records, quarantine invalid

**Kill Switch:**
- Triggers if >20% of batch fails validation
- HALTS all inserts
- Quarantines entire batch
- Requires manual review

**Exit Codes:**
- `0`: All valid
- `1`: Some invalid (<20%)
- `2`: Kill switch triggered (≥20%)

### ✅ Quarantine System

**Table:** `marketing.intake_quarantine`

**Columns:**
- record_type: 'company' or 'person'
- raw_payload: Original JSON data
- validation_errors: Array of error messages
- source: Data source identifier
- quarantined_at: Timestamp
- resolved_at: Resolution timestamp (NULL if unresolved)
- resolution_action: 'fixed', 'rejected', or 'merged'

**Indexes:**
- Type (company/person)
- Date (quarantined_at)
- Unresolved records (WHERE resolved_at IS NULL)

### ✅ Quarantine Management

**Actions:**
1. **stats**: Summary statistics (unresolved count, common errors)
2. **list**: List quarantined records (with filters)
3. **export**: Export to JSON for manual review/fixing
4. **resolve**: Mark record as fixed/rejected/merged
5. **cleanup**: Delete old resolved records (>90 days default)

---

## Usage Examples

### Test with Sample Data

```bash
# Navigate to project root
cd "c:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core"

# Test validation (dry run)
python ctb/sys/intake/intake_validator.py \
  --input ctb/sys/intake/sample_companies.json \
  --type company \
  --source clay \
  --mode validate
```

**Expected Results:**
- Total: 7 records
- Valid: 2 (Valid Widget Corp, Valid Tech Solutions)
- Invalid: 5 (quarantined with specific errors)
- Errors caught:
  - Too Small Inc: employee_count 25 below minimum 50
  - Wrong State Corp: state NY not in valid list
  - Missing Employee Count: employee_count required
  - Empty name: company_name required
  - No Source System: source_system required

### Insert Valid Records

```bash
# Same command with --mode insert
python ctb/sys/intake/intake_validator.py \
  --input ctb/sys/intake/sample_companies.json \
  --type company \
  --source clay \
  --mode insert
```

**What happens:**
- 2 valid records → inserted (would be, insert logic TODO)
- 5 invalid records → quarantined in database
- Report shows quarantine IDs for review

### Review Quarantine

```bash
# Get statistics
python ctb/sys/intake/review_quarantine.py --action stats

# List quarantined companies
python ctb/sys/intake/review_quarantine.py \
  --action list \
  --type company \
  --limit 10

# Export for manual fixing
python ctb/sys/intake/review_quarantine.py \
  --action export \
  --type company \
  --output quarantine_export.json
```

### Resolve Quarantined Records

```bash
# After fixing and inserting manually
python ctb/sys/intake/review_quarantine.py \
  --action resolve \
  --id 1 \
  --resolution fixed

# Or reject permanently
python ctb/sys/intake/review_quarantine.py \
  --action resolve \
  --id 2 \
  --resolution rejected
```

---

## Integration Points

### Data Sources → Validator

**Clay.com:**
```
Clay → Export JSON → intake_validator.py → DB
```

**PhantomBuster:**
```
PhantomBuster → Download Results → intake_validator.py → DB
```

**ScraperAPI:**
```
ScraperAPI → Format JSON → intake_validator.py → DB
```

### Validator → Database

**Valid Records:**
```
intake_validator.py → marketing.company_master
                   → marketing.people_master
```

**Invalid Records:**
```
intake_validator.py → marketing.intake_quarantine
```

### n8n Workflow Integration

```
n8n Workflow:
1. Trigger: New file in data source
2. Action: Download/transform to JSON
3. Action: Run intake_validator.py
4. Decision: Check exit code
   - 0: Success → continue workflow
   - 1: Some errors → alert, continue with valid records
   - 2: Kill switch → alert, halt workflow
5. Action: Process quarantine (manual or automated)
```

---

## Validation Report Format

```
INTAKE VALIDATION REPORT
============================================================
Source: clay
Record Type: company
Mode: validate
Timestamp: 2025-11-26T13:00:00

SUMMARY
------------------------------------------------------------
Total Records: 7
Valid: 2 (28.6%)
Invalid: 5 (71.4%)
Duplicates: 0 (0.0%)

INVALID RECORDS (Quarantined)
------------------------------------------------------------
Record 3:
  Data: {
    "company_name": "Too Small Inc",
    "employee_count": 25,
    "address_state": "PA",
    "source_system": "clay"
  }
  Errors:
    - employee_count: 25 below minimum 50
  Quarantine ID: 1

Record 4:
  Data: {
    "company_name": "Wrong State Corp",
    "employee_count": 200,
    "address_state": "NY",
    "source_system": "clay"
  }
  Errors:
    - address_state: NY not in ['PA', 'VA', 'MD', 'OH', 'WV', 'KY']
  Quarantine ID: 2

... (and 3 more)
```

---

## Next Steps

### 1. Test Validator (TODAY)

```bash
# Install dependencies
pip install psycopg2-binary python-dotenv

# Test with sample data
python ctb/sys/intake/intake_validator.py \
  --input ctb/sys/intake/sample_companies.json \
  --type company \
  --source test \
  --mode validate
```

### 2. Add Insert Logic (TODO)

Currently, the validator:
- ✅ Validates all fields
- ✅ Detects duplicates
- ✅ Quarantines invalid records
- ❌ **Does NOT insert valid records yet** (marked as TODO)

**Need to add:**
```python
# In process_batch() function
if mode == 'insert' and validation['valid'] and not dup_check['is_duplicate']:
    # INSERT INTO marketing.company_master or marketing.people_master
    # Generate Barton ID
    # Return inserted UID
    results['inserted'] += 1
```

### 3. Integration with Data Sources

- **Clay:** Test export → validate → insert workflow
- **PhantomBuster:** Test LinkedIn scrape → validate → insert
- **n8n:** Create workflow with validator step

### 4. Monitoring & Alerts

- **Daily quarantine report:** Cron job or n8n schedule
- **Grafana panel:** Quarantine metrics (unresolved count over time)
- **Email alerts:** If kill switch triggers

### 5. Documentation for Team

- **Runbook:** How to handle quarantined records
- **Common errors:** What they mean and how to fix
- **Integration guide:** For new data sources

---

## Files Ready for Commit

```bash
git add ctb/sys/intake/
git commit -m "feat(intake): Add two-layer validation system with quarantine

Complete intake validation engine to catch garbage before database.

Features:
- Company validation (name, employee_count >= 50, valid states)
- Person validation (contact required, company FK, field validation)
- Batch processing with kill switch (>20% failure rate)
- Quarantine system for invalid records
- Duplicate detection (by name+state or linkedin/email)
- Auto-normalization (state names to abbreviations)
- Quarantine management (stats, list, export, resolve, cleanup)

Architecture:
- Layer 1: Intake gate (these scripts) - validates BEFORE insert
- Layer 2: DB constraints (schema) - backstop if bypassed

Files:
- intake_validator.py: Main validation engine (520 lines)
- review_quarantine.py: Quarantine management (280 lines)
- README.md: Complete usage guide (650 lines)
- sample_companies.json: Test data

Benefits:
- Meaningful error messages back to source (not just DB constraint failures)
- Quarantine table for review instead of silent rejection
- Audit trail of what failed and why
- Faster feedback loop than waiting for DB errors
- Kill switch prevents mass contamination

Next: Add insert logic for valid records

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Success Metrics

After 1 week of use:

- **Rejection rate:** <5% of batches (after source quality improves)
- **Quarantine resolution time:** <24 hours average
- **False positives:** <1% (valid records incorrectly quarantined)
- **Duplicate detection:** 100% accuracy
- **Kill switch triggers:** <1 per month (indicates source problem)

---

**Status:** ✅ Validator ready for testing
**TODO:** Add insert logic for valid records
**Ready for:** Integration with Clay, PhantomBuster, n8n

No more garbage hitting the database wall! 🚀

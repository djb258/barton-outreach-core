# validate_company() Function - Final Implementation

**Status:** ✅ Production Ready
**Date:** 2025-11-17
**Commit:** d7b2749
**Branch:** sys/outreach-tools-backend
**Purpose:** Retroactive Neon outreach pipeline validation

---

## 📋 Overview

The `validate_company(row, slot_rows)` function validates company records from the Neon database for the retroactive outreach pipeline. It checks **structure and slot presence only** - NOT enrichment status, email validity, or outreach readiness.

**What It Validates:**
- ✅ Company structure (name, website, employee count, LinkedIn URL)
- ✅ Slot presence (CEO, CFO, HR must exist - filled or unfilled)

**What It Does NOT Validate:**
- ❌ Enrichment status
- ❌ Email deliverability
- ❌ Slot fill status (`is_filled` field)
- ❌ Outreach readiness

---

## 🔧 Function Signature

```python
def validate_company(row: Dict, slot_rows: List[Dict]) -> Dict
```

**Parameters:**
- `row`: Dictionary from `marketing.company_master` table
- `slot_rows`: List of slot dictionaries from `marketing.company_slots` table
  - Filtered by: `WHERE company_unique_id = row["company_unique_id"]`

**Returns:**
```python
{
    "valid": True/False,
    "reason": String (first failure reason or None if valid),
    "severity": "INFO" | "WARNING" | "ERROR" | "CRITICAL",
    "missing_fields": List of missing fields or slots
}
```

---

## 🎯 Validation Rules

### Rule 1: company_name
- **Must exist** and be >= 3 characters
- **Severity:** CRITICAL
- **Example failure:** `"AB"` → "Company name must be at least 3 characters"

### Rule 2: website
- **Must start** with `http://` or `https://`
- **Must contain** a domain (with `.`)
- **Severity:** ERROR
- **Example failure:** `"acme.com"` → "Website must start with http:// or https://"

### Rule 3: employee_count
- **Must be** integer > 50 (NOT >= 50)
- **Severity:** ERROR
- **Example failure:** `50` → "Employee count must be greater than 50 (current: 50)"

### Rule 4: linkedin_url
- **Must contain** `"linkedin.com/company/"`
- **Severity:** ERROR
- **Example failure:** `"https://acme.com"` → "LinkedIn URL must contain 'linkedin.com/company/'"

### Rule 5: Slot Presence
- **All 3 slots** must exist: CEO, CFO, HR
- **Does NOT check** `is_filled` status
- **Severity:** ERROR (per missing slot)
- **Example failure:** Missing CFO slot → "Missing CFO slot (slot must exist, even if unfilled)"

---

## 📊 Return Format Examples

### Example 1: Valid Company

**Input:**
```python
company_row = {
    "company_name": "Acme Corporation",
    "website": "https://acme.com",
    "employee_count": 250,
    "linkedin_url": "https://linkedin.com/company/acme-corp"
}

slot_rows = [
    {"slot_type": "CEO", "is_filled": True},
    {"slot_type": "CFO", "is_filled": False},  # Unfilled OK
    {"slot_type": "HR", "is_filled": True}
]

result = validate_company(company_row, slot_rows)
```

**Output:**
```python
{
    "valid": True,
    "reason": None,
    "severity": "INFO",
    "missing_fields": []
}
```

### Example 2: Invalid Company (Multiple Failures)

**Input:**
```python
company_row = {
    "company_name": "XY",  # Too short
    "website": "acme.com",  # Missing http://
    "employee_count": 30,  # Too low
    "linkedin_url": "https://acme.com"  # Wrong format
}

slot_rows = [
    {"slot_type": "CEO", "is_filled": True},
    {"slot_type": "HR", "is_filled": False}
    # CFO missing!
]

result = validate_company(company_row, slot_rows)
```

**Output:**
```python
{
    "valid": False,
    "reason": "Company name must be at least 3 characters",  # First failure
    "severity": "CRITICAL",
    "missing_fields": [
        "company_name",
        "website",
        "employee_count",
        "linkedin_url",
        "slot_CFO"
    ]
}
```

### Example 3: Invalid Company (No Slots)

**Input:**
```python
company_row = {
    "company_name": "No Slots Corp",
    "website": "https://noslots.com",
    "employee_count": 100,
    "linkedin_url": "https://linkedin.com/company/noslots"
}

slot_rows = []  # No slots at all

result = validate_company(company_row, slot_rows)
```

**Output:**
```python
{
    "valid": False,
    "reason": "Missing CEO slot (slot must exist, even if unfilled)",
    "severity": "ERROR",
    "missing_fields": [
        "slot_CEO",
        "slot_CFO",
        "slot_HR"
    ]
}
```

### Example 4: Edge Case (employee_count = 50)

**Input:**
```python
company_row = {
    "company_name": "Edge Case Corp",
    "website": "https://edge.com",
    "employee_count": 50,  # Exactly 50 (must be > 50)
    "linkedin_url": "https://linkedin.com/company/edge"
}

slot_rows = [
    {"slot_type": "CEO", "is_filled": True},
    {"slot_type": "CFO", "is_filled": True},
    {"slot_type": "HR", "is_filled": True}
]

result = validate_company(company_row, slot_rows)
```

**Output:**
```python
{
    "valid": False,
    "reason": "Employee count must be greater than 50 (current: 50)",
    "severity": "ERROR",
    "missing_fields": ["employee_count"]
}
```

---

## 🔄 Integration Usage

### Integration 1: Retroactive Validation Script

```python
# File: retro_validate_neon.py

from validator.validation_rules import validate_company

# Load company from Neon
company_row = fetch_company_from_neon(company_id)

# Load slots for this company
slot_rows = fetch_slots_from_neon(company_id)

# Validate
result = validate_company(company_row, slot_rows)

if result['valid']:
    # Update validation_status to 'valid'
    update_validation_status(company_id, 'valid')
else:
    # Route to n8n webhook for Google Sheets
    route_to_n8n("company", company_row, result['reason'], result['missing_fields'])
    update_validation_status(company_id, 'invalid')

# Log to audit
log_to_audit("retro_validator", f"Validated {company_id}: {result['valid']}")
```

### Integration 2: Forward Pipeline

```python
# File: run_live_pipeline.py

from validator.validation_rules import validate_company

for company in intake_companies:
    # Get slots for this company
    slots = get_slots_for_company(company['company_unique_id'])

    # Validate before proceeding
    result = validate_company(company, slots)

    if result['valid']:
        # Proceed to enrichment
        enqueue_for_enrichment(company)
    else:
        # Route to manual review
        logger.warning(f"Company {company['company_name']} failed: {result['reason']}")
        route_to_sheets(company, result)
```

---

## 📋 Database Queries

### Load Company Row

```sql
SELECT
    company_unique_id,
    company_name,
    website,
    employee_count,
    linkedin_url
FROM marketing.company_master
WHERE company_unique_id = '04.04.02.04.30000.001';
```

### Load Slot Rows

```sql
SELECT
    slot_type,
    is_filled,
    person_unique_id,
    filled_at
FROM marketing.company_slots
WHERE company_unique_id = '04.04.02.04.30000.001'
  AND slot_type IN ('CEO', 'CFO', 'HR');
```

### Validate All Companies in State

```python
import psycopg2
from validator.validation_rules import validate_company

conn = psycopg2.connect(os.getenv('NEON_CONNECTION_STRING'))
cursor = conn.cursor(cursor_factory=RealDictCursor)

# Load all WV companies
cursor.execute("""
    SELECT * FROM marketing.company_master
    WHERE state = 'WV'
""")
companies = cursor.fetchall()

for company in companies:
    # Load slots
    cursor.execute("""
        SELECT * FROM marketing.company_slots
        WHERE company_unique_id = %s
          AND slot_type IN ('CEO', 'CFO', 'HR')
    """, (company['company_unique_id'],))

    slots = cursor.fetchall()

    # Validate
    result = validate_company(dict(company), [dict(s) for s in slots])

    print(f"{company['company_name']}: {result['valid']}")
    if not result['valid']:
        print(f"  Reason: {result['reason']}")
        print(f"  Missing: {result['missing_fields']}")
```

---

## ✅ Unit Tests

All tests pass successfully:

**Test 1: Valid Company**
- All fields present, all slots exist
- Result: ✅ valid=True, severity=INFO, reason=None

**Test 2: Invalid Company (Multiple Failures)**
- company_name too short, website missing protocol, employee_count too low, linkedin_url wrong, missing CFO
- Result: ✅ valid=False, returns first failure, lists all missing fields

**Test 3: Invalid Company (No Slots)**
- All fields valid, but no slots at all
- Result: ✅ valid=False, identifies all 3 missing slots

**Test 4: Edge Case (employee_count = 50)**
- All valid except employee_count exactly 50
- Result: ✅ valid=False, correctly requires > 50 (not >= 50)

**Run Tests:**
```bash
python backend/validator/validation_rules.py
```

---

## 🎯 Design Decisions

### 1. Returns First Failure as "reason"
**Why:** Human-readable error messages for manual review
**Alternative:** Could return all failures, but first failure is usually enough

### 2. Accumulates All Missing Fields
**Why:** Comprehensive reporting for debugging and bulk fixes
**Alternative:** Could stop at first failure, but that's less helpful

### 3. Validates Structure Only
**Why:** This is validation phase, not enrichment phase
**Alternative:** Could validate enrichment status, but that's a different concern

### 4. Does NOT Check is_filled
**Why:** Slot presence != slot fill status. Enrichment will fill slots later.
**Alternative:** Could require filled slots, but that conflates validation with enrichment

### 5. Severity Levels
**Why:** CRITICAL for company_name (data quality issue), ERROR for others, INFO for valid
**Alternative:** Could make all ERROR, but distinguishing helps prioritization

---

## 🔗 Related Functions

- **`validate_company_phase1(record, slot_rows)`** - Phase 1 validation with more detailed output
- **`validate_person(record, valid_company_ids)`** - Person validation
- **`CompanyValidator.validate_all(record, state)`** - Basic field validation

---

## 📚 Related Documentation

- **Validation Rules Module:** `backend/validator/validation_rules.py`
- **Retroactive Validation Guide:** `docs/RETROACTIVE_VALIDATION_GUIDE.md`
- **Phase 1 Validation Summary:** `PHASE1_VALIDATION_SUMMARY.md`
- **Production Workflow Guide:** `docs/PRODUCTION_WORKFLOW_GUIDE.md`

---

**Status:** ✅ Production Ready
**Total Changes:** 205 lines added, 43 lines modified
**Commit:** d7b2749
**Branch:** sys/outreach-tools-backend

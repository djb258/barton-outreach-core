# Phase 1 Company Validation - Implementation Summary

**Status:** ✅ Production Ready
**Date:** 2025-11-17
**Commit:** df2fa9c
**Branch:** sys/outreach-tools-backend

---

## 📋 Overview

Phase 1 validation ensures companies meet **structural requirements** and have the **minimum slot infrastructure** before proceeding to enrichment (Phase 2).

**Phase 1 Focus:**
- ✅ Company structure validation (name, website, employee count, LinkedIn URL)
- ✅ Slot presence validation (CEO, CFO, HR slots must exist)
- ❌ Does NOT require slots to be filled (enrichment is Phase 2+)

---

## 🎯 Validation Rules

### Structural Validation

| Field | Rule | Severity | Example Failure |
|-------|------|----------|-----------------|
| `company_unique_id` | Must not be null | CRITICAL | null → Required |
| `company_name` | Must be present and >= 3 chars | CRITICAL/ERROR | "AB" → Too short |
| `website` | Must start with `http://` or `https://` | ERROR | "acme.com" → Missing protocol |
| `website` | Must contain domain (with `.`) | ERROR | "http://acme" → No TLD |
| `employee_count` | Must be > 50 | ERROR | 30 → Below minimum |
| `linkedin_url` | Must include "linkedin.com/company/" | ERROR | "" → Missing |

### Slot Presence Validation

| Slot Type | Requirement | Notes |
|-----------|------------|-------|
| CEO | Must exist | Filled or unfilled OK |
| CFO | Must exist | Filled or unfilled OK |
| HR | Must exist | Filled or unfilled OK |

**Key Point:** Phase 1 checks that the **slot structure exists**, not that slots are filled with actual people. Enrichment (Phase 2) will fill the slots.

---

## 🔧 New API

### Main Validation Function

```python
from validator.validation_rules import validate_company_phase1

# Load company and slots from database
company = {
    "company_unique_id": "04.04.02.04.30000.001",
    "company_name": "Acme Corporation",
    "website": "https://acme.com",
    "employee_count": 250,
    "linkedin_url": "https://linkedin.com/company/acme-corp"
}

# Load slots from marketing.company_slot table
slots = [
    {"slot_type": "CEO", "is_filled": True},
    {"slot_type": "CFO", "is_filled": False},  # Unfilled OK for Phase 1
    {"slot_type": "HR", "is_filled": True}
]

# Validate
result = validate_company_phase1(company, slots)
```

### Return Format

```python
{
    "valid": True/False,
    "reason": "Missing CFO slot; employee_count: Employee count must be greater than 50",
    "required_fields": [
        "company_unique_id",
        "company_name",
        "website",
        "employee_count",
        "linkedin_url"
    ],
    "missing_fields": ["linkedin_url"],
    "failures": [
        {
            "field": "employee_count",
            "rule": "employee_count_minimum",
            "message": "Employee count must be greater than 50 (current: 30)",
            "severity": "error",
            "current_value": "30"
        },
        {
            "field": "company_slots",
            "rule": "slot_cfo_missing",
            "message": "Missing CFO slot (slot must exist, even if unfilled)",
            "severity": "error",
            "current_value": "Existing slots: CEO, HR"
        }
    ],
    "slots_checked": ["CEO", "CFO", "HR"],
    "slots_present": ["CEO", "HR"],
    "phase": "Phase 1 - Structure + Slot Presence"
}
```

---

## 📊 Example Usage

### Example 1: Valid Company (All Checks Pass)

```python
company = {
    "company_unique_id": "04.04.02.04.30000.001",
    "company_name": "Acme Corporation",
    "website": "https://acme.com",
    "employee_count": 250,
    "linkedin_url": "https://linkedin.com/company/acme-corp"
}

slots = [
    {"slot_type": "CEO", "is_filled": True},
    {"slot_type": "CFO", "is_filled": True},
    {"slot_type": "HR", "is_filled": False}  # Unfilled OK
]

result = validate_company_phase1(company, slots)
```

**Result:**
```python
{
    "valid": True,
    "reason": "Valid",
    "required_fields": ["company_unique_id", "company_name", "website", "employee_count", "linkedin_url"],
    "missing_fields": [],
    "failures": [],
    "slots_checked": ["CEO", "CFO", "HR"],
    "slots_present": ["CEO", "CFO", "HR"],
    "phase": "Phase 1 - Structure + Slot Presence"
}
```

### Example 2: Invalid Company (Multiple Failures)

```python
company = {
    "company_unique_id": "04.04.02.04.30000.002",
    "company_name": "Small Corp",
    "website": "https://smallcorp.com",
    "employee_count": 30,  # Too low
    "linkedin_url": ""  # Missing
}

slots = [
    {"slot_type": "CEO", "is_filled": True},
    {"slot_type": "HR", "is_filled": False}
    # CFO slot missing!
]

result = validate_company_phase1(company, slots)
```

**Result:**
```python
{
    "valid": False,
    "reason": "employee_count: Employee count must be greater than 50 (current: 30); linkedin_url: LinkedIn URL is required; company_slots: Missing CFO slot (slot must exist, even if unfilled)",
    "required_fields": ["company_unique_id", "company_name", "website", "employee_count", "linkedin_url"],
    "missing_fields": ["linkedin_url"],
    "failures": [
        {
            "field": "employee_count",
            "rule": "employee_count_minimum",
            "message": "Employee count must be greater than 50 (current: 30)",
            "severity": "error",
            "current_value": "30"
        },
        {
            "field": "linkedin_url",
            "rule": "linkedin_url_required",
            "message": "LinkedIn URL is required",
            "severity": "error",
            "current_value": ""
        },
        {
            "field": "company_slots",
            "rule": "slot_cfo_missing",
            "message": "Missing CFO slot (slot must exist, even if unfilled)",
            "severity": "error",
            "current_value": "Existing slots: CEO, HR"
        }
    ],
    "slots_checked": ["CEO", "CFO", "HR"],
    "slots_present": ["CEO", "HR"],
    "phase": "Phase 1 - Structure + Slot Presence"
}
```

---

## 🔄 Integration Points

### 1. Retroactive Validation (`retro_validate_neon.py`)

```python
# Can be integrated to validate existing companies
from validator.validation_rules import validate_company_phase1

# Load company and slots from Neon
company = fetch_company_from_neon(company_id)
slots = fetch_slots_from_neon(company_id)

# Validate
result = validate_company_phase1(company, slots)

if not result['valid']:
    # Route to n8n webhook
    route_to_n8n("company", company, result['failures'], "WV")
```

### 2. Forward Pipeline (`run_live_pipeline.py`)

```python
# Can be used during intake validation
for company in intake_companies:
    slots = fetch_slots_for_company(company['company_unique_id'])

    result = validate_company_phase1(company, slots)

    if result['valid']:
        # Proceed to Phase 2 (enrichment)
        enqueue_for_enrichment(company)
    else:
        # Route to manual review
        route_to_sheets(company, result)
```

### 3. Enrichment Scoring (Phase 2+)

```python
# Pre-enrichment check
result = validate_company_phase1(company, slots)

if result['valid']:
    # Company ready for enrichment
    enrichment_score = calculate_enrichment_priority(company, slots)
    enqueue_enrichment(company, score=enrichment_score)
else:
    # Fix structure first
    logger.warning(f"Company {company['company_name']} failed Phase 1: {result['reason']}")
```

---

## 📋 Database Query for Slots

**Load slots for a company:**
```sql
SELECT
    slot_type,
    is_filled,
    person_unique_id,
    filled_at,
    last_refreshed_at
FROM marketing.company_slot
WHERE company_unique_id = '04.04.02.04.30000.001'
  AND slot_type IN ('CEO', 'CFO', 'HR');
```

**Find companies missing slots:**
```sql
WITH company_slots AS (
    SELECT
        c.company_unique_id,
        c.company_name,
        STRING_AGG(DISTINCT s.slot_type, ', ') as existing_slots
    FROM marketing.company_master c
    LEFT JOIN marketing.company_slot s ON c.company_unique_id = s.company_unique_id
        AND s.slot_type IN ('CEO', 'CFO', 'HR')
    WHERE c.state = 'WV'
    GROUP BY c.company_unique_id, c.company_name
)
SELECT
    company_unique_id,
    company_name,
    existing_slots,
    CASE
        WHEN existing_slots NOT LIKE '%CEO%' THEN 'Missing CEO'
        WHEN existing_slots NOT LIKE '%CFO%' THEN 'Missing CFO'
        WHEN existing_slots NOT LIKE '%HR%' THEN 'Missing HR'
        ELSE 'All slots present'
    END as status
FROM company_slots
WHERE existing_slots IS NULL
   OR existing_slots NOT LIKE '%CEO%'
   OR existing_slots NOT LIKE '%CFO%'
   OR existing_slots NOT LIKE '%HR%';
```

---

## 🚀 New Methods Added

### CompanyValidator Class

1. **`validate_employee_count(record, minimum=50)`**
   - Updated to support minimum threshold
   - Phase 1 default: > 50 employees
   - Returns: `Optional[ValidationFailure]`

2. **`validate_linkedin_url(record)`**
   - Validates LinkedIn company URL format
   - Must include "linkedin.com/company/"
   - Returns: `Optional[ValidationFailure]`

3. **`validate_company_unique_id(record)`**
   - Validates unique ID is not null
   - CRITICAL severity
   - Returns: `Optional[ValidationFailure]`

4. **`validate_slots_presence(record, slot_rows)`**
   - Validates CEO, CFO, HR slots exist
   - Does NOT check if filled
   - Returns: `List[ValidationFailure]`

5. **`validate_phase1(record, slot_rows)`**
   - Comprehensive Phase 1 validation
   - Runs all structural + slot checks
   - Returns: `(is_valid, failures, validation_result_dict)`

### Convenience Function

**`validate_company_phase1(record, slot_rows)`**
- User-friendly wrapper
- Returns complete validation result dictionary
- Includes all failures, reason codes, and slot information

---

## ✅ Testing

**Test Results:**

```bash
python backend/validator/validation_rules.py
```

**Output:**
```
============================================================
Phase 1 Company Validation Tests:
------------------------------------------------------------
Test Company (Phase 1): Acme Corporation
Valid: True
Reason: Valid
Slots Checked: ['CEO', 'CFO', 'HR']
Slots Present: ['CEO', 'CFO', 'HR']


Invalid Company (Phase 1): Small Corp
Valid: False
Reason: employee_count: Employee count must be greater than 50 (current: 30); linkedin_url: LinkedIn URL is required; company_slots: Missing CFO slot (slot must exist, even if unfilled)
Missing Fields: ['linkedin_url']
Slots Checked: ['CEO', 'CFO', 'HR']
Slots Present: ['CEO', 'HR']
Failures:
  - employee_count: Employee count must be greater than 50 (current: 30)
  - linkedin_url: LinkedIn URL is required
  - company_slots: Missing CFO slot (slot must exist, even if unfilled)
```

---

## 📚 Related Documentation

- **Validation Rules Module:** `backend/validator/validation_rules.py`
- **Retroactive Validation:** `docs/RETROACTIVE_VALIDATION_GUIDE.md`
- **Production Workflow:** `docs/PRODUCTION_WORKFLOW_GUIDE.md`

---

## 🎯 Next Steps (Phase 2+)

1. **Phase 2: Enrichment**
   - Check if slots are **filled** (not just exist)
   - Trigger enrichment for unfilled slots
   - Validate enrichment data quality

2. **Phase 3: Scoring**
   - Calculate enrichment priority score
   - Score based on: company size, industry, slot fill rate
   - Queue high-priority companies first

3. **Phase 4: Validation**
   - Validate enriched data quality
   - Check LinkedIn profile completeness
   - Verify email deliverability

---

**Total Changes:** 289 lines added, 6 lines modified
**Status:** ✅ Production Ready
**Commit:** df2fa9c

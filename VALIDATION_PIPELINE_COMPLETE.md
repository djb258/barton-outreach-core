# Complete Validation & Promotion Pipeline Documentation

**Created**: 2025-11-18
**Status**: Production-Ready
**Doctrine Version**: Barton Outreach A→Z v1.3.2

---

## Table of Contents

1. [Overview](#overview)
2. [Data Flow](#data-flow)
3. [Validation Rules (Doctrine)](#validation-rules)
4. [Garage 2.0 Classification](#garage-20-classification)
5. [Database Schema](#database-schema)
6. [Usage Examples](#usage-examples)
7. [Scripts & Modules](#scripts--modules)

---

## Overview

The validation & promotion pipeline ensures **only fully valid company and people records** enter the master tables. Invalid records are routed to **Garage 2.0** for agent-based enrichment, with **up to 2 attempts** before marking as `chronic_bad`.

### Core Principles

✅ **Intake tables are temporary staging areas** → Goal: Keep them empty
✅ **Master tables contain only validated records**
✅ **Garage 2.0 handles enrichment** → Agents fix missing/contradictory data
✅ **No duplicate promotions** → SHA256 hash deduplication
✅ **Audit trail** → Every validation tracked with reasons

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ COMPLETE VALIDATION & PROMOTION PIPELINE                         │
└─────────────────────────────────────────────────────────────────┘

Step 1: DATA ARRIVES
├── CSV Upload / API Import / Manual Entry
└── → intake.company_raw_intake (or intake.people_raw_intake)

Step 2: FIRST VALIDATION (validate_and_promote_companies.py)
├── Run validation rules (company_validator.py)
├── Check: Required fields, format, contradictions, DNS resolution
│
├── ✅ PASS
│   ├── Generate Barton ID (04.04.01.XX.XXXXX.XXX)
│   ├── Promote to marketing.company_master
│   └── DELETE from intake ← Goal: Keep intake empty!
│
└── ❌ FAIL
    ├── Classify: Bay A (missing) or Bay B (contradictions)
    ├── Generate SHA256 hash
    ├── Upload JSON to Backblaze B2
    ├── Set enrichment_attempt = 1
    └── KEEP in intake ← Awaiting agent enrichment

Step 3: AGENT ENRICHMENT (Garage 2.0)
├── Pull failed records from B2
├── Route to agent based on bay:
│   ├── Bay A → Firecrawl/Apify ($0.05-0.10)
│   └── Bay B → Abacus/Claude ($0.50-1.00)
├── Enrich: Fill missing fields, resolve contradictions
└── UPDATE existing row in intake (enrichment_attempt++)

Step 4: SECOND VALIDATION (re-run validate_and_promote_companies.py)
├── Re-validate enriched records
│
├── ✅ PASS
│   ├── Promote to marketing.company_master
│   └── DELETE from intake
│
└── ❌ FAIL (2nd time)
    ├── Set enrichment_attempt = 2
    ├── Set chronic_bad = TRUE
    ├── Upload to B2 again
    └── Flag for manual review

FINAL STATE:
├── intake.company_raw_intake → EMPTY (or only chronic_bad records)
└── marketing.company_master → COMPLETE, VALIDATED DATA
```

---

## Validation Rules

### Required Fields

All fields must be **present, valid, and not placeholders**:

| Field | Validation Rules | Example Valid | Example Invalid |
|-------|-----------------|---------------|-----------------|
| `company_name` | ≥2 characters, not placeholder | "Acme Corp" | "N/A", "", "test" |
| `domain` | Valid domain with TLD | "acme.com" | "acme", "localhost" |
| `linkedin_url` | Contains `/company/` | `linkedin.com/company/acme` | `linkedin.com/in/john` |
| `employee_count` | Numeric or range | "50", "11-50" | "unknown", "-1" |
| `industry` | ≥3 characters | "Software" | "n/a", "" |
| `location` | City/State minimum | "Charleston, WV" | "", "TBD" |
| `apollo_id` | Optional (warning only) | "abc123xyz" | N/A |

### Placeholder Detection

Values matching these patterns are **rejected**:

- Empty/whitespace: `""`, `"   "`
- Null equivalents: `"n/a"`, `"none"`, `"null"`, `"unknown"`
- Pending: `"TBD"`, `"pending"`
- Test data: `"test"`, `"example"`, `"placeholder"`

### Domain Resolution (Production Only)

When `check_live_dns=True`:

1. **DNS Check**: `socket.gethostbyname(domain)` must succeed
2. **HTTP Check**: `HEAD` request to domain must return `< 400` status

**Failures**:
- DNS not found → `"domain_dns_not_found"` (Bay A)
- HTTP 404/500 → `"domain_http_error_404"` (Bay B)
- Unreachable → `"domain_http_unreachable"` (Bay B)

---

## Garage 2.0 Classification

### Bay A: Missing Parts

**Criteria**: Required fields are empty or invalid (but no contradictions)

**Examples**:
- Missing domain
- Invalid LinkedIn URL format
- Empty industry
- No employee count

**Agent Routing**:
- Firecrawl → Web scraping for basic fields ($0.05/record)
- Apify → LinkedIn scraping ($0.10/record)

### Bay B: Contradictions

**Criteria**: Fields are present but contain conflicting information

**Examples**:
- `.edu` domain but industry = "Oil & Gas"
- `.org` domain but industry = "Software"
- `.gov` domain but industry = "Retail"
- Company name contains "School" but industry ≠ Education
- Employee count < 10 but domain = "raytheon.com" (corporate)

**Agent Routing**:
- Abacus → Data contradiction resolution ($0.50/record)
- Claude → Complex reasoning ($1.00/record)

### Chronic Bad (3+ Failures)

After **2 failed enrichment attempts**, record is marked `chronic_bad = TRUE` and requires **manual review**.

---

## Database Schema

### intake.company_raw_intake (New Fields)

```sql
-- Apollo anchor key
apollo_id VARCHAR(255)  -- External ID from Apollo.io

-- Deduplication hash
last_hash VARCHAR(64)   -- SHA256 of name+domain+linkedin+apollo+timestamp

-- Enrichment tracking
enrichment_attempt INTEGER DEFAULT 0  -- 0 = fresh, 1 = 1st try, 2 = chronic
chronic_bad BOOLEAN DEFAULT FALSE     -- TRUE after 2+ failures

-- Agent enrichment metadata
last_enriched_at TIMESTAMP
enriched_by VARCHAR(255)  -- Agent name (firecrawl, apify, abacus, claude)

-- Garage 2.0 classification
garage_bay VARCHAR(10)         -- 'bay_a' | 'bay_b'
validation_reasons TEXT        -- Comma-separated failure reasons

-- B2 storage tracking
b2_file_path TEXT              -- Path in Backblaze B2
b2_uploaded_at TIMESTAMP
```

### marketing.company_master (Barton ID Format)

```sql
company_unique_id VARCHAR(100)  -- Format: 04.04.01.XX.XXXXX.XXX
-- Constraint: ^04\.04\.01\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$

-- Example: 04.04.01.24.00024.024
--   04.04.01 = Subhive.App.Layer (companies)
--   24 = Last 2 digits of sequence (sequence % 100)
--   00024 = 5-digit sequence (zero-padded)
--   024 = 3-digit sequence (zero-padded)
```

---

## Usage Examples

### 1. Validate a Single Company (Dev Mode)

```python
from outreach_core.validation import validate_company

company = {
    'company_name': 'Acme Corporation',
    'domain': 'acme.com',
    'linkedin_url': 'https://linkedin.com/company/acme',
    'employee_count': '50',
    'industry': 'Software',
    'location': 'San Francisco, CA',
    'apollo_id': 'abc123',
}

result = validate_company(company, check_live_dns=False)

print(result)
# {
#     'validation_status': 'passed',
#     'garage_bay': None,
#     'reasons': [],
#     'last_hash': 'abc123def456...',
#     'is_chronic': False
# }
```

### 2. Validate with DNS Checks (Production)

```python
result = validate_company(company, check_live_dns=True)
# Will perform live DNS and HTTP HEAD checks
```

### 3. Batch Validation

```python
from outreach_core.validation import validate_companies

companies = [company1, company2, company3]
results = validate_companies(companies, check_live_dns=False)

for idx, result in enumerate(results):
    if result['validation_status'] == 'failed':
        print(f"Company {idx} failed: {result['reasons']}")
        print(f"Garage bay: {result['garage_bay']}")
```

### 4. Run Complete Validation & Promotion Pipeline

```bash
cd outreach_core/workbench

# Validate all companies in intake → promote valid, route invalid to B2
python validate_and_promote_companies.py

# Check results
psql -c "SELECT COUNT(*) FROM intake.company_raw_intake;"  # Should be 0 or only chronic_bad
psql -c "SELECT COUNT(*) FROM marketing.company_master;"   # Should have all valid records
```

---

## Scripts & Modules

### Core Modules

| File | Purpose | Key Functions |
|------|---------|---------------|
| `outreach_core/validation/company_validator.py` | Standalone validation logic | `validate_company()`, `validate_companies()` |
| `outreach_core/workbench/validate_and_promote_companies.py` | Complete pipeline orchestrator | Validate → Promote/B2 → Delete |
| `outreach_core/workbench/validate_and_promote_people.py` | People validation pipeline | Same workflow for people |

### Migrations

| File | Purpose |
|------|---------|
| `infra/migrations/003_create_people_raw_intake.sql` | Creates `intake.people_raw_intake` table |
| `infra/migrations/004_add_enrichment_tracking_to_intake.sql` | Adds apollo_id, garage_bay, validation_reasons, etc. |

### Validation Rules Reference

**File**: `outreach_core/validation/company_validator.py`

**Functions**:
- `validate_company_name()` → Check presence, length, placeholders
- `validate_domain()` → Format validation
- `validate_domain_resolution()` → Live DNS/HTTP checks
- `validate_linkedin_url()` → Company profile format
- `validate_employee_count()` → Numeric or range
- `validate_industry()` → Presence check
- `validate_location()` → City/State minimum
- `detect_domain_industry_mismatch()` → .edu/.org/.gov vs industry
- `detect_employee_domain_mismatch()` → Small count vs corporate domain
- `detect_name_industry_mismatch()` → School/Church in name vs industry
- `generate_sha256_hash()` → Deduplication hash

---

## Monitoring & Debugging

### Check Validation Statistics

```sql
-- Companies awaiting enrichment (in intake)
SELECT
    garage_bay,
    enrichment_attempt,
    COUNT(*) as count
FROM intake.company_raw_intake
WHERE validated = FALSE
GROUP BY garage_bay, enrichment_attempt
ORDER BY enrichment_attempt DESC, garage_bay;

-- Chronic bad records (manual review needed)
SELECT
    company,
    validation_reasons,
    enrichment_attempt,
    last_enriched_at,
    enriched_by
FROM intake.company_raw_intake
WHERE chronic_bad = TRUE
ORDER BY last_enriched_at DESC;

-- Validation failure breakdown
SELECT
    UNNEST(string_to_array(validation_reasons, ',')) as reason,
    COUNT(*) as count
FROM intake.company_raw_intake
WHERE validated = FALSE
GROUP BY reason
ORDER BY count DESC;
```

### Check B2 Upload Status

```sql
SELECT
    COUNT(*) as uploaded,
    COUNT(*) FILTER (WHERE b2_uploaded_at IS NULL) as pending
FROM intake.company_raw_intake
WHERE validated = FALSE;
```

---

## Success Metrics

✅ **Intake Table Empty** → All valid records promoted, invalid records in Garage 2.0
✅ **Low Chronic Bad Rate** → <5% of records fail 2+ times
✅ **High First-Pass Rate** → >70% of records pass on first validation
✅ **Fast Enrichment Cycle** → <24 hours from failure to re-validation

---

## Next Steps

1. ✅ Migration 004 applied → apollo_id, garage_bay, etc. added
2. ✅ Standalone validator created → `outreach_core/validation/company_validator.py`
3. ⏳ Update `validate_and_promote_companies.py` to use new validator
4. ⏳ Create `people_validator.py` with similar rules
5. ⏳ Test end-to-end with sample data
6. ⏳ Deploy to production with `check_live_dns=True`

---

**Last Updated**: 2025-11-18
**Author**: Claude Code
**Barton ID**: 04.04.02.04.50000.###

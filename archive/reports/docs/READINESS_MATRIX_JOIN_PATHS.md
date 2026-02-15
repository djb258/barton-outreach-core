# Outreach Readiness Matrix Join Paths

**Generated**: 2026-02-10
**Purpose**: Document the database schema and join paths for building the outreach readiness matrix and downstream export views.

---

## Executive Summary

- **Total Companies**: 95,837 in `outreach.outreach` (operational spine)
- **Sovereign Eligible**: Data mismatch - CL shows 0 PASS, needs investigation
- **Email Method Coverage**: 82,074 (85.6%)
- **DOL Ready**: 64,932 (67.8% have `filing_present = TRUE`)
- **Slot Fill**: 64,298 companies (67.1%) have at least 1 filled slot
- **BIT Scores**: 13,226 companies (13.8%)
- **ZIP Coverage**: 12,915 companies (13.5%) in `outreach.company_target.postal_code`

---

## Core Join Path: OUTREACH_ID

**Universal Join Key**: `outreach_id` (UUID)

All sub-hubs join to the operational spine via this key. **NEVER use domain as a join key**.

```
outreach.outreach (operational spine, PK: outreach_id)
    ├── outreach.company_target (FK: outreach_id) — 100% coverage (95,837)
    ├── outreach.dol (FK: outreach_id) — 72.2% coverage (69,233)
    ├── people.company_slot (FK: outreach_id) — 99.1% coverage (95,004 companies, 285,845 slots)
    ├── outreach.blog (FK: outreach_id) — 99.1% coverage (95,004)
    └── outreach.bit_scores (FK: outreach_id) — 13.8% coverage (13,226)
```

---

## Table Schemas

### 1. outreach.company_target

**Coverage**: 95,837 companies (100% of outreach.outreach)

#### Key Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `outreach_id` | uuid | YES | FK to outreach.outreach |
| `email_method` | varchar | YES | Email pattern (86.4% coverage) |
| `method_type` | varchar | YES | FACT / GUESS / CATCHALL |
| `confidence_score` | numeric | YES | Pattern confidence |
| `is_catchall` | boolean | YES | Catchall flag |
| `postal_code` | varchar | YES | ZIP code (13.5% coverage) |
| `state` | varchar | YES | State code |
| `city` | varchar | YES | City name |
| `country` | varchar | YES | Country code |
| `industry` | varchar | YES | Industry classification |
| `employees` | integer | YES | Employee count |
| `execution_status` | varchar | YES | Execution status |
| `bit_score_snapshot` | integer | YES | Snapshot of BIT score |

**Email Method Readiness**:
- Total: 95,837
- Has `email_method`: 82,074 (85.6%)

---

### 2. outreach.outreach (Operational Spine)

**Coverage**: 95,837 companies (authoritative)

#### Key Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `outreach_id` | uuid | NO | Primary key |
| `sovereign_id` | uuid | NO | FK to CL (but CL mismatch) |
| `domain` | varchar | YES | Company domain (100% coverage) |
| `ein` | varchar | YES | EIN (72.2% coverage) |
| `has_appointment` | boolean | YES | Appointment flag |
| `created_at` | timestamptz | NO | Created timestamp |
| `updated_at` | timestamptz | NO | Updated timestamp |

**Domain Coverage**: 95,837 (100%)
**EIN Coverage**: 69,233 (72.2%)

---

### 3. outreach.dol

**Coverage**: 70,150 companies (73.2% of outreach.outreach)
**DOL Ready**: 64,975 companies (67.8% of total, 92.6% of DOL records have `filing_present = TRUE`)

#### Key Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `outreach_id` | uuid | NO | FK to outreach.outreach |
| `ein` | text | YES | EIN (100% of DOL records) |
| `filing_present` | boolean | YES | Has Form 5500 (92.6% TRUE) |
| `funding_type` | text | YES | pension_only / fully_insured / self_funded (100%) |
| `broker_or_advisor` | text | YES | Broker/advisor name (10% coverage) |
| `carrier` | text | YES | Insurance carrier (14.6% coverage) |
| `renewal_month` | integer | YES | Plan year begin month 1-12 (100%) |
| `outreach_start_month` | integer | YES | 5 months before renewal (100%) |

**DOL Readiness Breakdown**:
- Total DOL records: 70,150
- `filing_present = TRUE`: 64,975 (92.6%)
- Has EIN: 70,150 (100%)
- Has `funding_type`: 70,150 (100%)
- Has `renewal_month`: 70,142 (100%)
- Has `broker_or_advisor`: 6,995 (10%)
- Has `carrier`: 10,233 (14.6%)

**Definition of "DOL Ready"**: `filing_present = TRUE` (indicates Form 5500 filing exists)

---

### 4. people.company_slot

**Coverage**: 95,004 companies (99.1% of outreach.outreach), 285,845 total slots (3 slots per company: CEO, CFO, HR)

#### Key Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `slot_id` | uuid | NO | Primary key |
| `outreach_id` | uuid | NO | FK to outreach.outreach |
| `slot_type` | text | NO | CEO / CFO / HR |
| `person_unique_id` | text | YES | FK to people.people_master |
| `is_filled` | boolean | YES | Slot filled flag |
| `filled_at` | timestamptz | YES | Fill timestamp |
| `slot_phone` | text | YES | Phone number (680 records, 0.2%) |
| `confidence_score` | numeric | YES | Match confidence |
| `source_system` | text | YES | Source system |

**Slot Fill Breakdown**:

| Slot Type | Total | Filled | Fill % | Has Email |
|-----------|-------|--------|--------|-----------|
| CEO | 95,004 | 62,404 | 65.7% | 61,540 |
| CFO | 95,004 | 57,399 | 60.4% | 57,062 |
| HR | 95,004 | 58,240 | 61.3% | 57,764 |
| **TOTAL** | **285,012** | **178,043** | **62.5%** | **176,366** |

**Note**: `company_slot` does NOT have an `email` column. Emails are in `people.people_master` and accessed via `person_unique_id` FK join.

---

### 5. people.people_master

**Coverage**: 182,661 people records (linked to slots via `person_unique_id`)

#### Key Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `unique_id` | text | NO | Primary key (Barton ID: 04.04.02.YY.NNNNNN.NNN) |
| `company_unique_id` | text | NO | FK to company.company_master |
| `company_slot_unique_id` | text | NO | FK to company_slot (legacy?) |
| `first_name` | text | NO | First name |
| `last_name` | text | NO | Last name |
| `full_name` | text | YES | Full name |
| `title` | text | YES | Job title |
| `email` | text | YES | Email address (176,366 filled slots have email) |
| `linkedin_url` | text | YES | LinkedIn profile |
| `work_phone_e164` | text | YES | Work phone E.164 format |
| `email_verified` | boolean | YES | Email verification status |
| `validation_status` | varchar | YES | Validation status |
| `is_decision_maker` | boolean | YES | Decision maker flag |
| `outreach_ready` | boolean | YES | Outreach ready flag |

**Email Coverage in Filled Slots**:
- CEO: 61,540 / 62,404 filled (98.6%)
- CFO: 57,062 / 57,399 filled (99.4%)
- HR: 57,764 / 58,240 filled (99.2%)

---

### 6. outreach.blog

**Coverage**: 95,004 companies (99.1% of outreach.outreach)

#### Key Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `blog_id` | uuid | NO | Primary key |
| `outreach_id` | uuid | NO | FK to outreach.outreach |
| `context_summary` | text | YES | Content summary |
| `source_type` | text | YES | about_page / press_page / blog_page |
| `source_url` | text | YES | URL |
| `about_url` | text | YES | About URL |
| `news_url` | text | YES | News/press URL |
| `extraction_method` | text | YES | Extraction method |
| `last_extracted_at` | timestamptz | YES | Last extraction timestamp |

---

### 7. outreach.bit_scores

**Coverage**: 13,226 companies (13.8% of outreach.outreach)

#### Key Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `outreach_id` | uuid | NO | FK to outreach.outreach |
| `score` | numeric | NO | BIT score (0-100) |
| `score_tier` | varchar | NO | COLD / WARM / HOT / BURNING |
| `signal_count` | integer | NO | Total signals |
| `people_score` | numeric | NO | People sub-score |
| `dol_score` | numeric | NO | DOL sub-score |
| `blog_score` | numeric | NO | Blog sub-score |
| `talent_flow_score` | numeric | NO | Talent flow sub-score |
| `last_signal_at` | timestamptz | YES | Last signal timestamp |
| `last_scored_at` | timestamptz | YES | Last scoring timestamp |

**BIT Score Distribution**:
- COLD (0-24): 13,226 companies (all current scores)
- Note: No WARM/HOT/BURNING bands populated yet

**Authorization Bands** (per ADR-017):

| Band | Score Range | Name | Permitted Actions |
|------|-------------|------|-------------------|
| 0 | 0-9 | SILENT | None |
| 1 | 10-24 | WATCH | Internal flag only |
| 2 | 25-39 | EXPLORATORY | 1 educational message per 60 days |
| 3 | 40-59 | TARGETED | Persona-specific email, 3-touch max |
| 4 | 60-79 | ENGAGED | Phone (warm), 5-touch max |
| 5 | 80+ | DIRECT | Direct contact, meeting request |

---

### 8. cl.company_identity (Authority Registry)

**Coverage**: 102,922 companies (CL authoritative)

#### Key Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `company_unique_id` | uuid | NO | Primary key (CL sovereign ID) |
| `sovereign_company_id` | uuid | YES | Sovereign ID (new column?) |
| `outreach_id` | uuid | YES | FK to outreach.outreach (WRITE-ONCE) |
| `company_name` | text | NO | Company name |
| `company_domain` | text | YES | Domain |
| `linkedin_company_url` | text | YES | LinkedIn URL |
| `eligibility_status` | text | YES | ELIGIBLE / NULL |
| `exclusion_reason` | text | YES | Exclusion reason |
| `state_code` | char(2) | YES | State code |

**Eligibility Status Distribution**:
- NULL: 56,339 (54.7%)
- ELIGIBLE: 46,583 (45.3%)
- **CRITICAL**: 0 records with `eligibility_status = 'PASS'` (expected 95,004)

**CL-Outreach Mismatch**:
- CL records with outreach_id: 0 (expected 95,004)
- This suggests either:
  1. CL uses different eligibility_status values (ELIGIBLE vs PASS)
  2. CL-outreach link is broken
  3. Query needs to filter differently

---

## ZIP Code Coverage

**Problem**: Very limited ZIP code coverage across all tables.

### ZIP Coverage by Table

| Table | Column | Coverage | Notes |
|-------|--------|----------|-------|
| `outreach.company_target` | `postal_code` | 12,915 / 95,837 (13.5%) | Most complete in outreach |
| `company.company_master` | `address_zip` | 385 / 74,641 (0.5%) | Minimal coverage |
| `enrichment.hunter_company` | - | No ZIP column | - |

### Other ZIP Tables

- `dol.form_5500.*` - Has multiple ZIP columns (admin, preparer, sponsor) but NOT linked to outreach yet
- `coverage.v_service_agent_coverage_zips` - 668 records, service agent coverage by ZIP
- `reference.us_zip_codes` - Reference table for ZIP lookups

### ZIP Enrichment Options

1. **DOL Form 5500 Bridge**: Extract sponsor ZIP from `dol.form_5500` via EIN match
2. **Hunter Enrichment**: Add ZIP column to enrichment pipeline
3. **Domain Geolocation**: IP geolocation for domain (low accuracy)
4. **Manual Enrichment**: One-time ZIP append via paid service

**Recommendation**: Use DOL Form 5500 as primary ZIP source (70,150 companies with EIN = 73.2% coverage potential).

---

## Sample Join Query: Readiness Matrix

```sql
SELECT
    o.outreach_id,
    o.domain,
    ct.email_method,
    ct.postal_code,
    ct.state,
    ct.city,

    -- DOL Readiness
    d.filing_present AS dol_ready,
    d.renewal_month,
    d.outreach_start_month,
    d.funding_type,

    -- Slot Fill Counts
    COUNT(DISTINCT CASE WHEN cs.slot_type = 'CEO' AND cs.is_filled = TRUE THEN cs.slot_id END) AS ceo_filled,
    COUNT(DISTINCT CASE WHEN cs.slot_type = 'CFO' AND cs.is_filled = TRUE THEN cs.slot_id END) AS cfo_filled,
    COUNT(DISTINCT CASE WHEN cs.slot_type = 'HR' AND cs.is_filled = TRUE THEN cs.slot_id END) AS hr_filled,

    -- Email Availability
    COUNT(DISTINCT CASE WHEN cs.slot_type = 'CEO' AND pm.email IS NOT NULL THEN pm.unique_id END) AS ceo_has_email,
    COUNT(DISTINCT CASE WHEN cs.slot_type = 'CFO' AND pm.email IS NOT NULL THEN pm.unique_id END) AS cfo_has_email,
    COUNT(DISTINCT CASE WHEN cs.slot_type = 'HR' AND pm.email IS NOT NULL THEN pm.unique_id END) AS hr_has_email,

    -- BIT Score
    bs.score AS bit_score,
    bs.score_tier AS bit_tier,

    -- Blog Signals
    b.about_url,
    b.news_url

FROM outreach.outreach o
LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
LEFT JOIN people.company_slot cs ON o.outreach_id = cs.outreach_id
LEFT JOIN people.people_master pm ON cs.person_unique_id = pm.unique_id
LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
LEFT JOIN outreach.bit_scores bs ON o.outreach_id = bs.outreach_id

GROUP BY
    o.outreach_id, o.domain,
    ct.email_method, ct.postal_code, ct.state, ct.city,
    d.filing_present, d.renewal_month, d.outreach_start_month, d.funding_type,
    bs.score, bs.score_tier,
    b.about_url, b.news_url;
```

---

## Readiness Flags

### Email Readiness

```sql
CASE
    WHEN ct.email_method IS NOT NULL THEN TRUE
    ELSE FALSE
END AS email_ready
```

**Coverage**: 82,074 / 95,837 (85.6%)

---

### DOL Readiness

```sql
CASE
    WHEN d.filing_present = TRUE THEN TRUE
    ELSE FALSE
END AS dol_ready
```

**Coverage**: 64,975 / 95,837 (67.8%)

**Additional DOL Signals**:
- `renewal_month` (1-12): 70,142 / 70,150 (100% of DOL records)
- `funding_type`: 70,150 / 70,150 (100% of DOL records)
- `broker_or_advisor`: 6,995 / 70,150 (10%)
- `carrier`: 10,233 / 70,150 (14.6%)

---

### Slot Readiness

**Individual Slot Fill**:
```sql
COUNT(CASE WHEN cs.slot_type = 'CEO' AND cs.is_filled = TRUE THEN 1 END) > 0 AS ceo_ready
COUNT(CASE WHEN cs.slot_type = 'CFO' AND cs.is_filled = TRUE THEN 1 END) > 0 AS cfo_ready
COUNT(CASE WHEN cs.slot_type = 'HR' AND cs.is_filled = TRUE THEN 1 END) > 0 AS hr_ready
```

**Any Slot Filled**:
```sql
COUNT(CASE WHEN cs.is_filled = TRUE THEN 1 END) > 0 AS slot_ready
```

**Coverage**: 64,298 / 95,837 companies (67.1%) have at least 1 filled slot

---

### BIT Readiness

```sql
CASE
    WHEN bs.score_tier IN ('WARM', 'HOT', 'BURNING') THEN TRUE
    ELSE FALSE
END AS bit_ready
```

**Current Coverage**: 13,226 / 95,837 (13.8%) have BIT scores, but ALL are COLD tier (score 5-10)

**Note**: No companies currently meet BIT readiness threshold (score >= 25 for Band 2+)

---

### Overall Outreach Readiness

**Proposed Logic** (strictest):
```sql
CASE
    WHEN ct.email_method IS NOT NULL
     AND d.filing_present = TRUE
     AND (COUNT(CASE WHEN cs.is_filled = TRUE THEN 1 END) > 0)
     AND bs.score >= 25  -- Band 2+ (EXPLORATORY)
    THEN TRUE
    ELSE FALSE
END AS outreach_ready
```

**Current Coverage**: 0 companies (BIT scores all < 25)

**Relaxed Logic** (without BIT requirement):
```sql
CASE
    WHEN ct.email_method IS NOT NULL
     AND d.filing_present = TRUE
     AND (COUNT(CASE WHEN cs.is_filled = TRUE THEN 1 END) > 0)
    THEN TRUE
    ELSE FALSE
END AS outreach_ready_relaxed
```

**Estimated Coverage**: ~40,000-50,000 companies (intersection of email + DOL + slot)

---

## ZIP Enrichment Path

### Option 1: DOL Form 5500 Bridge (RECOMMENDED)

```sql
-- Extract sponsor ZIP from Form 5500
SELECT
    o.outreach_id,
    o.domain,
    o.ein,
    f.spons_dfe_loc_us_zip AS sponsor_zip,
    f.spons_dfe_mail_us_zip AS sponsor_mail_zip
FROM outreach.outreach o
JOIN dol.form_5500 f ON o.ein = f.ein
WHERE o.ein IS NOT NULL;
```

**Potential Coverage**: 69,233 companies (72.2% of outreach.outreach have EIN)

---

### Option 2: Company Master Bridge

```sql
-- Use company_master ZIP via domain match
SELECT
    o.outreach_id,
    o.domain,
    cm.address_zip
FROM outreach.outreach o
JOIN company.company_master cm
    ON LOWER(o.domain) = LOWER(
        REPLACE(REPLACE(REPLACE(cm.website_url, 'http://', ''), 'https://', ''), 'www.', '')
    )
WHERE cm.address_zip IS NOT NULL;
```

**Potential Coverage**: 385 companies (0.5% of company_master has ZIP)

---

## Next Steps

1. **Investigate CL Mismatch**:
   - Why does CL show 0 PASS records?
   - What is the correct `eligibility_status` value?
   - Is `sovereign_company_id` the correct join key?

2. **ZIP Enrichment**:
   - Create DOL Form 5500 bridge to extract sponsor ZIP
   - Add ZIP to `outreach.company_target` from DOL data
   - Consider one-time ZIP append service for remaining companies

3. **Create Readiness Matrix View**:
   - Materialized view with all readiness flags
   - Refresh daily or on-demand
   - Include ZIP from DOL bridge

4. **Create Export Views**:
   - Service agent coverage by state + ZIP
   - Outreach-ready companies by renewal month
   - Slot-ready companies by slot type
   - BIT-authorized companies by band

5. **BIT Scoring**:
   - Investigate why all scores are COLD (5-10)
   - Run BIT scoring pipeline to populate WARM/HOT/BURNING bands
   - Implement movement event tracking

---

## Key Findings

1. **outreach_id is the universal join key** - All sub-hubs use this, not domain
2. **Email coverage is strong** (85.6%) but **BIT coverage is weak** (13.8%)
3. **DOL readiness is good** (67.8%) but **broker/carrier data is sparse** (10-15%)
4. **Slot fills are healthy** (62.5% overall, 67.1% of companies have >=1 filled)
5. **ZIP coverage is poor** (13.5%) - requires enrichment from DOL or paid service
6. **CL-outreach link appears broken** - needs investigation
7. **BIT scores need refresh** - all companies are COLD tier, no authorization bands populated

---

**Last Updated**: 2026-02-10
**Verified Against**: Live Neon database via doppler
**Next Document**: ADR justification for readiness + export views

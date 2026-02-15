# ERD-Based DONE State Verification Report

**Generated**: 2026-02-02
**Source**: Neon PostgreSQL Live Database
**Purpose**: Determine "DONE" criteria for each Outreach sub-hub based on actual schema and data

---

## Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| **CL-Outreach Alignment** | 42,192 = 42,192 | ✓ ALIGNED |
| **Outreach Spine Records** | 42,192 | ✓ |
| **Company Target Coverage** | 41,425 (98.2%) | ✓ |
| **Blog Content Coverage** | 41,425 (98.2%) | ✓ |
| **DOL Coverage** | 16,860 (40.0%) | ⚠ PARTIAL |
| **People Coverage** | 324 (0.8%) | ⚠ MINIMAL |
| **BIT Scores** | 13,226 (31.3%) | ⚠ PARTIAL |

---

## 1. Company Target (outreach.company_target)

### Schema Fields (18 columns)
- **Primary Key**: `target_id` (uuid)
- **Foreign Key**: `outreach_id` (uuid) → outreach.outreach
- **Execution Tracking**: `execution_status`, `imo_completed_at`
- **Email Discovery**: `email_method`, `method_type`, `confidence_score`, `is_catchall`
- **Status**: `outreach_status` (default: 'queued')

### DONE Criteria Analysis

| Metric | Value | Percentage |
|--------|-------|------------|
| **Total Records** | 41,425 | 100% |
| **Records with email_method** | 37,878 | 91.4% |
| **Records with confidence_score** | 37,878 | 91.4% |
| **Records with imo_completed_at** | 38,733 | 93.5% |

### Execution Status Breakdown

| Status | Count | Percentage | DONE? |
|--------|-------|------------|-------|
| **ready** | 37,878 | 91.4% | ✓ YES |
| **pending** | 2,692 | 6.5% | ✗ NO |
| **failed** | 855 | 2.1% | ✗ NO |

### Error Tracking
- **Error Table**: `outreach.company_target_errors`
- **Total Errors**: 4,404 records

### DONE Definition for Company Target
```sql
-- A Company Target record is DONE when:
execution_status = 'ready'
AND email_method IS NOT NULL
AND confidence_score IS NOT NULL
AND imo_completed_at IS NOT NULL

-- Current DONE count: 37,878 / 41,425 = 91.4%
```

---

## 2. People Intelligence (people.company_slot, outreach.people)

### Schema: people.company_slot (11 columns)
- **Primary Key**: `slot_id` (uuid)
- **Foreign Keys**: `outreach_id` (uuid), `company_unique_id` (text)
- **Slot Assignment**: `slot_type` (CEO, CFO, HR, etc.), `person_unique_id`
- **Fill Status**: `is_filled` (boolean), `filled_at`, `confidence_score`

### Slot Fill Status

| Status | Count | Percentage |
|--------|-------|------------|
| **Filled** (is_filled = TRUE) | 27,303 | 21.6% |
| **Unfilled** (is_filled = FALSE) | 99,273 | 78.4% |
| **Total Slots** | 126,576 | 100% |

### Schema: outreach.people (20 columns)
- **Primary Key**: `person_id` (uuid)
- **Foreign Keys**: `target_id` (uuid), `outreach_id` (uuid)
- **Email**: `email`, `email_verified`, `email_verified_at`
- **Lifecycle**: `lifecycle_state`, `funnel_membership`, `contact_status`
- **Engagement**: `email_open_count`, `email_click_count`, `email_reply_count`

### People Coverage

| Metric | Value | Note |
|--------|-------|------|
| **Total People Records** | 324 | Only 0.8% of outreach spine |
| **vs Outreach Spine** | 324 / 42,192 | ⚠ MINIMAL COVERAGE |

### DONE Definition for People Intelligence
```sql
-- Option 1: Slot-level DONE (company has required slots filled)
SELECT outreach_id
FROM people.company_slot
WHERE is_filled = TRUE
GROUP BY outreach_id
HAVING COUNT(*) >= 3;  -- e.g., CEO, CFO, HR filled

-- Option 2: Person-level DONE (individual contact ready)
SELECT person_id
FROM outreach.people
WHERE email_verified = TRUE
  AND contact_status != 'bounced';

-- Current state: Very low coverage (324 people for 42K companies)
```

---

## 3. DOL Filings (outreach.dol, dol.form_5500)

### Schema: outreach.dol (9 columns)
- **Primary Key**: `dol_id` (uuid)
- **Foreign Key**: `outreach_id` (uuid)
- **EIN**: `ein` (text) - Employer Identification Number
- **Filing Status**: `filing_present` (boolean)
- **Enrichment**: `funding_type`, `broker_or_advisor`, `carrier`

### DOL Coverage Analysis

| Metric | Value | Percentage |
|--------|-------|------------|
| **Total DOL Records** | 16,860 | 40.0% of spine |
| **Records with EIN** | 16,860 | 100% of DOL records |
| **Records with filing_present = TRUE** | 11,685 | 69.3% of DOL records |
| **vs Outreach Spine** | 16,860 / 42,192 | 40.0% coverage |

### Schema: dol.form_5500
- **Total Form 5500 Filings**: 230,482 records (reference data)

### DONE Definition for DOL Filings
```sql
-- A DOL record is DONE when:
ein IS NOT NULL
AND filing_present = TRUE

-- Current DONE count: 11,685 / 42,192 = 27.7% of total spine
-- Current DOL coverage: 16,860 / 42,192 = 40.0% attempted
```

---

## 4. Blog Content (outreach.blog)

### Schema: outreach.blog (8 columns)
- **Primary Key**: `blog_id` (uuid)
- **Foreign Key**: `outreach_id` (uuid) - NOT NULL
- **Content**: `context_summary`, `source_type`, `source_url`
- **Timestamp**: `context_timestamp`, `created_at`

### Blog Coverage

| Metric | Value | Percentage |
|--------|-------|------------|
| **Total Blog Records** | 41,425 | 98.2% of spine |
| **vs Outreach Spine** | 41,425 / 42,192 | 98.2% coverage |

### DONE Definition for Blog Content
```sql
-- A Blog record is DONE when:
outreach_id IS NOT NULL  -- Required FK
-- Note: All 41,425 records have outreach_id

-- Current DONE count: 41,425 / 42,192 = 98.2%
```

**Note**: Blog content appears to be auto-generated or default-populated for nearly all companies.

---

## 5. BIT Scores (outreach.bit_scores)

### Schema: outreach.bit_scores (12 columns)
- **Primary Key**: `outreach_id` (uuid) - 1:1 with outreach.outreach
- **Score Components**: `score`, `score_tier`, `signal_count`
- **Sub-scores**: `people_score`, `dol_score`, `blog_score`, `talent_flow_score`
- **Tracking**: `last_signal_at`, `last_scored_at`

### BIT Score Coverage

| Metric | Value | Percentage |
|--------|-------|------------|
| **Total BIT Score Records** | 13,226 | 31.3% of spine |
| **vs Outreach Spine** | 13,226 / 42,192 | 31.3% coverage |

### DONE Definition for BIT Scores
```sql
-- A BIT Score record is DONE when:
outreach_id IS NOT NULL
AND score IS NOT NULL
AND score_tier IS NOT NULL
AND signal_count > 0

-- Current DONE count: 13,226 / 42,192 = 31.3%
```

**Note**: BIT Scores are calculated based on signals from People, DOL, Blog, and Talent Flow sub-hubs.

---

## 6. Outreach Spine (outreach.outreach)

### Schema: outreach.outreach (5 columns)
- **Primary Key**: `outreach_id` (uuid)
- **Foreign Key**: `sovereign_id` (uuid) → cl.company_identity.sovereign_company_id
- **Timestamps**: `created_at`, `updated_at`
- **Domain**: `domain` (varchar) - May be NULL

### Spine Status

| Metric | Value |
|--------|-------|
| **Total Outreach Records** | 42,192 |
| **CL Alignment** | 42,192 = 42,192 ✓ |

**Note**: The outreach.outreach table does NOT have a `status` column. Status tracking is done at the sub-hub level (e.g., `outreach.company_target.execution_status`).

---

## 7. CL Alignment Verification

### Alignment Check

| Registry | Count | Status |
|----------|-------|--------|
| **outreach.outreach** | 42,192 | ✓ |
| **cl.company_identity** (outreach_id NOT NULL) | 42,192 | ✓ ALIGNED |

### Verification Query
```sql
SELECT
  (SELECT COUNT(*) FROM outreach.outreach) as outreach_spine,
  (SELECT COUNT(*) FROM cl.company_identity WHERE outreach_id IS NOT NULL) as cl_with_outreach_id;

-- Result: 42,192 = 42,192 ✓ PERFECT ALIGNMENT
```

---

## DONE State Summary by Sub-Hub

| Sub-Hub | DONE Records | Total | Coverage | DONE Criteria |
|---------|--------------|-------|----------|---------------|
| **Company Target** | 37,878 | 41,425 | 91.4% | execution_status='ready' AND email_method IS NOT NULL |
| **Blog Content** | 41,425 | 42,192 | 98.2% | outreach_id IS NOT NULL (auto-populated) |
| **DOL Filings** | 11,685 | 42,192 | 27.7% | ein IS NOT NULL AND filing_present=TRUE |
| **BIT Scores** | 13,226 | 42,192 | 31.3% | score IS NOT NULL AND signal_count > 0 |
| **People Intelligence** | 27,303 slots filled | 126,576 slots | 21.6% | is_filled=TRUE (slot-level) |
| **People Intelligence** | 324 people | 42,192 companies | 0.8% | email_verified=TRUE (person-level) |

---

## Key Findings

1. **Company Target is primary anchor** - 91.4% completion with email method discovery
2. **Blog Content is nearly universal** - 98.2% coverage, likely auto-generated
3. **DOL Filings are partially complete** - 27.7% with verified filings (40% attempted)
4. **People Intelligence is severely underutilized** - Only 324 people records for 42K companies
5. **BIT Scores require multi-hub signals** - 31.3% coverage, depends on People + DOL + Blog
6. **CL Alignment is perfect** - No orphaned outreach_ids

---

## Recommended DONE Definitions for Production Use

### Tier 1: Marketing-Ready (High Confidence)
```sql
-- Company is marketing-ready when:
SELECT o.outreach_id
FROM outreach.outreach o
JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
WHERE ct.execution_status = 'ready'
  AND ct.email_method IS NOT NULL
  AND ct.confidence_score >= 0.8;  -- High confidence threshold
```

### Tier 2: Enrichment Complete (All Sub-Hubs Pass)
```sql
-- Company has completed all enrichment when:
SELECT o.outreach_id
FROM outreach.outreach o
WHERE EXISTS (SELECT 1 FROM outreach.company_target WHERE outreach_id = o.outreach_id AND execution_status = 'ready')
  AND EXISTS (SELECT 1 FROM outreach.blog WHERE outreach_id = o.outreach_id)
  AND EXISTS (SELECT 1 FROM outreach.dol WHERE outreach_id = o.outreach_id AND filing_present = TRUE)
  AND EXISTS (SELECT 1 FROM outreach.bit_scores WHERE outreach_id = o.outreach_id);
```

### Tier 3: Campaign-Ready (People + Email Verified)
```sql
-- Company is campaign-ready when:
SELECT o.outreach_id
FROM outreach.outreach o
WHERE EXISTS (
  SELECT 1
  FROM people.company_slot cs
  WHERE cs.outreach_id = o.outreach_id
    AND cs.is_filled = TRUE
  GROUP BY cs.outreach_id
  HAVING COUNT(*) >= 3  -- At least 3 filled slots (e.g., CEO, CFO, HR)
);
```

---

## Error Tracking

| Sub-Hub | Error Table | Error Count |
|---------|-------------|-------------|
| **Company Target** | `outreach.company_target_errors` | 4,404 |

**Note**: Other sub-hubs do not have dedicated error tables in the schema.

---

## Data Integrity Notes

1. **Foreign Key Enforcement**: All sub-hub tables properly reference `outreach.outreach.outreach_id`
2. **No Orphaned Records**: CL-Outreach alignment is perfect (42,192 = 42,192)
3. **Status Field Location**: Status tracking is at sub-hub level, not spine level
4. **Email Method Coverage**: 91.4% of companies have discovered email patterns
5. **People Gap**: Significant gap between slot creation (126K) and actual people (324)

---

**Report Generated**: 2026-02-02
**Database**: Neon PostgreSQL (Marketing DB)
**Query Execution**: All queries read-only, no modifications made

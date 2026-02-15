# Slot Filling Investigation Report
**Date**: 2026-02-06
**Status**: READ-ONLY ANALYSIS COMPLETE

---

## Executive Summary

This investigation analyzes unfilled executive slots in `people.company_slot` and matching opportunities from Hunter data in `enrichment.hunter_contact`.

**Key Findings**:
- **107,851 unfilled slots** across CEO/CFO/HR positions
- **583,433 Hunter contacts** available with 385,070 having job titles
- **30,633 Hunter contacts** match CEO/CFO/HR/CTO/CMO/COO patterns
- **6,088 companies** have Hunter contact data linked to `company_unique_id`
- **336,071 Hunter contacts** already linked to `outreach_id`

---

## Current State

### 1. Unfilled Slots in `people.company_slot`

| Slot Type | Unfilled Count |
|-----------|----------------|
| CFO       | 37,840        |
| HR        | 37,013        |
| CEO       | 32,998        |
| **TOTAL** | **107,851**   |

### 2. Hunter Contact Availability (`enrichment.hunter_contact`)

| Metric | Count |
|--------|-------|
| Total Records | 583,433 |
| Distinct Domains | 83,410 |
| Distinct Companies (company_unique_id) | 6,088 |
| With Job Title | 385,070 |
| With Email | 583,433 |
| With Outreach ID | 336,071 |

### 3. Hunter Contacts by Job Title Pattern

| Slot Type | Count | Distinct Companies |
|-----------|-------|--------------------|
| OTHER | 354,437 | 4,686 |
| **CEO** | **11,389** | **739** |
| **HR** | **6,595** | **666** |
| **CFO** | **5,391** | **530** |
| COO | 4,932 | 356 |
| CTO | 1,626 | 153 |
| CMO | 700 | 59 |

---

## Database Schema Analysis

### `people.company_slot` Structure

```sql
Column Name            Data Type                 Nullable
slot_id                uuid                      NO (PK)
outreach_id            uuid                      NO (FK)
company_unique_id      text                      NO (FK)
slot_type              text                      NO (CEO/CFO/HR)
person_unique_id       text                      YES (NULL = unfilled)
is_filled              boolean                   YES
filled_at              timestamp with time zone  YES
confidence_score       numeric                   YES
source_system          text                      YES
created_at             timestamp with time zone  YES
updated_at             timestamp with time zone  YES
```

**Key Linking Column**: `company_unique_id`

### `enrichment.hunter_contact` Structure (Relevant Columns)

```sql
Column Name            Data Type                 Nullable
id                     integer                   NO (PK)
domain                 character varying         NO
company_unique_id      character varying         YES
outreach_id            uuid                      YES
email                  character varying         YES
first_name             character varying         YES
last_name              character varying         YES
job_title              character varying         YES
department             character varying         YES
linkedin_url           character varying         YES
confidence_score       integer                   YES
email_verified         boolean                   YES
data_quality_score     numeric                   YES
seniority_level        character varying         YES
is_decision_maker      boolean                   YES
```

**Key Linking Column**: `company_unique_id`

### `outreach.people` Structure

**NOTE**: `outreach.people` does NOT contain the Hunter data directly. It contains:
- `person_id` (PK)
- `target_id` (FK to unknown target table)
- `company_unique_id`
- `slot_type` (mostly NULL or 'OTHER' - 324 records)
- `email`, `email_verified`
- `contact_status`, `lifecycle_state`, `funnel_membership`
- NO `person_unique_id`, NO `job_title`, NO `first_name`, NO `last_name`

---

## Slot Filling Mechanism

### Correct Join Path

```sql
people.company_slot.company_unique_id = enrichment.hunter_contact.company_unique_id
```

### Matching Criteria by Slot Type

| Slot Type | Job Title Pattern |
|-----------|-------------------|
| CEO | `job_title ILIKE '%chief executive%' OR job_title ILIKE '%CEO%'` |
| CFO | `job_title ILIKE '%chief financial%' OR job_title ILIKE '%CFO%'` |
| HR | `job_title ILIKE '%human resource%' OR job_title ILIKE '%chief people%' OR job_title ILIKE '%CHRO%'` |
| CTO | `job_title ILIKE '%chief technology%' OR job_title ILIKE '%CTO%'` |
| CMO | `job_title ILIKE '%chief marketing%' OR job_title ILIKE '%CMO%'` |
| COO | `job_title ILIKE '%chief operating%' OR job_title ILIKE '%COO%'` |

### Slot Assignment Logic

```sql
UPDATE people.company_slot
SET person_unique_id = <generated_person_unique_id_from_hunter_record>,
    is_filled = true,
    filled_at = NOW(),
    confidence_score = enrichment.hunter_contact.data_quality_score,
    source_system = 'hunter',
    updated_at = NOW()
WHERE company_unique_id = <company_unique_id>
  AND slot_type = <matched_slot_type>
  AND person_unique_id IS NULL;
```

### Data Quality Filters

Before filling slots, apply these filters to Hunter contacts:

1. **Email Verification**: `email_verified = true` (preferred)
2. **Confidence Score**: `confidence_score >= 90` (Hunter's confidence threshold)
3. **Data Quality**: `data_quality_score >= 0.7` (if available)
4. **Decision Maker**: `is_decision_maker = true` (if available)
5. **Company Match**: `company_unique_id IS NOT NULL`

---

## Sample Unfilled Slot

```
Slot ID: 209e79df-a3c3-42cf-aba8-973540a885b4
  Outreach ID: 0d26907e-4566-4a45-8b00-d8b282d05826
  Company ID: 023a8528-f0fd-47af-a380-e248e19e828e
  Slot Type: CEO
  Person ID: None
  Is Filled: False
  Source System: None
  Created: 2026-01-15 20:40:00.532012+00:00
  Updated: 2026-01-15 20:40:00.532012+00:00
```

---

## Potential Match Analysis

### Query to Find Matches

```sql
SELECT
    cs.slot_type,
    COUNT(DISTINCT hc.id) as matching_hunter_contacts,
    COUNT(DISTINCT cs.slot_id) as unfilled_slots_with_matches,
    COUNT(DISTINCT hc.company_unique_id) as distinct_companies_with_matches
FROM people.company_slot cs
INNER JOIN enrichment.hunter_contact hc
    ON cs.company_unique_id = hc.company_unique_id
WHERE cs.person_unique_id IS NULL
  AND hc.email_verified = true
  AND hc.confidence_score >= 90
  AND (
      (cs.slot_type = 'CEO' AND (hc.job_title ILIKE '%chief executive%' OR hc.job_title ILIKE '%CEO%'))
      OR (cs.slot_type = 'CFO' AND (hc.job_title ILIKE '%chief financial%' OR hc.job_title ILIKE '%CFO%'))
      OR (cs.slot_type = 'HR' AND (hc.job_title ILIKE '%human resource%' OR hc.job_title ILIKE '%chief people%' OR hc.job_title ILIKE '%CHRO%'))
  )
GROUP BY cs.slot_type
ORDER BY matching_hunter_contacts DESC;
```

---

## Slot Filling Workflow (Recommended)

### Phase 1: Data Preparation

1. **Generate `person_unique_id`** for each Hunter contact
   - Format: UUID or Barton ID format
   - Store mapping: `hunter_contact.id` → `person_unique_id`

2. **Create staging table** (optional)
   ```sql
   CREATE TABLE people.slot_fill_staging (
       staging_id SERIAL PRIMARY KEY,
       slot_id UUID NOT NULL,
       hunter_contact_id INTEGER NOT NULL,
       person_unique_id TEXT NOT NULL,
       match_score NUMERIC,
       created_at TIMESTAMP DEFAULT NOW()
   );
   ```

### Phase 2: Matching Process

1. **Match by company_unique_id + slot_type + job_title**
2. **Apply quality filters**
3. **Resolve conflicts** (multiple candidates per slot)
   - Prefer `is_decision_maker = true`
   - Prefer higher `confidence_score`
   - Prefer higher `data_quality_score`

### Phase 3: Slot Assignment

1. **Update `people.company_slot`**
   ```sql
   UPDATE people.company_slot
   SET person_unique_id = staging.person_unique_id,
       is_filled = true,
       filled_at = NOW(),
       confidence_score = hc.data_quality_score,
       source_system = 'hunter',
       updated_at = NOW()
   FROM people.slot_fill_staging staging
   INNER JOIN enrichment.hunter_contact hc ON staging.hunter_contact_id = hc.id
   WHERE people.company_slot.slot_id = staging.slot_id;
   ```

2. **Sync to `outreach.people`** (if needed)
   - Create new `person_id` records
   - Link to `target_id` (if applicable)
   - Set `slot_type` correctly (not 'OTHER')

### Phase 4: Validation

1. **Verify slot fill counts**
   ```sql
   SELECT slot_type, COUNT(*) as filled_count
   FROM people.company_slot
   WHERE is_filled = true AND source_system = 'hunter'
   GROUP BY slot_type;
   ```

2. **Audit data quality**
   ```sql
   SELECT slot_type,
          AVG(confidence_score) as avg_confidence,
          COUNT(CASE WHEN confidence_score >= 0.7 THEN 1 END) as high_quality_count
   FROM people.company_slot
   WHERE is_filled = true AND source_system = 'hunter'
   GROUP BY slot_type;
   ```

---

## Important Constraints

1. **No duplicate person assignments**
   - One `person_unique_id` per slot per company
   - Enforce via unique constraint: `(company_unique_id, slot_type, person_unique_id)`

2. **Outreach ID requirement**
   - All slots have `outreach_id` (FK to `outreach.outreach`)
   - Do NOT fill slots without valid `outreach_id`

3. **Company unique_id alignment**
   - Hunter contacts MUST have `company_unique_id` populated
   - Only 6,088 companies currently have this linkage
   - This limits potential matches significantly

4. **Email verification**
   - Prefer `email_verified = true` in Hunter data
   - Validate emails before slot assignment

---

## Risks & Considerations

### Data Quality Risks

1. **Job title ambiguity**: Hunter job titles may not match slot types perfectly
2. **Outdated data**: Hunter contacts may have moved companies or changed roles
3. **Duplicate contacts**: Multiple Hunter records for same person

### Process Risks

1. **Overwriting existing assignments**: Ensure `person_unique_id IS NULL` check
2. **Orphaned slots**: Slots without matching `outreach_id` (2 records found)
3. **Company linkage gaps**: Only 6,088 companies have `company_unique_id` in Hunter data

### Mitigation Strategies

1. **Dry run first**: Test matching logic on sample dataset
2. **Manual review**: Audit high-value matches (CEO/CFO) before bulk assignment
3. **Confidence thresholds**: Start with `confidence_score >= 95` for initial batch
4. **Incremental rollout**: Fill CEO slots first, then CFO, then HR
5. **Rollback plan**: Archive original state before bulk updates

---

## Next Steps

### Option 1: Manual Slot Filling Script

Create a Python script that:
1. Queries unfilled slots
2. Finds matching Hunter contacts
3. Generates `person_unique_id` for each match
4. Updates `people.company_slot` with validation
5. Logs all changes to audit table

### Option 2: Database Procedure

Create a PostgreSQL stored procedure:
```sql
CREATE OR REPLACE FUNCTION fill_slots_from_hunter(
    p_slot_type TEXT DEFAULT NULL,
    p_min_confidence NUMERIC DEFAULT 90,
    p_dry_run BOOLEAN DEFAULT TRUE
)
RETURNS TABLE (
    slots_filled INTEGER,
    companies_affected INTEGER,
    avg_confidence NUMERIC
)
```

### Option 3: ETL Pipeline

Integrate into existing People Intelligence Hub:
- Add Phase 9: "Hunter Slot Fill"
- Leverage existing Neon writer patterns
- Maintain correlation_id for audit trail

---

## Sample Queries for Investigation

### 1. Find CEO matches

```sql
SELECT
    cs.slot_id,
    cs.company_unique_id,
    hc.email,
    hc.first_name,
    hc.last_name,
    hc.job_title,
    hc.confidence_score,
    hc.data_quality_score
FROM people.company_slot cs
INNER JOIN enrichment.hunter_contact hc
    ON cs.company_unique_id = hc.company_unique_id
WHERE cs.slot_type = 'CEO'
  AND cs.person_unique_id IS NULL
  AND hc.email_verified = true
  AND hc.confidence_score >= 90
  AND (hc.job_title ILIKE '%chief executive%' OR hc.job_title ILIKE '%CEO%')
LIMIT 10;
```

### 2. Count potential matches by slot type

```sql
SELECT
    cs.slot_type,
    COUNT(DISTINCT cs.slot_id) as unfilled_slots,
    COUNT(DISTINCT hc.id) as matching_contacts,
    COUNT(DISTINCT cs.company_unique_id) as companies_with_matches
FROM people.company_slot cs
LEFT JOIN enrichment.hunter_contact hc
    ON cs.company_unique_id = hc.company_unique_id
    AND hc.email_verified = true
    AND hc.confidence_score >= 90
    AND (
        (cs.slot_type = 'CEO' AND (hc.job_title ILIKE '%chief executive%' OR hc.job_title ILIKE '%CEO%'))
        OR (cs.slot_type = 'CFO' AND (hc.job_title ILIKE '%chief financial%' OR hc.job_title ILIKE '%CFO%'))
        OR (cs.slot_type = 'HR' AND (hc.job_title ILIKE '%human resource%' OR hc.job_title ILIKE '%chief people%'))
    )
WHERE cs.person_unique_id IS NULL
GROUP BY cs.slot_type;
```

### 3. Check for orphaned slots (no company_unique_id)

```sql
SELECT COUNT(*)
FROM people.company_slot
WHERE person_unique_id IS NULL
  AND company_unique_id IS NULL;
```

---

## Conclusion

The investigation reveals a significant opportunity to fill executive slots using Hunter contact data. The key challenges are:

1. **Company linkage**: Only 6,088 companies (~12% of slots) have `company_unique_id` in Hunter data
2. **Job title matching**: Requires fuzzy matching to handle Hunter's varied job title formats
3. **Data quality**: Need to filter for high-confidence, verified contacts

**Recommendation**: Proceed with a phased approach, starting with high-confidence CEO matches for companies with existing `company_unique_id` linkage, then expand to CFO and HR slots.

---

**Report Generated**: 2026-02-06 15:05:00
**Analyst**: Claude Code (Database Expert)
**Status**: READ-ONLY INVESTIGATION COMPLETE

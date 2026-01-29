# CL Eligibility Enforcement with Outreach Cascade Export

**Status**: ACTIVE
**Authority**: OPERATIONAL
**Version**: 1.0.0
**Change Protocol**: ADR + HUMAN APPROVAL REQUIRED

---

## ROLE

You are a **Commercial Eligibility Enforcement Agent** operating in the **CL (Company Lifecycle) repository**.

Your responsibilities:
1. **Identify non-commercial entities** in `cl.company_identity`
2. **Mark them as INELIGIBLE**
3. **Export affected outreach_ids** for downstream cleanup in barton-outreach-core

**You do NOT clean up Outreach data.** You produce the export that Outreach uses.

---

## TWO-REPOSITORY WORKFLOW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CL REPOSITORY (YOU ARE HERE)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  STEP 1: Query cl.company_identity for non-commercial patterns              │
│  STEP 2: Mark matching records as INELIGIBLE                                 │
│  STEP 3: Export list of affected sovereign_company_ids + outreach_ids       │
│  STEP 4: Provide export to barton-outreach-core                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ EXPORT: ineligible_companies.json
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BARTON-OUTREACH-CORE REPOSITORY                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  STEP 5: Receive export from CL                                              │
│  STEP 6: Cascade cleanup through all sub-hubs (see cascade order below)      │
│  STEP 7: Archive affected records                                            │
│  STEP 8: Verify alignment                                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## DATABASE CONNECTION

```bash
# Via Doppler
doppler run -- python script.py

# Connection string in DATABASE_URL
```

---

## STEP 1: DISCOVERY — Count Non-Commercial Entities

Run this query to see what will be affected:

```sql
-- Count by exclusion category
SELECT
    CASE
        -- Government
        WHEN company_domain LIKE '%.gov' OR company_domain LIKE '%.mil'
            THEN 'GOVERNMENT_ENTITY'

        -- Education
        WHEN company_domain LIKE '%.edu'
            OR LOWER(company_domain) LIKE '%k12%'
            OR LOWER(company_domain) LIKE '%school%'
            OR LOWER(company_name) LIKE '%school district%'
            OR LOWER(company_name) LIKE '%school system%'
            OR LOWER(company_name) LIKE '% isd'
            OR LOWER(company_name) LIKE '%isd %'
            OR LOWER(company_name) LIKE '%college%'
            OR LOWER(company_name) LIKE '%university%'
            OR LOWER(company_name) LIKE '%academy%'
            OR LOWER(company_name) LIKE '%k12%'
            OR LOWER(company_name) LIKE '%k-12%'
            THEN 'EDUCATIONAL_INSTITUTION'

        -- Healthcare
        WHEN LOWER(company_name) LIKE '%hospital%'
            OR LOWER(company_name) LIKE '%medical center%'
            OR LOWER(company_name) LIKE '%health system%'
            THEN 'HEALTHCARE_FACILITY'

        -- Religious
        WHEN LOWER(company_name) LIKE '%church%'
            OR LOWER(company_name) LIKE '%ministry%'
            OR LOWER(company_name) LIKE '%ministries%'
            THEN 'RELIGIOUS_ORGANIZATION'

        -- Insurance carriers
        WHEN LOWER(company_name) LIKE '%insurance company%'
            OR LOWER(company_name) LIKE '%mutual insurance%'
            THEN 'INSURANCE_CARRIER'

        ELSE 'COMMERCIAL'
    END AS category,
    COUNT(*) as count
FROM cl.company_identity
WHERE eligibility_status IS NULL
   OR eligibility_status != 'INELIGIBLE'
GROUP BY 1
ORDER BY 2 DESC;
```

**Expected output:**
```
category                  | count
--------------------------+-------
COMMERCIAL                | ~48000
EDUCATIONAL_INSTITUTION   | ~1500
GOVERNMENT_ENTITY         | ~150
HEALTHCARE_FACILITY       | ~150
RELIGIOUS_ORGANIZATION    | ~70
INSURANCE_CARRIER         | ~15
```

---

## STEP 2: MARK AS INELIGIBLE

```sql
BEGIN;

UPDATE cl.company_identity
SET
    eligibility_status = 'INELIGIBLE',
    exclusion_reason = CASE
        WHEN company_domain LIKE '%.gov' OR company_domain LIKE '%.mil'
            THEN 'GOVERNMENT_ENTITY'
        WHEN company_domain LIKE '%.edu'
            OR LOWER(company_domain) LIKE '%k12%'
            OR LOWER(company_domain) LIKE '%school%'
            OR LOWER(company_name) LIKE '%school district%'
            OR LOWER(company_name) LIKE '%school system%'
            OR LOWER(company_name) LIKE '% isd'
            OR LOWER(company_name) LIKE '%isd %'
            OR LOWER(company_name) LIKE '%college%'
            OR LOWER(company_name) LIKE '%university%'
            OR LOWER(company_name) LIKE '%academy%'
            OR LOWER(company_name) LIKE '%k12%'
            OR LOWER(company_name) LIKE '%k-12%'
            THEN 'EDUCATIONAL_INSTITUTION'
        WHEN LOWER(company_name) LIKE '%hospital%'
            OR LOWER(company_name) LIKE '%medical center%'
            OR LOWER(company_name) LIKE '%health system%'
            THEN 'HEALTHCARE_FACILITY'
        WHEN LOWER(company_name) LIKE '%church%'
            OR LOWER(company_name) LIKE '%ministry%'
            OR LOWER(company_name) LIKE '%ministries%'
            THEN 'RELIGIOUS_ORGANIZATION'
        WHEN LOWER(company_name) LIKE '%insurance company%'
            OR LOWER(company_name) LIKE '%mutual insurance%'
            THEN 'INSURANCE_CARRIER'
    END,
    eligibility_evaluated_at = NOW()
WHERE (
    company_domain LIKE '%.gov'
    OR company_domain LIKE '%.mil'
    OR company_domain LIKE '%.edu'
    OR LOWER(company_domain) LIKE '%k12%'
    OR LOWER(company_domain) LIKE '%school%'
    OR LOWER(company_name) LIKE '%school district%'
    OR LOWER(company_name) LIKE '%school system%'
    OR LOWER(company_name) LIKE '% isd'
    OR LOWER(company_name) LIKE '%isd %'
    OR LOWER(company_name) LIKE '%college%'
    OR LOWER(company_name) LIKE '%university%'
    OR LOWER(company_name) LIKE '%academy%'
    OR LOWER(company_name) LIKE '%k12%'
    OR LOWER(company_name) LIKE '%k-12%'
    OR LOWER(company_name) LIKE '%hospital%'
    OR LOWER(company_name) LIKE '%medical center%'
    OR LOWER(company_name) LIKE '%health system%'
    OR LOWER(company_name) LIKE '%church%'
    OR LOWER(company_name) LIKE '%ministry%'
    OR LOWER(company_name) LIKE '%ministries%'
    OR LOWER(company_name) LIKE '%insurance company%'
    OR LOWER(company_name) LIKE '%mutual insurance%'
)
AND (eligibility_status IS NULL OR eligibility_status != 'INELIGIBLE');

-- Check affected count
SELECT COUNT(*) as records_marked_ineligible
FROM cl.company_identity
WHERE eligibility_status = 'INELIGIBLE';

-- If looks correct:
COMMIT;
```

---

## STEP 3: EXPORT AFFECTED RECORDS FOR OUTREACH CASCADE

**This is the critical export that barton-outreach-core needs.**

```sql
-- Export ineligible companies WITH their outreach_ids
SELECT
    ci.sovereign_company_id,
    ci.outreach_id,
    ci.company_name,
    ci.company_domain,
    ci.exclusion_reason,
    ci.eligibility_evaluated_at
FROM cl.company_identity ci
WHERE ci.eligibility_status = 'INELIGIBLE'
  AND ci.outreach_id IS NOT NULL  -- Only those that have outreach records
ORDER BY ci.exclusion_reason, ci.company_name;
```

**Export as JSON for barton-outreach-core:**

```sql
SELECT json_agg(row_to_json(t))
FROM (
    SELECT
        sovereign_company_id::text,
        outreach_id::text,
        company_name,
        company_domain,
        exclusion_reason
    FROM cl.company_identity
    WHERE eligibility_status = 'INELIGIBLE'
      AND outreach_id IS NOT NULL
) t;
```

**Save this output to: `ineligible_for_outreach_cascade.json`**

---

## STEP 4: SUMMARY REPORT FOR BARTON-OUTREACH-CORE

Produce this report to hand off:

```
================================================================================
CL COMMERCIAL ELIGIBILITY ENFORCEMENT COMPLETE
================================================================================

Execution Date: [DATE]
Executed By: Claude Code (CL Repository)

RECORDS MARKED INELIGIBLE:
─────────────────────────────────────────────────────────────────────────────────
Category                    | CL Records | With outreach_id | Needs Cascade
─────────────────────────────────────────────────────────────────────────────────
GOVERNMENT_ENTITY           | [X]        | [X]              | YES
EDUCATIONAL_INSTITUTION     | [X]        | [X]              | YES
HEALTHCARE_FACILITY         | [X]        | [X]              | YES
RELIGIOUS_ORGANIZATION      | [X]        | [X]              | YES
INSURANCE_CARRIER           | [X]        | [X]              | YES
─────────────────────────────────────────────────────────────────────────────────
TOTAL                       | [X]        | [X]              |
─────────────────────────────────────────────────────────────────────────────────

EXPORT FILE: ineligible_for_outreach_cascade.json
RECORD COUNT: [X] outreach_ids requiring cascade cleanup

================================================================================
ACTION REQUIRED IN BARTON-OUTREACH-CORE
================================================================================

The following outreach_ids must be cascaded through all sub-hubs:

CASCADE ORDER (MUST FOLLOW THIS SEQUENCE):
1. outreach.outreach (spine) - Archive, do not delete
2. outreach.company_target
3. outreach.dol
4. outreach.people
5. outreach.blog
6. outreach.bit_scores
7. outreach.bit_signals
8. outreach.campaigns
9. outreach.sequences
10. outreach.send_log
11. outreach.manual_overrides
12. people.company_slot
13. people.people_master

See: OUTREACH_CASCADE_CLEANUP.prompt.md for execution steps.

================================================================================
```

---

## WHAT BARTON-OUTREACH-CORE NEEDS BACK

**For Claude Code in barton-outreach-core to clean up, it needs:**

### 1. List of outreach_ids to cascade

```json
{
  "ineligible_outreach_ids": [
    "uuid-1",
    "uuid-2",
    "uuid-3"
  ],
  "exclusion_summary": {
    "GOVERNMENT_ENTITY": 45,
    "EDUCATIONAL_INSTITUTION": 1080,
    "HEALTHCARE_FACILITY": 50,
    "RELIGIOUS_ORGANIZATION": 30,
    "INSURANCE_CARRIER": 10
  },
  "total_affected": 1215,
  "generated_at": "2026-01-29T00:00:00Z",
  "generated_by": "CL Commercial Eligibility Enforcer"
}
```

### 2. Cascade cleanup order (barton-outreach-core will execute)

```
OUTREACH CASCADE CLEANUP ORDER
──────────────────────────────

For each outreach_id in the export:

1. ARCHIVE (create _archive tables first):
   - outreach.outreach → outreach.outreach_archive
   - outreach.company_target → outreach.company_target_archive
   - outreach.dol → outreach.dol_archive
   - outreach.people → outreach.people_archive
   - outreach.blog → outreach.blog_archive
   - outreach.bit_scores → outreach.bit_scores_archive
   - people.company_slot → people.company_slot_archive
   - people.people_master → people.people_master_archive

2. DELETE from operational tables (reverse FK order):
   - outreach.send_log (FK: sequence_id)
   - outreach.sequences (FK: campaign_id)
   - outreach.campaigns (FK: outreach_id)
   - outreach.bit_signals (FK: outreach_id)
   - outreach.bit_scores (FK: outreach_id)
   - outreach.blog (FK: outreach_id)
   - outreach.people (FK: outreach_id)
   - outreach.dol (FK: outreach_id)
   - outreach.company_target (FK: outreach_id)
   - people.people_master (FK: company_slot)
   - people.company_slot (FK: outreach_id)
   - outreach.manual_overrides (FK: outreach_id)
   - outreach.outreach (spine - last)

3. CLEAR outreach_id in CL (set to NULL):
   UPDATE cl.company_identity
   SET outreach_id = NULL
   WHERE outreach_id IN (SELECT outreach_id FROM ineligible_export);

4. VERIFY alignment:
   - CL ELIGIBLE count = outreach.outreach count
   - No orphaned records in sub-hubs
```

---

## SQL EXPORT QUERY (COPY-PASTE READY)

Run this in CL to generate the export file:

```sql
\copy (
    SELECT
        sovereign_company_id::text,
        outreach_id::text,
        company_name,
        company_domain,
        exclusion_reason
    FROM cl.company_identity
    WHERE eligibility_status = 'INELIGIBLE'
      AND outreach_id IS NOT NULL
) TO '/tmp/ineligible_for_outreach_cascade.csv' WITH CSV HEADER;
```

Or as JSON:

```sql
\copy (
    SELECT json_agg(row_to_json(t))::text
    FROM (
        SELECT
            sovereign_company_id::text as sovereign_company_id,
            outreach_id::text as outreach_id,
            exclusion_reason
        FROM cl.company_identity
        WHERE eligibility_status = 'INELIGIBLE'
          AND outreach_id IS NOT NULL
    ) t
) TO '/tmp/ineligible_for_outreach_cascade.json';
```

---

## VERIFICATION QUERIES

After CL enforcement, run these to verify:

```sql
-- Verify CL state
SELECT
    eligibility_status,
    COUNT(*) as count,
    COUNT(outreach_id) as with_outreach_id
FROM cl.company_identity
GROUP BY eligibility_status;

-- Expected:
-- ELIGIBLE:   ~50,000 with outreach_id ~48,000
-- INELIGIBLE: ~1,900 with outreach_id ~1,200 (these need cascade)

-- Verify no new INELIGIBLE can get outreach_id
-- (This should be enforced by application logic)
```

---

## HANDOFF CHECKLIST

Before handing off to barton-outreach-core:

- [ ] Discovery query run - counts reviewed
- [ ] INELIGIBLE records marked in cl.company_identity
- [ ] Export generated (CSV or JSON)
- [ ] Export contains: sovereign_company_id, outreach_id, exclusion_reason
- [ ] Summary report produced
- [ ] Export file location communicated

**Hand off the export file and summary to barton-outreach-core Claude Code agent.**

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-29 |
| Last Modified | 2026-01-29 |
| Version | 1.0.0 |
| Status | ACTIVE |
| Authority | OPERATIONAL |
| Related | OUTREACH_CASCADE_CLEANUP.prompt.md (barton-outreach-core) |

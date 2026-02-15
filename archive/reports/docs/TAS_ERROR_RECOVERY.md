# Technical Architecture Specification: Error Recovery

**Repository**: barton-outreach-core
**Version**: 1.0.0
**Generated**: 2026-01-28
**Purpose**: What to check when things fail — NO guessing

---

## Error Recovery Index

| Error Category | Jump To |
|----------------|---------|
| Outreach Init Failures | Section 1 |
| Company Target Failures | Section 2 |
| DOL Matching Failures | Section 3 |
| People/Slot Failures | Section 4 |
| BIT Scoring Failures | Section 5 |
| Database/Connection Failures | Section 6 |

---

## 1. Outreach Init Failures

### Error: "Company not found in CL"

**Symptom**: Cannot find company_unique_id in cl.company_identity

**Check**:
```sql
-- Verify company exists
SELECT * FROM cl.company_identity
WHERE company_unique_id = $id;

-- If not found, check by domain
SELECT * FROM cl.company_identity
WHERE normalized_domain = $domain;

-- Check if archived
SELECT * FROM cl.company_identity_archive
WHERE company_unique_id = $id;
```

**Resolution**:
1. If not in CL → Company must be imported via intake first
2. If archived → Check archive reason, may need restoration
3. If domain mismatch → Update normalized_domain in CL

---

### Error: "Outreach ID already claimed"

**Symptom**: `UPDATE cl.company_identity SET outreach_id = $oid` returns 0 rows

**Check**:
```sql
-- See who claimed it
SELECT outreach_id, outreach_attached_at
FROM cl.company_identity
WHERE company_unique_id = $id;

-- Check outreach spine status
SELECT * FROM outreach.outreach
WHERE outreach_id = (
    SELECT outreach_id FROM cl.company_identity
    WHERE company_unique_id = $id
);
```

**Resolution**:
1. If outreach exists and active → Use existing outreach_id
2. If outreach exists but stale → Check if should be archived
3. This is a WRITE-ONCE column — never overwrite, always use existing

---

### Error: "Company not eligible"

**Symptom**: eligibility_status != 'ELIGIBLE'

**Check**:
```sql
SELECT eligibility_status, exclusion_reason, identity_status, existence_verified
FROM cl.company_identity
WHERE company_unique_id = $id;
```

**Resolution by exclusion_reason**:

| exclusion_reason | Action |
|------------------|--------|
| `EXISTENCE_FAILED` | Re-run existence verification |
| `IDENTITY_PENDING` | Wait for identity resolution to complete |
| `DUPLICATE` | Find canonical company_unique_id |
| `MANUAL_EXCLUSION` | Check manual_overrides, requires human review |
| `BAD_DOMAIN` | Domain is invalid/parked, manual fix needed |
| `COMPETITOR` | Intentionally excluded, do not proceed |

---

## 2. Company Target Failures

### Error: "Domain resolution failed"

**Symptom**: Cannot resolve company domain

**Check**:
```sql
-- Get domain from CL
SELECT company_domain, normalized_domain, domain_status_code
FROM cl.company_identity
WHERE company_unique_id = $id;

-- Check domain errors
SELECT * FROM outreach.company_target_errors
WHERE outreach_id = $oid
ORDER BY created_at DESC LIMIT 5;
```

**Resolution by domain_status_code**:

| Status Code | Meaning | Action |
|-------------|---------|--------|
| 200 | OK | Domain is fine, check other issues |
| 301/302 | Redirect | Update to redirect target |
| 403 | Forbidden | May be blocking bots, try manual |
| 404 | Not Found | Domain parked or dead |
| 500+ | Server Error | Retry later |
| NULL | Not checked | Run domain verification |

---

### Error: "Email pattern not found"

**Symptom**: email_method is NULL after Company Target execution

**Check**:
```sql
-- Check what was attempted
SELECT * FROM outreach.company_target
WHERE outreach_id = $oid;

-- Check errors
SELECT * FROM outreach.company_target_errors
WHERE outreach_id = $oid
AND error_type LIKE '%email%';
```

**Resolution**:
1. If is_catchall = true → Domain accepts all, use any pattern
2. If confidence_score < 0.5 → Pattern uncertain, try verification
3. If method_type = 'NONE' → Manual enrichment required
4. Try alternative patterns: `{first}{last}`, `{f}{last}`, `{first}_{last}`

---

## 3. DOL Matching Failures

### Error: "EIN not found"

**Symptom**: No EIN match for company

**Check**:
```sql
-- Check what DOL has
SELECT * FROM outreach.dol WHERE outreach_id = $oid;

-- Search by company name in DOL
SELECT * FROM dol.form_5500
WHERE sponsor_name ILIKE '%' || $company_name || '%'
ORDER BY plan_year DESC LIMIT 10;

-- Check EIN-URL mappings
SELECT * FROM dol.ein_urls
WHERE company_name ILIKE '%' || $company_name || '%';
```

**Resolution**:
1. If company is small (<100 employees) → May not file Form 5500
2. If name variations → Try alternate spellings, abbreviations
3. If subsidiary → Look up parent company EIN
4. Mark as `form_5500_matched = false`, continue waterfall

---

### Error: "Multiple EIN matches"

**Symptom**: Ambiguous match, multiple EINs found

**Check**:
```sql
-- See all matches
SELECT ein, sponsor_name, plan_year, total_participants
FROM dol.form_5500
WHERE sponsor_name ILIKE '%' || $company_name || '%'
ORDER BY plan_year DESC;
```

**Resolution**:
1. Use most recent plan_year
2. Match by participant count (closer to employee_count_band)
3. Match by state if available
4. If still ambiguous → Flag for manual review

---

### Error: "Schedule A not found"

**Symptom**: form_5500_matched = true but schedule_a_matched = false

**Check**:
```sql
-- Check if Schedule A exists for filing
SELECT * FROM dol.schedule_a
WHERE filing_id = $filing_id;

-- Check filing type
SELECT form_type, is_large_plan
FROM dol.form_5500
WHERE filing_id = $filing_id;
```

**Resolution**:
1. Small plans (Form 5500-SF) may not have Schedule A
2. Some plans self-administer without insurance carriers
3. This is NOT a failure — proceed without Schedule A data

---

## 4. People/Slot Failures

### Error: "No people found for company"

**Symptom**: No records in people.people_master for company

**Check**:
```sql
-- Check people_master
SELECT COUNT(*) FROM people.people_master
WHERE company_unique_id = $company_id;

-- Check if people exist but unlinked
SELECT * FROM people.people_master
WHERE email LIKE '%@' || $domain;

-- Check candidate pool
SELECT * FROM people.people_candidate
WHERE company_unique_id = $company_id;
```

**Resolution**:
1. If no people → Trigger enrichment via paid_enrichment_queue
2. If people exist with domain match → Link to company
3. If candidates exist → Promote to people_master

---

### Error: "Slot already filled"

**Symptom**: Trying to assign person to occupied slot

**Check**:
```sql
-- See current slot assignment
SELECT cs.*, pm.full_name, pm.email
FROM people.company_slot cs
LEFT JOIN people.people_master pm ON pm.unique_id = cs.person_unique_id
WHERE cs.outreach_id = $oid AND cs.slot_type = $slot_type;

-- Check assignment history
SELECT * FROM people.slot_assignment_history
WHERE slot_id = $slot_id
ORDER BY changed_at DESC;
```

**Resolution**:
1. If slot has better person → Keep existing
2. If new person is better → Update slot (logs to history)
3. If need multiple → Use different slot_type or add numbered slots

---

### Error: "Email generation failed"

**Symptom**: Could not generate email for person

**Check**:
```sql
-- Get person details
SELECT * FROM people.people_master WHERE unique_id = $person_id;

-- Get email pattern
SELECT email_method FROM outreach.company_target WHERE outreach_id = $oid;

-- Check people errors
SELECT * FROM outreach.people_errors
WHERE outreach_id = $oid
AND error_message LIKE '%email%';
```

**Resolution**:
1. If first_name or last_name is NULL → Enrichment needed
2. If email_method is NULL → Company Target must complete first
3. If special characters in name → Sanitize before pattern application

---

## 5. BIT Scoring Failures

### Error: "BIT score calculation failed"

**Symptom**: No record in outreach.bit_scores after calculation

**Check**:
```sql
-- Check if all sub-hubs complete
SELECT
    (SELECT COUNT(*) FROM outreach.company_target WHERE outreach_id = $oid) as ct,
    (SELECT COUNT(*) FROM outreach.dol WHERE outreach_id = $oid) as dol,
    (SELECT COUNT(*) FROM outreach.people WHERE outreach_id = $oid) as people,
    (SELECT COUNT(*) FROM outreach.blog WHERE outreach_id = $oid) as blog;

-- Check BIT errors
SELECT * FROM outreach.bit_errors
WHERE outreach_id = $oid
ORDER BY created_at DESC;
```

**Resolution**:
1. If any sub-hub count = 0 → Sub-hub must complete first
2. If all complete → Re-run BIT calculation
3. Check bit_input_history for calculation attempts

---

### Error: "BIT tier mismatch"

**Symptom**: Tier doesn't match expected for score

**Check**:
```sql
SELECT bit_score, bit_tier,
    CASE
        WHEN bit_score >= 80 THEN 'PLATINUM'
        WHEN bit_score >= 60 THEN 'GOLD'
        WHEN bit_score >= 40 THEN 'SILVER'
        WHEN bit_score >= 20 THEN 'BRONZE'
        ELSE 'NONE'
    END as expected_tier
FROM outreach.bit_scores
WHERE outreach_id = $oid;

-- Check for tier override
SELECT * FROM outreach.manual_overrides
WHERE outreach_id = $oid AND override_type = 'TIER_FORCE';
```

**Resolution**:
1. If manual override exists → Tier is intentionally forced
2. If no override → Recalculate tier from score
3. Update with correct tier

---

## 6. Database/Connection Failures

### Error: "Connection refused"

**Check**:
1. Verify Doppler credentials: `doppler run -- env | grep NEON`
2. Check Neon dashboard for database status
3. Verify IP not blocked

**Resolution**:
1. Refresh Doppler token
2. Check Neon compute is active (may be suspended)
3. Retry with exponential backoff

---

### Error: "Transaction deadlock"

**Symptom**: Multiple processes competing for same rows

**Check**:
```sql
-- Check for locks (run in separate connection)
SELECT * FROM pg_locks WHERE NOT granted;
```

**Resolution**:
1. Implement row-level locking: `SELECT ... FOR UPDATE`
2. Use smaller transactions
3. Retry with backoff

---

### Error: "Foreign key violation"

**Symptom**: Insert/update fails due to FK constraint

**Check**:
```sql
-- Identify the constraint
-- Error message will contain constraint name
-- e.g., "violates foreign key constraint fk_outreach_id"

-- Verify parent exists
SELECT * FROM outreach.outreach WHERE outreach_id = $oid;
```

**Resolution**:
1. Ensure parent record exists before child insert
2. For outreach sub-hubs: `outreach.outreach` record must exist first
3. For people: `people.people_master` record must exist before `company_slot`

---

## Error Table Reference

| Sub-Hub | Error Table | Key Columns |
|---------|-------------|-------------|
| Company Target | `outreach.company_target_errors` | outreach_id, error_type, error_message, phase |
| DOL | `outreach.dol_errors` | outreach_id, error_type, error_message, ein |
| People | `outreach.people_errors` | outreach_id, error_type, error_message, slot_type |
| Blog | `outreach.blog_errors` | outreach_id, error_type, error_message, blog_url |
| BIT | `outreach.bit_errors` | outreach_id, error_type, error_message, signal_type |
| General | `outreach.outreach_errors` | outreach_id, error_type, error_message |

---

## Quick Diagnostic Query

Run this to get full error summary for an outreach_id:

```sql
SELECT 'company_target' as source, error_type, error_message, created_at
FROM outreach.company_target_errors WHERE outreach_id = $oid
UNION ALL
SELECT 'dol', error_type, error_message, created_at
FROM outreach.dol_errors WHERE outreach_id = $oid
UNION ALL
SELECT 'people', error_type, error_message, created_at
FROM outreach.people_errors WHERE outreach_id = $oid
UNION ALL
SELECT 'blog', error_type, error_message, created_at
FROM outreach.blog_errors WHERE outreach_id = $oid
UNION ALL
SELECT 'bit', error_type, error_message, created_at
FROM outreach.bit_errors WHERE outreach_id = $oid
ORDER BY created_at DESC
LIMIT 20;
```

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-28 |
| Version | 1.0.0 |
| Author | Claude Code (AI Employee) |

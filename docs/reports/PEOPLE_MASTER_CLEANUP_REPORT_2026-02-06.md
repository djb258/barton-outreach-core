# People Master Cleanup Report

**Date**: 2026-02-06
**Operation**: Invalid records cleanup in `people.people_master`
**Status**: COMPLETED SUCCESSFULLY

---

## Executive Summary

Cleaned up 47,486 invalid orphaned records from `people.people_master` (20.9% reduction).
All records were archived to `people.people_master_archive` before deletion.

**Key Metrics:**
- Initial count: 226,849 records
- Final count: 179,363 records
- Removed: 47,486 records (archived)
- Preserved: 1,559 invalid records (linked to filled slots)

---

## Pre-Cleanup Analysis

### Data Quality Issues

| Issue | Count | Percentage |
|-------|-------|------------|
| Missing email | 49,045 | 21.6% |
| Missing unique_id | 0 | 0% |
| Missing name fields | 0 | 0% |
| Missing company_unique_id | 0 | 0% |
| Multiple critical issues | 0 | 0% |

### Slot Linkage Status

| Status | Count |
|--------|-------|
| Linked to filled slots | 175,945 |
| Linked to unfilled slots | 0 |
| NOT linked to any slot | 50,904 |
| Invalid + linked to filled slots | 1,559 |

---

## Cleanup Strategy

### 1. Safe to Delete (47,486 records)
**Criteria:**
- No slot linkage (orphaned)
- Missing email OR missing company_unique_id OR missing name
- Primarily from `free_extraction` source

**Action:** Archived to `people.people_master_archive` and deleted

**Sample Records:**
```
- 04.04.02.57.113157.157: Lara Glass | Missing email | free_extraction
- 04.04.02.85.113285.285: Amy Beros | Missing email | free_extraction
- 04.04.02.38.113538.538: Vice President | Missing email | free_extraction
```

### 2. Needs Review (0 records)
**Criteria:**
- Linked to unfilled slots
- Invalid data

**Action:** None (no records found)

### 3. Must Preserve (1,561 records)
**Criteria:**
- Linked to FILLED slots
- Missing email or other invalid data

**Action:** PRESERVED - These records are actively assigned and require manual review/fixing

**Sample Records:**
```
- 04.04.02.03.113803.803: Internal Medicine | Slot: CEO | Missing email
- 04.04.02.04.113704.704: Greg Catevenis | Slot: CFO | Missing email
- 04.04.02.24.113224.224: Retail Joe | Slot: CEO | Missing email
```

---

## Cleanup Results

### Records Deleted
- **Orphaned invalid records**: 47,486
- **Unlinked from unfilled slots**: 0
- **Total removed**: 47,486

### Records Preserved
- **Linked to filled slots**: 1,561 (require manual fixing)

### Archive Table
- **Table**: `people.people_master_archive`
- **Total archived**: 47,486
- **Archive reason**: `orphaned_invalid`

---

## Post-Cleanup State

### Final Counts

| Metric | Count |
|--------|-------|
| Total people_master records | 179,363 |
| Records with missing email | 1,559 |
| Records linked to filled slots | 175,945 |
| Records NOT linked to any slot | 3,418 |
| Invalid records linked to filled slots | 1,559 |

### Data Quality Improvement

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Total records | 226,849 | 179,363 | -47,486 (-20.9%) |
| Missing email | 49,045 (21.6%) | 1,559 (0.87%) | -47,486 (-96.8%) |
| Orphaned records | 50,904 | 3,418 | -47,486 (-93.3%) |

---

## Remaining Issues

### 1. Invalid Records in Filled Slots (1,559 records)

**Issue**: People assigned to filled slots but missing email addresses

**Impact**: These are actively used in slot assignments and cannot be deleted without breaking slot linkage

**Recommendation**:
1. Generate emails using company email patterns
2. Enrich via external data providers
3. Manual review and correction
4. Consider creating a data quality task to systematically fix these

**Priority**: MEDIUM - These slots are filled but contacts are not reachable

### 2. Valid Orphaned Records (3,418 records)

**Issue**: Records with valid data but no slot assignments

**Impact**: Wasted storage, potential duplicates

**Recommendation**:
- Review for potential slot assignments
- Consider archiving if not needed for future enrichment
- Check for duplicate contacts that could be merged

**Priority**: LOW - Not affecting operations

---

## Database Schema Changes

### New Archive Table

```sql
CREATE TABLE people.people_master_archive (
    archived_at TIMESTAMP NOT NULL DEFAULT NOW(),
    archive_reason TEXT,
    unique_id TEXT,
    company_unique_id TEXT,
    company_slot_unique_id TEXT,
    first_name TEXT,
    last_name TEXT,
    full_name TEXT,
    title TEXT,
    seniority TEXT,
    department TEXT,
    email TEXT,
    work_phone_e164 TEXT,
    personal_phone_e164 TEXT,
    linkedin_url TEXT,
    twitter_url TEXT,
    facebook_url TEXT,
    bio TEXT,
    skills TEXT[],
    education TEXT,
    certifications TEXT[],
    source_system TEXT,
    source_record_id TEXT,
    promoted_from_intake_at TIMESTAMP,
    promotion_audit_log_id INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    email_verified BOOLEAN,
    message_key_scheduled TEXT,
    email_verification_source TEXT,
    email_verified_at TIMESTAMP,
    validation_status VARCHAR,
    last_verified_at TIMESTAMP,
    last_enrichment_attempt TIMESTAMP,
    is_decision_maker BOOLEAN
);
```

---

## Verification Queries

### Check Archive Integrity
```sql
SELECT archive_reason, COUNT(*) as count
FROM people.people_master_archive
GROUP BY archive_reason;
```

### Identify Remaining Invalid Filled Slots
```sql
SELECT
    pm.unique_id,
    pm.full_name,
    pm.email,
    cs.slot_type,
    cs.company_unique_id
FROM people.people_master pm
INNER JOIN people.company_slot cs ON pm.unique_id = cs.person_unique_id
WHERE cs.is_filled = TRUE
  AND (pm.email IS NULL OR TRIM(pm.email) = '');
```

### Check for Orphaned Valid Records
```sql
SELECT
    pm.unique_id,
    pm.full_name,
    pm.email,
    pm.company_unique_id,
    pm.source_system
FROM people.people_master pm
WHERE NOT EXISTS (
    SELECT 1 FROM people.company_slot cs
    WHERE cs.person_unique_id = pm.unique_id
)
AND pm.email IS NOT NULL
AND TRIM(pm.email) != '';
```

---

## Next Steps

1. **Fix Invalid Filled Slots (1,559 records)**
   - Create task to generate emails for these records
   - Use company email patterns from `outreach.company_target`
   - Verify generated emails

2. **Review Valid Orphaned Records (3,418 records)**
   - Analyze source systems
   - Check for slot assignment opportunities
   - Archive if no longer needed

3. **Establish Data Quality Gates**
   - Prevent insertion of records without emails
   - Add validation to slot assignment process
   - Regular data quality audits

4. **Monitor Archive Table**
   - Set up periodic reviews
   - Consider retention policy (e.g., 90 days)
   - Implement restore procedure if needed

---

## Rollback Procedure

If rollback is required:

```sql
-- Restore archived records
INSERT INTO people.people_master
SELECT
    unique_id, company_unique_id, company_slot_unique_id,
    first_name, last_name, full_name, title, seniority, department,
    email, work_phone_e164, personal_phone_e164,
    linkedin_url, twitter_url, facebook_url, bio,
    skills, education, certifications,
    source_system, source_record_id,
    promoted_from_intake_at, promotion_audit_log_id,
    created_at, updated_at,
    email_verified, message_key_scheduled, email_verification_source,
    email_verified_at, validation_status, last_verified_at,
    last_enrichment_attempt, is_decision_maker
FROM people.people_master_archive
WHERE archive_reason = 'orphaned_invalid';

-- Verify count
SELECT COUNT(*) FROM people.people_master;
```

---

## Script Location

**Script**: `C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\scripts\cleanup_invalid_people.py`

**Usage**:
```bash
# Dry run (analysis only)
doppler run -- python scripts/cleanup_invalid_people.py

# Execute cleanup
doppler run -- python scripts/cleanup_invalid_people.py --execute
```

---

## Approval

**Executed by**: Claude Code (Sonnet 4.5)
**Date**: 2026-02-06
**Operation**: Automated cleanup with dry-run verification

---

## References

- Task #4: Clean up 48,106 invalid people records
- CLAUDE.md: Doctrine compliance (CL Authority Registry)
- Schema: `people.people_master`, `people.company_slot`

---

**Report Generated**: 2026-02-06
**Status**: CLEANUP COMPLETED - 1,559 invalid filled slots require manual review

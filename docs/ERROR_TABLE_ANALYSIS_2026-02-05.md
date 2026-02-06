# Error Table Analysis Report
**Generated**: 2026-02-05
**Database**: Neon PostgreSQL (Marketing DB)
**Purpose**: Comprehensive analysis of error tables and data quality issues across all sub-hubs

---

## Executive Summary

### Current Error Table Population

| Error Table | Record Count | Status |
|-------------|--------------|--------|
| `shq.error_master` | **86,411** | Central error registry |
| `outreach.company_target_errors` | **4,404** | NO_MX domain failures |
| `outreach.dol_errors` | **29,740** | DOL match failures |
| `outreach.people_errors` | **0** | Unused |
| `outreach.blog_errors` | **2** | Upstream failures |
| `people.people_invalid` | **21** | Title pattern mismatches |
| `company.pipeline_errors` | **0** | Unused |
| `intake.quarantine` | **2** | Intake failures |

### Critical Data Quality Issues

| Sub-Hub | Issue Type | Count | Severity |
|---------|-----------|-------|----------|
| **Company Target** | Invalid execution_status | **37,878** | HIGH |
| **Company Target** | Missing company_unique_id | **81,778** | CRITICAL |
| **Company Target** | Missing email_method | **12,930** | HIGH |
| **DOL** | Invalid EIN format | **70,150** | HIGH |
| **People Master** | Missing email | **49,045** | HIGH |
| **People Master** | Unverified email | **192,886** | MEDIUM |
| **Company Slot** | Unfilled slots | **133,519** | MEDIUM |
| **Company Slot** | Low confidence (<0.5) | **180** | LOW |
| **Blog** | Missing about_url | **77,196** | MEDIUM |
| **Blog** | Missing news_url | **80,531** | MEDIUM |
| **Blog** | No URLs at all | **68,370** | HIGH |
| **Outreach Spine** | Missing EIN | **42,138** | MEDIUM |

---

## Error Distribution Analysis

### By Error Type (Top 10)

| Error Type | Severity | Total | Unresolved | Resolved | Agent |
|------------|----------|-------|------------|----------|-------|
| DOL_EIN_MISSING | HARD_FAIL | 51,192 | 51,192 | 0 | DOL_EIN_BACKFILL_V1 |
| NO_MATCH | WARNING | 24,546 | 24,546 | 0 | dol-filings |
| NO_STATE | WARNING | 5,194 | 5,194 | 0 | dol-filings |
| CT-M-NO-MX | HARD_FAIL | 4,404 | 4,404 | 0 | company-target |
| PI-E001 | HARD_FAIL | 1,053 | 1,053 | 0 | people-enrichment |
| DOL_EIN_AMBIGUOUS | HARD_FAIL | 20 | 20 | 0 | DOL_EIN_BACKFILL_V1 |
| BLOG-I-UPSTREAM-FAIL | HARD_FAIL | 2 | 2 | 0 | blog-content |

**Key Insight**: 100% of errors are unresolved. No resolution workflows are active.

### By Agent (Top 5)

| Agent | Total Errors | Unresolved |
|-------|--------------|------------|
| DOL_EIN_BACKFILL_V1 | 51,212 | 51,212 |
| dol-filings | 29,740 | 29,740 |
| company-target | 4,404 | 4,404 |
| people-enrichment | 1,053 | 1,053 |
| blog-content | 2 | 2 |

---

## Error Table Schemas

### 1. shq.error_master (Central Error Registry)

**Purpose**: Hub-wide error tracking with disposition, TTL, and escalation support

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| error_id | uuid | NOT NULL | PK, unique error identifier |
| process_id | varchar | NOT NULL | Process/pipeline identifier |
| agent_id | varchar | NOT NULL | Agent that generated error |
| severity | varchar | NOT NULL | ERROR/WARNING/HARD_FAIL |
| error_type | varchar | NOT NULL | Error classification code |
| message | text | NOT NULL | Human-readable error message |
| company_unique_id | varchar | NULL | Company reference (if applicable) |
| outreach_context_id | varchar | NULL | Outreach context reference |
| air_event_id | varchar | NULL | AirTable event reference |
| context | jsonb | NULL | Additional error context |
| created_at | timestamptz | NOT NULL | Error creation timestamp |
| resolved_at | timestamptz | NULL | Resolution timestamp |
| resolution_type | varchar | NULL | How error was resolved |
| disposition | enum | NULL | IGNORE/RETRY/ESCALATE/PARKED/ARCHIVED |
| archived_at | timestamptz | NULL | Archive timestamp |
| ttl_tier | enum | NULL | SHORT/MEDIUM/LONG retention tier |

**Key Features**:
- Supports disposition workflow (IGNORE → PARKED → ARCHIVED)
- TTL-based retention (SHORT: 7d, MEDIUM: 30d, LONG: 90d)
- Escalation tracking via escalation_level
- JSONB context field for flexible metadata

---

### 2. outreach.company_target_errors

**Purpose**: Company Target sub-hub failures (Phase 1-4)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| error_id | uuid | NOT NULL | PK, unique error identifier |
| outreach_id | uuid | NOT NULL | FK to outreach.outreach |
| pipeline_stage | text | NULL | Stage where error occurred |
| failure_code | text | NULL | Structured failure code (e.g., CT-M-NO-MX) |
| blocking_reason | text | NULL | Human-readable blocking reason |
| severity | text | NULL | blocking/warning/critical |
| retry_allowed | boolean | NULL | Can this error be retried? |
| created_at | timestamptz | NULL | Error creation timestamp |
| imo_stage | text | NULL | IMO stage reference (I/M/O) |
| requeue_attempts | integer | NULL | Number of requeue attempts |
| disposition | text | NULL | PARKED/ARCHIVED/ESCALATED |
| retry_count | integer | NULL | Current retry attempt |
| max_retries | integer | NULL | Maximum retry ceiling |
| parked_at | timestamptz | NULL | When error was parked |
| park_reason | text | NULL | Why error was parked |
| escalation_level | integer | NULL | Current escalation level |
| ttl_tier | text | NULL | Retention tier |
| last_retry_at | timestamptz | NULL | Last retry timestamp |
| retry_exhausted | boolean | NULL | Has retry ceiling been hit? |

**Sample Record**:
```
error_id: 47b8cd05-0ad5-4afa-b4f0-7dfd105cae9b
outreach_id: 1028fcd8-cc6e-4bfb-9b94-48bc06895152
failure_code: CT-M-NO-MX
blocking_reason: No MX for buccosu.com
severity: blocking
retry_allowed: False
disposition: PARKED
park_reason: NO_MX_RECORD - Domain has no valid MX, unfixable by enrichment
```

**Key Issues**:
- All 4,404 errors are CT-M-NO-MX (No MX record found)
- All marked as `retry_allowed: False` (structural failures)
- All in PARKED disposition
- Park reason: "NO_MX_RECORD - Domain has no valid MX, unfixable by enrichment"

**Resolution Recommendation**: These are structural failures. Consider:
1. Archive these records (they will never be resolvable)
2. Update marketing eligibility view to filter out NO_MX companies
3. Document NO_MX as permanent disqualification criterion

---

### 3. outreach.dol_errors

**Purpose**: DOL Filings sub-hub failures (Phase DOL)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| error_id | uuid | NOT NULL | PK, unique error identifier |
| outreach_id | uuid | NOT NULL | FK to outreach.outreach |
| pipeline_stage | text | NULL | Stage where error occurred |
| failure_code | text | NULL | NO_MATCH/NO_STATE/DOL_EIN_MISSING |
| blocking_reason | text | NULL | Human-readable reason |
| severity | text | NULL | WARNING/HARD_FAIL |
| retry_allowed | boolean | NULL | Can this error be retried? |
| created_at | timestamptz | NULL | Error creation timestamp |
| requeue_attempts | integer | NULL | Number of requeue attempts |
| disposition | text | NULL | ARCHIVED/PARKED/RETRY |
| retry_count | integer | NULL | Current retry attempt |
| max_retries | integer | NULL | Maximum retry ceiling |
| archived_at | timestamptz | NULL | Archive timestamp |
| parked_at | timestamptz | NULL | When error was parked |
| parked_by | text | NULL | Agent that parked error |
| park_reason | text | NULL | Parking justification |
| escalation_level | integer | NULL | Current escalation level |
| ttl_tier | text | NULL | Retention tier |
| retry_exhausted | boolean | NULL | Has retry ceiling been hit? |

**Sample Record**:
```
error_id: 27aa00ae-2621-4b25-9944-9cc32799b980
outreach_id: 89e22900-e00f-4754-add3-012e455f72ff
failure_code: NO_MATCH
blocking_reason: No match in PA
severity: WARNING
retry_allowed: True
disposition: ARCHIVED
parked_by: ops_cleanup_agent
park_reason: STRUCTURAL_NO_DOL_MATCH [Phase 1 cleanup]
```

**Distribution**:
- 24,546 NO_MATCH (no DOL filing found in state)
- 5,194 NO_STATE (company has no state information)
- All in ARCHIVED disposition from ops_cleanup_agent

**Resolution Status**: Already cleaned up by ops agent. These are expected structural failures (not all companies have DOL filings).

---

### 4. outreach.blog_errors

**Purpose**: Blog Content sub-hub failures

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| error_id | uuid | NOT NULL | PK, unique error identifier |
| outreach_id | uuid | NOT NULL | FK to outreach.outreach |
| pipeline_stage | text | NULL | Stage where error occurred |
| failure_code | text | NULL | BLOG-I-UPSTREAM-FAIL |
| blocking_reason | text | NULL | Human-readable reason |
| severity | text | NULL | ERROR/WARNING |
| retry_allowed | boolean | NULL | Can this error be retried? |
| created_at | timestamptz | NULL | Error creation timestamp |
| process_id | uuid | NULL | Process identifier |
| requeue_attempts | integer | NULL | Number of requeue attempts |

**Sample Record**:
```
error_id: defaf187-a9b3-4283-8f7f-a9df13cda3ea
outreach_id: 00033c90-5ee0-4c5a-8d03-d7f2208540c7
failure_code: BLOG-I-UPSTREAM-FAIL
blocking_reason: Company Target not PASS (status: NOT_FOUND)
severity: ERROR
retry_allowed: False
```

**Status**: Only 2 errors (same outreach_id). Appears to be waterfall cascade failure from Company Target.

---

### 5. people.people_invalid

**Purpose**: People validation failures (title pattern mismatches, email validation)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | integer | NOT NULL | PK, auto-increment |
| unique_id | text | NOT NULL | People master unique ID |
| full_name | text | NULL | Full name |
| first_name | text | NULL | First name |
| last_name | text | NULL | Last name |
| email | text | NULL | Email address |
| phone | text | NULL | Phone number |
| title | text | NULL | Job title |
| company_name | text | NULL | Company name |
| company_unique_id | text | NULL | Company reference |
| linkedin_url | text | NULL | LinkedIn URL |
| city | text | NULL | City |
| state | text | NULL | State |
| validation_status | varchar | NULL | FAILED/NEEDS_REVIEW |
| reason_code | text | NULL | Primary failure reason |
| validation_errors | array | NULL | List of validation errors |
| validation_warnings | array | NULL | List of warnings |
| failed_at | timestamp | NULL | Failure timestamp |
| reviewed | boolean | NULL | Manual review flag |
| batch_id | text | NULL | Batch identifier |
| source_table | text | NULL | Source table reference |
| created_at | timestamp | NULL | Creation timestamp |
| updated_at | timestamp | NULL | Last update timestamp |
| promoted_to | text | NULL | Promotion destination |
| promoted_at | timestamp | NULL | Promotion timestamp |

**Sample Issues**:
1. **Invalid email patterns**: 5 records with test/invalid emails
2. **Missing name components**: 4 records with incomplete names
3. **Title pattern mismatches**: 17 records with CEO/CFO titles that don't match patterns

**Key Insight**: Most records (17/21) are NEEDS_REVIEW, not FAILED. These are CFO/CEO titles like:
- "Chief Financial Officer"
- "President & Chief Executive Officer"
- "Co-Founder & CEO"
- "Executive Vice President & Chief Financial Officer"

**Issue**: The title pattern matching is TOO STRICT. These are valid executive titles that should map to CFO/CEO slots.

---

## Data Quality Issues by Sub-Hub

### Company Target

| Issue | Count | Severity | Recommended Action |
|-------|-------|----------|-------------------|
| Invalid execution_status | 37,878 | HIGH | Validate against enum, standardize statuses |
| Missing company_unique_id | 81,778 | CRITICAL | Investigate broken FK references |
| Missing email_method | 12,930 | HIGH | Backfill from email pattern discovery |

**Critical Issue**: 81,778 records with NULL company_unique_id is a severe FK violation. This suggests:
1. Records created before CL authority registry was implemented
2. Broken migration or import process
3. Orphaned records after sovereign cleanup

**Recommendation**: Run integrity check against `cl.company_identity` to identify:
- Orphaned outreach_ids (no matching sovereign_id in CL)
- Missing FK constraints
- Archive orphaned records

---

### DOL Filings

| Issue | Count | Severity | Recommended Action |
|-------|-------|----------|-------------------|
| Invalid EIN format | 70,150 | HIGH | Standardize to XX-XXXXXXX format |

**Current Format**: Raw EINs from DOL data (various formats)
**Expected Format**: `^\d{2}-\d{7}$` (e.g., "12-3456789")

**Recommendation**: Create migration to standardize EIN format:
```sql
UPDATE outreach.dol
SET ein = CONCAT(LEFT(REGEXP_REPLACE(ein, '[^0-9]', '', 'g'), 2), '-', RIGHT(REGEXP_REPLACE(ein, '[^0-9]', '', 'g'), 7))
WHERE ein IS NOT NULL
  AND ein !~ '^\d{2}-\d{7}$';
```

---

### People Master

| Issue | Count | Severity | Recommended Action |
|-------|-------|----------|-------------------|
| Missing email | 49,045 | HIGH | Mark as enrichment_required |
| Unverified email | 192,886 | MEDIUM | Queue for email verification |

**Unverified Email Analysis**:
- 192,886 people with `email_verified = false` or `email_verified IS NULL`
- These are candidates for MillionVerifier batch processing
- Should be queued via `marketing.data_enrichment_log`

**Recommendation**: Create enrichment pipeline:
1. Mark missing_email records as `ENRICHMENT_REQUIRED`
2. Queue unverified emails for MillionVerifier
3. Update `email_verified` and `email_verified_at` on completion

---

### Company Slot

| Issue | Count | Severity | Recommended Action |
|-------|-------|----------|-------------------|
| Unfilled slots | 133,519 | MEDIUM | Expected (not all slots filled) |
| Low confidence | 180 | LOW | Review slot assignments |

**Unfilled Slots Breakdown**:
- Total slots: 153,444
- Filled slots: ~20,000 (13%)
- Unfilled: 133,519 (87%)

**Slot Fill Rates by Type**:
- CEO: 27.1% (13,901 filled)
- CFO: 8.6% (4,413 filled)
- HR: 13.7% (7,027 filled)

**Note**: Unfilled slots are EXPECTED. This is not an error condition. Slots represent REQUIREMENTS, not necessarily filled positions.

---

### Blog Content

| Issue | Count | Severity | Recommended Action |
|-------|-------|----------|-------------------|
| Missing about_url | 77,196 | MEDIUM | Acceptable (not all companies have about pages) |
| Missing news_url | 80,531 | MEDIUM | Acceptable (not all companies have news pages) |
| No URLs at all | 68,370 | HIGH | Consider blog_score = 0 |

**Analysis**:
- 68,370 companies have NEITHER about_url NOR news_url
- These contribute 0 to blog_score in BIT calculation
- This is expected for small companies or companies without web presence

**Recommendation**: No action required. Blog signals are optional. Companies without blog content receive blog_score = 0.

---

### Outreach Spine

| Issue | Count | Severity | Recommended Action |
|-------|-------|----------|-------------------|
| Missing EIN | 42,138 | MEDIUM | Acceptable (DOL coverage = 27%) |

**Analysis**:
- 42,138 / 51,148 = 82.4% of companies have no EIN
- DOL filing coverage = 13,829 / 51,148 = 27%
- This is expected (not all companies have DOL filings)

**Recommendation**: No action required. EIN is optional. Companies without EIN contribute 0 to dol_score.

---

## Recommended Actions

### Immediate (Critical)

1. **Investigate company_target.company_unique_id NULL values (81,778 records)**
   - Run FK integrity check against `cl.company_identity`
   - Identify orphaned records
   - Archive or link to correct sovereign_id

2. **Standardize DOL EIN format (70,150 records)**
   - Create migration to convert to XX-XXXXXXX format
   - Update DOL matching logic to handle both formats

3. **Fix people_invalid title pattern matching**
   - Update title patterns to recognize:
     - "Chief Financial Officer" → CFO
     - "Chief Executive Officer" → CEO
     - "President & Chief Executive Officer" → CEO
     - "Co-Founder & CEO" → CEO
   - Reprocess 17 NEEDS_REVIEW records

### Short-Term (High Priority)

1. **Archive company_target_errors NO_MX records (4,404)**
   - These are structural failures (no MX record)
   - Will never be resolvable
   - Update marketing eligibility to filter NO_MX

2. **Fix execution_status invalid values (37,878)**
   - Standardize to: pending/in_progress/completed/failed
   - Update records with invalid statuses

3. **Queue unverified emails for enrichment (192,886)**
   - Create batch enrichment job for MillionVerifier
   - Update email_verified status after verification

### Long-Term (Medium Priority)

1. **Implement error resolution workflows**
   - Currently 0% of errors are resolved
   - Create automated resolution for recoverable errors
   - Implement escalation for blocking errors

2. **Create error governance dashboard**
   - Track error rates by sub-hub
   - Monitor TTL expiration
   - Alert on escalation thresholds

3. **Standardize error table schemas**
   - Create unified error table template
   - Migrate legacy error tables to standard schema
   - Implement consistent disposition workflow

---

## Error Table Usage Patterns

### Active Error Tables

1. **shq.error_master**: Central registry (86,411 records)
   - All errors flow through here
   - Supports disposition/TTL/escalation
   - **KEEP**: This is the authoritative error source

2. **outreach.company_target_errors**: Sub-hub specific (4,404 records)
   - Tracks IMO stage failures
   - Supports retry logic
   - **KEEP**: Sub-hub error detail

3. **outreach.dol_errors**: Sub-hub specific (29,740 records)
   - Tracks DOL matching failures
   - Already cleaned up by ops agent
   - **REVIEW**: Consider archiving ARCHIVED records

### Unused Error Tables

1. **outreach.people_errors**: 0 records
   - **CONSIDER REMOVING**: If people errors go to shq.error_master

2. **company.pipeline_errors**: 0 records
   - **CONSIDER REMOVING**: If pipeline errors go to shq.error_master

### Special Purpose Tables

1. **people.people_invalid**: Title pattern mismatches (21 records)
   - Requires manual review
   - **KEEP**: Manual review queue

2. **intake.quarantine**: Intake failures (2 records)
   - Tracks bad imports
   - **KEEP**: Import quality gate

---

## Appendix: Error Code Reference

### Company Target Error Codes

| Code | Description | Severity | Retry | Count |
|------|-------------|----------|-------|-------|
| CT-M-NO-MX | No MX record for domain | HARD_FAIL | No | 4,404 |

### DOL Error Codes

| Code | Description | Severity | Retry | Count |
|------|-------------|----------|-------|-------|
| DOL_EIN_MISSING | Company has no EIN | HARD_FAIL | No | 51,192 |
| NO_MATCH | No DOL filing found in state | WARNING | Yes | 24,546 |
| NO_STATE | Company has no state | WARNING | Yes | 5,194 |
| DOL_EIN_AMBIGUOUS | Multiple EIN matches | HARD_FAIL | No | 20 |

### People Error Codes

| Code | Description | Severity | Retry | Count |
|------|-------------|----------|-------|-------|
| PI-E001 | People enrichment failure | HARD_FAIL | No | 1,053 |

### Blog Error Codes

| Code | Description | Severity | Retry | Count |
|------|-------------|----------|-------|-------|
| BLOG-I-UPSTREAM-FAIL | Upstream hub failure | HARD_FAIL | No | 2 |

---

## Summary Statistics

- **Total Errors Tracked**: 86,411
- **Total Error Tables**: 9 (8 active, 1 unused)
- **Unresolved Errors**: 86,411 (100%)
- **Resolved Errors**: 0 (0%)
- **Archived Errors**: 29,740 (34.4% of total)
- **Parked Errors**: 4,404 (5.1% of total)
- **Blocking Errors**: 56,649 (65.5% of total)

**Critical Insight**: No error resolution workflows are active. All errors remain unresolved or are manually archived/parked.

---

**End of Report**

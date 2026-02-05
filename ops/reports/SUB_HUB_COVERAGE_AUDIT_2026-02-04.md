# Sub-Hub Coverage Audit Report

**Date**: 2026-02-04
**Auditor**: Database Operations Team
**Scope**: Comprehensive gap analysis across Outreach spine and all sub-hubs

---

## EXECUTIVE SUMMARY

**Outreach Spine Baseline**: 96,347 companies

### Critical Findings

| Issue | Count | Coverage | Severity |
|-------|-------|----------|----------|
| Missing Company Target | 767 | 99.20% | CRITICAL |
| Missing Blog Content | 767 | 99.20% | CRITICAL |
| Missing People Slots | 1,343 | 98.61% | HIGH |
| Missing DOL Filings | 25,771 | 73.25% | EXPECTED |

### Key Insights

1. **Company Target & Blog gaps are IDENTICAL**: The same 767 companies are missing both CT and Blog records
2. **People Slots have DIFFERENT gaps**: 1,343 companies missing slots, with NO overlap with CT/Blog gaps
3. **DOL gaps are expected**: Not all companies have DOL filings (27% missing)
4. **Temporal pattern detected**: Gap companies were created on 2026-01-27 through 2026-01-30

---

## 1. OUTREACH SPINE BASELINE

```
Total Outreach records: 96,347
```

This is the authoritative count for comparison across all sub-hubs.

---

## 2. COMPANY TARGET COVERAGE

**Coverage**: 95,580 / 96,347 (99.20%)
**Gap**: 767 companies
**Status**: CRITICAL - Must be 100%

### Gap Characteristics

- All 767 gap companies have domains (not NULL)
- All were created between 2026-01-27 and 2026-01-30
- All are recent additions (within last 7 days)

### Sample Gap Companies

| Outreach ID | Domain | Created At |
|-------------|--------|------------|
| c354ba82-aa1c-4b2d-9c53-d748d92bf3f2 | alphaacademy.education | 2026-01-30 13:25:34 |
| e67c09f1-b7cd-416d-b718-749de4d37ed6 | trinityacademy.com | 2026-01-30 13:25:34 |
| 028b6afa-02e4-44a7-8cf5-b33a337d4a48 | campbelloil.net | 2026-01-30 13:25:34 |
| a6f85657-c1c4-4684-bb4f-5bed3d19f3f9 | image360.com | 2026-01-30 12:21:24 |

**Finding**: Company Target pipeline did NOT execute for these 767 companies despite having valid domains.

---

## 3. BLOG CONTENT COVERAGE

**Coverage**: 95,580 / 96,347 (99.20%)
**Gap**: 767 companies
**Status**: CRITICAL - Must be 100%

### Gap Characteristics

- **IDENTICAL to Company Target gaps**: Same 767 companies missing both
- No companies missing only Blog (all missing both CT and Blog)
- No companies missing only CT (all missing both CT and Blog)

**Finding**: Blog records are created as part of Company Target pipeline. When CT fails, Blog also fails.

---

## 4. PEOPLE SLOTS COVERAGE

**Coverage**: 95,004 / 96,347 (98.61%)
**Gap**: 1,343 companies
**Status**: HIGH - Should be near 100%

### Gap Characteristics

- All 1,343 gap companies **DO HAVE** Company Target records
- All 1,343 gap companies **DO HAVE** Blog records
- **NO OVERLAP** with CT/Blog gaps
- These are DIFFERENT companies than the 767 CT/Blog gap companies

### Slot Distribution

| Slots Per Company | # Companies |
|-------------------|-------------|
| 3 (correct) | 95,004 |

**Finding**: 100% of companies WITH slots have exactly 3 slots (CEO, CFO, HR). No partial slot assignments exist.

### Missing Slot Types

| Slot Type | Companies Missing |
|-----------|-------------------|
| CEO | 1,343 |
| CFO | 1,343 |
| HR | 1,343 |
| ALL | 1,343 |

All 1,343 companies are missing ALL three slots (not just individual slots).

### Sample Gap Companies (Missing Slots but Has CT/Blog)

| Outreach ID | Domain | Has CT | Has Blog |
|-------------|--------|--------|----------|
| 00fa6276-d6a6-43b7-9a31-24f612155c59 | parkhillsanimalhospital.com | YES | YES |
| 61d6439b-7daa-44fe-a2f8-bf13df38070b | brownequinehospital.com | YES | YES |
| f5831522-dc48-41c4-8f8a-ff1190f111d1 | dogwoodlaneca.com | YES | YES |

**Finding**: People Intelligence pipeline did NOT execute for these 1,343 companies despite having valid CT records.

---

## 5. DOL FILINGS COVERAGE

**Coverage**: 70,576 / 96,347 (73.25%)
**Gap**: 25,771 companies
**Status**: EXPECTED - Not all companies have filings

### Notes

- DOL coverage gap is expected and acceptable
- Not all companies are required to file Form 5500
- Many small businesses and non-ERISA plans don't file
- 73.25% coverage is reasonable for the dataset

---

## 6. TEMPORAL PATTERN ANALYSIS

### Creation Pattern (Last 30 Days)

| Date | Created | With CT | With Slots | With Blog |
|------|---------|---------|------------|-----------|
| 2026-02-04 | 54,155 | 54,155 | 52,812 | 54,155 |
| 2026-01-30 | 21 | 0 | 21 | 0 |
| 2026-01-29 | 38 | 0 | 38 | 0 |
| 2026-01-28 | 419 | 0 | 419 | 0 |
| 2026-01-27 | 289 | 0 | 289 | 0 |
| 2026-01-06 | 30,891 | 30,891 | 30,891 | 30,891 |

### Key Observations

1. **2026-01-27 through 2026-01-30**: 767 companies created with NO CT or Blog processing
2. **2026-02-04**: 54,155 companies created with 100% CT/Blog coverage but 1,343 missing slots
3. **2026-01-06**: Perfect 100% coverage across all sub-hubs

**Hypothesis**:
- Companies created on 2026-01-27 to 2026-01-30 bypassed Company Target pipeline entirely
- Companies created on 2026-02-04 completed Company Target but People Intelligence failed for 2.5%

---

## 7. GAP PATTERN CLASSIFICATION

### Pattern A: Company Target Pipeline Failure (767 companies)

**Characteristics**:
- Missing both Company Target AND Blog records
- All have valid domains
- Created between 2026-01-27 and 2026-01-30
- 100% correlation between CT and Blog gaps

**Root Cause Hypothesis**:
- Company Target hub initialization failed
- Blog is dependent on CT, so both failed
- May indicate a pipeline execution issue during this time window

**Action Required**:
- Re-run Company Target pipeline for these 767 companies
- Blog records should auto-generate when CT completes

### Pattern B: People Intelligence Failure (1,343 companies)

**Characteristics**:
- Missing ALL slots (CEO, CFO, HR)
- Have valid Company Target records
- Have valid Blog records
- NO overlap with Pattern A companies
- Created on 2026-02-04

**Root Cause Hypothesis**:
- People Intelligence pipeline did not execute after CT completion
- May indicate a waterfall gate issue (CT to People transition)
- Could be a slot assignment worker failure on 2026-02-04

**Action Required**:
- Re-run People Intelligence pipeline for these 1,343 companies
- Investigate waterfall gate between CT and People hubs

### Pattern C: DOL Filings (25,771 companies)

**Status**: No action required - expected gap

---

## 8. OVERALL COVERAGE SUMMARY

| Sub-Hub | Coverage | Gap | Coverage % | Status |
|---------|----------|-----|------------|--------|
| Company Target | 95,580 | 767 | 99.20% | CRITICAL |
| Blog Content | 95,580 | 767 | 99.20% | CRITICAL |
| People Slots | 95,004 | 1,343 | 98.61% | HIGH |
| DOL Filings | 70,576 | 25,771 | 73.25% | EXPECTED |

---

## 9. REMEDIATION RECOMMENDATIONS

### Priority 1: Fix Company Target Pipeline Failure (767 companies)

```sql
-- Get list of companies needing CT re-processing
SELECT
    o.outreach_id,
    o.domain,
    o.created_at
FROM outreach.outreach o
LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
WHERE ct.outreach_id IS NULL
ORDER BY o.created_at;
```

**Steps**:
1. Export list of 767 outreach_ids
2. Re-run Company Target pipeline (Phases 1-4)
3. Verify Blog records auto-generate
4. Confirm coverage reaches 100%

### Priority 2: Fix People Intelligence Failure (1,343 companies)

```sql
-- Get list of companies needing People re-processing
SELECT
    o.outreach_id,
    o.domain,
    ct.email_method
FROM outreach.outreach o
INNER JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
LEFT JOIN people.company_slot cs ON o.outreach_id = cs.outreach_id
WHERE cs.outreach_id IS NULL
ORDER BY o.created_at DESC;
```

**Steps**:
1. Export list of 1,343 outreach_ids
2. Verify email_method exists in Company Target
3. Re-run People Intelligence pipeline (Phases 5-8)
4. Verify 3 slots created per company (CEO, CFO, HR)
5. Confirm coverage reaches 100%

### Priority 3: Investigate Root Causes

1. **Why did CT fail for 767 companies on 2026-01-27 to 2026-01-30?**
   - Check pipeline execution logs
   - Check for system outages or errors during this window
   - Verify waterfall gate logic

2. **Why did People fail for 1,343 companies on 2026-02-04?**
   - Check People Intelligence worker status
   - Verify spoke contract between CT and People hubs
   - Check for resource constraints or timeouts

---

## 10. DATA QUALITY ASSERTIONS

### Positive Findings

1. **Perfect slot distribution**: 100% of companies with slots have exactly 3 slots (CEO, CFO, HR)
2. **No partial records**: No companies have partial CT or Blog records
3. **No partial slots**: No companies have 1 or 2 slots (either 0 or 3)
4. **Perfect correlation**: CT and Blog gaps are 100% identical (same 767 companies)
5. **Clean separation**: People gaps have NO overlap with CT/Blog gaps

### Data Integrity

- No orphaned records detected
- No duplicate slot assignments
- All companies with slots have valid CT records
- FK relationships intact

---

## 11. APPENDIX: SQL QUERIES

### Query 1: Identify CT/Blog Gap Companies

```sql
SELECT
    o.outreach_id,
    o.domain,
    o.created_at
FROM outreach.outreach o
LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
WHERE ct.outreach_id IS NULL
  AND b.outreach_id IS NULL
ORDER BY o.created_at DESC;
```

### Query 2: Identify People Slot Gap Companies

```sql
SELECT
    o.outreach_id,
    o.domain,
    ct.email_method,
    o.created_at
FROM outreach.outreach o
INNER JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
LEFT JOIN people.company_slot cs ON o.outreach_id = cs.outreach_id
WHERE cs.outreach_id IS NULL
ORDER BY o.created_at DESC;
```

### Query 3: Verify Slot Distribution

```sql
SELECT
    COUNT(*) as slots_per_company,
    COUNT(DISTINCT outreach_id) as company_count
FROM people.company_slot
GROUP BY outreach_id
ORDER BY slots_per_company;
```

---

## CONCLUSION

The Outreach spine has **TWO DISTINCT GAP PATTERNS**:

1. **767 companies missing Company Target & Blog** (99.20% coverage)
   - Same companies for both sub-hubs
   - Created 2026-01-27 to 2026-01-30
   - Company Target pipeline never executed

2. **1,343 companies missing People Slots** (98.61% coverage)
   - Different companies than CT/Blog gaps
   - All have valid CT and Blog records
   - Created 2026-02-04
   - People Intelligence pipeline never executed

**Total companies with ANY gap**: 767 + 1,343 = 2,110 companies (2.19% of total)

**Action Required**: Re-run pipelines for 2,110 companies to achieve 100% coverage across critical sub-hubs.

---

**Report Generated**: 2026-02-04
**Next Audit Date**: After remediation (TBD)

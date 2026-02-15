# Sub-Hub Coverage Audit - Executive Summary

**Date**: 2026-02-04
**Outreach Spine Baseline**: 96,347 companies
**Overall Coverage**: 97.81% (94,237 companies fully covered)

---

## CRITICAL FINDINGS

### 1. Company Target & Blog Pipeline Failure
- **767 companies (0.80%)** missing both Company Target and Blog records
- **100% correlation** - Same companies missing both sub-hubs
- **Created**: 2026-01-27 through 2026-01-30
- **Status**: CRITICAL - Pipeline never executed
- **Action**: Re-run Company Target pipeline (Phases 1-4)

### 2. People Intelligence Pipeline Failure
- **1,343 companies (1.39%)** missing all People Slots (CEO, CFO, HR)
- **NO overlap** with CT/Blog gaps - Different companies
- **Created**: 2026-02-04
- **Status**: HIGH - Pipeline never executed despite valid CT records
- **Action**: Re-run People Intelligence pipeline (Phases 5-8)

### 3. DOL Filings Coverage
- **25,771 companies (26.75%)** missing DOL records
- **Status**: EXPECTED - Not all companies file Form 5500
- **Action**: None required

---

## COVERAGE METRICS

| Sub-Hub | Records | Coverage | Gap | Status |
|---------|---------|----------|-----|--------|
| **Outreach Spine** | 96,347 | 100.00% | 0 | BASELINE |
| **Company Target** | 95,580 | 99.20% | 767 | CRITICAL |
| **Blog Content** | 95,580 | 99.20% | 767 | CRITICAL |
| **People Slots** | 95,004 | 98.61% | 1,343 | HIGH |
| **DOL Filings** | 70,576 | 73.25% | 25,771 | EXPECTED |

---

## GAP PATTERNS

### Pattern A: CT/Blog Pipeline Failure (767 companies)

**Characteristics**:
- Missing both Company Target AND Blog records
- All have valid domains (100%)
- Created in a 4-day window (2026-01-27 to 2026-01-30)
- Perfect correlation (CT gap = Blog gap)

**Hypothesis**: Company Target hub initialization failed during this time window, causing cascading Blog failure.

**Temporal Distribution**:
- 2026-01-27: 289 companies
- 2026-01-28: 419 companies
- 2026-01-29: 38 companies
- 2026-01-30: 21 companies

### Pattern B: People Intelligence Failure (1,343 companies)

**Characteristics**:
- Missing ALL slots (CEO, CFO, HR) - no partial assignments
- All have valid Company Target records (100%)
- All have valid Blog records (100%)
- Created on single day (2026-02-04)
- Zero overlap with Pattern A

**Hypothesis**: People Intelligence waterfall gate failed after Company Target completion on 2026-02-04.

---

## DATA QUALITY FINDINGS

### Positive Indicators

1. **Perfect slot distribution**: 100% of companies with slots have exactly 3 slots
2. **No orphaned records**: All sub-hub records link back to valid outreach_ids
3. **No partial failures**: Companies either have all records or none (no partial state)
4. **Clean FK relationships**: No integrity violations detected
5. **Perfect correlation**: CT and Blog gaps are identical (same 767 companies)

### Data Integrity Score: 100%

- No duplicate records
- No null outreach_ids in sub-hub tables
- All companies with slots have CT records
- No companies with 1 or 2 slots (atomic failure mode)

---

## REMEDIATION PLAN

### Phase 1: Fix Company Target Pipeline (767 companies)

**Priority**: CRITICAL
**Estimated Time**: 2-4 hours

**Steps**:
1. Load `ct_blog_gaps_20260204_163005.csv` (generated)
2. Re-run Company Target pipeline for 767 outreach_ids
3. Verify Blog records auto-generate (should be automatic)
4. Confirm coverage reaches 100%

**Expected Outcome**: 99.20% → 100.00% coverage for CT and Blog

### Phase 2: Fix People Intelligence Pipeline (1,343 companies)

**Priority**: HIGH
**Estimated Time**: 3-5 hours

**Steps**:
1. Load `people_slot_gaps_20260204_163006.csv` (generated)
2. Verify email_method exists in Company Target records
3. Re-run People Intelligence pipeline for 1,343 outreach_ids
4. Verify 3 slots created per company (CEO, CFO, HR)
5. Confirm coverage reaches 100%

**Expected Outcome**: 98.61% → 100.00% coverage for People Slots

### Phase 3: Investigate Root Causes

**Priority**: MEDIUM
**Estimated Time**: 4-8 hours

**Investigation Questions**:

1. **Why did Company Target fail for 767 companies?**
   - Check pipeline execution logs for 2026-01-27 to 2026-01-30
   - Check for system outages or errors during this window
   - Verify waterfall gate logic
   - Check worker status and resource availability

2. **Why did People Intelligence fail for 1,343 companies?**
   - Check People Intelligence worker status on 2026-02-04
   - Verify spoke contract between CT and People hubs
   - Check for resource constraints or timeouts
   - Verify waterfall transition logic from CT to People

3. **Preventive Measures**:
   - Implement coverage monitoring alerts
   - Add waterfall gate validation
   - Create automated gap detection (daily cron)
   - Improve error logging for pipeline failures

---

## EXPORTED FILES

The following CSV files have been generated for remediation:

1. **ct_blog_gaps_20260204_163005.csv** (767 rows)
   - Companies needing Company Target re-processing
   - Includes: outreach_id, sovereign_id, domain, ein, timestamps

2. **people_slot_gaps_20260204_163006.csv** (1,343 rows)
   - Companies needing People Intelligence re-processing
   - Includes: outreach_id, sovereign_id, domain, email_method, timestamps

3. **combined_gap_report_20260204_163006.csv** (2,110 rows)
   - Comprehensive gap report across all sub-hubs
   - Includes: outreach_id, coverage flags for each sub-hub

**Location**: `C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\ops\gap_exports\`

---

## SQL QUERIES FOR REMEDIATION

### Verify CT Gap Before Re-processing

```sql
SELECT COUNT(*) as remaining_ct_gaps
FROM outreach.outreach o
LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
WHERE ct.outreach_id IS NULL;
```

Expected: 767 (before), 0 (after)

### Verify People Slot Gap Before Re-processing

```sql
SELECT COUNT(*) as remaining_slot_gaps
FROM outreach.outreach o
LEFT JOIN people.company_slot cs ON o.outreach_id = cs.outreach_id
WHERE cs.outreach_id IS NULL;
```

Expected: 1,343 (before), 0 (after)

### Verify Slot Distribution After Re-processing

```sql
SELECT
    slots_per_company,
    COUNT(*) as companies
FROM (
    SELECT outreach_id, COUNT(*) as slots_per_company
    FROM people.company_slot
    GROUP BY outreach_id
) sub
GROUP BY slots_per_company
ORDER BY slots_per_company;
```

Expected: All companies should have exactly 3 slots

---

## TIMELINE

### Detection
- **2026-02-04 16:25:36**: Initial audit run
- **2026-02-04 16:27:40**: Gap investigation completed
- **2026-02-04 16:30:05**: CSV exports generated

### Remediation (Proposed)
- **Phase 1**: Fix CT/Blog gaps (767 companies) - 2-4 hours
- **Phase 2**: Fix People Slots gaps (1,343 companies) - 3-5 hours
- **Phase 3**: Root cause investigation - 4-8 hours

### Verification
- **Post-Remediation**: Re-run audit to confirm 100% coverage
- **Follow-up**: Daily coverage monitoring for 1 week

---

## SUCCESS CRITERIA

### Coverage Targets
- Company Target: 100% (currently 99.20%)
- Blog Content: 100% (currently 99.20%)
- People Slots: 100% (currently 98.61%)
- DOL Filings: No target (filing-dependent)

### Data Quality Targets
- Zero orphaned records
- Zero partial slot assignments
- Perfect FK integrity
- All companies with slots have exactly 3 slots (CEO, CFO, HR)

---

## RECOMMENDATIONS

### Immediate Actions (Next 24 Hours)
1. Re-run Company Target pipeline for 767 companies
2. Re-run People Intelligence pipeline for 1,343 companies
3. Verify 100% coverage achievement

### Short-Term Actions (Next Week)
1. Investigate root causes for both pipeline failures
2. Implement automated coverage monitoring
3. Set up daily gap detection alerts
4. Review waterfall gate logic

### Long-Term Actions (Next Month)
1. Implement pipeline health monitoring
2. Add pre-flight validation checks
3. Create automated remediation workflows
4. Document incident response procedures

---

## CONTACT

**Report Generated By**: Database Operations Team
**Audit Scripts Location**: `C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\ops\`
**Full Report**: `SUB_HUB_COVERAGE_AUDIT_2026-02-04.md`

---

## APPENDIX: KEY METRICS

### Coverage Summary
- **Total Companies**: 96,347
- **Fully Covered**: 94,237 (97.81%)
- **Partial Coverage**: 0 (0.00%)
- **Missing CT/Blog**: 767 (0.80%)
- **Missing Slots Only**: 1,343 (1.39%)
- **Total with ANY Gap**: 2,110 (2.19%)

### Pipeline Health
- **Company Target**: 99.20% success rate
- **People Intelligence**: 98.61% success rate
- **Blog Content**: 99.20% success rate (follows CT)
- **DOL Filings**: 73.25% coverage (expected)

### Temporal Analysis
- **CT/Blog Failures**: 4-day window (2026-01-27 to 2026-01-30)
- **People Failures**: Single day (2026-02-04)
- **Gap Overlap**: 0 companies (distinct failure modes)

---

**END OF SUMMARY REPORT**

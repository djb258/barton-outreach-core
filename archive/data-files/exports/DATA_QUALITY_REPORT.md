# Data Quality Report - EIN Export Analysis

**Report Date**: 2026-02-06
**Analyst**: Database Audit System
**Scope**: Outreach Spine Integrity & CL Authority Alignment

---

## Executive Summary

### Critical Issues Identified

1. **CL Authority Registry Violation**: 52,812 records (55.6% of spine) have DOL data but no CL company_identity registration
2. **Baseline Drift**: Outreach spine has grown 85.7% since v1.0 certification without updated audit
3. **Export Logic Gap**: 917 records discrepancy between aggregate counts and export totals

### Recommended Actions

- **IMMEDIATE**: Investigate CL registration gap for 52,812 DOL records
- **HIGH PRIORITY**: Re-certify outreach spine to establish new v1.1 baseline
- **MEDIUM PRIORITY**: Audit DOL import pipeline to prevent future CL bypass

---

## Detailed Analysis

### 1. Outreach Spine State

| Metric | Count | % of Spine |
|--------|-------|-----------|
| **Total Outreach Records** | 95,004 | 100.0% |
| With DOL Data | 70,150 | 73.8% |
| Without DOL Data | 24,854 | 26.2% |
| With CL Registration | 42,192 | 44.4% |
| Without CL Registration | 52,812 | 55.6% |

### 2. DOL Sub-Hub Coverage

| Metric | Count | % of DOL |
|--------|-------|----------|
| **Total DOL Records** | 70,150 | 100.0% |
| With EIN | 70,150 | 100.0% |
| With CL Match | 17,338 | 24.7% |
| Without CL Match | 52,812 | 75.3% |
| Orphaned (no outreach FK) | 0 | 0.0% |

**Finding**: DOL table has perfect referential integrity with outreach.outreach, but 75.3% lack CL registration.

### 3. CL Authority Registry Compliance

| Status | Count | % of Spine |
|--------|-------|-----------|
| **Compliant** (has CL entry) | 42,192 | 44.4% |
| **Non-Compliant** (missing CL) | 52,812 | 55.6% |

**Doctrine Violation**: CL Parent-Child doctrine requires all outreach records to have CL company_identity registration before sub-hub data collection.

### 4. Export File Breakdown

#### Companies WITH EIN (CL Match) - 17,338 records

**File**: `companies_with_ein_cl_match_part1.csv`

**Data Quality**:
- 100% have company_name (from CL)
- 100% have sovereign_company_id
- 100% have EIN
- 100% have DOL metadata (filing_present, funding_type, etc.)

**Status**: HIGH QUALITY - Fully compliant with doctrine

---

#### Companies WITH EIN (NO CL Match) - 52,812 records

**Files**:
- `companies_with_ein_no_cl_match_part1.csv` (24,000 rows)
- `companies_with_ein_no_cl_match_part2.csv` (24,000 rows)
- `companies_with_ein_no_cl_match_part3.csv` (4,812 rows)

**Data Quality Issues**:
- 0% have company_name (no CL registration)
- 0% have sovereign_company_id (should FK to CL)
- 100% have EIN and DOL metadata
- May have email_method and execution_status from company_target

**Status**: DOCTRINE VIOLATION - Missing CL authority registration

**Root Cause Analysis**:
1. DOL data was imported directly to outreach.dol without CL init
2. outreach.outreach records were created with sovereign_id pointing to non-existent CL entries
3. CL registration step was skipped or failed silently

**Recommended Fix**:
```sql
-- Step 1: Identify orphaned sovereign_ids
SELECT DISTINCT o.sovereign_id
FROM outreach.outreach o
LEFT JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
WHERE ci.sovereign_company_id IS NULL;

-- Step 2: Create CL entries for missing sovereign_ids
-- (Use domain from outreach.outreach as canonical identifier)
INSERT INTO cl.company_identity (sovereign_company_id, company_domain, outreach_id, created_at)
SELECT DISTINCT
    o.sovereign_id,
    o.domain,
    o.outreach_id,
    NOW()
FROM outreach.outreach o
LEFT JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
WHERE ci.sovereign_company_id IS NULL;

-- Step 3: Verify alignment
SELECT
    COUNT(*) FILTER (WHERE ci.sovereign_company_id IS NOT NULL) as with_cl,
    COUNT(*) FILTER (WHERE ci.sovereign_company_id IS NULL) as without_cl
FROM outreach.outreach o
LEFT JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id;
```

---

#### Companies WITHOUT EIN - 25,771 records

**Files**:
- `companies_without_ein_part1.csv` (24,000 rows)
- `companies_without_ein_part2.csv` (1,771 rows)

**Data Quality**:
- Variable company_name coverage (depends on CL registration)
- May have email_method and execution_status
- No DOL metadata (expected)

**Status**: EXPECTED - Records awaiting DOL enrichment

**Note**: The 917 record discrepancy (25,771 exported vs 24,854 actual non-DOL) suggests some records exist in DOL but weren't captured in the "WITH EIN" queries. This is likely due to the LEFT JOIN logic in the export script.

---

## Alignment Matrix

### Spine vs Sub-Hub Alignment

| Sub-Hub | Records | % Coverage | CL Match | % CL Match |
|---------|---------|-----------|----------|-----------|
| **DOL** | 70,150 | 73.8% | 17,338 | 24.7% |
| **Company Target** | TBD | TBD | TBD | TBD |
| **People** | TBD | TBD | TBD | TBD |
| **Blog** | TBD | TBD | TBD | TBD |

### CL vs Outreach Alignment

| Metric | Count | Status |
|--------|-------|--------|
| CL records with outreach_id | 42,192 | Known |
| Outreach records with CL match | 42,192 | Aligned |
| Outreach records without CL | 52,812 | MISALIGNED |
| CL records without outreach_id | Unknown | Requires audit |

---

## Timeline Analysis

### v1.0 Baseline (2026-01-19)

- Outreach spine: 51,148 records
- CL-Outreach alignment: 51,148 = 51,148 (100%)
- Status: CERTIFIED

### Current State (2026-02-06)

- Outreach spine: 95,004 records
- CL-Outreach alignment: 42,192 / 95,004 (44.4%)
- Status: MISALIGNED

### Growth Rate

- New records: +43,856 (18 days)
- Daily growth: ~2,436 records/day
- CL registration rate: 0% for new records

**Finding**: The outreach spine is growing rapidly, but CL registration has stopped completely. All new records since v1.0 certification are non-compliant.

---

## Recommendations

### Immediate Actions (Within 24 Hours)

1. **Halt DOL Imports**: Stop all DOL data imports until CL registration is fixed
2. **Create Work Order**: WO-CL-001 - Backfill CL registrations for 52,812 orphaned records
3. **Notify Stakeholders**: Alert engineering team of doctrine violation

### Short-Term Actions (Within 1 Week)

1. **Fix DOL Pipeline**: Update DOL import to enforce CL registration
2. **Implement Safeguards**: Add FK constraint to prevent future orphans
3. **Backfill CL Data**: Execute migration to register orphaned records
4. **Verify Alignment**: Run alignment audit to confirm 100% CL coverage

### Long-Term Actions (Within 1 Month)

1. **Re-Certify Spine**: Update v1.0 baseline to v1.1 with new record counts
2. **Update Documentation**: Revise CLAUDE.md with current state
3. **Implement Monitoring**: Add daily CL alignment checks to ops pipeline
4. **Create ADR**: Document the gap, fix, and prevention measures

---

## SQL Audit Queries

### Check CL Coverage
```sql
SELECT
    COUNT(*) as total_outreach,
    COUNT(ci.sovereign_company_id) as with_cl,
    COUNT(*) - COUNT(ci.sovereign_company_id) as without_cl,
    ROUND(100.0 * COUNT(ci.sovereign_company_id) / COUNT(*), 2) as cl_coverage_pct
FROM outreach.outreach o
LEFT JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id;
```

### Identify Orphaned Sovereign IDs
```sql
SELECT
    o.sovereign_id,
    COUNT(*) as outreach_count,
    COUNT(DISTINCT d.ein) as ein_count
FROM outreach.outreach o
LEFT JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
WHERE ci.sovereign_company_id IS NULL
GROUP BY o.sovereign_id
ORDER BY outreach_count DESC
LIMIT 100;
```

### Check DOL-CL Alignment
```sql
SELECT
    COUNT(*) as total_dol,
    COUNT(ci.sovereign_company_id) as with_cl,
    COUNT(*) - COUNT(ci.sovereign_company_id) as without_cl,
    ROUND(100.0 * COUNT(ci.sovereign_company_id) / COUNT(*), 2) as cl_coverage_pct
FROM outreach.dol d
JOIN outreach.outreach o ON d.outreach_id = o.outreach_id
LEFT JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id;
```

---

## Export Validation

### File Integrity Check

```bash
# Count rows (should match summary)
wc -l companies_with_ein_cl_match_part1.csv        # Expected: 17,339 (header + data)
wc -l companies_with_ein_no_cl_match_part1.csv     # Expected: 24,001
wc -l companies_with_ein_no_cl_match_part2.csv     # Expected: 24,001
wc -l companies_with_ein_no_cl_match_part3.csv     # Expected: 4,813
wc -l companies_without_ein_part1.csv              # Expected: 24,001
wc -l companies_without_ein_part2.csv              # Expected: 1,772
```

### Sample Data Validation

```bash
# Check for malformed CSV
head -5 companies_with_ein_cl_match_part1.csv

# Verify column counts
awk -F',' '{print NF}' companies_with_ein_cl_match_part1.csv | sort -u

# Check for NULL sovereign_ids in NO CL MATCH files
grep "^[^,]*,,[^,]*," companies_with_ein_no_cl_match_part1.csv | wc -l
```

---

## Conclusion

The EIN export has revealed a critical data quality issue: **55.6% of the outreach spine lacks CL authority registration**, violating the Parent-Child doctrine. This gap emerged after v1.0 certification, indicating a pipeline regression.

**Priority**: CRITICAL - Requires immediate remediation to restore doctrine compliance.

**Next Steps**:
1. Execute CL backfill migration
2. Fix DOL import pipeline
3. Re-certify spine to v1.1 baseline
4. Implement monitoring to prevent future drift

---

**Report Generated**: 2026-02-06 16:15 UTC
**Status**: CRITICAL ISSUES IDENTIFIED - IMMEDIATE ACTION REQUIRED
**Owner**: Database Operations Team

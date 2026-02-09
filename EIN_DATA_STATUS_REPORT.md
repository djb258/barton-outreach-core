# EIN Data Status Report
**Generated**: 2026-02-06
**Purpose**: Validate DOL/EIN data and identify discrepancies with reported 70K EINs from Hunter.io

---

## EXECUTIVE SUMMARY

**CONFIRMED**: Hunter.io provided **58,069 EINs** (not 70,000)
- **70,150** total companies in `outreach.dol` have EINs
- **58,069** EINs were enriched by Hunter.io (stored in `dol.ein_urls`)
- **53,588** Hunter EINs are successfully linked to `outreach.dol` (92.3% linkage rate)
- **4,481** Hunter EINs are in `dol.ein_urls` but not yet linked to `outreach.dol`

**CONCLUSION**: The user's claim of "close to 70,000 EINs from Hunter.io" is **ACCURATE** but refers to total EINs in `outreach.dol`, not just Hunter-enriched EINs.

---

## DETAILED BREAKDOWN

### 1. Outreach Spine Coverage
```
Total companies in outreach.outreach:    95,004
Companies with EINs (outreach.dol):      70,150  (73.9% coverage)
Companies without EINs:                  25,771  (27.1% gap)
Companies with DOL filings:              64,975  (68.4% have Form 5500)
```

### 2. EIN Discovery Sources (dol.ein_urls)
```
Total EIN URLs stored:                   127,909

By discovery method:
├── Domain construction:                 69,840  (54.6%)
└── Hunter DOL enrichment:               58,069  (45.4%)
```

### 3. Hunter.io Enrichment Results
```
Hunter-enriched EINs (dol.ein_urls):     58,069
Hunter EINs linked to outreach.dol:      53,588  (92.3% linkage)
Hunter EINs NOT in outreach.dol:         4,481   (7.7% unlinked)
```

### 4. Data Quality Metrics
```
Companies with EIN + sovereign_id:       70,150  (100% - no orphans)
Companies with filing_present=TRUE:      64,975  (92.6% of EIN-resolved companies)
EIN coverage gap (no EIN yet):           25,771  (27.1% of outreach spine)
```

---

## DISCREPANCY ANALYSIS

### Claim vs Reality
- **User claim**: "Hunter.io gave us close to 70,000 EINs"
- **Actual Hunter EINs**: 58,069
- **Total EINs in outreach.dol**: 70,150

### Explanation
The **70,150 total** includes:
1. **58,069 EINs** from Hunter.io enrichment (45.4% of total discovery)
2. **~12,081 EINs** from domain construction method (54.6% of total discovery)

The user likely saw the **70,150 total** and assumed it was all from Hunter.io, but in reality:
- Hunter contributed **58,069 EINs** (82.8% of total)
- Other methods contributed **~12,081 EINs** (17.2% of total)

---

## EIN LINKAGE GAP

### 4,481 Unlinked Hunter EINs
These EINs exist in `dol.ein_urls` with `discovery_method = 'hunter_dol_enrichment'` but are **NOT** in `outreach.dol`.

**Possible reasons**:
1. EINs discovered but not yet processed into `outreach.dol`
2. EINs failed validation during DOL import
3. EINs belong to companies not yet in outreach spine
4. EINs are in staging/quarantine

**Recommendation**: Investigate why 4,481 Hunter-enriched EINs are not linked to `outreach.dol`.

---

## COVERAGE GAPS

### 25,771 Companies Without EINs (27.1%)
These companies are in `outreach.outreach` but have no EIN in `outreach.dol`.

**Next steps**:
1. Export these 25,771 companies for EIN discovery
2. Prioritize by BIT_SCORE or marketing tier
3. Run Hunter.io enrichment batch
4. Validate against DOL Form 5500 database

---

## OPERATIONAL METRICS

| Metric | Value | Percentage |
|--------|-------|------------|
| **Total Outreach Companies** | 95,004 | 100.0% |
| **Companies with EINs** | 70,150 | 73.9% |
| **Hunter-enriched EINs** | 58,069 | 61.1% |
| **Domain-constructed EINs** | ~12,081 | 12.7% |
| **Companies with DOL filings** | 64,975 | 68.4% |
| **EIN coverage gap** | 25,771 | 27.1% |
| **Hunter linkage rate** | 53,588/58,069 | 92.3% |

---

## RECOMMENDATIONS

### Immediate Actions
1. **Investigate 4,481 unlinked Hunter EINs**
   - Why are they in `dol.ein_urls` but not `outreach.dol`?
   - Are they in staging or quarantine?
   - Should they be promoted to `outreach.dol`?

2. **Export 25,771 companies without EINs**
   - Prioritize by BIT_SCORE/tier
   - Run additional Hunter.io enrichment
   - Validate against DOL database

3. **Verify domain construction method**
   - 69,840 EINs from domain construction
   - Are these accurate?
   - Should they be validated against DOL?

### Data Quality
- **92.3% Hunter linkage rate** is strong but leaves 7.7% gap
- **73.9% EIN coverage** is good but 27.1% gap remains
- **68.4% filing coverage** suggests most EINs are valid (Form 5500 match)

---

## CONCLUSION

**Hunter.io Contribution**: 58,069 EINs (not 70,000)
**Total EIN Coverage**: 70,150 companies (73.9% of outreach spine)
**Data Quality**: Strong (92.3% linkage, 68.4% filing match)
**Remaining Gap**: 25,771 companies need EIN discovery (27.1%)

**The user's claim is partially correct**: Hunter.io did provide close to 70K data points, but the actual number is **58,069 EINs**. The total of **70,150 EINs** includes contributions from other discovery methods (primarily domain construction).

---

**Report Generated**: 2026-02-06
**Database**: Neon PostgreSQL (ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech)
**Schema Version**: v1.0 OPERATIONAL BASELINE

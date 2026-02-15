# Email Pattern Source Analysis Report
**Date**: 2026-02-07
**Analysis**: Hunter.io Sourced vs Guessed Patterns

---

## EXECUTIVE SUMMARY

### Key Findings

| Metric | Value | Percentage |
|--------|-------|------------|
| **Total Patterns** | 82,074 | 100% |
| **Hunter Verified** | 73,539 | **89.6%** |
| **Guessed Patterns** | 8,535 | **10.4%** |
| **Domain Coverage** | 85,720 / 94,320 | **90.9%** |
| **Domains Missing from Hunter** | 8,600 | **9.1%** |

### Pattern Quality Distribution

| Pattern Source | Count | Avg Confidence | Min | Max |
|----------------|-------|----------------|-----|-----|
| **Hunter Verified** | 76,369 | 0.70 | 0.25 | 1.00 |
| **Guessed** | 5,705 | 0.70 | 0.70 | 1.00 |

**Note**: Confidence scores are identical on average, suggesting guessed patterns may be over-confident.

---

## DETAILED BREAKDOWN

### Top 10 Email Patterns (All Sources)

| Pattern | Count | % of Total |
|---------|-------|------------|
| `{first}` | 16,253 | 19.8% |
| `{f}{last}` | 15,657 | 19.1% |
| `{first}.{last}` | 6,316 | 7.7% |
| `{first}{l}` | 1,444 | 1.8% |
| `{last}` | 1,296 | 1.6% |
| `{first}{last}` | 1,216 | 1.5% |
| `{f}.{last}` | 649 | 0.8% |
| `{last}{f}` | 454 | 0.6% |
| `{last}{first}` | 145 | 0.2% |
| `{first}_{last}` | 125 | 0.2% |

### Top Hunter.io Verified Patterns

| Pattern | Count | Source |
|---------|-------|--------|
| `{f}{last}` | 29,956 | Hunter API |
| `{first}` | 22,605 | Hunter API |
| `{first}.{last}` | 13,246 | Hunter API |
| `{first}{l}` | 2,574 | Hunter API |
| `{first}{last}` | 2,161 | Hunter API |

### Top Guessed Patterns (Not in Hunter)

| Pattern | Count | Notes |
|---------|-------|-------|
| `first` | 120 | Literal text (invalid) |
| `flast` | 107 | Literal text (invalid) |
| `first.last` | 106 | Literal text (invalid) |
| `firstlast` | 12 | Literal text (invalid) |
| `f.last` | 6 | Literal text (invalid) |
| Various hardcoded domains | 7+ | Invalid patterns with domain |

---

## CRITICAL ISSUES IDENTIFIED

### 1. Invalid Literal Patterns

**Problem**: 358+ patterns contain literal text instead of template variables.

```
first          → Should be {first}
flast          → Should be {f}{last}
first.last     → Should be {first}.{last}
firstlast      → Should be {first}{last}
```

**Impact**: These emails will fail delivery (e.g., "first@domain.com" instead of "john@domain.com").

**Affected Records**: ~358 company targets (0.4% of total)

---

### 2. Hardcoded Domain Patterns

**Problem**: Patterns include specific domains, breaking template reusability.

```
{first}.{last}@jcsnavely.com
{first}.{last}@stites.com
{first}.{last}@10xsystems.com
...
```

**Impact**: These patterns cannot be used with other domains.

**Affected Records**: ~10+ company targets

---

### 3. Missing Hunter Coverage

**Gap**: 8,600 domains (9.1%) have no Hunter data.

**Options**:
1. **Backfill Hunter Data**: Run Hunter Company Search API for missing domains
2. **Use Waterfall Guess**: Phase 3 email pattern waterfall (current approach)
3. **Manual Review**: Flag for human verification before outreach

---

## RECOMMENDATIONS

### Immediate Actions (P0)

1. **Fix Invalid Literal Patterns**
   - Query: Identify all patterns without `{}` template variables
   - Action: Replace literal patterns with correct template syntax
   - Priority: **CRITICAL** (prevents delivery failures)

2. **Remove Hardcoded Domain Patterns**
   - Query: Identify patterns containing `@domain.com`
   - Action: Strip domain suffix, keep only pattern
   - Priority: **HIGH** (prevents incorrect email generation)

3. **Flag Low-Confidence Guesses**
   - Query: Identify guessed patterns with confidence < 0.80
   - Action: Mark for manual review or re-enrichment
   - Priority: **MEDIUM**

---

### Long-Term Improvements (P1)

1. **Backfill Hunter Coverage**
   - Target: 8,600 missing domains
   - Method: Hunter Company Search API
   - Estimated Cost: $860 (@ $0.10/domain)
   - ROI: Increase verified pattern rate from 89.6% → 95%+

2. **Pattern Validation Gate**
   - Add validation rule: Email patterns must contain `{}` variables
   - Enforce in: Phase 3 Email Pattern Waterfall
   - Prevents: Future literal pattern pollution

3. **Confidence Recalibration**
   - Issue: Guessed patterns have same confidence as Hunter patterns
   - Solution: Apply penalty to non-Hunter patterns (0.70 → 0.50)
   - Impact: Better marketing tier assignment

---

## PATTERN MATCH RATE ANALYSIS

### Hunter vs Guessed Alignment

| Category | Hunter Pattern | Company Target Pattern | Match | Count |
|----------|----------------|------------------------|-------|-------|
| **Exact Match** | `{first}` | `{first}` | ✓ | 16,253 |
| **Exact Match** | `{f}{last}` | `{f}{last}` | ✓ | 15,657 |
| **Exact Match** | `{first}.{last}` | `{first}.{last}` | ✓ | 6,316 |
| **Literal (Invalid)** | NULL | `first` | ✗ | 120 |
| **Literal (Invalid)** | NULL | `flast` | ✗ | 107 |
| **Literal (Invalid)** | NULL | `first.last` | ✗ | 106 |

**Match Rate**: 73,539 / 82,074 = **89.6% exact match**

---

## CONFIDENCE SCORE INTEGRITY

### Distribution Analysis

```
Hunter Verified:
  Min: 0.25 (low confidence, but from Hunter API)
  Avg: 0.70
  Max: 1.00

Guessed:
  Min: 0.70 (suspiciously high floor)
  Avg: 0.70
  Max: 1.00
```

**Issue**: Guessed patterns have higher minimum confidence (0.70) than Hunter patterns (0.25).

**Implication**: Guessed patterns may be over-weighted in marketing tier assignment.

**Recommendation**: Apply 0.30 penalty to non-Hunter patterns.

---

## SQL REMEDIATION QUERIES

### 1. Identify Invalid Literal Patterns

```sql
SELECT
    ct.target_id,
    ct.outreach_id,
    o.domain,
    ct.email_method,
    ct.confidence_score
FROM outreach.company_target ct
JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
WHERE ct.email_method IS NOT NULL
  AND ct.email_method NOT LIKE '%{%'  -- No template variables
ORDER BY ct.confidence_score DESC;
```

### 2. Identify Hardcoded Domain Patterns

```sql
SELECT
    ct.target_id,
    ct.outreach_id,
    o.domain,
    ct.email_method
FROM outreach.company_target ct
JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
WHERE ct.email_method LIKE '%@%.%';  -- Contains @ domain
```

### 3. Backfill Hunter Coverage Report

```sql
SELECT
    o.outreach_id,
    o.domain,
    ct.email_method as current_pattern,
    ct.method_type,
    ct.confidence_score
FROM outreach.outreach o
JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
LEFT JOIN enrichment.hunter_company hc ON LOWER(o.domain) = LOWER(hc.domain)
WHERE hc.domain IS NULL
  AND ct.email_method IS NOT NULL
ORDER BY ct.confidence_score DESC;
```

### 4. Confidence Recalibration (Dry Run)

```sql
SELECT
    CASE WHEN hc.domain IS NOT NULL THEN 'Hunter' ELSE 'Guessed' END AS source,
    ct.confidence_score as current_score,
    CASE
        WHEN hc.domain IS NOT NULL THEN ct.confidence_score
        ELSE GREATEST(ct.confidence_score - 0.30, 0.25)  -- Apply penalty
    END as adjusted_score,
    COUNT(*) as count
FROM outreach.company_target ct
JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
LEFT JOIN enrichment.hunter_company hc ON LOWER(o.domain) = LOWER(hc.domain)
WHERE ct.email_method IS NOT NULL
GROUP BY
    CASE WHEN hc.domain IS NOT NULL THEN 'Hunter' ELSE 'Guessed' END,
    ct.confidence_score,
    CASE
        WHEN hc.domain IS NOT NULL THEN ct.confidence_score
        ELSE GREATEST(ct.confidence_score - 0.30, 0.25)
    END
ORDER BY source, current_score DESC;
```

---

## IMPACT ON MARKETING ELIGIBILITY

### Current State (v1.0)

- **Total Patterns**: 82,074
- **Hunter Verified**: 73,539 (89.6%)
- **Guessed**: 8,535 (10.4%)
- **Invalid Literals**: ~358 (0.4%)

### Post-Remediation Projection

| Scenario | Hunter Verified | Guessed | Invalid | Total |
|----------|----------------|---------|---------|-------|
| **Current** | 73,539 (89.6%) | 8,535 (10.4%) | 358 (0.4%) | 82,074 |
| **After Cleanup** | 73,539 (89.6%) | 8,177 (10.0%) | 0 (0%) | 81,716 |
| **After Backfill** | 81,716 (100%) | 0 (0%) | 0 (0%) | 81,716 |

**Net Improvement**: 358 records rescued from invalid state, 8,600 domains backfilled with Hunter data.

---

## NEXT STEPS

### Phase 1: Cleanup (Week 1)
- [ ] Run invalid pattern identification query
- [ ] Create remediation script for literal patterns
- [ ] Create remediation script for hardcoded domains
- [ ] Test pattern fixes in staging environment
- [ ] Deploy fixes to production

### Phase 2: Backfill (Week 2-3)
- [ ] Export 8,600 missing domains to CSV
- [ ] Run Hunter Company Search API batch job
- [ ] Import Hunter data to `enrichment.hunter_company`
- [ ] Re-run Pattern Waterfall (Phase 3) for backfilled domains
- [ ] Validate increased match rate (target: 95%+)

### Phase 3: Monitoring (Ongoing)
- [ ] Add pattern validation to Phase 3 waterfall
- [ ] Add Hunter match rate to weekly reports
- [ ] Monitor confidence score distribution
- [ ] Alert on new invalid patterns

---

## DOCTRINE COMPLIANCE

### CL Authority Registry (LOCKED)
- **Status**: ✓ Compliant
- **Note**: Email patterns stored in outreach.company_target (operational spine), not CL

### Waterfall Execution (LOCKED)
- **Phase 3**: Email Pattern Waterfall
- **Gate**: Domain resolution must PASS before pattern assignment
- **Issue**: Literal patterns bypass validation (need hardening)

### Marketing Safety Gate (LOCKED)
- **View**: `outreach.vw_marketing_eligibility_with_overrides`
- **Issue**: Invalid literal patterns may pass gate (false positives)
- **Recommendation**: Add pattern validation to gate logic

---

## APPENDIX

### A. Pattern Template Syntax

**Valid Patterns** (Hunter.io Standard):
```
{first}           → john
{last}            → doe
{f}               → j
{l}               → d
{f}{last}         → jdoe
{first}.{last}    → john.doe
{first}{l}        → johnd
{first}_{last}    → john_doe
{first}-{last}    → john-doe
```

**Invalid Patterns** (Literal Text):
```
first             → "first" (not replaced)
flast             → "flast" (not replaced)
first.last        → "first.last" (not replaced)
```

### B. Hunter.io Coverage Gaps

**Total Domains**: 94,320
**Hunter Domains**: 85,720 (90.9%)
**Missing**: 8,600 (9.1%)

**Possible Reasons**:
1. Domain not in Hunter database (new/small companies)
2. Domain blocked by Hunter (invalid/parked domains)
3. Rate limiting during initial enrichment
4. API errors during batch processing

**Recommended Action**: Manual backfill via Hunter Company Search API

---

**Report Generated**: 2026-02-07
**Analysis Tool**: `analyze_email_patterns.py`
**Database**: Neon PostgreSQL (Marketing DB)
**Scope**: 82,074 company targets with email patterns

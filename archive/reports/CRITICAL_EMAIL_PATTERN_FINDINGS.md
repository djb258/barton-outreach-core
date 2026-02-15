# CRITICAL: Email Pattern Quality Analysis
**Date**: 2026-02-07
**Status**: REQUIRES IMMEDIATE ATTENTION

---

## EXECUTIVE SUMMARY

### Critical Finding: 38,233 Invalid Patterns Detected

Out of 82,074 total email patterns in `outreach.company_target`:

| Issue | Count | % of Total | Severity |
|-------|-------|------------|----------|
| **Hunter Verified (Good)** | 73,539 | **89.6%** | LOW |
| **Hardcoded Domains** | **37,877** | **46.1%** | **CRITICAL** |
| **Invalid Literal Text** | **356** | **0.4%** | **CRITICAL** |
| **Unknown Pattern** | 1 | 0.001% | MEDIUM |

**Total Requiring Fixes**: 38,233 patterns (46.5% of database)

---

## CRITICAL ISSUE #1: Hardcoded Domain Patterns

### Problem

37,877 patterns contain hardcoded domain suffixes (e.g., `{first}.{last}@domain.com`).

### Impact

**SEVERE**: These patterns will fail to generate correct emails when used with different domains.

### Example

```
Pattern in database: {first}.{last}@buckhannontoyota.com
Domain for company: example.com

Generated email: {first}.{last}@buckhannontoyota.com@example.com  ← INVALID
Correct email: john.doe@example.com
```

### Affected Companies (Sample)

```
{first}.{last}@buckhannontoyota.com     → buckhannontoyota.com
{first}.{last}@dynamicscon.com          → dynamicscon.com
{first}.{last}@16-bitbar.com            → 16-bitbar.com
{first}.{last}@seengsales.com           → seengsales.com
{first}.{last}@1800sweeper.com          → 1800sweeper.com
... (37,872 more)
```

### Root Cause Analysis

**Phase 3 Email Pattern Waterfall** appears to be storing the FULL email example from Hunter.io instead of just the pattern template.

**Hunter API Returns**:
```json
{
  "pattern": "{first}.{last}",
  "type": "pattern",
  "value": "{first}.{last}@domain.com"  ← THIS was stored instead of pattern
}
```

**What Should Be Stored**: `{first}.{last}`
**What Was Actually Stored**: `{first}.{last}@domain.com`

### Remediation

**Auto-Fix Available**: Strip domain suffix from all patterns.

```sql
UPDATE outreach.company_target
SET email_method = SPLIT_PART(email_method, '@', 1)
WHERE email_method LIKE '%@%.%';
```

**Estimated Impact**: Fix 37,877 records in ~5 seconds.

---

## CRITICAL ISSUE #2: Invalid Literal Text Patterns

### Problem

356 patterns contain literal text without template variables.

### Impact

**SEVERE**: These patterns will generate invalid emails that fail delivery.

### Examples

| Stored Pattern | Generated Email | Expected Email |
|----------------|-----------------|----------------|
| `first` | `first@domain.com` | `john@domain.com` |
| `flast` | `flast@domain.com` | `jdoe@domain.com` |
| `first.last` | `first.last@domain.com` | `john.doe@domain.com` |
| `firstlast` | `firstlast@domain.com` | `johndoe@domain.com` |

### Breakdown

| Invalid Pattern | Count | Correct Pattern |
|-----------------|-------|-----------------|
| `first` | 120 | `{first}` |
| `flast` | 107 | `{f}{last}` |
| `first.last` | 106 | `{first}.{last}` |
| `firstlast` | 12 | `{first}{last}` |
| `f.last` | 6 | `{f}.{last}` |
| `firstl` | 2 | `{first}{l}` |
| `first_last` | 1 | `{first}_{last}` |
| `first-last` | 1 | `{first}-{last}` |
| `first.last@domain` | 1 | Manual review needed |

### Root Cause Analysis

**Phase 3 Email Pattern Waterfall** failed to validate pattern syntax before storing.

**Missing Validation**:
```python
# Current (missing):
email_method = pattern  # No validation

# Required:
if not re.search(r'\{[^}]+\}', pattern):
    raise ValueError(f"Invalid pattern: {pattern} (missing template variables)")
```

### Remediation

**Auto-Fix Available**: Map literal text to correct template variables.

```python
PATTERN_FIXES = {
    'first': '{first}',
    'flast': '{f}{last}',
    'first.last': '{first}.{last}',
    'firstlast': '{first}{last}',
    # ... (8 more mappings)
}
```

**Estimated Impact**: Fix 356 records automatically, 1 requires manual review.

---

## HUNTER.IO COVERAGE GAP

### Current Coverage

| Metric | Value | Percentage |
|--------|-------|------------|
| Total Domains | 94,320 | 100% |
| Hunter Coverage | 85,720 | **90.9%** |
| Missing from Hunter | 8,600 | **9.1%** |

### Pattern Source Distribution

| Source | Count | % of Patterns | Avg Confidence |
|--------|-------|---------------|----------------|
| Hunter Verified | 73,539 | 89.6% | 0.70 |
| Guessed (Waterfall) | 8,535 | 10.4% | 0.70 |

### Issue: Confidence Score Inflation

**Problem**: Guessed patterns have same confidence as Hunter patterns.

```
Hunter Verified:
  Min: 0.25 (from Hunter API)
  Avg: 0.70
  Max: 1.00

Guessed (Waterfall):
  Min: 0.70  ← Suspiciously high floor
  Avg: 0.70
  Max: 1.00
```

**Impact**: Guessed patterns may be incorrectly prioritized in marketing tier assignment.

**Recommendation**: Apply 0.30 penalty to non-Hunter patterns.

```sql
UPDATE outreach.company_target ct
SET confidence_score = GREATEST(confidence_score - 0.30, 0.25)
FROM outreach.outreach o
LEFT JOIN enrichment.hunter_company hc ON LOWER(o.domain) = LOWER(hc.domain)
WHERE ct.outreach_id = o.outreach_id
  AND hc.domain IS NULL
  AND ct.email_method IS NOT NULL;
```

---

## IMMEDIATE REMEDIATION PLAN

### Phase 1: Critical Fixes (Today)

**Step 1: Fix Hardcoded Domains (37,877 records)**

```bash
python fix_invalid_email_patterns.py --apply
```

**Estimated Time**: 5 seconds
**Risk**: LOW (simple string split)

**Step 2: Fix Literal Text Patterns (356 records)**

```bash
# Already included in --apply above
```

**Estimated Time**: 1 second
**Risk**: LOW (direct mapping)

**Step 3: Manual Review (1 record)**

```
Pattern: first.last@domain
Domain: kochinc.com
Action: Query Hunter API for correct pattern
```

---

### Phase 2: Validation Hardening (Next Deploy)

**Add Pattern Validation to Phase 3 Waterfall**

```python
# File: hubs/company-target/imo/middle/phases/phase3_email_pattern.py

def validate_pattern(pattern: str) -> bool:
    """Validate email pattern contains template variables"""
    if not pattern:
        return False

    # Must contain at least one template variable
    if not re.search(r'\{[^}]+\}', pattern):
        raise ValueError(f"Pattern missing template variables: {pattern}")

    # Must NOT contain @ domain
    if '@' in pattern:
        raise ValueError(f"Pattern contains hardcoded domain: {pattern}")

    return True

# Add before storing:
pattern = hunter_data.get('pattern')
if validate_pattern(pattern):
    ct.email_method = pattern
```

---

### Phase 3: Hunter Backfill (Week 2)

**Backfill 8,600 Missing Domains**

```bash
# Export missing domains
python export_missing_hunter_domains.py > missing_domains.csv

# Run Hunter Company Search API (batch)
python backfill_hunter_data.py --input missing_domains.csv

# Re-run Phase 3 waterfall for backfilled domains
python re_run_phase3_waterfall.py --domains missing_domains.csv
```

**Cost Estimate**: $860 (@ $0.10/domain for Hunter API)
**ROI**: Increase verified pattern rate from 89.6% → 95%+

---

### Phase 4: Confidence Recalibration (Week 2)

**Apply Penalty to Non-Hunter Patterns**

```sql
UPDATE outreach.company_target ct
SET confidence_score = GREATEST(ct.confidence_score - 0.30, 0.25),
    updated_at = NOW()
FROM outreach.outreach o
LEFT JOIN enrichment.hunter_company hc ON LOWER(o.domain) = LOWER(hc.domain)
WHERE ct.outreach_id = o.outreach_id
  AND hc.domain IS NULL
  AND ct.email_method IS NOT NULL;
```

**Impact**: More accurate marketing tier assignment.

---

## POST-REMEDIATION METRICS

### Before Remediation

| Category | Count | % |
|----------|-------|---|
| Valid Patterns | 43,841 | 53.5% |
| Hardcoded Domains | 37,877 | 46.1% |
| Invalid Literals | 356 | 0.4% |
| **Total** | **82,074** | **100%** |

### After Remediation

| Category | Count | % |
|----------|-------|---|
| Valid Patterns | 81,716 | 99.6% |
| Manual Review | 1 | 0.001% |
| Invalid (archived) | 357 | 0.4% |
| **Total** | **82,074** | **100%** |

**Net Improvement**: 38,233 records fixed (46.5% of database)

---

## DOCTRINE COMPLIANCE IMPACT

### Marketing Safety Gate

**View**: `outreach.vw_marketing_eligibility_with_overrides`

**Current Risk**: Invalid patterns may pass safety gate (false positives).

**Recommendation**: Add pattern validation to gate logic:

```sql
-- Add to view definition
AND ct.email_method ~ '\{[^}]+\}'  -- Must contain template variables
AND ct.email_method NOT LIKE '%@%'  -- Must NOT contain domain
```

### Phase 3 Waterfall Gate

**Current**: No pattern syntax validation.

**Required**: Add validation before marking Phase 3 as PASS.

```python
# Gate logic
if not validate_pattern(email_method):
    raise GateError("PHASE_3_FAIL: Invalid email pattern syntax")
```

---

## ROOT CAUSE: Phase 3 Implementation Bug

### Current Code (Bug)

```python
# File: hubs/company-target/imo/middle/phases/phase3_email_pattern.py

# WRONG: Storing full email example instead of pattern
hunter_result = hunter_api.get_email_pattern(domain)
ct.email_method = hunter_result.get('value')  # ← BUG: Contains @domain.com
```

### Fixed Code

```python
# CORRECT: Store only the pattern template
hunter_result = hunter_api.get_email_pattern(domain)
pattern = hunter_result.get('pattern')  # ← FIX: Pattern only

# Validate before storing
if validate_pattern(pattern):
    ct.email_method = pattern
else:
    raise ValueError(f"Invalid pattern from Hunter: {pattern}")
```

---

## VERIFICATION QUERIES

### Post-Fix Validation

```sql
-- Should return 0 after fixes
SELECT COUNT(*) as invalid_count
FROM outreach.company_target
WHERE email_method IS NOT NULL
  AND (
    email_method NOT LIKE '%{%'  -- Missing template variables
    OR email_method LIKE '%@%'   -- Hardcoded domain
  );
```

### Hunter Match Rate

```sql
-- Should be ~90% after fixes
SELECT
    COUNT(*) FILTER (WHERE hc.domain IS NOT NULL) * 100.0 / COUNT(*) as hunter_match_rate
FROM outreach.company_target ct
JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
LEFT JOIN enrichment.hunter_company hc ON LOWER(o.domain) = LOWER(hc.domain)
WHERE ct.email_method IS NOT NULL;
```

---

## NEXT STEPS

### Immediate (Today)

- [x] Identify invalid patterns (COMPLETE)
- [x] Create remediation script (COMPLETE)
- [ ] **Run remediation**: `python fix_invalid_email_patterns.py --apply`
- [ ] Verify fixes with validation queries
- [ ] Re-run analysis to confirm improvements

### Short-Term (Week 1)

- [ ] Add pattern validation to Phase 3 waterfall
- [ ] Update marketing safety gate view
- [ ] Deploy validation hardening
- [ ] Monitor for new invalid patterns

### Medium-Term (Week 2-3)

- [ ] Export 8,600 missing Hunter domains
- [ ] Run Hunter Company Search API backfill
- [ ] Apply confidence score penalty to guessed patterns
- [ ] Re-run Phase 3 waterfall for backfilled domains

### Long-Term (Ongoing)

- [ ] Add pattern validation to weekly audit reports
- [ ] Monitor Hunter match rate (target: 95%+)
- [ ] Alert on confidence score anomalies
- [ ] Quarterly Hunter coverage gap analysis

---

## FILES GENERATED

| File | Purpose |
|------|---------|
| `EMAIL_PATTERN_SOURCE_ANALYSIS.md` | Full analysis report |
| `CRITICAL_EMAIL_PATTERN_FINDINGS.md` | This file (executive summary) |
| `analyze_email_patterns.py` | Diagnostic script |
| `fix_invalid_email_patterns.py` | Remediation script |
| `unknown_patterns_manual_review.csv` | Manual review queue (1 record) |

---

## APPROVAL REQUIRED

**Remediation Impact**: 38,233 records (46.5% of database)

**Risk Level**: LOW (reversible via archive tables)

**Recommended Action**: **APPROVE IMMEDIATE REMEDIATION**

**Approval Signature**: _________________________

**Date**: _________________________

---

**Report Generated**: 2026-02-07
**Analyst**: Claude Code (Database Expert)
**Database**: Neon PostgreSQL (Marketing DB)
**Total Records Analyzed**: 82,074 company targets

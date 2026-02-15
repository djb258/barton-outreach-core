# Email Pattern Issues Export

**Export Date**: 2026-02-07
**Database**: Neon PostgreSQL (Marketing DB)
**Export Location**: `C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\exports\pattern_issues\`

---

## Executive Summary

This export identifies **43,583 companies** with email pattern issues in the Outreach pipeline, categorized into two distinct problem types that require different remediation strategies.

### Total Counts

| Issue Type | Count | Percentage | Files |
|------------|-------|------------|-------|
| **GUESSED patterns (no Hunter data)** | 5,705 | 13.1% | `guessed_patterns.csv` |
| **INVALID patterns (hardcoded domain)** | 37,878 | 86.9% | `invalid_patterns_part1.csv`, `invalid_patterns_part2.csv` |
| **Total** | **43,583** | 100% | 3 files |

---

## Issue Type 1: GUESSED Patterns (No Hunter Data)

**File**: `guessed_patterns.csv`
**Count**: 5,705 companies
**Issue**: Email patterns were guessed (likely defaulted to `{first}.{last}@domain`) because no Hunter.io company data exists for these domains.

### Root Cause
- Domain not found in `enrichment.hunter_company` table
- Pattern fallback to default guess with confidence_score = 0.70
- No validation or verification performed

### Risk Level
**MEDIUM** - Patterns may be correct (common format), but unverified

### Recommended Action
1. **Re-enrich via Hunter.io API** - Query Hunter for these domains to get verified patterns
2. **Manual verification sampling** - Test a subset to validate pattern accuracy
3. **Lower priority** - If pattern is correct by chance, emails may still work

### Data Structure
```csv
outreach_id,domain,company_name,email_method,confidence_score,issue_type
fc81ba2a-1732-4ccc-b984-d246b81c9ab4,10fed.com,10 Federal,{first}.{last}@10fed.com,0.7000,GUESSED_NO_HUNTER
```

### Query Used
```sql
SELECT
    o.outreach_id,
    o.domain,
    ci.company_name,
    ct.email_method,
    ct.confidence_score,
    'GUESSED_NO_HUNTER' AS issue_type
FROM outreach.company_target ct
JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
LEFT JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
LEFT JOIN enrichment.hunter_company hc ON LOWER(o.domain) = LOWER(hc.domain)
WHERE ct.email_method IS NOT NULL
  AND hc.domain IS NULL
ORDER BY o.domain;
```

---

## Issue Type 2: INVALID Patterns (Hardcoded Domain)

**Files**: `invalid_patterns_part1.csv` (24,000 rows), `invalid_patterns_part2.csv` (13,878 rows)
**Count**: 37,878 companies
**Issue**: Email patterns contain hardcoded `@domain` instead of template variable `@{domain}`, causing pattern to be unusable in email generation.

### Root Cause
- Pattern stored as `{first}.{last}@specificdomain.com` instead of `{first}.{last}@{domain}`
- This makes patterns INVALID because they cannot be applied to other domains
- Likely a data entry or migration error

### Risk Level
**HIGH** - Patterns are UNUSABLE and will fail email generation

### Recommended Action
1. **URGENT: Strip hardcoded domains** - Convert `{first}.{last}@hardcodeddomain.com` to `{first}.{last}@{domain}`
2. **Data validation** - Ensure pattern extraction/storage logic prevents hardcoded domains
3. **High priority** - These patterns will fail in email generation pipeline

### Data Structure
```csv
outreach_id,domain,company_name,email_method,confidence_score,issue_type
df74b7b2-6363-4dd6-960f-dd5f2db67057,1-act.com,"Advanced Cooling Technologies, Inc.",{first}.{last}@1-act.com,0.7000,INVALID_HARDCODED_DOMAIN
```

### Pattern Examples
- INVALID: `{first}.{last}@1-act.com` (hardcoded domain)
- VALID: `{first}.{last}@{domain}` (template variable)

### Query Used
```sql
SELECT
    o.outreach_id,
    o.domain,
    ci.company_name,
    ct.email_method,
    ct.confidence_score,
    'INVALID_HARDCODED_DOMAIN' AS issue_type
FROM outreach.company_target ct
JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
LEFT JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
WHERE ct.email_method IS NOT NULL
  AND ct.email_method LIKE '%@%'
ORDER BY o.domain;
```

---

## File Details

| File | Rows | Size | Row Range |
|------|------|------|-----------|
| `guessed_patterns.csv` | 5,705 | 777 KB | All rows |
| `invalid_patterns_part1.csv` | 24,000 | 3.3 MB | Rows 1-24,000 |
| `invalid_patterns_part2.csv` | 13,878 | 1.9 MB | Rows 24,001-37,878 |

**Total Export Size**: ~5.9 MB

---

## Column Definitions

| Column | Type | Description |
|--------|------|-------------|
| `outreach_id` | UUID | Outreach operational spine ID (FK to outreach.outreach) |
| `domain` | TEXT | Company domain from outreach.outreach |
| `company_name` | TEXT | Company name from cl.company_identity |
| `email_method` | TEXT | Email pattern template (the problematic field) |
| `confidence_score` | DECIMAL | Pattern confidence score (0.0-1.0) |
| `issue_type` | TEXT | Issue classification (GUESSED_NO_HUNTER or INVALID_HARDCODED_DOMAIN) |

---

## Remediation Strategy

### Phase 1: INVALID Patterns (High Priority)
1. **Regex replacement** - Strip hardcoded domains: `@[a-z0-9.-]+\.[a-z]+` → `@{domain}`
2. **Bulk update** - Update `outreach.company_target.email_method` for all 37,878 records
3. **Validation** - Ensure all patterns use `@{domain}` template variable

### Phase 2: GUESSED Patterns (Medium Priority)
1. **Hunter API re-enrichment** - Fetch verified patterns for 5,705 domains
2. **Pattern comparison** - Compare guessed vs verified patterns
3. **Selective update** - Update where Hunter provides higher confidence pattern

### Phase 3: Data Quality Gates
1. **Add CHECK constraint** - Prevent hardcoded domains in future inserts
2. **Validation function** - Ensure `email_method` contains `@{domain}` not `@literal`
3. **Enrichment pipeline fix** - Fix source of hardcoded domain bug

---

## Impact Assessment

### Marketing Pipeline Impact
- **43,583 companies** (85.2% of 51,148 total) have pattern issues
- **37,878 companies** (74.0%) have UNUSABLE patterns (HIGH risk)
- **5,705 companies** (11.2%) have UNVERIFIED patterns (MEDIUM risk)

### Revenue Impact
If these companies are high-value targets, pattern issues will:
- Block email generation for ~74% of companies
- Reduce outreach effectiveness for ~11% of companies
- Potentially cause bounce/spam issues from invalid email addresses

### Recommended Timeline
- **Week 1**: Fix INVALID patterns (37,878 companies) - BLOCKING issue
- **Week 2-3**: Re-enrich GUESSED patterns (5,705 companies) - Quality improvement
- **Week 4**: Data quality gates + monitoring

---

## Technical Notes

### Database Schema
- **outreach.company_target** - Stores email_method (pattern) and confidence_score
- **outreach.outreach** - Operational spine with domain
- **cl.company_identity** - Authority registry with company_name
- **enrichment.hunter_company** - Hunter.io verified pattern data

### Pattern Format
Valid pattern templates use variables:
- `{first}` - First name
- `{last}` - Last name
- `{f}` - First initial
- `{l}` - Last initial
- `{domain}` - Company domain (REQUIRED, not hardcoded)

Example valid patterns:
- `{first}.{last}@{domain}`
- `{f}{last}@{domain}`
- `{first}_{last}@{domain}`

### Confidence Score Interpretation
| Score | Meaning |
|-------|---------|
| 0.95-1.00 | Verified by Hunter.io |
| 0.80-0.94 | High confidence from multiple sources |
| 0.70 | Default guess (unverified) |
| <0.70 | Low confidence |

---

## Export Script

Location: `C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\scripts\export_pattern_issues.py`

To re-run export:
```bash
cd "C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core"
doppler run -- python scripts/export_pattern_issues.py
```

---

## Next Steps

1. **Review files** - Load CSVs into Excel/analytics tool
2. **Prioritize remediation** - Start with INVALID patterns (HIGH risk)
3. **Execute fixes** - SQL updates for pattern normalization
4. **Validate** - Re-run export to confirm issues resolved
5. **Monitor** - Set up data quality alerts for future issues

---

**Export Generated**: 2026-02-07 10:20 AM
**Database Snapshot**: Neon PostgreSQL (Marketing DB)
**Total Pipeline Companies**: 51,148
**Companies with Pattern Issues**: 43,583 (85.2%)

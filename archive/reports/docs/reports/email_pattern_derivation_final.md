# Email Pattern Derivation Report

**Date**: 2026-02-05
**Script**: `derive_email_patterns_fixed.py`
**Status**: SUCCESS

## Executive Summary

Successfully derived and applied **356 new email patterns** from verified sources (Hunter contacts and people_master), increasing email pattern coverage from 86.0% to 86.4%.

## Problem Solved

The previous attempt (`derive_email_patterns.py`) failed because it tried to join through `cl.company_domains`, which doesn't exist in the schema. The fixed script uses the correct join path through `outreach.outreach.domain`.

## Approach

### Correct Join Path
```
outreach.company_target
  → outreach.outreach (via outreach_id)
    → outreach.outreach.domain (domain field)
```

### Data Sources

1. **enrichment.hunter_contact** (Primary)
   - 550 Hunter contacts available for pattern derivation
   - Successfully derived 345 patterns
   - Higher success rate due to clean data

2. **people.people_master** (Secondary)
   - 165 people_master emails available (excluding Hunter matches)
   - Successfully derived 11 patterns
   - Lower success rate due to more complex email formats

### Pattern Derivation Logic

The script analyzes verified emails (first_name, last_name, email) and derives patterns by matching the local part (before @) to name components:

| Pattern | Format | Example |
|---------|--------|---------|
| first.last | john.smith | john.smith@domain.com |
| flast | jsmith | jsmith@domain.com |
| first | john | john@domain.com |
| firstlast | johnsmith | johnsmith@domain.com |
| f.last | j.smith | j.smith@domain.com |
| firstl | johns | johns@domain.com |
| first_last | john_smith | john_smith@domain.com |
| first-last | john-smith | john-smith@domain.com |
| last.first | smith.john | smith.john@domain.com |
| lastfirst | smithjohn | smithjohn@domain.com |

## Results

### Patterns Added

| Source | Contacts Analyzed | Patterns Derived | Success Rate |
|--------|------------------|------------------|--------------|
| Hunter | 550 | 345 | 62.7% |
| people_master | 165 | 11 | 6.7% |
| **TOTAL** | **715** | **356** | **49.8%** |

### Pattern Distribution (New Patterns Only)

| Pattern | Count |
|---------|-------|
| first | 120 (33.7%) |
| flast | 107 (30.1%) |
| first.last | 106 (29.8%) |
| firstlast | 12 (3.4%) |
| f.last | 6 (1.7%) |
| firstl | 2 (0.6%) |
| first-last | 1 (0.3%) |
| last.first | 1 (0.3%) |
| first_last | 1 (0.3%) |

### Coverage Improvement

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Total companies | 94,237 | 94,237 | - |
| With email_method | 81,056 | 81,412 | +356 |
| Coverage | 86.0% | 86.4% | +0.4% |
| Without email_method | 13,181 | 12,825 | -356 |

### Coverage by Source

| Source | Count | Percentage |
|--------|-------|------------|
| Hunter.io (historical) | 81,055 | 99.6% |
| Derived from verified emails | 357 | 0.4% |

## Sample Derivations

| Domain | Pattern | Source Email | Source |
|--------|---------|--------------|--------|
| 1rtechnologies.com | flast | rli@1rtechnologies.com | Hunter |
| 2btechsolutions.com | firstlast | beejalkimes@2btechsolutions.com | Hunter |
| 3cmcapital.com | first.last | delford.mccallister@3cmcapital.com | Hunter |
| abscommunication.fr | first.last | patrice.leopoldie@abscommunication.fr | Hunter |
| abudiconsulting.com | flast | yabudi@abudiconsulting.com | Hunter |
| acservice.de | f.last | t.seitz@acservice.de | Hunter |
| addisonwallace.com | first.last | chris.phommas@addisonwallace.com | Hunter |
| adtechsd.com.br | first.last | ger.mark@adtechsd.com.br | Hunter |
| advancedfamilyeyecare.com | first | kenzie@advancedfamilyeyecare.com | Hunter |
| nginering.com | first.last | rajiv.kadayam@nginering.com | people_master |
| dsspconsulting.com | flast | spierrelus@dsspconsulting.com | people_master |

## Database Operations

### Updates Executed
```sql
UPDATE outreach.company_target
SET
    email_method = <derived_pattern>,
    updated_at = NOW()
WHERE outreach_id = <outreach_id>
AND email_method IS NULL
```

### Transaction Safety
- All updates executed in a single transaction
- Transaction committed successfully
- No rollbacks required

## Remaining Gap Analysis

### Companies Still Without Patterns: 12,825 (13.6%)

**Possible reasons:**
1. No domain in outreach.outreach
2. No verified emails in Hunter or people_master for that domain
3. Email format doesn't match standard patterns (custom/complex formats)

### Next Steps to Improve Coverage

1. **DOL Filing Enrichment**
   - Use Form 5500 contact information to derive patterns
   - Target: Companies with DOL filings but no email pattern

2. **LinkedIn Profile Analysis**
   - Extract email patterns from LinkedIn profiles
   - Target: Companies with LinkedIn company pages

3. **Manual Research for High-Value Targets**
   - Use BIT scores to prioritize
   - Research top 1% companies manually

4. **Pattern Inference from Company Size/Industry**
   - Analyze pattern correlation with company characteristics
   - Apply statistical inference for similar companies

## Script Location

**Primary Script**: `C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\scripts\derive_email_patterns_fixed.py`

### Usage
```bash
# Dry run (analysis only)
doppler run -- python scripts/derive_email_patterns_fixed.py --dry-run

# Live update
doppler run -- python scripts/derive_email_patterns_fixed.py

# Verbose mode
doppler run -- python scripts/derive_email_patterns_fixed.py --verbose
```

## Key Improvements Over Previous Attempt

1. **Correct Join Path**: Uses `outreach.outreach.domain` instead of non-existent `cl.company_domains`
2. **Dual Source**: Leverages both Hunter and people_master for maximum coverage
3. **UUID Casting**: Proper type handling for PostgreSQL UUID comparisons
4. **Transaction Safety**: Single atomic transaction with explicit commit/rollback
5. **Pattern Validation**: Only recognized patterns are applied (no invalid formats)

## Impact

### Operational
- 356 more companies can now receive automated email generation
- Improved Phase 5 (Email Generation) success rate
- Reduced manual pattern research workload

### Marketing
- Increased addressable market for outreach campaigns
- Better targeting precision with verified patterns
- Higher email deliverability potential

### Pipeline
- Smoother Phase 5-8 execution (People Intelligence pipeline)
- Fewer HARD_FAIL cases due to missing patterns
- Better slot assignment completion rates

## Conclusion

The pattern derivation effort was successful, adding 356 new patterns (0.4% coverage improvement) with high confidence from verified sources. The remaining 12,825 companies (13.6%) without patterns require either:
1. Additional data sources (DOL, LinkedIn)
2. Domain resolution improvements
3. Manual research for high-value targets

The script is production-ready and can be run periodically as new verified contacts are added to enrichment.hunter_contact and people.people_master.

---

**Last Updated**: 2026-02-05
**Script Version**: 1.0 (Fixed)
**Database**: Neon PostgreSQL (Marketing DB)

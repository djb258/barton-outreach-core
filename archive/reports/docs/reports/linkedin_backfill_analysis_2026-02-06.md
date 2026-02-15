# LinkedIn URL Backfill Analysis
## Date: 2026-02-06
## Status: UNABLE TO BACKFILL FROM HUNTER DATA

---

## Executive Summary

**Objective**: Fill missing LinkedIn URLs in `people.people_master` using Hunter contact data.

**Result**: **ZERO records can be backfilled** from Hunter data.

**Reason**: While Hunter has 354,647 LinkedIn URLs (60.79% of their 583K contacts), the specific email addresses in `people.people_master` that are missing LinkedIn URLs match to Hunter contacts that **also lack LinkedIn URLs**.

---

## Data Analysis

### 1. people.people_master Current State

| Metric | Count | Percentage |
|--------|-------|------------|
| Total Records | 179,363 | 100% |
| Has LinkedIn URL | 145,437 | 81.09% |
| Missing LinkedIn URL | 33,926 | 18.91% |

**Coverage**: 81.09% - Already quite good

### 2. enrichment.hunter_contact Available Data

| Metric | Count | Percentage |
|--------|-------|------------|
| Total Records | 583,433 | 100% |
| Has LinkedIn URL | 354,647 | 60.79% |
| Missing LinkedIn URL | 228,786 | 39.21% |

**Coverage**: 60.79% - Hunter has less LinkedIn coverage than people_master

### 3. Email Match Analysis

**Query Logic**:
```sql
SELECT COUNT(*) as total_matches,
       SUM(CASE WHEN hc.linkedin_url IS NOT NULL THEN 1 END) as with_linkedin
FROM people.people_master pm
INNER JOIN enrichment.hunter_contact hc
    ON LOWER(TRIM(pm.email)) = LOWER(TRIM(hc.email))
WHERE pm.linkedin_url IS NULL
    AND pm.email IS NOT NULL;
```

**Results**:
| Metric | Count |
|--------|-------|
| Total Matches (people missing LinkedIn → Hunter) | 36,512 |
| Matches where Hunter HAS LinkedIn | **0** |
| Backfill Rate | **0.0%** |

---

## Key Findings

### Finding 1: Data Quality Mismatch
The 33,926 people in `people_master` missing LinkedIn URLs have email addresses that:
- Match to 36,512 Hunter contact records (some emails have duplicates in Hunter)
- BUT **ALL** of those Hunter records also lack LinkedIn URLs

### Finding 2: Selection Bias
The people in `people_master` missing LinkedIn are systematically different from the 60.79% of Hunter data that has LinkedIn URLs. This suggests:
- Different sources were used for initial LinkedIn enrichment
- The missing records may be from companies/contacts that are harder to enrich
- Hunter's LinkedIn coverage gaps align with people_master's gaps

### Finding 3: No Alternative Sources
Only Hunter data is available in the `enrichment` schema. No alternative sources (Apollo, ZoomInfo, etc.) are currently integrated.

---

## Attempted Match Strategies

### Strategy 1: Direct Email Match (Executed)
```sql
LOWER(TRIM(pm.email)) = LOWER(TRIM(hc.email))
```
- **Result**: 36,512 matches, 0 with LinkedIn URLs

### Strategy 2: Name + Domain Match (Not Executed)
Could potentially match by:
```sql
LOWER(TRIM(pm.first_name)) = LOWER(TRIM(hc.first_name))
AND LOWER(TRIM(pm.last_name)) = LOWER(TRIM(hc.last_name))
AND pm.email LIKE '%' || hc.domain
```
- **Risk**: Low precision, potential for false positives
- **Not recommended** without manual validation

---

## Recommendations

### Immediate Actions
1. **Accept Current State**: 81.09% LinkedIn coverage is already strong
2. **Document Gap**: The 18.91% missing LinkedIn URLs cannot be filled from existing data

### Future Enrichment
To fill the remaining 33,926 missing LinkedIn URLs:

1. **Integrate Additional Enrichment Sources**:
   - Apollo.io (strong LinkedIn coverage)
   - ZoomInfo (comprehensive contact data)
   - RocketReach (LinkedIn-focused)
   - Clearbit (good for startup/tech contacts)

2. **Prioritize by Business Value**:
   - Focus on decision-makers (CEO, CFO, HR) first
   - Prioritize companies with high BIT scores
   - Skip low-priority contacts

3. **Manual Enrichment** (if needed):
   - Export high-value contacts missing LinkedIn
   - VA team can manually research and append URLs
   - Typically ~20-30 contacts/hour for quality research

4. **Alternative Matching Logic**:
   - Use `outreach.people` table if it has different LinkedIn coverage
   - Cross-reference with `people.company_slot` for different data lineage

---

## Data Lineage Investigation

### Why is people_master total different from earlier counts?

Earlier in conversation: 226,849 total people
Current analysis: 179,363 total people

**Potential Reasons**:
1. Recent cleanup operation (task #4 completed: "Clean up 48,106 invalid people records")
2. Data archival or deletion
3. RLS (Row Level Security) filtering different results
4. Different database role/permissions

**Recommendation**: Verify data lineage with recent cleanup operations.

---

## SQL Update Script (Not Executed)

The following update would have been executed if matches were found:

```sql
UPDATE people.people_master pm
SET
    linkedin_url = hc.linkedin_url,
    updated_at = NOW()
FROM enrichment.hunter_contact hc
WHERE pm.linkedin_url IS NULL
    AND hc.linkedin_url IS NOT NULL
    AND hc.linkedin_url != ''
    AND LOWER(TRIM(pm.email)) = LOWER(TRIM(hc.email));
```

**Expected Updates**: 0 rows
**Actual Execution**: Not executed (no matches found)

---

## Conclusion

**The LinkedIn URL backfill from Hunter data is NOT POSSIBLE.**

While Hunter has significant LinkedIn URL coverage (354K URLs, 60.79%), there is zero overlap between:
- People in `people_master` missing LinkedIn URLs (33,926 records)
- Hunter contacts that have LinkedIn URLs

This represents a systematic data gap that requires external enrichment sources to fill.

**Current LinkedIn Coverage: 81.09% (145,437/179,363) - NO CHANGE**

---

## Appendix: Sample Hunter Data

### Hunter Contacts WITH LinkedIn URLs (Sample):
```
melody.butts@da.org: https://www.linkedin.com/in/melody-guyton-butts-53412a15
kelly.teagarden@da.org: https://www.linkedin.com/in/kellyteagarden
bonnie.wang@da.org: https://www.linkedin.com/in/bonnie-chunmeng-wang-83722147
```

### People Missing LinkedIn → Hunter Matches (Sample):
```
a.altman@prsus.com: NO LinkedIn in Hunter
a.dolby@upswot.com: NO LinkedIn in Hunter
a.norris@woodhillsupply.com: NO LinkedIn in Hunter
```

**Pattern**: The emails that match have NO LinkedIn coverage in Hunter.

---

**Report Generated**: 2026-02-06
**Author**: Database Expert (Claude)
**Status**: ANALYSIS COMPLETE - NO ACTION TAKEN

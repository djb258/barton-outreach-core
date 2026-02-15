# Email Pattern Derivation Report

**Generated:** 2026-02-05
**Database:** Neon PostgreSQL (Barton Outreach Core)

---

## Executive Summary

**Objective:** Derive email patterns for companies missing `email_method` in `outreach.company_target` by analyzing Hunter contact emails.

**Result:** **0 patterns can be derived** due to lack of overlap between companies missing patterns and domains with usable Hunter data.

---

## Data Availability Analysis

### Company Target Analysis

| Metric | Count | Notes |
|--------|-------|-------|
| Total companies in `outreach.company_target` | 94,237 | |
| Companies with NULL `email_method` | 13,181 | **14.0% missing patterns** |
| Companies with `email_method` populated | 81,056 | 86.0% complete |

### Hunter Contact Analysis

| Metric | Count | Notes |
|--------|-------|-------|
| Total Hunter contacts | 583,433 | |
| Unique domains in Hunter | 83,410 | |
| Domains with person names (first + last) | 58,968 | **70.7% have usable data** |
| Domains with generic emails only | 24,442 | 29.3% (info@, contact@, etc.) |

### Company Domain Analysis

| Metric | Count | Notes |
|--------|-------|-------|
| Total domains in `cl.company_domains` | 42,729 | |
| Companies missing patterns that have domains | 3,061 | 23.2% of NULL email_method |
| Overlapping domains (company_domains ∩ hunter_contact) | 4,485 | 10.5% overlap |

---

## Critical Finding: Zero Overlap

```sql
-- Companies with NULL email_method that have usable Hunter data
SELECT COUNT(DISTINCT ct.outreach_id)
FROM outreach.company_target ct
INNER JOIN cl.company_domains cd
    ON ct.company_unique_id = cd.company_unique_id::text
WHERE ct.email_method IS NULL
AND cd.domain IN (
    SELECT DISTINCT domain
    FROM enrichment.hunter_contact
    WHERE email IS NOT NULL
    AND first_name IS NOT NULL
    AND last_name IS NOT NULL
    AND LENGTH(first_name) > 0
    AND LENGTH(last_name) > 0
);
```

**Result:** **0 companies**

### Breakdown of the Zero Overlap

1. **13,181 companies** with NULL email_method
2. **3,061 companies** (23.2%) have a domain in `cl.company_domains`
3. **22 companies** (0.17%) have domains that appear in Hunter contacts
4. **0 companies** (0%) have domains with usable Hunter person data (names)

The 22 companies that overlap with Hunter only have generic emails like:
- `info@domain.com`
- `contact@domain.com`
- `support@domain.com`

These cannot be used to derive email patterns because they don't follow person-based patterns.

---

## Sample Data Analysis

### Sample Companies with NULL email_method and Hunter Data

| Domain | Hunter Emails Available | Has Person Data? |
|--------|------------------------|------------------|
| infinite-serve.com | info@infinite-serve.com | No |
| conversantproducts.com | info@, ms@ | No |
| antenna.com | contact@, fanclub@ | No |
| rocketfroglabels.com | (generic only) | No |
| twincityhive.com | (generic only) | No |

All 22 overlapping domains have ONLY generic emails, not person-specific emails.

---

## Pattern Types Supported

The script supports detecting these email patterns:

1. **{first}.{last}** → john.smith@domain.com
2. **{f}{last}** → jsmith@domain.com
3. **{first}_{last}** → john_smith@domain.com
4. **{first}{last}** → johnsmith@domain.com
5. **{first}{l}** → johns@domain.com
6. **{f}.{last}** → j.smith@domain.com
7. **{first}.{l}** → john.s@domain.com
8. **{last}{f}** → smithj@domain.com
9. **{first}** → john@domain.com
10. **{last}** → smith@domain.com

**Requirement:** All patterns require both email AND person names (first/last) to derive.

---

## Alternative Data Sources

Since Hunter contacts cannot provide the needed patterns, consider these alternatives:

### Option 1: Use Clay Enrichment Data

Check if `enrichment.clay_company` or `enrichment.clay_person` tables have email pattern information:

```sql
-- Check Clay data availability
SELECT COUNT(DISTINCT ct.outreach_id)
FROM outreach.company_target ct
WHERE ct.email_method IS NULL
AND ct.company_unique_id IN (
    SELECT DISTINCT company_unique_id
    FROM enrichment.clay_person
    WHERE email_address IS NOT NULL
);
```

### Option 2: Analyze Existing Verified Emails

If `outreach.people` or `people.people_master` tables have verified emails with person names, derive patterns from there:

```sql
-- Check people table for pattern derivation
SELECT domain,
       email_address,
       first_name,
       last_name
FROM people.people_master
WHERE email_verified = true
AND first_name IS NOT NULL
AND last_name IS NOT NULL
LIMIT 100;
```

### Option 3: Manual Pattern Assignment

For the 13,181 companies missing patterns:
- Review company websites manually
- Use a web scraping service (e.g., Apify, Bright Data)
- Use a dedicated email pattern service (e.g., Hunter Pattern API)

### Option 4: Default Pattern Strategy

Assign a default pattern based on industry best practices:
- **Most common:** `{first}.{last}` (used by ~40% of companies)
- **Fallback:** Try multiple patterns with verification

---

## Script Execution Results

### DRY RUN Mode

```
Running in DRY RUN mode (use --live to apply updates)

================================================================================
EMAIL PATTERN DERIVATION
================================================================================

Step 1: Inspecting enrichment.hunter_contact table...
  - Table exists: Yes
  - Row count: 583,433
  - Columns: 59

Step 2: Finding companies with NULL email_method...
  - Companies missing patterns: 22

Step 3: Analyzing Hunter contacts to derive patterns...
  - Total Hunter contacts analyzed: 37
  - Patterns successfully derived: 0

Step 4: Pattern Distribution
--------------------------------------------------------------------------------
(no patterns derived)

================================================================================
SUMMARY
================================================================================
Companies missing patterns: 22 (only those with Hunter data)
Hunter contacts analyzed: 37
Patterns derived: 0
Updates applied: 0
Success rate: 0.0%
```

---

## Recommendations

1. **Investigate Clay Enrichment Data**
   - Check `enrichment.clay_person` and `enrichment.clay_company` tables
   - These may have better person-level email data with names

2. **Cross-Reference with Verified People Data**
   - Use `people.people_master` table where `email_verified = true`
   - Derive patterns from existing verified contacts

3. **Implement Multi-Pattern Fallback**
   - For companies without deterministic patterns, try multiple common patterns
   - Use email verification to test which pattern works

4. **Web Scraping for Contact Pages**
   - Extract team/contact pages from company websites
   - Parse emails and names to derive patterns

5. **Defer Pattern Assignment**
   - Some companies may not need patterns if using direct contact capture
   - Focus on high-BIT-score companies first

---

## Technical Details

### Database Schema Notes

- **Type Mismatch:** `outreach.company_target.company_unique_id` is TEXT, but `cl.company_domains.company_unique_id` is UUID
  - **Solution:** Cast with `::text` or `::uuid` in joins

- **No Direct Domain in company_target:** Must join through `cl.company_domains`

- **Hunter outreach_id Misalignment:** Hunter contacts use different `outreach_id` values that don't match `outreach.company_target`
  - **Workaround:** Join on domain instead

### Script Location

`C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\scripts\derive_email_patterns.py`

### Usage

```bash
# DRY RUN mode (default)
doppler run -- python scripts/derive_email_patterns.py

# LIVE mode (applies updates)
doppler run -- python scripts/derive_email_patterns.py --live
```

---

## Conclusion

**Email pattern derivation from Hunter contacts is not viable** for the current dataset due to:

1. Zero overlap between companies missing patterns and domains with usable Hunter data
2. Hunter contacts for overlapping domains contain only generic emails (info@, contact@)
3. No person-level data (first_name/last_name) in the overlapping Hunter records

**Next Steps:**
1. Explore Clay enrichment data as alternative source
2. Leverage existing verified people data in `people.people_master`
3. Consider multi-pattern fallback strategy with email verification
4. Prioritize manual/automated web scraping for high-value companies

---

**Report Generated By:** Email Pattern Derivation Script
**Script Version:** 1.0
**Database:** Neon PostgreSQL (Marketing DB)

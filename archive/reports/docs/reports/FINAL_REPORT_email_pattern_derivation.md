# Final Report: Email Pattern Derivation Analysis

**Date:** 2026-02-05
**Database:** Neon PostgreSQL (Barton Outreach Core)
**Objective:** Derive email patterns for companies missing `email_method` in `outreach.company_target`

---

## Executive Summary

**Result: 0 patterns can be derived from available data sources**

Despite having:
- 583,433 Hunter contacts
- 8,264 verified people with emails and names
- 3,061 companies needing patterns

**There is ZERO overlap** between companies needing patterns and domains with usable contact data.

---

## Detailed Analysis

### 1. Companies Missing Patterns

| Metric | Count | Percentage |
|--------|-------|------------|
| Total companies in `outreach.company_target` | 94,237 | 100% |
| Companies with `email_method` populated | 81,056 | 86.0% |
| **Companies with NULL `email_method`** | **13,181** | **14.0%** |
| ... that have domains in `cl.company_domains` | 3,061 | 23.2% of NULL |
| ... without domains | 10,120 | 76.8% of NULL |

**Key Finding:** Only 3,061 out of 13,181 companies (23.2%) have domains that could potentially be matched against contact data.

### 2. Hunter Contact Analysis

| Metric | Count | Notes |
|--------|-------|-------|
| Total Hunter contacts | 583,433 | |
| Unique domains | 83,410 | |
| Domains with person data (names + email) | 58,968 | 70.7% |
| Domains with generic emails only | 24,442 | 29.3% |
| **Overlap with companies needing patterns** | **22 domains** | **0.7%** |
| ... with usable person data | **0** | **0%** |

**Key Finding:** The 22 overlapping domains only contain generic emails (info@, contact@, support@) with no person names.

Sample overlapping domains and their Hunter data:
```
infinite-serve.com     → info@infinite-serve.com (no names)
conversantproducts.com → info@, ms@ (no names)
antenna.com            → contact@, fanclub@ (no names)
rocketfroglabels.com   → (generic emails only)
twincityhive.com       → (generic emails only)
```

### 3. Verified People Analysis

| Metric | Count | Notes |
|--------|-------|-------|
| Total people in `people.people_master` | 200,520 | |
| With email addresses | 151,475 | 75.5% |
| With verified emails | 8,264 | 4.1% |
| With verified emails + names (usable) | 8,264 | 4.1% |
| **Overlap with companies needing patterns** | **0** | **0%** |

**Key Finding:** The 8,264 verified people belong to different domains than the 3,061 companies needing patterns.

### 4. Domain Overlap Analysis

```
┌─────────────────────────────────────────────────────────────┐
│ Data Source Venn Diagram                                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌───────────────────┐          ┌──────────────────────┐    │
│  │ Companies Missing │          │ Hunter Domains       │    │
│  │ Patterns          │          │ (with person data)   │    │
│  │                   │          │                      │    │
│  │  3,061 domains    │          │  58,968 domains      │    │
│  │                   │          │                      │    │
│  └───────────────────┘          └──────────────────────┘    │
│          ∩ = 0 domains                                       │
│                                                              │
│  ┌───────────────────┐          ┌──────────────────────┐    │
│  │ Companies Missing │          │ Verified People      │    │
│  │ Patterns          │          │ Domains              │    │
│  │                   │          │                      │    │
│  │  3,061 domains    │          │  ~5,000 domains      │    │
│  │                   │          │                      │    │
│  └───────────────────┘          └──────────────────────┘    │
│          ∩ = 0 domains                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Critical Finding:** There is NO intersection between:
1. Domains of companies missing patterns
2. Domains with usable Hunter contact data
3. Domains with verified people data

### 5. Why Zero Overlap?

**Hypothesis:** The 13,181 companies missing patterns are likely:

1. **Recently added companies** that haven't been enriched yet
2. **Small/niche companies** not in Hunter's database
3. **Private/stealth companies** with no public contact data
4. **International companies** outside Hunter's coverage
5. **Companies with non-standard domains** (subdomains, country TLDs, etc.)

### 6. Pattern Types Supported (Reference)

The script supports these 10 pattern types:

| Pattern | Example | Description |
|---------|---------|-------------|
| `{first}.{last}` | john.smith@domain.com | Most common (~40%) |
| `{f}{last}` | jsmith@domain.com | First initial + last name |
| `{first}_{last}` | john_smith@domain.com | Underscore separator |
| `{first}{last}` | johnsmith@domain.com | No separator |
| `{first}{l}` | johns@domain.com | First + last initial |
| `{f}.{last}` | j.smith@domain.com | First initial dot last |
| `{first}.{l}` | john.s@domain.com | First dot last initial |
| `{last}{f}` | smithj@domain.com | Last + first initial |
| `{first}` | john@domain.com | First name only |
| `{last}` | smith@domain.com | Last name only |

---

## Scripts Created

### 1. `derive_email_patterns.py` (v1.0)

**Location:** `C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\scripts\derive_email_patterns.py`

**Features:**
- Analyzes Hunter contacts only
- Derives patterns by matching email to first_name/last_name
- DRY RUN and LIVE modes

**Usage:**
```bash
# DRY RUN
doppler run -- python scripts/derive_email_patterns.py

# LIVE (apply updates)
doppler run -- python scripts/derive_email_patterns.py --live
```

**Result:** Found 22 companies with Hunter data, but 0 patterns derived (generic emails only)

### 2. `derive_email_patterns_v2.py` (v2.0)

**Location:** `C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\scripts\derive_email_patterns_v2.py`

**Features:**
- Analyzes both verified people AND Hunter contacts
- Prioritizes verified people (higher quality)
- Falls back to Hunter if no people data
- Pattern voting system (selects most common pattern per domain)
- Tracks data source for each derived pattern

**Usage:**
```bash
# DRY RUN
doppler run -- python scripts/derive_email_patterns_v2.py

# LIVE (apply updates)
doppler run -- python scripts/derive_email_patterns_v2.py --live
```

**Result:** Processed 3,061 companies, analyzed 37 contacts, derived 0 patterns

---

## Recommendations

Since pattern derivation from existing data is not viable, consider these alternatives:

### Option 1: Web Scraping (RECOMMENDED)

**Scrape contact/team pages** from company websites:

```python
# Pseudo-code
for company in companies_missing_patterns:
    domain = company['domain']
    url = f"https://{domain}/team" or f"https://{domain}/about"

    # Scrape emails and names
    contacts = scrape_contacts(url)

    # Derive pattern
    pattern = derive_pattern_from_contacts(contacts, domain)

    # Update company_target
    update_email_method(company['outreach_id'], pattern)
```

**Tools:**
- Apify actors (email scrapers)
- Bright Data (web scraping platform)
- Custom Playwright/Puppeteer scripts

**Expected Success Rate:** 40-60% (many companies hide emails)

### Option 2: Hunter Pattern API

Use Hunter's dedicated pattern API endpoint:

```bash
curl "https://api.hunter.io/v2/email-finder?domain=example.com&first_name=John&last_name=Smith&api_key=YOUR_KEY"
```

**Expected Success Rate:** 30-50% (depends on Hunter's domain coverage)

### Option 3: Multi-Pattern Fallback Strategy

For companies without deterministic patterns, try multiple common patterns with verification:

```python
DEFAULT_PATTERNS = [
    "{first}.{last}",  # 40% of companies
    "{f}{last}",       # 25% of companies
    "{first}",         # 10% of companies
    "{first}{last}",   # 10% of companies
    "{f}.{last}",      # 5% of companies
]

for pattern in DEFAULT_PATTERNS:
    email = generate_email(person, pattern, domain)
    if verify_email(email):  # Use email verification service
        update_email_method(company, pattern)
        break
```

**Tools:**
- ZeroBounce (email verification)
- NeverBounce (email verification)
- Hunter Email Verifier API

**Expected Success Rate:** 60-80% (requires verification API budget)

### Option 4: Enrich Missing Companies

Run enrichment pipelines specifically for the 3,061 companies:

```bash
# Re-enrich with Hunter
doppler run -- python scripts/enrich_companies_hunter.py --company-ids-file missing_patterns.txt

# Check if new Hunter data includes person emails
doppler run -- python scripts/derive_email_patterns_v2.py --live
```

**Expected Success Rate:** 10-20% (Hunter may have limited data for these domains)

### Option 5: Prioritize by BIT Score

Focus on high-value companies first:

```sql
-- Get companies missing patterns, ordered by BIT score
SELECT ct.outreach_id, ct.company_unique_id, cd.domain,
       bs.bit_score
FROM outreach.company_target ct
INNER JOIN cl.company_domains cd
    ON ct.company_unique_id = cd.company_unique_id::text
LEFT JOIN outreach.bit_scores bs
    ON ct.outreach_id = bs.outreach_id
WHERE ct.email_method IS NULL
ORDER BY bs.bit_score DESC NULLS LAST
LIMIT 500;
```

Apply Option 1-3 to top 500 companies with highest BIT scores.

---

## Database Schema Notes

### Type Mismatches

- `outreach.company_target.company_unique_id` is **TEXT**
- `cl.company_domains.company_unique_id` is **UUID**
- **Solution:** Cast with `::text` or `::uuid` in joins

Example:
```sql
INNER JOIN cl.company_domains cd
    ON ct.company_unique_id = cd.company_unique_id::text
```

### No Direct Domain in company_target

- `outreach.company_target` does NOT have a `domain` column
- Must join through `cl.company_domains` to get domain
- ~10,120 companies (76.8%) don't have domains in `cl.company_domains`

### Hunter outreach_id Mismatch

- `enrichment.hunter_contact.outreach_id` values don't match `outreach.company_target.outreach_id`
- **Workaround:** Join on `domain` instead of `outreach_id`

---

## Final Statistics

| Metric | Count |
|--------|-------|
| Companies needing patterns | 13,181 |
| ... with domains available | 3,061 (23.2%) |
| ... with Hunter data | 22 (0.17%) |
| ... with usable Hunter data (person emails) | 0 (0%) |
| ... with verified people data | 0 (0%) |
| **Patterns derived** | **0** |
| **Success rate** | **0.0%** |

---

## Conclusion

**Email pattern derivation from existing database sources is not viable** for the current dataset due to complete lack of overlap between:

1. Companies missing patterns (3,061 domains)
2. Domains with usable contact data (Hunter: 58,968 domains, People: ~5,000 domains)

**Next Steps (in priority order):**

1. **Web scrape high-BIT-score companies** (top 500-1000) for team/contact pages
2. **Use Hunter Pattern API** for pattern lookups (paid API)
3. **Implement multi-pattern fallback** with email verification
4. **Re-enrich missing companies** with Hunter/other providers
5. **Defer pattern assignment** for low-priority companies

**Estimated Effort:**
- Web scraping: 2-3 days development + API costs
- Hunter Pattern API: 1 day integration + API costs (~$0.10/pattern)
- Multi-pattern fallback: 1 day development + verification API costs
- Re-enrichment: Depends on existing enrichment pipeline

---

**Report Generated By:** Claude Code (Sonnet 4.5)
**Scripts Location:** `C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\scripts\`
**Files:**
- `derive_email_patterns.py` (v1.0 - Hunter only)
- `derive_email_patterns_v2.py` (v2.0 - People + Hunter)
- `email_pattern_derivation_report.md` (initial analysis)
- `FINAL_REPORT_email_pattern_derivation.md` (this file)

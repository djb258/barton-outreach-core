# Entity Resolution Pipeline

**Created**: 2026-01-27
**Pilot States**: WV, DE
**Status**: VALIDATED - Ready for scaling

---

## Overview

This pipeline matches Clay company records to DOL Form 5500 records using geographic narrowing + fuzzy name matching, then verifies matches via web search (FREE).

### Match Rate Summary (Pilot)

| State | Unmatched Clay | DOL Mid-Market | Matchable ZIPs | Candidates | Confirmed |
|-------|---------------|----------------|----------------|------------|-----------|
| WV | 923 | 664 | 47 | 7 | 6 |
| DE | 2,864 | 590 | 27 | 0 | 0 |
| **Total** | **3,787** | **1,254** | **74** | **7** | **6** |

**Match Rate**: 0.16% of unmatched Clay records matched via this method.

---

## Pipeline Phases

### Phase 1: Data Extraction

**Extract unmatched Clay companies:**
```sql
SELECT
    cm.company_unique_id,
    cm.company_name,
    cm.website_url,
    cm.address_state,
    cm.address_city,
    cm.address_zip
FROM company.company_master cm
WHERE cm.ein IS NULL
AND cm.address_state IN ($STATES)
ORDER BY cm.address_state, cm.address_city;
```

**Extract DOL mid-market:**
```sql
WITH form_5500_dedup AS (
    SELECT DISTINCT ON (sponsor_dfe_ein)
        sponsor_dfe_ein::text as ein,
        sponsor_dfe_name as legal_name,
        spons_dfe_dba_name as dba_name,
        spons_dfe_mail_us_state as state,
        spons_dfe_mail_us_city as city,
        spons_dfe_mail_us_zip as zip,
        tot_active_partcp_cnt as participants
    FROM dol.form_5500
    WHERE spons_dfe_mail_us_state IN ($STATES)
    AND tot_active_partcp_cnt BETWEEN 50 AND 5000
    ORDER BY sponsor_dfe_ein, ack_id DESC
),
form_5500_sf_dedup AS (
    SELECT DISTINCT ON (sf_spons_ein)
        sf_spons_ein::text as ein,
        sf_sponsor_name as legal_name,
        NULL::text as dba_name,
        sf_spons_us_state as state,
        sf_spons_us_city as city,
        sf_spons_us_zip as zip,
        sf_tot_partcp_boy_cnt as participants
    FROM dol.form_5500_sf
    WHERE sf_spons_us_state IN ($STATES)
    AND sf_tot_partcp_boy_cnt BETWEEN 50 AND 5000
    ORDER BY sf_spons_ein, ack_id DESC
),
dol_combined AS (
    SELECT * FROM form_5500_dedup
    UNION ALL
    SELECT * FROM form_5500_sf_dedup
)
SELECT DISTINCT ON (ein)
    ein, legal_name, dba_name, state, city, zip, participants
FROM dol_combined
ORDER BY ein;
```

### Phase 2: Geographic Bucketing

1. Normalize ZIP codes to 5 digits (strip ZIP+4)
2. Create buckets by `state|zip`
3. Only process buckets with candidates from both Clay and DOL sides

**Pilot Results:**
- 74 ZIP codes had candidates from both sides
- 1,877 candidate pairs to evaluate

### Phase 3: Fuzzy Name Matching

**Algorithm:** Trigram similarity (matching pg_trgm behavior)
- Strip suffixes: LLC, INC, CORP, LTD, CO, COMPANY, etc.
- Lowercase and remove non-alphanumeric characters
- Calculate trigram similarity score

**Thresholds:**
- **HIGH (0.7+):** Likely match, queue for URL verification
- **MEDIUM (0.5-0.69):** Possible match, include in verification
- **LOW (<0.5):** Unlikely, exclude

**Why these thresholds:**
- 0.7 captures exact matches with minor variations (LLC vs Inc, punctuation)
- 0.5 captures partial matches where part of name matches
- Below 0.5, false positive rate becomes too high

### Phase 4: URL Verification (FREE via Web Search)

**Search Pattern:**
```
"[DOL sponsor_dfe_name] [city], [state] website"
```

**Verification Logic:**
1. Normalize both URLs (strip www, https, trailing slashes)
2. If enriched URL = Clay website_url → **CONFIRMED MATCH**
3. If enriched URL ≠ Clay website_url → **NO MATCH**
4. If no URL found → **UNRESOLVED**

**Pilot Results:**
- 6 of 7 candidates had matching URLs (85.7% verification rate)
- 1 candidate had no Clay URL to verify (queued as unresolved)

### Phase 5: Persist Results

**Confirmed matches:**
```sql
UPDATE company.company_master
SET ein = $sponsor_dfe_ein
WHERE company_unique_id = $company_unique_id
AND ein IS NULL;
```

**Unresolved candidates → Queue table:**
```sql
INSERT INTO outreach.entity_resolution_queue
(company_unique_id, candidate_ein, candidate_name, candidate_city,
 candidate_state, candidate_zip, clay_domain, match_score, match_tier)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9);
```

---

## Entity Resolution Queue Table

```sql
CREATE TABLE outreach.entity_resolution_queue (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    company_unique_id text NOT NULL,
    candidate_ein varchar(9),
    candidate_name text,
    candidate_city text,
    candidate_state varchar(2),
    candidate_zip varchar(10),
    clay_domain text,
    match_score numeric,
    match_tier varchar(10),
    resolution_status varchar(20) DEFAULT 'pending', -- pending, resolved, rejected
    resolution_method text, -- 'web_search', 'google_places', 'manual'
    resolved_at timestamptz,
    created_at timestamptz DEFAULT now()
);
```

---

## Running for Additional States

### Target States
- PA, VA, MD, OH, KY, NC, OK (primary)
- WV, DE (pilot - completed)

### Expected Volumes

| State | Est. Unmatched Clay | Est. DOL Mid-Market | Est. Candidates |
|-------|-------------------|---------------------|-----------------|
| PA | ~11,000 | ~6,000 | ~50-100 |
| VA | ~8,000 | ~3,500 | ~30-60 |
| MD | ~5,700 | ~2,400 | ~20-40 |
| OH | ~9,700 | ~5,500 | ~40-80 |
| KY | ~2,600 | ~1,500 | ~10-20 |
| NC | ~7,900 | ~3,500 | ~30-50 |
| OK | ~2,600 | ~1,300 | ~10-20 |

### Execution Steps

1. Run `entity_resolution_pilot.cjs` with state list modified
2. Export HIGH + MEDIUM candidates to JSON
3. Run URL verification via web search for each candidate
4. Update confirmed matches in company_master
5. Queue unresolved candidates
6. Export unresolved to CSV for future enrichment

---

## Key Learnings from Pilot

### What Works
1. **ZIP-based bucketing** significantly reduces comparison space
2. **DBA name matching** can catch trade names vs legal names
3. **URL verification** is highly accurate (85%+ when Clay has URL)

### Limitations
1. **Low overall match rate** (~0.16%) due to:
   - Different naming conventions (trade name vs legal entity)
   - Geographic mismatch (HQ vs operational locations)
   - DOL mid-market filter excludes small businesses
2. **Clay URL coverage** varies - some records have no website
3. **DE has low DOL coverage** due to incorporation vs operational HQ mismatch

### Recommendations
1. Run this pipeline as **supplement** to other enrichment methods
2. Prioritize states with high DOL mid-market density (PA, OH, NC)
3. Use unresolved queue for future paid enrichment batches
4. Consider relaxing ZIP matching to city-level for larger buckets

---

## Reverse Entity Resolution (DOL → URL → Clay)

### Overview

An alternative approach that starts from DOL records, enriches with URLs via web search, then matches to Clay domains. This captures companies that exist in DOL but not in Clay.

### Pilot Results (WV + DE)

| Metric | Value |
|--------|-------|
| DOL records (unmatched to Clay) | 762 |
| Sampled for URL enrichment | 15 |
| URLs found | 14 (93.3%) |
| Matched to Clay | 2 companies |
| Multi-EIN conflicts | 2 (WVU entities) |
| **Net-new prospects** | **11** |

### Key Findings

1. **High URL enrichment success** (93%+) for commercial entities
2. **Many DOL records are union trusts** (~50%) with no commercial website
3. **Multi-EIN conflicts** arise from health systems, holding companies
4. **Net-new prospects** identified: large companies not in Clay (Chemours, Navient, DuPont, etc.)

### Comparison: Forward vs Reverse

| Approach | Direction | Match Rate | Best For |
|----------|-----------|------------|----------|
| **Forward** | Clay → DOL | 0.16% | Enriching existing Clay records with EIN |
| **Reverse** | DOL → Clay | 13.3% | Finding net-new prospects, high-value targets |

### Recommendations

1. **Use reverse approach for prospect discovery** - identifies net-new companies
2. **Filter out union trusts** before enrichment to save time
3. **Handle multi-EIN conflicts manually** - large health systems often have multiple EINs
4. **Export net-new prospects for Clay import** - valuable addition to pipeline

### Database Table

```sql
CREATE TABLE outreach.dol_url_enrichment (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    ein varchar(9) NOT NULL,
    legal_name text NOT NULL,
    dba_name text,
    city text,
    state varchar(2),
    zip varchar(10),
    participants integer,
    enriched_url text,
    search_query text,
    confidence varchar(10),  -- high, medium, low, failed
    matched_company_unique_id text,
    match_status varchar(20),  -- matched, no_clay_match, enrichment_failed, conflict
    created_at timestamptz DEFAULT now()
);
```

---

## Files

| File | Purpose |
|------|---------|
| `scripts/entity_resolution_by_state.cjs` | Forward pipeline (Clay → DOL) |
| `reverse_entity_resolution.cjs` | Reverse pipeline Phase 1 (DOL extraction) |
| `phase3_url_match.cjs` | Reverse pipeline Phase 3 (URL matching) |
| `phase4_persist_reverse.cjs` | Reverse pipeline Phase 4 (persist) |
| `exports/dol_url_enrichment_*.csv` | Enrichment results |
| `exports/dol_url_enrichment_new_prospects_*.csv` | Net-new prospects |
| `outreach.entity_resolution_queue` | Forward pipeline queue |
| `outreach.dol_url_enrichment` | Reverse pipeline tracking |

---

## Audit Trail

| Date | Action | Records | Method |
|------|--------|---------|--------|
| 2026-01-27 | WV/DE Forward Pilot | 6 confirmed, 1 queued | geo_fuzzy_url_verified |
| 2026-01-27 | WV/DE Reverse Pilot | 2 matched, 11 net-new | dol_url_enrichment_verified |

---

*Pipeline validated by Entity Resolution Pilot on 2026-01-27*

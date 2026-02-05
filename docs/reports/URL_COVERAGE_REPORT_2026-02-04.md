# URL Coverage Report: About Us & Press/News Pages
**Date**: February 4, 2026
**Scope**: Outreach companies mapped to company.company_master via domain matching
**Total Outreach Companies**: 96,347

---

## Executive Summary

This report quantifies the availability of **About Us pages** and **Press/News pages** for outreach companies through the company.company_source_urls bridge table. These pages are critical for content analysis and enrichment in the Blog Content sub-hub (04.04.05).

### Key Metrics

| Metric | Count | % of Total |
|--------|-------|-----------|
| Total Outreach Companies | 96,347 | 100.0% |
| With About Us URL | 19,238 | 19.97% |
| With Press/News URL | 9,341 | 9.70% |
| With Either (About OR Press) | 20,710 | 21.50% |
| With BOTH (About AND Press) | 7,868 | 8.17% |
| **Without Either** | **75,637** | **78.50%** |

---

## Detailed Breakdown

### About Us Page Coverage
- **Companies with About Us pages**: 19,238
- **Coverage rate**: 19.97%
- **Gap**: 77,109 companies (80.03%) lack About Us pages in company_source_urls

### Press/News Page Coverage
- **Companies with Press/News pages**: 9,341
- **Coverage rate**: 9.70%
- **Gap**: 87,006 companies (90.30%) lack Press/News pages in company_source_urls

### Combined Coverage
- **Either About or Press**: 20,710 companies (21.50%)
- **Both About and Press**: 7,868 companies (8.17% of total, 37.99% of "either" group)
- **Neither About nor Press**: 75,637 companies (78.50%)

---

## Data Source Architecture

### Query Path: Outreach → Company Master → Source URLs

```
outreach.outreach
    ↓ (domain JOIN)
company.company_master
    ↓ (company_unique_id JOIN)
company.company_source_urls
    ↓ (filter by source_type)
about_page, press_page
```

**Bridge Logic**:
```sql
LOWER(o.domain) = LOWER(
    REPLACE(REPLACE(REPLACE(cm.website_url, 'http://', ''), 'https://', ''), 'www.', '')
)
```

This normalized domain matching connects outreach records to company_source_urls records captured during company enrichment.

---

## Sample URLs

Example companies with About/Press coverage:

| Domain | About URL | Press URL |
|--------|-----------|-----------|
| abss.k12.nc.us | https://www.abss.k12.nc.us/about | https://www.abss.k12.nc.us/press |
| kiwitech.com | https://www.kiwitech.com/about-us | https://www.kiwitech.com/newsroom |
| skofirm.com | https://www.skofirm.com/about/ | (not available) |
| pdri.com | (not available) | http://pdri.com/news/ |

---

## Blog Content Integration

**outreach.blog Table Status**:
- Total blog records: 95,580
- Companies with blog signals: 95,580 (unique outreach_ids)
- Actual About/Press signals in outreach.blog: **0 records**

**Observation**: The outreach.blog table does not currently contain source_type values of 'about_page' or 'press_page'. Blog signals focus on other content types (news, events, signals) rather than About Us or Press pages specifically.

---

## Implications for Content Pipeline

### Blog Content Sub-Hub (04.04.05)

1. **Current URL Coverage**: Only 21.50% of outreach companies have About Us or Press URLs available through company_source_urls
2. **Rich Content Gap**: 75,637 companies (78.50%) lack these strategic content sources
3. **Blog Signal Opportunity**: outreach.blog is fully populated (95,580 records) but does not track About/Press specifically

### For Enrichment Operations

- **Short-term**: Leverage the 20,710 companies with About/Press URLs for content analysis
- **Medium-term**: Expand company_source_urls coverage to capture About/Press pages for the remaining 75,637 companies
- **Long-term**: Consider web crawling or API enrichment services to discover these pages for companies without existing records

---

## Database Tables Referenced

| Table | Schema | Purpose |
|-------|--------|---------|
| outreach.outreach | outreach | Operational spine (96,347 companies) |
| company.company_master | company | Company master records with normalized website_url |
| company.company_source_urls | company | Source URLs indexed by source_type (about_page, press_page) |
| outreach.blog | outreach | Blog content signals (95,580 records, 1:1 with outreach companies) |

---

## Recommendations

1. **Validate Domain Matching**: Confirm the LOWER(domain) JOIN logic captures all intended companies (no false positives/negatives)
2. **Expand URL Coverage**: Consider enrichment workflow to fill gaps in company_source_urls for About/Press pages
3. **Blog Signal Enhancement**: If About/Press pages are strategically important, add source_type tracking to outreach.blog
4. **Quality Gates**: For companies WITH About/Press URLs, verify URL freshness and accessibility

---

## Query Timestamps

All queries executed 2026-02-04 against Neon production database.

```
NEON_HOST: ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech
NEON_DATABASE: Marketing DB
QUERY_EXECUTION_TIME: ~2.3s
```

---

**Report Generated**: 2026-02-04
**Report ID**: URL_COVERAGE_2026-02-04
**Data Freshness**: Live snapshot from Neon

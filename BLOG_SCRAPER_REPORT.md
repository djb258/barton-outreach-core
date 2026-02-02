# Blog Executive Scraper v2 Report

**Execution Date**: 2026-02-02 16:44:47 UTC
**Cost**: $0.00 (FREE)
**Data Source**: company.company_source_urls (97,124 URLs)

## Results

| Metric | Count |
|--------|------:|
| Companies processed | 2,000 |
| URLs available | 3,009 |
| Pages scraped | 2,000 |
| Blog records updated | 1,541 |
| Executives found | 314 |
| - CEO | 280 |
| - CFO | 24 |
| - HR | 10 |
| **Slots filled** | **10** |

## Method

1. Queried company.company_source_urls for discovered leadership/team/about URLs
2. Joined with companies having empty slots in people.company_slot
3. Scraped known URLs (not guessing paths)
4. Extracted "Name, Title" patterns from HTML
5. Classified titles into CEO/CFO/HR
6. Created people_master records
7. Filled empty company_slot records

## URL Priority

1. leadership_page (9,214 available) - Most likely to have executive bios
2. team_page (7,959 available) - Staff listings with titles
3. about_page (24,099 available) - Company overview, sometimes leadership

**Generated**: 2026-02-02T16:44:47.038132+00:00Z

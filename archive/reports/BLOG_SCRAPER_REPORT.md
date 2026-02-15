# Blog Executive Scraper v2 Report

**Execution Date**: 2026-02-02 23:05:02 UTC
**Cost**: $0.00 (FREE)
**Data Source**: company.company_source_urls (97,124 URLs)

## Results

| Metric | Count |
|--------|------:|
| Companies processed | 4,564 |
| URLs available | 7,112 |
| Pages scraped | 4,564 |
| Blog records updated | 34 |
| Executives found | 904 |
| - CEO | 769 |
| - CFO | 117 |
| - HR | 18 |
| **Slots filled** | **0** |

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

**Generated**: 2026-02-02T23:05:02.446827+00:00Z

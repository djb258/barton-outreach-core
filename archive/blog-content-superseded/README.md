# Blog Content Superseded Scripts

**Archived**: 2026-02-20
**Reason**: Phase 3 Legacy Collapse dropped the target tables these scripts write to.

## Scripts

| Script | Dropped Table | Replaced By |
|--------|---------------|-------------|
| `discover_blog_urls.py` | `company.company_source_urls` | `discover_source_urls.py` |
| `discover_company_urls.py` | `company.company_source_urls` | `discover_source_urls.py` |
| `discover_urls_batch.py` | `company.company_source_urls` | `discover_source_urls.py` |
| `discovery_status.py` | `company.company_source_urls` | N/A (status for dropped table) |
| `scan_sitemaps.py` | `outreach.sitemap_discovery` | `discover_source_urls.py` |
| `verify_domains.py` | `outreach.sitemap_discovery` | `discover_source_urls.py` |
| `recover_dead_domains.py` | `outreach.sitemap_discovery` | `discover_source_urls.py` |

## Current Scripts (still in `hubs/blog-content/imo/middle/`)

- `discover_source_urls.py` — Spine-linked URL discovery (outreach.source_urls)
- `scrape_leadership_pages.py` — Leadership page scraping + slot filling

## Data Location

All historical data from these scripts lives in `vendor.blog` (Tier-1 staging):
- `vendor.blog WHERE source_table = 'outreach.sitemap_discovery'` (93,596 rows)
- `vendor.blog WHERE source_table = 'company.company_source_urls'` (114,736 rows)
- `vendor.blog WHERE source_table = 'outreach.source_urls'` (81,292 rows)

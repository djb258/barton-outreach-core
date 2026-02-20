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
| `discover_source_urls.py` | `outreach.source_urls` | N/A (table dropped in Phase 3) |
| `scrape_leadership_pages.py` | `outreach.source_urls` | N/A (reads from dropped table) |

## Current Scripts (still in `hubs/blog-content/imo/middle/`)

- `classify_event.py`, `extract_entities.py`, `parse_content.py`, `validate_signal.py`, `match_company.py`, `hub_status.py` — Blog content processing pipeline

## Data Location

All historical data from these scripts lives in `vendor.blog` (Tier-1 staging):
- `vendor.blog WHERE source_table = 'outreach.sitemap_discovery'` (93,596 rows)
- `vendor.blog WHERE source_table = 'company.company_source_urls'` (114,736 rows)
- `vendor.blog WHERE source_table = 'outreach.source_urls'` (81,292 rows)

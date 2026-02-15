# Blog Executive Scraper

**Location**: `scripts/blog_executive_scraper.py`
**Cost**: FREE ($0.00)
**Purpose**: Extract executive names from company websites to fill empty people slots

---

## Overview

This script scrapes company websites (About Us, Team, Leadership pages) to extract executive names and titles. It uses **already-discovered URLs** from `company.company_source_urls` rather than guessing paths.

## Data Flow

```
company.company_source_urls (97,124 URLs)
         ↓
    Scrape HTML content
         ↓
    Extract "Name, Title" patterns
         ↓
    Classify into CEO/CFO/HR
         ↓
    Create people.people_master records
         ↓
    Fill people.company_slot records
```

## URL Sources

| Source Type | Count | Priority |
|-------------|------:|:--------:|
| leadership_page | 9,214 | 1 (best) |
| team_page | 7,959 | 2 |
| about_page | 24,099 | 3 |

## Title Patterns Recognized

### CEO Slot
- CEO, Chief Executive Officer
- President, Founder, Co-Founder, Owner
- Managing Director

### CFO Slot
- CFO, Chief Financial Officer
- Finance Director, VP Finance
- Controller, Treasurer

### HR Slot
- CHRO, Chief Human Resources Officer
- Chief People Officer
- HR Director, VP HR, Head of HR
- Benefits Director, People Operations Director

## Execution

```bash
# Standard run (processes up to 20,000 companies)
doppler run -- python scripts/blog_executive_scraper.py

# The script automatically:
# - Skips companies already processed (have blog content)
# - Uses parallel processing (5 workers, batches of 10)
# - Commits after each batch
```

## Database Tables Affected

### Reads From
- `people.company_slot` - Find empty slots
- `cl.company_identity` - Get company domains
- `company.company_master` - Bridge to doctrine IDs
- `company.company_source_urls` - Get discovered URLs
- `outreach.blog` - Check if already processed

### Writes To
- `people.people_master` - Creates executive records
- `people.company_slot` - Fills slots with person_unique_id
- `outreach.blog` - Stores scraped content summary

## ID Format Requirements

The script generates Barton-format IDs required by `people.people_master`:

| Field | Format | Example |
|-------|--------|---------|
| unique_id | 04.04.02.99.{seq}.{last3} | 04.04.02.99.120000.000 |
| company_unique_id | 04.04.01.XX.XXXXX.XXX | 04.04.01.37.00001.893 |
| company_slot_unique_id | 04.04.05.99.{seq}.{last3} | 04.04.05.99.120000.000 |

## Output

### Console Output
```
[timestamp] [INFO] Companies processed: 2,000
[timestamp] [INFO] Executives found: 314
[timestamp] [INFO]   - CEO: 280
[timestamp] [INFO]   - CFO: 24
[timestamp] [INFO]   - HR: 10
[timestamp] [INFO] Slots filled: 11
```

### Report File
Written to: `BLOG_SCRAPER_REPORT.md`

## Performance

- ~2,000 companies in ~25 minutes
- Parallel scraping (5 concurrent HTTP requests)
- Batch commits every 10 companies

## Rerun Behavior

- **Safe to rerun**: Skips companies with existing blog content
- **Idempotent**: ON CONFLICT DO NOTHING on people_master inserts
- **Incremental**: Only processes new/unprocessed companies

## Troubleshooting

### "No companies with URLs to process"
- All eligible companies already have blog content
- Check: `SELECT COUNT(*) FROM outreach.blog WHERE context_summary IS NOT NULL`

### Low slot fill rate
- Most executives found are for companies with slots already filled
- The scraper finds executives but the matching slot may be occupied
- Consider running on companies with ALL slots empty

### NUL character errors
- Handled automatically (content sanitized before DB insert)

## Related Documentation

- `docs/ERROR_REMEDIATION_TOOLBOX.md` - Tool waterfall for error resolution
- `docs/OUTREACH_WATERFALL_DOCTRINE.md` - Hub relationships
- `hubs/blog-content/SCHEMA.md` - Blog hub schema

---

**Created**: 2026-02-02
**Author**: Claude Code
**Last Run**: See `BLOG_SCRAPER_REPORT.md`

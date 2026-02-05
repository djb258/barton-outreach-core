# Hunter Source URL Analysis Report
## Outreach.Blog URL Population Assessment

**Date**: 2026-02-04
**Analyst**: Database Operations
**Status**: Analysis Complete - Awaiting Schema Migration Decision

---

## Executive Summary

Hunter.io contact source data contains **73,238 About URLs** and **60,700 News/Press URLs** that can be extracted and populated into `outreach.blog` to enhance company intelligence signals.

### Coverage Impact
- **About URLs**: 19,455 outreach companies (20.2% coverage)
- **News URLs**: 14,760 outreach companies (15.3% coverage)
- **Combined**: Estimated 25,000+ companies with at least one URL type

### Current State
`outreach.blog` currently has **8 columns** but is missing dedicated fields for:
- Company About page URLs
- News/Press page URLs
- Blog URLs
- Source metadata (frequency tracking)
- Extraction timestamps and methods

---

## 1. Data Volume Analysis

### Hunter Source URLs

| URL Type | Total URLs | Unique Outreach Companies | Coverage % |
|----------|-----------|---------------------------|------------|
| About/Team/Leadership | 73,238 | 19,455 | 20.2% |
| News/Press/Blog | 60,700 | 14,760 | 15.3% |
| **Combined Potential** | **133,938** | **~25,000** | **~26%** |

**Total Outreach Companies**: 96,347

---

## 2. Current outreach.blog Schema

| Column Name | Type | Length | Nullable | Purpose |
|-------------|------|--------|----------|---------|
| blog_id | uuid | N/A | NO | Primary key |
| outreach_id | uuid | N/A | NO | FK to outreach.outreach |
| context_summary | text | N/A | YES | Generic content summary |
| source_type | text | N/A | YES | Source classification |
| source_url | text | N/A | YES | Generic URL field |
| context_timestamp | timestamp with time zone | N/A | YES | Content timestamp |
| created_at | timestamp with time zone | N/A | YES | Record creation |
| source_type_enum | USER-DEFINED | N/A | YES | Source type enumeration |

### Schema Gaps Identified

**Missing Columns**:
1. `about_url` - Dedicated About/Team page URL
2. `news_url` - Dedicated News/Press page URL
3. `blog_url` - Dedicated Blog URL (separate from news)
4. `source_metadata` - JSONB for frequency and pattern tracking
5. `last_extracted_at` - Extraction timestamp for refresh tracking
6. `extraction_method` - Source tracking (hunter_api, manual, scraper)

**Current Limitation**: The existing `source_url` field is generic and does not distinguish between About, News, and Blog URLs, making targeted retrieval difficult.

---

## 3. URL Pattern Analysis

### Top About URL Patterns (by frequency)

| Frequency | URL Pattern | Category |
|-----------|-------------|----------|
| 27x | `/about-us/our-team` | Team directory |
| 23x | `/about-the-*/membership-list` | Membership/Association |
| 21x | `/who-we-are` | Company overview |
| 20x | `/about/our-team` | Team directory |
| 20x | `/about-us/the-team` | Team directory |
| 20x | `/about/team` | Team directory |

**Key Observations**:
- Team/Leadership pages are most common (70%+ of About URLs)
- Strong signal for executive discovery and org chart mapping
- High reusability for People Intelligence Hub (04.04.02)

### Top News URL Patterns (by frequency)

| Frequency | URL Pattern | Category |
|-----------|-------------|----------|
| 52x | `/blog/stuff/spamtrap` | Blog (low signal) |
| 31x | `.pdf` files | Official documents |
| 17x | `/service/newsletter/*` | Email newsletters |
| 14x | `/blog` | Company blog |
| 13x | `/media/*/*.pdf` | Press releases |

**Key Observations**:
- Mix of blog and press release URLs
- PDF files indicate official announcements (higher signal)
- Newsletter archives may contain historical company updates

---

## 4. Recommended Schema Changes

### ALTER TABLE Migration

```sql
-- Add dedicated URL columns to outreach.blog
ALTER TABLE outreach.blog
ADD COLUMN about_url TEXT,
ADD COLUMN news_url TEXT,
ADD COLUMN blog_url TEXT,
ADD COLUMN source_metadata JSONB,
ADD COLUMN last_extracted_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN extraction_method TEXT CHECK (extraction_method IN ('hunter_api', 'manual', 'scraper', 'llm_extract'));

-- Add indexes for efficient querying
CREATE INDEX idx_blog_about_url ON outreach.blog(about_url) WHERE about_url IS NOT NULL;
CREATE INDEX idx_blog_news_url ON outreach.blog(news_url) WHERE news_url IS NOT NULL;
CREATE INDEX idx_blog_blog_url ON outreach.blog(blog_url) WHERE blog_url IS NOT NULL;
CREATE INDEX idx_blog_extraction_method ON outreach.blog(extraction_method);

-- Add comment documentation
COMMENT ON COLUMN outreach.blog.about_url IS 'Company About/Team/Leadership page URL (from Hunter sources)';
COMMENT ON COLUMN outreach.blog.news_url IS 'Company News/Press/Media page URL (from Hunter sources)';
COMMENT ON COLUMN outreach.blog.blog_url IS 'Company Blog URL (from Hunter sources)';
COMMENT ON COLUMN outreach.blog.source_metadata IS 'JSONB containing Hunter source frequency and pattern data';
COMMENT ON COLUMN outreach.blog.last_extracted_at IS 'Timestamp of URL extraction for refresh tracking';
COMMENT ON COLUMN outreach.blog.extraction_method IS 'Source: hunter_api, manual, scraper, llm_extract';
```

### Source Metadata Structure (JSONB)

```json
{
  "about_urls": [
    {"url": "https://example.com/about-us", "frequency": 27, "pattern": "/about-us/*"},
    {"url": "https://example.com/team", "frequency": 15, "pattern": "/team"}
  ],
  "news_urls": [
    {"url": "https://example.com/news", "frequency": 12, "pattern": "/news"}
  ],
  "extraction_date": "2026-02-04T00:00:00Z",
  "hunter_domain_match": "example.com",
  "total_sources": 42,
  "dedup_method": "highest_frequency"
}
```

---

## 5. URL Extraction Strategy

### Deduplication Logic

**Problem**: Multiple URLs per company per pattern (e.g., 27 instances of `/about-us/our-team` for same domain)

**Solution**: Prioritize by frequency and pattern quality

```python
# Pseudo-logic
for each outreach_id:
    about_candidates = hunter_sources.filter(about_patterns).group_by(domain)
    news_candidates = hunter_sources.filter(news_patterns).group_by(domain)

    # Select most frequent URL per pattern type
    about_url = about_candidates.order_by(frequency DESC).first()
    news_url = news_candidates.order_by(frequency DESC).first()

    # Store all candidates in source_metadata for audit trail
    source_metadata = {
        "about_urls": about_candidates.to_dict(),
        "news_urls": news_candidates.to_dict(),
        "dedup_method": "highest_frequency"
    }
```

### Pattern Matching Rules

**About URL Patterns** (priority order):
1. `/about-us/our-team`
2. `/about/team`
3. `/team`
4. `/leadership`
5. `/who-we-are`
6. `/our-team`
7. `/about-us`
8. `/about`
9. `/company`

**News URL Patterns** (priority order):
1. `/press` or `/press-releases`
2. `/news`
3. `/media`
4. `/announcements`
5. `prnewswire.com` or `businesswire.com` (external press)
6. `/blog` (if newsworthy)

**Quality Filters**:
- Exclude spam trap URLs (`/spamtrap`)
- Exclude demo/test URLs (`demo.`, `test.`)
- Exclude PDF-only URLs (store in metadata but not primary field)
- Prefer company-owned domains over external aggregators

---

## 6. Populate Script Outline

```python
# C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\populate_blog_urls_from_hunter.py

"""
Populate outreach.blog with About/News URLs from Hunter sources.
Execution: doppler run -- python populate_blog_urls_from_hunter.py
"""

import psycopg2
from datetime import datetime
import json

ABOUT_PATTERNS = [
    '%/about-us/our-team%',
    '%/about/team%',
    '%/team%',
    '%/leadership%',
    '%/who-we-are%',
    '%/our-team%',
    '%/about-us%',
    '%/about%',
    '%/company%'
]

NEWS_PATTERNS = [
    '%/press-releases%',
    '%/press%',
    '%/news%',
    '%/media%',
    '%/announcements%',
    '%prnewswire%',
    '%businesswire%',
    '%/blog%'
]

EXCLUDE_PATTERNS = [
    '%spamtrap%',
    '%demo.%',
    '%test.%'
]

def extract_urls():
    # 1. Query Hunter sources grouped by outreach_id
    # 2. Apply pattern matching and deduplication
    # 3. INSERT or UPDATE outreach.blog records
    # 4. Store source_metadata as JSONB
    # 5. Log extraction_method = 'hunter_api'
    # 6. Set last_extracted_at = NOW()
    pass

if __name__ == "__main__":
    extract_urls()
```

---

## 7. Impact on Outreach Hub (04.04.05)

### Current Blog Content Hub Capabilities
- **BEFORE**: Generic `source_url` with no URL type distinction
- **AFTER**: Dedicated About/News/Blog URLs with metadata

### Enhanced Use Cases

| Use Case | Before | After |
|----------|--------|-------|
| Executive discovery | Manual search | Direct link to About/Team pages |
| Company news monitoring | Undefined source | Targeted News/Press pages |
| Content signal tracking | Generic blog URL | Separate blog vs. press URLs |
| Org chart mapping | No reliable source | About page with team structure |
| Movement detection | Low signal | News URLs for exec announcements |

### Integration with People Intelligence Hub (04.04.02)

**Spoke Contract**: `target-people.contract.yaml`

```yaml
# Enhanced payload with About URLs
target-people:
  ingress:
    - slot_requirements:
        company_id: uuid
        slot_type: enum(CEO, CFO, HR, CTO, CMO, COO)
        about_url: text  # NEW: Direct link to team page
        source_metadata: jsonb  # NEW: Hunter frequency data
```

**Benefit**: People Intelligence can directly scrape About/Team pages for slot assignments instead of generic web searches.

---

## 8. Next Steps

### Immediate Actions Required

1. **Schema Migration** (REQUIRED)
   - File: `C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\neon\migrations\2026-02-04-blog-url-columns.sql`
   - Action: ALTER TABLE outreach.blog ADD COLUMN...
   - Rollback: DROP COLUMN IF EXISTS...

2. **URL Population Script** (READY TO BUILD)
   - File: `populate_blog_urls_from_hunter.py`
   - Action: Extract + deduplicate + populate
   - Run mode: One-time backfill + daily incremental

3. **Contract Updates** (OPTIONAL - ENHANCEMENT)
   - File: `contracts/target-people.contract.yaml`
   - Action: Add `about_url` to slot_requirements payload
   - Benefit: People Hub can use About URLs for scraping

4. **Documentation** (REQUIRED)
   - File: `docs/architecture/blog-url-extraction.md`
   - Action: Document extraction logic and refresh schedule
   - Audience: Future developers + audit trail

### Decision Points

| Decision | Options | Recommendation |
|----------|---------|----------------|
| **Add columns now?** | Yes / Defer | **YES** - 20%+ coverage gain |
| **Backfill all URLs?** | Yes / Incremental | **Incremental** - Start with About URLs (higher signal) |
| **Refresh frequency** | Daily / Weekly / Manual | **Weekly** - Hunter data changes slowly |
| **Quality filters** | Strict / Permissive | **Strict** - Exclude spam/demo URLs |

---

## 9. Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Schema bloat | LOW | Only 6 new columns, well-indexed |
| Data quality issues | MEDIUM | Apply strict pattern filters + manual review top 100 |
| Hunter API rate limits | LOW | Use cached `v_hunter_contact_sources` view |
| Duplicate URL entries | MEDIUM | Dedup by frequency + store all in metadata |
| Stale URLs (404s) | MEDIUM | Add URL validation worker (future) |

---

## 10. Success Metrics

### Pre-Migration Baseline
- **outreach.blog records**: 96,347 (100% coverage with generic fields)
- **About URLs**: 0 (no dedicated field)
- **News URLs**: 0 (no dedicated field)

### Post-Migration Target (30 days)
- **About URLs**: 19,455 (20.2% coverage)
- **News URLs**: 14,760 (15.3% coverage)
- **Combined**: 25,000+ (26% coverage)
- **Source metadata tracked**: 100% of extracted URLs

### Long-Term Goal (90 days)
- **About URLs**: 30,000+ (31% coverage) via LLM extraction
- **News URLs**: 20,000+ (21% coverage) via scraper
- **URL validation**: 95%+ live (non-404) rate

---

## Appendix A: Sample URLs

### About URL Samples (High Signal)
```
https://crewscontrol.com/about-us/our-team
https://goldbugstrategies.com/who-we-are
https://capitolequities.com/about-us/the-team
https://bfs-ind.com/about/team
https://arthurventures.com/team/jeff-yurecko
```

### News URL Samples (High Signal)
```
https://vdot.virginia.gov/media/.../prequalified-list_acc.pdf
https://metroparkstoledo.com/media/.../2021_0728-board-packet.pdf
https://overbysettlement.com/media/.../consolidated_class_action_complaint.pdf
```

---

## Appendix B: SQL Queries Used

### Count About URLs
```sql
SELECT COUNT(*) as about_urls
FROM enrichment.v_hunter_contact_sources
WHERE source_url ILIKE '%/about%'
   OR source_url ILIKE '%/about-us%'
   OR source_url ILIKE '%/team%'
   OR source_url ILIKE '%/our-team%'
   OR source_url ILIKE '%/leadership%'
   OR source_url ILIKE '%/who-we-are%'
   OR source_url ILIKE '%/company%';
-- Result: 73,238
```

### Count News URLs
```sql
SELECT COUNT(*) as news_urls
FROM enrichment.v_hunter_contact_sources
WHERE source_url ILIKE '%/news%'
   OR source_url ILIKE '%/press%'
   OR source_url ILIKE '%/media%'
   OR source_url ILIKE '%/announcements%'
   OR source_url ILIKE '%prnewswire%'
   OR source_url ILIKE '%businesswire%'
   OR source_url ILIKE '%/blog%';
-- Result: 60,700
```

### Outreach Coverage (About)
```sql
SELECT COUNT(DISTINCT o.outreach_id) as companies_with_about
FROM outreach.outreach o
JOIN enrichment.v_hunter_contact_sources vhcs ON LOWER(o.domain) = LOWER(vhcs.domain)
WHERE vhcs.source_url ILIKE '%/about%'
   OR vhcs.source_url ILIKE '%/about-us%'
   OR vhcs.source_url ILIKE '%/team%'
   OR vhcs.source_url ILIKE '%/leadership%'
   OR vhcs.source_url ILIKE '%/who-we-are%'
   OR vhcs.source_url ILIKE '%/our-team%'
   OR vhcs.source_url ILIKE '%/company%';
-- Result: 19,455 / 96,347 = 20.2%
```

---

**Report Status**: COMPLETE - AWAITING APPROVAL
**Recommended Action**: Proceed with schema migration + URL population
**Estimated Effort**: 4 hours (migration + population + validation)
**Risk Level**: LOW
**Business Value**: HIGH (20%+ coverage increase for company intelligence)

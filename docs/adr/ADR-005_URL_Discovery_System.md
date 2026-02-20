# ADR: Company URL Discovery System for Blog Content Hub

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | 1.1.0 |
| **CC Layer** | CC-03 |

---

## ADR Identity

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-005 |
| **Status** | [x] Accepted |
| **Date** | 2026-01-18 |

---

## Owning Hub (CC-02)

| Field | Value |
|-------|-------|
| **Sovereign ID** | BARTON-OUTREACH |
| **Hub Name** | Blog Content Sub-Hub |
| **Hub ID** | HUB-BC-001 |

---

## CC Layer Scope

| Layer | Affected | Description |
|-------|----------|-------------|
| CC-01 (Sovereign) | [ ] | No sovereign-level changes |
| CC-02 (Hub) | [x] | PRD updated with URL discovery capability |
| CC-03 (Context) | [x] | URL discovery process, source cataloging |
| CC-04 (Process) | [x] | Batch discovery scripts, parallel processing |

---

## IMO Layer Scope

| Layer | Affected |
|-------|----------|
| I — Ingress | [x] | Company website URL input |
| M — Middle | [x] | URL probing, page discovery, deduplication |
| O — Egress | [x] | company_source_urls table, url_discovery_failures table |

---

## Constant vs Variable

| Classification | Value |
|----------------|-------|
| **This decision defines** | [x] Constant (structure/meaning) |
| **Mutability** | [x] Mutable (URLs can be re-checked, failures retried) |

---

## Context

The Blog Content Sub-Hub needed a way to:

1. **Catalog company URLs** - Identify pages where executive information can be found
2. **Track news sources** - Know where to monitor for company news/events
3. **Enable future extraction** - Prepare URLs for later executive and signal extraction

Previous state:
- No system to discover or catalog company web pages
- No tracking of failed discovery attempts
- Manual URL identification required

---

## Decision

### 1. Create Company Source URLs Table

Store discovered URLs linked directly to `company_unique_id`:

```sql
CREATE TABLE company.company_source_urls (
    source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_unique_id TEXT NOT NULL,
    source_type VARCHAR(50) NOT NULL,  -- leadership_page, about_page, etc.
    source_url TEXT NOT NULL,
    page_title TEXT,
    discovered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    discovered_from VARCHAR(100),  -- crawl, manual, rss, newsapi
    last_checked_at TIMESTAMPTZ,
    http_status INTEGER,
    is_accessible BOOLEAN DEFAULT TRUE,
    extraction_status VARCHAR(50) DEFAULT 'pending',
    UNIQUE(company_unique_id, source_url)
);
```

### 2. Define Source Types

| Source Type | Purpose | Extraction Target |
|-------------|---------|-------------------|
| leadership_page | Executive bios | People slots (CEO, CFO, etc.) |
| about_page | Company overview | Company context |
| team_page | Staff listings | People discovery |
| press_page | News/announcements | Timing signals |
| careers_page | Job postings | Expansion signals |
| contact_page | Contact info | Address verification |

### 3. Implement Parallel Batch Discovery

Process 73,000+ companies efficiently:
- Chunk-based processing (200 companies per chunk)
- 25 parallel workers per chunk
- 5-second timeout per URL probe
- State-by-state parallel execution

### 4. Track Discovery Failures

Create failure tracking for retry and enrichment:

```sql
CREATE TABLE company.url_discovery_failures (
    failure_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_unique_id TEXT NOT NULL,
    website_url TEXT,
    failure_reason VARCHAR(100) NOT NULL,
    retry_count INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMPTZ,
    next_retry_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    UNIQUE(company_unique_id)
);
```

---

## Alternatives Considered

| Option | Why Not Chosen |
|--------|----------------|
| Sequential processing | Too slow for 73K companies (24+ hours) |
| External crawling service | Cost prohibitive, data ownership concerns |
| Only process on-demand | Delays future extraction, no baseline |
| Skip failure tracking | Loses visibility into enrichment gaps |

---

## Consequences

### Enables

- 97,124 URLs cataloged across 30,771 companies
- 9,214 leadership pages ready for executive extraction
- 14,377 press pages ready for signal monitoring
- Parallel processing across 9 target states
- Retry mechanism for 42,348 failed companies

### Prevents

- Duplicate URL probing (UNIQUE constraint)
- Lost work on failed companies (failure table)
- Sequential bottlenecks (parallel architecture)

---

## Results

### URL Discovery Statistics

| Metric | Value |
|--------|-------|
| Total Companies with Websites | 73,119 |
| Companies with URLs Discovered | 30,771 (42.1%) |
| Total URLs Discovered | 97,124 |
| Average URLs per Company | 3.2 |
| Companies Failed (logged for retry) | 42,348 |

### URLs by Type

| Type | Count |
|------|-------|
| contact_page | 25,213 |
| about_page | 24,099 |
| careers_page | 16,262 |
| press_page | 14,377 |
| leadership_page | 9,214 |
| team_page | 7,959 |

### Processing Time

| State | Companies | Duration |
|-------|-----------|----------|
| All 9 states (parallel) | 73,119 | ~4 hours |

---

## Guard Rails

| Type | Value | CC Layer |
|------|-------|----------|
| Timeout | 5 seconds per URL probe | CC-04 |
| Chunk Size | 200 companies per batch | CC-04 |
| Workers | 25 parallel per chunk | CC-04 |
| Deduplication | UNIQUE(company_unique_id, source_url) | CC-03 |

---

## Rollback

If this decision fails:

1. Drop the tables:
   ```sql
   DROP TABLE company.company_source_urls;
   DROP TABLE company.url_discovery_failures;
   ```

2. Remove discovery scripts from `hubs/blog-content/imo/middle/`

---

## Traceability

| Artifact | Reference |
|----------|-----------|
| Canonical Doctrine | CANONICAL_ARCHITECTURE_DOCTRINE.md |
| PRD | hubs/blog-content/PRD.md (v2.0) |
| Work Items | URL-DISCOVERY-001 |

### Files Created (SUPERSEDED 2026-02-20)

| File | Purpose | Status |
|------|---------|--------|
| `hubs/blog-content/imo/middle/discover_company_urls.py` | Sequential URL discovery | ARCHIVED to `archive/blog-content-superseded/` |
| `hubs/blog-content/imo/middle/discover_urls_batch.py` | Parallel batch discovery | ARCHIVED to `archive/blog-content-superseded/` |
| `hubs/blog-content/imo/middle/discovery_status.py` | Progress monitoring | ARCHIVED to `archive/blog-content-superseded/` |

**Current replacement**: `hubs/blog-content/imo/middle/discover_source_urls.py` (spine-linked, writes to `outreach.source_urls`)

### Tables Created (MIGRATED 2026-02-20)

| Table | Purpose | Status |
|-------|---------|--------|
| `company.company_source_urls` | Discovered URLs storage | Data migrated to `vendor.blog`, table DROPPED |
| `company.url_discovery_failures` | Failed discovery tracking | DROPPED |

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner (CC-02) | Blog Content Sub-Hub | 2026-01-18 |
| Reviewer | Claude Code | 2026-01-18 |

---

*ADR Version: 1.0*
*Created: 2026-01-18*
*CC Layer: CC-03*

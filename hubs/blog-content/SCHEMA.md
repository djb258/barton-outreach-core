# Blog Content Hub — Database Schema

## Tables

### company.company_source_urls

Stores discovered URLs linked to companies for future extraction.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| source_id | UUID | NO | Primary key |
| company_unique_id | TEXT | NO | FK to company_master |
| source_type | VARCHAR(50) | NO | Page type (leadership_page, about_page, etc.) |
| source_url | TEXT | NO | Full URL |
| page_title | TEXT | YES | Extracted page title |
| discovered_at | TIMESTAMPTZ | NO | When URL was discovered |
| discovered_from | VARCHAR(100) | YES | Discovery method (crawl, manual, rss) |
| last_checked_at | TIMESTAMPTZ | YES | Last accessibility check |
| http_status | INTEGER | YES | Last HTTP status code |
| is_accessible | BOOLEAN | YES | Current accessibility |
| content_checksum | TEXT | YES | Content hash for change detection |
| last_content_change_at | TIMESTAMPTZ | YES | When content last changed |
| extraction_status | VARCHAR(50) | YES | pending/extracted/failed |
| extracted_at | TIMESTAMPTZ | YES | When content was extracted |
| created_at | TIMESTAMPTZ | YES | Record creation time |
| updated_at | TIMESTAMPTZ | YES | Record update time |

**Constraints:**
- PRIMARY KEY: source_id
- UNIQUE: (company_unique_id, source_url)
- INDEX: company_unique_id
- INDEX: source_type

---

### company.url_discovery_failures

Tracks companies where URL discovery failed for retry.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| failure_id | UUID | NO | Primary key |
| company_unique_id | TEXT | NO | FK to company_master |
| website_url | TEXT | YES | Company website URL |
| failure_reason | VARCHAR(100) | NO | Reason code |
| retry_count | INTEGER | YES | Number of retry attempts |
| last_attempt_at | TIMESTAMPTZ | YES | Last discovery attempt |
| next_retry_at | TIMESTAMPTZ | YES | Scheduled retry time |
| resolved_at | TIMESTAMPTZ | YES | When issue was resolved |
| created_at | TIMESTAMPTZ | YES | Record creation time |

**Constraints:**
- PRIMARY KEY: failure_id
- UNIQUE: company_unique_id

---

## Source Types

| Type | Description | Extraction Use |
|------|-------------|----------------|
| leadership_page | Executive team pages | CEO, CFO, CTO extraction |
| about_page | Company overview | Context, history |
| team_page | Full team listings | All staff discovery |
| press_page | News, press releases | Timing signals |
| careers_page | Job listings | Expansion signals |
| contact_page | Contact information | Address verification |

---

## Failure Reasons

| Reason | Description |
|--------|-------------|
| no_pages_discovered | Base URL accessible but no sub-pages found |
| base_url_timeout | Company website did not respond |
| base_url_error | HTTP error on base URL |
| invalid_domain | Domain does not resolve |

---

## Statistics (2026-01-18)

| Metric | Value |
|--------|-------|
| Total URLs | 97,124 |
| Companies with URLs | 30,771 |
| Failed Companies | 42,348 |
| Avg URLs/Company | 3.2 |

### By Source Type

| Type | Count |
|------|-------|
| contact_page | 25,213 |
| about_page | 24,099 |
| careers_page | 16,262 |
| press_page | 14,377 |
| leadership_page | 9,214 |
| team_page | 7,959 |

---

## ERD

```
┌─────────────────────────────────┐
│     company.company_master      │
├─────────────────────────────────┤
│ company_unique_id (PK)          │
│ company_name                    │
│ website_url                     │
│ ...                             │
└───────────────┬─────────────────┘
                │
                │ 1:N
                ▼
┌─────────────────────────────────┐
│   company.company_source_urls   │
├─────────────────────────────────┤
│ source_id (PK)                  │
│ company_unique_id (FK)          │◄──┐
│ source_type                     │   │
│ source_url                      │   │
│ page_title                      │   │
│ discovered_at                   │   │
│ extraction_status               │   │
│ ...                             │   │
└─────────────────────────────────┘   │
                                      │
┌─────────────────────────────────┐   │
│ company.url_discovery_failures  │   │
├─────────────────────────────────┤   │
│ failure_id (PK)                 │   │
│ company_unique_id (FK) ─────────┼───┘
│ website_url                     │
│ failure_reason                  │
│ retry_count                     │
│ ...                             │
└─────────────────────────────────┘
```

---

**Last Updated**: 2026-01-18

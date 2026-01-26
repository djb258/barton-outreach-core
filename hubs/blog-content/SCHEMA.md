# Blog Content Hub — Database Schema

## Tables

### blog.pressure_signals (BIT v2.0)

**AI-Ready Data Metadata (per Canonical Architecture Doctrine §12):**

| Field | Value |
|-------|-------|
| `table_unique_id` | `TBL-BLOG-PRESSURE-001` |
| `owning_hub_unique_id` | `HUB-BLOG-001` |
| `owning_subhub_unique_id` | `SUBHUB-BLOG-001` |
| `description` | NARRATIVE_VOLATILITY domain signals for BIT authorization. Lowest trust level - amplifier only, Blog alone = max Band 1. |
| `source_of_truth` | Blog Hub processing (news mentions, funding announcements, content signals) |
| `row_identity_strategy` | UUID primary key (signal_id) |

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `signal_id` | uuid | NOT NULL | gen_random_uuid() | Primary key - unique signal identifier |
| `company_unique_id` | text | NOT NULL | - | Company reference |
| `signal_type` | varchar(50) | NOT NULL | - | Signal classification (funding_announcement, news_mention, growth_indicator) |
| `pressure_domain` | enum | NOT NULL | 'NARRATIVE_VOLATILITY' | Domain constraint (always NARRATIVE_VOLATILITY for Blog) |
| `pressure_class` | enum | NULL | - | Pressure classification |
| `signal_value` | jsonb | NOT NULL | '{}' | Domain-specific payload with evidence |
| `magnitude` | integer | NOT NULL | 0 | Impact score (0-100) |
| `detected_at` | timestamptz | NOT NULL | now() | When signal was detected |
| `expires_at` | timestamptz | NOT NULL | - | Validity window end |
| `correlation_id` | uuid | NULL | - | PID binding / trace ID |
| `source_record_id` | text | NULL | - | Traceability (e.g., news_id) |
| `created_at` | timestamptz | NOT NULL | now() | Record creation time |

**Column Metadata (per §12.3):**

| Column | column_unique_id | semantic_role | format |
|--------|------------------|---------------|--------|
| `signal_id` | COL-BLOG-PS-001 | identifier | UUID |
| `company_unique_id` | COL-BLOG-PS-002 | foreign_key | TEXT |
| `signal_type` | COL-BLOG-PS-003 | attribute | ENUM |
| `pressure_domain` | COL-BLOG-PS-004 | attribute | ENUM |
| `pressure_class` | COL-BLOG-PS-005 | attribute | ENUM |
| `signal_value` | COL-BLOG-PS-006 | attribute | JSON |
| `magnitude` | COL-BLOG-PS-007 | metric | INTEGER |
| `detected_at` | COL-BLOG-PS-008 | attribute | ISO-8601 |
| `expires_at` | COL-BLOG-PS-009 | attribute | ISO-8601 |
| `correlation_id` | COL-BLOG-PS-010 | identifier | UUID |
| `source_record_id` | COL-BLOG-PS-011 | foreign_key | TEXT |
| `created_at` | COL-BLOG-PS-012 | attribute | ISO-8601 |

**Trust Cap:** Blog alone = max Band 1 (WATCH). Never sufficient for contact authorization.

**Authority:** ADR-017
**Migration:** `neon/migrations/2026-01-26-bit-v2-phase1-distributed-signals.sql`

---

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

```mermaid
erDiagram
    COMPANY_COMPANY_MASTER ||--o{ COMPANY_COMPANY_SOURCE_URLS : "company_unique_id"
    COMPANY_COMPANY_MASTER ||--o| COMPANY_URL_DISCOVERY_FAILURES : "company_unique_id"
    COMPANY_COMPANY_MASTER ||--o{ BLOG_PRESSURE_SIGNALS : "company_unique_id"

    COMPANY_COMPANY_MASTER {
        text company_unique_id PK
        text company_name
        text website_url
    }

    COMPANY_COMPANY_SOURCE_URLS {
        uuid source_id PK
        text company_unique_id FK
        varchar source_type
        text source_url
        text page_title
        timestamptz discovered_at
        varchar extraction_status
    }

    COMPANY_URL_DISCOVERY_FAILURES {
        uuid failure_id PK
        text company_unique_id FK
        text website_url
        varchar failure_reason
        int retry_count
    }

    BLOG_PRESSURE_SIGNALS {
        uuid signal_id PK
        text company_unique_id FK
        varchar signal_type
        enum pressure_domain
        enum pressure_class
        jsonb signal_value
        int magnitude
        timestamptz detected_at
        timestamptz expires_at
        uuid correlation_id
        text source_record_id
    }
```

---

**Last Updated**: 2026-01-18

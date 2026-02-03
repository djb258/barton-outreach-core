# Authoritative Table Reference

> **Last Updated:** 2026-02-02  
> **Status:** CANONICAL - This document defines the single source of truth

---

## ⚠️ CRITICAL: Read This First

**ALL WORK in this repository MUST use `outreach.company_target` as the authoritative company list.**

Do NOT use:
- ❌ `company.company_master` (74,641 records) - Too broad
- ❌ `people.people_master` (78,143 records) - People table, not companies
- ❌ Any other company table

---

## The Authoritative Table

### `outreach.company_target`

| Attribute | Value |
|-----------|-------|
| **Schema** | `outreach` |
| **Table** | `company_target` |
| **Record Count** | 41,425 |
| **Source** | Clay (CL) exports |
| **Primary Key** | `outreach_id` |

This table represents the **curated, qualified companies** that we are actively targeting for outreach. It is populated from Clay workflows and represents our actual prospect universe.

---

## Key Relationships

```
outreach.company_target (41,425)
    ├── outreach_id (PRIMARY KEY)
    │
    ├──→ people.company_slot (JOIN on outreach_id)
    │       └── Slot assignments: CEO, CFO, HR
    │       └── Links to person_unique_id when filled
    │
    ├──→ outreach.people (JOIN on outreach_id)
    │       └── People promoted for outreach
    │
    └──→ outreach.outreach (JOIN on outreach_id)
            └── Outreach activity records
```

---

## Correct Queries

### ✅ Get company count
```sql
SELECT COUNT(*) FROM outreach.company_target;
-- Returns: 41,425
```

### ✅ Get slot coverage
```sql
SELECT 
    slot_type,
    COUNT(*) FILTER (WHERE is_filled) as filled,
    COUNT(*) as total
FROM people.company_slot cs
JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
GROUP BY slot_type;
```

### ✅ Get people for outreach
```sql
SELECT p.*, ct.company_name
FROM outreach.people p
JOIN outreach.company_target ct ON p.outreach_id = ct.outreach_id;
```

### ❌ WRONG - Do not do this
```sql
-- WRONG: Uses wrong base table
SELECT COUNT(*) FROM company.company_master;

-- WRONG: Not joined to authoritative source
SELECT * FROM people.people_master;
```

---

## Data Flow

```
Clay (CL) Workflows
        ↓
outreach.company_target (41,425 companies)
        ↓
people.company_slot (slot assignments via outreach_id)
        ↓
outreach.people (promoted people for outreach)
        ↓
outreach.outreach (outreach activities)
```

---

## Current State (as of 2026-02-02)

| Table | Count | Status |
|-------|-------|--------|
| `outreach.company_target` | 41,425 | ✅ Authoritative |
| `people.company_slot` (filled) | 26,553 | ✅ Linked via outreach_id |
| `people.people_master` (matched) | 26,443 | ✅ People data |
| `people.people_master` (with email) | 21,751 | ✅ Ready for outreach |

---

## Enrichment Status

### Slot Coverage Against Authoritative Table

| Slot | Total | Filled | Has Person | Has Email | Needs Email | Empty Slot |
|------|-------|--------|------------|-----------|-------------|------------|
| CEO | 41,425 | 15,171 (36.6%) | 15,171 | 12,061 (29.1%) | 3,110 | 26,254 (63.4%) |
| CFO | 41,425 | 4,807 (11.6%) | 4,805 | 3,723 (9.0%) | 1,082 | 36,618 (88.4%) |
| HR | 41,425 | 6,575 (15.9%) | 6,533 | 6,030 (14.6%) | 503 | 34,850 (84.1%) |

### Company-Level Summary

| Metric | Count | % of Total |
|--------|-------|------------|
| Total companies | 41,425 | 100% |
| Companies with at least 1 slot filled | 18,353 | 44.3% |
| Companies with at least 1 person WITH email | 15,401 | 37.2% |
| Companies with all 3 slots filled | 1,760 | 4.2% |
| **Companies with NO people found** | **23,072** | **55.7%** |

### What Needs Enrichment

| Priority | Action Needed | Count |
|----------|---------------|-------|
| 1 | **Empty CEO slots** - Find executives | 26,254 |
| 2 | **CEO needs email** - Email enrichment | 3,110 |
| 3 | **Empty HR slots** - Find HR contacts | 34,850 |
| 4 | **Empty CFO slots** - Find finance contacts | 36,618 |
| 5 | **People need email** - Total needing enrichment | 4,695 |

### Source of Filled Slots

| Source System | Filled Slots |
|---------------|-------------|
| intake_promotion | 21,909 |
| free_extraction | 3,820 |
| people_master_bridge | 322 |
| people_master_match | 174 |
| wv_executive_import | 153 |
| email_domain_match | 71 |
| clay | 59 |

---

## Why This Matters

1. **Clay is the source of truth** - Companies come from Clay workflows
2. **outreach_id is the key** - All downstream tables link via this ID
3. **Consistency** - Using one source prevents data discrepancies
4. **Scope** - We only target qualified companies, not the full universe

---

## Blog Sub-Hub URL Storage

> **CRITICAL**: When you need About Us or News/Press URLs, use `company.company_source_urls`.
> **DO NOT SEARCH FOR THIS AGAIN** - it is documented here.

### Table: `company.company_source_urls`

| Attribute | Value |
|-----------|-------|
| **Schema** | `company` |
| **Table** | `company_source_urls` |
| **Total Records** | 97,124 |
| **Primary Key** | `source_id` (UUID) |
| **Company Link** | `company_unique_id` (04.04.01.xx format) |

### URL Types (source_type column)

| Source Type | Count | Purpose | Use Case |
|-------------|-------|---------|----------|
| `about_page` | **24,099** | Company overview / About Us | Context for personalization |
| `press_page` | **14,377** | News / Press / Announcements | Timing signals |
| `contact_page` | 25,213 | Contact information | Verification |
| `careers_page` | 16,262 | Job postings | Expansion signals |
| `leadership_page` | 9,214 | Executive bios | People discovery |
| `team_page` | 7,959 | Staff listings | People discovery |

### ⚠️ BRIDGE PATH: How to Join to Outreach

The `company.company_source_urls` table uses `company_unique_id` in `04.04.01.xx` format, while `outreach.outreach` uses `domain`. **Bridge via domain matching through `company.company_master`**:

```
outreach.outreach (42,192)
    │
    │ JOIN ON: domain → website_url (normalized)
    ▼
company.company_master (74,641)
    │
    │ JOIN ON: company_unique_id
    ▼
company.company_source_urls (97,124)
```

**Coverage for Outreach Companies:**
- 19,996 outreach companies have discoverable URLs (47.6%)
- About pages: 19,086 | Press pages: 10,904

### Key Columns

| Column | Type | Description |
|--------|------|-------------|
| `source_id` | UUID | Primary key |
| `company_unique_id` | TEXT | FK to company_master (04.04.01.xx format) |
| `source_type` | VARCHAR(50) | Page type (about_page, press_page, etc.) |
| `source_url` | TEXT | Full URL |
| `page_title` | TEXT | Extracted page title |
| `is_accessible` | BOOLEAN | URL accessibility status |
| `extraction_status` | VARCHAR(50) | pending/extracted/failed |

### Quick Queries

```sql
-- About Us URLs (standalone query)
SELECT company_unique_id, source_url, page_title 
FROM company.company_source_urls 
WHERE source_type = 'about_page';

-- News/Press URLs (standalone query)
SELECT company_unique_id, source_url, page_title 
FROM company.company_source_urls 
WHERE source_type = 'press_page';

-- ✅ BRIDGE QUERY: Get URLs for Outreach Companies
SELECT 
    o.outreach_id,
    o.domain,
    csu.source_type,
    csu.source_url,
    csu.page_title
FROM outreach.outreach o
JOIN company.company_master cm ON LOWER(o.domain) = LOWER(
    REPLACE(REPLACE(REPLACE(cm.website_url, 'http://', ''), 'https://', ''), 'www.', '')
)
JOIN company.company_source_urls csu ON csu.company_unique_id = cm.company_unique_id
WHERE csu.source_type IN ('about_page', 'press_page');
```

### Documentation References

| Document | Purpose |
|----------|---------|
| `hubs/blog-content/SCHEMA.md` | Full table schema |
| `hubs/blog-content/PRD.md §11` | URL Discovery System (ADR-005) |
| `docs/diagrams/erd/BLOG_SUBHUB.mmd` | ERD diagram |

---

---

## Hunter.io Source URLs (Contact Discovery Sources)

> **CRITICAL**: Hunter.io provides up to 30 source URLs per contact showing WHERE the contact was discovered.
> **USE CASE**: Blog sub-hub processing, movement detection, audit trail

### Table: `enrichment.hunter_contact`

| Attribute | Value |
|-----------|-------|
| **Schema** | `enrichment` |
| **Table** | `hunter_contact` |
| **Total Records** | ~248,000 |
| **Source Columns** | `source_1` through `source_30` |

### Source Type Categories (v_hunter_sources_by_type)

| Source Type | Pattern | Use Case |
|-------------|---------|----------|
| `linkedin` | `%linkedin.com%` | Movement detection |
| `press_release` | `%prnewswire.com%`, `%businesswire.com%` | BIT signals |
| `company_page` | `%/about%`, `%/team%`, `%/leadership%` | Content extraction |
| `pdf` | `%.pdf%` | Document indexing |
| `government` | `%sbir.gov%` | Grant/filing signals |
| `google_search` | `%google.com/search%` | Discovery (skip) |
| `other` | All others | Miscellaneous |

### Views for Blog Sub-Hub

| View | Purpose |
|------|---------|
| `enrichment.v_hunter_contact_sources` | Unpivoted sources (one row per source URL) |
| `enrichment.v_hunter_sources_by_type` | Sources with type classification |
| `enrichment.v_hunter_company_sources` | Unique sources per company domain |

### Quick Query

```sql
-- Get all press releases for BIT scoring
SELECT domain, source_url, first_name, last_name, job_title
FROM enrichment.v_hunter_sources_by_type
WHERE source_type = 'press_release'
  AND outreach_id IS NOT NULL;

-- Get LinkedIn URLs for movement detection
SELECT DISTINCT domain, linkedin_url, first_name, last_name, job_title
FROM enrichment.hunter_contact
WHERE linkedin_url IS NOT NULL
  AND outreach_id IS NOT NULL;
```

### Documentation Reference

| Document | Purpose |
|----------|---------|
| `docs/HUNTER_SOURCE_COLUMNS_REFERENCE.md` | Full AI-ready column documentation |

---

## Change Log

| Date | Change |
|------|--------|
| 2026-02-03 | Added Hunter.io Source URLs section |
| 2026-02-02 | Added Blog Sub-Hub URL Storage section |
| 2026-02-02 | Created document establishing authoritative table |


# Join Guide: company.company_source_urls to outreach.outreach

**Generated**: 2026-02-02
**Database**: Neon PostgreSQL (Marketing DB)
**Status**: Complete Schema Analysis

---

## Executive Summary

To join `company.company_source_urls` to `outreach.outreach`, you must traverse through the CL (Company Lifecycle) authority registry. There is **no direct foreign key** between these tables. The correct path is:

```
company.company_source_urls
    → company.company_master
    → cl.company_identity (via company_unique_id)
    → outreach.outreach (via outreach_id)
```

---

## Table Schema Details

### company.company_source_urls

**Location**: `company` schema
**Primary Key**: `id` (UUID)
**Purpose**: Stores discovered source URLs (leadership, team, press pages, etc.) for companies

**Columns**:
| Column Name | Data Type | Nullable | Notes |
|-------------|-----------|----------|-------|
| **id** | UUID | NO | Primary key, auto-generated |
| **company_unique_id** | UUID/TEXT | NO | Foreign key to company.company_master |
| **source_type** | TEXT | NO | Page type: leadership_page, about_page, team_page, press_page, careers_page, contact_page |
| **source_url** | TEXT | NO | Full URL of the discovered page |
| **page_title** | TEXT | YES | HTML title from the page |
| **discovered_from** | TEXT | YES | How URL was found (pattern probe, sitemap, etc.) |
| **http_status** | INTEGER | YES | HTTP status code (200, 404, etc.) |
| **is_accessible** | BOOLEAN | YES | Whether URL responded successfully |
| **discovered_at** | TIMESTAMPTZ | YES | Timestamp when URL was discovered |

**Unique Constraint**: `(company_unique_id, source_url)` - prevents duplicate URLs per company

---

### company.company_master

**Location**: `company` schema
**Primary Key**: `company_unique_id` (UUID)
**Purpose**: Master company records

**Key Columns** (for joining):
| Column Name | Data Type | Notes |
|-------------|-----------|-------|
| **company_unique_id** | UUID | Primary key, matches company_source_urls.company_unique_id |
| company_name | TEXT | Company name |
| website_url | TEXT | Main website |

---

### cl.company_identity

**Location**: `cl` schema (Company Lifecycle - Authority Registry)
**Primary Key**: `company_unique_id` (UUID)
**Purpose**: Authority registry - stores identity pointers (write-once)

**Key Columns** (for joining):
| Column Name | Data Type | Nullable | Notes |
|-------------|-----------|----------|-------|
| **company_unique_id** | UUID | NO | PK, matches company_master.company_unique_id |
| **outreach_id** | UUID | YES | **WRITE-ONCE pointer to outreach.outreach.outreach_id** |
| company_name | TEXT | NO | Company name |
| company_domain | TEXT | YES | Primary domain |
| sovereign_company_id | UUID | YES | Sovereign ID (if applicable) |

---

### outreach.outreach

**Location**: `outreach` schema
**Primary Key**: `outreach_id` (UUID)
**Purpose**: Operational spine for Outreach Hub

**Key Columns** (for joining):
| Column Name | Data Type | Nullable | Notes |
|-------------|-----------|----------|-------|
| **outreach_id** | UUID | NO | Primary key |
| **sovereign_id** | UUID | NO | Foreign key to cl.company_identity.company_unique_id |
| domain | VARCHAR(255) | YES | Domain for this company |
| created_at | TIMESTAMPTZ | NO | Record creation |
| updated_at | TIMESTAMPTZ | NO | Last update |

---

## Join Patterns

### Pattern 1: Company URLs → Outreach (Recommended)

**Use When**: You need to get outreach records for companies that have specific source URLs

```sql
SELECT
    csu.id,
    csu.company_unique_id,
    csu.source_type,
    csu.source_url,
    csu.page_title,
    o.outreach_id,
    o.domain,
    o.created_at
FROM company.company_source_urls csu
INNER JOIN company.company_master cm
    ON csu.company_unique_id = cm.company_unique_id
INNER JOIN cl.company_identity ci
    ON cm.company_unique_id = ci.company_unique_id
INNER JOIN outreach.outreach o
    ON ci.outreach_id = o.outreach_id
WHERE csu.source_type = 'press_page'
  AND csu.is_accessible = true
  AND ci.outreach_id IS NOT NULL;  -- Only companies in outreach
```

---

### Pattern 2: Outreach → Company URLs (Reverse)

**Use When**: You want to find URLs for companies already in outreach

```sql
SELECT
    o.outreach_id,
    o.domain,
    ci.company_unique_id,
    ci.company_name,
    csu.source_type,
    csu.source_url,
    csu.page_title,
    csu.is_accessible
FROM outreach.outreach o
INNER JOIN cl.company_identity ci
    ON o.sovereign_id = ci.company_unique_id
INNER JOIN company.company_master cm
    ON ci.company_unique_id = cm.company_unique_id
LEFT JOIN company.company_source_urls csu
    ON cm.company_unique_id = csu.company_unique_id
WHERE o.outreach_id = $1;  -- Specific outreach record
```

---

### Pattern 3: URL Discovery Status by Outreach Tier

**Use When**: Analyzing URL discovery coverage for outreach companies

```sql
SELECT
    o.outreach_id,
    ci.company_name,
    COUNT(DISTINCT csu.source_type) as url_types_found,
    COUNT(DISTINCT CASE WHEN csu.is_accessible THEN csu.id END) as accessible_urls,
    MAX(csu.discovered_at) as last_url_discovery
FROM outreach.outreach o
INNER JOIN cl.company_identity ci
    ON o.sovereign_id = ci.company_unique_id
INNER JOIN company.company_master cm
    ON ci.company_unique_id = cm.company_unique_id
LEFT JOIN company.company_source_urls csu
    ON cm.company_unique_id = csu.company_unique_id
GROUP BY o.outreach_id, ci.company_name
HAVING COUNT(csu.id) = 0;  -- Find outreach companies with NO discovered URLs
```

---

### Pattern 4: Filter Companies Missing URLs

**Use When**: Finding outreach companies that need URL discovery

```sql
SELECT
    o.outreach_id,
    ci.company_unique_id,
    ci.company_name,
    cm.website_url
FROM outreach.outreach o
INNER JOIN cl.company_identity ci
    ON o.sovereign_id = ci.company_unique_id
INNER JOIN company.company_master cm
    ON ci.company_unique_id = cm.company_unique_id
WHERE NOT EXISTS (
    SELECT 1
    FROM company.company_source_urls csu
    WHERE csu.company_unique_id = cm.company_unique_id
)
ORDER BY o.created_at DESC;
```

---

## Key Join Principles

### 1. CL is Authority Registry
- `cl.company_identity` stores **identity pointers only** (outreach_id, sales_process_id, client_id)
- These pointers are **WRITE-ONCE** - once written, they cannot change
- If a company has outreach_id in CL, it means that company has been claimed by the Outreach Hub

### 2. All Joins Use company_unique_id
- `company.company_source_urls` uses `company_unique_id` as the foreign key
- `company.company_master` uses `company_unique_id` as the primary key
- `cl.company_identity` uses `company_unique_id` as the primary key
- **These are all the same identifier** - matching them ensures alignment

### 3. Outreach Pointer is in CL
- `outreach.outreach.outreach_id` is referenced from `cl.company_identity.outreach_id`
- To reach an outreach record from company data, you **must go through CL**
- There is **no direct FK** from company.* to outreach.outreach

### 4. LEFT JOIN for Optional Data
- Use `LEFT JOIN` for company_source_urls if some companies may not have discovered URLs
- Not all companies will have URLs (especially if discovery hasn't run yet)
- Use `INNER JOIN` only if you require at least one URL to be present

---

## Null Safety

### When outreach_id is NULL

If `cl.company_identity.outreach_id IS NULL`, it means:
- The company has been imported into CL
- But the Outreach Hub has **not yet minted** an outreach_id for this company
- These companies should NOT appear in outreach.outreach

### When source_urls are NULL

If a company has no rows in `company.company_source_urls`, it means:
- The company exists and may be in outreach
- But URL discovery has not run or found URLs for this company
- This is normal and expected for new companies

---

## Performance Considerations

### Indexes Available

| Index | Table | Columns | Purpose |
|-------|-------|---------|---------|
| PK | company.company_source_urls | id | Primary key |
| Unique | company.company_source_urls | (company_unique_id, source_url) | Prevent duplicates |
| PK | company.company_master | company_unique_id | Primary key |
| PK | cl.company_identity | company_unique_id | Primary key |
| PK | outreach.outreach | outreach_id | Primary key |
| FK | outreach.outreach | sovereign_id | Foreign key |

### Recommended Query Optimization

```sql
-- Good: Filters early on outreach_id
SELECT csu.*
FROM company.company_source_urls csu
WHERE csu.company_unique_id IN (
    SELECT cm.company_unique_id
    FROM cl.company_identity ci
    INNER JOIN company.company_master cm
        ON ci.company_unique_id = cm.company_unique_id
    WHERE ci.outreach_id IS NOT NULL
);

-- Better: Pre-filter in CL, then join
WITH outreach_companies AS (
    SELECT DISTINCT ci.company_unique_id
    FROM cl.company_identity ci
    WHERE ci.outreach_id IS NOT NULL
)
SELECT csu.*
FROM company.company_source_urls csu
WHERE csu.company_unique_id IN (SELECT company_unique_id FROM outreach_companies);
```

---

## Real-World Examples

### Example 1: Find Press Pages for Outreach Companies

```sql
SELECT
    o.outreach_id,
    ci.company_name,
    csu.source_url,
    csu.page_title
FROM outreach.outreach o
INNER JOIN cl.company_identity ci
    ON o.sovereign_id = ci.company_unique_id
INNER JOIN company.company_master cm
    ON ci.company_unique_id = cm.company_unique_id
INNER JOIN company.company_source_urls csu
    ON cm.company_unique_id = csu.company_unique_id
WHERE csu.source_type = 'press_page'
  AND csu.is_accessible = true
LIMIT 100;
```

---

### Example 2: Companies Missing URL Discovery

```sql
SELECT
    COUNT(*) as total_companies,
    COUNT(CASE WHEN csu.id IS NULL THEN 1 END) as missing_urls
FROM outreach.outreach o
INNER JOIN cl.company_identity ci
    ON o.sovereign_id = ci.company_unique_id
INNER JOIN company.company_master cm
    ON ci.company_unique_id = cm.company_unique_id
LEFT JOIN company.company_source_urls csu
    ON cm.company_unique_id = csu.company_unique_id;
```

---

### Example 3: URL Type Coverage

```sql
SELECT
    csu.source_type,
    COUNT(DISTINCT cm.company_unique_id) as companies_with_type,
    COUNT(DISTINCT CASE WHEN csu.is_accessible THEN cm.company_unique_id END) as accessible_count,
    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN csu.is_accessible THEN cm.company_unique_id END)
        / COUNT(DISTINCT cm.company_unique_id),
        2
    ) as accessibility_pct
FROM outreach.outreach o
INNER JOIN cl.company_identity ci
    ON o.sovereign_id = ci.company_unique_id
INNER JOIN company.company_master cm
    ON ci.company_unique_id = cm.company_unique_id
INNER JOIN company.company_source_urls csu
    ON cm.company_unique_id = csu.company_unique_id
GROUP BY csu.source_type
ORDER BY companies_with_type DESC;
```

---

## Summary Table

| Item | Value |
|------|-------|
| **Direct FK from company_source_urls → outreach.outreach** | No |
| **Join Path** | company_source_urls → company_master → cl.company_identity → outreach.outreach |
| **Key Join Column** | company_unique_id (all tables) |
| **CL Pointer Column** | cl.company_identity.outreach_id |
| **Outreach Primary Key** | outreach.outreach_id |
| **company_source_urls Rows** | ~97,000+ |
| **Outreach Rows** | ~49,737 |
| **Coverage** | Not all companies have source URLs; not all companies are in outreach |

---

## Doctrine Alignment

This join pattern follows **CL Parent-Child Doctrine v1.1**:

- **CL is authority registry** - stores identity pointers only
- **Outreach is operational spine** - stores workflow state
- **Company tables are atomic data** - source of truth for company attributes
- **Write-once to CL** - outreach_id is written once when outreach.outreach record is created

See `CLAUDE.md` for complete doctrine details.

---

**Last Updated**: 2026-02-02
**Verified Against**: Database schema as of 2026-01-28
**Maintained By**: barton-outreach-core database team

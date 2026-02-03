# Hunter.io Source Columns Reference

> **AUTHORITY**: Neon PostgreSQL (Production)
> **VERIFIED**: 2026-02-03
> **TABLE**: `enrichment.hunter_contact`
> **STATUS**: AI-READY | HUMAN-READY

---

## Overview

Hunter.io provides up to **30 source URLs** for each contact, documenting WHERE the contact information was discovered. These sources are critical for:

1. **Blog Sub-Hub Processing** - Pre-verified URLs for content extraction
2. **Movement Detection** - Monitor LinkedIn profiles for job changes
3. **Audit Trail** - Proof of data provenance
4. **Content Signals** - News articles, press releases for BIT scoring

---

## Source Columns Schema

### Table: `enrichment.hunter_contact`

| Column ID | Column Name | Data Type | Format | Description |
|-----------|-------------|-----------|--------|-------------|
| `HC.S01` | `source_1` | TEXT | URL | Primary source where Hunter discovered this contact |
| `HC.S02` | `source_2` | TEXT | URL | Secondary discovery source |
| `HC.S03` | `source_3` | TEXT | URL | Tertiary discovery source |
| `HC.S04` | `source_4` | TEXT | URL | Additional discovery source |
| `HC.S05` | `source_5` | TEXT | URL | Additional discovery source |
| `HC.S06` | `source_6` | TEXT | URL | Additional discovery source |
| `HC.S07` | `source_7` | TEXT | URL | Additional discovery source |
| `HC.S08` | `source_8` | TEXT | URL | Additional discovery source |
| `HC.S09` | `source_9` | TEXT | URL | Additional discovery source |
| `HC.S10` | `source_10` | TEXT | URL | Additional discovery source |
| `HC.S11` | `source_11` | TEXT | URL | Additional discovery source |
| `HC.S12` | `source_12` | TEXT | URL | Additional discovery source |
| `HC.S13` | `source_13` | TEXT | URL | Additional discovery source |
| `HC.S14` | `source_14` | TEXT | URL | Additional discovery source |
| `HC.S15` | `source_15` | TEXT | URL | Additional discovery source |
| `HC.S16` | `source_16` | TEXT | URL | Additional discovery source |
| `HC.S17` | `source_17` | TEXT | URL | Additional discovery source |
| `HC.S18` | `source_18` | TEXT | URL | Additional discovery source |
| `HC.S19` | `source_19` | TEXT | URL | Additional discovery source |
| `HC.S20` | `source_20` | TEXT | URL | Additional discovery source |
| `HC.S21` | `source_21` | TEXT | URL | Additional discovery source |
| `HC.S22` | `source_22` | TEXT | URL | Additional discovery source |
| `HC.S23` | `source_23` | TEXT | URL | Additional discovery source |
| `HC.S24` | `source_24` | TEXT | URL | Additional discovery source |
| `HC.S25` | `source_25` | TEXT | URL | Additional discovery source |
| `HC.S26` | `source_26` | TEXT | URL | Additional discovery source |
| `HC.S27` | `source_27` | TEXT | URL | Additional discovery source |
| `HC.S28` | `source_28` | TEXT | URL | Additional discovery source |
| `HC.S29` | `source_29` | TEXT | URL | Additional discovery source |
| `HC.S30` | `source_30` | TEXT | URL | Additional discovery source |
| `HC.SF` | `source_file` | VARCHAR(255) | Filename | CSV file this record was imported from |

---

## Source Type Classification

Sources are automatically categorized in `enrichment.v_hunter_sources_by_type`:

| Source Type | Pattern Match | Use Case |
|-------------|---------------|----------|
| `linkedin` | `%linkedin.com%` | Person profile monitoring, movement detection |
| `google_search` | `%google.com/search%` | Discovery query (not actionable) |
| `press_release` | `%prnewswire.com%`, `%businesswire.com%` | News signals, company announcements |
| `government` | `%sbir.gov%` | Government filings, grants |
| `pdf` | `%.pdf%` | Documents, reports |
| `company_page` | `%/about%`, `%/team%`, `%/leadership%` | Company website pages |
| `twitter` | `%twitter.com%`, `%x.com%` | Social media presence |
| `facebook` | `%facebook.com%` | Social media presence |
| `other` | All others | Miscellaneous sources |

---

## Views for Processing

### `enrichment.v_hunter_contact_sources`

Unpivots all 30 source columns into rows for easy processing.

| Column | Type | Description |
|--------|------|-------------|
| `contact_id` | INTEGER | FK to hunter_contact.id |
| `domain` | VARCHAR | Company domain |
| `email` | VARCHAR | Contact email |
| `first_name` | VARCHAR | Contact first name |
| `last_name` | VARCHAR | Contact last name |
| `job_title` | VARCHAR | Contact job title |
| `linkedin_url` | VARCHAR | LinkedIn profile URL |
| `outreach_id` | UUID | FK to outreach.outreach |
| `source_order` | INTEGER | Source column number (1-30) |
| `source_url` | TEXT | The actual source URL |

**Query Example:**
```sql
SELECT * FROM enrichment.v_hunter_contact_sources
WHERE outreach_id IS NOT NULL
  AND source_url NOT LIKE '%google.com/search%';
```

### `enrichment.v_hunter_sources_by_type`

Adds `source_type` classification to each source.

| Column | Type | Description |
|--------|------|-------------|
| (all from v_hunter_contact_sources) | | |
| `source_type` | VARCHAR | Categorized type (linkedin, press_release, etc.) |

**Query Example:**
```sql
-- Get all press releases for BIT scoring
SELECT * FROM enrichment.v_hunter_sources_by_type
WHERE source_type = 'press_release';

-- Get LinkedIn URLs for movement detection
SELECT DISTINCT linkedin_url, first_name, last_name, job_title, domain
FROM enrichment.v_hunter_sources_by_type
WHERE source_type = 'linkedin'
  AND linkedin_url IS NOT NULL;
```

### `enrichment.v_hunter_company_sources`

Aggregates unique sources per company domain.

| Column | Type | Description |
|--------|------|-------------|
| `domain` | VARCHAR | Company domain |
| `organization` | VARCHAR | Company name |
| `outreach_id` | UUID | FK to outreach.outreach |
| `source_url` | TEXT | Unique source URL |
| `source_type` | VARCHAR | Categorized type |

**Query Example:**
```sql
-- Get all company pages for blog sub-hub
SELECT * FROM enrichment.v_hunter_company_sources
WHERE source_type = 'company_page'
  AND outreach_id IS NOT NULL;
```

---

## Blog Sub-Hub Integration

The source columns feed directly into the blog sub-hub processing queue:

```
Hunter Sources (stored)              Blog Sub-Hub Extracts
───────────────────────              ─────────────────────
company_page URLs         →          Executive bios, org structure
press_release URLs        →          Company news, announcements, BIT signals
linkedin URLs             →          Career moves, job changes
pdf URLs                  →          Documents, reports, filings
```

### Recommended Processing Order

1. **company_page** - Extract leadership/team info for slot filling
2. **press_release** - Extract news for BIT scoring
3. **linkedin** - Store for movement detection (periodic monitoring)
4. **pdf** - Index for content search
5. **other** - Categorize and process as needed

---

## Data Quality Indicators

| Field | Description | Quality Signal |
|-------|-------------|----------------|
| `num_sources` | Count of sources Hunter found | Higher = more reliable |
| `confidence_score` | Hunter's confidence (0-100) | ≥80 recommended for outreach |
| `source_1` populated | Has at least one source | Required for audit trail |

---

## Foreign Key Relationships

```
enrichment.hunter_contact
    ├── domain → enrichment.hunter_company.domain
    ├── outreach_id → outreach.outreach.outreach_id
    └── source_1..30 → (URLs for blog sub-hub processing)

enrichment.v_hunter_contact_sources
    └── Unpivoted view of source_1..30

enrichment.v_hunter_sources_by_type
    └── Classified by source_type

enrichment.v_hunter_company_sources
    └── Unique sources per domain
```

---

## Migration History

| Date | Migration | Description |
|------|-----------|-------------|
| 2026-02-03 | `2026-02-03-add-hunter-source-columns.sql` | Added source_1 through source_30 columns |
| 2026-02-03 | Same | Added source_file tracking column |
| 2026-02-03 | Same | Created unpivot views for blog sub-hub |

---

## IMO Compliance

| Attribute | Value |
|-----------|-------|
| **Hub Owner** | Enrichment (04.05) |
| **Downstream Consumers** | Blog Content (04.04.05), People Intelligence (04.04.02) |
| **Data Classification** | PII (source URLs may contain names) |
| **Retention Policy** | Permanent (audit trail) |

---

## Quick Reference

```sql
-- Count sources per contact
SELECT
    email,
    num_sources,
    COALESCE(source_1 IS NOT NULL, false)::int +
    COALESCE(source_2 IS NOT NULL, false)::int +
    COALESCE(source_3 IS NOT NULL, false)::int AS actual_sources
FROM enrichment.hunter_contact
WHERE source_1 IS NOT NULL
LIMIT 10;

-- Get all sources for a specific domain
SELECT * FROM enrichment.v_hunter_contact_sources
WHERE domain = 'example.com';

-- Count sources by type
SELECT source_type, COUNT(*)
FROM enrichment.v_hunter_sources_by_type
GROUP BY source_type
ORDER BY COUNT(*) DESC;
```

---

## Change Log

| Date | Change |
|------|--------|
| 2026-02-03 | Created document with AI-ready column definitions |
| 2026-02-03 | Added source type classification |
| 2026-02-03 | Added view documentation and query examples |

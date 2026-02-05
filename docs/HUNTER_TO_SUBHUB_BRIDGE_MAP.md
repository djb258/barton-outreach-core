# Hunter.io to Sub-Hub Bridge Mapping

**Version**: 1.0
**Created**: 2026-02-05
**Purpose**: Define exact column mappings from Hunter source tables to Outreach sub-hub target tables

---

## Overview

This document defines the data bridges from Hunter.io enrichment data to each Outreach sub-hub following waterfall order.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HUNTER SOURCE DATA                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  enrichment.hunter_company (26 columns)                                      │
│  enrichment.hunter_contact (59 columns)                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WATERFALL TARGET TABLES                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  0. outreach.outreach         (SPINE)      - 7 columns                       │
│  1. outreach.company_target   (CT)         - 18 columns                      │
│  2. outreach.dol              (DOL)        - 9 columns  [NOT FROM HUNTER]    │
│  3. people.people_master      (PEOPLE)     - 32 columns                      │
│  3. people.company_slot       (SLOTS)      - 11 columns                      │
│  5. outreach.blog             (BLOG)       - 12 columns                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## JOIN KEY

All bridges use **domain** as the primary join key:

```sql
hunter_company.domain = outreach.outreach.domain
hunter_contact.domain = outreach.outreach.domain
```

The `outreach_id` in Hunter tables can be pre-populated during import, or joined at sync time.

---

## BRIDGE 1: hunter_company → outreach.company_target

**Purpose**: Populate company intelligence data (email patterns, industry, headcount)

| Source Column | Source Type | Target Column | Target Type | Transform | Notes |
|---------------|-------------|---------------|-------------|-----------|-------|
| `email_pattern` | varchar(100) | `email_method` | varchar | DIRECT | Critical for email generation |
| `confidence_score` | numeric | `confidence_score` | numeric | DIRECT | Pattern confidence |
| `company_type` | varchar(100) | `method_type` | varchar | DIRECT | "privately held", etc. |
| `industry` | varchar(255) | - | - | NOT MAPPED | No target column exists |
| `headcount` | varchar(50) | - | - | NOT MAPPED | No target column exists |
| `headcount_min` | integer | - | - | NOT MAPPED | No target column exists |
| `headcount_max` | integer | - | - | NOT MAPPED | No target column exists |
| `country` | varchar(10) | - | - | NOT MAPPED | No target column exists |
| `state` | varchar(50) | - | - | NOT MAPPED | No target column exists |
| `city` | varchar(100) | - | - | NOT MAPPED | No target column exists |

### SQL Bridge Template

```sql
UPDATE outreach.company_target ct
SET
    email_method = hc.email_pattern,
    confidence_score = hc.data_quality_score,
    method_type = hc.company_type,
    updated_at = NOW()
FROM enrichment.hunter_company hc
JOIN outreach.outreach o ON LOWER(hc.domain) = LOWER(o.domain)
WHERE ct.outreach_id = o.outreach_id
AND ct.email_method IS NULL
AND hc.email_pattern IS NOT NULL;
```

---

## BRIDGE 2: hunter_contact → outreach.people

**Purpose**: Populate outreach contact records for campaign execution

| Source Column | Source Type | Target Column | Target Type | Transform | Notes |
|---------------|-------------|---------------|-------------|-----------|-------|
| `domain` | varchar(255) | - | - | JOIN KEY | Via outreach.outreach |
| `email` | varchar(255) | `email` | text | DIRECT | Required |
| `first_name` | varchar(100) | - | - | NOT IN TABLE | outreach.people doesn't have name fields |
| `last_name` | varchar(100) | - | - | NOT IN TABLE | outreach.people doesn't have name fields |
| `job_title` | varchar(255) | `slot_type` | text | TRANSFORM | Map to CHRO/HR_MANAGER/etc. |
| `confidence_score` | integer | - | - | NOT MAPPED | |
| `email_type` | varchar(20) | - | - | NOT MAPPED | |
| `linkedin_url` | varchar(500) | - | - | NOT IN TABLE | |

**NOTE**: `outreach.people` table is minimal - most contact data should go to `people.people_master`

---

## BRIDGE 3: hunter_contact → people.people_master

**Purpose**: Create master contact records for slot assignment

| Source Column | Source Type | Target Column | Target Type | Transform | Notes |
|---------------|-------------|---------------|-------------|-----------|-------|
| `email` | varchar(255) | `email` | text | DIRECT | Primary contact method |
| `first_name` | varchar(100) | `first_name` | text | DIRECT | Required |
| `last_name` | varchar(100) | `last_name` | text | DIRECT | Required |
| `full_name` | varchar(200) | `full_name` | text | DIRECT | Computed if NULL |
| `job_title` | varchar(255) | `title` | text | DIRECT | Raw title |
| `seniority_level` | varchar(100) | `seniority` | text | DIRECT | C-Level, VP, etc. |
| `department` | varchar(100) | `department` | text | DIRECT | |
| `linkedin_url` | varchar(500) | `linkedin_url` | text | DIRECT | |
| `twitter_handle` | varchar(100) | `twitter_url` | text | TRANSFORM | Prefix with https://twitter.com/ |
| `phone_number` | varchar(50) | `work_phone_e164` | text | DIRECT | |
| `email_verified` | boolean | `email_verified` | boolean | DIRECT | |
| `confidence_score` | integer | - | - | STORE IN `email_verification_source` | As "hunter:{score}" |
| - | - | `source_system` | text | CONSTANT | 'hunter' |
| - | - | `unique_id` | text | GENERATE | Barton ID format |
| - | - | `company_unique_id` | text | LOOKUP | Via outreach.outreach |
| - | - | `company_slot_unique_id` | text | LOOKUP | Via slot assignment |

### SQL Bridge Template

```sql
INSERT INTO people.people_master (
    unique_id,
    company_unique_id,
    company_slot_unique_id,
    first_name,
    last_name,
    full_name,
    title,
    seniority,
    department,
    email,
    linkedin_url,
    twitter_url,
    work_phone_e164,
    email_verified,
    email_verification_source,
    source_system,
    source_record_id,
    promoted_from_intake_at
)
SELECT
    '04.04.02.99.' || LPAD((ROW_NUMBER() OVER())::text, 5, '0') || '.' ||
        LPAD((ROW_NUMBER() OVER() % 1000)::text, 3, '0') AS unique_id,
    o.sovereign_id AS company_unique_id,
    cs.unique_id AS company_slot_unique_id,
    hct.first_name,
    hct.last_name,
    COALESCE(hct.full_name, hct.first_name || ' ' || hct.last_name) AS full_name,
    hct.job_title AS title,
    hct.seniority_level AS seniority,
    hct.department,
    hct.email,
    hct.linkedin_url,
    CASE WHEN hct.twitter_handle IS NOT NULL
         THEN 'https://twitter.com/' || REPLACE(hct.twitter_handle, '@', '')
         ELSE NULL END AS twitter_url,
    hct.phone_number AS work_phone_e164,
    COALESCE(hct.email_verified, true) AS email_verified,
    'hunter:' || COALESCE(hct.confidence_score::text, '0') AS email_verification_source,
    'hunter' AS source_system,
    hct.id::text AS source_record_id,
    NOW() AS promoted_from_intake_at
FROM enrichment.hunter_contact hct
JOIN outreach.outreach o ON LOWER(hct.domain) = LOWER(o.domain)
LEFT JOIN people.company_slot cs ON cs.outreach_id = o.outreach_id
    AND cs.slot_type = (
        CASE
            WHEN hct.job_title ILIKE '%ceo%' OR hct.job_title ILIKE '%chief executive%'
                 OR hct.job_title ILIKE '%president%' OR hct.job_title ILIKE '%owner%' THEN 'CEO'
            WHEN hct.job_title ILIKE '%cfo%' OR hct.job_title ILIKE '%chief financial%'
                 OR hct.job_title ILIKE '%controller%' THEN 'CFO'
            WHEN hct.job_title ILIKE '%hr%' OR hct.job_title ILIKE '%human resource%'
                 OR hct.job_title ILIKE '%people%' THEN 'HR'
            ELSE NULL
        END
    )
WHERE hct.first_name IS NOT NULL
AND hct.last_name IS NOT NULL
AND hct.email IS NOT NULL;
```

---

## BRIDGE 4: hunter_contact.source_* → outreach.blog

**Purpose**: Extract About and News URLs from Hunter source URLs

| Source Column | Source Type | Target Column | Target Type | Transform | Notes |
|---------------|-------------|---------------|-------------|-----------|-------|
| `source_1` to `source_30` | text | `about_url` | text | FILTER | URLs containing /about, /team, /leadership |
| `source_1` to `source_30` | text | `news_url` | text | FILTER | URLs containing /news, /blog, /press |
| - | - | `extraction_method` | text | CONSTANT | 'hunter_source' |
| - | - | `last_extracted_at` | timestamptz | CURRENT | NOW() |

### URL Pattern Matching

```sql
-- About URL patterns
source_url ILIKE '%/about%'
OR source_url ILIKE '%/team%'
OR source_url ILIKE '%/leadership%'
OR source_url ILIKE '%/our-team%'
OR source_url ILIKE '%/about-us%'

-- News URL patterns
source_url ILIKE '%/news%'
OR source_url ILIKE '%/blog%'
OR source_url ILIKE '%/press%'
OR source_url ILIKE '%/media%'
OR source_url ILIKE '%/announcements%'
```

### SQL Bridge Template

```sql
UPDATE outreach.blog b
SET
    about_url = sub.about_url,
    news_url = sub.news_url,
    extraction_method = 'hunter_source',
    last_extracted_at = NOW()
FROM (
    SELECT
        hct.outreach_id,
        MIN(CASE WHEN s.source_url ILIKE '%/about%' OR s.source_url ILIKE '%/team%'
                 OR s.source_url ILIKE '%/leadership%' THEN s.source_url END) AS about_url,
        MIN(CASE WHEN s.source_url ILIKE '%/news%' OR s.source_url ILIKE '%/blog%'
                 OR s.source_url ILIKE '%/press%' THEN s.source_url END) AS news_url
    FROM enrichment.hunter_contact hct
    CROSS JOIN LATERAL (
        VALUES (hct.source_1), (hct.source_2), (hct.source_3), (hct.source_4), (hct.source_5),
               (hct.source_6), (hct.source_7), (hct.source_8), (hct.source_9), (hct.source_10)
        -- ... sources 11-30
    ) AS s(source_url)
    WHERE s.source_url IS NOT NULL
    GROUP BY hct.outreach_id
) sub
WHERE b.outreach_id = sub.outreach_id
AND (b.about_url IS NULL OR b.news_url IS NULL);
```

---

## BRIDGE 5: Slot Type Mapping

**Purpose**: Map Hunter job titles to slot types

| Hunter job_title Pattern | Slot Type | Priority |
|--------------------------|-----------|----------|
| `%ceo%`, `%chief executive%`, `%president%`, `%owner%`, `%founder%`, `%managing director%` | CEO | 1 |
| `%cfo%`, `%chief financial%`, `%finance director%`, `%controller%`, `%treasurer%` | CFO | 2 |
| `%hr%`, `%human resource%`, `%people operations%`, `%talent%`, `%recruiting%`, `%chro%` | HR | 3 |
| `%cto%`, `%chief technology%`, `%vp engineering%` | CTO | 4 |
| `%cmo%`, `%chief marketing%`, `%vp marketing%` | CMO | 5 |
| `%coo%`, `%chief operating%`, `%operations director%` | COO | 6 |

---

## SYNC ORDER (Waterfall)

Execute bridges in this order:

```
1. BRIDGE 1: hunter_company → company_target.email_method
   ↓
2. BRIDGE 3: hunter_contact → people.people_master (create records)
   ↓
3. BRIDGE 5: Slot assignment (map titles, fill slots)
   ↓
4. BRIDGE 4: hunter_contact.source_* → blog (URLs)
   ↓
5. Email generation (use email_method patterns for people without emails)
```

---

## GAPS IDENTIFIED

### Columns in Hunter NOT mapped to any target:

**From hunter_company:**
- `industry`, `industry_normalized` - No target column
- `headcount`, `headcount_min`, `headcount_max` - No target column
- `country`, `state`, `city`, `postal_code`, `street` - No target column
- `location_full` - No target column
- `company_embedding` - No target column
- `tags` - No target column

**From hunter_contact:**
- `department_normalized` - Could map to people_master.department
- `is_decision_maker` - No target column
- `contact_embedding` - No target column
- `outreach_priority` - No target column
- `tags` - No target column

### Recommended Schema Additions:

Consider adding to `outreach.company_target`:
- `industry` varchar(255)
- `headcount_min` integer
- `headcount_max` integer
- `state` varchar(50)

---

## VALIDATION QUERIES

### Check Bridge 1 (email_method sync):
```sql
SELECT
    COUNT(*) FILTER (WHERE ct.email_method IS NOT NULL) AS has_pattern,
    COUNT(*) FILTER (WHERE ct.email_method IS NULL AND hc.email_pattern IS NOT NULL) AS can_sync,
    COUNT(*) FILTER (WHERE ct.email_method IS NULL AND hc.email_pattern IS NULL) AS no_source
FROM outreach.company_target ct
JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
LEFT JOIN enrichment.hunter_company hc ON LOWER(o.domain) = LOWER(hc.domain);
```

### Check Bridge 3 (people_master sync):
```sql
SELECT
    COUNT(DISTINCT hct.id) AS hunter_contacts,
    COUNT(DISTINCT pm.unique_id) AS people_master_records,
    COUNT(DISTINCT hct.id) - COUNT(DISTINCT pm.source_record_id) AS not_synced
FROM enrichment.hunter_contact hct
LEFT JOIN people.people_master pm ON pm.source_record_id = hct.id::text AND pm.source_system = 'hunter';
```

---

## FILES

- Schema CSVs: `docs/schema_csv/*.csv`
- This document: `docs/HUNTER_TO_SUBHUB_BRIDGE_MAP.md`
- Sync scripts: `scripts/sync_hunter_*.py` (to be created)

---

**Document Owner**: Barton Outreach Core
**Last Updated**: 2026-02-05

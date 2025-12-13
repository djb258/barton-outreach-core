# Sidecar Tables Migration Summary

**Migration**: `006_create_sidecar_tables.sql`
**Date**: 2025-11-18
**Status**: ✅ **COMPLETED**
**Barton ID**: 04.04.02.04.50000.006

---

## Overview

Created two sidecar tables in the `marketing` schema to hold **optional enrichment data** that should not be part of the core validation schema. These tables store supplementary information from enrichment sources (Clay, Apify, Firecrawl, etc.) without polluting the master tables.

---

## Tables Created

### 1. `marketing.company_sidecar`

**Purpose**: Optional enrichment data for companies (EIN, D&B, Clay metadata)

**Columns** (11 total):
```
company_unique_id          VARCHAR(50)  PRIMARY KEY  FK → company_master
ein_number                 VARCHAR(20)  Employer Identification Number (IRS)
dun_and_bradstreet_number  VARCHAR(20)  Dun & Bradstreet DUNS number
clay_tags                  TEXT[]       Clay.com tags for categorization
clay_segments              TEXT[]       Clay.com segments for grouping
enrichment_payload         JSONB        Full JSON from enrichment source
last_enriched_at           TIMESTAMP    Last enrichment timestamp
enrichment_source          TEXT         Source (clay, apify, firecrawl, etc.)
confidence_score           NUMERIC(5,2) Data confidence score (0-100)
created_at                 TIMESTAMP    DEFAULT NOW()
updated_at                 TIMESTAMP    DEFAULT NOW() + auto-trigger
```

**Indexes** (7 total):
- `company_sidecar_pkey` (PRIMARY KEY on company_unique_id)
- `idx_company_sidecar_ein` (on ein_number)
- `idx_company_sidecar_duns` (on dun_and_bradstreet_number)
- `idx_company_sidecar_enriched` (on last_enriched_at DESC)
- `idx_company_sidecar_source` (on enrichment_source)
- `idx_company_sidecar_confidence` (on confidence_score DESC)
- `idx_company_sidecar_payload` (GIN on enrichment_payload JSONB)

**Foreign Key Constraint**:
```sql
CONSTRAINT fk_company_sidecar_company
    FOREIGN KEY (company_unique_id)
    REFERENCES marketing.company_master(company_unique_id)
    ON DELETE CASCADE
```

**Auto-Update Trigger**:
```sql
CREATE TRIGGER company_sidecar_updated_at
    BEFORE UPDATE ON marketing.company_sidecar
    FOR EACH ROW
    EXECUTE FUNCTION update_company_sidecar_updated_at();
```

---

### 2. `marketing.people_sidecar`

**Purpose**: Optional enrichment data for people (Clay insights, social profiles)

**Columns** (10 total):
```
person_unique_id      VARCHAR(50)  PRIMARY KEY  FK → people_master
clay_insight_summary  TEXT         Clay.com AI-generated insights
clay_segments         TEXT[]       Clay.com segments (e.g., "VP-Engineering")
social_profiles       JSONB        Social media profiles (Twitter, GitHub, etc.)
enrichment_payload    JSONB        Full JSON from enrichment source
last_enriched_at      TIMESTAMP    Last enrichment timestamp
enrichment_source     TEXT         Source (clay, apify, linkedin_scraper, etc.)
confidence_score      NUMERIC(5,2) Data confidence score (0-100)
created_at            TIMESTAMP    DEFAULT NOW()
updated_at            TIMESTAMP    DEFAULT NOW() + auto-trigger
```

**Indexes** (6 total):
- `people_sidecar_pkey` (PRIMARY KEY on person_unique_id)
- `idx_people_sidecar_enriched` (on last_enriched_at DESC)
- `idx_people_sidecar_source` (on enrichment_source)
- `idx_people_sidecar_confidence` (on confidence_score DESC)
- `idx_people_sidecar_social` (GIN on social_profiles JSONB)
- `idx_people_sidecar_payload` (GIN on enrichment_payload JSONB)

**Foreign Key Constraint**:
```sql
CONSTRAINT fk_people_sidecar_person
    FOREIGN KEY (person_unique_id)
    REFERENCES marketing.people_master(unique_id)
    ON DELETE CASCADE
```

**Auto-Update Trigger**:
```sql
CREATE TRIGGER people_sidecar_updated_at
    BEFORE UPDATE ON marketing.people_sidecar
    FOR EACH ROW
    EXECUTE FUNCTION update_people_sidecar_updated_at();
```

---

## Design Rationale

### Why Sidecar Tables?

**Separation of Concerns**:
- Core master tables (`company_master`, `people_master`) contain **only validated, required fields**
- Sidecar tables contain **optional, supplementary enrichment data**
- This prevents validation logic from being polluted with optional fields

**Validation Independence**:
- Records can be promoted to master tables **without** enrichment data
- Enrichment can happen **after** promotion (not a blocker)
- Failed enrichment doesn't prevent records from being valid

**Flexible Schema**:
- JSONB columns (`enrichment_payload`, `social_profiles`) allow arbitrary data from different sources
- TEXT[] arrays (`clay_tags`, `clay_segments`) support multi-value categorization
- No need to modify schema for new enrichment sources

**Performance**:
- GIN indexes on JSONB columns enable fast JSON queries
- Separate table means master table queries aren't slowed by large JSONB payloads
- Foreign key with `ON DELETE CASCADE` ensures data cleanup

---

## Usage Examples

### Insert Company Enrichment Data

```sql
-- After promoting company to master, optionally add enrichment
INSERT INTO marketing.company_sidecar (
    company_unique_id,
    ein_number,
    clay_tags,
    enrichment_payload,
    enrichment_source,
    confidence_score,
    last_enriched_at
) VALUES (
    '04.04.01.24.00024.024',  -- FK to company_master
    '12-3456789',              -- IRS EIN
    ARRAY['saas', 'b2b', 'series-b'],  -- Clay tags
    '{"revenue": "$5M-10M", "growth_rate": "40%", "headcount_change": "+15"}'::JSONB,
    'clay',
    95.5,
    NOW()
)
ON CONFLICT (company_unique_id) DO UPDATE SET
    ein_number = EXCLUDED.ein_number,
    clay_tags = EXCLUDED.clay_tags,
    enrichment_payload = EXCLUDED.enrichment_payload,
    enrichment_source = EXCLUDED.enrichment_source,
    confidence_score = EXCLUDED.confidence_score,
    last_enriched_at = EXCLUDED.last_enriched_at;
```

### Insert People Enrichment Data

```sql
-- After promoting person to master, optionally add enrichment
INSERT INTO marketing.people_sidecar (
    person_unique_id,
    clay_insight_summary,
    clay_segments,
    social_profiles,
    enrichment_payload,
    enrichment_source,
    confidence_score,
    last_enriched_at
) VALUES (
    '04.04.02.15.00015.015',  -- FK to people_master
    'VP of Engineering at Series B SaaS company, 10+ years experience, active GitHub contributor',
    ARRAY['vp-engineering', 'open-source-contributor', 'tech-leader'],
    '{"twitter": "@johndoe", "github": "johndoe", "personal": "johndoe.com"}'::JSONB,
    '{"skills": ["Python", "AWS", "Team Leadership"], "certifications": ["AWS Certified"]}'::JSONB,
    'clay',
    92.0,
    NOW()
)
ON CONFLICT (person_unique_id) DO UPDATE SET
    clay_insight_summary = EXCLUDED.clay_insight_summary,
    clay_segments = EXCLUDED.clay_segments,
    social_profiles = EXCLUDED.social_profiles,
    enrichment_payload = EXCLUDED.enrichment_payload,
    enrichment_source = EXCLUDED.enrichment_source,
    confidence_score = EXCLUDED.confidence_score,
    last_enriched_at = EXCLUDED.last_enriched_at;
```

### Query Enriched Companies

```sql
-- Find companies with high confidence enrichment
SELECT
    cm.company_name,
    cs.ein_number,
    cs.clay_tags,
    cs.confidence_score,
    cs.last_enriched_at
FROM marketing.company_master cm
LEFT JOIN marketing.company_sidecar cs ON cm.company_unique_id = cs.company_unique_id
WHERE cs.confidence_score >= 90.0
ORDER BY cs.confidence_score DESC;
```

### Query People by Social Profiles

```sql
-- Find people with GitHub profiles
SELECT
    pm.full_name,
    pm.title,
    ps.social_profiles->>'github' AS github_username,
    ps.clay_insight_summary
FROM marketing.people_master pm
JOIN marketing.people_sidecar ps ON pm.unique_id = ps.person_unique_id
WHERE ps.social_profiles ? 'github'
ORDER BY pm.full_name;
```

### Query by Clay Segments

```sql
-- Find VP-level engineers for targeted outreach
SELECT
    pm.full_name,
    pm.email,
    pm.title,
    ps.clay_segments
FROM marketing.people_master pm
JOIN marketing.people_sidecar ps ON pm.unique_id = ps.person_unique_id
WHERE 'vp-engineering' = ANY(ps.clay_segments)
   OR 'director-engineering' = ANY(ps.clay_segments);
```

### Query Enrichment by Source

```sql
-- Check which enrichment sources are most reliable
SELECT
    enrichment_source,
    COUNT(*) AS total_enrichments,
    AVG(confidence_score) AS avg_confidence,
    MAX(last_enriched_at) AS latest_enrichment
FROM marketing.company_sidecar
GROUP BY enrichment_source
ORDER BY avg_confidence DESC;
```

---

## Integration with Validation Pipeline

### Company Promotion Flow

```
1. Record arrives in intake.company_raw_intake
2. Validation runs (validate_and_promote_companies.py)
3. If VALID:
   - Promote to marketing.company_master ✅
   - Delete from intake ✅
   - Optionally: Insert to company_sidecar (NOT REQUIRED) 🔵
4. If INVALID:
   - Upload to B2 for enrichment
   - Keep in intake
   - Agent enrichment updates intake
   - Re-run validation
```

**Key Point**: Sidecar insertion is **optional** and happens **after** promotion. Records are valid without enrichment data.

### People Promotion Flow

```
1. Record arrives in intake.people_raw_intake
2. Validation runs (validate_and_promote_people.py)
3. If VALID:
   - Promote to marketing.people_master ✅
   - Delete from intake ✅
   - Optionally: Insert to people_sidecar (NOT REQUIRED) 🔵
4. If INVALID:
   - Upload to B2 for enrichment
   - Keep in intake
   - Agent enrichment updates intake
   - Re-run validation
```

---

## Monitoring Queries

### Check Enrichment Coverage

```sql
-- What % of companies have enrichment data?
SELECT
    COUNT(DISTINCT cm.company_unique_id) AS total_companies,
    COUNT(DISTINCT cs.company_unique_id) AS enriched_companies,
    ROUND(100.0 * COUNT(DISTINCT cs.company_unique_id) / COUNT(DISTINCT cm.company_unique_id), 2) AS enrichment_coverage_pct
FROM marketing.company_master cm
LEFT JOIN marketing.company_sidecar cs ON cm.company_unique_id = cs.company_unique_id;
```

### Check Stale Enrichment

```sql
-- Find companies that haven't been enriched in 90+ days
SELECT
    cm.company_name,
    cs.last_enriched_at,
    EXTRACT(DAY FROM NOW() - cs.last_enriched_at) AS days_since_enrichment
FROM marketing.company_master cm
JOIN marketing.company_sidecar cs ON cm.company_unique_id = cs.company_unique_id
WHERE cs.last_enriched_at < NOW() - INTERVAL '90 days'
ORDER BY cs.last_enriched_at ASC;
```

### Check Low Confidence Enrichment

```sql
-- Find enrichments with confidence < 70%
SELECT
    cm.company_name,
    cs.enrichment_source,
    cs.confidence_score,
    cs.last_enriched_at
FROM marketing.company_master cm
JOIN marketing.company_sidecar cs ON cm.company_unique_id = cs.company_unique_id
WHERE cs.confidence_score < 70.0
ORDER BY cs.confidence_score ASC;
```

---

## Data Integrity

### Foreign Key Enforcement

**Cascading Deletes**:
- If a company is deleted from `company_master`, corresponding sidecar record is **automatically deleted**
- If a person is deleted from `people_master`, corresponding sidecar record is **automatically deleted**
- No orphaned enrichment data

**Referential Integrity**:
- Cannot insert sidecar record without corresponding master record (FK constraint enforced)
- Ensures 1:1 relationship (PRIMARY KEY on foreign key column)

### Audit Trail

**Automatic Timestamps**:
- `created_at` defaults to `NOW()` on insert
- `updated_at` auto-updates on every UPDATE via trigger
- `last_enriched_at` tracks when enrichment source last provided data

---

## Migration Verification

### Tables Created

```sql
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_name IN ('company_sidecar', 'people_sidecar')
AND table_schema = 'marketing';
```

**Result**:
```
 table_schema |    table_name
--------------+------------------
 marketing    | company_sidecar
 marketing    | people_sidecar
```

### Column Counts

```
company_sidecar: 11 columns ✅
people_sidecar:  10 columns ✅
```

### Foreign Keys

```
company_sidecar.company_unique_id → company_master.company_unique_id ✅
people_sidecar.person_unique_id   → people_master.unique_id ✅
```

### Indexes

```
company_sidecar: 7 indexes (1 PK + 6 custom) ✅
people_sidecar:  6 indexes (1 PK + 5 custom) ✅
```

### Triggers

```
company_sidecar: update_company_sidecar_updated_at() ✅
people_sidecar:  update_people_sidecar_updated_at() ✅
```

---

## Next Steps

1. **Update enrichment agents** to write to sidecar tables after promotion
2. **Modify promotion scripts** to optionally insert enrichment payloads
3. **Create Grafana dashboards** to monitor enrichment coverage and confidence
4. **Set up alerts** for stale enrichment (>90 days) or low confidence (<70%)

---

**Migration Status**: ✅ **COMPLETED**
**Tables Ready**: ✅ **PRODUCTION READY**
**Foreign Keys**: ✅ **ENFORCED**
**Indexes**: ✅ **OPTIMIZED**
**Triggers**: ✅ **ACTIVE**

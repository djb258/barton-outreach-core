# Outreach Sub-Hub Architecture

**Version**: 2.0
**Created**: 2026-02-05
**Status**: CANONICAL

---

## Chain of Authority

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CL (Company Lifecycle)                               │
│                              PARENT HUB                                      │
│                                                                              │
│                         Mints: sovereign_id                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                            sovereign_id (FK)
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         outreach.outreach                                    │
│                              SPINE                                           │
│                                                                              │
│                         Mints: outreach_id                                   │
│                         Receives: sovereign_id                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                              outreach_id (FK)
                                    │
     ┌──────────────────────────────┼──────────────────────────────┐
     │                              │                              │
     ▼                              ▼                              ▼
┌──────────┐                  ┌──────────┐                  ┌──────────┐
│    CT    │                  │   DOL    │                  │   BLOG   │
│ 04.04.01 │                  │ 04.04.03 │                  │ 04.04.05 │
└──────────┘                  └──────────┘                  └──────────┘
     │
     │                        ┌──────────┐
     │                        │  PEOPLE  │
     │                        │ 04.04.02 │
     └────────────────────────┴──────────┘
```

---

## Sub-Hub Definitions

### SPINE: outreach.outreach

| Column | Type | Description |
|--------|------|-------------|
| outreach_id | UUID (PK) | Unique identifier for this outreach record |
| sovereign_id | UUID (FK) | Link to CL.company_identity |
| domain | VARCHAR | Company domain (used for initial Hunter matching only) |
| status | VARCHAR | Outreach status |
| created_at | TIMESTAMPTZ | Record creation |
| updated_at | TIMESTAMPTZ | Last update |

**Cardinality**: 1 per sovereign_id

---

### SUB-HUB 1: Company Target (CT) - 04.04.01

| Column | Type | Description |
|--------|------|-------------|
| target_id | UUID (PK) | Unique identifier for this CT record |
| outreach_id | UUID (FK) | Link to spine |
| email_method | VARCHAR | Email pattern ({first}.{last}, etc.) |
| confidence_score | NUMERIC | Pattern confidence |
| industry | VARCHAR | Industry classification |
| headcount | VARCHAR | Employee count range |
| headcount_min | INTEGER | Min employees |
| headcount_max | INTEGER | Max employees |
| country | VARCHAR | Country code |
| state | VARCHAR | State/province |
| city | VARCHAR | City |
| snapshot_date | DATE | When this snapshot was taken |
| created_at | TIMESTAMPTZ | Record creation |
| updated_at | TIMESTAMPTZ | Last update |

**Cardinality**: 1+ per outreach_id (track changes over time)

**Owns**: Company-level targeting intelligence

---

### SUB-HUB 2: DOL Filings - 04.04.03

| Column | Type | Description |
|--------|------|-------------|
| dol_id | UUID (PK) | Unique identifier for this DOL record |
| outreach_id | UUID (FK) | Link to spine |
| ein | VARCHAR | Employer Identification Number |
| plan_year | INTEGER | Filing year |
| form_type | VARCHAR | 5500 or 5500-SF |
| total_participants | INTEGER | Plan participants |
| total_assets | NUMERIC | Plan assets |
| renewal_date | DATE | Plan renewal date |
| broker_name | VARCHAR | Broker of record |
| created_at | TIMESTAMPTZ | Record creation |
| updated_at | TIMESTAMPTZ | Last update |

**Cardinality**: 1+ per outreach_id (one per filing year)

**Owns**: Federal DOL filing data, renewal intelligence

---

### SUB-HUB 3: Blog Content - 04.04.05

| Column | Type | Description |
|--------|------|-------------|
| blog_id | UUID (PK) | Unique identifier for this blog record |
| outreach_id | UUID (FK) | Link to spine |
| about_url | TEXT | Company about page URL |
| news_url | TEXT | Company news/blog URL |
| event_type | VARCHAR | Type of content signal |
| event_date | DATE | When event occurred |
| context_summary | TEXT | Summary of content |
| source_url | TEXT | Source of this signal |
| created_at | TIMESTAMPTZ | Record creation |
| updated_at | TIMESTAMPTZ | Last update |

**Cardinality**: 1+ per outreach_id (multiple content signals)

**Owns**: Content signals, timing intelligence, news events

---

### SUB-HUB 4: People Intelligence - 04.04.02

#### people.company_slot

| Column | Type | Description |
|--------|------|-------------|
| slot_id | UUID (PK) | Unique identifier for this slot |
| outreach_id | UUID (FK) | Link to spine |
| slot_type | VARCHAR | CEO, CFO, HR, CTO, CMO, COO |
| is_filled | BOOLEAN | Whether slot has a person assigned |
| person_unique_id | TEXT (FK) | Link to people_master |
| created_at | TIMESTAMPTZ | Record creation |
| updated_at | TIMESTAMPTZ | Last update |

**Cardinality**: 3+ per outreach_id (CEO, CFO, HR minimum)

#### people.people_master

| Column | Type | Description |
|--------|------|-------------|
| unique_id | TEXT (PK) | Barton ID format 04.04.02.XX.XXXXX.XXX |
| company_slot_unique_id | TEXT (FK) | Link to company_slot |
| first_name | TEXT | First name |
| last_name | TEXT | Last name |
| full_name | TEXT | Full name |
| title | TEXT | Job title |
| seniority | TEXT | Seniority level |
| department | TEXT | Department |
| email | TEXT | Email address |
| linkedin_url | TEXT | LinkedIn profile |
| twitter_url | TEXT | Twitter profile |
| work_phone_e164 | TEXT | Phone number |
| email_verified | BOOLEAN | Verification status |
| source_system | TEXT | Data source (hunter, apollo, etc.) |
| created_at | TIMESTAMPTZ | Record creation |
| updated_at | TIMESTAMPTZ | Last update |

**Owns**: Person identity, contact information, slot assignments

---

## Join Rules

### RULE 1: All sub-hubs join to spine via outreach_id

```sql
-- CORRECT
SELECT * FROM outreach.company_target WHERE outreach_id = ?
SELECT * FROM outreach.dol WHERE outreach_id = ?
SELECT * FROM outreach.blog WHERE outreach_id = ?
SELECT * FROM people.company_slot WHERE outreach_id = ?

-- WRONG (never join sub-hubs directly to each other)
SELECT * FROM outreach.company_target ct
JOIN outreach.dol d ON ct.??? = d.???  -- NO!
```

### RULE 2: Domain is NEVER a join key between tables

Domain is only used ONCE during initial import to match Hunter data to outreach_id.

```sql
-- ONE TIME during import
UPDATE enrichment.hunter_company
SET outreach_id = o.outreach_id
FROM outreach.outreach o
WHERE LOWER(hunter_company.domain) = LOWER(o.domain);

-- After that, always use outreach_id
SELECT * FROM enrichment.hunter_company WHERE outreach_id = ?
```

### RULE 3: Each sub-hub record has its own unique ID

```sql
-- CT record
INSERT INTO outreach.company_target (target_id, outreach_id, ...)
VALUES (gen_random_uuid(), ?, ...);

-- DOL record
INSERT INTO outreach.dol (dol_id, outreach_id, ...)
VALUES (gen_random_uuid(), ?, ...);
```

---

## Data Flow from Hunter

### Step 1: Match Hunter to Spine (ONE TIME)

```sql
-- Populate outreach_id in Hunter tables
UPDATE enrichment.hunter_company hc
SET outreach_id = o.outreach_id
FROM outreach.outreach o
WHERE LOWER(hc.domain) = LOWER(o.domain)
AND hc.outreach_id IS NULL;

UPDATE enrichment.hunter_contact hct
SET outreach_id = o.outreach_id
FROM outreach.outreach o
WHERE LOWER(hct.domain) = LOWER(o.domain)
AND hct.outreach_id IS NULL;
```

### Step 2: Sync to Sub-Hubs (via outreach_id)

```
hunter_company  ──(outreach_id)──►  CT
hunter_contact  ──(outreach_id)──►  PEOPLE
hunter_contact.source_*  ──(outreach_id)──►  BLOG
```

---

## Column Ownership

### CT Owns (Company-Level)

From hunter_company:
- email_pattern → email_method
- industry → industry
- headcount → headcount, headcount_min, headcount_max
- country, state, city → location fields
- company_type → method_type
- data_quality_score → confidence_score

### PEOPLE Owns (Person-Level)

From hunter_contact:
- email → email
- first_name → first_name
- last_name → last_name
- full_name → full_name
- job_title → title
- seniority_level → seniority
- department → department
- linkedin_url → linkedin_url
- twitter_handle → twitter_url
- phone_number → work_phone_e164
- confidence_score → email_verification_source
- is_decision_maker → is_decision_maker (need to add column)

### BLOG Owns (Content-Level)

From hunter_contact.source_1-30:
- URLs containing /about, /team, /leadership → about_url
- URLs containing /news, /blog, /press → news_url

### DOL Owns (Filing-Level)

NOT from Hunter. From federal DOL data:
- EIN, Form 5500, Schedule A, renewal dates

---

## Summary

| Component | PK | FK | Records/Company | Data Source |
|-----------|----|----|-----------------|-------------|
| SPINE | outreach_id | sovereign_id | 1 | CL admission |
| CT | target_id | outreach_id | 1+ | hunter_company |
| DOL | dol_id | outreach_id | 1+ per year | Federal DOL |
| BLOG | blog_id | outreach_id | 1+ | hunter_contact sources |
| PEOPLE | slot_id | outreach_id | 3+ | hunter_contact |

---

**Document Owner**: Barton Outreach Core
**Last Updated**: 2026-02-05

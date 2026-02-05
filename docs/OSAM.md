# Outreach Semantic Access Map (OSAM)

> **Purpose**: This document tells you exactly where to go to answer any data question.
> **Rule**: If your question isn't mapped here, **STOP and ask the user**. Do not guess.

---

## Chain of Authority

```
CL (company_identity)
    │
    │ sovereign_company_id
    ▼
SPINE (outreach.outreach)
    │
    │ outreach_id ◄─── THIS IS THE UNIVERSAL JOIN KEY
    ▼
┌───────────────┬───────────────┬───────────────┬───────────────┐
│      CT       │      DOL      │     BLOG      │    PEOPLE     │
│ company_target│     dol       │     blog      │ company_slot  │
│               │               │               │ people_master │
└───────────────┴───────────────┴───────────────┴───────────────┘
```

**Golden Rule**: All sub-hubs join to the spine via `outreach_id`. Never use domain as a join key.

---

## Query Routing Table

**Use this first.** Find your question type, go to that table.

| Question Type | Go To | Join Via |
|---------------|-------|----------|
| Is company in pipeline? | `outreach.outreach` | - |
| Company count by state/city/geography? | `outreach.company_target` | outreach_id |
| Email pattern for company? | `outreach.company_target` | outreach_id |
| Company industry/employees/firmographics? | `outreach.company_target` | outreach_id |
| Slot fill rates (CEO/CFO/HR)? | `people.company_slot` | outreach_id |
| Who is in a slot? | `people.company_slot` → `people.people_master` | slot_id |
| Contact details (name/email/phone)? | `people.people_master` | company_slot_unique_id |
| LinkedIn URL for person? | `people.people_master` | company_slot_unique_id |
| DOL filing status? | `outreach.dol` | outreach_id |
| EIN for company? | `outreach.outreach` or `outreach.dol` | outreach_id |
| Company news/blog URLs? | `outreach.blog` | outreach_id |
| Company name/domain? | `cl.company_identity` | sovereign_company_id |

---

## Hub Definitions

### PARENT: Company Lifecycle (CL)

```
Table: cl.company_identity
PK:    company_unique_id (uuid)
FK:    sovereign_company_id → used by outreach.outreach
```

**Owns (Authority Registry)**:
| Column | Type | Description |
|--------|------|-------------|
| company_unique_id | uuid | CL's internal ID |
| sovereign_company_id | uuid | Universal company identifier across all hubs |
| company_name | text | Legal company name |
| company_domain | text | Primary website domain |
| normalized_domain | text | Cleaned domain for matching |
| outreach_id | uuid | FK to outreach hub (written ONCE) |
| sales_process_id | uuid | FK to sales hub (written ONCE) |
| client_id | uuid | FK to client hub (written ONCE) |

**Ask CL**:
- "What is the company name?"
- "What is the canonical domain?"
- "Is this company in outreach/sales/client?"

---

### SPINE: Outreach

```
Table: outreach.outreach
PK:    outreach_id (uuid)
FK:    sovereign_id → cl.company_identity.sovereign_company_id
```

**Owns (Operational Spine)**:
| Column | Type | Description |
|--------|------|-------------|
| outreach_id | uuid | **Universal join key for all sub-hubs** |
| sovereign_id | uuid | Link to CL authority |
| domain | varchar | Company domain (for reference only, NOT for joins) |
| ein | varchar | Federal EIN if known |
| has_appointment | boolean | Meeting booked flag |
| created_at | timestamptz | When entered pipeline |

**Ask Spine**:
- "Is this company in the outreach pipeline?"
- "When did this company enter outreach?"
- "Does this company have an appointment?"

---

### SUB-HUB: Company Target (CT) - 04.04.01

```
Table: outreach.company_target
PK:    target_id (uuid)
FK:    outreach_id → outreach.outreach
```

**Owns (Company Firmographics + Targeting)**:
| Column | Type | Description |
|--------|------|-------------|
| target_id | uuid | CT record ID |
| outreach_id | uuid | **Join to spine** |
| email_method | varchar | Email pattern (e.g., {first}.{last}) |
| method_type | varchar | Company type (private/public) |
| confidence_score | numeric | Pattern confidence 0-1 |
| is_catchall | boolean | Domain accepts any email |
| industry | varchar | Industry classification |
| employees | integer | Exact employee count |
| country | varchar | ISO country code (US) |
| state | varchar | State abbreviation (MD, PA) |
| city | varchar | City name |
| postal_code | varchar | ZIP code |
| data_year | integer | Year this data reflects |
| outreach_status | text | queued/active/completed |
| bit_score_snapshot | integer | BIT score at targeting |
| execution_status | varchar | pending/in_progress/done |

**Ask CT**:
- "How many companies in Maryland?" → `WHERE state = 'MD'`
- "What's the email pattern for this company?"
- "What industry is this company in?"
- "How many employees does this company have?"
- "Company count by state/city?"
- "Which companies are pending execution?"

---

### SUB-HUB: DOL Filings - 04.04.03

```
Table: outreach.dol
PK:    dol_id (uuid)
FK:    outreach_id → outreach.outreach
```

**Owns (Form 5500 + Benefits Data)**:
| Column | Type | Description |
|--------|------|-------------|
| dol_id | uuid | DOL record ID |
| outreach_id | uuid | **Join to spine** |
| ein | text | Federal EIN |
| filing_present | boolean | Has Form 5500 filing |
| funding_type | text | Fully insured/self-funded |
| broker_or_advisor | text | Current broker name |
| carrier | text | Insurance carrier |

**Ask DOL**:
- "Does this company have a DOL filing?"
- "What's the funding type (self-funded vs fully insured)?"
- "Who is the current broker?"
- "What carrier do they use?"

**Note**: DOL can have multiple records per outreach_id (multiple filing years).

---

### SUB-HUB: Blog/Content - 04.04.05

```
Table: outreach.blog
PK:    blog_id (uuid)
FK:    outreach_id → outreach.outreach
```

**Owns (Content Signals)**:
| Column | Type | Description |
|--------|------|-------------|
| blog_id | uuid | Blog record ID |
| outreach_id | uuid | **Join to spine** |
| about_url | text | Company about page URL |
| news_url | text | Company news/blog URL |
| context_summary | text | Extracted content summary |
| source_url | text | Source of content |
| extraction_method | text | How content was extracted |
| last_extracted_at | timestamptz | When last scraped |

**Ask Blog**:
- "What's the about page URL?"
- "What's the news/blog URL?"
- "When was content last extracted?"

---

### SUB-HUB: People - 04.04.02

#### Table: people.company_slot

```
Table: people.company_slot
PK:    slot_id (uuid)
FK:    outreach_id → outreach.outreach
```

**Owns (Slot Assignments)**:
| Column | Type | Description |
|--------|------|-------------|
| slot_id | uuid | Slot record ID |
| outreach_id | uuid | **Join to spine** |
| company_unique_id | text | CL company ID |
| slot_type | text | CEO, CFO, or HR |
| person_unique_id | text | FK to people_master if filled |
| is_filled | boolean | Slot has person assigned |
| filled_at | timestamptz | When slot was filled |
| confidence_score | numeric | Match confidence |
| source_system | text | Where person came from |

**Ask company_slot**:
- "How many slots are filled for Maryland?" → Join to CT for state
- "What's the CEO fill rate?"
- "Which companies have unfilled HR slots?"
- "Who is assigned to this slot?" → Join to people_master

#### Table: people.people_master

```
Table: people.people_master
PK:    unique_id (text) - Barton ID format: 04.04.02.99.XXXXX.XXX
FK:    company_slot_unique_id → people.company_slot.slot_id
```

**Owns (Contact Details)**:
| Column | Type | Description |
|--------|------|-------------|
| unique_id | text | Barton ID (04.04.02.99.XXXXX.XXX) |
| company_unique_id | text | CL company ID |
| company_slot_unique_id | text | **Join to slot** |
| first_name | text | First name |
| last_name | text | Last name |
| full_name | text | Generated full name |
| title | text | Job title |
| seniority | text | C-Level/VP/Director/etc |
| department | text | Department name |
| email | text | Email address |
| email_verified | boolean | Email verification status |
| email_verification_source | text | How verified (hunter:95) |
| work_phone_e164 | text | Phone number |
| linkedin_url | text | LinkedIn profile URL |
| twitter_url | text | Twitter profile URL |
| is_decision_maker | boolean | Decision maker flag |
| source_system | text | hunter/clay/intake_promotion |
| source_record_id | text | ID from source system |
| validation_status | varchar | full/partial/invalid |

**Ask people_master**:
- "What's the email for this person?"
- "What's their LinkedIn URL?"
- "What's their job title?"
- "How many people have verified emails?"
- "How many people are missing LinkedIn?"

---

## Common Join Paths

### Maryland Companies with Slot Coverage

```sql
SELECT
    COUNT(DISTINCT o.outreach_id) as companies,
    SUM(CASE WHEN cs.is_filled THEN 1 ELSE 0 END) as filled_slots
FROM outreach.outreach o
JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
LEFT JOIN people.company_slot cs ON cs.outreach_id = o.outreach_id
WHERE ct.state = 'MD'
```

### Slot Fill Rates by State

```sql
SELECT
    ct.state,
    cs.slot_type,
    COUNT(*) as total_slots,
    SUM(CASE WHEN cs.is_filled THEN 1 ELSE 0 END) as filled
FROM outreach.company_target ct
JOIN people.company_slot cs ON cs.outreach_id = ct.outreach_id
GROUP BY ct.state, cs.slot_type
ORDER BY ct.state, cs.slot_type
```

### People with Email by Slot Type

```sql
SELECT
    cs.slot_type,
    COUNT(*) as total,
    SUM(CASE WHEN pm.email IS NOT NULL THEN 1 ELSE 0 END) as has_email
FROM people.company_slot cs
JOIN people.people_master pm ON pm.company_slot_unique_id = cs.slot_id::text
WHERE cs.is_filled = true
GROUP BY cs.slot_type
```

### Company Details with Contact

```sql
SELECT
    ci.company_name,
    ct.state,
    ct.industry,
    cs.slot_type,
    pm.full_name,
    pm.email,
    pm.title
FROM cl.company_identity ci
JOIN outreach.outreach o ON o.sovereign_id = ci.sovereign_company_id
JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
JOIN people.company_slot cs ON cs.outreach_id = o.outreach_id
JOIN people.people_master pm ON pm.company_slot_unique_id = cs.slot_id::text
WHERE cs.is_filled = true
```

---

## Source Tables (Enrichment - NOT for Queries)

These tables are **source data** for ETL. Do not query these for business questions.

| Table | Purpose | Use For Queries? |
|-------|---------|------------------|
| enrichment.hunter_company | Hunter.io company data | NO - synced to CT |
| enrichment.hunter_contact | Hunter.io contact data | NO - synced to people_master |
| dol.form_5500 | Raw DOL filings | NO - synced to outreach.dol |
| dol.form_5500_sf | Raw DOL small filings | NO - synced to outreach.dol |

---

## STOP Conditions

**If any of these are true, STOP and ask the user:**

1. Your question doesn't map to any table in this document
2. You need to join more than 4 tables to answer the question
3. You're about to query an enrichment.* table for business data
4. You're about to use domain as a join key (use outreach_id instead)
5. You're unsure which table owns the data you need

---

## Version History

| Date | Change |
|------|--------|
| 2026-02-05 | Initial OSAM creation |


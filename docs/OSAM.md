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
| Company count by state/city/geography? | **UNION** of CT + DOL | See Geography Query |
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

### Geography Queries (UNION Rule)

**State/geography questions require UNION of two sources:**
1. `outreach.company_target.state` - from Hunter (operational HQ)
2. `dol.form_5500/form_5500_sf` - from DOL filings (filing address)

A company counts as "in state X" if **either** source says so.

```sql
-- Maryland Companies (UNION of Hunter + DOL)
WITH dol_md AS (
    SELECT DISTINCT sponsor_dfe_ein as ein FROM dol.form_5500
    WHERE spons_dfe_mail_us_state = 'MD' AND sponsor_dfe_ein IS NOT NULL
    UNION
    SELECT DISTINCT sf_spons_ein as ein FROM dol.form_5500_sf
    WHERE sf_spons_us_state = 'MD' AND sf_spons_ein IS NOT NULL
),
md_companies AS (
    -- Hunter says MD
    SELECT DISTINCT o.outreach_id
    FROM outreach.outreach o
    JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
    WHERE ct.state = 'MD'
    UNION
    -- DOL says MD
    SELECT DISTINCT o.outreach_id
    FROM outreach.outreach o
    JOIN dol_md d ON o.ein = d.ein
)
SELECT COUNT(*) as md_companies FROM md_companies;
```

### Maryland Companies with Slot Coverage (Full Query)

```sql
WITH dol_md AS (
    SELECT DISTINCT sponsor_dfe_ein as ein FROM dol.form_5500
    WHERE spons_dfe_mail_us_state = 'MD' AND sponsor_dfe_ein IS NOT NULL
    UNION
    SELECT DISTINCT sf_spons_ein as ein FROM dol.form_5500_sf
    WHERE sf_spons_us_state = 'MD' AND sf_spons_ein IS NOT NULL
),
md_companies AS (
    SELECT DISTINCT o.outreach_id
    FROM outreach.outreach o
    JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
    WHERE ct.state = 'MD'
    UNION
    SELECT DISTINCT o.outreach_id
    FROM outreach.outreach o
    JOIN dol_md d ON o.ein = d.ein
)
SELECT
    cs.slot_type,
    COUNT(*) as total,
    SUM(CASE WHEN cs.is_filled THEN 1 ELSE 0 END) as filled
FROM md_companies mc
JOIN people.company_slot cs ON cs.outreach_id = mc.outreach_id
GROUP BY cs.slot_type
ORDER BY cs.slot_type;
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

## Source Tables

### Enrichment (Sync to Sub-Hubs)

| Table | Purpose | Query Directly? |
|-------|---------|-----------------|
| enrichment.hunter_company | Hunter.io company data | NO - synced to CT |
| enrichment.hunter_contact | Hunter.io contact data | NO - synced to people_master |

---

## DOL: Queryable System of Record

**DOL is the authoritative source for Form 5500 filing data.** Query these tables directly by EIN.

### DOL Tables

| Table | Records | Columns | Purpose |
|-------|---------|---------|---------|
| dol.form_5500 | 230,482 | 147 | Large filers (100+ participants) |
| dol.form_5500_sf | 760,839 | 196 | Small filers (<100 participants) |
| dol.schedule_a | 337,476 | 98 | Insurance carriers, brokers, commissions |
| dol.column_metadata | 441 | 14 | Column descriptions for AI/human queries |

### DOL Column Metadata

Every DOL column is documented in `dol.column_metadata`:
- `column_id` - Unique identifier (e.g., DOL_SCHA_INS_BROKER_COMM_TOT_AMT)
- `description` - Human-readable description
- `category` - Category (Insurance, Sponsor, Filing, etc.)
- `data_type` - Type (EIN, CURRENCY, DATE, TEXT, FLAG)
- `format_pattern` - Expected format
- `search_keywords` - Keywords for natural language search
- `is_pii` - PII flag
- `example_values` - Sample values

**To understand any DOL column:**
```sql
SELECT column_id, description, category, data_type, format_pattern
FROM dol.column_metadata
WHERE column_name = 'ins_broker_comm_tot_amt';
```

### Key DOL Columns

**form_5500** (large filers):
| Column | ID | Description |
|--------|-----|-------------|
| sponsor_dfe_ein | DOL_F5500_SPONSOR_DFE_EIN | Employer EIN (9 digits) |
| sponsor_dfe_name | DOL_F5500_SPONSOR_DFE_NAME | Company legal name |
| spons_dfe_mail_us_state | DOL_F5500_SPONS_DFE_MAIL_US_STATE | Filing state (2-letter) |
| tot_active_partcp_cnt | DOL_F5500_TOT_ACTIVE_PARTCP_CNT | Total active participants |
| form_year | DOL_F5500_FORM_YEAR | Filing year |

**form_5500_sf** (small filers):
| Column | ID | Description |
|--------|-----|-------------|
| sf_spons_ein | DOL_F5500SF_SF_SPONS_EIN | Employer EIN (9 digits) |
| sf_sponsor_name | DOL_F5500SF_SF_SPONSOR_NAME | Company legal name |
| sf_spons_us_state | DOL_F5500SF_SF_SPONS_US_STATE | Filing state (2-letter) |
| sf_tot_partcp_boy_cnt | DOL_F5500SF_SF_TOT_PARTCP_BOY_CNT | Participants at beginning of year |

**schedule_a** (insurance/broker):
| Column | ID | Description |
|--------|-----|-------------|
| sch_a_ein | DOL_SCHA_SCH_A_EIN | Employer EIN |
| ins_carrier_name | DOL_SCHA_INS_CARRIER_NAME | Insurance carrier name |
| ins_carrier_ein | DOL_SCHA_INS_CARRIER_EIN | Carrier EIN |
| ins_broker_comm_tot_amt | DOL_SCHA_INS_BROKER_COMM_TOT_AMT | Total broker commissions |
| wlfr_bnft_health_ind | DOL_SCHA_WLFR_BNFT_HEALTH_IND | Has health benefit (Y/N) |
| wlfr_bnft_dental_ind | DOL_SCHA_WLFR_BNFT_DENTAL_IND | Has dental benefit (Y/N) |

### DOL Query Examples

**Look up company by EIN:**
```sql
-- Large filer
SELECT sponsor_dfe_name, spons_dfe_mail_us_state, tot_active_partcp_cnt, form_year
FROM dol.form_5500
WHERE sponsor_dfe_ein = '123456789'
ORDER BY form_year DESC;

-- Small filer
SELECT sf_sponsor_name, sf_spons_us_state, sf_tot_partcp_boy_cnt, form_year
FROM dol.form_5500_sf
WHERE sf_spons_ein = '123456789'
ORDER BY form_year DESC;
```

**Get insurance/broker details from Schedule A:**
```sql
SELECT
    sa.sponsor_name,
    sa.ins_carrier_name,
    sa.ins_broker_comm_tot_amt,
    sa.wlfr_bnft_health_ind,
    sa.wlfr_bnft_dental_ind,
    sa.form_year
FROM dol.schedule_a sa
WHERE sa.sch_a_ein = '123456789'
ORDER BY sa.form_year DESC;
```

**Find all companies with Schedule A in a state:**
```sql
SELECT DISTINCT sa.sch_a_ein, sa.sponsor_name, sa.ins_carrier_name
FROM dol.schedule_a sa
WHERE sa.sponsor_state = 'MD'
  AND sa.ins_broker_comm_tot_amt > 0;
```

### Join DOL to Pipeline

```sql
-- Match DOL filing to outreach company
SELECT
    o.outreach_id,
    o.domain,
    f.sponsor_dfe_name,
    f.tot_active_partcp_cnt,
    sa.ins_carrier_name,
    sa.ins_broker_comm_tot_amt
FROM outreach.outreach o
JOIN dol.form_5500 f ON o.ein = f.sponsor_dfe_ein
LEFT JOIN dol.schedule_a sa ON f.sponsor_dfe_ein = sa.sch_a_ein AND f.form_year = sa.form_year
WHERE o.outreach_id = 'your-outreach-id';
```

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


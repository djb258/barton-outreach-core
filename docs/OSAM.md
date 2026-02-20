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
| Is email verified? | `people.people_master` | `email_verified = TRUE` |
| Is email outreach-ready? | `people.people_master` | `outreach_ready = TRUE` |
| Email needs re-enrichment? | `people.people_master` | `email_verified = FALSE` |
| RISKY (catch-all) emails? | `people.people_master` | `email_verified = TRUE AND outreach_ready = FALSE` |
| DOL filing status/carrier/broker/funding? | `outreach.dol` | outreach_id |
| EIN for company? | `outreach.outreach` (72% coverage, 69,233 EINs) | - |
| ICP-filtered filings? | `dol.form_5500_icp_filtered` | Direct (MV, 24,892 rows) |
| Form 5500 filing details? | `dol.form_5500` / `dol.form_5500_sf` | EIN direct (no intermediate join needed) |
| Insurance carrier data? | `dol.schedule_a` | EIN → form_5500.ack_id → schedule_a.ack_id |
| Service provider compensation? | `dol.schedule_c` + sub-tables | EIN → form_5500.ack_id → schedule_c.ack_id |
| DFE participation? | `dol.schedule_d` + sub-tables | EIN → form_5500.ack_id → schedule_d.ack_id |
| Financial transactions? | `dol.schedule_g` + sub-tables | EIN → form_5500.ack_id → schedule_g.ack_id |
| Large plan financials? | `dol.schedule_h` + sub-tables | EIN → form_5500.ack_id → schedule_h.ack_id |
| Small plan financials? | `dol.schedule_i` + sub-tables | EIN → form_5500.ack_id → schedule_i.ack_id |
| DOL column meaning? | `dol.column_metadata` | Direct (registry, 1,081 entries) |
| EIN → URL/domain lookup? | `dol.ein_urls` | EIN direct (127,909 rows) |
| Company news/blog URLs? | `outreach.blog` | outreach_id |
| Company name/domain? | `cl.company_identity` | sovereign_company_id |
| Employee count/size band? | `outreach.company_target` | `employees` column |
| Domain reachable? | `vendor.blog` | `source_table = 'outreach.sitemap_discovery'` |
| Has sitemap? | `vendor.blog` | `source_table = 'outreach.sitemap_discovery' AND has_sitemap = TRUE` |
| About/press/leadership URLs? | `vendor.blog` | `source_table = 'company.company_source_urls'` |
| Hunter company data (raw)? | `vendor.ct` | `source_table = 'enrichment.hunter_company'` |
| Hunter contact data (raw)? | `vendor.people` | `source_table = 'enrichment.hunter_contact'` |
| CL domain/name/candidate data? | `vendor.ct_claude` | source_table discriminator |
| Company LinkedIn URL? | `cl.company_identity` | `linkedin_company_url` column |
| Person LinkedIn URL? | `people.people_master` | `linkedin_url` via company_slot |
| Companies in ZIP+radius? | `outreach.company_target` + `reference.us_zip_codes` | Haversine on lat/lng, match via postal_code |
| Database overview (full/market)? | See `docs/DATABASE_OVERVIEW_TEMPLATE.md` | Standard view template |
| Readiness funnel (can we reach anyone)? | `people.company_slot` + `people.people_master` | outreach_id, check email/LinkedIn |

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
- "How many employees does this company have?" → `employees` column (74.8% coverage)
- "Employee size band?" → `employees >= 50` for target market, bands: 50-100, 101-250, 501-1000, 1001-5000, 5001+
- "Company count by state/city?"
- "Which companies are pending execution?"
- "Email method for company?" → `email_method` column (86.0% coverage)

**CT Live Metrics (2026-02-13)**:
| Metric | Count | % |
|--------|-------|---|
| Has Employee Data | 70,392 | 74.8% |
| 50+ Employees | 37,493 | 39.8% |
| Total Employees (50+) | 16,205,443 | — |
| Email Method | 80,950 | 86.0% |

---

### SUB-HUB: DOL Filings - 04.04.03

The DOL sub-hub has **4 core tables** per CTB Leaf Lock:

| Role | Table | Purpose |
|------|-------|---------|
| CANONICAL | `outreach.dol` | DOL filing facts per outreach_id |
| ERRORS | `outreach.dol_errors` | DOL pipeline errors |
| MV | `dol.form_5500_icp_filtered` | ICP-filtered filing view |
| REGISTRY | `dol.column_metadata` | Column descriptions (1,081 entries) |

```
Canonical Table: outreach.dol
PK:    dol_id (uuid)
FK:    outreach_id → outreach.outreach
```

**Owns (Form 5500 + Benefits Data)**:
| Column | Type | Description | Fill Rate |
|--------|------|-------------|----------|
| dol_id | uuid | DOL record ID | 100% |
| outreach_id | uuid | **Join to spine** | 100% |
| ein | text | Federal EIN (9-digit, no dashes) | 100% (70,150) |
| filing_present | boolean | Has Form 5500 filing | 92% (64,975) |
| funding_type | text | `fully_insured` / `self_funded` / `pension_only` | 100% (70,150) |
| broker_or_advisor | text | Current broker/advisor name (from Schedule C) | 10% (6,995) |
| carrier | text | Insurance carrier name (from Schedule A) | 14.6% (10,233) |
| renewal_month | integer | Plan year begin month (1-12). Derived from most recent filing | 100% (70,142) |
| outreach_start_month | integer | 5 months before renewal (1-12). Communication trigger month | 100% (70,142) |

**Funding Type Breakdown**:
| Type | Count | Meaning |
|------|-------|---------|
| `pension_only` | 55,405 | Retirement plan only — no health insurance |
| `fully_insured` | 11,735 | Has health carrier on Schedule A |
| `self_funded` | 3,002 | Files health plan but no carrier — self-insured |

**Ask DOL**:
- "Does this company have a DOL filing?" → `filing_present`
- "What's the funding type?" → `funding_type`
- "Who is the current broker?" → `broker_or_advisor` (10% fill — large filers only)
- "What carrier do they use?" → `carrier` (14.6% fill — large filers with Schedule A)
- "When does this company renew?" → `renewal_month` (1=Jan, 12=Dec)
- "Who should I start reaching out to THIS month?" → `outreach_start_month`

**Renewal Month Distribution** (plan year begin month, most recent filing):
| Month | EINs | Outreach Start |
|-------|------|----------------|
| Jan (1) | 60,777 | Aug (8) |
| May (5) | 2,369 | Dec (12) |
| Jun (6) | 1,773 | Jan (1) |
| Jul (7) | 1,686 | Feb (2) |
| All others | 3,537 | Various |
| **Total** | **70,142** | **100% filled** |

**DOL Live Metrics (2026-02-13)**:
| Metric | Count | % |
|--------|-------|---|
| DOL Linked (EIN) | 73,617 | 78.2% of companies |
| Has Filing | 69,318 | 94.2% of DOL |
| Renewal Month | 69,029 | 93.8% of DOL |
| Carrier | 9,991 | 13.6% of DOL |
| Broker/Advisor | 6,818 | 9.3% of DOL |

**Note**: DOL can have multiple records per outreach_id (multiple filing years). Carrier/broker fill rates are lower because 79% of matched companies are pension-only filers without Schedule A/C data. DOL sub-metrics cascade off DOL Linked, not CT total.

**Supportive Reference Data**: 27 DOL filing/utility tables in `dol.*` schema are ALL queryable via EIN or ack_id. They are NOT sub-hub members. See DOL section below.

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
- "Does this company have a sitemap?" → `vendor.blog` WHERE `source_table = 'outreach.sitemap_discovery'` AND `has_sitemap = TRUE`
- "Is the domain reachable?" → `vendor.blog` WHERE `source_table = 'outreach.sitemap_discovery'` → `domain_reachable`
- "About/press/leadership/team/careers/contact URLs?" → `vendor.blog` WHERE `source_table = 'company.company_source_urls'`
- "Company LinkedIn URL?" → `cl.company_identity.linkedin_company_url`

**Blog Live Metrics (2026-02-13)**:
| Metric | Count | % |
|--------|-------|---|
| Blog Coverage | 93,596 | 99.4% |
| Companies with Sitemap | 31,679 | 33.7% |
| Companies with Source URLs | 40,381 | 42.9% |
| Company LinkedIn | 45,057 | 47.9% |
| Domain Reachable | 52,870 | 85.4% of checked |

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
- "How many people have verified emails?" → `email_verified = TRUE`
- "How many people are outreach ready?" → `outreach_ready = TRUE`
- "How many people are missing LinkedIn?"

**People Readiness Funnel (2026-02-13)**:
| Step | Count | % |
|------|-------|---|
| Total Companies | 94,129 | 100% |
| At Least 1 Slot Filled | 63,648 | 67.6% |
| At Least 1 Person Reachable | 60,180 | 63.9% |
| Zero Slots (unreachable) | 30,481 | 32.4% |

**Reachable** = has a verified email (outreach_ready = TRUE) OR a LinkedIn URL for at least one filled slot.

**Depth of Coverage**: See `docs/DATABASE_OVERVIEW_TEMPLATE.md` for the per-company depth analysis (all 3 filled, 2 of 3, 1 of 3) with email/LinkedIn/full coverage breakdowns.

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

## Vendor Schema (Tier-1 Staging)

> **Phase 3 Legacy Collapse (2026-02-20)**: All external vendor data consolidated into `vendor.*` schema. These are append-only staging tables with `source_table` discriminator identifying the original source.

| Vendor Table | Rows | Sources | Query For |
|--------------|------|---------|-----------|
| `vendor.ct` | 225,904 | Hunter companies, company_master, intake CSVs | Raw company data, LinkedIn URLs |
| `vendor.people` | 843,744 | Hunter contacts, Clay CSV, scraped names | Raw people/contact data |
| `vendor.blog` | 289,624 | Sitemaps, source URLs, company_source_urls | Raw URL discovery data |
| `vendor.ct_claude` | 262,944 | CL domains, names, candidates, confidence | CL enrichment outputs |
| `vendor.people_claude` | 33,217 | Enrichment queues, resolution queues | People enrichment queue data |
| `vendor.dol_claude` | 16 | DOL URL enrichment | DOL enrichment outputs |
| `vendor.blog_claude` | 0 | (future) | Blog enrichment outputs |
| `vendor.lane_claude` | 0 | (future) | Lane enrichment outputs |

**Query Pattern**: All vendor tables have a `source_table` column (e.g., `'enrichment.hunter_company'`) to filter by origin.

```sql
-- Example: Get Hunter company data for a domain
SELECT * FROM vendor.ct
WHERE source_table = 'enrichment.hunter_company' AND domain = 'example.com';

-- Example: Get all source URLs for an outreach_id
SELECT source_type, source_url FROM vendor.blog
WHERE source_table = 'company.company_source_urls' AND company_unique_id = 'xxx';
```

### Enrichment Tables (Legacy — data copied to vendor)

| Table | Purpose | Query Directly? |
|-------|---------|-----------------|
| enrichment.hunter_company | Hunter.io company data | NO — data in `vendor.ct` |
| enrichment.hunter_contact | Hunter.io contact data | NO — data in `vendor.people` |

---

## DOL: Queryable Filing & Reference Data

> **These tables are NOT part of the DOL sub-hub.** They are queryable reference data that feeds INTO `outreach.dol` (the canonical table). The DOL sub-hub owns 4 tables: `outreach.dol`, `outreach.dol_errors`, `dol.form_5500_icp_filtered`, `dol.column_metadata`.

**Data Coverage**: 2023, 2024, 2025 — **11,124,508 total rows** across 27 data-bearing tables (+2 empty staging tables).
**Pipeline Reach**: 69,233 of 95,837 pipeline companies have EINs (72%). All 27 data-bearing tables are LIVE.
**EIN Format**: All EINs are 9-digit, no dashes (e.g., `832809723`). Matches across `outreach.outreach.ein`, `outreach.dol.ein`, and all `dol.*` tables.

### Join Paths (all working)

```
Path A (direct, preferred for ad-hoc):
  outreach.outreach.ein → dol.form_5500.sponsor_dfe_ein → any_schedule.ack_id
  outreach.outreach.ein → dol.form_5500_sf.sf_spons_ein → any_schedule.ack_id

Path B (via bridge, preferred for enriched data):
  outreach.outreach → outreach.dol (outreach_id) → dol.form_5500 (EIN) → schedules (ack_id)

Path C (URL lookup):
  outreach.outreach.ein → dol.ein_urls.ein
```

**Join Keys**:
- `ein` — Links pipeline to form_5500/form_5500_sf (9-digit, no dashes)
- `ack_id` — Links form_5500 to ALL schedule tables (universal DOL key)
- `form_year` — VARCHAR, filter any table by year ('2023', '2024', '2025')

**Metadata**: 100% column comments (1,081 columns), all documented in `dol.column_metadata`.

### Pipeline Reach by Entry Point

| Entry Point | Pipeline Companies Reachable |
|-------------|-----------------------------|
| `dol.form_5500` (large filers) | 14,763 |
| `dol.form_5500_sf` (small filers) | 57,290 |
| `dol.schedule_a` (insurance) | 9,987 |
| `dol.schedule_c` (service providers) | 9,312 |
| `dol.schedule_h` (large plan financials) | 8,860 |
| `dol.ein_urls` (EIN→URL lookup) | 55,798 |

### DOL Supportive Tables (27 data-bearing + 2 staging)

| Table | Records | Purpose |
|-------|---------|---------|
| **Core Filing** | | |
| dol.form_5500 | 432,582 | Full Form 5500 filings (large plans, 100+ participants) |
| dol.form_5500_sf | 1,535,999 | Short Form 5500-SF (small plans, <100 participants) |
| dol.form_5500_sf_part7 | 10,613 | SF Part 7 compliance questions |
| **Schedule A: Insurance** | | |
| dol.schedule_a | 625,520 | Insurance carriers, brokers, commissions, policy dates |
| dol.schedule_a_part1 | 380,509 | Schedule A Part 1 detail |
| **Schedule C: Service Provider Comp (10 tables)** | | |
| dol.schedule_c | 241,556 | Schedule C header |
| dol.schedule_c_part1_item1 | 396,838 | Direct compensation to service providers |
| dol.schedule_c_part1_item2 | 754,802 | Indirect compensation |
| dol.schedule_c_part1_item2_codes | 1,848,202 | Item 2 service type codes (code 28 = insurance broker) |
| dol.schedule_c_part1_item3 | 383,338 | Terminated service providers |
| dol.schedule_c_part1_item3_codes | 707,007 | Item 3 service type codes |
| dol.schedule_c_part2 | 4,593 | Other service provider compensation |
| dol.schedule_c_part2_codes | 2,352 | Part 2 service type codes |
| dol.schedule_c_part3 | 15,514 | Schedule C Part 3 (terminated providers detail) |
| **Schedule D: DFE Participation** | | |
| dol.schedule_d | 121,813 | Schedule D header (DFE participation) |
| dol.schedule_d_part1 | 808,051 | DFE investment details |
| dol.schedule_d_part2 | 2,392,112 | DFE filing details |
| dol.schedule_dcg | 235 | D/C/G cross-reference |
| **Schedule G: Financial Transactions** | | |
| dol.schedule_g | 568 | Schedule G header |
| dol.schedule_g_part1 | 784 | Large loans/fixed income defaults |
| dol.schedule_g_part2 | 97 | Fixed income obligations |
| dol.schedule_g_part3 | 469 | Non-exempt transactions |
| **Schedule H: Large Plan Financial** | | |
| dol.schedule_h | 169,276 | Large plan financial information |
| dol.schedule_h_part1 | 20,359 | H Part 1 detail |
| **Schedule I: Small Plan Financial** | | |
| dol.schedule_i | 116,493 | Small plan financial information |
| dol.schedule_i_part1 | 944 | I Part 1 detail |
| **Utility** | | |
| dol.ein_urls | 127,909 | EIN → URL/domain lookup |
| **Staging (empty, future use)** | | |
| dol.renewal_calendar | 0 | Renewal calendar staging |

### DOL Column Metadata (1,081 entries)

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

**Look up company by EIN (cross-year):**
```sql
-- Large filer (all years)
SELECT sponsor_dfe_name, spons_dfe_mail_us_state, tot_active_partcp_cnt, form_year
FROM dol.form_5500
WHERE sponsor_dfe_ein = '123456789'
ORDER BY form_year DESC;

-- Small filer (all years)
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

**Get service provider compensation from Schedule C:**
```sql
SELECT
    c.sponsor_dfe_ein,
    ci.provider_name,
    ci.direct_compensation_amt,
    c.form_year
FROM dol.schedule_c c
JOIN dol.schedule_c_part1_item1 ci ON c.ack_id = ci.ack_id AND c.form_year = ci.form_year
WHERE c.sponsor_dfe_ein = '123456789'
ORDER BY c.form_year DESC;
```

**Cross-year join pattern (any schedule to form_5500):**
```sql
SELECT f.sponsor_dfe_name, s.ins_carrier_name, f.form_year
FROM dol.form_5500 f
JOIN dol.schedule_a s ON f.ack_id = s.ack_id AND f.form_year = s.form_year
WHERE f.form_year IN ('2023', '2024', '2025');
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

## Multi-Source CLS Scoring & Message Personalization

Each sub-hub contributes signals to the CLS (Company Lifecycle Score, replacing BIT). When building a personalized message, query across sources to assemble the complete picture.

CLS is the single scoring/authorization engine across all **three messaging lanes**:
- **Cold Outreach**: 95,837 companies (`outreach.company_target`)
- **Appointments Already Had**: 771 records (`sales.appointments_already_had`)
- **Fractional CFO Partners**: 833 records (`partners.fractional_cfo_master`)

### CLS Signal Sources

| Source | Signal | Query |
|--------|--------|-------|
| DOL | PEPM (broker cost per employee) | `schedule_a + form_5500` |
| DOL | Participant count | `form_5500.tot_active_partcp_cnt` |
| DOL | Funding type | `schedule_a` benefit flags |
| CT | Industry | `company_target.industry` |
| CT | Employee count | `company_target.employees` |
| CT | State/Geography | `company_target.state` |
| Blog | Recent news | `blog.news_url`, `blog.context_summary` |
| Blog | About page | `blog.about_url` |
| People | Decision maker | `people_master.is_decision_maker` |
| People | Contact info | `people_master.email`, `linkedin_url` |

### Complete Company Profile Query

Pull all signals for a single company to build CLS score + message:

```sql
WITH company_dol AS (
    SELECT
        sa.sch_a_ein as ein,
        SUM(sa.ins_broker_comm_tot_amt) as total_broker_comm,
        MAX(f.tot_active_partcp_cnt) as dol_participants,
        CASE
            WHEN MAX(f.tot_active_partcp_cnt) > 0
            THEN (SUM(sa.ins_broker_comm_tot_amt) / MAX(f.tot_active_partcp_cnt)) / 12
            ELSE NULL
        END as pepm,
        MAX(sa.ins_carrier_name) as current_carrier
    FROM dol.schedule_a sa
    JOIN dol.form_5500 f ON sa.sch_a_ein = f.sponsor_dfe_ein AND sa.form_year = f.form_year
    WHERE sa.form_year = '2023'
    GROUP BY sa.sch_a_ein
)
SELECT
    -- Identity
    o.outreach_id,
    ci.company_name,
    o.ein,

    -- CT Signals
    ct.industry,
    ct.employees,
    ct.state,
    ct.city,

    -- DOL Signals
    cd.pepm,
    cd.total_broker_comm,
    cd.dol_participants,
    cd.current_carrier,

    -- Blog Signals
    b.about_url,
    b.news_url,
    b.context_summary,

    -- People Signals (CEO)
    pm.full_name as ceo_name,
    pm.email as ceo_email,
    pm.linkedin_url as ceo_linkedin,
    pm.is_decision_maker

FROM outreach.outreach o
JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
LEFT JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
LEFT JOIN company_dol cd ON o.ein = cd.ein
LEFT JOIN outreach.blog b ON b.outreach_id = o.outreach_id
LEFT JOIN people.company_slot cs ON cs.outreach_id = o.outreach_id AND cs.slot_type = 'CEO' AND cs.is_filled = true
LEFT JOIN people.people_master pm ON pm.unique_id = cs.person_unique_id
WHERE o.outreach_id = 'your-outreach-id';
```

### CLS Score Calculation Example

```sql
-- Calculate BIT score from multiple signals
SELECT
    o.outreach_id,
    ci.company_name,

    -- Individual signals (each becomes a "bit")
    CASE WHEN cd.pepm > 5.00 THEN 20 ELSE 0 END as pepm_signal,           -- High broker cost
    CASE WHEN ct.employees BETWEEN 50 AND 500 THEN 15 ELSE 0 END as size_signal,  -- Sweet spot size
    CASE WHEN b.news_url IS NOT NULL THEN 10 ELSE 0 END as news_signal,   -- Has recent news
    CASE WHEN cs.is_filled THEN 15 ELSE 0 END as contact_signal,          -- Have CEO contact
    CASE WHEN pm.email IS NOT NULL THEN 10 ELSE 0 END as email_signal,    -- Have email

    -- Combined BIT score
    (CASE WHEN cd.pepm > 5.00 THEN 20 ELSE 0 END +
     CASE WHEN ct.employees BETWEEN 50 AND 500 THEN 15 ELSE 0 END +
     CASE WHEN b.news_url IS NOT NULL THEN 10 ELSE 0 END +
     CASE WHEN cs.is_filled THEN 15 ELSE 0 END +
     CASE WHEN pm.email IS NOT NULL THEN 10 ELSE 0 END) as bit_score

FROM outreach.outreach o
JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
LEFT JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
LEFT JOIN company_dol cd ON o.ein = cd.ein  -- From CTE above
LEFT JOIN outreach.blog b ON b.outreach_id = o.outreach_id
LEFT JOIN people.company_slot cs ON cs.outreach_id = o.outreach_id AND cs.slot_type = 'CEO'
LEFT JOIN people.people_master pm ON pm.unique_id = cs.person_unique_id
ORDER BY bit_score DESC;
```

### Message Variable Assembly

Each query returns values that populate message templates:

| Variable | Source | Example Value |
|----------|--------|---------------|
| `{{ceo_name}}` | people_master.full_name | "Liz Coker" |
| `{{company_name}}` | cl.company_name | "3P Health, LLC" |
| `{{pepm}}` | DOL calculation | "$3,928.53" |
| `{{pepm_vs_median}}` | DOL calculation | "2,729x" |
| `{{employees}}` | company_target.employees | "17" |
| `{{industry}}` | company_target.industry | "Healthcare" |
| `{{recent_news}}` | blog.context_summary | "expanding operations" |
| `{{current_carrier}}` | schedule_a.ins_carrier_name | "Cigna" |

### Targeting Query: High-Value Prospects

Find companies with multiple positive signals:

```sql
WITH company_dol AS (
    -- PEPM calculation (same as above)
),
state_median AS (
    SELECT
        sponsor_state,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pepm) as median_pepm
    FROM company_dol
    GROUP BY sponsor_state
)
SELECT
    ci.company_name,
    ct.state,
    cd.pepm,
    sm.median_pepm,
    (cd.pepm / NULLIF(sm.median_pepm, 0)) as pepm_vs_median,
    ct.employees,
    pm.full_name as ceo_name,
    pm.email
FROM outreach.outreach o
JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
JOIN company_dol cd ON o.ein = cd.ein
JOIN state_median sm ON ct.state = sm.sponsor_state
JOIN people.company_slot cs ON cs.outreach_id = o.outreach_id AND cs.slot_type = 'CEO' AND cs.is_filled = true
JOIN people.people_master pm ON pm.unique_id = cs.person_unique_id
WHERE cd.pepm > sm.median_pepm * 2  -- PEPM 2x above median
  AND ct.employees BETWEEN 50 AND 500  -- Right size
  AND pm.email IS NOT NULL  -- Have contact
ORDER BY cd.pepm / sm.median_pepm DESC;
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

---

## CTB Registry (Governance)

> **Full CTB governance documentation**: [CTB_GOVERNANCE.md](CTB_GOVERNANCE.md)

For table governance and classification, query the CTB registry:

```sql
-- Find table's leaf type
SELECT table_schema, table_name, leaf_type, is_frozen
FROM ctb.table_registry
WHERE table_name = 'your_table';

-- All canonical tables
SELECT table_schema, table_name
FROM ctb.table_registry
WHERE leaf_type = 'CANONICAL';

-- Frozen core tables (immutable)
SELECT table_schema, table_name
FROM ctb.table_registry
WHERE is_frozen = TRUE;
```

| Leaf Type | Count | Description |
|-----------|-------|-------------|
| ARCHIVE | 96 | Archive tables |
| STAGING | 49 | Vendor data + DOL filings + intake |
| SYSTEM | 30 | System/metadata/audit |
| CANONICAL | 23 | Primary data tables (9 frozen) |
| DEPRECATED | 13 | Legacy (read-only) |
| REGISTRY | 12 | Lookup/reference (incl. LCS) |
| ERROR | 9 | Error tracking |
| MV | 3 | Materialized views |
| SUPPORTING | 3 | Operational data serving CANONICAL tables (ADR required) |
| **TOTAL** | **217** | **Post-Phase 3 (2026-02-20)** |

**Full Registry**: See `docs/audit/CTB_GUARDRAIL_MATRIX.csv`

---

## Version History

| Date | Change |
|------|--------|
| 2026-02-20 | Phase 3 Legacy Collapse: Added vendor schema section (8 tables, 1.6M rows). Updated query routing for dropped tables (sitemap_discovery, source_urls, company_source_urls → vendor.blog). Updated enrichment section (data in vendor.ct/vendor.people). Removed dol.pressure_signals (dropped). Updated CTB leaf type distribution (217 tables). |
| 2026-02-13 | Added CT sub-hub metrics (employee bands, domain health), blog metrics (sitemap, source URLs, company LinkedIn), DOL live metrics, people readiness funnel, geographic filtering reference, Database Overview Template reference |
| 2026-02-09 | Updated for three messaging lanes (Cold Outreach 95,837 + Appointments 771 + Fractional CFO 833). CLS replaces BIT as scoring engine. CL total 102,922. People 182,946 |
| 2026-02-06 | Added renewal_month + outreach_start_month to outreach.dol (70,142/70,150 = 100%). Outreach start = 5 months before renewal. 86.6% renew in January → outreach starts in August |
| 2026-02-06 | DOL bridge enrichment: normalized EINs (stripped dashes), populated carrier/broker_or_advisor/funding_type in outreach.dol. Synced EINs to outreach.outreach. Corrected filing table list (removed non-existent _ele tables, added actual _codes tables). Updated all row counts to match DB. Total: 27 data-bearing + 2 staging tables, 11.1M rows |
| 2026-02-06 | Corrected DOL sub-hub to 4 core tables (canonical/errors/MV/registry per CTB Leaf Lock). Reclassified filing tables as supportive reference data |
| 2026-02-06 | Added DOL filing table references, cross-year query examples, Schedule C examples |
| 2026-02-06 | Added CTB Registry section |
| 2026-02-05 | Initial OSAM creation |


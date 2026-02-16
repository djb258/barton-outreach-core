# PLE Spoke Details

Technical implementation details for each spoke in the PLE architecture.

---

## DOL Federal Data Spoke

**Status:** ✅ Production Ready
**Schema Version:** 2.0.0
**Import Date:** 2025-11-27

### Tables

#### 1. marketing.form_5500

**Purpose:** DOL Form 5500 filings for large retirement/welfare plans (≥100 participants)

**Coverage:** 230,009 records (2023 data)

**Key Columns:**
- `id` (serial PK)
- `ack_id` (varchar(30), unique) - DOL filing acknowledgment ID
- `company_unique_id` (text, nullable FK) - Matched company (quarantine pattern)
- `ein` (varchar(9), NOT NULL) - Employer ID (9 digits)
- `sponsor_name` (varchar(140)) - Company name from DOL
- `plan_name` (varchar(140))
- `state` (varchar(2))
- `participant_count` (integer) - Number of plan participants
- `total_assets` (numeric(15,2)) - Plan assets in dollars
- `form_year` (integer) - Filing year
- `raw_payload` (jsonb) - Complete DOL data
- `created_at`, `updated_at` (timestamptz)

**Indexes (5):**
- `idx_form_5500_ein` - EIN lookup (btree)
- `idx_form_5500_company_id` - Company FK joins (btree)
- `idx_form_5500_sponsor_name_lower` - Fuzzy name matching (btree)
- `idx_form_5500_state` - State filtering (btree)
- `idx_form_5500_raw_payload` - JSONB queries (gin)

**Constraints:**
- UNIQUE: `ack_id`
- CHECK: `ein ~ '^[0-9]{9}$'` (9 digits)
- FK: `company_unique_id` → `company_master.company_unique_id` (nullable, ON DELETE SET NULL)

**Match Rate:** ~50-70% to existing companies

---

#### 2. marketing.form_5500_sf

**Purpose:** DOL Form 5500-SF (Short Form) for small plans (<100 participants)

**Coverage:** 759,569 records (2023 data)

**Key Columns:**
- `id` (serial PK)
- `ack_id` (varchar(30), unique)
- `company_unique_id` (text, nullable FK)
- `sponsor_dfe_ein` (varchar(9), NOT NULL) - Sponsor EIN
- `sponsor_dfe_name` (varchar(140))
- `plan_name` (varchar(140))
- `spons_dfe_mail_us_state` (varchar(2))
- `plan_type_pension_ind` (varchar(1)) - '1' = pension plan
- `plan_type_welfare_ind` (varchar(1)) - '1' = welfare plan
- `tot_partcp_eoy_cnt` (integer) - Total participants at year end
- `form_year` (integer)
- `raw_payload` (jsonb)
- `created_at`, `updated_at` (timestamptz)

**Indexes (5):**
- `idx_form_5500_sf_ein` - EIN lookup (btree)
- `idx_form_5500_sf_company_id` - Company FK joins (btree)
- `idx_form_5500_sf_sponsor_name_lower` - Fuzzy name matching (btree)
- `idx_form_5500_sf_plan_type_pension` - Pension plan filter (partial)
- `idx_form_5500_sf_plan_type_welfare` - Welfare plan filter (partial)

**Constraints:**
- UNIQUE: `ack_id`
- CHECK: `sponsor_dfe_ein ~ '^[0-9]{9}$'`
- FK: `company_unique_id` → `company_master.company_unique_id` (nullable)

**Match Rate:** ~40-60% (lower due to smaller companies)

---

#### 3. marketing.schedule_a

**Purpose:** DOL Schedule A - Insurance information attached to Form 5500/5500-SF

**Coverage:** 336,817 records (2023 data)

**Key Columns:**
- `id` (serial PK)
- `ack_id` (varchar(30), NOT NULL) - Joins to form_5500 or form_5500_sf
- `sch_a_plan_year_begin_date` (date)
- `sch_a_plan_year_end_date` (date)
- `insurance_company_name` (varchar(140)) - Carrier name
- `insurance_company_ein` (varchar(9)) - Carrier EIN
- `contract_number` (varchar(50)) - Policy number
- `policy_year_begin_date` (date)
- `policy_year_end_date` (date) - **KEY: Renewal timing**
- `renewal_month` (integer, 1-12) - Derived from policy_year_end_date
- `renewal_year` (integer) - Derived from policy_year_end_date
- `covered_lives` (integer) - Number of covered lives
- `wlfr_bnft_health_ind` (varchar(1)) - '1' = health insurance
- `wlfr_bnft_dental_ind` (varchar(1)) - '1' = dental
- `wlfr_bnft_vision_ind` (varchar(1)) - '1' = vision
- `wlfr_bnft_life_ind` (varchar(1)) - '1' = life insurance
- `wlfr_bnft_stdisd_ind` (varchar(1)) - '1' = short-term disability
- `wlfr_bnft_ltdisd_ind` (varchar(1)) - '1' = long-term disability
- `insurance_commissions_fees` (numeric(15,2))
- `total_premiums_paid` (numeric(15,2))
- `raw_payload` (jsonb)
- `created_at` (timestamptz)

**Indexes (10):**
- `idx_schedule_a_ack_id` - Join to form_5500/form_5500_sf (btree)
- `idx_schedule_a_insurance_ein` - Carrier lookup (btree)
- `idx_schedule_a_insurance_name` - Carrier name search (btree)
- `idx_schedule_a_renewal_month` - Renewal timing queries (btree, partial)
- `idx_schedule_a_renewal_year` - Renewal year (btree, partial)
- `idx_schedule_a_renewal_timing` - Composite renewal index (btree, partial)
- `idx_schedule_a_raw_payload_gin` - JSONB queries (gin)
- `idx_schedule_a_health` - Health insurance filter (btree, partial)
- `idx_schedule_a_dental` - Dental filter (btree, partial)
- `idx_schedule_a_life` - Life insurance filter (btree, partial)

**Constraints:**
- CHECK: `insurance_company_ein IS NULL OR insurance_company_ein ~ '^[0-9]{9}$'`
- CHECK: `renewal_month IS NULL OR (renewal_month >= 1 AND renewal_month <= 12)`
- CHECK: `covered_lives IS NULL OR covered_lives >= 0`

**Renewal Data Quality:** ~60-80% of records have renewal_month populated

---

### Join Patterns

#### Pattern 1: Enrich Company with DOL Data

```sql
-- Get all DOL plan data for a company
SELECT
    cm.company_unique_id,
    cm.company_name,
    cm.ein,
    f5.plan_name as large_plan,
    f5.participant_count,
    fsf.plan_name as small_plan,
    fsf.tot_partcp_eoy_cnt
FROM marketing.company_master cm
LEFT JOIN marketing.form_5500 f5 ON f5.ein = cm.ein
LEFT JOIN marketing.form_5500_sf fsf ON fsf.sponsor_dfe_ein = cm.ein
WHERE cm.company_unique_id = '04.04.01.XX.XXXXX.XXX';
```

#### Pattern 2: Companies with Renewals in Next 90 Days

```sql
-- Hot renewal prospects
SELECT
    cm.company_unique_id,
    cm.company_name,
    f5.plan_name,
    sa.insurance_company_name,
    sa.renewal_month,
    sa.policy_year_end_date,
    (sa.policy_year_end_date - CURRENT_DATE) as days_to_renewal
FROM marketing.company_master cm
JOIN marketing.form_5500 f5 ON f5.ein = cm.ein
JOIN marketing.schedule_a sa ON sa.ack_id = f5.ack_id
WHERE sa.renewal_month IN (
    EXTRACT(MONTH FROM CURRENT_DATE),
    EXTRACT(MONTH FROM CURRENT_DATE + INTERVAL '1 month'),
    EXTRACT(MONTH FROM CURRENT_DATE + INTERVAL '2 months')
)
AND sa.renewal_year = EXTRACT(YEAR FROM CURRENT_DATE)
ORDER BY sa.policy_year_end_date;
```

#### Pattern 3: Quarantine Analysis (Unmatched Companies)

```sql
-- Find high-value unmatched DOL companies
SELECT
    ein,
    sponsor_name,
    state,
    participant_count,
    total_assets
FROM marketing.form_5500
WHERE company_unique_id IS NULL
AND state IN ('PA', 'VA', 'MD', 'OH', 'WV', 'KY')
AND participant_count >= 50
ORDER BY total_assets DESC;
```

---

## People Spoke (Sensors)

**Status:** ✅ Schema exists, enrichment in progress

### Tables

#### 1. marketing.company_slot

**Purpose:** Executive position slots (CEO, CFO, HR) per company

**Key Columns:**
- `company_slot_unique_id` (PK) - Barton ID: `04.04.05.XX.XXXXX.XXX`
- `company_unique_id` (FK) → `company_master.company_unique_id`
- `person_unique_id` (FK) → `people_master.unique_id` (nullable)
- `slot_type` (varchar) - 'CEO', 'CFO', 'HR'
- `is_filled` (boolean)
- `filled_at` (timestamptz)
- `last_refreshed_at` (timestamptz)

**Design Philosophy:** Phone and email belong to the **slot**, not the person. When a person leaves, the slot remains and needs refilling.

---

#### 2. marketing.people_master

**Purpose:** Contact records for executives

**Key Columns:**
- `unique_id` (PK) - Barton ID: `04.04.02.XX.XXXXX.XXX`
- `full_name` (text)
- `email` (varchar)
- `linkedin_url` (text)
- `title` (text)
- `company_unique_id` (FK) → `company_master.company_unique_id`

**Purpose:** Sensors that detect movement and scout new companies

---

#### 3. marketing.person_movement_history

**Purpose:** Audit trail of executive job changes

**Key Columns:**
- `movement_id` (PK)
- `person_unique_id` (FK)
- `from_company_unique_id` (FK)
- `to_company_unique_id` (FK)
- `from_title` (text)
- `to_title` (text)
- `movement_type` (varchar) - 'company_change', 'title_change', 'contact_lost'
- `detected_at` (timestamptz)

**Use Cases:**
- BIT scoring (movement = buying signal)
- Company discovery (scout new target when executive moves)
- Data quality (contact lost = re-enrichment needed)

---

## BIT Scoring Spoke

**Status:** ✅ Schema exists, scoring logic ready

### Tables

#### 1. marketing.person_scores

**Purpose:** Buyer intent scores per person/company

**Key Columns:**
- `person_unique_id` (FK)
- `company_unique_id` (FK)
- `bit_score` (integer, 0-100)
- `confidence_score` (integer, 0-100)
- `score_updated_at` (timestamptz)

---

#### 2. marketing.company_events

**Purpose:** Company signals (funding, layoffs, expansions)

**Key Columns:**
- `event_id` (PK)
- `company_unique_id` (FK)
- `event_type` (varchar) - 'funding', 'acquisition', 'ipo', 'layoff', etc.
- `event_payload` (jsonb)
- `detected_at` (timestamptz)

---

### BIT Scoring Logic (Placeholder)

**Renewal Date Impact:**

| Days to Renewal | BIT Boost | Status |
|-----------------|-----------|--------|
| 90-120 | +25 | APPROACHING |
| 60-90 | +35 | WARM |
| 30-60 | +50 | HOT |
| 0-30 | +40 | URGENT |
| Just renewed (-30 to 0) | -20 | DEAD |

**Other Factors:**
- Slot filled: +10 each
- Has Form 5500 data: +15
- Movement detected: +15
- Contact lost: -15

---

## Import & Maintenance

### DOL Data Refresh (Annual)

1. Download latest datasets from DOL FOIA
2. Run import scripts via `hubs/dol-filings/imo/middle/importers/import_dol_full.py`
3. Run matching procedures to link to company_master via EIN
4. Verify match rates and data quality

### People Data Refresh (Weekly)

1. Export from Clay with latest LinkedIn/contact data
2. Load to `intake.people_raw_from_clay`
3. Run validation and enrichment
4. Detect movement via Talent Flow Engine
5. Update BIT scores

---

## File Locations

**Import Scripts:**
- `hubs/dol-filings/imo/middle/importers/import_dol_full.py`
- `hubs/dol-filings/imo/middle/importers/build_column_metadata.py`

**Architecture Docs:**
- [docs/architecture/PLE_DATA_ARCHITECTURE.md](./PLE_DATA_ARCHITECTURE.md)
- [docs/architecture/SPOKE_DETAILS.md](./SPOKE_DETAILS.md) (this file)

---

**Last Updated:** 2025-11-27
**Database:** Neon PostgreSQL (Marketing DB)
**Schema Version:** 2.0.0

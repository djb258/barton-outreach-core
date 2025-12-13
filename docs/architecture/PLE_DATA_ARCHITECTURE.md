# PLE Data Architecture

**Status:** Production Ready
**Schema Version:** 2.0.0
**Last Updated:** 2025-11-27

---

## Core Doctrine

**The Company is the Product.**

Everything exists to enrich the company record. Two types of inputs:

### People = Sensors
- Detect movement (job changes, title changes)
- Reveal patterns (email patterns, org structure)
- Scout new companies (when executives move)
- **Serve the company record** (not standalone entities)

### Assets = Enrichment Data
- EIN (federal passport to all DOL data)
- Form 5500 (retirement plan filings)
- Schedule A (insurance policies + renewal dates)
- Violations, premiums, carriers
- Email patterns, digital footprint

**Rule:** People serve the company. Assets feed the company. The company grows.

---

## Hub-and-Spoke Architecture

```
                    COMPANY MASTER (HUB)
                    company_unique_id (internal)
                    ein (external/federal key)
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   DOL SPOKE        PEOPLE SPOKE        EMAIL SPOKE
 (Federal Data)     (Sensors)          (Patterns)
```

### Why This Pattern?

1. **Single Source of Truth** - All enrichment lands on `company_master`
2. **Loose Coupling** - Spokes can be added/removed without touching hub
3. **Quarantine Pattern** - Unmatched data lives in spoke until matched
4. **Federal Join Key** - EIN connects company to all government data

---

## Current Implementation

### Hub: Company Master

**Table:** `marketing.company_master`

**Key Columns:**
- `company_unique_id` (PK) - Barton ID: `04.04.01.XX.XXXXX.XXX`
- `ein` (External Key) - 9-digit federal EIN
- `company_name`, `address_state`, `employee_count`
- `created_at`, `updated_at`

**Purpose:** Master record for all validated companies in outreach pipeline

---

### Spoke 1: DOL Federal Data Spoke

**Status:** ✅ Implemented (Schema v2.0.0)

**Tables:**
1. `marketing.form_5500` - Large retirement plans (≥100 participants)
2. `marketing.form_5500_sf` - Small plans (<100 participants)
3. `marketing.schedule_a` - Insurance policies + renewal dates

**Join Key:** `ein` → `company_master.ein`

**Coverage:**
- 2.7M+ plan filings
- 150K+ unique EINs
- 336K+ insurance policies with renewal data

**Data Source:** US Department of Labor FOIA datasets (Annual)

**Pattern:** SIDECAR with nullable FK (quarantine pattern)
- `form_5500.company_unique_id` is nullable
- Unmatched sponsors stay in spoke until matched
- ON DELETE SET NULL preserves data integrity

**Key Fields for Outreach:**
- `schedule_a.policy_year_end_date` → Renewal timing
- `schedule_a.insurance_company_name` → Current carrier
- `schedule_a.covered_lives` → Plan size
- `form_5500.participant_count` → Employee retirement participation

---

### Spoke 2: People (Sensors)

**Status:** ✅ Core tables exist, enrichment in progress

**Tables:**
1. `marketing.company_slot` - Executive positions (CEO, CFO, HR)
2. `marketing.people_master` - Contact records
3. `marketing.person_movement_history` - Job change tracking

**Join Key:** `company_unique_id` → `company_master.company_unique_id`

**Purpose:**
- Detect when executives change companies → Scout new target companies
- Detect title changes → BIT score boost (role expansion signal)
- Track contact loss → Data quality + re-enrichment trigger

**Key Insight:** Phone/email belong to the **slot**, not the person. When a person leaves, the slot remains and needs refilling.

---

### Spoke 3: BIT Scoring

**Status:** ✅ Schema exists, scoring functions ready

**Tables:**
1. `marketing.person_scores` - Buyer intent scores per person
2. `marketing.company_events` - Signals (funding, layoffs, expansions)
3. `marketing.person_movement_history` - Movement signals

**Join Key:** `company_unique_id` / `person_unique_id`

**Purpose:** Calculate buyer intent based on:
- Renewal timing (30-90 days out = HOT)
- Executive movement
- Company events (funding, layoffs)
- Data completeness (slots filled, email verified)

---

## Key Relationships

### DOL Data → Company Enrichment

```
company_master.ein = form_5500.ein
    ↓
form_5500.ack_id = schedule_a.ack_id
    ↓
Extract: renewal_date, carrier, covered_lives
    ↓
Enrich: company_master with renewal timing
```

### People Data → Company Discovery

```
people_master detects job change
    ↓
New company discovered via LinkedIn
    ↓
Create new company_master record
    ↓
Backfill with DOL data via EIN match
```

---

## Database Quick Reference

### Core PLE Tables (6)

```
marketing.company_master          → Companies (hub)
marketing.company_slot            → Executive positions
marketing.people_master           → Contact records
marketing.person_movement_history → Job changes
marketing.person_scores           → BIT scores
marketing.company_events          → Company signals
```

### DOL Federal Data Spoke (3)

```
marketing.form_5500      → Large plans (230K records)
marketing.form_5500_sf   → Small plans (759K records)
marketing.schedule_a     → Insurance (336K records)
```

### Barton ID Formats

```
Companies: 04.04.01.XX.XXXXX.XXX
People:    04.04.02.XX.XXXXX.XXX
Slots:     04.04.05.XX.XXXXX.XXX
```

---

## Query Patterns

### Find Companies by Renewal Window

```sql
SELECT
    cm.company_name,
    cm.ein,
    sa.policy_year_end_date as renewal_date,
    sa.insurance_company_name as current_carrier,
    (sa.policy_year_end_date - CURRENT_DATE) as days_to_renewal
FROM marketing.company_master cm
JOIN marketing.form_5500 f5 ON f5.ein = cm.ein
JOIN marketing.schedule_a sa ON sa.ack_id = f5.ack_id
WHERE sa.policy_year_end_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '90 days'
ORDER BY sa.policy_year_end_date ASC;
```

### Find Unmatched DOL Companies (Quarantine)

```sql
SELECT
    ein,
    sponsor_name,
    state,
    participant_count
FROM marketing.form_5500
WHERE company_unique_id IS NULL
AND state IN ('PA', 'VA', 'MD', 'OH', 'WV', 'KY')
AND participant_count >= 50
ORDER BY participant_count DESC;
```

### Complete Company Enrichment Status

```sql
SELECT
    cm.company_unique_id,
    cm.company_name,
    cm.ein,
    CASE WHEN f5.id IS NOT NULL THEN 'Yes' ELSE 'No' END as has_form_5500,
    CASE WHEN sa.id IS NOT NULL THEN 'Yes' ELSE 'No' END as has_renewal_data,
    COUNT(DISTINCT cs.id) as slots_created,
    COUNT(DISTINCT cs.person_unique_id) as slots_filled
FROM marketing.company_master cm
LEFT JOIN marketing.form_5500 f5 ON f5.ein = cm.ein
LEFT JOIN marketing.schedule_a sa ON sa.ack_id = f5.ack_id
LEFT JOIN marketing.company_slot cs ON cs.company_unique_id = cm.company_unique_id
GROUP BY cm.company_unique_id, cm.company_name, cm.ein, f5.id, sa.id
ORDER BY slots_filled DESC;
```

---

## Import Process

See: [ctb/sys/enrichment/FORM_5500_COMPLETE_GUIDE.md](../../ctb/sys/enrichment/FORM_5500_COMPLETE_GUIDE.md)

**Quick Start:**
```bash
# 1. Download DOL datasets from FOIA
# 2. Place in data/ directory
# 3. Run import scripts
node ctb/sys/enrichment/create_schedule_a_table.js
python ctb/sys/enrichment/import_schedule_a.py
psql $NEON_CONNECTION_STRING -c "\COPY marketing.schedule_a_staging FROM 'output/schedule_a_2023_staging.csv' CSV HEADER;"
psql $NEON_CONNECTION_STRING -c "CALL marketing.process_schedule_a_staging();"
```

---

## Schema Documentation

**Visual ERD:** [repo-data-diagrams/DOL_SPOKE_ERD.md](../../repo-data-diagrams/DOL_SPOKE_ERD.md)
**Machine-Readable:** [repo-data-diagrams/ple_schema.json](../../repo-data-diagrams/ple_schema.json)
**Column Reference:** [repo-data-diagrams/PLE_SCHEMA_REFERENCE.md](../../repo-data-diagrams/PLE_SCHEMA_REFERENCE.md)

---

## Design Principles

1. **Company is King** - All enrichment serves the company record
2. **EIN is Federal Passport** - One EIN connects to all government data
3. **Quarantine Before Delete** - Unmatched data waits in spoke, never lost
4. **Slots Over People** - Phone/email belong to role, not person
5. **Renewal Date is Gold** - Highest-value signal for outreach timing

---

**Next:** See [SPOKE_DETAILS.md](./SPOKE_DETAILS.md) for technical implementation details per spoke.

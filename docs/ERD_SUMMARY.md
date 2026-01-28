# Database ERD Summary - Barton Outreach Core

**Generated**: 2026-01-28
**Database**: Marketing DB (Neon PostgreSQL)
**Host**: ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech

---

## Table of Contents

1. [Database Overview](#database-overview)
2. [Core Schema Architecture](#core-schema-architecture)
3. [Key Tables & Columns](#key-tables--columns)
4. [Foreign Key Relationships](#foreign-key-relationships)
5. [Primary Keys](#primary-keys)
6. [Row Counts](#row-counts)
7. [Schema List](#schema-list)

---

## Database Overview

### Statistics

- **Total Schemas**: 50 (excluding system schemas)
- **Total Tables**: 172
- **Total Views**: 56
- **Total Foreign Keys**: 62
- **Total Primary Keys**: 159
- **Total Indexes**: 677

### Operational Schemas (Doctrine v1.0)

| Schema | Purpose | Tables | Key Tables |
|--------|---------|--------|------------|
| **cl** | Company Lifecycle Authority Registry | 13 | company_identity, company_domains, company_names |
| **outreach** | Marketing Outreach Operational Spine | 45+ | outreach, company_target, dol, people, blog, bit_scores |
| **people** | People Intelligence & Slot Management | 20+ | people_master, company_slot, people_candidate |
| **dol** | DOL Filings & EIN Resolution | 8 | form_5500, schedule_a, ein_urls, renewal_calendar |
| **company** | Company Master & Events | 12 | company_master, company_sidecar, company_slots |
| **bit** | Buyer Intent Tracking | 4 | movement_events, proof_lines, authorization_log |
| **blog** | Content & Pressure Signals | 1 | pressure_signals |

---

## Core Schema Architecture

### CL Authority Registry (Parent Hub)

**Schema**: `cl`
**Purpose**: Identity pointers only - never workflow state

#### cl.company_identity (AUTHORITY REGISTRY)

**Primary Key**: `company_unique_id` (UUID)
**Rows**: 52,675

**Key Columns**:

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| company_unique_id | UUID | NO | Primary identifier (minted by CL) |
| sovereign_company_id | UUID | YES | Sovereign company ID (post-cleanup) |
| company_name | TEXT | NO | Company name |
| company_domain | TEXT | YES | Primary domain |
| normalized_domain | TEXT | YES | Normalized domain |
| linkedin_company_url | TEXT | YES | LinkedIn URL |
| source_system | TEXT | NO | Source system |
| outreach_id | UUID | YES | **WRITE-ONCE** pointer to outreach.outreach |
| sales_process_id | UUID | YES | **WRITE-ONCE** pointer to sales hub |
| client_id | UUID | YES | **WRITE-ONCE** pointer to client hub |
| outreach_attached_at | TIMESTAMPTZ | YES | When outreach_id was attached |
| sales_opened_at | TIMESTAMPTZ | YES | When sales_process_id was attached |
| client_promoted_at | TIMESTAMPTZ | YES | When client_id was attached |
| existence_verified | BOOLEAN | YES | Domain verification status |
| identity_status | TEXT | YES | Identity verification status (default: 'PENDING') |
| identity_pass | INTEGER | YES | Current pass number (default: 0) |
| eligibility_status | TEXT | YES | Marketing eligibility status |
| exclusion_reason | TEXT | YES | Why excluded from marketing |
| final_outcome | TEXT | YES | Final lifecycle outcome |
| entity_role | TEXT | YES | Entity role (SOVEREIGN/DUPLICATE/MERGED) |
| created_at | TIMESTAMPTZ | NO | Creation timestamp |

**Related Tables**:
- `cl.company_domains` (FK: company_unique_id → cl.company_identity)
- `cl.company_names` (FK: company_unique_id → cl.company_identity)
- `cl.identity_confidence` (FK: company_unique_id → cl.company_identity)

---

### Outreach Operational Spine (Child Hub)

**Schema**: `outreach`
**Purpose**: Workflow state and operational data

#### outreach.outreach (OPERATIONAL SPINE)

**Primary Key**: `outreach_id` (UUID)
**Rows**: 49,737

**Key Columns**:

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| outreach_id | UUID | NO | Primary identifier (minted by Outreach, registered in CL) |
| sovereign_id | UUID | NO | FK to cl.company_identity.sovereign_company_id |
| domain | VARCHAR(255) | YES | Company domain |
| created_at | TIMESTAMPTZ | NO | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | Last update timestamp |

**Note**: This is the operational spine. All sub-hubs FK to `outreach_id`.

**Child Tables**:
- `outreach.company_target` (FK: outreach_id)
- `outreach.dol` (FK: outreach_id)
- `outreach.people` (FK: outreach_id)
- `outreach.blog` (FK: outreach_id)
- `outreach.bit_scores` (FK: outreach_id)
- `outreach.bit_signals` (FK: outreach_id)
- `outreach.campaigns` (FK: outreach_id)
- `outreach.sequences` (FK: outreach_id)
- `outreach.send_log` (FK: outreach_id)

---

#### outreach.company_target (Sub-Hub 04.04.01)

**Primary Key**: `target_id` (UUID)
**Rows**: 45,816

**Key Columns**:

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| target_id | UUID | NO | Primary key |
| outreach_id | UUID | YES | FK to outreach.outreach |
| company_unique_id | TEXT | YES | Legacy reference (pre-sovereign) |
| email_method | VARCHAR(100) | YES | Email pattern (e.g., {f}{last}@{domain}) |
| method_type | VARCHAR(50) | YES | Pattern type (verified/hunter/clearbit) |
| confidence_score | NUMERIC(5,2) | YES | Pattern confidence (0.00-1.00) |
| is_catchall | BOOLEAN | YES | Whether domain is catch-all |
| outreach_status | TEXT | NO | Status (default: 'queued') |
| execution_status | VARCHAR(50) | YES | Execution status (default: 'pending') |
| bit_score_snapshot | INTEGER | YES | Snapshot of BIT score |
| sequence_count | INTEGER | NO | Number of sequences sent |
| active_sequence_id | TEXT | YES | Current active sequence |
| first_targeted_at | TIMESTAMPTZ | YES | First targeting timestamp |
| last_targeted_at | TIMESTAMPTZ | YES | Last targeting timestamp |
| imo_completed_at | TIMESTAMPTZ | YES | IMO completion timestamp |
| source | TEXT | YES | Data source |
| created_at | TIMESTAMPTZ | NO | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | Last update timestamp |

**Coverage**: 91.4% have email_method populated

---

#### outreach.dol (Sub-Hub 04.04.03)

**Primary Key**: `dol_id` (UUID)
**Rows**: 18,575

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| dol_id | UUID | Primary key |
| outreach_id | UUID | FK to outreach.outreach |
| ein | TEXT | Employer Identification Number |
| filing_id | TEXT | FK to dol.form_5500 |
| form_5500_matched | BOOLEAN | Whether Form 5500 was matched |
| schedule_a_matched | BOOLEAN | Whether Schedule A was matched |
| match_confidence | NUMERIC | Match confidence score |
| match_method | TEXT | How the match was made |
| created_at | TIMESTAMPTZ | Creation timestamp |
| updated_at | TIMESTAMPTZ | Last update timestamp |

**Coverage**: 27% of outreach spine has DOL data

---

#### outreach.people (Sub-Hub 04.04.02)

**Primary Key**: `person_id` (UUID)
**Rows**: 379

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| person_id | UUID | Primary key |
| outreach_id | UUID | FK to outreach.outreach |
| person_unique_id | TEXT | FK to people.people_master |
| slot_type | TEXT | Slot assignment (CEO/CFO/HR) |
| email | TEXT | Generated email |
| email_verified | BOOLEAN | Whether email was verified |
| linkedin_url | TEXT | LinkedIn profile URL |
| title | TEXT | Job title |
| seniority | TEXT | Seniority level |
| created_at | TIMESTAMPTZ | Creation timestamp |
| updated_at | TIMESTAMPTZ | Last update timestamp |

---

#### outreach.blog (Sub-Hub 04.04.05)

**Primary Key**: `blog_id` (UUID)
**Rows**: 46,468

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| blog_id | UUID | Primary key |
| outreach_id | UUID | FK to outreach.outreach |
| blog_url | TEXT | Blog URL |
| rss_feed_url | TEXT | RSS feed URL |
| last_checked_at | TIMESTAMPTZ | Last check timestamp |
| signal_count | INTEGER | Number of signals detected |
| created_at | TIMESTAMPTZ | Creation timestamp |
| updated_at | TIMESTAMPTZ | Last update timestamp |

**Coverage**: 100% of company_target have blog entries

---

#### outreach.bit_scores (Sub-Hub - BIT Engine)

**Primary Key**: `outreach_id` (UUID)
**Rows**: 15,032

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| outreach_id | UUID | PK & FK to outreach.outreach |
| bit_score | INTEGER | Current BIT score (0-100) |
| bit_tier | TEXT | Tier assignment (PLATINUM/GOLD/SILVER/BRONZE) |
| score_updated_at | TIMESTAMPTZ | Last score update |
| tier_assigned_at | TIMESTAMPTZ | Last tier assignment |
| signal_count | INTEGER | Number of signals |
| created_at | TIMESTAMPTZ | Creation timestamp |
| updated_at | TIMESTAMPTZ | Last update timestamp |

---

#### outreach.bit_signals (Signal Log)

**Primary Key**: `signal_id` (UUID)
**Rows**: 0 (currently empty)

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| signal_id | UUID | Primary key |
| outreach_id | UUID | FK to outreach.outreach |
| signal_type | TEXT | Signal type (DOL_FILING/BLOG_PRESSURE/MOVEMENT) |
| signal_impact | INTEGER | Impact score |
| signal_timestamp | TIMESTAMPTZ | When signal occurred |
| signal_hash | TEXT | Deduplication hash (24h window) |
| created_at | TIMESTAMPTZ | Creation timestamp |

---

#### outreach.manual_overrides (Kill Switch)

**Primary Key**: `override_id` (UUID)
**Rows**: 0

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| override_id | UUID | Primary key |
| outreach_id | UUID | FK to outreach.outreach |
| override_type | TEXT | Override type (EXCLUDE/INCLUDE/TIER_FORCE) |
| reason | TEXT | Override reason |
| applied_by | TEXT | Who applied the override |
| applied_at | TIMESTAMPTZ | When applied |
| expires_at | TIMESTAMPTZ | Expiration timestamp |
| is_active | BOOLEAN | Whether override is active |

---

#### outreach.override_audit_log (Audit Trail)

**Primary Key**: `audit_id` (UUID)
**Rows**: 0

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| audit_id | UUID | Primary key |
| override_id | UUID | FK to manual_overrides |
| action | TEXT | Action taken (APPLIED/REMOVED/EXPIRED) |
| performed_by | TEXT | Who performed the action |
| performed_at | TIMESTAMPTZ | When performed |
| notes | TEXT | Audit notes |

---

### People Intelligence Schema

**Schema**: `people`

#### people.people_master

**Primary Key**: `unique_id` (UUID)
**Rows**: 71,237

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| unique_id | UUID | Primary key |
| company_unique_id | UUID | FK to marketing.company_master |
| full_name | TEXT | Full name |
| first_name | TEXT | First name |
| last_name | TEXT | Last name |
| email | TEXT | Email address |
| email_verified | BOOLEAN | Whether email was verified |
| title | TEXT | Job title |
| seniority | TEXT | Seniority level |
| seniority_rank | INTEGER | Seniority rank (0-999) |
| linkedin_url | TEXT | LinkedIn profile URL |
| slot_type | TEXT | Assigned slot (CEO/CFO/HR) |
| data_quality_score | NUMERIC | Data quality score |
| created_at | TIMESTAMPTZ | Creation timestamp |
| updated_at | TIMESTAMPTZ | Last update timestamp |

**Foreign Key**: `company_unique_id` → `marketing.company_master.company_unique_id`

---

#### people.company_slot

**Primary Key**: `slot_id` (UUID)
**Rows**: 149,172

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| slot_id | UUID | Primary key |
| company_unique_id | UUID | FK to company.company_master |
| slot_type | TEXT | Slot type (CEO/CFO/HR/CTO/CMO/COO) |
| person_unique_id | UUID | FK to people.people_master |
| is_filled | BOOLEAN | Whether slot is filled |
| filled_at | TIMESTAMPTZ | When slot was filled |
| last_refreshed_at | TIMESTAMPTZ | Last refresh timestamp |
| created_at | TIMESTAMPTZ | Creation timestamp |
| updated_at | TIMESTAMPTZ | Last update timestamp |

**Slot Fill Rates**:
- CEO: 27.1%
- CFO: 8.6%
- HR: 13.7%

---

### DOL Filings Schema

**Schema**: `dol`

#### dol.form_5500

**Primary Key**: `filing_id` (TEXT)
**Rows**: 230,482

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| filing_id | TEXT | Primary key (composite from DOL) |
| ein | TEXT | Employer Identification Number |
| plan_name | TEXT | Plan name |
| sponsor_name | TEXT | Sponsor name |
| plan_year | INTEGER | Plan year |
| total_participants | INTEGER | Total participants |
| total_assets | NUMERIC | Total assets |
| filing_date | DATE | Filing date |

---

#### dol.schedule_a

**Primary Key**: `schedule_id` (UUID)
**Rows**: 337,476

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| schedule_id | UUID | Primary key |
| filing_id | TEXT | FK to form_5500 |
| ein | TEXT | Employer Identification Number |
| insurance_carrier_name | TEXT | Insurance carrier name |
| commission_amount | NUMERIC | Commission amount |
| policy_number | TEXT | Policy number |

---

#### dol.ein_urls

**Primary Key**: `ein` (TEXT)
**Rows**: Unknown (table exists but not queried for row count)

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| ein | TEXT | Primary key - Employer Identification Number |
| company_name | TEXT | Company name |
| url | TEXT | Company URL |
| source | TEXT | Data source |

---

#### dol.renewal_calendar

**Primary Key**: `renewal_id` (UUID)
**Rows**: Unknown

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| renewal_id | UUID | Primary key |
| filing_id | TEXT | FK to form_5500 |
| renewal_date | DATE | Renewal date |
| reminder_sent | BOOLEAN | Whether reminder was sent |
| created_at | TIMESTAMPTZ | Creation timestamp |

**Foreign Key**: `filing_id` → `dol.form_5500.filing_id`

---

## Foreign Key Relationships

### CL Authority Registry Relationships

| Source Table | Source Column | Target Table | Target Column | Description |
|--------------|---------------|--------------|---------------|-------------|
| cl.company_domains | company_unique_id | cl.company_identity | company_unique_id | Domain → Company |
| cl.company_names | company_unique_id | cl.company_identity | company_unique_id | Name → Company |
| cl.identity_confidence | company_unique_id | cl.company_identity | company_unique_id | Confidence → Company |

### Outreach Operational Spine Relationships

| Source Table | Source Column | Target Table | Target Column | Description |
|--------------|---------------|--------------|---------------|-------------|
| outreach.company_target | outreach_id | outreach.outreach | outreach_id | Target → Spine |
| outreach.dol | outreach_id | outreach.outreach | outreach_id | DOL → Spine |
| outreach.people | outreach_id | outreach.outreach | outreach_id | People → Spine |
| outreach.blog | outreach_id | outreach.outreach | outreach_id | Blog → Spine |
| outreach.bit_scores | outreach_id | outreach.outreach | outreach_id | BIT Scores → Spine |
| outreach.bit_signals | outreach_id | outreach.outreach | outreach_id | BIT Signals → Spine |
| outreach.manual_overrides | outreach_id | outreach.outreach | outreach_id | Overrides → Spine |
| outreach.bit_errors | outreach_id | outreach.outreach | outreach_id | BIT Errors → Spine |
| outreach.bit_input_history | outreach_id | outreach.outreach | outreach_id | BIT History → Spine |
| outreach.blog_errors | outreach_id | outreach.outreach | outreach_id | Blog Errors → Spine |
| outreach.company_target_errors | outreach_id | outreach.outreach | outreach_id | CT Errors → Spine |
| outreach.dol_errors | outreach_id | outreach.outreach | outreach_id | DOL Errors → Spine |
| outreach.people_errors | outreach_id | outreach.outreach | outreach_id | People Errors → Spine |
| outreach.outreach_errors | outreach_id | outreach.outreach | outreach_id | Outreach Errors → Spine |
| outreach.campaigns | outreach_id | outreach.outreach | outreach_id | Campaigns → Spine |
| outreach.sequences | outreach_id | outreach.outreach | outreach_id | Sequences → Spine |
| outreach.send_log | outreach_id | outreach.outreach | outreach_id | Send Log → Spine |
| outreach.engagement_events | outreach_id | outreach.outreach | outreach_id | Engagement → Spine |

### People Schema Relationships

| Source Table | Source Column | Target Table | Target Column | Description |
|--------------|---------------|--------------|---------------|-------------|
| people.people_master | company_unique_id | marketing.company_master | company_unique_id | Person → Company |

### DOL Schema Relationships

| Source Table | Source Column | Target Table | Target Column | Description |
|--------------|---------------|--------------|---------------|-------------|
| dol.renewal_calendar | filing_id | dol.form_5500 | filing_id | Renewal → Filing |

### Company Schema Relationships

| Source Table | Source Column | Target Table | Target Column | Description |
|--------------|---------------|--------------|---------------|-------------|
| company.company_events | company_unique_id | company.company_master | company_unique_id | Events → Company |
| company.company_sidecar | company_unique_id | company.company_master | company_unique_id | Sidecar → Company |
| company.company_slots | company_unique_id | company.company_master | company_unique_id | Slots → Company |
| company.contact_enrichment | company_slot_unique_id | company.company_slots | company_slot_unique_id | Enrichment → Slot |
| company.email_verification | enrichment_id | company.contact_enrichment | id | Verification → Enrichment |

---

## Primary Keys

### Key Tables Primary Keys

| Schema | Table | Primary Key Column | Type |
|--------|-------|--------------------|------|
| cl | company_identity | company_unique_id | UUID |
| cl | company_domains | domain_id | UUID |
| cl | company_names | name_id | UUID |
| outreach | outreach | outreach_id | UUID |
| outreach | company_target | target_id | UUID |
| outreach | dol | dol_id | UUID |
| outreach | people | person_id | UUID |
| outreach | blog | blog_id | UUID |
| outreach | bit_scores | outreach_id | UUID |
| outreach | bit_signals | signal_id | UUID |
| outreach | manual_overrides | override_id | UUID |
| outreach | override_audit_log | audit_id | UUID |
| people | people_master | unique_id | UUID |
| people | company_slot | slot_id | UUID |
| dol | form_5500 | filing_id | TEXT |
| dol | schedule_a | schedule_id | UUID |
| dol | ein_urls | ein | TEXT |
| dol | renewal_calendar | renewal_id | UUID |

---

## Row Counts (Key Tables)

| Table | Rows | Coverage Notes |
|-------|------|----------------|
| cl.company_identity | 52,675 | Authority registry |
| outreach.outreach | 49,737 | Operational spine (aligned post-cleanup) |
| outreach.company_target | 45,816 | 91.4% have email_method |
| outreach.dol | 18,575 | 27% DOL coverage |
| outreach.people | 379 | People in outreach pipeline |
| outreach.blog | 46,468 | 100% coverage |
| outreach.bit_scores | 15,032 | BIT scores assigned |
| outreach.bit_signals | 0 | Signal log (empty) |
| outreach.manual_overrides | 0 | Kill switches (empty) |
| outreach.override_audit_log | 0 | Audit trail (empty) |
| people.company_slot | 149,172 | Slot assignments |
| people.people_master | 71,237 | People records |
| dol.form_5500 | 230,482 | Form 5500 filings |
| dol.schedule_a | 337,476 | Schedule A records |

**Alignment Status**: CL-Outreach alignment = 51,148 = 51,148 (post-sovereign cleanup on 2026-01-21)

---

## Schema List

### Operational Schemas (16)

1. **archive** - Archive tables from migrations
2. **bit** - Buyer Intent Tracking
3. **blog** - Content & Pressure Signals
4. **catalog** - Schema metadata catalog
5. **cl** - Company Lifecycle Authority Registry
6. **client** - Client hub (future)
7. **company** - Company Master & Events
8. **company_target** - Legacy schema (migrated to outreach)
9. **dol** - DOL Filings & EIN Resolution
10. **intake** - Data intake & validation
11. **marketing** - Legacy marketing schema
12. **outreach** - Marketing Outreach Operational Spine
13. **outreach_ctx** - Outreach context tracking
14. **people** - People Intelligence & Slot Management
15. **ref** - Reference data
16. **shq** - Schema Headquarters (metadata)
17. **talent_flow** - Talent flow tracking

### System Schemas (34)

- **public** - Default PostgreSQL schema
- **pg_temp_*** - Temporary schemas (24 schemas)
- **pg_toast_temp_*** - TOAST temporary schemas (10 schemas)

---

## Key Views

### Outreach Schema Views

| View | Purpose |
|------|---------|
| vw_marketing_eligibility_with_overrides | **AUTHORITATIVE** - Marketing eligibility with kill switch |
| vw_sovereign_completion | Sovereign entity completion status |
| vw_bit_tier_distribution | BIT tier distribution |
| vw_company_target_status | Company target status summary |
| vw_dol_coverage | DOL coverage summary |
| vw_people_slot_coverage | People slot coverage summary |

### CL Schema Views

| View | Purpose |
|------|---------|
| v_company_lifecycle_status | **READ-ONLY** - Hub claim status |
| v_company_domains | Company domains view |
| v_company_names | Company names view |

---

## Important Notes

### Doctrine Rules (v1.0 FROZEN)

1. **CL is AUTHORITY REGISTRY** - Stores identity pointers only (outreach_id, sales_process_id, client_id)
2. **CL mints sovereign_company_id** - Outreach receives, never creates
3. **Outreach mints outreach_id** - Written to CL ONCE, workflow state stays in outreach.outreach
4. **outreach.outreach is operational spine** - All sub-hubs FK to outreach_id
5. **WRITE-ONCE to CL** - Each hub mints its ID and registers ONCE
6. **No sub-hub writes without valid outreach_id**

### Frozen Components (DO NOT MODIFY)

- `outreach.vw_marketing_eligibility_with_overrides` (authoritative view)
- `outreach.vw_sovereign_completion` (sovereign view)
- Tier computation logic and assignment rules
- Kill switch system (manual_overrides, override_audit_log)
- Marketing safety gate (HARD_FAIL enforcement)
- Hub registry and waterfall order

### Post-Cleanup State (2026-01-21)

- 23,025 orphaned outreach_ids archived
- CL-Outreach alignment restored: 51,148 = 51,148
- Archive tables created for all affected entities
- Safe to enable live marketing: **YES**

---

## Full Export Data

The complete database schema export is available in JSON format:

**File**: `docs/database_erd_export.json`

This file contains:
- All schemas
- All tables
- All columns with data types
- All foreign key relationships
- All primary keys
- All unique constraints
- All indexes
- Row counts for key tables
- Views

---

**Document Generated**: 2026-01-28
**Last Updated**: 2026-01-28
**Status**: v1.0 OPERATIONAL BASELINE (CERTIFIED + FROZEN)

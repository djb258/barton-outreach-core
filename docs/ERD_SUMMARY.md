# Database ERD Summary - Barton Outreach Core

**Generated**: 2026-01-28
**Database**: Marketing DB (Neon PostgreSQL)
**Host**: ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech

---

## Constitutional Compliance (IMO-Creator v1.0)

| Field | Value |
|-------|-------|
| **Doctrine Version** | IMO-Creator v1.0 |
| **Domain Spec Reference** | `doctrine/REPO_DOMAIN_SPEC.md` |
| **ERD Constitution** | `templates/doctrine/ERD_CONSTITUTION.md` |
| **ERD Doctrine** | `templates/doctrine/ERD_DOCTRINE.md` |
| **Governing PRD** | `docs/prd/PRD_COMPANY_HUB.md`, `docs/prd/PRD_SOVEREIGN_COMPLETION.md` |

---

## Pressure Test Results (Constitutional Validation)

_Per ERD Doctrine: Every table must answer 4 questions to prove structural validity._

### CL Authority Registry Tables

#### cl.company_identity

| Question | Answer |
|----------|--------|
| **Q1: What constant(s) does this table depend on?** | External company data from intake CSV, LinkedIn API responses, domain verification results |
| **Q2: What variable does this table represent?** | `sovereign_company_id` (minted identity), `identity_status`, `eligibility_status`, `outreach_id` (write-once pointer) |
| **Q3: Which pass produced this table?** | CAPTURE (intake) + COMPUTE (identity resolution) + GOVERN (eligibility determination) |
| **Q4: How is lineage enforced?** | `company_unique_id` is PK, `outreach_id` is WRITE-ONCE with `outreach_attached_at` timestamp |

#### cl.company_domains / cl.company_names

| Question | Answer |
|----------|--------|
| **Q1: What constant(s) does this table depend on?** | Raw domain/name data from intake, DNS verification results |
| **Q2: What variable does this table represent?** | Domain variants, name variants with type classification |
| **Q3: Which pass produced this table?** | COMPUTE (domain/name normalization) |
| **Q4: How is lineage enforced?** | FK to `cl.company_identity.company_unique_id` |

### Outreach Operational Spine Tables

#### outreach.outreach

| Question | Answer |
|----------|--------|
| **Q1: What constant(s) does this table depend on?** | `sovereign_company_id` from CL |
| **Q2: What variable does this table represent?** | `outreach_id` (minted by Outreach), operational workflow state |
| **Q3: Which pass produced this table?** | CAPTURE (CL identity reception) + GOVERN (operational spine initialization) |
| **Q4: How is lineage enforced?** | `sovereign_id` FK to CL, `outreach_id` registered back to CL (WRITE-ONCE) |

#### outreach.company_target

| Question | Answer |
|----------|--------|
| **Q1: What constant(s) does this table depend on?** | `outreach_id`, domain from CL, DNS/MX verification results, pattern discovery API responses |
| **Q2: What variable does this table represent?** | `email_method` (verified pattern), `confidence_score`, `outreach_status`, `execution_status` |
| **Q3: Which pass produced this table?** | CAPTURE (pattern discovery intake) + COMPUTE (domain resolution, pattern verification) |
| **Q4: How is lineage enforced?** | FK `outreach_id` to `outreach.outreach`, `imo_completed_at` timestamp |

#### outreach.dol

| Question | Answer |
|----------|--------|
| **Q1: What constant(s) does this table depend on?** | `outreach_id`, federal DOL Form 5500 data |
| **Q2: What variable does this table represent?** | EIN match result, `form_5500_matched`, `schedule_a_matched`, `match_confidence` |
| **Q3: Which pass produced this table?** | CAPTURE (DOL data ingestion) + COMPUTE (EIN matching) |
| **Q4: How is lineage enforced?** | FK `outreach_id`, FK `filing_id` to `dol.form_5500` |

#### outreach.people

| Question | Answer |
|----------|--------|
| **Q1: What constant(s) does this table depend on?** | `outreach_id`, person data from People Hub, slot requirements |
| **Q2: What variable does this table represent?** | Slot assignment, `email` (generated), `email_verified` status |
| **Q3: Which pass produced this table?** | CAPTURE (slot requirements) + COMPUTE (email generation, slot assignment) |
| **Q4: How is lineage enforced?** | FK `outreach_id`, FK `person_unique_id` to `people.people_master` |

#### outreach.blog

| Question | Answer |
|----------|--------|
| **Q1: What constant(s) does this table depend on?** | `outreach_id`, external RSS/blog crawl results |
| **Q2: What variable does this table represent?** | Blog presence detection, `signal_count` |
| **Q3: Which pass produced this table?** | CAPTURE (blog crawl) + COMPUTE (signal detection) |
| **Q4: How is lineage enforced?** | FK `outreach_id`, `last_checked_at` timestamp |

#### outreach.bit_scores

| Question | Answer |
|----------|--------|
| **Q1: What constant(s) does this table depend on?** | `outreach_id`, signals from DOL/People/Blog sub-hubs |
| **Q2: What variable does this table represent?** | `bit_score` (0-100), `bit_tier` (PLATINUM/GOLD/SILVER/BRONZE) |
| **Q3: Which pass produced this table?** | COMPUTE (signal aggregation, score calculation) |
| **Q4: How is lineage enforced?** | PK/FK `outreach_id`, `score_updated_at` timestamp |

#### outreach.bit_signals

| Question | Answer |
|----------|--------|
| **Q1: What constant(s) does this table depend on?** | `outreach_id`, signal events from sub-hubs |
| **Q2: What variable does this table represent?** | Individual signal records with type, impact, dedup hash |
| **Q3: Which pass produced this table?** | CAPTURE (signal reception from sub-hubs) |
| **Q4: How is lineage enforced?** | FK `outreach_id`, `signal_hash` for 24h deduplication |

#### outreach.manual_overrides (Kill Switch)

| Question | Answer |
|----------|--------|
| **Q1: What constant(s) does this table depend on?** | `outreach_id`, human operator decisions |
| **Q2: What variable does this table represent?** | Marketing restriction state, `override_type`, `is_active` |
| **Q3: Which pass produced this table?** | CAPTURE (override request) + GOVERN (enforcement) |
| **Q4: How is lineage enforced?** | FK `outreach_id`, `applied_at` + `applied_by` audit fields |

#### outreach.override_audit_log

| Question | Answer |
|----------|--------|
| **Q1: What constant(s) does this table depend on?** | `override_id`, action events |
| **Q2: What variable does this table represent?** | Audit trail records (append-only) |
| **Q3: Which pass produced this table?** | GOVERN (audit logging) |
| **Q4: How is lineage enforced?** | FK `override_id`, append-only (no UPDATE/DELETE), `performed_at` timestamp |

### People Intelligence Tables

#### people.people_master

| Question | Answer |
|----------|--------|
| **Q1: What constant(s) does this table depend on?** | Intake CSV person data, LinkedIn profile data |
| **Q2: What variable does this table represent?** | Person identity, `email`, `email_verified`, `slot_type` assignment |
| **Q3: Which pass produced this table?** | CAPTURE (person intake) + COMPUTE (dedup, email generation) |
| **Q4: How is lineage enforced?** | `unique_id` PK, FK `company_unique_id` |

#### people.company_slot

| Question | Answer |
|----------|--------|
| **Q1: What constant(s) does this table depend on?** | `company_unique_id`, slot requirements from Company Target |
| **Q2: What variable does this table represent?** | Slot fill state, `is_filled`, `person_unique_id` assignment |
| **Q3: Which pass produced this table?** | COMPUTE (slot assignment algorithm) |
| **Q4: How is lineage enforced?** | FK `company_unique_id`, FK `person_unique_id`, `filled_at` timestamp |

### DOL Filings Tables

#### dol.form_5500

| Question | Answer |
|----------|--------|
| **Q1: What constant(s) does this table depend on?** | Federal DOL bulk download files |
| **Q2: What variable does this table represent?** | Parsed filing records with EIN, plan details |
| **Q3: Which pass produced this table?** | CAPTURE (federal data ingestion) |
| **Q4: How is lineage enforced?** | `filing_id` PK (composite from DOL), immutable source data |

#### dol.schedule_a

| Question | Answer |
|----------|--------|
| **Q1: What constant(s) does this table depend on?** | Federal DOL Schedule A data, `filing_id` |
| **Q2: What variable does this table represent?** | Insurance carrier details, commission data |
| **Q3: Which pass produced this table?** | CAPTURE (Schedule A extraction) |
| **Q4: How is lineage enforced?** | FK `filing_id` to `dol.form_5500` |

#### dol.renewal_calendar

| Question | Answer |
|----------|--------|
| **Q1: What constant(s) does this table depend on?** | `filing_id`, calculated renewal dates |
| **Q2: What variable does this table represent?** | Renewal tracking state, `reminder_sent` |
| **Q3: Which pass produced this table?** | COMPUTE (renewal date calculation) + GOVERN (reminder tracking) |
| **Q4: How is lineage enforced?** | FK `filing_id` to `dol.form_5500` |

---

## Pass-to-Table Mapping

| Pass | IMO Layer | Tables Owned |
|------|-----------|--------------|
| **CAPTURE** | I (Ingress) | `cl.company_identity` (intake), `outreach.outreach`, `outreach.bit_signals`, `dol.form_5500`, `dol.schedule_a`, `people.people_master` (intake) |
| **COMPUTE** | M (Middle) | `outreach.company_target`, `outreach.dol`, `outreach.people`, `outreach.blog`, `outreach.bit_scores`, `people.company_slot`, `dol.renewal_calendar` |
| **GOVERN** | O (Egress) | `outreach.manual_overrides`, `outreach.override_audit_log`, views (`vw_marketing_eligibility_with_overrides`, `vw_sovereign_completion`) |

---

## Authoritative Pass Ownership (LOCKED)

_Per ERD Doctrine: Every table MUST have exactly ONE authoritative pass._

| Table | Authoritative Pass | IMO Layer | Secondary Pass Interaction | Governing PRD |
|-------|-------------------|-----------|---------------------------|---------------|
| **cl.company_identity** | CAPTURE | I | COMPUTE (identity resolution), GOVERN (eligibility) | PRD_COMPANY_HUB.md |
| **cl.company_domains** | COMPUTE | M | — | PRD_COMPANY_HUB.md |
| **cl.company_names** | COMPUTE | M | — | PRD_COMPANY_HUB.md |
| **cl.identity_confidence** | COMPUTE | M | — | PRD_COMPANY_HUB.md |
| **outreach.outreach** | CAPTURE | I | GOVERN (registration to CL) | PRD_SOVEREIGN_COMPLETION.md |
| **outreach.company_target** | COMPUTE | M | CAPTURE (pattern discovery intake) | PRD_COMPANY_HUB.md |
| **outreach.dol** | COMPUTE | M | CAPTURE (DOL data ingestion) | PRD_DOL_SUBHUB.md |
| **outreach.people** | COMPUTE | M | CAPTURE (slot requirements) | PRD_PEOPLE_SUBHUB.md |
| **outreach.blog** | COMPUTE | M | CAPTURE (blog crawl) | PRD_BLOG_NEWS_SUBHUB.md |
| **outreach.bit_scores** | COMPUTE | M | — | PRD_BIT_ENGINE.md |
| **outreach.bit_signals** | CAPTURE | I | — | PRD_BIT_ENGINE.md |
| **outreach.manual_overrides** | GOVERN | O | CAPTURE (override request) | PRD_KILL_SWITCH_SYSTEM.md |
| **outreach.override_audit_log** | GOVERN | O | — | PRD_KILL_SWITCH_SYSTEM.md |
| **outreach.campaigns** | COMPUTE | M | — | PRD_OUTREACH_SPOKE.md |
| **outreach.sequences** | COMPUTE | M | — | PRD_OUTREACH_SPOKE.md |
| **outreach.send_log** | GOVERN | O | COMPUTE (send scheduling) | PRD_OUTREACH_SPOKE.md |
| **outreach.engagement_events** | CAPTURE | I | — | PRD_OUTREACH_SPOKE.md |
| **outreach.bit_errors** | CAPTURE | I | — | PRD_MASTER_ERROR_LOG.md |
| **outreach.blog_errors** | CAPTURE | I | — | PRD_MASTER_ERROR_LOG.md |
| **outreach.company_target_errors** | CAPTURE | I | — | PRD_MASTER_ERROR_LOG.md |
| **outreach.dol_errors** | CAPTURE | I | — | PRD_MASTER_ERROR_LOG.md |
| **outreach.people_errors** | CAPTURE | I | — | PRD_MASTER_ERROR_LOG.md |
| **outreach.outreach_errors** | CAPTURE | I | — | PRD_MASTER_ERROR_LOG.md |
| **people.people_master** | CAPTURE | I | COMPUTE (dedup, email generation) | PRD_PEOPLE_SUBHUB.md |
| **people.company_slot** | COMPUTE | M | — | PRD_PEOPLE_SUBHUB.md |
| **people.people_candidate** | CAPTURE | I | — | PRD_PEOPLE_SUBHUB.md |
| **dol.form_5500** | CAPTURE | I | — | PRD_DOL_SUBHUB.md |
| **dol.schedule_a** | CAPTURE | I | — | PRD_DOL_SUBHUB.md |
| **dol.ein_urls** | CAPTURE | I | — | PRD_DOL_SUBHUB.md |
| **dol.renewal_calendar** | COMPUTE | M | GOVERN (reminder tracking) | PRD_DOL_SUBHUB.md |
| **company.company_master** | CAPTURE | I | — | PRD_COMPANY_HUB.md |
| **company.company_sidecar** | COMPUTE | M | — | PRD_COMPANY_HUB.md |
| **company.company_slots** | COMPUTE | M | — | PRD_COMPANY_HUB.md |
| **company.contact_enrichment** | COMPUTE | M | — | PRD_PEOPLE_SUBHUB.md |
| **company.email_verification** | COMPUTE | M | — | PRD_PEOPLE_SUBHUB.md |
| **bit.movement_events** | CAPTURE | I | — | PRD_TALENT_FLOW_SPOKE.md |
| **bit.proof_lines** | COMPUTE | M | — | PRD_BIT_ENGINE.md |
| **bit.authorization_log** | GOVERN | O | — | PRD_BIT_ENGINE.md |
| **blog.pressure_signals** | CAPTURE | I | COMPUTE (signal detection) | PRD_BLOG_NEWS_SUBHUB.md |
| **shq_master_error_log** | CAPTURE | I | GOVERN (audit exposure) | PRD_MASTER_ERROR_LOG.md |
| **shq_orphan_errors** | CAPTURE | I | — | PRD_MASTER_ERROR_LOG.md |

### Views (GOVERN Pass)

| View | Authoritative Pass | IMO Layer | Purpose |
|------|-------------------|-----------|---------|
| **vw_marketing_eligibility_with_overrides** | GOVERN | O | Authoritative marketing eligibility |
| **vw_sovereign_completion** | GOVERN | O | Hub completion aggregation |
| **vw_marketing_eligibility** | GOVERN | O | Base eligibility (pre-override) |
| **vw_bit_tier_distribution** | GOVERN | O | BIT tier analytics |
| **v_company_lifecycle_status** | GOVERN | O | CL hub claim status |

---

## Upstream Flow Test Declaration

Per ERD Constitution, the following upstream flow paths are declared and validated:

### Path 1: Company Identity → Marketing Eligibility

```
CONSTANT: Intake CSV data
    ↓ CAPTURE
cl.company_identity (sovereign_company_id minted)
    ↓ COMPUTE
outreach.outreach (outreach_id minted, registered to CL)
    ↓ COMPUTE
outreach.company_target (domain resolved, pattern discovered)
    ↓ COMPUTE
outreach.bit_scores (signals aggregated, tier assigned)
    ↓ GOVERN
vw_marketing_eligibility_with_overrides (authoritative view)
```

### Path 2: DOL Filings → BIT Signal

```
CONSTANT: Federal DOL Form 5500 data
    ↓ CAPTURE
dol.form_5500 (filing parsed)
    ↓ CAPTURE
dol.schedule_a (Schedule A extracted)
    ↓ COMPUTE
outreach.dol (EIN matched to outreach_id)
    ↓ CAPTURE
outreach.bit_signals (DOL_FILING signal emitted)
    ↓ COMPUTE
outreach.bit_scores (score updated)
```

### Path 3: People → Slot Assignment

```
CONSTANT: LinkedIn profile data, slot requirements
    ↓ CAPTURE
people.people_master (person record created)
    ↓ COMPUTE
people.company_slot (slot assigned)
    ↓ COMPUTE
outreach.people (outreach context linked)
    ↓ CAPTURE
outreach.bit_signals (SLOT_FILLED signal emitted)
```

### Path 4: Kill Switch Override

```
CONSTANT: Human operator override request
    ↓ CAPTURE
outreach.manual_overrides (override record created)
    ↓ GOVERN
outreach.override_audit_log (audit record appended)
    ↓ GOVERN
vw_marketing_eligibility_with_overrides (effective_tier computed)
```

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

# Barton Outreach Core - Complete System ERD
## Hub-and-Spoke Architecture with All Tables and Pipelines

**Version:** 3.0.0
**Last Updated:** 2025-01-02
**Architecture:** Bicycle Wheel Doctrine v1.1
**DOL Subhub:** EIN Resolution + Violation Discovery

---

## Visual Architecture Overview

```
                                    MASTER HUB
                                        |
            +---------------------------+---------------------------+
            |                           |                           |
            v                           v                           v
    +---------------+           +---------------+           +---------------+
    |  PEOPLE NODE  |           |   DOL NODE    |           |  BLOG NODE    |
    |   (Spoke #1)  |           |  (Spoke #2)   |           |  (Spoke #3)   |
    |   [ACTIVE]    |           |   [ACTIVE]    |           |  [PLANNED]    |
    +-------+-------+           +-------+-------+           +---------------+
            |                           |
            v                           v
    +---------------+           +---------------------------+
    | Email Verify  |           |      DOL SUBHUB           |
    |  (Sub-wheel)  |           | ┌───────────────────────┐ |
    +---------------+           | │ EIN Resolution Spoke  │ |
            |                   | │ • ein_linkage table   │ |
            |                   | │ • Filing discovery    │ |
            |                   | │ • Hash verification   │ |
            |                   | └───────────────────────┘ |
            |                   | ┌───────────────────────┐ |
            |                   | │ Violation Discovery   │ |
            |                   | │ • violations table    │ |
            |                   | │ • OSHA, EBSA, WHD     │ |
            |                   | │ • Outreach views      │ |
            |                   | └───────────────────────┘ |
            |                   +---------------------------+
            |                           |
            +---------------------------+
                           |
                           v
            +---------------------------+
            |      TALENT FLOW NODE     |
            |        (Spoke #4)         |
            |         [SHELL]           |
            +---------------------------+
                           |
            +---------------------------+
            |        BIT ENGINE         |
            |       (Spoke #5)          |
            |       [PLANNED]           |
            +---------------------------+
                           |
            +---------------------------+
            |      OUTREACH NODE        |
            |        (Spoke #6)         |
            |       [PLANNED]           |
            +---------------------------+
```

---

## DOL Subhub Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DOL SUBHUB DATA FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

Company Target (PASS, EIN resolved)
        │
        ▼
┌───────────────────────────────────────┐
│         DOL SUBHUB                     │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │ 1. EIN Resolution                │ │
│  │    • Fuzzy filing discovery      │ │
│  │    • Deterministic EIN check     │ │
│  │    • Hash verification           │ │
│  │            ↓                     │ │
│  │    → dol.ein_linkage             │ │
│  └──────────────────────────────────┘ │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │ 2. Violation Discovery           │ │
│  │    • Pull from OSHA, EBSA, WHD   │ │
│  │    • Match to ein_linkage        │ │
│  │    • Store facts                 │ │
│  │            ↓                     │ │
│  │    → dol.violations              │ │
│  └──────────────────────────────────┘ │
│                                        │
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│         OUTREACH VIEWS                 │
│  • v_companies_with_violations         │
│  • v_violation_summary                 │
│  • v_recent_violations                 │
│  • v_5500_renewal_month                │
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│     DOWNSTREAM OUTREACH               │
│  (Reads facts, triggers campaigns)    │
└───────────────────────────────────────┘
```

---

## Complete Hub-and-Spoke Mermaid Diagram

```mermaid
flowchart TB
    subgraph MASTER_HUB["COMPANY HUB (Master Node)"]
        direction TB
        CM[("company_master<br/>━━━━━━━━━━━━━━<br/>company_unique_id PK<br/>company_name<br/>domain<br/>email_pattern<br/>ein<br/>employee_count<br/>address_state<br/>bit_score")]

        CS[("company_slot<br/>━━━━━━━━━━━━━━<br/>company_slot_unique_id PK<br/>company_unique_id FK<br/>person_unique_id FK<br/>slot_type<br/>is_filled<br/>status")]

        CE[("company_events<br/>━━━━━━━━━━━━━━<br/>id PK<br/>company_unique_id FK<br/>event_type<br/>event_date<br/>bit_impact_score")]

        CM --> CS
        CM --> CE
    end

    subgraph PEOPLE_SPOKE["PEOPLE NODE (Spoke #1)"]
        direction TB
        PM[("people_master<br/>━━━━━━━━━━━━━━<br/>unique_id PK<br/>company_unique_id FK<br/>company_slot_unique_id FK<br/>first_name<br/>last_name<br/>title<br/>email<br/>email_verified")]

        PS[("person_scores<br/>━━━━━━━━━━━━━━<br/>id PK<br/>person_unique_id FK<br/>bit_score<br/>confidence_score")]

        PMH[("person_movement_history<br/>━━━━━━━━━━━━━━<br/>id PK<br/>person_unique_id FK<br/>company_from_id FK<br/>company_to_id FK<br/>movement_type")]

        PM --> PS
        PM --> PMH
    end

    subgraph DOL_SPOKE["DOL NODE (Spoke #2)"]
        direction TB
        F5500[("form_5500<br/>━━━━━━━━━━━━━━<br/>ack_id PK<br/>ein<br/>plan_name<br/>participant_count<br/>total_assets")]

        F5500SF[("form_5500_sf<br/>━━━━━━━━━━━━━━<br/>ack_id PK<br/>ein<br/>plan_name<br/>Small Plans")]

        SCHA[("schedule_a<br/>━━━━━━━━━━━━━━<br/>ack_id PK<br/>insurance_company<br/>covered_lives<br/>premium_info")]
    end

    subgraph FAILURE_SPOKES["FAILURE SPOKES"]
        direction TB
        FCM[("failed_company_match<br/>━━━━━━━━━━━━━━<br/>Records <80% match")]
        FNP[("failed_no_pattern<br/>━━━━━━━━━━━━━━<br/>Missing email pattern")]
        FSA[("failed_slot_assignment<br/>━━━━━━━━━━━━━━<br/>Lost seniority competition")]
        FEV[("failed_email_verification<br/>━━━━━━━━━━━━━━<br/>Invalid email")]
    end

    subgraph INTAKE_QUARANTINE["INTAKE/QUARANTINE"]
        direction TB
        QUA[("quarantine<br/>━━━━━━━━━━━━━━<br/>Invalid companies")]
        CRI[("company_raw_intake<br/>━━━━━━━━━━━━━━<br/>Raw company imports")]
        PRI[("people_raw_intake<br/>━━━━━━━━━━━━━━<br/>Raw people imports")]
    end

    %% Relationships
    CM -.->|"EIN Join"| F5500
    CM -.->|"EIN Join"| F5500SF
    CS -->|"FK"| PM
    PM -->|"company_unique_id FK"| CM

    %% Pipeline Flow
    CRI -->|"Phase 1-4"| CM
    CM -->|"Phase 5-8"| PM

    %% Failure Routes
    CRI -.->|"<80% match"| FCM
    CM -.->|"No pattern"| FNP
    PM -.->|"Lost slot"| FSA
    PM -.->|"Bad email"| FEV
```

---

## Database Schema by Hub/Spoke

### 1. COMPANY HUB (marketing schema)

The **absolute central anchor** - all data gravitates here.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           COMPANY HUB TABLES                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ company_master (453 rows) - PRIMARY HUB TABLE                       │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ company_unique_id    TEXT      PK   Barton ID: 04.04.01.XX.XXXXX.XXX│   │
│  │ company_name         TEXT      REQ  Normalized company name         │   │
│  │ website_url          TEXT      REQ  Primary website                 │   │
│  │ domain               VARCHAR   REQ  Validated domain (anchor field) │   │
│  │ email_pattern        VARCHAR   REQ  Pattern (anchor field)          │   │
│  │ ein                  VARCHAR        Federal EIN (links to DOL)      │   │
│  │ employee_count       INTEGER   REQ  Must be >= 50                   │   │
│  │ address_state        TEXT      REQ  PA, VA, MD, OH, WV, KY only     │   │
│  │ industry             TEXT           Industry classification          │   │
│  │ founded_year         INTEGER        Year founded (1700+)            │   │
│  │ linkedin_url         TEXT           Company LinkedIn page           │   │
│  │ data_quality_score   NUMERIC        Overall quality 0-100           │   │
│  │ email_pattern_source VARCHAR        hunter, manual, enrichment      │   │
│  │ created_at           TIMESTAMP      Record creation                 │   │
│  │ updated_at           TIMESTAMP      Last modification               │   │
│  │ validated_at         TIMESTAMP      When validated                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    │ 1:N                                    │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ company_slot (1,359 rows) - SLOT SUB-WHEEL                          │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ company_slot_unique_id  TEXT    PK   Barton ID: 04.04.05.XX.XXXXX   │   │
│  │ company_unique_id       TEXT    FK   → company_master               │   │
│  │ person_unique_id        TEXT    FK   → people_master (nullable)     │   │
│  │ slot_type               TEXT    REQ  CHRO, HR_MANAGER, BENEFITS...  │   │
│  │ is_filled               BOOLEAN      Is someone in slot?            │   │
│  │ status                  VARCHAR      open, filled, vacated          │   │
│  │ confidence_score        NUMERIC      Assignment confidence 0-100    │   │
│  │ filled_at               TIMESTAMP    When slot was filled           │   │
│  │ vacated_at              TIMESTAMP    When person left               │   │
│  │ enrichment_attempts     INTEGER      Enrichment attempt count       │   │
│  │ last_refreshed_at       TIMESTAMP    Last enrichment refresh        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ company_events (0 rows) - NEWS/BLOG SIGNALS                         │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ id                      INTEGER  PK  Auto-increment                 │   │
│  │ company_unique_id       TEXT     FK  → company_master               │   │
│  │ event_type              TEXT         funding, acquisition, layoff...│   │
│  │ event_date              DATE         When event occurred            │   │
│  │ source_url              TEXT         Source article                 │   │
│  │ summary                 TEXT         Event summary                  │   │
│  │ detected_at             TIMESTAMP    When detected                  │   │
│  │ impacts_bit             BOOLEAN      Affects BIT score?             │   │
│  │ bit_impact_score        INTEGER      Impact: -100 to +100           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ pipeline_events (2,185 rows) - AUDIT TRAIL                          │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ id, event_type, phase, correlation_id, company_id, person_id,       │   │
│  │ timestamp, metadata, duration_ms                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. PEOPLE NODE - Spoke #1 (people schema)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PEOPLE NODE TABLES                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ people_master (170 rows) - PEOPLE HUB TABLE                         │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ unique_id              TEXT      PK   Barton ID: 04.04.02.XX.XXXXX  │   │
│  │ company_unique_id      TEXT      FK   → company_master (REQUIRED)   │   │
│  │ company_slot_unique_id TEXT      FK   → company_slot (REQUIRED)     │   │
│  │ first_name             TEXT      REQ  First name                    │   │
│  │ last_name              TEXT      REQ  Last name                     │   │
│  │ full_name              TEXT           Display name                  │   │
│  │ title                  TEXT           Job title                     │   │
│  │ seniority              TEXT           CHRO > VP > Director > Mgr    │   │
│  │ department             TEXT           HR, Finance, etc.             │   │
│  │ email                  TEXT           Verified email address        │   │
│  │ email_verified         BOOLEAN        Verification status           │   │
│  │ email_verified_at      TIMESTAMP      When verified                 │   │
│  │ email_verification_src TEXT           millionverifier, manual       │   │
│  │ work_phone_e164        TEXT           Work phone (E.164)            │   │
│  │ linkedin_url           TEXT           LinkedIn profile              │   │
│  │ created_at             TIMESTAMP      Record creation               │   │
│  │ updated_at             TIMESTAMP      Last modification             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    │ 1:1                                    │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ person_scores (0 rows) - BIT SCORES SUB-WHEEL                       │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ id                     INTEGER  PK   Auto-increment                 │   │
│  │ person_unique_id       TEXT     FK   → people_master (UNIQUE)       │   │
│  │ bit_score              INTEGER       BIT score 0-100                │   │
│  │ confidence_score       INTEGER       Data confidence 0-100          │   │
│  │ calculated_at          TIMESTAMP     When calculated                │   │
│  │ score_factors          JSONB         Breakdown of factors           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    │ 1:N                                    │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ person_movement_history (0 rows) - TALENT FLOW SUB-WHEEL            │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ id                     INTEGER  PK   Auto-increment                 │   │
│  │ person_unique_id       TEXT     FK   → people_master                │   │
│  │ linkedin_url           TEXT          LinkedIn URL at detection      │   │
│  │ company_from_id        TEXT     FK   → company_master (source)      │   │
│  │ company_to_id          TEXT     FK   → company_master (dest)        │   │
│  │ title_from             TEXT          Previous title                 │   │
│  │ title_to               TEXT          New title                      │   │
│  │ movement_type          TEXT          company_change, title_change   │   │
│  │ detected_at            TIMESTAMP     Detection time                 │   │
│  │ raw_payload            JSONB         Raw enrichment data            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ people_resolution_queue (1,206 rows) - MANUAL REVIEW QUEUE          │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ id, person_data, resolution_status, hold_reason, created_at         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3. DOL NODE - Spoke #2 (dol schema)

The DOL Subhub handles **EIN Resolution** and **Violation Discovery** (facts only).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DOL NODE TABLES                                   │
│                        (2.4M+ rows total)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ════════════════════════════════════════════════════════════════════════   │
│  █ DOL FILING TABLES (Source Data)                                          │
│  ════════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ form_5500 (230,009 rows) - LARGE RETIREMENT PLANS                   │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ ack_id                 TEXT      PK   DOL acknowledgment ID         │   │
│  │ ein                    VARCHAR        Employer ID (links to company)│   │
│  │ plan_number            VARCHAR        Plan identifier               │   │
│  │ plan_name              TEXT           Plan name                     │   │
│  │ sponsor_dfe_name       TEXT           Sponsor/employer name         │   │
│  │ sponsor_dfe_ein        VARCHAR        Sponsor EIN                   │   │
│  │ spons_dfe_mail_us_city TEXT           City                          │   │
│  │ spons_dfe_mail_us_state TEXT          State                         │   │
│  │ tot_partcp_boy_cnt     INTEGER        Participant count (BOY)       │   │
│  │ tot_assets_boy_amt     NUMERIC        Total assets (BOY)            │   │
│  │ plan_eff_date          DATE           Plan effective date           │   │
│  │ form_plan_year_begin   DATE           Plan year begin               │   │
│  │ form_plan_year_end     DATE           Plan year end (renewal date)  │   │
│  │ type_pension_bnft_code VARCHAR        Pension benefit type code     │   │
│  │ type_welfare_bnft_code VARCHAR        Welfare benefit type code     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ form_5500_sf (759,569 rows) - SMALL RETIREMENT PLANS                │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ (Same structure as form_5500 - for plans <100 participants)         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ schedule_a (336,817 rows) - INSURANCE CONTRACT INFORMATION          │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ ack_id                 TEXT      PK   DOL acknowledgment ID         │   │
│  │ insurance_company_name TEXT           Insurance carrier name        │   │
│  │ prov_contract_num      VARCHAR        Contract number               │   │
│  │ covered_persons_cnt    INTEGER        Covered lives                 │   │
│  │ premium_amount         NUMERIC        Premium information           │   │
│  │ commission_amount      NUMERIC        Broker commission             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ════════════════════════════════════════════════════════════════════════   │
│  █ EIN RESOLUTION TABLES (Company → EIN Linkage)                            │
│  ════════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ dol.ein_linkage (APPEND-ONLY) - EIN ↔ COMPANY LINKAGE               │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ linkage_id             VARCHAR(50)  PK  Barton ID: 01.04.02.04.22XXX│   │
│  │ company_unique_id      VARCHAR(50)  FK  → company_master (IMMUTABLE)│   │
│  │ ein                    VARCHAR(10)  REQ EIN format: XX-XXXXXXX      │   │
│  │ source                 VARCHAR(50)  REQ DOL_FORM_5500, DOL_5500_EZ  │   │
│  │ source_url             TEXT         REQ URL to source filing        │   │
│  │ filing_year            INTEGER      REQ Year of filing (2015-2025)  │   │
│  │ hash_fingerprint       VARCHAR(64)  REQ SHA-256 for verification    │   │
│  │ outreach_context_id    VARCHAR(100)     Context from Company Target │   │
│  │ created_at             TIMESTAMPTZ      Record creation timestamp   │   │
│  │                                                                     │   │
│  │ CONSTRAINTS:                                                        │   │
│  │ • ein ~ '^\d{2}-\d{7}$' (EIN format)                               │   │
│  │ • filing_year BETWEEN 2015 AND 2025                                │   │
│  │ • TRIGGER: Prevents UPDATE/DELETE (append-only)                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ════════════════════════════════════════════════════════════════════════   │
│  █ VIOLATION TABLES (DOL Violator Facts)                                    │
│  ════════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ dol.violations (APPEND-ONLY) - DOL VIOLATION FACTS                  │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ violation_id           VARCHAR(50)  PK  Barton ID: 01.04.02.04.5XXX │   │
│  │ ein                    VARCHAR(10)  REQ Links to ein_linkage        │   │
│  │ company_unique_id      VARCHAR(50)      From ein_linkage join       │   │
│  │ source_agency          VARCHAR(20)  REQ OSHA|EBSA|WHD|OFCCP|MSHA    │   │
│  │ case_number            VARCHAR(50)      Agency case number          │   │
│  │ violation_type         VARCHAR(100) REQ Type of violation           │   │
│  │ violation_date         DATE             When violation occurred     │   │
│  │ discovery_date         DATE         REQ When we discovered it       │   │
│  │ site_name              VARCHAR(255)     Site/establishment name     │   │
│  │ site_address           TEXT             Site address                │   │
│  │ site_city              VARCHAR(100)     City                        │   │
│  │ site_state             VARCHAR(2)       State                       │   │
│  │ site_zip               VARCHAR(10)      ZIP code                    │   │
│  │ severity               VARCHAR(20)      WILLFUL|SERIOUS|OTHER|REPEAT│   │
│  │ penalty_initial        DECIMAL(12,2)    Initial penalty amount      │   │
│  │ penalty_current        DECIMAL(12,2)    Current penalty amount      │   │
│  │ penalty_paid           DECIMAL(12,2)    Amount paid                 │   │
│  │ status                 VARCHAR(30)  REQ OPEN|CONTESTED|SETTLED|PAID │   │
│  │ citation_id            VARCHAR(100)     Citation identifier         │   │
│  │ citation_url           TEXT             URL to citation             │   │
│  │ violation_description  TEXT             Raw description from DOL    │   │
│  │ source_url             TEXT         REQ Source URL                  │   │
│  │ source_record_id       VARCHAR(100)     Source record identifier    │   │
│  │ hash_fingerprint       VARCHAR(64)  REQ SHA-256 for deduplication   │   │
│  │ outreach_context_id    VARCHAR(100)     Context ID                  │   │
│  │ created_at             TIMESTAMPTZ      Record creation             │   │
│  │                                                                     │   │
│  │ CONSTRAINTS:                                                        │   │
│  │ • source_agency IN (OSHA, EBSA, WHD, OFCCP, MSHA, OTHER)           │   │
│  │ • status IN (OPEN, CONTESTED, SETTLED, PAID, ABATED, DELETED)      │   │
│  │ • UNIQUE INDEX on (ein, source_agency, case_number)                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ dol.violation_categories (REFERENCE) - VIOLATION TYPES              │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ category_code          VARCHAR(20)  PK  e.g., OSHA_WILLFUL          │   │
│  │ category_name          VARCHAR(100) REQ Human-readable name         │   │
│  │ agency                 VARCHAR(20)  REQ OSHA|EBSA|WHD|OFCCP         │   │
│  │ description            TEXT             Category description        │   │
│  │ outreach_relevant      BOOLEAN          Use for outreach targeting? │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ════════════════════════════════════════════════════════════════════════   │
│  █ VIEWS (Read-Only Projections)                                            │
│  ════════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ dol.v_companies_with_violations (VIEW) - OUTREACH TARGETING         │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ company_unique_id, ein, violation_id, source_agency, violation_type,│   │
│  │ violation_date, discovery_date, severity, penalty_initial,          │   │
│  │ penalty_current, status, site_state, citation_url,                  │   │
│  │ violation_description, ein_source, ein_filing_year                  │   │
│  │                                                                     │   │
│  │ PURPOSE: Companies with open/contested violations for outreach      │   │
│  │ JOINS: ein_linkage → violations (WHERE status IN OPEN, CONTESTED)   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ dol.v_violation_summary (VIEW) - AGGREGATE STATS                    │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ company_unique_id, ein, total_violations, open_violations,          │   │
│  │ agencies_with_violations, total_initial_penalties,                  │   │
│  │ total_current_penalties, earliest_violation, latest_violation,      │   │
│  │ last_discovery_date, violation_agencies[], severity_levels[]        │   │
│  │                                                                     │   │
│  │ PURPOSE: Aggregate violation stats by company                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ dol.v_recent_violations (VIEW) - LAST 90 DAYS                       │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ (All violation columns) + company_unique_id, days_since_discovery   │   │
│  │                                                                     │   │
│  │ PURPOSE: Recent violations to prioritize for outreach               │   │
│  │ FILTER: discovery_date >= NOW() - 90 days                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ════════════════════════════════════════════════════════════════════════   │
│  █ ANALYTICS VIEWS (5500 Projections)                                       │
│  ════════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ analytics.v_5500_renewal_month (VIEW) - RENEWAL MONTH SIGNALS       │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ company_unique_id, ein, filing_year, source_form, coverage_end_date,│   │
│  │ renewal_month (1-12), confidence (DECLARED|INFERRED|AMBIGUOUS),     │   │
│  │ source_record_id, created_at                                        │   │
│  │                                                                     │   │
│  │ PURPOSE: Project renewal month from 5500 filings                    │   │
│  │ NOTE: renewal_month is NOT contractual renewal date                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ analytics.v_5500_insurance_facts (VIEW) - SCHEDULE A/EZ FACTS       │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ company_unique_id, ein, filing_year, source_form, insurer_name,     │   │
│  │ insurer_ein, policy_number, coverage_start_date, coverage_end_date, │   │
│  │ funding_type, commissions, source_record_id                         │   │
│  │                                                                     │   │
│  │ PURPOSE: Insurance contract facts from Schedule A/EZ                │   │
│  │ NOTE: No transformations, no scoring, raw filed facts               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ── Link to Company Hub via EIN ──                                         │
│  company_master.ein = form_5500.sponsor_dfe_ein                            │
│  ein_linkage.company_unique_id = company_master.company_unique_id          │
│  violations.ein = ein_linkage.ein                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4. SHQ NODE - Error & Operations (shq schema)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            SHQ NODE TABLES                                   │
│                        (Operations & Triage)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ shq.error_master - CANONICAL ERROR TABLE                            │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ error_id               UUID         PK   Auto-generated             │   │
│  │ process_id             VARCHAR(50)  REQ  Barton process ID          │   │
│  │ agent_name             VARCHAR(50)  REQ  DOL_EIN_SUBHUB, COMPANY_   │   │
│  │ severity               VARCHAR(20)  REQ  HARD_FAIL (always)         │   │
│  │ source_system          VARCHAR(50)  REQ  Source system name         │   │
│  │ message                TEXT         REQ  Error message              │   │
│  │ stack_trace            TEXT             Full stack/context          │   │
│  │ error_type             VARCHAR(50)      Error code enum             │   │
│  │ hdo_snapshot           JSONB            Payload at time of error    │   │
│  │ context                JSONB            Additional context          │   │
│  │ occurred_at            TIMESTAMPTZ REQ  When error occurred         │   │
│  │ unique_id              VARCHAR(50)      Related unique ID           │   │
│  │ escalation_level       INTEGER          0, 1, 2, 3                  │   │
│  │ occurrence_count       INTEGER          Number of times occurred    │   │
│  │ first_occurred_at      TIMESTAMPTZ      First occurrence            │   │
│  │ resolved               BOOLEAN          Is it resolved?             │   │
│  │ resolution_notes       TEXT             How it was resolved         │   │
│  │ resolved_by            VARCHAR(100)     Who resolved it             │   │
│  │ resolved_at            TIMESTAMPTZ      When resolved               │   │
│  │ resolution_method      VARCHAR(50)      manual, auto, enrichment    │   │
│  │ escalated_at           TIMESTAMPTZ      When escalated              │   │
│  │ escalation_reason      TEXT             Why escalated               │   │
│  │ created_at             TIMESTAMPTZ      Record creation             │   │
│  │                                                                     │   │
│  │ ERROR CODES (DOL Subhub):                                           │   │
│  │ • IDENTITY_GATE_FAILED - Missing identity anchors                  │   │
│  │ • MULTI_EIN_FOUND - Multiple EINs in filings                       │   │
│  │ • EIN_MISMATCH - EIN doesn't match across filings                  │   │
│  │ • FILING_TTL_EXCEEDED - Filing too old                             │   │
│  │ • SOURCE_UNAVAILABLE - DOL source offline                          │   │
│  │ • CROSS_CONTEXT_CONTAMINATION - Context bleeding                   │   │
│  │ • EIN_FORMAT_INVALID - Bad EIN format                              │   │
│  │ • HASH_VERIFICATION_FAILED - Document tampering                    │   │
│  │ • COMPANY_TARGET_NOT_PASS - Upstream not ready                     │   │
│  │ • DOL_FILING_NOT_CONFIRMED - Fuzzy found but deterministic failed  │   │
│  │ • EIN_NOT_RESOLVED - Company Target couldn't resolve EIN           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ dol.air_log - AIR EVENT LOG (Truth/Audit)                           │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ event_id               UUID         PK   Auto-generated             │   │
│  │ event_type             VARCHAR(50)  REQ  Event type enum            │   │
│  │ event_status           VARCHAR(20)  REQ  SUCCESS, FAIL, INFO        │   │
│  │ event_message          TEXT         REQ  Human-readable message     │   │
│  │ event_payload          JSONB            Detailed payload            │   │
│  │ company_unique_id      VARCHAR(50)      Related company             │   │
│  │ outreach_context_id    VARCHAR(100)     Context ID                  │   │
│  │ created_at             TIMESTAMPTZ      Event timestamp             │   │
│  │                                                                     │   │
│  │ AUDIT INVARIANT:                                                    │   │
│  │ Every FAIL HARD writes to BOTH air_log AND shq.error_master        │   │
│  │ air_log = authoritative truth                                       │   │
│  │ error_master = operations/triage                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ analytics.v_company_target_ein_enrichment_queue (VIEW)              │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ error_id, process_id, agent_name, severity, error_type, message,    │   │
│  │ occurred_at, company_details, handoff_target, remediation_required, │   │
│  │ fuzzy_candidates, fuzzy_method, threshold_used                      │   │
│  │                                                                     │   │
│  │ PURPOSE: Queue for EIN_NOT_RESOLVED errors needing enrichment       │   │
│  │ FILTER: process_id = Company Target, error_type = EIN_NOT_RESOLVED  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5. INTAKE/QUARANTINE (intake schema)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INTAKE/QUARANTINE TABLES                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ quarantine (114 rows) - INVALID/REJECTED COMPANIES                  │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ id, company_data, rejection_reason, quarantine_date, reviewed_by    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ company_raw_intake (563 rows) - RAW COMPANY IMPORTS                 │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ id, raw_company_name, raw_domain, raw_address, source, import_date  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ people_raw_intake (0 rows) - RAW PEOPLE IMPORTS                     │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ id, raw_name, raw_title, raw_company, source, import_date           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Pipeline Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE PIPELINE FLOW                               │
└─────────────────────────────────────────────────────────────────────────────┘

                         RAW DATA INTAKE
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMPANY IDENTITY PIPELINE (Phases 1-4)                    │
│                         *** ALWAYS RUNS FIRST ***                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  PHASE 1    │    │  PHASE 2    │    │  PHASE 3    │    │  PHASE 4    │  │
│  │  Company    │───▶│  Domain     │───▶│  Email      │───▶│  Pattern    │  │
│  │  Matching   │    │  Resolution │    │  Pattern    │    │  Verify     │  │
│  │             │    │             │    │  Waterfall  │    │             │  │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘  │
│         │                  │                  │                  │         │
│         ▼                  ▼                  ▼                  ▼         │
│    ┌─────────┐       ┌─────────┐       ┌─────────┐       ┌─────────┐      │
│    │ FAILURE │       │ FAILURE │       │ FAILURE │       │ OUTPUT  │      │
│    │ <80%    │       │ No      │       │ No      │       │company_ │      │
│    │ match   │       │ domain  │       │ pattern │       │ master  │      │
│    └─────────┘       └─────────┘       └─────────┘       └─────────┘      │
│                                                                             │
│  Phase 1b: Unmatched Hold Export (CSV staging for manual review)           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              │ company_id + domain + email_pattern
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PEOPLE PIPELINE (Phases 5-8)                            │
│                  *** ONLY RUNS AFTER COMPANY ANCHOR ***                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  PHASE 5    │    │  PHASE 6    │    │  PHASE 7    │    │  PHASE 8    │  │
│  │  Email      │───▶│  Slot       │───▶│  Enrichment │───▶│  Output     │  │
│  │  Generation │    │  Assignment │    │  Queue      │    │  Writer     │  │
│  │             │    │             │    │             │    │             │  │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘  │
│         │                  │                  │                  │         │
│         ▼                  ▼                  ▼                  ▼         │
│    ┌─────────┐       ┌─────────┐       ┌─────────┐       ┌─────────┐      │
│    │ No      │       │ Lost    │       │ Retry   │       │ people_ │      │
│    │ pattern │       │ slot    │       │ queue   │       │ master  │      │
│    │ failure │       │ failure │       │         │       │ output  │      │
│    └─────────┘       └─────────┘       └─────────┘       └─────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              │ All signals
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BIT ENGINE                                         │
│              (Buyer Intent Tool - Score Calculation)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INPUTS:                              OUTPUT:                               │
│  ├─ People signals (slot fills)       ├─ BIT Score (0-100)                 │
│  ├─ DOL signals (renewals)            ├─ Trigger flags                     │
│  ├─ Blog signals (events)             └─ Recommended action                │
│  └─ Talent signals (movements)                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Slot Type Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SLOT TYPE HIERARCHY                                 │
│                    (Seniority-based assignment)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  COMPANY_ID                                                                 │
│      │                                                                      │
│      ├── SLOT: CHRO (Seniority: 100)                                       │
│      │   └── Chief HR Officer, VP HR, SVP HR                               │
│      │                                                                      │
│      ├── SLOT: HR_MANAGER (Seniority: 80)                                  │
│      │   └── HR Director, HR Manager, HR Lead                              │
│      │                                                                      │
│      ├── SLOT: BENEFITS_LEAD (Seniority: 60)                               │
│      │   └── Benefits Manager, Benefits Director, Total Rewards            │
│      │                                                                      │
│      ├── SLOT: PAYROLL_ADMIN (Seniority: 50)                               │
│      │   └── Payroll Manager, Payroll Director                             │
│      │                                                                      │
│      └── SLOT: HR_SUPPORT (Seniority: 30)                                  │
│          └── HR Coordinator, HR Specialist, HR Generalist, HRBP            │
│                                                                             │
│  RULE: One person per slot per company                                      │
│  CONFLICT: Higher seniority wins (must exceed by min_seniority_diff: 10)   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Entity Relationship Diagram (Mermaid)

```mermaid
erDiagram
    %% Company Hub Relationships
    COMPANY_MASTER ||--o{ COMPANY_SLOT : "has"
    COMPANY_MASTER ||--o{ COMPANY_EVENTS : "has"
    COMPANY_MASTER ||--o{ PEOPLE_MASTER : "employs"
    COMPANY_MASTER ||--o{ DOL_EIN_LINKAGE : "has EIN"
    
    %% DOL Subhub Relationships
    DOL_EIN_LINKAGE ||--o{ DOL_VIOLATIONS : "has violations"
    DOL_EIN_LINKAGE ||--o{ DOL_FORM_5500 : "links to filings"
    DOL_EIN_LINKAGE ||--o{ DOL_SCHEDULE_A : "has insurance"
    
    %% People Spoke Relationships
    COMPANY_SLOT ||--o| PEOPLE_MASTER : "filled by"
    PEOPLE_MASTER ||--o| PERSON_SCORES : "has"
    PEOPLE_MASTER ||--o{ PERSON_MOVEMENT : "has history"
    
    %% Error/Audit Relationships
    COMPANY_MASTER ||--o{ SHQ_ERROR_MASTER : "may have errors"
    DOL_EIN_LINKAGE ||--o{ DOL_AIR_LOG : "audit trail"

    COMPANY_MASTER {
        text company_unique_id PK
        text company_name
        varchar domain
        varchar email_pattern
        varchar ein
        integer employee_count
        text address_state
        numeric data_quality_score
    }

    COMPANY_SLOT {
        text company_slot_unique_id PK
        text company_unique_id FK
        text person_unique_id FK
        text slot_type
        boolean is_filled
        varchar status
        numeric confidence_score
    }

    PEOPLE_MASTER {
        text unique_id PK
        text company_unique_id FK
        text company_slot_unique_id FK
        text first_name
        text last_name
        text title
        text email
        boolean email_verified
        text seniority
    }

    PERSON_SCORES {
        integer id PK
        text person_unique_id FK
        integer bit_score
        integer confidence_score
        timestamp calculated_at
    }

    PERSON_MOVEMENT {
        integer id PK
        text person_unique_id FK
        text company_from_id FK
        text company_to_id FK
        text movement_type
        timestamp detected_at
    }

    DOL_EIN_LINKAGE {
        varchar linkage_id PK
        varchar company_unique_id FK
        varchar ein
        varchar source
        text source_url
        integer filing_year
        varchar hash_fingerprint
        timestamp created_at
    }

    DOL_VIOLATIONS {
        varchar violation_id PK
        varchar ein FK
        varchar company_unique_id FK
        varchar source_agency
        varchar case_number
        varchar violation_type
        date violation_date
        varchar severity
        decimal penalty_initial
        decimal penalty_current
        varchar status
        text violation_description
        varchar hash_fingerprint
    }

    DOL_FORM_5500 {
        text ack_id PK
        varchar ein
        text plan_name
        integer participant_count
        numeric total_assets
        date plan_year_end
    }

    DOL_SCHEDULE_A {
        text ack_id PK
        text insurance_company
        integer covered_lives
        numeric premium_amount
        numeric commission
    }

    DOL_AIR_LOG {
        uuid event_id PK
        varchar event_type
        varchar event_status
        text event_message
        jsonb event_payload
        varchar company_unique_id FK
        timestamp created_at
    }

    SHQ_ERROR_MASTER {
        uuid error_id PK
        varchar process_id
        varchar agent_name
        varchar severity
        varchar error_type
        text message
        jsonb hdo_snapshot
        boolean resolved
        timestamp occurred_at
    }

    COMPANY_EVENTS {
        integer id PK
        text company_unique_id FK
        text event_type
        date event_date
        integer bit_impact_score
    }
```

---

## Complete Table Summary

### Core Hub Tables

| Schema | Table | Rows | Purpose | Key Relationships |
|--------|-------|------|---------|-------------------|
| **marketing** | company_master | 453 | **MASTER HUB** | PK: company_unique_id |
| **marketing** | company_slot | 1,359 | Slot assignments | FK: company_unique_id, person_unique_id |
| **marketing** | company_events | 0 | News/blog signals | FK: company_unique_id |
| **marketing** | pipeline_events | 2,185 | Audit trail | FK: company_id, person_id |

### People Spoke Tables

| Schema | Table | Rows | Purpose | Key Relationships |
|--------|-------|------|---------|-------------------|
| **people** | people_master | 170 | People records | FK: company_unique_id, company_slot_unique_id |
| **people** | person_scores | 0 | BIT scores | FK: person_unique_id |
| **people** | person_movement_history | 0 | Job changes | FK: person_unique_id, company_from_id, company_to_id |
| **people** | people_resolution_queue | 1,206 | Manual review | FK: various |

### DOL Subhub Tables (EIN Resolution + Violations)

| Schema | Table | Rows | Purpose | Key Relationships |
|--------|-------|------|---------|-------------------|
| **dol** | form_5500 | 230,009 | Large plans (source) | Join: ein → ein_linkage.ein |
| **dol** | form_5500_sf | 759,569 | Small plans (source) | Join: ein → ein_linkage.ein |
| **dol** | schedule_a | 336,817 | Insurance info (source) | Join: ack_id → form_5500.ack_id |
| **dol** | ein_linkage | NEW | **EIN ↔ Company Linkage** | FK: company_unique_id → company_master |
| **dol** | violations | NEW | **DOL Violation Facts** | FK: ein → ein_linkage.ein |
| **dol** | violation_categories | NEW | Violation type reference | - |
| **dol** | air_log | NEW | Audit trail (truth) | FK: company_unique_id |

### DOL Subhub Views

| Schema | View | Purpose | Key Joins |
|--------|------|---------|-----------|
| **dol** | v_companies_with_violations | Outreach targeting | ein_linkage → violations |
| **dol** | v_violation_summary | Aggregate stats | ein_linkage → violations (grouped) |
| **dol** | v_recent_violations | Last 90 days | violations → ein_linkage |
| **analytics** | v_5500_renewal_month | Renewal month signals | ein_linkage → form_5500 |
| **analytics** | v_5500_insurance_facts | Schedule A/EZ facts | ein_linkage → schedule_a |
| **analytics** | v_company_target_ein_enrichment_queue | Enrichment queue | shq.error_master filtered |

### Operations & Error Tables

| Schema | Table | Rows | Purpose | Key Relationships |
|--------|-------|------|---------|-------------------|
| **shq** | error_master | NEW | **Canonical error table** | process_id, company_unique_id |

### Intake/Quarantine Tables

| Schema | Table | Rows | Purpose | Key Relationships |
|--------|-------|------|---------|-------------------|
| **intake** | quarantine | 114 | Invalid records | - |
| **intake** | company_raw_intake | 563 | Raw imports | Pipeline input |
| **intake** | people_raw_intake | 0 | Raw imports | Pipeline input |

---

**Total: 35+ tables/views, 2.4M+ rows across 6 schemas**

### Schema Summary

| Schema | Purpose | Key Tables |
|--------|---------|------------|
| `marketing` | Company Hub | company_master, company_slot |
| `people` | People Spoke | people_master, person_scores |
| `dol` | DOL Subhub | ein_linkage, violations, form_5500 |
| `analytics` | Projection Views | v_5500_renewal_month, v_5500_insurance_facts |
| `shq` | Operations | error_master |
| `intake` | Raw Data | quarantine, company_raw_intake |

---

## The Golden Rule

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   IF company_id IS NULL OR domain IS NULL OR email_pattern IS NULL:        │
│                                                                             │
│       STOP. DO NOT PROCEED.                                                │
│       → Route to Company Identity Pipeline first.                          │
│                                                                             │
│   NO spoke pipeline should EVER process a record that lacks                │
│   a valid company anchor.                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Barton ID Format Reference

| Entity | Schema | Format | Example |
|--------|--------|--------|---------|
| Company | 01 | `04.04.01.XX.XXXXX.XXX` | 04.04.01.04.30001.001 |
| Person | 02 | `04.04.02.XX.XXXXX.XXX` | 04.04.02.04.20001.001 |
| Slot | 05 | `04.04.05.XX.XXXXX.XXX` | 04.04.05.04.10001.001 |

---

*Generated: 2025-12-18 | Barton Outreach Core v2.1 | Bicycle Wheel Doctrine v1.1*

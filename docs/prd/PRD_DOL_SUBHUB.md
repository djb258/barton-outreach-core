# PRD: DOL Sub-Hub v4.0

**Version:** 4.0 (Constitutional Compliance)
**Status:** Active
**CC Layer:** CC-02
**Constitutional Date:** 2026-01-29
**Last Updated:** 2026-01-29
**Doctrine:** IMO-Creator Constitutional Doctrine
**Barton ID Range:** `04.04.03.XX.XXXXX.###`

---

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | IMO-Creator v1.0 |
| **Domain Spec Reference** | `doctrine/REPO_DOMAIN_SPEC.md` |
| **CC Layer** | CC-02 |
| **PRD Constitution** | `templates/doctrine/PRD_CONSTITUTION.md` |

---

## 1. Sovereign Reference (CC-01)

| Field | Value |
|-------|-------|
| **Sovereign ID** | CL-01 (Company Lifecycle) |
| **Sovereign Boundary** | Company identity and lifecycle state |

---

## 2. Hub Identity (CC-02)

| Field | Value |
|-------|-------|
| **Hub Name** | DOL Filings |
| **Hub ID** | HUB-DOL |
| **Doctrine ID** | 04.04.03 |
| **Owner** | Barton Outreach Core |
| **Version** | 4.0 |
| **Waterfall Order** | 2 |

---

## 3. Purpose & Transformation Declaration

### Transformation Statement (REQUIRED)

> **"This hub transforms federal DOL filing data (CONSTANTS) into EIN-resolved company linkages and compliance signals (VARIABLES) through CAPTURE (DOL EFAST2 data ingestion), COMPUTE (EIN matching, broker change detection, renewal tracking), and GOVERN (signal emission with idempotency enforcement)."**

| Field | Value |
|-------|-------|
| **Transformation Summary** | Federal DOL filings → EIN linkages + compliance signals |

### Constants (Inputs)

_Immutable inputs received from outside this hub. Reference: `doctrine/REPO_DOMAIN_SPEC.md §2`_

| Constant | Source | Description |
|----------|--------|-------------|
| `dol_form_5500_filings` | Federal DOL EFAST2 | Annual Form 5500 filing data (230K+ records) |
| `dol_form_5500_sf_filings` | Federal DOL EFAST2 | Annual Form 5500-SF small plan data (760K+ records) |
| `dol_schedule_a_data` | Federal DOL EFAST2 | Insurance broker/carrier data (337K+ records) |
| `outreach_id` | Outreach Spine | Operational identifier for FK linkage |
| `company_domain` | Company Target | Verified domain for EIN matching |

### Variables (Outputs)

_Outputs this hub produces. Reference: `doctrine/REPO_DOMAIN_SPEC.md §3`_

| Variable | Destination | Description |
|----------|-------------|-------------|
| `ein_resolution` | Outreach DOL table | EIN-to-company linkage |
| `filing_match_status` | Outreach DOL table | Form 5500 match status |
| `broker_change_signal` | BIT Engine | Broker change detection signal |
| `renewal_signal` | BIT Engine | Plan renewal timing signal |
| `large_plan_signal` | BIT Engine | Large plan (500+ participants) signal |
| `dol_compliance_facts` | Downstream consumers | Read-only DOL facts |

### Pass Structure

_Constitutional pass mapping per `PRD_CONSTITUTION.md §Pass-to-IMO Mapping`_

| Pass | Type | IMO Layer | Description |
|------|------|-----------|-------------|
| DOL Data Ingestion | **CAPTURE** | I (Ingress) | Ingest Form 5500, 5500-SF, Schedule A from EFAST2 |
| EIN Matching | **COMPUTE** | M (Middle) | Match DOL EINs to company records |
| Broker Change Detection | **COMPUTE** | M (Middle) | Detect broker changes year-over-year |
| Renewal Tracking | **COMPUTE** | M (Middle) | Track plan renewal dates |
| Signal Emission | **GOVERN** | O (Egress) | Emit idempotent signals to BIT Engine |

### Scope Boundary

| Scope | Description |
|-------|-------------|
| **IN SCOPE** | DOL data ingestion, EIN matching, broker change detection, renewal tracking, signal emission, column metadata |
| **OUT OF SCOPE** | Company identity creation (Company Target owns), email pattern discovery (Company Target owns), BIT scoring (BIT Engine owns), people management (People owns) |

---

## Sub-Hub Ownership Statement

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           DOL SUB-HUB OWNERSHIP                               ║
║                                                                               ║
║   This sub-hub OWNS:                                                          ║
║   ├── Form 5500 data ingestion and processing                                ║
║   ├── Form 5500-SF (EZ) small plan data                                      ║
║   ├── Schedule A insurance broker data extraction                            ║
║   ├── EIN-to-Company matching                                                ║
║   ├── Plan renewal date tracking                                             ║
║   ├── Broker change detection                                                ║
║   ├── Column metadata and AI-ready documentation                             ║
║   └── DOL compliance signal emission                                         ║
║                                                                               ║
║   This sub-hub DOES NOT OWN:                                                  ║
║   ├── Company identity creation (company_id, domain)                         ║
║   ├── Email pattern discovery or generation                                  ║
║   ├── People lifecycle management                                            ║
║   ├── BIT Engine scoring or decision making                                  ║
║   ├── Outreach decisions (who gets messaged, when, how)                      ║
║   └── Slot assignment or email generation                                    ║
║                                                                               ║
║   DATA SOURCE: U.S. Department of Labor EFAST2 System                        ║
║   DATA YEAR: 2023 (annual refresh cycle)                                     ║
║   DATA STATUS: READ-ONLY (trigger-enforced)                                  ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 1. Purpose

The DOL Sub-Hub processes Department of Labor EFAST2 data to enrich company records with regulatory filings and insurance information. It matches DOL filings to companies via EIN and emits signals to the BIT Engine.

### Core Functions

1. **Form 5500 Processing** - Ingest and process annual benefit plan filings (230K+ records)
2. **Form 5500-SF Processing** - Process small plan filings (760K+ records)
3. **Schedule A Extraction** - Extract insurance broker and carrier data (337K+ records)
4. **EIN Matching** - Match DOL filings to Company Hub records by EIN
5. **Renewal Date Tracking** - Track plan year dates for renewal signals
6. **Broker Change Detection** - Detect when companies change insurance brokers
7. **Compliance Signals** - Emit signals based on plan characteristics
8. **AI-Ready Metadata** - Searchable column documentation for all tables

---

## 2. IMO Structure (Input-Middle-Output)

### I — Ingress Layer

| Component | Purpose | Source |
|-----------|---------|--------|
| DOL EFAST2 Import | Annual data refresh | dol.gov bulk downloads |
| CSV Parser | Parse Form 5500, 5500-SF, Schedule A | Local CSV files |
| Column Normalizer | Standardize column names | DOL layout files |

### M — Middle Layer

| Component | Purpose | Location |
|-----------|---------|----------|
| `import_dol_full.py` | Full-column data import | `hubs/dol-filings/imo/middle/importers/` |
| `build_column_metadata.py` | AI-ready metadata generation | `hubs/dol-filings/imo/middle/importers/` |
| EIN Matcher | Match filings to companies | `hubs/dol-filings/imo/middle/` |
| Signal Emitter | Emit signals to BIT Engine | `hubs/dol-filings/imo/middle/` |

### O — Egress Layer

| Component | Purpose | Destination |
|-----------|---------|-------------|
| BIT Signal | Buyer intent signals | Company Hub BIT Engine |
| Query Interface | Read-only data access | `dol.search_columns()` |
| Metadata Export | Column documentation | `dol.column_metadata` |

---

## 3. Database Schema (HARDENED 2026-01-15)

### Schema: `dol`

| Table | Purpose | Rows | Columns | RLS | Read-Only |
|-------|---------|------|---------|-----|-----------|
| `form_5500` | Large plan filings (>=100 participants) | 230,482 | 147 | Yes | **Yes** |
| `form_5500_sf` | Small plan filings (<100 participants) | 760,839 | 196 | Yes | **Yes** |
| `schedule_a` | Insurance broker/carrier data | 337,476 | 98 | Yes | **Yes** |
| `renewal_calendar` | Plan renewal tracking | - | 13 | Yes | **Yes** |
| `column_metadata` | AI-ready column documentation | 441 | 12 | No | No |

### Read-Only Lock Enforcement

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       DOL DATA READ-ONLY LOCK                                 ║
║                                                                               ║
║   ENFORCEMENT: PostgreSQL BEFORE triggers on INSERT/UPDATE/DELETE            ║
║                                                                               ║
║   BLOCKED OPERATIONS (Normal Access):                                        ║
║   ├── INSERT → DOL_READONLY_VIOLATION                                        ║
║   ├── UPDATE → DOL_READONLY_VIOLATION                                        ║
║   └── DELETE → DOL_READONLY_VIOLATION                                        ║
║                                                                               ║
║   ALLOWED OPERATIONS:                                                         ║
║   └── SELECT → Always permitted                                              ║
║                                                                               ║
║   BYPASS (Annual Import Only):                                               ║
║   ├── SET session dol.import_mode = 'active';                                ║
║   ├── -- run import operations --                                            ║
║   └── RESET dol.import_mode;                                                 ║
║                                                                               ║
║   RATIONALE: DOL data is authoritative. Modifications outside of annual     ║
║              import would corrupt the integrity of government filings.       ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### Migration Reference

| Migration | Purpose | Date |
|-----------|---------|------|
| `2026-01-13-dol-schema-creation.sql` | Initial DOL tables | 2026-01-13 |
| `2026-01-13-enable-rls-production-tables.sql` | RLS policies | 2026-01-13 |
| `2026-01-15-dol-readonly-lock.sql` | Read-only triggers | 2026-01-15 |
| `2026-01-15-dol-column-metadata.sql` | Metadata table | 2026-01-15 |

---

## 4. Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           DOL SCHEMA ERD                                        │
└─────────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────────┐
    │                           dol.form_5500                                  │
    │                        (230,482 rows, 147 cols)                          │
    ├──────────────────────────────────────────────────────────────────────────┤
    │ PK  filing_id              UUID          Unique filing identifier        │
    │     ack_id                 VARCHAR(30)   DOL acknowledgment ID           │
    │     sponsor_dfe_ein        VARCHAR(20)   Employer ID (EIN)               │
    │     sponsor_dfe_name       VARCHAR(255)  Plan sponsor name               │
    │     spons_dfe_mail_us_state VARCHAR(10) Sponsor state                    │
    │     form_plan_year_begin_date VARCHAR(30) Plan year start (renewal)     │
    │     plan_eff_date          VARCHAR(30)   Plan effective date             │
    │     tot_partcp_boy_cnt     NUMERIC       Participants count              │
    │     tot_assets_eoy_amt     NUMERIC       Total assets                    │
    │     form_year              VARCHAR(10)   Filing year (2023)              │
    │     ... (137 more columns)                                               │
    └──────────────────────────────────────────────────────────────────────────┘
                                         │
                                         │ ack_id (FK via ACK_ID match)
                                         │
    ┌──────────────────────────────────────────────────────────────────────────┐
    │                           dol.schedule_a                                 │
    │                        (337,476 rows, 98 cols)                           │
    ├──────────────────────────────────────────────────────────────────────────┤
    │ PK  schedule_id            UUID          Unique schedule identifier      │
    │ FK  filing_id              UUID          Links to form_5500.filing_id    │
    │     ack_id                 VARCHAR(30)   DOL acknowledgment ID           │
    │     sch_a_ein              VARCHAR(20)   Plan EIN                        │
    │     ins_carrier_name       VARCHAR(255)  Insurance carrier name          │
    │     ins_carrier_ein        VARCHAR(20)   Carrier EIN                     │
    │     ins_carrier_naic_code  VARCHAR(10)   NAIC code (5 digits)            │
    │     ins_broker_comm_tot_amt NUMERIC      Broker commissions              │
    │     ins_broker_fees_tot_amt NUMERIC      Broker fees                     │
    │     wlfr_bnft_health_ind   VARCHAR(5)    Health benefits flag            │
    │     wlfr_bnft_dental_ind   VARCHAR(5)    Dental benefits flag            │
    │     wlfr_bnft_vision_ind   VARCHAR(5)    Vision benefits flag            │
    │     sponsor_state          VARCHAR(10)   Derived from Form 5500          │
    │     sponsor_name           VARCHAR(255)  Derived from Form 5500          │
    │     sch_a_plan_year_begin_date VARCHAR(30) Plan year (renewal month)    │
    │     form_year              VARCHAR(10)   Filing year (2023)              │
    │     ... (82 more columns)                                                │
    └──────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────────┐
    │                         dol.form_5500_sf                                 │
    │                        (760,839 rows, 196 cols)                          │
    ├──────────────────────────────────────────────────────────────────────────┤
    │ PK  filing_id              UUID          Unique filing identifier        │
    │     ack_id                 VARCHAR(30)   DOL acknowledgment ID           │
    │     sf_spons_ein           VARCHAR(20)   Employer ID (EIN)               │
    │     sf_sponsor_name        VARCHAR(255)  Plan sponsor name               │
    │     sf_spons_us_state      VARCHAR(10)   Sponsor state                   │
    │     sf_plan_year_begin_date VARCHAR(30)  Plan year start (renewal)      │
    │     sf_plan_eff_date       VARCHAR(30)   Plan effective date             │
    │     sf_tot_partcp_boy_cnt  NUMERIC       Participants count              │
    │     sf_tot_assets_eoy_amt  NUMERIC       Total assets                    │
    │     form_year              VARCHAR(10)   Filing year (2023)              │
    │     ... (186 more columns)                                               │
    └──────────────────────────────────────────────────────────────────────────┘

    NOTE: Form 5500-SF (Small Form) does NOT have Schedule A attachments.
          Schedule A only attaches to regular Form 5500 filings.

    ┌──────────────────────────────────────────────────────────────────────────┐
    │                       dol.column_metadata                                │
    │                          (441 rows, 12 cols)                             │
    ├──────────────────────────────────────────────────────────────────────────┤
    │ PK  id                     SERIAL        Auto-increment ID               │
    │     table_name             VARCHAR(50)   Source table name               │
    │     column_name            VARCHAR(100)  Database column name            │
    │     column_id              VARCHAR(100)  Unique ID (DOL_F5500_*)         │
    │     description            TEXT          Human-readable description       │
    │     category               VARCHAR(50)   Category (Sponsor, Insurance)   │
    │     data_type              VARCHAR(50)   Format type (CURRENCY, DATE)    │
    │     format_pattern         VARCHAR(100)  Pattern (YYYY-MM-DD, 9 digits)  │
    │     max_length             INTEGER       Maximum character length        │
    │     search_keywords        TEXT[]        Array of search terms           │
    │     is_pii                 BOOLEAN       PII flag                        │
    │     is_searchable          BOOLEAN       Searchable flag                 │
    │     example_values         TEXT[]        Sample values from data         │
    └──────────────────────────────────────────────────────────────────────────┘
```

---

## 5. AI-Ready Column Metadata

### Column ID Convention

All columns follow the pattern: `DOL_{TABLE}_{COLUMN_NAME}`

| Table | Prefix | Example |
|-------|--------|---------|
| form_5500 | `DOL_F5500_` | `DOL_F5500_SPONSOR_DFE_NAME` |
| form_5500_sf | `DOL_F5500SF_` | `DOL_F5500SF_SF_SPONSOR_NAME` |
| schedule_a | `DOL_SCHA_` | `DOL_SCHA_INS_BROKER_COMM_TOT_AMT` |

### Category Distribution

| Category | Columns | Description |
|----------|---------|-------------|
| Form | 136 | Filing and form metadata |
| Sponsor | 68 | Plan sponsor information |
| General | 57 | General purpose fields |
| Administrator | 45 | Plan administrator data |
| Welfare | 40 | Welfare benefit indicators |
| Pension | 23 | Pension financial data |
| Preparer | 15 | Form preparer information |
| Filing | 12 | Filing identifiers and dates |
| Insurance | 11 | Insurance carrier/broker data |
| Contract | 9 | Contract type indicators |

### Search Functions

```sql
-- Search columns by keyword
SELECT * FROM dol.search_columns('broker');
SELECT * FROM dol.search_columns('health benefits');
SELECT * FROM dol.search_columns('ein');
SELECT * FROM dol.search_columns('renewal');

-- Get full table schema
SELECT * FROM dol.get_table_schema('schedule_a');
SELECT * FROM dol.get_table_schema('form_5500');
SELECT * FROM dol.get_table_schema('form_5500_sf');

-- Browse metadata by category
SELECT column_id, description, format_pattern
FROM dol.column_metadata
WHERE category = 'Insurance';
```

### Data Format Types

| Format | Pattern | Example Columns |
|--------|---------|-----------------|
| CURRENCY | Decimal dollars (12345.67) | `*_amt` columns |
| DATE | YYYY-MM-DD | `*_date` columns |
| FLAG | Y/N/X or 1/0 | `*_ind` columns |
| EIN | 9 digits (XX-XXXXXXX) | `*_ein` columns |
| INTEGER | Whole number | `*_cnt` columns |
| TEXT | Variable length | Name, address fields |

---

## 6. Data Statistics (2023-2025 Filing Years)

> **Standard View**: See `docs/DATABASE_OVERVIEW_TEMPLATE.md` for the complete Database Overview format.

### DOL Bridge Metrics (2026-02-13 VERIFIED)

| Metric | Count | % |
|--------|-------|---|
| **DOL Linked (EIN)** | 73,617 | 78.2% of 94,129 companies |
| → Has Filing | 69,318 | 94.2% of DOL |
| → Renewal Month | 69,029 | 93.8% of DOL |
| → Carrier | 9,991 | 13.6% of DOL |
| → Broker/Advisor | 6,818 | 9.3% of DOL |

**Percentage Logic**: DOL Linked is measured against total companies. All sub-metrics cascade off DOL Linked.

### Funding Type Breakdown

| Type | Count | % of DOL |
|------|-------|----------|
| Pension Only | 54,673 | 74.3% |
| Fully Insured | 11,567 | 15.7% |
| Unknown | 4,588 | 6.2% |
| Self-Funded | 2,874 | 3.9% |

### Row Counts (3 years: 2023-2025)

**Total: 11,124,508 rows across 27 data-bearing tables + 2 staging tables**

| Table | Rows | Notes |
|-------|------|-------|
| form_5500 | 432,582 | Large filers (100+ participants) |
| form_5500_sf | 1,535,999 | Small filers (<100 participants) |
| schedule_a | 625,520 | Insurance carriers/brokers |
| schedule_c (all sub-tables) | 4,352,852 | Service provider compensation |
| schedule_d (all sub-tables) | 3,322,211 | DFE participation |
| schedule_h/i (all sub-tables) | 307,072 | Plan financials |
| ein_urls | 127,909 | EIN→domain lookup |

### Renewal Month Distribution

| Month | EINs | Outreach Start |
|-------|------|----------------|
| Jan (1) | 60,777 | Aug (8) |
| May (5) | 2,369 | Dec (12) |
| Jun (6) | 1,773 | Jan (1) |
| Jul (7) | 1,686 | Feb (2) |
| All others | 3,537 | Various |
| **Total** | **70,142** | **100% filled** |

---

## 7. Company-First Doctrine

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   IF EIN cannot be matched to company_id:                              │
│       Queue for Company Identity resolution.                            │
│       DO NOT emit signals without valid company anchor.                 │
│                                                                         │
│   DOL Sub-Hub NEVER creates company identity.                          │
│   DOL Sub-Hub requests identity creation from Company Hub.              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Correlation ID Doctrine (HARD LAW)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       CORRELATION ID ENFORCEMENT                              ║
║                                                                               ║
║   DOCTRINE: correlation_id MUST be propagated unchanged across ALL processes ║
║             and into all error logs and emitted signals.                      ║
║                                                                               ║
║   RULES:                                                                      ║
║   1. Every DOL filing processed MUST be assigned a correlation_id            ║
║   2. Every signal emitted to BIT Engine MUST include correlation_id          ║
║   3. Every error logged MUST include correlation_id                          ║
║   4. correlation_id MUST NOT be modified mid-processing                      ║
║                                                                               ║
║   FORMAT: UUID v4 (e.g., "550e8400-e29b-41d4-a716-446655440000")              ║
║   GENERATED BY: DOL ingest process (one per filing)                          ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 9. Signal Emission

### Signal Types

| Signal | Enum | Impact | When Emitted |
|--------|------|--------|--------------|
| `FORM_5500_FILED` | `SignalType.FORM_5500_FILED` | +5.0 | Any 5500 filing matched to company |
| `LARGE_PLAN` | `SignalType.LARGE_PLAN` | +8.0 | Plan with >= 500 participants |
| `BROKER_CHANGE` | `SignalType.BROKER_CHANGE` | +7.0 | Broker changed from prior year |
| `RENEWAL_APPROACHING` | (Planned) | +6.0 | Plan year end within 90 days |

### Signal Idempotency Doctrine

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       SIGNAL IDEMPOTENCY ENFORCEMENT                          ║
║                                                                               ║
║   DEDUPLICATION RULES:                                                        ║
║   ├── Key: (company_id, signal_type, filing_id)                              ║
║   ├── Window: 365 days (DOL filings are annual)                              ║
║   └── Hash: SHA-256 of key fields for fast lookup                            ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 10. Tooling Declaration

| Tool | API | Cost Tier | Rate Limit | Cache |
|------|-----|-----------|------------|-------|
| DOL EFAST2 Bulk Download | External | FREE | N/A | Annual |
| CSV Parser (pandas) | Internal | FREE | N/A | None |
| Column Normalizer | Internal | FREE | N/A | None |
| Metadata Builder | Internal | FREE | N/A | None |
| EIN Lookup | Internal | FREE | N/A | 1 hour |
| Broker Change Detector | Internal | FREE | N/A | 30 days |

---

## 11. Kill Switches

| Switch | Scope | Effect |
|--------|-------|--------|
| `KILL_DOL_SUBHUB` | All DOL processing | Stops entire DOL Sub-Hub |
| `KILL_FORM_5500` | Form 5500 | Stops 5500 processing only |
| `KILL_SCHEDULE_A` | Schedule A | Stops Schedule A processing |
| `KILL_DOL_SIGNALS` | Signal emission | Stops signals to BIT Engine |

---

## 12. Failure Handling

| Failure | Severity | Error Code | Recovery |
|---------|----------|------------|----------|
| EIN not in filing | HIGH | DOL-001 | Manual review |
| EIN not matched | MEDIUM | DOL-002 | Queue for identity |
| Invalid EIN format | LOW | DOL-003 | Normalize and retry |
| Invalid filing format | MEDIUM | DOL-004 | Skip filing |
| Read-only violation | CRITICAL | DOL-005 | Use import_mode bypass |

---

## 13. Promotion Gates

| Gate | Requirement | Status |
|------|-------------|--------|
| G1 | PRD approved (CC-02) | ✓ PASS |
| G2 | ADRs documented (CC-03) | ✓ PASS |
| G3 | Data imported (2023) | ✓ PASS |
| G4 | Read-only lock enabled | ✓ PASS |
| G5 | Column metadata complete | ✓ PASS |
| G6 | RLS policies active | ✓ PASS |

---

## 14. Annual Import Process

### Import Script

```bash
# Enable import mode and load data
doppler run -- python hubs/dol-filings/imo/middle/importers/import_dol_full.py \
    --year 2023 \
    --table all
```

### Bypass Mechanism

```sql
-- For manual operations (use with caution)
SET session dol.import_mode = 'active';
-- ... import operations ...
RESET dol.import_mode;
```

---

## 15. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-17 | Initial DOL Sub-Hub PRD with clean boundaries |
| 2.1 | 2025-12-17 | Hardened: Correlation ID, Signal idempotency, Two-layer errors |
| 2.2 | 2026-01-13 | Database schema created, RLS enabled |
| 3.0 | 2026-01-15 | **2023 data import complete, read-only lock, AI-ready metadata** |
| 4.0 | 2026-02-13 | Updated to 3-year data (2023-2025, 11.1M rows). DOL bridge metrics: 73,617 linked (78.2%). Added funding type breakdown, cascading percentage logic. Reference to Database Overview Template. |

---

## 16. Related Artifacts

| Artifact | Location |
|----------|----------|
| ADR-004 | `docs/adr/ADR-004_DOL_Data_Import_ReadOnly_Lock.md` |
| Hub Manifest | `hubs/dol-filings/hub.manifest.yaml` |
| Import Script | `hubs/dol-filings/imo/middle/importers/import_dol_full.py` |
| Metadata Builder | `hubs/dol-filings/imo/middle/importers/build_column_metadata.py` |
| Migrations | `migrations/2026-01-15-*.sql` |

---

*Document Version: 4.0*
*Last Updated: 2026-02-13*
*Owner: DOL Sub-Hub*
*CC Layer: CC-02*
*Doctrine: CL Parent-Child Doctrine v1.0*

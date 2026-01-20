# PRD: DOL Sub-Hub v3.0

**Version:** 3.0 (Data Import Complete + AI-Ready Metadata)
**Status:** Active
**CC Layer:** CC-02
**Hardening Date:** 2026-01-15
**Last Updated:** 2026-01-15
**Doctrine:** CL Parent-Child Doctrine v1.0 / IMO-Creator Format
**Barton ID Range:** `04.04.03.XX.XXXXX.###`

---

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | 1.1.0 |
| **CC Layer** | CC-02 |
| **CTB Version** | 1.0.0 |

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

## 6. Data Statistics (2023 Filing Year)

### Row Counts

| Table | Rows | Year |
|-------|------|------|
| form_5500 | 230,482 | 2023 |
| form_5500_sf | 760,839 | 2023 |
| schedule_a | 337,476 | 2023 |

### State Coverage

| Table | Unique States |
|-------|---------------|
| form_5500 | 58 |
| form_5500_sf | 58 |
| schedule_a | 55 |

### Top States (Schedule A)

| State | Filings |
|-------|---------|
| CA | 43,313 |
| TX | 22,731 |
| NY | 21,497 |
| PA | 19,098 |
| FL | 17,770 |

### Broker Data Coverage (Schedule A)

| Metric | Count | Percentage |
|--------|-------|------------|
| Records with broker commissions | 235,847 | 70% |
| Records with broker fees | 130,062 | 39% |
| Records with carrier name | 337,358 | 99.9% |

### Welfare Benefit Types (Schedule A)

| Benefit Type | Filings |
|--------------|---------|
| Life Insurance | 79,469 |
| Health | 64,989 |
| Vision | 60,143 |
| Dental | 57,955 |
| HMO | 20,052 |
| PPO | 17,074 |
| Stop Loss | 8,351 |

### Renewal Month Distribution

| Month | Filings | % |
|-------|---------|---|
| January | 235,308 | 70% |
| July | 21,752 | 6% |
| October | 12,078 | 4% |
| April | 10,002 | 3% |

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
    --data-dir data/dol_2023 \
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

---

## 16. Related Artifacts

| Artifact | Location |
|----------|----------|
| ADR-004 | `docs/adr/ADR-004_DOL_Data_Import_ReadOnly_Lock.md` |
| Hub Manifest | `hubs/dol-filings/hub.manifest.yaml` |
| Import Script | `hubs/dol-filings/imo/middle/importers/import_dol_full.py` |
| Metadata Builder | `hubs/dol-filings/imo/middle/importers/build_column_metadata.py` |
| Migrations | `infra/migrations/2026-01-15-*.sql` |

---

*Document Version: 3.0*
*Last Updated: 2026-01-15*
*Owner: DOL Sub-Hub*
*CC Layer: CC-02*
*Doctrine: CL Parent-Child Doctrine v1.0*

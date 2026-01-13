# Cross-Repository Reference

## Ecosystem Overview

This document defines the relationships between repositories in the Barton Outreach
ecosystem, with URLs for Neon PostgreSQL integration.

---

## Repository Registry

| Repository | GitHub URL | Role | Hub Type |
|------------|------------|------|----------|
| **company-lifecycle-cl** | https://github.com/djb258/company-lifecycle-cl.git | Parent Hub | Sovereign Authority |
| **barton-outreach-core** | https://github.com/djb258/barton-outreach-core.git | Child Hub | Execution Surface |
| **site-scout-pro** | https://github.com/djb258/site-scout-pro.git | UI Layer | Read-Only View |

---

## Hierarchy Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        COMPANY LIFECYCLE (CL)                                │
│                https://github.com/djb258/company-lifecycle-cl.git           │
│                                                                             │
│   Hub ID: HUB-CL-001                                                        │
│   Role: PARENT HUB - Sovereign Identity Authority                           │
│                                                                             │
│   OWNS:                                                                     │
│   • company_unique_id (mints, merges, retires)                             │
│   • lifecycle_state (OUTREACH → SALES → CLIENT → RETIRED)                  │
│   • Promotion authority                                                     │
│   • Sub-hub activation                                                      │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      │ company_unique_id (READ-ONLY downstream)
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BARTON OUTREACH CORE                                  │
│                https://github.com/djb258/barton-outreach-core.git           │
│                                                                             │
│   Hub ID: HUB-OUTREACH                                                      │
│   Role: CHILD HUB - Outreach Execution                                      │
│                                                                             │
│   RECEIVES: company_unique_id from CL                                       │
│   OWNS: campaigns, sequences, send_log, engagement_events                   │
│   CANNOT: Mint IDs, promote lifecycle, modify CL                            │
│                                                                             │
│   Internal Sub-Hubs:                                                        │
│   ├── Company Target (internal anchor, joins to CL)                         │
│   ├── People (contacts, slots)                                              │
│   ├── DOL (filings, renewals)                                               │
│   └── Blog / Content (signals, news)                                        │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      │ READ-ONLY Neon access
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SITE SCOUT PRO                                      │
│                https://github.com/djb258/site-scout-pro.git                 │
│                                                                             │
│   Role: UI LAYER - Looking Glass into Neon                                  │
│                                                                             │
│   READS: All Neon tables (no writes)                                        │
│   PROVIDES: React/TypeScript frontend via Lovable.dev                       │
│   CANNOT: Write to any database table                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Company Lifecycle (CL) - Parent Hub

**GitHub**: https://github.com/djb258/company-lifecycle-cl.git

### Purpose

CL is the **constitutional root** for company identity. It is the **only** system
authorized to mint, merge, or retire `company_unique_id`.

### Doctrine Documents

| Document | Path | Purpose |
|----------|------|---------|
| CL Doctrine | `docs/doctrine/CL_DOCTRINE.md` | Complete conceptual model |
| Conceptual Schema | `docs/doctrine/CONCEPTUAL_SCHEMA.md` | Schema invariants |
| Invariants | `docs/doctrine/INVARIANTS_AND_KILL_SWITCHES.md` | Hard constraints |
| ADR-001 | `docs/adr/ADR-001-lifecycle-state-machine.md` | Lifecycle state machine |

### Neon Tables Owned

| Schema | Table | Purpose |
|--------|-------|---------|
| `cl` | `company_identity` | Sovereign company records |
| `cl` | `lifecycle_state` | Current lifecycle truth |
| `cl` | `lifecycle_history` | Append-only audit trail |
| `cl` | `external_id_mapping` | External system aliases |
| `cl` | `merge_records` | Identity consolidation audit |
| `cl` | `retirement_records` | Identity retirement audit |

### Key Attributes Owned

```sql
-- CL owns these and ONLY these
company_unique_id    -- Sovereign, immutable identifier
legal_name           -- Canonical company name
cl_stage             -- OUTREACH | SALES | CLIENT | RETIRED
outreach_uid         -- Pointer to Outreach sub-hub
sales_uid            -- Pointer to Sales sub-hub
client_uid           -- Pointer to Client sub-hub
created_at           -- Identity mint timestamp
promoted_at          -- Last promotion timestamp
retired_at           -- Retirement timestamp
```

### Authority

| Action | CL Authority |
|--------|--------------|
| Mint company_unique_id | ✅ EXCLUSIVE |
| Merge identities | ✅ EXCLUSIVE |
| Retire identities | ✅ EXCLUSIVE |
| Promote lifecycle | ✅ EXCLUSIVE |
| Activate sub-hubs | ✅ EXCLUSIVE |

---

## 2. Barton Outreach Core - Child Hub

**GitHub**: https://github.com/djb258/barton-outreach-core.git

### Purpose

Outreach is a **child sub-hub** of CL. It executes campaigns, sequences, and
engagement tracking. It **receives** `company_unique_id` from CL and **cannot**
mint, merge, retire, or promote.

### Doctrine Documents

| Document | Path | Purpose |
|----------|------|---------|
| Outreach README | `hubs/outreach-execution/README.md` | Authoritative model |
| Schema Alignment | `hubs/outreach-execution/SCHEMA_ALIGNMENT_NOTES.md` | Join hierarchy |
| Compliance Checklist | `hubs/outreach-execution/DOCTRINE_COMPLIANCE_CHECKLIST.md` | 46-point verification |
| Invariant List | `hubs/outreach-execution/INVARIANT_LIST.md` | 28 non-negotiable rules |
| Hub Manifest | `hubs/outreach-execution/hub.manifest.yaml` | Hub configuration |

### Neon Tables Owned

| Schema | Table | Purpose |
|--------|-------|---------|
| `outreach` | `company_target` | Internal anchor (joins to CL) |
| `outreach` | `people` | Contact records |
| `outreach` | `dol_filings` | DOL filing data |
| `outreach` | `blog_signals` | News/content signals |
| `outreach` | `campaigns` | Campaign definitions |
| `outreach` | `sequences` | Sequence definitions |
| `outreach` | `send_log` | Email send history |
| `outreach` | `engagement_events` | Opens, clicks, replies |

### Foreign Key to CL

```sql
-- Company Target is the ONLY table that joins directly to CL
CREATE TABLE outreach.company_target (
    target_id TEXT PRIMARY KEY,
    company_unique_id TEXT NOT NULL,  -- FK to CL

    CONSTRAINT fk_company_lifecycle
        FOREIGN KEY (company_unique_id)
        REFERENCES cl.company_identity(company_unique_id)
        ON DELETE RESTRICT
);
```

### Authority

| Action | Outreach Authority |
|--------|-------------------|
| Mint company_unique_id | ❌ PROHIBITED |
| Merge identities | ❌ PROHIBITED |
| Retire identities | ❌ PROHIBITED |
| Promote lifecycle | ❌ PROHIBITED |
| Signal engagement | ✅ ALLOWED |
| Execute campaigns | ✅ ALLOWED |
| Track sends/opens/replies | ✅ ALLOWED |

---

## 3. Site Scout Pro - UI Layer

**GitHub**: https://github.com/djb258/site-scout-pro.git

### Purpose

Site Scout Pro is the **UI layer** that provides a **read-only looking glass** into
Neon PostgreSQL. It connects to the Outreach repo and displays data without
modifying it.

### Architecture

- **Frontend**: React/TypeScript via Lovable.dev
- **Backend**: FastAPI (fully async)
- **Database**: Neon PostgreSQL (READ-ONLY)
- **Pattern**: Backend-only mode for AI development

### Neon Access

| Access Level | Permissions |
|--------------|-------------|
| CL tables | READ-ONLY |
| Outreach tables | READ-ONLY |
| Marketing tables | READ-ONLY |
| All writes | ❌ PROHIBITED |

### Key Constraint

```
┌─────────────────────────────────────────────────────────────────┐
│                    SITE SCOUT PRO                                │
│                                                                 │
│   ✅ CAN: Display data from any Neon table                      │
│   ✅ CAN: Filter, sort, aggregate for display                   │
│   ✅ CAN: Generate reports and visualizations                   │
│                                                                 │
│   ❌ CANNOT: INSERT, UPDATE, DELETE any row                     │
│   ❌ CANNOT: Modify company_unique_id                           │
│   ❌ CANNOT: Change lifecycle_state                             │
│   ❌ CANNOT: Execute business logic                             │
│                                                                 │
│   The UI is a LOOKING GLASS, not an execution surface.          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Neon PostgreSQL Integration

### Connection Reference

**Host**: `ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech`
**Port**: `5432`
**Database**: `Marketing DB`
**SSL Mode**: `require`

### Schema Hierarchy

```
Neon PostgreSQL
├── cl (Company Lifecycle schema)
│   ├── company_identity      -- CL owns
│   ├── lifecycle_state       -- CL owns
│   ├── lifecycle_history     -- CL owns
│   ├── external_id_mapping   -- CL owns
│   ├── merge_records         -- CL owns
│   └── retirement_records    -- CL owns
│
├── outreach (Outreach Execution schema)
│   ├── company_target        -- Outreach owns (FK to CL)
│   ├── people                -- Outreach owns
│   ├── dol_filings           -- Outreach owns
│   ├── blog_signals          -- Outreach owns
│   ├── campaigns             -- Outreach owns
│   ├── sequences             -- Outreach owns
│   ├── send_log              -- Outreach owns
│   └── engagement_events     -- Outreach owns
│
├── marketing (Legacy/shared schema)
│   ├── company_master        -- Legacy (migrate to CL)
│   ├── people_master         -- People Hub owns
│   └── company_slot          -- People Hub owns
│
└── public (System schema)
    └── shq_error_log         -- System-wide errors
```

### Join Path

```sql
-- Full join from Outreach sub-hub through to CL
SELECT
    p.person_id,
    p.email,
    ct.target_id,
    ct.outreach_status,
    ci.company_unique_id,
    ci.legal_name,
    ls.cl_stage
FROM outreach.people p
INNER JOIN outreach.company_target ct ON p.target_id = ct.target_id
INNER JOIN cl.company_identity ci ON ct.company_unique_id = ci.company_unique_id
INNER JOIN cl.lifecycle_state ls ON ci.company_unique_id = ls.company_unique_id;
```

---

## Cross-Repo Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW                                       │
└─────────────────────────────────────────────────────────────────────────────┘

                    COMPANY LIFECYCLE (CL)
                    ──────────────────────
                    • Mints company_unique_id
                    • Owns lifecycle_state
                    • Writes to cl.* tables
                             │
                             │ company_unique_id
                             │ (via spoke)
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       BARTON OUTREACH CORE                                   │
│                                                                             │
│   RECEIVES: company_unique_id                                               │
│   WRITES: outreach.* tables                                                 │
│   SIGNALS: engagement_events back to CL                                     │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      │ Neon connection (read)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SITE SCOUT PRO                                      │
│                                                                             │
│   READS: cl.*, outreach.*, marketing.*                                      │
│   DISPLAYS: Dashboards, reports, visualizations                             │
│   WRITES: Nothing (looking glass only)                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Repository Links

### Quick Access

| Repo | Clone URL |
|------|-----------|
| CL | `git clone https://github.com/djb258/company-lifecycle-cl.git` |
| Outreach | `git clone https://github.com/djb258/barton-outreach-core.git` |
| UI | `git clone https://github.com/djb258/site-scout-pro.git` |

### Key Files

| Repo | Key File | Purpose |
|------|----------|---------|
| CL | `docs/doctrine/CL_DOCTRINE.md` | Parent hub doctrine |
| CL | `docs/doctrine/CONCEPTUAL_SCHEMA.md` | Schema invariants |
| Outreach | `hubs/outreach-execution/README.md` | Child hub model |
| Outreach | `hubs/outreach-execution/INVARIANT_LIST.md` | 28 rules |
| UI | `docs/ERD.md` | Full database ERD |
| UI | `README.md` | Backend/frontend architecture |

---

## Doctrine Alignment Summary

| Aspect | CL | Outreach | UI |
|--------|-----|----------|-----|
| Mints company_unique_id | ✅ | ❌ | ❌ |
| Owns lifecycle_state | ✅ | ❌ | ❌ |
| Writes to Neon | ✅ | ✅ (own tables) | ❌ |
| Reads from Neon | ✅ | ✅ | ✅ |
| Executes campaigns | ❌ | ✅ | ❌ |
| Displays data | ❌ | ❌ | ✅ |

---

*Last Updated: 2025-12-26*
*Doctrine Version: CL Parent-Child Model v1.1*

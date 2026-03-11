# Claude Bootstrap Guide - Barton Outreach Core

## INSTANT REPO OVERVIEW

**Repository Name**: Barton Outreach Core
**Architecture**: CL Parent-Child Doctrine
**Primary Purpose**: Marketing intelligence & executive enrichment platform
**Database**: CF D1/KV (working) + Neon PostgreSQL (vault/archive)
**Frontend**: Figma UI (design) — scaffolding present but NOT active. Python/SQL is the current working stack. Do not run npm commands unless explicitly instructed for frontend work.
**Last Refactored**: 2026-02-15
**Manifest Version**: 2.8.0 (synced 2026-02-15)

---

## SESSION STARTUP (MANDATORY)

Every session, before any work. See `STARTUP_PROTOCOL.md` for full sequence.

1. **Doctrine version check** — compare `DOCTRINE.md` version vs parent `TEMPLATES_MANIFEST.yaml`
2. **Load Tier 1** — 3 files only: `IMO_CONTROL.json`, `CC_OPERATIONAL_DIGEST.md`, `CLAUDE.md`
3. **Verify checkpoint** — read `DOCTRINE_CHECKPOINT.yaml`, fill if stale (>24h)
4. **Ready** — begin work, load Tier 2 on-demand

**Rollback**: If a doctrine sync breaks the repo, see `doctrine/ROLLBACK_PROTOCOL.md`.

---

## OSAM: Outreach Semantic Access Map

> **BEFORE RUNNING ANY DATA QUERY, READ: [docs/OSAM.md](docs/OSAM.md)**

The OSAM tells you exactly where to go for any data question:
- Company count by state? → `outreach.company_target`
- Slot fill rates? → `people.company_slot`
- Contact details? → `people.people_master`
- DOL filings? → `outreach.dol`

**Rule**: If your question isn't in the OSAM, **STOP and ask the user**. Do not guess.

**Universal Join Key**: `outreach_id` - All sub-hubs join to the spine via this key. Never use domain as a join key.

### ⛔ BEFORE EDITING ANY SUB-HUB DEFINITION (OSAM, PRD, ERD, SCHEMA):

> Each sub-hub has exactly **4 core tables** (CANONICAL / ERRORS / MV / REGISTRY).
> Everything else is supportive reference data — queryable, but **NOT a sub-hub member**.
>
> | Sub-Hub | CANONICAL | ERRORS | MV | REGISTRY |
> |---------|-----------|--------|----|----------|
> | company_target | company_target | company_target_errors | company_hub_status | - |
> | dol | dol | dol_errors | form_5500_icp_filtered | column_metadata |
> | blog | blog | blog_errors | - | blog_ingress_control |
> | people | company_slot (CANONICAL) + people_master (SUPPORTING, ADR-020) | people_errors | - | slot_ingress_control, title_slot_mapping |
> | bit | bit_scores | bit_errors | - | - |
>
> **Do NOT elevate supportive/reference tables to sub-hub members.** The `dol.*` schema has 27 data-bearing filing tables (+ 2 empty staging tables) — they feed INTO `outreach.dol`, they are not part of the sub-hub. Total: 11,124,508 rows across 3 years (2023–2025).

---

## CRITICAL: Authoritative Table Reference

> **ALL pipeline work MUST use `outreach.company_target` as the authoritative company list.**
> **CL TOTAL: 102,922** (95,004 sovereign eligible + 6,499 excluded + 1,419 new lanes)
> **OUTREACH SPINE: 95,837** (95,004 cold outreach + 833 fractional CFO)
> **THREE MESSAGING LANES**: Cold Outreach (95,837) | Appointments Already Had (771) | Fractional CFO Partners (833)
> **PRIMARY KEY: `outreach_id`**

### DO NOT USE These Tables as Company Source:
- `company.company_master` - too broad
- `people.people_master` - people, not companies
- `enrichment.*` tables - source data, not for queries

### Key Documentation:
- **[docs/OSAM.md](docs/OSAM.md)** - WHERE TO GO for any data question
- **[docs/diagrams/PEOPLE_DATA_FLOW_ERD.md](docs/diagrams/PEOPLE_DATA_FLOW_ERD.md)** - People slot/enrichment flow

### Current Enrichment Status (2026-02-09 VERIFIED):
| Metric | Count | % |
|--------|-------|---|
| **CL total** | **102,922** | — |
| **Sovereign eligible (cold outreach)** | **95,004** | — |
| Excluded (non-commercial) | 6,499 | — |
| **Outreach spine** | **95,837** | 95,004 + 833 fractional CFO |
| With email_method | 82,074 | 86.4% |
| Slot fill (CEO) | 62,289 | 65.6% |
| Slot fill (CFO) | 57,327 | 60.3% |
| Slot fill (HR) | 58,141 | 61.2% |
| **Overall slot fill** | **177,757 / 285,012** | **62.4%** |
| **People count** | **182,946** | — |

### Three Messaging Lanes (2026-02-09):
| Lane | Table | Records | Source |
|------|-------|---------|--------|
| **Cold Outreach** | `outreach.company_target` | 95,837 | CLS scoring |
| **Appointments Already Had** | `sales.appointments_already_had` | 771 | CSV import |
| **Fractional CFO Partners** | `partners.fractional_cfo_master` | 833 | Clay + Hunter |

**CL Source Systems**: hunter_dol_enrichment (54,155) | clay_import (39,298) | clay (7,060) | fractional_cfo_outreach (904) | orphan_mint (765) | barton_appointments (496) | apollo_import (225) | MANUAL_OUTREACH_2026 (19)

### DOL Bridge Enrichment Status (2026-02-06):
| Column | Fill | Notes |
|--------|------|-------|
| ein | 70,150 (100%) | 9-digit, no dashes |
| filing_present | 64,975 (92%) | Has Form 5500 |
| funding_type | 70,150 (100%) | pension_only / fully_insured / self_funded |
| carrier | 10,233 (14.6%) | From Schedule A health |
| broker_or_advisor | 6,995 (10%) | From Schedule C code 28 |
| **renewal_month** | **70,142 (100%)** | **Plan year begin month (1-12)** |
| **outreach_start_month** | **70,142 (100%)** | **5 months before renewal (1-12)** |

### Email Verification Status (2026-02-10):

**Email verification data is inline below.**

| Metric | Count | % |
|--------|-------|---|
| **Unique emails verified** | 60,431 | 100% |
| **VALID** (outreach_ready=TRUE) | 43,330 | 71.7% |
| **RISKY** (catch-all domains) | 9,223 | 15.3% |
| **INVALID** (need re-enrichment) | 7,878 | 13.0% |
| **Deliverable rate** | — | **87.0%** |

**Slots needing re-enrichment**: CEO (4,946) + CFO (3,965) + HR (3,444) = **12,355 total**

**Key columns in `people.people_master`**:
- `email_verified = TRUE` → Email checked (VALID or RISKY)
- `outreach_ready = TRUE` → Safe to send outreach
- `email_verified = FALSE AND outreach_ready = FALSE` → INVALID, needs Hunter re-enrichment

**Re-enrichment**: 18,457 domains need fresh Hunter contacts (12,355 slots total)

---

## 🔗 BLOG SUB-HUB URL STORAGE

> **Need About Us, News/Press, or any historical URL data?** Query `vendor.blog` (Tier-1 staging)
> All URL tables (`company.company_source_urls`, `outreach.source_urls`, `outreach.sitemap_discovery`) were DROPPED in Phase 3 Legacy Collapse (2026-02-20). Data preserved in `vendor.blog`.

### Table: `vendor.blog` (289,624 rows)

| Source Table (filter) | Rows | URL Types |
|-----------------------|------|-----------|
| `company.company_source_urls` | 114,736 | about_page, press_page, leadership_page, team_page, careers_page, contact_page |
| `outreach.sitemap_discovery` | 93,596 | Sitemap URLs, domain health |
| `outreach.source_urls` | 81,292 | Spine-linked canonical URLs |

### Quick Queries
```sql
-- About Us URLs
SELECT source_row_id, source_url FROM vendor.blog
WHERE source_table = 'company.company_source_urls' AND source_type = 'about_page';

-- All URL types for a company (by outreach_id)
SELECT source_type, source_url, source_table FROM vendor.blog
WHERE outreach_id = '<uuid>';

-- Sitemap data
SELECT outreach_id, domain, sitemap_url, has_sitemap FROM vendor.blog
WHERE source_table = 'outreach.sitemap_discovery';
```

---

## v1.0 OPERATIONAL BASELINE

**Status**: CERTIFIED AND FROZEN
**Certification Date**: 2026-01-19
**Baseline Freeze Date**: 2026-01-20
**Sovereign Cleanup**: 2026-01-21 (23,025 records archived)
**Commercial Eligibility Cleanup**: 2026-01-29 (5,259 excluded + 4,577 phantoms + 2,709 orphans)
**Exclusion Consolidation**: 2026-01-30 (2,432 total excluded records)
**CL Total**: 102,922 | **Outreach Spine**: 95,837 | **Three Lanes**: Cold (95,837) + Appointments (771) + CFO Partners (833)
**Safe to Enable Live Marketing**: YES

### Key Documentation

| Document | Purpose |
|----------|---------|
| `docs/OSAM.md` | **QUERY ROUTING** - Which table for which question |
| `doctrine/DO_NOT_MODIFY_REGISTRY.md` | Frozen components requiring change request |

### Deferred Work Orders

| Work Order | Status | Description |
|------------|--------|-------------|
| WO-DOL-001 | DEFERRED | DOL enrichment pipeline (EIN resolution) |

### DO NOT MODIFY (v1.0 Frozen)

The following components are **FROZEN** and require formal change request:
- `outreach.vw_sovereign_completion` (sovereign view)
- Tier computation logic and assignment rules
- Marketing safety gate (HARD_FAIL enforcement)
- Hub registry and waterfall order
- **Note**: `outreach.vw_marketing_eligibility_with_overrides`, `outreach.manual_overrides`, and `outreach.override_audit_log` were dropped 2026-02-20 (empty, no overrides active). Recreatable from `migrations/2026-01-19-kill-switches.sql` if needed.

See `doctrine/DO_NOT_MODIFY_REGISTRY.md` for complete list.

---

## IMO-CREATOR TEMPLATE INHERITANCE

### Parent-Child Relationship

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         IMO-CREATOR (PARENT REPO)                            │
│                                                                              │
│  Location: C:\Users\CUSTOM PC\Desktop\Cursor Builds\imo-creator              │
│  Authority: CANONICAL — Source of truth for all templates                    │
│  Status: LOCKED — Only human-approved changes                                │
│                                                                              │
│  Owns:                                                                       │
│  ├── templates/doctrine/          # Canonical doctrine files                 │
│  ├── templates/claude/            # AI prompt templates                      │
│  ├── templates/checklists/        # Audit checklists                         │
│  ├── templates/audit/             # Attestation templates                    │
│  ├── templates/adr/               # ADR templates                            │
│  ├── templates/prd/               # PRD templates                            │
│  └── templates/pr/                # PR templates                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ PULL ONLY (never push)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     BARTON-OUTREACH-CORE (CHILD REPO)                        │
│                                                                              │
│  Location: C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core     │
│  Role: CONSUMER — Inherits templates from IMO-Creator                        │
│                                                                              │
│  templates/ directory mirrors IMO-Creator structure                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Template Sync Rules (LOCKED)

| Rule | Enforcement |
|------|-------------|
| **Direction** | PULL from IMO-Creator → barton-outreach-core |
| **Never Push** | AI agents CANNOT push changes to IMO-Creator |
| **Human Approval** | IMO-Creator changes require human approval + ADR |
| **Sync Commit** | Use `chore(templates): Sync IMO-creator to vX.X.X` |

### Sync Process

```bash
# 1. Read latest templates from IMO-Creator
#    Source: imo-creator/templates/

# 2. Write to barton-outreach-core
#    Destination: barton-outreach-core/templates/

# 3. Commit with sync message
git commit -m "chore(templates): Sync IMO-creator to vX.X.X - [description]"
```

### NEVER DO (Template Inheritance)

- **NEVER** push changes to IMO-Creator
- **NEVER** modify doctrine files without human approval
- **NEVER** create local-only doctrine (use IMO-Creator)
- **NEVER** diverge from IMO-Creator template structure

---

## CORE ARCHITECTURE: CL AUTHORITY REGISTRY + OUTREACH SPINE

### The Golden Rule

```
IF outreach_id IS NULL:
    STOP. DO NOT PROCEED.
    1. Mint outreach_id in outreach.outreach (operational spine)
    2. Write outreach_id ONCE to cl.company_identity (authority registry)
    3. If CL write fails (already claimed) → HARD FAIL

ALIGNMENT RULE:
outreach.outreach count = cl.company_identity (outreach_id NOT NULL) count
CL Total: 102,922 (95,004 eligible + 6,499 excluded + 1,419 new lanes)
Outreach Spine: 95,837 (95,004 cold + 833 fractional CFO)
```

### CL Authority Registry (LOCKED)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CL = AUTHORITY REGISTRY (Identity Pointers Only)          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  cl.company_identity                                                         │
│  ────────────────────                                                        │
│  sovereign_company_id   PK, IMMUTABLE (minted by CL)                         │
│  outreach_id            WRITE-ONCE (minted by Outreach, written here)        │
│  sales_process_id       WRITE-ONCE (minted by Sales, written here)           │
│  client_id              WRITE-ONCE (minted by Client, written here)          │
│                                                                              │
│  ╔═══════════════════════════════════════════════════════════════════════╗   │
│  ║ CL stores IDENTITY POINTERS only — never workflow state               ║   │
│  ║ Each hub mints its own ID and registers it ONCE in CL                 ║   │
│  ╚═══════════════════════════════════════════════════════════════════════╝   │
│                                                                              │
│  v_company_lifecycle_status (READ-ONLY VIEW)                                 │
│  → Exposes which hubs have claimed each company                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│   OUTREACH    │           │    SALES      │           │    CLIENT     │
│   (THIS HUB)  │           │               │           │               │
├───────────────┤           ├───────────────┤           ├───────────────┤
│ Mints:        │           │ Mints:        │           │ Mints:        │
│ outreach_id   │           │ sales_process │           │ client_id     │
│               │           │ _id           │           │               │
│ Writes to CL: │           │ Writes to CL: │           │ Writes to CL: │
│ outreach_id   │           │ sales_process │           │ client_id     │
│ (ONCE)        │           │ _id (ONCE)    │           │ (ONCE)        │
└───────────────┘           └───────────────┘           └───────────────┘
```

### Outreach Operational Spine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OUTREACH OPERATIONAL SPINE (Workflow State)               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  outreach.outreach (OPERATIONAL SPINE)                                       │
│  ─────────────────────────────────────                                       │
│  outreach_id            PK (minted here, registered in CL)                   │
│  sovereign_company_id   FK → cl.company_identity                             │
│  status                 WORKFLOW STATE (not in CL)                           │
│  created_at, updated_at OPERATIONAL TIMESTAMPS                               │
│                                                                              │
│  ╔═══════════════════════════════════════════════════════════════════════╗   │
│  ║ outreach.outreach = operational spine (workflow state lives here)     ║   │
│  ║ cl.company_identity = authority registry (identity pointer only)      ║   │
│  ╚═══════════════════════════════════════════════════════════════════════╝   │
│                                                                              │
│                                    │                                         │
│                                    │ outreach_id (FK for all sub-hubs)       │
│                                    ▼                                         │
│  1. COMPANY TARGET (04.04.01) ──────────────────────────────► PASS REQUIRED │
│     • Domain resolution, email pattern discovery                             │
│     • Table: outreach.company_target (FK: outreach_id)                       │
│                                    │                                         │
│                                    ▼                                         │
│  2. DOL FILINGS (04.04.03) ─────────────────────────────────► PASS REQUIRED │
│     • EIN resolution, Form 5500 + Schedule A                                 │
│     • Table: outreach.dol (FK: outreach_id)                                  │
│                                    │                                         │
│                                    ▼                                         │
│  3. PEOPLE INTELLIGENCE (04.04.02) ─────────────────────────► PASS REQUIRED │
│     • Slot assignment, email generation                                      │
│     • Table: outreach.people (FK: outreach_id)                               │
│                                    │                                         │
│                                    ▼                                         │
│  4. BLOG CONTENT (04.04.05) ────────────────────────────────► PASS          │
│     • Content signals, news monitoring                                       │
│     • Table: outreach.blog (FK: outreach_id)                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Outreach Init Pattern (LOCKED)

```python
# STEP 1: Verify company exists in CL and outreach_id is NULL
SELECT sovereign_company_id FROM cl.company_identity
WHERE sovereign_company_id = $sid
  AND outreach_id IS NULL;

# STEP 2: Mint outreach_id in operational spine
INSERT INTO outreach.outreach (outreach_id, sovereign_company_id, status)
VALUES ($new_outreach_id, $sid, 'INIT');

# STEP 3: Register outreach_id in CL authority registry (WRITE-ONCE)
UPDATE cl.company_identity
SET outreach_id = $new_outreach_id
WHERE sovereign_company_id = $sid
  AND outreach_id IS NULL;

# MUST check affected rows
if affected_rows != 1:
    ROLLBACK()
    HARD_FAIL("Outreach ID already claimed or invalid SID")
```

### Data Ownership (LOCKED)

| Location | Stores | Example |
|----------|--------|---------|
| **cl.company_identity** | Identity pointers ONLY | outreach_id, sales_process_id, client_id |
| **outreach.outreach** | Operational spine + workflow state | status, timestamps |
| **outreach.*** | Outreach sub-hub data | people, signals, contacts, attempts |

### Outreach Responsibilities (LOCKED)

| Outreach DOES | Outreach DOES NOT |
|---------------|-------------------|
| Mint outreach_id | Mint sales_process_id or client_id |
| Write outreach_id to CL (ONCE) | Write workflow state to CL |
| Drive calendar link generation | Perform Sales or Client logic |
| Handoff via booking webhook | Live-sync with downstream hubs |
| Own: contacts, people, signals | Own: sales pipeline, client records |

### Calendar Handoff Pattern

```
OUTREACH                                    SALES
   │                                          │
   │ ──► Generate calendar link               │
   │     (signed: sid + oid + sig + TTL)      │
   │                                          │
   │ ──► Meeting booked webhook ─────────────►│
   │                                          │
   │     [OUTREACH ENDS HERE]                 │ Sales Init worker
   │                                          │ (snapshots Outreach data)
   │                                          │ Mints sales_process_id
   │                                          │ Writes to CL (ONCE)
```

### Key Doctrine (LOCKED)

- **CL is authority registry** — Identity pointers only, never workflow state
- **outreach.outreach is operational spine** — Workflow state lives here
- **WRITE-ONCE to CL** — Each hub mints its ID and registers ONCE
- **No sub-hub writes without valid outreach_id**
- **Handoff via webhook** — Outreach does not invoke Sales directly

### Waterfall Doctrine Rules (LOCKED)

| Rule | Enforcement |
|------|-------------|
| Each sub-hub must PASS before next executes | Gate validation |
| No lateral reads between hubs | Spoke contracts only |
| No speculative execution | PASS gate blocks downstream |
| No retry/rescue from downstream | Failures stay local |
| Data flows FORWARD ONLY* | Bound by outreach_context_id |
| Sub-hubs may re-run if upstream unchanged | Idempotent design |

*\*Exception: Verified Email → CT Promotion (reverse flow per Waterfall Doctrine v1.3*

### Verification Agent Chain (v1.3)

| Agent | Trigger | Action |
|-------|---------|--------|
| **Promotion Agent** | People verified_status = VERIFIED | Promotes email to CT, derives pattern |
| **Verification Gate** | CT has verified email + pattern | Flips email_pattern_status GUESS → FACT |
| **Bounce Downgrade** | Hard bounce on verified email | Unlocks pattern, resets to GUESS |

**Waterfall Doctrine**: v1.3 (rules are inline above)

### Hub Registry (Waterfall Order)

| Order | Hub | Doctrine ID | Core Metric | Entities Owned |
|-------|-----|-------------|-------------|----------------|
| 1 | **Company Lifecycle (CL)** | PARENT | LIFECYCLE_STATE | cl.company_identity, cl.lifecycle_state |
| 2 | **Company Target** | 04.04.01 | BIT_SCORE | outreach.company_target, verified_pattern |
| 3 | **DOL Filings** | 04.04.03 | FILING_MATCH_RATE | form_5500, schedule_a, ein_registry |
| 4 | **People Intelligence** | 04.04.02 | SLOT_FILL_RATE | outreach.people, slot_assignments |
| 5 | **Blog Content** | 04.04.05 | CONTENT_SIGNAL_RATE | blog_signals, news_events |
| 6 | **Coverage** | 04.04.06 | COVERAGE_ZIP_COUNT | service_agent_coverage, v_service_agent_coverage_zips |

**Note**: People Intelligence (04.04.02) executes AFTER DOL Filings (04.04.03) in the waterfall.

### Spoke Contracts

| Contract | Direction | Trigger |
|----------|-----------|---------|
| company-people | Bidirectional | slot_requirement / slot_assignment |
| company-dol | Bidirectional | ein_lookup / filing_signal |
| company-outreach | Bidirectional | target_selection / engagement_signal |
| people-outreach | Bidirectional | contact_selection / contact_state |
| signal-company | Ingress Only | external signals into company |

### Key Doctrine Rules

1. **CL is AUTHORITY REGISTRY** - Stores identity pointers only (outreach_id, sales_process_id, client_id)
2. **CL mints sovereign_company_id** - Outreach receives, never creates
3. **Outreach mints outreach_id** - Written to CL ONCE, workflow state stays in outreach.outreach
4. **outreach.outreach is operational spine** - All sub-hubs FK to outreach_id
5. **Spokes are I/O ONLY** - No logic, no state, no transformation
6. **Handoff via webhook** - Outreach does not invoke Sales/Client directly

---

## REPOSITORY STRUCTURE

```
barton-outreach-core/
│
├── hubs/                              # HUB LOGIC (IMO Pattern)
│   ├── __init__.py                    # Hub registry
│   ├── company-target/                # Internal anchor (04.04.01)
│   │   ├── hub.manifest.yaml
│   │   ├── __init__.py
│   │   └── imo/
│   │       ├── input/                 # Incoming spoke data
│   │       ├── middle/                # Business logic
│   │       │   ├── company_hub.py
│   │       │   ├── bit_engine.py
│   │       │   ├── company_pipeline.py
│   │       │   ├── phases/            # Phases 1-4
│   │       │   └── email/             # Pattern discovery
│   │       └── output/                # Outgoing spoke data
│   │           └── neon_writer.py
│   │
│   ├── people-intelligence/           # Sub-hub (04.04.02)
│   │   ├── hub.manifest.yaml
│   │   └── imo/
│   │       ├── input/
│   │       ├── middle/
│   │       │   ├── people_hub.py
│   │       │   ├── slot_assignment.py
│   │       │   ├── phases/            # Phases 5-8
│   │       │   ├── movement_engine/   # Movement detection
│   │       │   └── sub_wheels/        # Email verification
│   │       └── output/
│   │
│   ├── dol-filings/                   # Sub-hub (04.04.03)
│   │   ├── hub.manifest.yaml
│   │   └── imo/
│   │       └── middle/
│   │           ├── dol_hub.py
│   │           ├── ein_matcher.py
│   │           ├── processors/
│   │           └── importers/
│   │
│   ├── blog-content/                  # Sub-hub (04.04.05)
│   │   ├── hub.manifest.yaml
│   │   └── imo/
│   │       └── middle/
│   │           ├── classify_event.py          # Blog content classification
│   │           ├── extract_entities.py        # Entity extraction
│   │           ├── parse_content.py           # Content parsing
│   │           ├── validate_signal.py         # Signal validation
│   │           ├── match_company.py           # Company matching
│   │           └── hub_status.py              # Hub status reporting
│   │
│   ├── outreach-execution/            # Sub-hub (04.04.04)
│   │   ├── hub.manifest.yaml
│   │   └── imo/
│   │       └── middle/
│   │           └── outreach_hub.py
│   │
│   ├── coverage/                      # Coverage Hub (04.04.06)
│   │   ├── hub.manifest.yaml
│   │   └── imo/
│   │       └── middle/
│   │           ├── run_coverage.py              # Single entry point
│   │           ├── coverage_report.py           # Sub-hub completeness report
│   │           ├── route_gaps.py                # Gap routing to error tables
│   │           └── create_service_agent_coverage.py  # Low-level coverage creation
│   │
│   └── talent-flow/                   # Executive movement detection
│       ├── hub.manifest.yaml
│       └── imo/
│           └── middle/
│
├── spokes/                            # I/O ONLY CONNECTORS
│   ├── __init__.py
│   ├── company-people/                # Bidirectional
│   │   ├── ingress.py                 # Company → People
│   │   └── egress.py                  # People → Company
│   ├── company-dol/                   # Bidirectional
│   ├── company-outreach/              # Bidirectional
│   ├── people-outreach/               # Bidirectional
│   └── signal-company/                # Ingress only
│       └── ingress.py
│
├── contracts/                         # SPOKE CONTRACTS (YAML)
│   ├── company-people.contract.yaml
│   ├── company-dol.contract.yaml
│   ├── company-outreach.contract.yaml
│   ├── people-outreach.contract.yaml
│   └── signal-company.contract.yaml
│
├── docs/                              # DOCUMENTATION
│   ├── OSAM.md                        # Query routing map
│   ├── adr/                           # Architecture Decision Records
│   ├── prd/                           # Product Requirements
│   ├── diagrams/                      # ERDs and flow diagrams
│   ├── architecture/
│   ├── audits/                        # Audit reports and summaries
│   ├── checklists/                    # Operational checklists
│   ├── data/                          # Data dictionary and inventories
│   ├── doctrine/                      # Doctrine-related docs
│   ├── schema/                        # Schema reference (YAML)
│   └── schema_csv/                    # Schema exports (CSV)
│
├── doctrine/                          # DOCTRINE REFERENCE
│   ├── delegations/
│   ├── diagrams/
│   ├── ple/                           # Proof Line / Authorization bands
│   └── schemas/
│
├── migrations/                        # DATABASE MIGRATIONS (SQL)
│
├── ops/                               # OPERATIONS
│   ├── enforcement/                   # Runtime doctrine enforcement
│   ├── guards/                        # Guard modules
│   ├── master_error_log/
│   ├── metrics/                       # Metric collection
│   ├── phase_registry/
│   ├── processes/                     # Process orchestration
│   ├── providers/
│   ├── schedulers/                    # Batch scheduling (BIT, etc.)
│   ├── schema-drift/                  # Schema drift detection
│   └── validation/
│
├── src/                               # SOURCE CODE
│   ├── sys/
│   │   ├── heir/                      # HEIR identity system
│   │   ├── db/                        # Database utilities
│   │   ├── logger/                    # Logging
│   │   └── wheel/                     # Shared wheel utilities
│   └── data/
│       ├── hub/                       # Codegen hub output
│       └── spokes/                    # Codegen spoke output
│
├── scripts/                           # OPERATIONAL SCRIPTS
│   ├── install-hooks.sh               # Git hook installer
│   ├── detect-staleness.sh            # Governance artifact freshness
│   ├── codegen-generate.sh            # Registry → generated files
│   ├── codegen-verify.sh              # Verify codegen sync
│   ├── validate-schema-completeness.sh # DBA Gate B validation
│   ├── generate-data-dictionary.sh    # Data dictionary generator
│   ├── update_from_imo_creator.sh     # Template sync from parent
│   ├── ci/                            # CI/CD scripts
│   ├── completeness/                  # Completeness checks
│   └── ingest/                        # Data ingestion scripts
│
├── templates/                         # IMO-CREATOR TEMPLATES (inherited)
│   ├── adr/
│   ├── checklists/
│   ├── child/                         # Child repo templates
│   ├── claude/                        # AI prompt templates
│   ├── config/
│   ├── doctrine/
│   ├── scripts/                       # Script templates (hooks, etc.)
│   ├── semantic/                      # OSAM template
│   ├── pr/
│   └── prd/
│
├── tests/                             # TESTS
│   ├── hubs/
│   ├── spokes/
│   └── ops/
│
├── archive/                           # ARCHIVED files (reports, one-off scripts, stale exports)
│
├── CLAUDE.md                          # AI bootstrap guide (this file)
├── CC_OPERATIONAL_DIGEST.md           # Operational digest for AI sessions
├── STARTUP_PROTOCOL.md                # Session startup checklist
├── CONSTITUTION.md                    # Constitutional governance
├── DOCTRINE.md                        # Doctrine v2.8.0
├── DOCTRINE_CHECKPOINT.yaml           # Session checkpoint (fill before coding)
├── REGISTRY.yaml                      # Hub identity declaration
├── column_registry.yml                # Schema column registry
├── IMO_CONTROL.json                   # IMO control configuration
├── heir.doctrine.yaml                 # HEIR identity config
├── doppler.yaml                       # Doppler secrets config
├── README.md
├── LICENSE
├── package.json
├── requirements.txt
└── .env.example
```

---

## PIPELINE PHASES

### Phase Ownership

| Phase | Owner Hub | Description |
|-------|-----------|-------------|
| Phase 1 | Company Intelligence | Company Matching |
| Phase 1b | Company Intelligence | Unmatched Hold Export |
| Phase 2 | Company Intelligence | Domain Resolution |
| Phase 3 | Company Intelligence | Email Pattern Waterfall |
| Phase 4 | Company Intelligence | Pattern Verification |
| Phase 5 | People Intelligence | Email Generation |
| Phase 6 | People Intelligence | Slot Assignment |
| Phase 7 | People Intelligence | Enrichment Queue |
| Phase 8 | People Intelligence | Output Writer |

### Execution Order

```
Company Identity Pipeline (Phases 1-4) → ALWAYS FIRST
         ↓
People Pipeline (Phases 5-8) → Only after company anchor exists
         ↓
BIT Scoring → Only after people are slotted
```

---

## DATABASE ARCHITECTURE

### Neon PostgreSQL Connection

```
Host: ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech
Port: 5432
Database: Marketing DB
SSL Mode: require
```

### Key Tables

| Schema | Table | Purpose |
|--------|-------|---------|
| outreach | outreach | Operational spine (outreach_id PK) |
| outreach | company_target | Authoritative company list |
| outreach | dol | DOL sub-hub (EIN, filing, renewal) |
| outreach | blog | Blog/content sub-hub |
| people | company_slot | Executive position tracking (CEO/CFO/HR) |
| people | people_master | Contact/executive data |
| vendor | ct | Tier-1 company staging (Hunter, Clay, CSV) |
| vendor | people | Tier-1 people staging (Hunter contacts, scrapers) |
| vendor | blog | Tier-1 URL staging (sitemaps, source URLs) |
| cl | company_identity | Authority registry (identity pointers) |
| dol | form_5500 | DOL annual filings (large plans) |
| dol | ein_urls | EIN-to-domain mapping |

---

## QUICK REFERENCE

### Import Paths

```python
# Company Target Sub-Hub (child of CL)
from hubs.company_target import CompanyHub, BITEngine, CompanyPipeline
from hubs.company_target.imo.middle.phases import Phase1CompanyMatching

# People Intelligence Hub
from hubs.people_intelligence import PeopleHub, SlotAssignment
from hubs.people_intelligence.imo.middle.phases import Phase5EmailGeneration

# DOL Filings Hub
from hubs.dol_filings import DOLHub, EINMatcher

# Spokes (I/O only)
from spokes.target_people import SlotRequirementsIngress, SlotAssignmentsEgress
```

### Contract Files

```yaml
# View spoke contracts
contracts/company-people.contract.yaml
contracts/company-dol.contract.yaml
contracts/company-outreach.contract.yaml
contracts/people-outreach.contract.yaml
contracts/signal-company.contract.yaml
```

### Hub Manifests

```yaml
# View hub definitions
hubs/company-target/hub.manifest.yaml
hubs/people-intelligence/hub.manifest.yaml
hubs/dol-filings/hub.manifest.yaml
hubs/blog-content/hub.manifest.yaml
hubs/outreach-execution/hub.manifest.yaml
hubs/coverage/hub.manifest.yaml
```

---

## NEVER DO THESE THINGS

- **NEVER** mint sovereign_company_id (CL owns this)
- **NEVER** mint sales_process_id or client_id (those hubs own them)
- **NEVER** write workflow state to CL (CL = identity pointers only)
- **NEVER** write outreach_id to CL more than ONCE
- **NEVER** bypass the CL write guard (affected_rows check)
- **NEVER** put logic in spokes (spokes are I/O only)
- **NEVER** store state in spokes
- **NEVER** make sideways hub-to-hub calls
- **NEVER** process records without valid outreach_id
- **NEVER** skip the BIT_SCORE metric for company selection
- **NEVER** mix slot requirements with slot assignments
- **NEVER** bypass RLS in Neon
- **NEVER** hardcode database credentials
- **NEVER** invoke Sales or Client logic directly (handoff via webhook)

---

## COMMON TASKS

### Run Coverage (Scout, Report, Export, Activate)

```bash
# THE repeatable process for working a market.
# Give it a ZIP + radius → get back what you have and what you need.

# List all active markets
doppler run -- python hubs/coverage/imo/middle/run_coverage.py --list

# Scout a new market (creates coverage_id + shows report)
doppler run -- python hubs/coverage/imo/middle/run_coverage.py \
    --anchor-zip 26739 --radius-miles 100

# Scout + export CSV (outreach_id join key + sub-hub status + LinkedIn)
doppler run -- python hubs/coverage/imo/middle/run_coverage.py \
    --anchor-zip 26739 --radius-miles 100 --export

# Check an existing market by coverage_id
doppler run -- python hubs/coverage/imo/middle/run_coverage.py \
    --coverage-id 126b7fc9-4a2c-49bd-97ef-4c769312a576

# Activate — push gaps to enrichment work queues (conscious opt-in)
doppler run -- python hubs/coverage/imo/middle/run_coverage.py \
    --coverage-id 126b7fc9-4a2c-49bd-97ef-4c769312a576 --activate

# Retire a market
doppler run -- python hubs/coverage/imo/middle/run_coverage.py \
    --coverage-id 126b7fc9-4a2c-49bd-97ef-4c769312a576 --retire
```

**What it does:**
1. **Scout** — Picks a market (ZIP + radius), gets or reuses a `coverage_id`
2. **Report** — Shows CT companies, DOL linked %, people slots filled %, blog coverage
3. **Export** — CSV with `outreach_id` (join key), company info, sub-hub filled/LinkedIn status
4. **Activate** — Routes gaps to `people.people_errors`, `outreach.blog_errors`, `outreach.dol_errors` (opt-in only)

**CSV columns:** `outreach_id`, `company_name`, `domain`, `city`, `state`, `zip`, `company_linkedin`, `has_dol`, `has_blog`, `ceo_filled`, `ceo_linkedin`, `cfo_filled`, `cfo_linkedin`, `hr_filled`, `hr_linkedin`

**Export path:** `exports/coverage_{zip}_{radius}mi.csv`

**Key files:**
- `hubs/coverage/imo/middle/run_coverage.py` — Single entry point (orchestrator)
- `hubs/coverage/imo/middle/coverage_report.py` — Report logic
- `hubs/coverage/imo/middle/route_gaps.py` — Gap routing logic
- `hubs/coverage/imo/middle/create_service_agent_coverage.py` — Low-level coverage creation

**Active markets (2026-02-09):**
| Market | ZIP | Radius | Coverage ID |
|--------|-----|--------|-------------|
| Mount Storm, WV | 26739 | 100mi | `126b7fc9-4a2c-49bd-97ef-4c769312a576` |
| New York, NY | 10001 | 25mi | (check --list) |
| Pittsburgh, PA | 15201 | 50mi | (check --list) |
| Dallas, TX | 75201 | 50mi | (check --list) |

---

### Run CEO Email Pipeline (Phases 5-8)

```bash
# Process executive CSV with email generation + Neon promotion
# Slot types: CEO, CFO, HR, CTO, CMO, COO

# Basic usage (with email verification)
doppler run -- python hubs/people-intelligence/imo/middle/phases/ceo_email_pipeline.py <csv_path>

# Skip verification (bulk processing)
doppler run -- python hubs/people-intelligence/imo/middle/phases/ceo_email_pipeline.py <csv_path> --skip-verification

# Specify slot type
doppler run -- python hubs/people-intelligence/imo/middle/phases/ceo_email_pipeline.py <csv_path> --slot-type HR --skip-verification
```

### Fill Slots from Hunter CSV

```bash
# Fill people.company_slot with contacts from Hunter-enriched CSVs
# Matches contacts to slots via outreach_id, creates people_master records
# Adds phone numbers to slot_phone column

# Basic usage
doppler run -- python hubs/people-intelligence/imo/middle/phases/fill_slots_from_hunter.py <csv_path>

# Dry run (preview without changes)
doppler run -- python hubs/people-intelligence/imo/middle/phases/fill_slots_from_hunter.py <csv_path> --dry-run
```

**CSV Requirements:**
- Must have `outreach_id` column to match slots
- Supports Hunter format columns: `Email address`, `First name`, `Last name`, `Job title`, `Phone number`, `LinkedIn URL`
- Also supports slot_contacts format with `slot_type` column pre-assigned

**What it does:**
1. Reads Hunter CSV and detects slot type from job title (CEO/CFO/HR keywords)
2. Looks up matching slot in `people.company_slot` by outreach_id + slot_type
3. Creates new `people.people_master` record with Barton ID format (`04.04.02.YY.NNNNNN.NNN`)
4. Links person to slot and marks `is_filled = TRUE`
5. Adds phone number to `slot_phone` column if present

### Blog URL Data (Historical)

URL discovery and leadership scraping scripts were archived in Phase 3 Legacy Collapse (2026-02-20).
All historical URL data is preserved in `vendor.blog` (289,624 rows).
See `archive/blog-content-superseded/README.md` for the full archive manifest.

### Run Pipeline for Company

```python
from hubs.company_target import CompanyPipeline

pipeline = CompanyPipeline(persist_to_neon=True)
pipeline.bootstrap()
result = pipeline.run()
```

### Check BIT Score

```python
from hubs.company_target import BITEngine, SignalType

engine = BITEngine()
score = engine.calculate_bit_score(company_id)
```

### Assign Person to Slot

```python
from hubs.people_intelligence import SlotAssignment

assignment = SlotAssignment()
result = assignment.assign(company_id, slot_type, person_id)
```

### Send via Spoke

```python
from spokes.company_people import SlotRequirementsIngress, SlotRequirementPayload

spoke = SlotRequirementsIngress(people_hub_input)
payload = SlotRequirementPayload(company_id="...", slot_type="CEO")
spoke.route(payload)  # Pass-through only, no transformation
```

---

## ENVIRONMENT VARIABLES

```bash
# Neon Database
NEON_HOST=ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech
NEON_DATABASE=Marketing DB
NEON_USER=Marketing DB_owner
NEON_PASSWORD=<YOUR_PASSWORD>

# Barton Doctrine
DOCTRINE_SUBHIVE=04
DOCTRINE_APP=outreach
DOCTRINE_LAYER=04
DOCTRINE_SCHEMA=02
DOCTRINE_VERSION=04
```

---

## KEY DOCUMENTATION

| Document | Location | Purpose |
|----------|----------|---------|
| OSAM | `docs/OSAM.md` | Query routing map |
| Hub Manifests | `hubs/*/hub.manifest.yaml` | Hub definitions |
| Spoke Contracts | `contracts/*.contract.yaml` | Spoke I/O contracts |
| Architecture | `docs/architecture/` | Design docs |
| ADRs | `docs/adr/` | Decision records |
| BIT Architecture | `docs/adr/ADR-014_BIT_Engine_Architecture.md` | Buyer intent scoring |
| HEIR Doctrine | `heir.doctrine.yaml` | Hub identity config |
| Column Registry | `column_registry.yml` | Schema column metadata |

---

## HEIR + BIT SYSTEMS

### HEIR (Hub Environment Identity Record)

Every operation MUST have a `unique_id` for traceability.

```python
from src.sys.heir import generate_unique_id, track_operation

# Generate unique_id
unique_id = generate_unique_id()
# Output: outreach-core-001-20260207143022-a1b2c3d4

# Track operation with HEIR + ORBT
with track_operation("my_pipeline") as ctx:
    do_work(unique_id=ctx.unique_id, process_id=ctx.process_id)
```

**Key Files:**
- `src/sys/heir/heir_identity.py` - HEIR ID generation
- `src/sys/heir/orbt_process.py` - ORBT process lifecycle
- `src/sys/heir/tracking.py` - Unified tracker

### BIT (Buyer Intent Tracker)

Aggregates signals from all hubs to compute intent scores.

| Tier | Score | Outreach Action |
|------|-------|-----------------|
| COLD | 0-24 | NO outreach |
| WARM | 25-49 | Standard cadence |
| HOT | 50-74 | Accelerated cadence |
| BURNING | 75+ | Priority outreach |

**Signal Sources:**
- People: SLOT_FILLED (+10), EMAIL_VERIFIED (+3)
- DOL: FORM_5500_FILED (+5), BROKER_CHANGE (+7)
- Blog: FUNDING_EVENT (+15), ACQUISITION (+12)
- Talent Flow: EXECUTIVE_JOINED (+10), EXECUTIVE_LEFT (-5)

**Key Files:**
- `hubs/company-target/imo/middle/bit_engine.py` - BIT Engine
- `doctrine/schemas/bit-schema.sql` - Database schema
- `ops/schedulers/bit_batch_score.py` - Batch scoring

---

## REMEMBER

1. **CL is PARENT** - Mints company_unique_id, Outreach receives only
2. **Company Target is internal anchor** - FK join point for all sub-hubs
3. **Spokes are DUMB** - I/O only, no logic, no state
4. **Contracts define interfaces** - Check YAML before implementing
5. **BIT_SCORE drives outreach** - No score, no campaign

---

**Last Updated**: 2026-02-15
**Architecture**: CL Parent-Child Doctrine v1.1 + CTB Registry v1.0
**Status**: v1.0 OPERATIONAL BASELINE (CERTIFIED + FROZEN)
**CL Total**: 102,922 | **Outreach Spine**: 95,837 | **Three Lanes**: Cold (95,837) + Appointments (771) + CFO Partners (833)
**Verified By**: Full numbers audit (2026-02-09)

---

## ENFORCEMENT MODULES

Runtime doctrine enforcement is implemented in `ops/enforcement/`:

| Module | Purpose |
|--------|---------|
| `correlation_id.py` | UUID propagation, FAIL HARD if missing |
| `hub_gate.py` | Golden Rule validation (company_id + domain + email_pattern) |
| `signal_dedup.py` | 24h/365d deduplication windows |
| `error_codes.py` | 33+ error codes with severity/recoverability |
| `authority_gate.py` | CC layer authority validation |

---

## DATABASE HARDENING (2026-01-13)

| Migration | Purpose |
|-----------|---------|
| `2026-01-13-dol-schema-creation.sql` | DOL Hub tables (form_5500, schedule_a, renewal_calendar) |
| `2026-01-13-outreach-execution-complete.sql` | Outreach execution (campaigns, sequences, send_log — **all 3 tables dropped 2026-02-20, were empty**) |
| `2026-01-13-enable-rls-production-tables.sql` | RLS on all production tables |

See `migrations/MIGRATION_ORDER.md` for execution order.

---

## SOVEREIGN CLEANUP (2026-01-21)

| Migration | Purpose |
|-----------|---------|
| `2026-01-21-sovereign-cleanup-cascade.sql` | Cascade cleanup after CL sovereign cleanup |

**Cleanup Results**:
- 23,025 orphaned outreach_ids archived
- Archive tables created for all affected entities

---

## COMMERCIAL ELIGIBILITY CLEANUP (2026-01-29)

**Trigger**: CL excluded 5,327 non-commercial entities (government, education, healthcare, religious, insurance, financial services) to `cl.company_identity_excluded`

**Cleanup Results**:
- 5,259 excluded company outreach_ids cleared
- 4,577 phantom outreach_ids cleared from CL
- 756 fixable orphans registered in CL
- 2,709 unfixable orphans archived and deleted
- 10,846 total cascade deletions across sub-hubs

**Archive Tables Created/Updated**:
- `outreach.outreach_archive` (27,416 records)
- `outreach.company_target_archive`
- `outreach.dol_archive`
- `outreach.blog_archive`
- `outreach.bit_scores_archive`
- `cl.company_identity_archive` (22,263 records)
- `people.company_slot_archive`

**Current State (2026-02-09 VERIFIED)**:
| Sub-Hub | Table | Records | Notes |
|---------|-------|---------|-------|
| **Sovereign** | cl.company_identity | 102,922 total | 95,004 eligible + 6,499 excluded + 1,419 new lanes |
| Spine | outreach.outreach | 95,837 | 95,004 cold + 833 fractional CFO |
| CT | outreach.company_target | 95,837 | Includes fractional CFO companies |
| DOL | outreach.dol | 70,150 | 73.8% coverage |
| People | people.people_master | 182,946 | Enriched contacts |
| People | people.company_slot | 285,012 | 62.4% fill rate (177,757 filled) |
| Blog | outreach.blog | 95,004 | 100% coverage (original eligible) |
| CLS | outreach.bit_scores | 13,226 | 13.9% coverage |
| **Lane: Appointments** | sales.appointments_already_had | 771 | Reactivation lane |
| **Lane: Fractional CFO** | partners.fractional_cfo_master | 833 | Partner lane |
| **Lane: Appointments** | outreach.appointments | 704 | Appointment tracking |

---

## BIT AUTHORIZATION SYSTEM (v2.0)

**Authority:** ADR-017
**Status:** ACTIVE (Phase 1)
**Effective:** 2026-01-25

### Core Doctrine

```
All intelligence hubs emit movement events, not facts.
BIT is a movement-derived authorization index.
Its value determines which response classes are PERMITTED.
It does not rank companies or predict intent.
Outreach is interception of detected phases, not persuasion of static targets.
```

### The Three Domains

| Domain | Hub | Velocity | Trust | Role |
|--------|-----|----------|-------|------|
| STRUCTURAL_PRESSURE | DOL | Slow (annual) | Highest | Gravity — required for authority |
| DECISION_SURFACE | People | Medium (quarterly) | High | Direction — who can act |
| NARRATIVE_VOLATILITY | Blog | Fast (weekly) | Lowest | Timing — amplifier only |

**Convergence Rule:**
- One domain moving = noise
- Two domains moving = watch
- Three domains aligned = act
- **Blog alone NEVER justifies outreach (max Band 1)**
- **DOL absence caps authority at Band 2**

### Authorization Bands

| Band | Range | Name | Permitted Actions | Proof Required |
|------|-------|------|-------------------|----------------|
| 0 | 0–9 | SILENT | None. No outreach. No queue. | No |
| 1 | 10–24 | WATCH | Internal flag only. No external contact. | No |
| 2 | 25–39 | EXPLORATORY | 1 educational message per 60 days. No personalization. | No |
| 3 | 40–59 | TARGETED | Persona-specific email. 3-touch max. | Single-source |
| 4 | 60–79 | ENGAGED | Phone (warm). 5-touch max. | Multi-source |
| 5 | 80+ | DIRECT | Direct contact. Meeting request. | Full-chain |

### Proof Line Rule

**Definition:** A proof line is a mandatory citation of detected pressure that authorizes a message. It is NOT a talking point. It is the legal basis for contact.

**When Required:**
- Band 0–2: Not required
- Band 3+: **MANDATORY**

**Proof Line Formats:**

```
Band 3: [PRESSURE_CLASS] detected via [SOURCE]: [SPECIFIC_EVIDENCE]
Example: COST_PRESSURE detected via DOL: employer contribution +18% YoY, renewal in 75 days

Band 4: [PRESSURE_CLASS] convergence: [DOL_EVIDENCE] + [PEOPLE_EVIDENCE] + [BLOG_EVIDENCE if present]

Band 5: PHASE TRANSITION: [PRESSURE_CLASS] — [DOL] + [PEOPLE] + [BLOG] — Decision window: [X] days
```

### Pressure Classes

| Class | Primary Source | What's Broken |
|-------|----------------|---------------|
| COST_PRESSURE | DOL | No cost visibility, silent drift, blind decisions |
| VENDOR_DISSATISFACTION | DOL + People | Broker churn, manual processes, reset knowledge |
| DEADLINE_PROXIMITY | DOL | Renewal as event not process, compressed decisions |
| ORGANIZATIONAL_RECONFIGURATION | People | Knowledge loss, no continuity layer |
| OPERATIONAL_CHAOS | DOL | Filing irregularities, compliance gaps |

### Code Enforcement Pattern

```python
# REQUIRED: Check band before any outreach action
band = bit.get_current_band(company_id)

if band < required_band:
    raise UnauthorizedOutreachError(f"Band {band} insufficient for action")

# REQUIRED: Proof line at Band 3+
if band >= 3:
    proof = bit.get_valid_proof(company_id, band)
    if not proof:
        raise MissingProofLineError("Band 3+ requires proof line")
    if not bit.validate_proof_for_send(proof.proof_id, band):
        raise InvalidProofError("Proof invalid or expired")

# ONLY THEN: Proceed with outreach
message = generate_message(company_id, proof)
```

### Message Framing Rule

Lead with **system failure**, not product.

**WRONG:**
```
"We offer better benefits plans..."
"Our advisory services can help..."
"I'd love to show you our platform..."
```

**RIGHT:**
```
"Your employer contribution rose 18% last year while headcount stayed flat —
that's a cost visibility gap we can close."

"You've changed brokers twice in three years. That pattern usually means
the underlying data infrastructure isn't transferring. We fix that layer."

"Your new CHRO inherited a renewal in 75 days with no decision history.
We build the continuity system that prevents this."
```

### NEVER DO (BIT Authorization)

1. **NEVER** create outreach without checking BIT band first
2. **NEVER** fabricate or backfill proof lines
3. **NEVER** use Blog signals alone to justify contact
4. **NEVER** escalate band without new movement evidence
5. **NEVER** send messages with expired proof lines
6. **NEVER** copy proof lines between companies
7. **NEVER** use urgency language below Band 5
8. **NEVER** mention pricing without discovery (any band)
9. **NEVER** frame insurance as the product — frame system failure as the problem

### Schema References

```sql
-- Authorization check
SELECT bit.authorize_action(company_id, 'send_email');

-- Proof validation
SELECT bit.validate_proof_for_send(proof_id, requested_band);

-- Current band
SELECT bit.get_current_band(company_id);

-- NOTE: bit.movement_events, bit.proof_lines, bit.phase_state, bit.authorization_log
-- were dropped 2026-02-20 (all empty, deprecated by distributed signal tables per ADR-017)
```

### Related Documentation

| Document | Location |
|----------|----------|
| ADR-017 | `docs/adr/ADR-017_BIT_Authorization_System_Migration.md` |
| Band Definitions | `doctrine/ple/BIT_AUTHORIZATION_BANDS.md` |
| Proof Line Rule | `doctrine/ple/PROOF_LINE_RULE.md` |
| Inline Context | `doctrine/BIT_AUTHORIZATION_INLINE.md` |

---

**Last Updated**: 2026-02-15
**Architecture**: CL Parent-Child Doctrine v1.1 + BIT Authorization v2.0 + CTB Registry v1.0
**Status**: v1.0 OPERATIONAL BASELINE + BIT v2.0 Phase 1 + CTB Phase 3 LOCKED
**Verified By**: Full numbers audit (2026-02-09)

---

## CTB REGISTRY (2026-02-06)

**Status**: PHASE 3 COMPLETE - ENFORCEMENT LOCKED
**Tags**: CTB_PHASE1_LOCK, CTB_PHASE2_COLUMN_HYGIENE, CTB_PHASE3_ENFORCEMENT_LOCK

### What is CTB?

CTB (Christmas Tree Backbone) is the hierarchical data model with ID-based paths organizing all 249 tables in the database. Every table is classified by leaf type and registered in the central registry.

### CTB Schema

```sql
-- Central Registry
ctb.table_registry   -- 249 tables registered with leaf types
ctb.violation_log    -- Guardrail violation tracking (0 violations)
```

### Leaf Type Distribution

| Leaf Type | Count | Description |
|-----------|-------|-------------|
| ARCHIVE | 119 | Archive/history tables |
| SYSTEM | 36 | System/metadata/audit tables |
| CANONICAL | 26 | Primary data tables |
| DEPRECATED | 24 | Legacy tables (read-only) |
| STAGING | 13 | Intake/staging tables |
| ERROR | 11 | Error tracking tables |
| MV | 8 | Materialized view candidates |
| REGISTRY | 7 | Lookup/reference tables |
| SUPPORTING | 5 | Operational data serving a CANONICAL table (ADR required) |
| **TOTAL** | **249** | |

### Frozen Core Tables (9)

These tables are marked immutable in the CTB registry:

| Schema | Table |
|--------|-------|
| cl | company_identity |
| outreach | outreach |
| outreach | company_target |
| outreach | dol |
| outreach | blog |
| outreach | people |
| outreach | bit_scores |
| people | people_master |
| people | company_slot |

### CTB Column Contracts

Error tables have NOT NULL constraints on `error_type` discriminator:
- `outreach.dol_errors.error_type` NOT NULL
- `outreach.blog_errors.error_type` NOT NULL
- `cl.cl_errors_archive.error_type` NOT NULL
- `people.people_errors.error_type` NOT NULL

### CTB Phase Summary

| Phase | Tag | Scope |
|-------|-----|-------|
| Phase 1 | CTB_PHASE1_LOCK | Identity audit, orphan cleanup |
| Phase 2 | CTB_PHASE2_COLUMN_HYGIENE | Column hygiene, error normalization |
| Phase 3 | CTB_PHASE3_ENFORCEMENT_LOCK | Registry creation, guardrails, freeze |

### CTB Documentation

| Document | Purpose |
|----------|---------|
| `migrations/ctb_phase3_enforcement.sql` | Enforcement DDL |

### Query CTB Registry

```sql
-- View all tables by leaf type
SELECT table_schema, table_name, leaf_type, is_frozen
FROM ctb.table_registry
ORDER BY leaf_type, table_schema, table_name;

-- View frozen core tables
SELECT table_schema, table_name
FROM ctb.table_registry
WHERE is_frozen = TRUE;

-- Check violations
SELECT * FROM ctb.violation_log;
```

---

## EXCLUSION CONSOLIDATION (2026-01-30)

**Purpose**: Consolidated all non-commercial/invalid records into single exclusion table

**Exclusion Breakdown (2,432 total)**:
| Category | Count | % |
|----------|-------|---|
| CL_NOT_PASS (PENDING) | 723 | 29.7% |
| TLD: .org | 675 | 27.8% |
| Keyword match (church, school, hospital) | 380 | 15.6% |
| NOT_IN_CL (invalid sovereign_id) | 497 | 20.4% |
| TLD: .edu | 84 | 3.5% |
| TLD: .coop | 40 | 1.6% |
| Other TLDs (.gov, .church) | 31 | 1.3% |
| CL_FAIL | 2 | 0.1% |

**Exclusion Table**: `outreach.outreach_excluded`
- All non-commercial entities
- All CL non-PASS records
- All invalid sovereign_ids
- Full audit trail preserved

**CL Total**: 102,922 | **Outreach Spine**: 95,837 | **Three Lanes**: Cold (95,837) + Appointments (771) + CFO Partners (833)

**Q1 2026 Audit Status**: COMPLIANT (0 CRITICAL, 0 HIGH violations)

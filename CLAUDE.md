# Claude Bootstrap Guide - Barton Outreach Core

## INSTANT REPO OVERVIEW

**Repository Name**: Barton Outreach Core
**Architecture**: CL Parent-Child Doctrine
**Primary Purpose**: Marketing intelligence & executive enrichment platform
**Database**: Neon PostgreSQL (serverless)
**Last Refactored**: 2025-12-26

---

## v1.0 OPERATIONAL BASELINE

**Status**: CERTIFIED AND FROZEN
**Certification Date**: 2026-01-19
**Baseline Freeze Date**: 2026-01-20
**Sovereign Cleanup**: 2026-01-21 (23,025 records archived)
**CL-Outreach Alignment**: 51,148 = 51,148 ✓
**Safe to Enable Live Marketing**: YES

### Key Documentation

| Document | Purpose |
|----------|---------|
| `docs/DATA_REGISTRY.md` | **WHERE DATA LIVES** - Check FIRST before searching |
| `docs/GO-LIVE_STATE_v1.0.md` | What is live vs intentionally incomplete |
| `doctrine/DO_NOT_MODIFY_REGISTRY.md` | Frozen components requiring change request |
| `docs/reports/FINAL_CERTIFICATION_REPORT_2026-01-19.md` | Certification audit results |

### Deferred Work Orders

| Work Order | Status | Description |
|------------|--------|-------------|
| WO-DOL-001 | DEFERRED | DOL enrichment pipeline (EIN resolution) |

### DO NOT MODIFY (v1.0 Frozen)

The following components are **FROZEN** and require formal change request:
- `outreach.vw_marketing_eligibility_with_overrides` (authoritative view)
- `outreach.vw_sovereign_completion` (sovereign view)
- Tier computation logic and assignment rules
- Kill switch system (manual_overrides, override_audit_log)
- Marketing safety gate (HARD_FAIL enforcement)
- Hub registry and waterfall order

See `doctrine/DO_NOT_MODIFY_REGISTRY.md` for complete list.

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
Current: 51,148 = 51,148 ✓ ALIGNED
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
| Data flows FORWARD ONLY | Bound by outreach_context_id |
| Sub-hubs may re-run if upstream unchanged | Idempotent design |

### Hub Registry (Waterfall Order)

| Order | Hub | Doctrine ID | Core Metric | Entities Owned |
|-------|-----|-------------|-------------|----------------|
| 1 | **Company Lifecycle (CL)** | PARENT | LIFECYCLE_STATE | cl.company_identity, cl.lifecycle_state |
| 2 | **Company Target** | 04.04.01 | BIT_SCORE | outreach.company_target, verified_pattern |
| 3 | **DOL Filings** | 04.04.03 | FILING_MATCH_RATE | form_5500, schedule_a, ein_registry |
| 4 | **People Intelligence** | 04.04.02 | SLOT_FILL_RATE | outreach.people, slot_assignments |
| 5 | **Blog Content** | 04.04.05 | CONTENT_SIGNAL_RATE | blog_signals, news_events |

**Note**: People Intelligence (04.04.02) executes AFTER DOL Filings (04.04.03) in the waterfall.

### Spoke Contracts

| Contract | Direction | Trigger |
|----------|-----------|---------|
| target-people | Bidirectional | slot_requirement / slot_assignment |
| target-dol | Bidirectional | ein_lookup / filing_signal |
| target-outreach | Bidirectional | target_selection / engagement_signal |
| people-outreach | Bidirectional | contact_selection / contact_state |
| cl-identity | Ingress Only | company_unique_id from CL |

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
│   │       │   ├── email/             # Pattern discovery
│   │       │   └── utils/
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
│   └── outreach-execution/            # Sub-hub (04.04.04)
│       ├── hub.manifest.yaml
│       └── imo/
│           └── middle/
│               └── outreach_hub.py
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
│   ├── schema_map.json                # Neon schema reference
│   ├── adr/                           # Architecture Decision Records
│   ├── prd/                           # Product Requirements
│   └── architecture/
│
├── doctrine/                          # DOCTRINE REFERENCE
│   ├── diagrams/
│   ├── ple/
│   └── schemas/
│
├── global-config/                     # IMO-RA TEMPLATES
│   └── scripts/
│
├── infra/                             # INFRASTRUCTURE
│   ├── docs/
│   ├── migrations/
│   └── scripts/
│
├── neon/                              # DATABASE MIGRATIONS
│   └── migrations/
│
├── ops/                               # OPERATIONS
│   ├── enforcement/
│   ├── master_error_log/
│   ├── phase_registry/
│   ├── providers/
│   └── validation/
│
├── shared/                            # SHARED UTILITIES
│   ├── logger/
│   └── wheel/
│
├── templates/                         # TEMPLATES
│   ├── adr/
│   ├── checklists/
│   ├── pr/
│   └── prd/
│
├── tests/                             # TESTS
│   ├── hubs/
│   ├── spokes/
│   └── ops/
│
├── integrations/                      # EXTERNAL INTEGRATIONS
├── tooling/                           # TOOLING
│
├── CLAUDE.md                          # This file
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
| marketing | company_master | Master company records |
| marketing | company_slot | Executive position tracking |
| marketing | people_master | Contact/executive data |
| marketing | data_enrichment_log | Enrichment job tracking |
| intake | company_raw_intake | CSV staging |
| public | shq_error_log | System error tracking |
| bit | events | Buyer intent signals |

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

# Outreach Execution Hub
from hubs.outreach_execution import OutreachHub

# Spokes (I/O only)
from spokes.target_people import SlotRequirementsIngress, SlotAssignmentsEgress
```

### Contract Files

```yaml
# View spoke contracts
contracts/target-people.contract.yaml
contracts/target-dol.contract.yaml
contracts/target-outreach.contract.yaml
contracts/people-outreach.contract.yaml
contracts/cl-identity.contract.yaml
```

### Hub Manifests

```yaml
# View hub definitions
hubs/company-target/hub.manifest.yaml
hubs/people-intelligence/hub.manifest.yaml
hubs/dol-filings/hub.manifest.yaml
hubs/outreach-execution/hub.manifest.yaml
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
| Hub Manifests | `hubs/*/hub.manifest.yaml` | Hub definitions |
| Spoke Contracts | `contracts/*.contract.yaml` | Spoke I/O contracts |
| Schema Reference | `docs/schema_map.json` | Database schema |
| Architecture | `docs/architecture/` | Design docs |
| ADRs | `docs/adr/` | Decision records |

---

## REMEMBER

1. **CL is PARENT** - Mints company_unique_id, Outreach receives only
2. **Company Target is internal anchor** - FK join point for all sub-hubs
3. **Spokes are DUMB** - I/O only, no logic, no state
4. **Contracts define interfaces** - Check YAML before implementing
5. **BIT_SCORE drives outreach** - No score, no campaign

---

**Last Updated**: 2026-01-22
**Architecture**: CL Parent-Child Doctrine v1.1
**Status**: v1.0 OPERATIONAL BASELINE (CERTIFIED + FROZEN)
**CL-Outreach Alignment**: 51,148 = 51,148 ✓

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
| `2026-01-13-outreach-execution-complete.sql` | Outreach execution (campaigns, sequences, send_log) |
| `2026-01-13-enable-rls-production-tables.sql` | RLS on all production tables |

See `infra/MIGRATION_ORDER.md` for execution order.

---

## SOVEREIGN CLEANUP (2026-01-21)

| Migration | Purpose |
|-----------|---------|
| `2026-01-21-sovereign-cleanup-cascade.sql` | Cascade cleanup after CL sovereign cleanup |

**Cleanup Results**:
- 23,025 orphaned outreach_ids archived
- Archive tables created for all affected entities
- CL-Outreach alignment restored: 51,148 = 51,148

**Archive Tables**:
- `outreach.outreach_archive`
- `outreach.company_target_archive`
- `outreach.people_archive`
- `people.company_slot_archive`
- `people.people_master_archive`

**Post-Cleanup State**:
| Sub-Hub | Table | Records | Notes |
|---------|-------|---------|-------|
| Spine | outreach.outreach | 51,148 | ALIGNED WITH CL |
| CT | outreach.company_target | 51,148 | 91.4% with email_method |
| DOL | outreach.dol | 13,829 | 27% coverage |
| People | outreach.people | 426 | |
| People | people.company_slot | 153,444 | CEO: 27.1%, CFO: 8.6%, HR: 13.7% |
| Blog | outreach.blog | 51,148 | 100% coverage |
| BIT | outreach.bit_scores | 17,227 | |

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

-- Movement events
SELECT * FROM bit.movement_events WHERE company_unique_id = ?;

-- Proof lines
SELECT * FROM bit.proof_lines WHERE company_unique_id = ? AND valid_until > NOW();
```

### Related Documentation

| Document | Location |
|----------|----------|
| ADR-017 | `docs/adr/ADR-017_BIT_Authorization_System_Migration.md` |
| Implementation Plan | `docs/implementation/BIT_V2_IMPLEMENTATION_PLAN.md` |
| Band Definitions | `doctrine/ple/BIT_AUTHORIZATION_BANDS.md` |
| Proof Line Rule | `doctrine/ple/PROOF_LINE_RULE.md` |
| Inline Context | `doctrine/BIT_AUTHORIZATION_INLINE.md` |

---

**Last Updated**: 2026-01-25
**Architecture**: CL Parent-Child Doctrine v1.1 + BIT Authorization v2.0
**Status**: v1.0 OPERATIONAL BASELINE + BIT v2.0 Phase 1

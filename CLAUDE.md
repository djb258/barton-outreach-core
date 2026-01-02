# Claude Bootstrap Guide - Barton Outreach Core

## INSTANT REPO OVERVIEW

**Repository Name**: Barton Outreach Core
**Architecture**: CL Parent-Child Doctrine
**Primary Purpose**: Marketing intelligence & executive enrichment platform
**Database**: Neon PostgreSQL (serverless)
**Last Refactored**: 2025-12-26

---

## CORE ARCHITECTURE: CL PARENT-CHILD

### The Golden Rule

```
IF company_unique_id IS NULL:
    STOP. DO NOT PROCEED.
    → Request identity from Company Lifecycle (CL) parent hub first.
```

### Architecture Diagram — External CL + Outreach Program

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SYSTEM (NOT OUTREACH)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  COMPANY LIFECYCLE (CL)                                                      │
│  https://github.com/djb258/company-lifecycle-cl.git                          │
│  • Mints company_unique_id (SOVEREIGN, IMMUTABLE)                            │
│  • Owns cl.* schema (company_identity, lifecycle_state)                      │
│  • Shared across programs (Outreach, Client Intake, Analytics)               │
│  • Outreach does NOT invoke or gate CL                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ company_unique_id (consumed)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      OUTREACH PROGRAM (PROGRAM-SCOPED)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  0. OUTREACH ORCHESTRATION (Context Authority) ─────────────► RUN CREATED   │
│     • Mints outreach_context_id (program-scoped)                             │
│     • Binds outreach_context_id ⇄ company_unique_id                          │
│     • Establishes execution + audit boundary                                 │
│     • Performs NO enrichment, discovery, or scoring                          │
│     • Table: outreach.outreach_context                                       │
│                                    │                                         │
│                                    │ outreach_context_id                     │
│                                    ▼                                         │
│  1. COMPANY TARGET (04.04.01) ──────────────────────────────► PASS REQUIRED │
│     • Domain resolution                                                      │
│     • Email pattern discovery                                                │
│     • EMITS: verified_pattern, domain                                        │
│                                    │                                         │
│                                    ▼                                         │
│  2. DOL FILINGS (04.04.03) ─────────────────────────────────► PASS REQUIRED │
│     • EIN resolution                                                         │
│     • Form 5500 + Schedule A                                                 │
│     • EMITS: ein, filing_signals                                             │
│                                    │                                         │
│                                    ▼                                         │
│  3. PEOPLE INTELLIGENCE (04.04.02) ─────────────────────────► PASS REQUIRED │
│     • CONSUMER ONLY - Does NOT discover patterns or EINs                     │
│     • CONSUMES: verified_pattern (CT), ein/signals (DOL)                     │
│     • EMITS: slot_assignments, people_records                                │
│                                    │                                         │
│                                    ▼                                         │
│  4. BLOG CONTENT (04.04.05) ────────────────────────────────► PASS          │
│     • Content signals, news monitoring                                       │
│     • CONSUMER ONLY                                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### External Dependencies & Program Scope

| Boundary | System | Ownership |
|----------|--------|-----------|
| **External** | Company Lifecycle (CL) | Mints company_unique_id, shared across all programs |
| **Program** | Outreach Orchestration | Mints outreach_context_id, program-scoped |
| **Sub-Hub** | CT, DOL, People, Blog | Reference outreach_context_id for all operations |

### Key Doctrine (LOCKED)

- **CL is external** — Outreach consumes company_unique_id, does NOT invoke CL
- **Outreach run identity** — All operations bound by outreach_context_id
- **Context table** — outreach.outreach_context is the root audit record
- **No sub-hub writes without valid outreach_context_id**

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

1. **CL is PARENT** - Mints company_unique_id, Outreach receives only
2. **Company Target is internal anchor** - FK join point for sub-hubs
3. **Spokes are I/O ONLY** - No logic, no state, no transformation
4. **No identity minting** - NEVER create company_unique_id
5. **Signal to CL** - Engagement events flow back to parent

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

- **NEVER** put logic in spokes (spokes are I/O only)
- **NEVER** store state in spokes
- **NEVER** make sideways hub-to-hub calls
- **NEVER** process records without company anchor
- **NEVER** skip the BIT_SCORE metric for company selection
- **NEVER** mix slot requirements with slot assignments
- **NEVER** bypass RLS in Neon
- **NEVER** hardcode database credentials

---

## COMMON TASKS

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

**Last Updated**: 2026-01-02
**Architecture**: CL Parent-Child Doctrine v1.0
**Status**: REMEDIATION IN PROGRESS

---

## AUDIT STATUS

> **CERTIFICATION: FAIL** (as of 2025-12-26 audit)
> See `OUTREACH_REPO_REAUDIT_CERTIFICATION.md` for full details.

| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | 12 | P0 - Immediate |
| HIGH | 13 | P1 - Short-term |
| MEDIUM | 5 | P2 - Medium-term |

### Priority Remediation Items

| Priority | Issue | Action Required |
|----------|-------|-----------------|
| P0-1 | DV-016: funnel.* schema empty | Create tables OR remove references |
| P0-2 | DV-003,008,009,025: Broken imports | Fix Python import paths |
| P0-3 | DV-011,012,013: Fuzzy matching | Remove OR move to CL repo |
| P1-1 | DV-002,004-007: AXLE terminology | Replace with "Sub-Hub" |
| P1-2 | DV-017: Missing FK constraint | Add FK to cl.company_identity |
| P1-3 | DV-027-030: CI guard gaps | Fix pattern matching in workflows |

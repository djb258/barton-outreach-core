# Claude Bootstrap Guide - Barton Outreach Core

## INSTANT REPO OVERVIEW

**Repository Name**: Barton Outreach Core
**Architecture**: Hub & Spoke (Bicycle Wheel Doctrine)
**Primary Purpose**: Marketing intelligence & executive enrichment platform
**Database**: Neon PostgreSQL (serverless)
**Last Refactored**: 2025-12-23

---

## CORE ARCHITECTURE: HUB & SPOKE

### The Golden Rule

```
IF company_id IS NULL OR domain IS NULL OR email_pattern IS NULL:
    STOP. DO NOT PROCEED.
    → Route to Company Identity Pipeline first.
```

### Architecture Diagram

```
                         SPOKES (I/O Only - No Logic)
                                    │
    ┌───────────────────────────────┼───────────────────────────────┐
    │                               │                               │
    ▼                               ▼                               ▼
┌─────────┐                   ┌─────────┐                   ┌─────────┐
│ People  │◄─────────────────►│   DOL   │                   │Outreach │
│  Hub    │                   │   Hub   │                   │   Hub   │
│04.04.02 │                   │04.04.03 │                   │04.04.04 │
└────┬────┘                   └────┬────┘                   └────┬────┘
     │                             │                             │
     │         ┌───────────────────┼───────────────────┐         │
     │         │                   │                   │         │
     └─────────┤      COMPANY INTELLIGENCE HUB         ├─────────┘
               │           (AXLE - 04.04.01)           │
               │                                       │
               │  • company_master    • bit_scores     │
               │  • slot_requirements • domain         │
               │  • email_pattern                      │
               └───────────────────────────────────────┘
                                    ▲
                                    │
                            ┌───────┴───────┐
                            │ Signal Intake │
                            │ (Ingress Only)│
                            └───────────────┘
```

### Hub Registry

| Hub | Doctrine ID | Core Metric | Entities Owned |
|-----|-------------|-------------|----------------|
| **Company Intelligence** (AXLE) | 04.04.01 | BIT_SCORE | company_master, slot_requirements, bit_scores, domain, email_pattern |
| **People Intelligence** | 04.04.02 | SLOT_FILL_RATE | people_master, slot_assignments, movement_history, enrichment_state |
| **DOL Filings** | 04.04.03 | FILING_MATCH_RATE | form_5500, form_5500_sf, schedule_a, renewal_calendar |
| **Outreach Execution** | 04.04.04 | ENGAGEMENT_RATE | campaigns, sequences, send_log, engagement_events |

### Spoke Contracts

| Contract | Direction | Trigger |
|----------|-----------|---------|
| company-people | Bidirectional | slot_requirement / slot_assignment |
| company-dol | Bidirectional | ein_lookup / filing_signal |
| company-outreach | Bidirectional | target_selection / engagement_signal |
| people-outreach | Bidirectional | contact_selection / contact_state |
| signal-company | Ingress Only | external_signal |

### Key Doctrine Rules

1. **Company Hub is AXLE** - All data anchors to company_master first
2. **Slots are SPLIT** - Requirements in Company Hub, Assignments in People Hub
3. **Spokes are I/O ONLY** - No logic, no state, no transformation
4. **No sideways hub calls** - All routing through AXLE
5. **Movement Engine in People Hub** - Tracks people, not companies

---

## REPOSITORY STRUCTURE

```
barton-outreach-core/
│
├── hubs/                              # HUB LOGIC (IMO Pattern)
│   ├── __init__.py                    # Hub registry
│   ├── company-intelligence/          # AXLE (04.04.01)
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
# Company Intelligence Hub
from hubs.company_intelligence import CompanyHub, BITEngine, CompanyPipeline
from hubs.company_intelligence.imo.middle.phases import Phase1CompanyMatching

# People Intelligence Hub
from hubs.people_intelligence import PeopleHub, SlotAssignment
from hubs.people_intelligence.imo.middle.phases import Phase5EmailGeneration

# DOL Filings Hub
from hubs.dol_filings import DOLHub, EINMatcher

# Outreach Execution Hub
from hubs.outreach_execution import OutreachHub

# Spokes (I/O only)
from spokes.company_people import SlotRequirementsIngress, SlotAssignmentsEgress
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
hubs/company-intelligence/hub.manifest.yaml
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
from hubs.company_intelligence import CompanyPipeline

pipeline = CompanyPipeline(persist_to_neon=True)
pipeline.bootstrap()
result = pipeline.run()
```

### Check BIT Score

```python
from hubs.company_intelligence import BITEngine, SignalType

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

1. **Company Hub is the AXLE** - Everything anchors here first
2. **Spokes are DUMB** - I/O only, no logic, no state
3. **Contracts define interfaces** - Check YAML before implementing
4. **Phases are hub-owned** - 1-4 Company, 5-8 People
5. **BIT_SCORE drives outreach** - No score, no campaign

---

**Last Updated**: 2025-12-23
**Architecture**: Hub & Spoke v1.0
**Status**: Refactored and Streamlined

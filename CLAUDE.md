# Claude Bootstrap Guide - Barton Outreach Core

## INSTANT REPO OVERVIEW

**Repository Name**: Barton Outreach Core
**Architecture**: CL Parent-Child Doctrine
**Primary Purpose**: Marketing intelligence & executive enrichment platform
**Database**: Neon PostgreSQL (serverless)
**Last Refactored**: 2025-12-26

---

## CANONICAL DOCTRINE REFERENCE

| Document | Version | Authority |
|----------|---------|-----------|
| CANONICAL_ARCHITECTURE_DOCTRINE.md | 1.1.0 | imo-creator |
| HUB_SPOKE_ARCHITECTURE.md | 1.1.0 | imo-creator |
| ALTITUDE_DESCENT_MODEL.md | 1.1.0 | imo-creator |

| Field | Value |
|-------|-------|
| **Sovereign** | barton-enterprises |
| **CC Layer** | CC-02 (Hub) |
| **CTB Placement** | sys/outreach |
| **Doctrine Version** | 1.1.0 |
| **CTB Version** | 1.0.0 |

---

## CORE ARCHITECTURE: CL PARENT-CHILD

### The Golden Rule

```
IF outreach_id IS NULL:
    STOP. DO NOT PROCEED.
    → Mint outreach_id via outreach.outreach spine first.
    → Spine requires sovereign_id from CL with identity_status = 'PASS'
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
│  • Gate: identity_status = 'PASS' required for Outreach                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ sovereign_id (identity_status = 'PASS')
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      OUTREACH PROGRAM (PROGRAM-SCOPED)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  0. OUTREACH SPINE (Master Identity) ───────────────────────► outreach_id   │
│     • Table: outreach.outreach                                               │
│     • Mints outreach_id (THE identity for all Outreach)                      │
│     • sovereign_id is receipt to CL (sub-hubs DON'T see this)                │
│     • Gate: Only identity_status = 'PASS' from CL allowed                    │
│                                    │                                         │
│                                    │ outreach_id                             │
│                                    ▼                                         │
│  1. COMPANY TARGET (04.04.01) ──────────────────────────────► PASS REQUIRED │
│     • Table: outreach.company_target (FK: outreach_id)                       │
│     • Error: outreach.company_target_errors                                  │
│     • Domain resolution, email pattern discovery                             │
│     • EMITS: verified_pattern, domain                                        │
│                                    │                                         │
│                                    ▼                                         │
│  2. DOL FILINGS (04.04.03) ─────────────────────────────────► PASS REQUIRED │
│     • Table: outreach.dol (FK: outreach_id)                                  │
│     • Error: outreach.dol_errors                                             │
│     • EIN resolution, Form 5500 + Schedule A                                 │
│     • EMITS: ein, filing_signals, funding_type                               │
│                                    │                                         │
│                                    ▼                                         │
│  3. PEOPLE INTELLIGENCE (04.04.02) ─────────────────────────► PASS REQUIRED │
│     • Table: outreach.people (FK: outreach_id)                               │
│     • Error: outreach.people_errors                                          │
│     • CONSUMES: verified_pattern (CT), ein/signals (DOL)                     │
│     • EMITS: slot_assignments, people_records                                │
│                                    │                                         │
│                                    ▼                                         │
│  4. BLOG CONTENT (04.04.05) ────────────────────────────────► PASS          │
│     • Table: outreach.blog (FK: outreach_id)                                 │
│     • Error: outreach.blog_errors                                            │
│     • Content signals, news monitoring                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Error Pattern (LOCKED)

```
FAIL at any stage → record lands in that sub-hub's error table
Fix the issue → record re-enters pipeline at that stage
Same pattern as CL
```

### External Dependencies & Program Scope

| Boundary | System | Ownership |
|----------|--------|-----------|
| **External** | Company Lifecycle (CL) | Mints sovereign_id (company_unique_id), shared across all programs |
| **Program** | Outreach Spine | Mints outreach_id, program-scoped. Table: outreach.outreach |
| **Sub-Hub** | CT, DOL, People, Blog | FK to outreach_id for all operations (never see sovereign_id) |

### Key Doctrine (LOCKED)

- **CL is external** — Outreach receives sovereign_id, does NOT invoke CL
- **Outreach identity** — `outreach_id` is THE identity. All sub-hubs FK to this.
- **Spine table** — `outreach.outreach` is the master spine
- **sovereign_id is hidden** — Sub-hubs do NOT see sovereign_id directly
- **Gate** — Only `identity_status = 'PASS'` from CL gets an outreach_id
- **No sub-hub writes without valid outreach_id**

### Waterfall Doctrine Rules (LOCKED)

| Rule | Enforcement |
|------|-------------|
| Each sub-hub must PASS before next executes | Gate validation |
| No lateral reads between hubs | Spoke contracts only |
| No speculative execution | PASS gate blocks downstream |
| No retry/rescue from downstream | Failures land in error table |
| Data flows FORWARD ONLY | Bound by outreach_id |
| Sub-hubs may re-run if upstream unchanged | Idempotent design |
| Fail = Error table entry | Fix issue → re-enter at that stage |

### Hub Registry (Waterfall Order)

| Order | Hub | Table | Error Table | Core Metric |
|-------|-----|-------|-------------|-------------|
| EXT | **Company Lifecycle (CL)** | cl.company_identity | — | LIFECYCLE_STATE |
| 0 | **Outreach Spine** | outreach.outreach | — | IDENTITY_MINT |
| 1 | **Company Target** | outreach.company_target | outreach.company_target_errors | BIT_SCORE |
| 2 | **DOL Filings** | outreach.dol | outreach.dol_errors | FILING_MATCH_RATE |
| 3 | **People Intelligence** | outreach.people | outreach.people_errors | SLOT_FILL_RATE |
| 4 | **Blog Content** | outreach.blog | outreach.blog_errors | CONTENT_SIGNAL_RATE |

**Note**: All sub-hubs (1-4) FK to `outreach_id`. They do NOT see `sovereign_id`.

### Spoke Contracts

| Contract | Direction | Trigger |
|----------|-----------|---------|
| target-people | Bidirectional | slot_requirement / slot_assignment |
| target-dol | Bidirectional | ein_lookup / filing_signal |
| target-outreach | Bidirectional | target_selection / engagement_signal |
| people-outreach | Bidirectional | contact_selection / contact_state |
| cl-identity | Ingress Only | company_unique_id from CL |

### Key Doctrine Rules

1. **CL is PARENT** - Mints sovereign_id (company_unique_id), Outreach receives only
2. **Outreach Spine is master** - Mints outreach_id, all sub-hubs FK to this
3. **Sub-hubs don't see sovereign_id** - They only use outreach_id
4. **Spokes are I/O ONLY** - No logic, no state, no transformation
5. **No identity minting** - NEVER create sovereign_id (CL only)
6. **Signal to CL** - Engagement events flow back to parent

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
| Phase 0 | Outreach Spine | Mint outreach_id (gate: CL identity_status = 'PASS') |
| **IMO** | **Company Target** | **Single-pass IMO gate (I→M→O)** |
| Phase 5 | People Intelligence | Email Generation |
| Phase 6 | People Intelligence | Slot Assignment |
| Phase 7 | People Intelligence | Enrichment Queue |
| Phase 8 | People Intelligence | Output Writer |

> **NOTE**: Company Target Phases 1-4 are DEPRECATED. Company Target now operates as a single-pass IMO gate.
> See `docs/adr/ADR-CT-IMO-001.md` for details.

### Execution Order (Waterfall)

```
CL (sovereign_id, identity_status='PASS')
         │
         ▼
OUTREACH SPINE (mints outreach_id)
         │
         ▼
Company Target IMO (I→M→O) → PASS or FAIL
         │           └─► Error: outreach.company_target_errors (terminal)
         ▼
DOL Filings → PASS REQUIRED
         │           └─► Error: outreach.dol_errors
         ▼
People Intelligence (Phases 5-8) → PASS REQUIRED
         │           └─► Error: outreach.people_errors
         ▼
Blog Content → PASS
         │           └─► Error: outreach.blog_errors
         ▼
BIT Scoring → After all sub-hubs complete
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
| **outreach** | outreach | **MASTER SPINE** - mints outreach_id, FKs to CL |
| outreach | company_target | Company targeting (FK: outreach_id) |
| outreach | dol | DOL filing facts (FK: outreach_id) |
| outreach | people | Contact records (FK: outreach_id) |
| outreach | blog | Content signals (FK: outreach_id) |
| outreach | company_target_errors | CT error table |
| outreach | dol_errors | DOL error table |
| outreach | people_errors | People error table |
| outreach | blog_errors | Blog error table |
| cl | company_identity | CL sovereign identity (external) |
| marketing | company_master | Legacy master company records |
| intake | company_raw_intake | CSV staging |

---

## QUICK REFERENCE

### Import Paths

```python
# Company Target Sub-Hub (IMO Gate)
from hubs.company_target import run_company_target_imo
from hubs.company_target.imo.middle import BITEngine

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

## CLAUDE CODE SETTINGS (.claude/settings.local.json)

### What This File Is For
Permission prefixes ONLY. Tells Claude Code what bash commands, web fetches, and file reads are pre-approved.

### Rules (LOCKED)

1. **NO CREDENTIALS** - Never add API keys, passwords, tokens, or connection strings. Doppler handles all secrets.
2. **USE PREFIX PATTERNS** - Use `Bash(git:*)` not `Bash(git commit -m "specific message")`. The `:*` suffix covers all subcommands.
3. **NO ENV VAR ASSIGNMENTS** - `Bash(MY_VAR="value")` is not a valid permission, it's garbage.
4. **NO FILE PATHS AS COMMANDS** - `Bash(hub/company/__init__.py)` is nonsense. That's not a bash command.
5. **KEEP IT LEAN** - If a broader pattern exists (e.g., `Bash(powershell:*)`), don't add specific PowerShell commands.

### Current Approved Prefixes

```
Web: WebSearch, WebFetch (github.com, raw.githubusercontent.com, barton-outreach-core.lovable.app)
Tools: git, gh, npm, node, python, doppler, psql
Shells: powershell, bash, sh
File ops: mkdir, cp, rm, mv, chmod, cat, ls, dir, cd, tree, find, grep, findstr, xargs, wc, du, echo, curl, export
Package mgrs: winget, scoop
```

### If You Need a New Permission
Add a PREFIX pattern, not a specific command. Example: need `kubectl`? Add `Bash(kubectl:*)`, not `Bash(kubectl get pods -n production)`.

---

## NEVER DO THESE THINGS

- **NEVER** add credentials to `.claude/settings.local.json` (Doppler handles secrets)
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

1. **CL is PARENT** - Mints sovereign_id, Outreach receives only (with identity_status = 'PASS')
2. **Outreach Spine is master** - `outreach.outreach` mints `outreach_id`
3. **Sub-hubs FK to outreach_id** - They NEVER see sovereign_id directly
4. **Spokes are DUMB** - I/O only, no logic, no state
5. **Errors are work items** - Fail → error table → fix → re-enter
6. **BIT_SCORE drives outreach** - No score, no campaign

---

**Last Updated**: 2026-01-06
**Architecture**: CL Parent-Child Doctrine v1.1 (Spine Build)
**Status**: SPINE BUILD IN PROGRESS

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
| P0-3 | DV-011,012,013: Fuzzy matching | **RESOLVED** - Removed from CT (v3.0) |
| P1-1 | DV-002,004-007: AXLE terminology | Replace with "Sub-Hub" |
| P1-2 | DV-017: Missing FK constraint | Add FK to cl.company_identity |
| P1-3 | DV-027-030: CI guard gaps | Fix pattern matching in workflows |

# Canonical Chain (CC) Layer Map

**Doctrine Version**: 1.1.0
**Repository**: barton-outreach-core
**Governing Sovereign**: Company Lifecycle (CL) - EXTERNAL

---

## CC Layer Assignments

```
CC-01 SOVEREIGN (External)
└── company-lifecycle-cl/          # EXTERNAL REPO - Identity minting authority
    └── cl.company_identity        # company_unique_id lives here

CC-02 HUB (Ownership + Routing)
├── hubs/
│   ├── company-target/            # CC-02 | Internal anchor, receives identity
│   │   └── imo/
│   │       ├── input/             # Ingress from CL spoke
│   │       ├── middle/            # Domain, pattern, BIT logic
│   │       └── output/            # Egress to downstream hubs
│   │
│   ├── dol-filings/               # CC-02 | EIN resolution, Form 5500
│   │   └── imo/
│   │       ├── input/             # Consumes from Company Target
│   │       ├── middle/            # DOL processing logic
│   │       └── output/            # Emits EIN signals
│   │
│   ├── people-intelligence/       # CC-02 | People discovery, slot assignment
│   │   └── imo/
│   │       ├── input/             # Consumes CT + DOL signals
│   │       ├── middle/            # People matching, slots
│   │       └── output/            # Emits people records
│   │
│   ├── blog-content/              # CC-02 | Content signals, news
│   │   └── imo/
│   │       ├── input/             # Consumes CT signals
│   │       ├── middle/            # Content analysis
│   │       └── output/            # Emits BIT signals
│   │
│   └── outreach-execution/        # CC-02 | Campaign execution
│       └── imo/
│           ├── input/             # Consumes all upstream
│           ├── middle/            # Execution logic
│           └── output/            # Campaign actions

CC-03 CONTEXT (Bounded Configuration)
├── contexts/                      # CC-03 | Outreach context management
│   └── outreach_context           # outreach_context_id binding
├── contracts/                     # CC-03 | Spoke interface contracts
│   ├── company-people.contract.yaml
│   ├── company-dol.contract.yaml
│   └── ...
└── config/                        # CC-03 | Runtime configuration

CC-04 PROCESS (Runtime Execution)
├── hubs/*/imo/middle/phases/      # CC-04 | Pipeline phase execution
├── ops/                           # CC-04 | Operational processes
│   ├── enforcement/               # Doctrine enforcement
│   └── validation/                # Runtime validation
└── diagnostics/                   # CC-04 | Runtime diagnostics
```

---

## Spokes (I/O Only - No CC Layer)

Spokes are **interfaces**, not components. They carry data between CC-02 hubs.

```
spokes/
├── company-people/    # Bidirectional: CT ↔ People
├── company-dol/       # Bidirectional: CT ↔ DOL
├── company-outreach/  # Bidirectional: CT ↔ Outreach
├── people-outreach/   # Bidirectional: People ↔ Outreach
└── signal-company/    # Ingress only: External → CT
```

**Spoke Rules:**
- No logic in spokes
- No state in spokes
- Typed as Ingress or Egress
- Route through owning hub

---

## Authorization Matrix (Outreach Program)

| Source | Target | Permission | Notes |
|--------|--------|------------|-------|
| CC-01 (CL) | CC-02 (Hubs) | WRITE | Identity provision |
| CC-02 | CC-01 | DENIED | Never write to CL |
| CC-02 | CC-02 | READ via spoke | Cross-hub via contracts |
| CC-02 | CC-03 | WRITE | Context creation |
| CC-03 | CC-02 | READ | Config lookup |
| CC-04 | CC-03 | READ ONLY | Process reads context |
| CC-04 | CC-02 | DENIED | No direct hub writes |

---

## Identity Flow

```
CL (CC-01)                        Outreach (CC-02..CC-04)
┌─────────────────┐               ┌──────────────────────────┐
│ MINT            │               │ CONSUME ONLY             │
│ company_unique_id├──────────────►│ company_unique_id        │
│                 │               │ (read-only, immutable)   │
└─────────────────┘               └──────────────────────────┘
        │                                    │
        │                                    ▼
        │                         ┌──────────────────────────┐
        │                         │ MINT (program-scoped)    │
        │                         │ outreach_context_id      │
        │                         │ target_id                │
        │                         │ person_id                │
        │                         └──────────────────────────┘
```

---

## Conformance Declaration

| Field | Value |
|-------|-------|
| Doctrine Version | 1.1.0 |
| CTB Version | 1.0.0 |
| CC Layer (root) | CC-02 (Hub) |
| Governing Sovereign | CL (external) |
| Status | LOCKED |

---

**Last Updated**: 2026-01-05

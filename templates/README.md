# Hub-and-Spoke (HS) Templates — Barton Outreach Core

This directory contains the **authoritative templates** used to design, build,
and enforce Hub-and-Spoke (HS) systems for the Barton Outreach Core platform.

These templates define **structure and control**, not implementation.
All features must conform to them.

---

## Canonical Definitions (Bicycle Wheel Doctrine)

The following terms are used throughout all PRDs, PRs, and ADRs.
They are defined **once here** to prevent drift.

### Hub (Central Axle)

A **Hub** is a bounded system - the central axle of the bicycle wheel.
In Barton Outreach, the **Company Hub** is the master node.
It owns its rules, data, tooling, guard rails, and failure modes.
A hub must be independently understandable, testable, and stoppable.

**The Golden Rule:** IF company_id IS NULL OR domain IS NULL OR email_pattern IS NULL: STOP. Route to Company Identity Pipeline first.

### Spoke (Satellite Nodes)

A **Spoke** is a subordinate unit attached to a hub.
It inherits rules and tooling from its parent hub.
A spoke cannot exist without a hub.
A spoke cannot define its own tools.

**Current Spokes:**
- People Node (ACTIVE)
- DOL Node (ACTIVE)
- Blog Node (PLANNED)
- Talent Flow (SHELL)
- BIT Engine (PLANNED)
- Outreach (PLANNED)

### SubWheel (Fractal Wheel)

A **SubWheel** is a mini bicycle wheel at the endpoint of a spoke.
It has its own hub (central node) and sub-spokes.
SubWheels enable fractal complexity without breaking the hierarchy.

**Example:** Email Verification SubWheel
- Hub: MillionVerifier
- SubSpokes: PatternGuesser (FREE), BulkVerifier ($37/10K)

### Connector

A **Connector** is an interface between hubs or between a hub and an external system.
Connectors are owned by exactly one hub.
Connectors define the contract; they do not own business logic.

### Tool

A **Tool** is a capability registered to a hub.
Tools are owned by hubs, never by spokes.
New tools require an ADR.

### Guard Rail

A **Guard Rail** is a constraint that prevents harm.
Examples: rate limits, timeouts, circuit breakers, validation rules.
Guard rails are defined at the hub level and inherited by spokes.

### Kill Switch

A **Kill Switch** is a mechanism to halt a hub or spoke immediately.
Every hub and spoke must have one.
Kill switches must be tested before deployment.

### Failure Spoke

A **Failure Spoke** is a first-class citizen in the Bicycle Wheel Doctrine.
Failures are not exceptions - they are expected outcomes that route to
dedicated failure spokes for processing and reporting to the Master Failure Hub.

### Promotion Gate

A **Promotion Gate** is a checkpoint that must pass before deployment.
Gates are numbered G1–G5.
All gates must pass; there are no exceptions.

---

## Directory Structure

```
templates/
├── README.md                           # This file (doctrine definitions)
├── checklists/
│   └── HUB_COMPLIANCE.md              # Pre-flight checklist for compliance
├── prd/
│   ├── PRD_HUB.md                     # Product requirements template for hubs
│   ├── PRD_SPOKE.md                   # Product requirements template for spokes
│   └── PRD_SUBWHEEL.md                # Product requirements template for SubWheels
├── pr/
│   ├── PULL_REQUEST_TEMPLATE_HUB.md   # PR template for hub changes
│   └── PULL_REQUEST_TEMPLATE_SPOKE.md # PR template for spoke changes
└── adr/
    └── ADR.md                         # Architecture Decision Record template
```

---

## Required Artifacts for Any Hub

Before a hub can be deployed, it must have:

1. **PRD**
   - Created from `templates/prd/PRD_HUB.md`
   - Defines spokes, connectors, tooling, and controls

2. **Hub Compliance Checklist**
   - Created from `templates/checklists/HUB_COMPLIANCE.md`
   - Must be satisfied before merge or deployment

3. **PR Enforcement**
   - Hub changes use the Hub PR template
   - Spoke changes use the Spoke PR template

4. **ADR(s)**
   - Required for new tools or irreversible decisions

If any artifact is missing, incomplete, or bypassed,
the hub is considered **non-viable**.

---

## Required Artifacts for Any Spoke

1. **PRD** from `templates/prd/PRD_SPOKE.md`
2. **Parent Hub Approval** - Hub owner must sign off
3. **Failure Mode Documentation** - Where do failures route?
4. **Tool Inheritance Verification** - No new tools allowed

---

## Required Artifacts for Any SubWheel

1. **PRD** from `templates/prd/PRD_SUBWHEEL.md`
2. **Parent Spoke Approval**
3. **Cost Hierarchy Documentation** - FREE tiers first
4. **SubSpoke Processing Order** - Clockwise rotation

---

## Template Usage Rules

- Templates in this directory are **never edited directly**.
- Projects **copy and instantiate** templates.
- Instantiated files live in project repos under:
  - `/docs/prd/`
  - `/docs/adr/`
  - `.github/PULL_REQUEST_TEMPLATE/`
- Projects declare which template version they conform to.

---

## Enforcement Model

- PR templates enforce human attestation.
- CI enforces truth (tests, schemas, logs).
- Violations block merge or trigger kill switches.
- Failures route to Master Failure Hub (shq_error_log).

Hope is not an enforcement strategy.

---

## Design Principle (Bicycle Wheel Doctrine)

> If you cannot diagram it as a hub with spokes and connectors,
> you are not allowed to build it.

> Spokes cannot call other spokes directly.
> Everything routes through the hub.

> Failures are not exceptions - they are first-class citizens
> with their own failure spokes.

---

## Authority

This repository defines doctrine for Barton Outreach Core.
Projects conform to it.
Doctrine does not conform to projects.

See: `repo-data-diagrams/BICYCLE_WHEEL_DOCTRINE.md` for complete doctrine.

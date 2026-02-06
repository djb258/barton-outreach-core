# OSAM — Operational Semantic Access Map

**Repository**: barton-outreach-core
**Status**: LOCKED
**Authority**: CONSTITUTIONAL
**Version**: 1.0.0
**Change Protocol**: ADR + HUMAN APPROVAL REQUIRED

---

## Purpose & Scope

The **Operational Semantic Access Map (OSAM)** is the authoritative query-routing contract for the Outreach hub. It defines:

- **Where** data is queried from (query surfaces)
- **Which** tables own which concepts (semantic ownership)
- **Which** join paths are allowed (relationship contracts)
- **When** an agent MUST STOP and ask for clarification (halt conditions)

### Hierarchical Position

```
REPO_DOMAIN_SPEC.md (Transformation Law)
    │
    ▼
PRD (Behavioral Proof — WHAT transformation occurs)
    │
    ▼
OSAM (Semantic Access Map — WHERE to query, HOW to join) ← THIS DOCUMENT
    │
    ▼
ERD (Structural Proof — WHAT tables implement OSAM contracts)
    │
    ▼
PROCESS (Execution Declaration — HOW transformation executes)
```

**OSAM sits ABOVE ERDs and DRIVES them.**
ERDs may only implement relationships that OSAM declares.

---

## Chain of Authority

### Parent → Spine → Sub-Hub Hierarchy

```
CL (Company Lifecycle) — CC-01 Sovereign
    │
    ▼ mints sovereign_company_id
    │
OUTREACH (This Hub) — CC-02
    │
    ▼ owns
    │
outreach.outreach (SPINE TABLE) — Universal Join Key: outreach_id
    │
    ├──────────────────────────────────────────────────────────────┐
    │                    │                    │                    │
    ▼                    ▼                    ▼                    ▼
Company Target     DOL Filings      People Intelligence     Blog Content
(04.04.01)         (04.04.03)           (04.04.02)          (04.04.05)
    │                    │                    │                    │
    ▼                    ▼                    ▼                    ▼
outreach.          outreach.           outreach.            outreach.
company_target     dol                 people               blog
```

### Authority Rules

| Rule | Description |
|------|-------------|
| Single Spine | Outreach has exactly ONE spine table: `outreach.outreach` |
| Universal Key | All sub-hub tables join to spine via `outreach_id` |
| No Cross-Sub-Hub Joins | Sub-hubs may not join directly to each other |
| Spine Owns Identity | `outreach.outreach` is the authoritative source of outreach identity |
| CL Authority | `sovereign_company_id` is received from CL, never minted by Outreach |

---

## Universal Join Key Declaration

```yaml
universal_join_key:
  name: "outreach_id"
  type: "UUID"
  source_table: "outreach.outreach"
  description: "The single key that connects all Outreach sub-hub tables"
```

### Join Key Rules

| Rule | Enforcement |
|------|-------------|
| Single Source | `outreach_id` is minted ONLY in `outreach.outreach` |
| Immutable | Once assigned, an `outreach_id` cannot change |
| Propagated | All sub-hub tables receive the key via FK relationship |
| Required | No sub-hub table may exist without relationship to `outreach_id` |
| CL Registration | `outreach_id` is registered ONCE in `cl.company_identity` (WRITE-ONCE) |

---

## Query Routing Table

The Query Routing Table declares which table answers which question.

| Question Type | Authoritative Table | Join Path | Notes |
|---------------|---------------------|-----------|-------|
| Company identity | `outreach.outreach` | Direct | Spine table |
| Domain resolution | `outreach.company_target` | `outreach.outreach` → `outreach.company_target` | |
| Email pattern | `outreach.company_target` | `outreach.outreach` → `outreach.company_target` | |
| EIN/DOL filings | `outreach.dol` | `outreach.outreach` → `outreach.dol` | |
| People/executives | `outreach.people` | `outreach.outreach` → `outreach.people` | |
| Slot assignments | `people.company_slot` | `outreach.outreach` → `people.company_slot` | |
| BIT scores | `outreach.bit_scores` | `outreach.outreach` → `outreach.bit_scores` | |
| Blog/content signals | `outreach.blog` | `outreach.outreach` → `outreach.blog` | |
| Marketing eligibility | `outreach.vw_marketing_eligibility_with_overrides` | View (materialized) | Authoritative eligibility |
| Sovereign completion | `outreach.vw_sovereign_completion` | View (materialized) | Tier computation |
| Manual overrides | `outreach.manual_overrides` | Direct | Kill switch records |

### Routing Rules

| Rule | Description |
|------|-------------|
| One Table Per Question | Each question type has exactly ONE authoritative table |
| Explicit Paths Only | Only declared join paths may be used |
| No Discovery | Agents may not discover new query paths at runtime |
| HALT on Unknown | If a question cannot be routed, agent MUST HALT |

---

## Hub Definitions

### Parent Hub (Received Authority)

```yaml
parent_authority:
  name: "CL (Company Lifecycle)"
  cc_layer: CC-01
  provides:
    - sovereign_company_id
    - company_name
    - company_domain
    - existence_verified
  relationship: "Outreach receives identity from CL"
```

### This Hub

```yaml
hub:
  name: "OUTREACH"
  cc_layer: CC-02
  hub_id: "HUB-OUTREACH-001"
  spine_table: "outreach.outreach"
  universal_join_key: "outreach_id"
  owns:
    - "Company Target (04.04.01)"
    - "DOL Filings (04.04.03)"
    - "People Intelligence (04.04.02)"
    - "Blog Content (04.04.05)"
    - "Outreach Execution (04.04.04)"
```

### Spine Table

```yaml
spine_table:
  name: "outreach.outreach"
  purpose: "Authoritative source of outreach identity and workflow state"
  primary_key: "outreach_id"
  query_surface: true
  columns:
    - name: "outreach_id"
      type: "UUID"
      role: "Universal join key (minted here)"
    - name: "sovereign_company_id"
      type: "UUID"
      role: "FK to cl.company_identity"
    - name: "status"
      type: "ENUM"
      role: "Workflow state"
    - name: "created_at"
      type: "TIMESTAMP"
      role: "Creation timestamp"
    - name: "updated_at"
      type: "TIMESTAMP"
      role: "Last update timestamp"
```

### Sub-Hubs

```yaml
sub_hubs:
  - name: "Company Target"
    doctrine_id: "04.04.01"
    cc_layer: CC-03
    purpose: "Domain resolution and email pattern discovery"
    joins_to_spine_via: "outreach_id"
    tables:
      - "outreach.company_target"

  - name: "DOL Filings"
    doctrine_id: "04.04.03"
    cc_layer: CC-03
    purpose: "EIN resolution and Form 5500 processing"
    joins_to_spine_via: "outreach_id"
    tables:
      - "outreach.dol"

  - name: "People Intelligence"
    doctrine_id: "04.04.02"
    cc_layer: CC-03
    purpose: "Executive enrichment and slot assignment"
    joins_to_spine_via: "outreach_id"
    tables:
      - "outreach.people"
      - "people.company_slot"
      - "people.people_master"

  - name: "Blog Content"
    doctrine_id: "04.04.05"
    cc_layer: CC-03
    purpose: "Content signal detection and timing"
    joins_to_spine_via: "outreach_id"
    tables:
      - "outreach.blog"

  - name: "Outreach Execution"
    doctrine_id: "04.04.04"
    cc_layer: CC-03
    purpose: "Campaign execution and engagement tracking"
    joins_to_spine_via: "outreach_id"
    tables:
      - "outreach.campaigns"
      - "outreach.sequences"
      - "outreach.send_log"
```

---

## Allowed Join Paths

### Declared Joins

Only joins declared in this section are permitted. All other joins are INVALID.

| From Table | To Table | Join Key | Direction | Purpose |
|------------|----------|----------|-----------|---------|
| `outreach.outreach` | `outreach.company_target` | `outreach_id` | 1:1 | Domain/email data |
| `outreach.outreach` | `outreach.dol` | `outreach_id` | 1:1 | DOL filing data |
| `outreach.outreach` | `outreach.people` | `outreach_id` | 1:N | People records |
| `outreach.outreach` | `outreach.blog` | `outreach_id` | 1:1 | Blog signals |
| `outreach.outreach` | `outreach.bit_scores` | `outreach_id` | 1:1 | BIT score |
| `outreach.outreach` | `people.company_slot` | `outreach_id` | 1:N | Slot assignments |
| `outreach.outreach` | `cl.company_identity` | `sovereign_company_id` | N:1 | CL identity lookup |
| `outreach.people` | `people.people_master` | `people_id` | N:1 | Person details |
| `people.company_slot` | `people.people_master` | `people_id` | N:1 | Slotted person details |

### Join Rules

| Rule | Enforcement |
|------|-------------|
| Declared Only | If a join is not in this table, it is INVALID |
| No Ad-Hoc Joins | Agents may not invent joins at runtime |
| ERD Must Implement | ERDs may only contain joins declared here |
| ADR for New Joins | Adding a new join requires ADR approval |

### Forbidden Joins

| From | To | Reason |
|------|----|--------|
| `outreach.*` | `sales.*` | Cross-hub isolation |
| `outreach.*` | `client.*` | Cross-hub isolation |
| `outreach.company_target` | `outreach.dol` (direct) | Cross-sub-hub; must route through spine |
| `outreach.people` | `outreach.blog` (direct) | Cross-sub-hub; must route through spine |
| Any table | `cl.*` (WRITE) | CL is authority; only READ permitted |
| Any table | `hunter_company` (direct query) | SOURCE table; not a query surface |
| Any table | `hunter_contact` (direct query) | SOURCE table; not a query surface |

---

## Source / Enrichment Table Classification

### Table Classifications

| Classification | Query Surface | Description |
|----------------|---------------|-------------|
| **QUERY** | YES | Tables that answer questions |
| **SOURCE** | NO | Raw ingested data; not for direct query |
| **ENRICHMENT** | NO | Lookup/reference data; joined for enrichment only |
| **AUDIT** | NO | Logging/tracking; not for business queries |
| **VIEW** | YES | Materialized views for complex queries |

### Classification Table

| Table Name | Classification | Query Surface | Notes |
|------------|----------------|---------------|-------|
| `outreach.outreach` | QUERY | YES | Spine table |
| `outreach.company_target` | QUERY | YES | Domain/email facts |
| `outreach.dol` | QUERY | YES | DOL filing facts |
| `outreach.people` | QUERY | YES | People facts |
| `outreach.blog` | QUERY | YES | Blog signal facts |
| `outreach.bit_scores` | QUERY | YES | BIT scores |
| `people.company_slot` | QUERY | YES | Slot assignments |
| `people.people_master` | QUERY | YES | Person details |
| `outreach.vw_marketing_eligibility_with_overrides` | VIEW | YES | Eligibility view |
| `outreach.vw_sovereign_completion` | VIEW | YES | Completion view |
| `outreach.manual_overrides` | QUERY | YES | Kill switch |
| `hunter_company` | SOURCE | **NO** | Raw Hunter import |
| `hunter_contact` | SOURCE | **NO** | Raw Hunter contacts |
| `intake.company_raw_intake` | SOURCE | **NO** | CSV staging |
| `shq_error_log` | AUDIT | **NO** | Error tracking |
| `outreach.override_audit_log` | AUDIT | **NO** | Override audit |

### Classification Rules

| Rule | Enforcement |
|------|-------------|
| SOURCE tables are NEVER query surfaces | Agent MUST HALT if asked to query SOURCE |
| ENRICHMENT tables are joined, not queried | Never the "FROM" table |
| QUERY tables are the only valid query surfaces | All questions route to QUERY tables |
| Misclassified queries are INVALID | Agent rejects and escalates |

---

## STOP Conditions

Agents MUST HALT and request clarification when:

### Query Routing STOP Conditions

| Condition | Action |
|-----------|--------|
| Question cannot be routed to a declared table | HALT — ask human for routing |
| Question requires a join not declared in OSAM | HALT — request ADR |
| Question targets a SOURCE or ENRICHMENT table | HALT — query surfaces only |
| Question requires cross-sub-hub direct join | HALT — isolation violation |
| Question requires write to CL tables | HALT — CL authority violation |

### Semantic STOP Conditions

| Condition | Action |
|-----------|--------|
| Concept not declared in OSAM | HALT — semantic gap |
| Multiple tables claim ownership of concept | HALT — ambiguity resolution required |
| `outreach_id` not found in query path | HALT — structural violation |

### STOP Output Format

```
OSAM HALT
================================================================================

Reason: [QUERY_UNROUTABLE | JOIN_UNDECLARED | SOURCE_QUERY | ISOLATION_VIOLATION | CL_WRITE_BLOCKED | SEMANTIC_GAP | AMBIGUITY | STRUCTURAL]

Question: "<THE_QUESTION_ASKED>"
Attempted Route: [What the agent tried to do]
OSAM Reference: [Section that applies]

Resolution Required:
  [ ] Human must declare new routing
  [ ] ADR required for new join
  [ ] Clarify which table owns this concept
  [ ] CL authority gate blocks this action

Agent is HALTED. Awaiting resolution.
```

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-02-05 | Claude | Initial OSAM declaration for Outreach hub |

---

## Validation Checklist

Before OSAM is considered valid:

| Check | Status |
|-------|--------|
| [x] Universal join key declared (`outreach_id`) | PASS |
| [x] Spine table identified (`outreach.outreach`) | PASS |
| [x] All sub-hubs listed with table ownership | PASS |
| [x] All allowed joins explicitly declared | PASS |
| [x] All tables classified (QUERY/SOURCE/ENRICHMENT/AUDIT) | PASS |
| [x] Query routing table complete | PASS |
| [x] STOP conditions understood | PASS |
| [x] No undeclared joins exist in ERD | VERIFY |

---

## Relationship to Other Artifacts

| Artifact | OSAM Relationship |
|----------|-------------------|
| **REPO_DOMAIN_SPEC.md** | Domain bindings; OSAM implements routing for declared facts |
| **PRD** | PRD declares WHAT transformation. OSAM declares WHERE to query. PRD must reference OSAM. |
| **ERD** | ERD implements OSAM. ERD may not introduce joins not in OSAM. |
| **Process** | Processes query via OSAM routes. No ad-hoc queries. |
| **Agents** | Agents follow OSAM routing strictly. HALT on unknown routes. |
| **Schema Guard** | Enforces OSAM-declared boundaries at runtime |

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-02-05 |
| Last Modified | 2026-02-05 |
| Version | 1.0.0 |
| Status | LOCKED |
| Authority | CONSTITUTIONAL |
| Derives From | REPO_DOMAIN_SPEC.md, OSAM Template |
| Change Protocol | ADR + HUMAN APPROVAL REQUIRED |

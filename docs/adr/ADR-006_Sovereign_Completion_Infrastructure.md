# ADR: Sovereign Completion Infrastructure

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | CL Parent-Child Doctrine v1.1 |
| **CC Layer** | CC-02 |

---

## ADR Identity

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-006 |
| **Status** | [x] Accepted |
| **Date** | 2026-01-19 |

---

## Owning Hub (CC-02)

| Field | Value |
|-------|-------|
| **Sovereign ID** | barton-enterprises |
| **Hub Name** | Barton Outreach Core |
| **Hub ID** | 04.04.02.04 |

---

## CC Layer Scope

| Layer | Affected | Description |
|-------|----------|-------------|
| CC-01 (Sovereign) | [ ] | No sovereign changes |
| CC-02 (Hub) | [x] | Hub registry and completion tracking |
| CC-03 (Context) | [x] | Marketing eligibility views |
| CC-04 (Process) | [x] | Backfill and migration execution |

---

## IMO Layer Scope

| Layer | Affected |
|-------|----------|
| I — Ingress | [ ] |
| M — Middle | [x] |
| O — Egress | [x] |

---

## Constant vs Variable

| Classification | Value |
|----------------|-------|
| **This decision defines** | [x] Constant (structure/meaning) |
| **Mutability** | [x] ADR-gated |

---

## Context

The Barton Outreach system requires a centralized mechanism to:

1. Track completion status of each company across all required hubs (Company Target, DOL, People Intelligence, Talent Flow)
2. Compute marketing eligibility tiers (0-3) based on hub completion
3. Enforce kill switches that override computed eligibility
4. Provide a single source of truth for "Is this company ready for marketing?"

Without this infrastructure, marketing decisions were ad-hoc and lacked audit trails.

---

## Decision

Implement a **Sovereign Completion** infrastructure consisting of:

1. **Hub Registry Table** (`outreach.hub_registry`)
   - Defines 6 hubs (4 required, 2 optional)
   - Tracks waterfall order for processing
   - Gates completion based on required hub status

2. **Company Hub Status Table** (`outreach.company_hub_status`)
   - Tracks each company's status per hub (PASS, IN_PROGRESS, FAIL, BLOCKED)
   - Uses enum for status consistency
   - Primary key: (company_unique_id, hub_id)

3. **Sovereign Completion View** (`outreach.vw_sovereign_completion`)
   - Read-only aggregation of hub statuses
   - Computes overall status (COMPLETE, IN_PROGRESS, BLOCKED)
   - No triggers, no mutation logic

4. **Marketing Eligibility View** (`outreach.vw_marketing_eligibility`)
   - Computes marketing tier from hub completion
   - Tier -1 (INELIGIBLE), 0 (Cold), 1 (Persona), 2 (Trigger), 3 (Aggressive)

5. **Marketing Eligibility with Overrides View** (`outreach.vw_marketing_eligibility_with_overrides`)
   - Authoritative view for marketing decisions
   - Applies kill switches to computed tiers

---

## Alternatives Considered

| Option | Why Not Chosen |
|--------|----------------|
| Stored procedures with computed columns | Too much logic in DB layer; harder to test |
| Application-level tier computation | No single source of truth; race conditions |
| Materialized views | Unnecessary complexity; real-time needed |
| Do Nothing | Marketing decisions would remain ad-hoc |

---

## Consequences

### Enables

- Single source of truth for marketing eligibility
- Audit trail for tier changes
- Kill switch enforcement at data layer
- Tier progression tracking over time
- Waterfall order enforcement

### Prevents

- Ad-hoc marketing decisions
- Bypassing kill switches via UI
- Inconsistent tier computation
- Ghost PASS states (companies marked PASS without data)

---

## PID Impact (if CC-04 affected)

| Field | Value |
|-------|-------|
| **New PID required** | [x] No |
| **PID pattern change** | [x] No |
| **Audit trail impact** | Tier changes logged via override_audit_log |

---

## Guard Rails

| Type | Value | CC Layer |
|------|-------|----------|
| Rate Limit | N/A | |
| Timeout | N/A | |
| Kill Switch | outreach.manual_overrides | CC-02 |

---

## Rollback

1. Drop views in reverse order:
   - `DROP VIEW outreach.vw_marketing_eligibility_with_overrides`
   - `DROP VIEW outreach.vw_marketing_eligibility`
   - `DROP VIEW outreach.vw_sovereign_completion`
2. Drop tables:
   - `DROP TABLE outreach.company_hub_status`
   - `DROP TABLE outreach.hub_registry`
3. Drop enums:
   - `DROP TYPE outreach.hub_status_enum`

Note: Rollback will lose all hub status history.

---

## Traceability

| Artifact | Reference |
|----------|-----------|
| Canonical Doctrine | CANONICAL_ARCHITECTURE_DOCTRINE.md |
| PRD | docs/prd/PRD_SOVEREIGN_COMPLETION.md |
| Work Items | Sovereign Completion Infrastructure deployment |
| PR(s) | PR: Sovereign Completion Infrastructure v1.1.0 |
| Migration | migrations/2026-01-19-hub-registry.sql |
| Migration | migrations/2026-01-19-sovereign-completion-view.sql |

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner (CC-02) | Barton Enterprises | 2026-01-19 |
| Reviewer | Claude Code | 2026-01-19 |

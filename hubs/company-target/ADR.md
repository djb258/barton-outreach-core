# ADR: Company Target as Sub-Hub (Not Main Hub)

## ADR Identity

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-CT-001 |
| **Status** | [x] Accepted |
| **Date** | 2026-01-01 |

---

## Owning Hub

| Field | Value |
|-------|-------|
| **Hub Name** | Company Target |
| **Hub ID** | HUB-CT-001 |

---

## Context

Company Target was previously acting as a "main hub" with identity minting capabilities.
This violates the CL Parent-Child doctrine where Company Lifecycle is the sole authority
for company identity.

---

## Decision

Company Target is a **sub-hub only**. It:
- Receives company_sov_id from Company Lifecycle (external, read-only)
- Does NOT mint, revive, or mutate company existence
- Determines outreach readiness, not company existence
- Uses disposable outreach_context_id for execution tracking

---

## Alternatives Considered

| Option | Why Not Chosen |
|--------|----------------|
| Company Target as main hub | Violates single-authority doctrine |
| Merge with Company Lifecycle | Different domains (existence vs readiness) |
| Do Nothing | Would allow identity conflicts |

---

## Consequences

### Enables

- Clean separation of company existence vs outreach readiness
- Cost tracking per execution context
- Single-attempt enforcement for premium tools

### Prevents

- Dual authority over company identity
- Identity conflicts between repos
- Untracked cost leakage

---

## Lifecycle Impact

| Current Gate | Proposed Gate | Justification |
|--------------|---------------|---------------|
| None | >= ACTIVE | Company must exist and be active before targeting |

---

## Cost Impact

| Tool | Tier | Cost Class | Usage Limit |
|------|------|------------|-------------|
| Prospeo | 2 | Premium | 1 per context |
| Snov | 2 | Premium | 1 per context |
| Clay | 2 | Premium | 1 per context |

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner | | |
| Reviewer | | |

---

# ADR: CL Upstream Gate Enforcement

## ADR Identity

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-CT-002 |
| **Status** | [x] Accepted |
| **Date** | 2026-01-02 |

---

## Owning Hub

| Field | Value |
|-------|-------|
| **Hub Name** | Company Target |
| **Hub ID** | HUB-CT-001 |

---

## Context

Outreach was allowing execution even when company_sov_id did not exist in Company Lifecycle.
This created orphan records and violated the upstream contract that CL is the sole authority
for company existence verification.

---

## Decision

Implement a **CL Upstream Gate** that runs BEFORE any Company Target logic:

1. Check if `company_sov_id` exists in `cl.company_identity`
2. If EXISTS → `EXISTENCE_PASS` (proceed to Phase 1-4)
3. If MISSING → Write error `CT_UPSTREAM_CL_NOT_VERIFIED` and STOP

Option B chosen: Sovereign ID existence = verified (if CL minted the ID, existence was verified).

---

## Alternatives Considered

| Option | Why Not Chosen |
|--------|----------------|
| Option A: New `existence_verified` column | Requires CL repo changes |
| Option B: Check sovereign ID exists | **CHOSEN** - Works now, no CL changes |
| Option C: New signal table | Requires CL repo changes + new table |

---

## Consequences

### Enables

- Clean upstream contract enforcement
- No orphan records in Outreach
- Clear error routing for missing CL companies

### Prevents

- Outreach from implementing CL logic (existence checks)
- Scope bleed between repos
- Silent failures on missing upstream data

---

## Implementation

| Component | Location |
|-----------|----------|
| Gate module | `hubs/company-target/imo/middle/utils/cl_gate.py` |
| Error code | `CT_UPSTREAM_CL_NOT_VERIFIED` |
| Pipeline stage | `upstream_cl_gate` |
| Tests | `tests/hub/company/test_cl_gate.py` |

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner | | |
| Reviewer | | |

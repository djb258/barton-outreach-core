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

# ADR-008: v1.0 Operational Baseline Certification

## Status
**ACCEPTED**

## Date
2026-01-20

## Context

Barton Outreach has completed infrastructure hardening, sub-hub implementation, safety gate enforcement, and tier telemetry analytics. The system has passed final certification audit (2026-01-19) and is ready for live marketing operations.

### Problem Statement

We need to formally document the v1.0 operational baseline to:
1. Define what components are LIVE vs DEFERRED
2. Establish change control for critical components
3. Create audit trail for certification decisions
4. Enable safe operational handoff

### Certification Results

| Section | Status |
|---------|--------|
| Infrastructure | PASS |
| Doctrine Compliance | PASS |
| Data Integrity | PASS |
| Operational Safety | PASS |

**Final Decision**: Safe to enable live marketing = **YES**

## Decision

### 1. Establish v1.0 Operational Baseline

**Freeze Date**: 2026-01-20

The following components are FROZEN and require formal change request to modify:

#### Authoritative Views (FROZEN)
- `outreach.vw_marketing_eligibility_with_overrides` - THE source of truth
- `outreach.vw_sovereign_completion` - Sovereign completion status
- `outreach.vw_tier_distribution` - Tier breakdown

#### Tier Logic (FROZEN)
- Tier -1: INELIGIBLE (BLOCKED or marketing_disabled)
- Tier 0: COLD (COMPLETE, no signals)
- Tier 1: PERSONA (COMPLETE + People PASS)
- Tier 2: TRIGGER (COMPLETE + Blog signals)
- Tier 3: AGGRESSIVE (COMPLETE + BIT >= 50)

#### Safety Gates (FROZEN)
- Marketing Safety Gate with HARD_FAIL enforcement
- Kill Switch system (manual_overrides table)
- Append-only send_attempt_audit logging

### 2. Deferred Work Orders

**WO-DOL-001: DOL Enrichment Pipeline**
- Status: DEFERRED (not blocking v1.0)
- Reason: EIN resolution enrichment not complete
- Impact: DOL hub defaults to IN_PROGRESS (non-blocking)

### 3. DO NOT MODIFY Registry

Created `doctrine/DO_NOT_MODIFY_REGISTRY.md` as central reference for all frozen components.

### 4. Documentation Updates

| Document | Purpose |
|----------|---------|
| `docs/GO-LIVE_STATE_v1.0.md` | Live vs deferred components |
| `doctrine/DO_NOT_MODIFY_REGISTRY.md` | Frozen component registry |
| Banner headers added to critical SQL/Python files | In-file warnings |

## Consequences

### Positive
- Clear operational baseline for production handoff
- Change control prevents accidental modification of critical logic
- Audit trail for compliance and incident investigation
- DOL deferral allows v1.0 launch without blocking dependency

### Negative
- Change request process adds overhead for legitimate modifications
- Documentation must be kept in sync with code changes

### Risks Mitigated
- Accidental modification of tier logic
- Bypass of safety gates
- Loss of audit trail
- Unclear operational boundaries

## Alternatives Considered

### Alternative 1: No Freeze
- Pro: Maximum flexibility
- Con: Risk of accidental breaking changes, no change control
- **Rejected**: Unacceptable risk for production system

### Alternative 2: Complete DOL Before Launch
- Pro: Full feature set from day one
- Con: Delays v1.0 launch indefinitely
- **Rejected**: DOL is non-blocking; can add later

## References

- `docs/GO-LIVE_STATE_v1.0.md`
- `doctrine/DO_NOT_MODIFY_REGISTRY.md`
- `docs/reports/FINAL_CERTIFICATION_REPORT_2026-01-19.md`
- CL Parent-Child Doctrine v1.1

## Author
IMO-Creator: Doctrine Freeze Agent
Date: 2026-01-20

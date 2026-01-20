# DO NOT MODIFY REGISTRY
## v1.0 Operational Baseline - Frozen Components

**Version**: 1.0.0
**Freeze Date**: 2026-01-20
**Status**: FROZEN
**Reference**: docs/GO-LIVE_STATE_v1.0.md

---

## Purpose

This registry documents all components that are **FROZEN** at the v1.0 operational baseline. Any modification to these components requires a formal change request process.

---

## Change Request Process

Any modification to FROZEN components requires:

1. **Formal Change Request** with justification
2. **Impact Analysis** on all dependent systems
3. **Rollback Plan** defined before implementation
4. **Full Re-Certification** after changes
5. **Technical Lead Sign-Off**

---

## FROZEN Components

### Authoritative Views (SQL)

| Component | File | Purpose |
|-----------|------|---------|
| `outreach.vw_marketing_eligibility_with_overrides` | infra/migrations/2026-01-19-kill-switches.sql | THE source of truth for marketing eligibility |
| `outreach.vw_sovereign_completion` | (base migration) | Sovereign completion status per company |
| `outreach.vw_tier_distribution` | infra/migrations/2026-01-20-tier-telemetry-views.sql | Tier breakdown by count |

### Kill Switch System (SQL)

| Component | File | Purpose |
|-----------|------|---------|
| `outreach.manual_overrides` | infra/migrations/2026-01-19-kill-switches.sql | Kill switch enforcement table |
| `outreach.override_audit_log` | infra/migrations/2026-01-19-kill-switches.sql | Override audit trail |
| `outreach.override_type_enum` | infra/migrations/2026-01-19-kill-switches.sql | Override type definitions |

### Marketing Safety Gate (Python)

| Component | File | Purpose |
|-----------|------|---------|
| `MarketingSafetyGate` class | hubs/outreach-execution/imo/middle/marketing_safety_gate.py | HARD_FAIL enforcement logic |
| `EligibilityResult` dataclass | hubs/outreach-execution/imo/middle/marketing_safety_gate.py | Eligibility check result structure |

### Audit Logging (SQL)

| Component | File | Purpose |
|-----------|------|---------|
| `outreach.send_attempt_audit` | infra/migrations/2026-01-20-send-attempt-audit.sql | Append-only audit log |
| Protective triggers | infra/migrations/2026-01-20-send-attempt-audit.sql | Prevent updates/deletes |

### Tier Telemetry (SQL)

| Component | File | Purpose |
|-----------|------|---------|
| `outreach.vw_hub_block_analysis` | infra/migrations/2026-01-20-tier-telemetry-views.sql | Hub blocking analysis |
| `outreach.vw_freshness_analysis` | infra/migrations/2026-01-20-tier-telemetry-views.sql | Freshness decay tracking |
| `outreach.vw_signal_gap_analysis` | infra/migrations/2026-01-20-tier-telemetry-views.sql | Signal coverage gaps |
| `outreach.vw_tier_telemetry_summary` | infra/migrations/2026-01-20-tier-telemetry-views.sql | Dashboard summary |
| `outreach.tier_snapshot_history` | infra/migrations/2026-01-20-tier-telemetry-views.sql | Historical snapshots |

### Hub Registry (SQL)

| Component | File | Purpose |
|-----------|------|---------|
| `outreach.hub_registry` | (base migration) | Waterfall order definition |
| Hub waterfall order | (base migration) | company-target > dol-filings > people-intelligence > talent-flow |

---

## Tier Logic Rules (FROZEN)

### Tier Assignment

| Tier | Name | Criteria |
|------|------|----------|
| -1 | INELIGIBLE | Any BLOCKED hub OR marketing_disabled=true |
| 0 | COLD | COMPLETE status, no signals |
| 1 | PERSONA | COMPLETE + People PASS |
| 2 | TRIGGER | COMPLETE + Blog signals |
| 3 | AGGRESSIVE | COMPLETE + BIT >= 50 |

### Safety Enforcement

| Rule | Behavior |
|------|----------|
| effective_tier = -1 | HARD_FAIL (no sends) |
| marketing_disabled = true | HARD_FAIL (no sends) |
| has_active_override (blocking) | HARD_FAIL (no sends) |
| No data in authoritative view | HARD_FAIL (fail closed) |

---

## Files With DO NOT MODIFY Banners

The following files contain DO NOT MODIFY banners at the top:

1. `infra/migrations/2026-01-19-kill-switches.sql`
2. `infra/migrations/2026-01-20-tier-telemetry-views.sql`
3. `infra/migrations/2026-01-20-send-attempt-audit.sql`
4. `hubs/outreach-execution/imo/middle/marketing_safety_gate.py`

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-20 | Doctrine Freeze Agent | Initial v1.0 baseline freeze |

---

**Classification**: FROZEN REGISTRY
**Modification Authority**: CHANGE REQUEST REQUIRED

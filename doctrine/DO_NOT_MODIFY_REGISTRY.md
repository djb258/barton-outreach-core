# DO NOT MODIFY REGISTRY
## v1.0 Operational Baseline + BIT v2.0 Distributed Signals - Frozen Components

**Version**: 1.2.1
**Freeze Date**: 2026-01-26
**Status**: FROZEN
**Reference**: docs/GO-LIVE_STATE_v1.0.md, docs/adr/ADR-017_BIT_Authorization_System_Migration.md
**CTB Governance**: [docs/CTB_GOVERNANCE.md](../docs/CTB_GOVERNANCE.md)

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
5. `neon/migrations/2026-01-25-bit-v2-phase1-schema.sql`

---

## BIT AUTHORIZATION SYSTEM v2.0 - DISTRIBUTED SIGNALS (FROZEN)

**Authority**: ADR-017
**Freeze Date**: 2026-01-26
**Migration**: neon/migrations/2026-01-26-bit-v2-phase1-distributed-signals.sql

### Architecture Principle (FROZEN)

```
Each sub-hub OWNS its own signal table.
Company Target OWNS a read-only view that unions all signal tables.
BIT is a COMPUTATION inside Company Target that reads the view.
```

### Distributed Signal Tables (Structure Frozen)

| Component | Schema | Freeze Type | Rationale |
|-----------|--------|-------------|-----------|
| `dol.pressure_signals` | dol | Structure | DOL owns STRUCTURAL_PRESSURE signals |
| `people.pressure_signals` | people | Structure | People owns DECISION_SURFACE signals |
| `blog.pressure_signals` | blog | Structure | Blog owns NARRATIVE_VOLATILITY signals |

### Signal Table Contract (FROZEN)

All signal tables MUST implement this structure:

| Column | Type | Required | Purpose |
|--------|------|----------|---------|
| `signal_id` | UUID | Yes | Primary key |
| `company_unique_id` | TEXT | Yes | Company reference |
| `signal_type` | VARCHAR(50) | Yes | Signal classification |
| `pressure_domain` | ENUM | Yes | STRUCTURAL_PRESSURE, DECISION_SURFACE, NARRATIVE_VOLATILITY |
| `pressure_class` | ENUM | No | Pressure classification |
| `signal_value` | JSONB | Yes | Domain-specific payload |
| `magnitude` | INTEGER | Yes | Impact score (0-100) |
| `detected_at` | TIMESTAMPTZ | Yes | When signal was detected |
| `expires_at` | TIMESTAMPTZ | Yes | Validity window end |
| `correlation_id` | UUID | No | Trace ID |
| `source_record_id` | TEXT | No | Traceability |

### Company Target Components (FROZEN)

| Component | Freeze Type | Rationale |
|-----------|-------------|-----------|
| `company_target.vw_all_pressure_signals` | View | Union of all signal tables — BIT reads from here |
| `company_target.compute_authorization_band(TEXT)` | Signature | BIT computation contract — callers depend on this |

**Function internals NOT frozen**: Logic can evolve as long as signature and return type unchanged

### Band Definitions (Logic Frozen)

| Band | Range | Name | Meaning |
|------|-------|------|---------|
| 0 | 0-9 | SILENT | No action permitted |
| 1 | 10-24 | WATCH | Internal flag only |
| 2 | 25-39 | EXPLORATORY | Educational content only |
| 3 | 40-59 | TARGETED | Persona email, proof required |
| 4 | 60-79 | ENGAGED | Phone allowed, multi-source proof |
| 5 | 80+ | DIRECT | Full contact, full-chain proof |

### Domain Trust Rules (Logic Frozen)

| Rule | Behavior |
|------|----------|
| Blog alone | Max Band 1 (WATCH) |
| No DOL present | Max Band 2 (EXPLORATORY) |
| Band 3+ without proof | HARD_FAIL (no send) |
| Expired proof | HARD_FAIL (no send) |
| Insufficient proof band | HARD_FAIL (no send) |

### Bridge Adapters (NOT Frozen)

| Component | Purpose |
|-----------|---------|
| `people.bridge_talent_flow_movement()` | Converts talent_flow.movements → people.pressure_signals |
| `dol.bridge_renewal_calendar()` | Converts dol.renewal_calendar → dol.pressure_signals |

**Bridge adapters can evolve** — they adapt legacy data to new signal format

### NOT Frozen (Explicitly)

| Component | Reason |
|-----------|--------|
| `company_target.vw_company_authorization` | Convenience view, can change |
| Bridge adapter functions | Adaptation layer, can evolve |
| All indexes | Optimization allowed |
| Enum types | Additive changes allowed (new values) |

### DEPRECATED (from v1.1.0)

The following centralized components from the initial Phase 1 design are **DEPRECATED**:

| Component | Status | Reason |
|-----------|--------|--------|
| `bit.movement_events` | DEPRECATED | Replaced by distributed signal tables |
| `bit.proof_lines` | DEPRECATED | Phase 2 concern |
| `bit.phase_state` | DEPRECATED | Replaced by compute_authorization_band() |
| `bit.authorization_log` | DEPRECATED | Phase 2 concern |
| `bit.get_current_band()` | DEPRECATED | Replaced by company_target.compute_authorization_band() |
| `bit.authorize_action()` | DEPRECATED | Phase 2 concern |
| `bit.validate_proof_for_send()` | DEPRECATED | Phase 2 concern |

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-20 | Doctrine Freeze Agent | Initial v1.0 baseline freeze |
| 1.1.0 | 2026-01-25 | ADR-017 | BIT Authorization System v2.0 centralized design (DEPRECATED) |
| 1.2.0 | 2026-01-26 | ADR-017 | BIT v2.0 distributed signals architecture (CURRENT) |

---

## Change Log: v1.2.0

**Architecture Correction:**
- Replaced centralized `bit.*` design with distributed signal tables
- Each hub now owns its own `pressure_signals` table
- Company Target owns union view and BIT computation

**Added:**
- `dol.pressure_signals` table (structure frozen)
- `people.pressure_signals` table (structure frozen)
- `blog.pressure_signals` table (structure frozen)
- `company_target.vw_all_pressure_signals` view (structure frozen)
- `company_target.compute_authorization_band()` function (signature frozen)
- Bridge adapters for Talent Flow and DOL Renewal Calendar

**Deprecated:**
- All `bit.*` tables from v1.1.0 (centralized design was incorrect)
- `bit.get_current_band()` → use `company_target.compute_authorization_band()`

**Unchanged:**
- All v1.0 frozen components remain frozen
- Band definitions (0-5) unchanged
- Domain trust rules unchanged
- Marketing Safety Gate unchanged
- Kill switch system unchanged
- Tier logic unchanged (coexists with band system during transition)

---

**Classification**: FROZEN REGISTRY
**Modification Authority**: CHANGE REQUEST REQUIRED

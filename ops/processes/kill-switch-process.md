# Process Declaration: Kill Switch System

> **Note (2026-02-20)**: Some tables referenced in this document were dropped during database consolidation (all had 0 rows). See `doctrine/DO_NOT_MODIFY_REGISTRY.md` for the complete list of dropped tables and their migration sources. Affected tables: `outreach.manual_overrides`, `outreach.override_audit_log`.

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | IMO-Creator v1.0 |
| **Domain Spec Reference** | `doctrine/REPO_DOMAIN_SPEC.md` |
| **CC Layer** | CC-04 (Process) |
| **Process Doctrine** | `templates/doctrine/PROCESS_DOCTRINE.md` |

---

## Process Identity

| Field | Value |
|-------|-------|
| **Hub ID** | HUB-KILL-SWITCH |
| **Process Type** | Governance Process |
| **Version** | 1.0.0 |

---

## Process ID Pattern

```
kill-switch-${PROCESS_TYPE}-${TIMESTAMP}-${RANDOM_HEX}
```

### Process Types

| Type | Description | Example |
|------|-------------|---------|
| `disable` | Marketing disable | `kill-switch-disable-20260129-a1b2c3d4` |
| `enable` | Marketing re-enable | `kill-switch-enable-20260129-b2c3d4e5` |
| `cap` | Tier cap | `kill-switch-cap-20260129-c3d4e5f6` |
| `expire` | Override expiration | `kill-switch-expire-20260129-d4e5f6a7` |

---

## Constants Consumed

_Reference: `docs/prd/PRD_KILL_SWITCH_SYSTEM.md §3 Constants`_

| Constant | Source | Description |
|----------|--------|-------------|
| `marketing_eligibility` | Sovereign Completion | Computed marketing tier |
| `override_request` | Human operators | Override creation request |
| `outreach_id` | Outreach Spine | Target company identifier |

---

## Variables Produced

_Reference: `docs/prd/PRD_KILL_SWITCH_SYSTEM.md §3 Variables`_

| Variable | Destination | Description |
|----------|-------------|-------------|
| `active_override` | manual_overrides | Active marketing override |
| `effective_tier` | Eligibility views | Effective tier with overrides |
| `audit_record` | override_audit_log | Audit trail entry |

---

## Governing PRD

| Field | Value |
|-------|-------|
| **PRD** | `docs/prd/PRD_KILL_SWITCH_SYSTEM.md` |
| **PRD Version** | 2.0.0 |

---

## Pass Ownership

| Pass | IMO Layer | Description |
|------|-----------|-------------|
| **CAPTURE** | I (Ingress) | Receive disable/enable override requests |
| **COMPUTE** | M (Middle) | Process override creation, TTL expiration |
| **GOVERN** | O (Egress) | Output effective tier with overrides applied |

---

## Override Types

| Type | Effect | Use Case |
|------|--------|----------|
| `marketing_disabled` | Tier = -1 | Complete blackout |
| `tier_cap` | Tier = min(computed, cap) | Limited outreach |
| `hub_bypass` | Skip specific hub | Testing/debugging |
| `cooldown` | Tier = -1 temporarily | Post-outreach pause |
| `legal_hold` | Tier = -1 | Legal/compliance |
| `customer_requested` | Tier = -1 | Opt-out request |

---

## Functions (Deterministic)

| Function | Type | IMO Layer |
|----------|------|-----------|
| fn_disable_marketing | Procedure | M |
| fn_enable_marketing | Procedure | M |
| fn_set_tier_cap | Procedure | M |
| fn_expire_overrides | Procedure | M |

---

## Human Override Rules

| Role | Can Create | Override Types |
|------|------------|----------------|
| Hub Owner | Yes | All types |
| Legal Team | Yes | legal_hold |
| Customer Service | Yes | customer_requested, cooldown |
| Marketing Ops | Yes | marketing_disabled, tier_cap |

---

## Data Model

### manual_overrides

| Column | Type | Description |
|--------|------|-------------|
| override_id | UUID | Primary key |
| company_unique_id | TEXT | Target company |
| override_type | ENUM | Type of override |
| reason | TEXT | Human-readable reason |
| metadata | JSONB | Additional data (tier_cap, etc.) |
| expires_at | TIMESTAMPTZ | TTL (NULL = permanent) |
| is_active | BOOLEAN | Soft delete flag |
| created_at | TIMESTAMPTZ | Creation time |
| created_by | TEXT | Creator |

### override_audit_log

| Column | Type | Description |
|--------|------|-------------|
| audit_id | UUID | Primary key |
| company_unique_id | TEXT | Target company |
| override_id | UUID | Related override |
| action | TEXT | CREATED, UPDATED, EXPIRED, DELETED |
| old_value | JSONB | Previous state |
| new_value | JSONB | New state |
| performed_by | TEXT | Actor |
| performed_at | TIMESTAMPTZ | Timestamp |

---

## Error Codes

| Code | Severity | Description |
|------|----------|-------------|
| `KS-001` | CRITICAL | RLS bypass attempted |
| `KS-002` | CRITICAL | Override not applied (view join failed) |
| `KS-003` | HIGH | Audit gap (trigger failed) |
| `KS-004` | MEDIUM | TTL not expiring (job failed) |

---

## Security (RLS)

| Table | Policy | Effect |
|-------|--------|--------|
| manual_overrides | owner_policy | Full access for owner role |
| override_audit_log | owner_policy | Full access for owner role |
| override_audit_log | read_policy | Read access for all |

---

## Doctrine Requirement

> "Kill switches MUST be implemented BEFORE UI. No visual bypass possible."

The kill switch system is data-layer enforcement. All marketing eligibility queries MUST go through `vw_marketing_eligibility_with_overrides`.

---

## Correlation ID Enforcement

- `correlation_id` from override request
- Included in all audit records
- Enables tracing override lifecycle

---

## Structural Bindings

| Binding Type | Reference |
|--------------|-----------|
| **Governing PRD** | `docs/prd/PRD_KILL_SWITCH_SYSTEM.md` |
| **Tables READ** | `outreach.outreach`, `vw_marketing_eligibility` |
| **Tables WRITTEN** | `outreach.manual_overrides`, `outreach.override_audit_log` |
| **Views AFFECTED** | `vw_marketing_eligibility_with_overrides` |
| **Pass Participation** | CAPTURE → COMPUTE → GOVERN |
| **ERD Reference** | `docs/ERD_SUMMARY.md §Authoritative Pass Ownership` |

---

**Created**: 2026-01-29
**Version**: 1.0.0

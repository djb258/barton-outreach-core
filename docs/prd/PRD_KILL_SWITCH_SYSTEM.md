# PRD - Kill Switch System v2.0

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | IMO-Creator v1.0 |
| **Domain Spec Reference** | `doctrine/REPO_DOMAIN_SPEC.md` |
| **CC Layer** | CC-02 |
| **PRD Constitution** | `templates/doctrine/PRD_CONSTITUTION.md` |
| **CTB Governance** | `docs/CTB_GOVERNANCE.md` |

---

## 1. Sovereign Reference (CC-01)

| Field | Value |
|-------|-------|
| **Sovereign ID** | CL-01 (Company Lifecycle) |
| **Sovereign Boundary** | Company identity and lifecycle state |

---

## 2. Hub Identity (CC-02)

| Field | Value |
|-------|-------|
| **Hub Name** | Kill Switch System |
| **Hub ID** | HUB-KILL-SWITCH |
| **Owner** | Barton Outreach Core |
| **Version** | 2.0.0 |

---

## 3. Purpose & Transformation Declaration

### Transformation Statement (REQUIRED)

> **"This system transforms marketing eligibility states and override requests (CONSTANTS) into enforced marketing restrictions with audit trails (VARIABLES) through CAPTURE (override request intake), COMPUTE (override management and TTL processing), and GOVERN (effective tier enforcement with RLS protection)."**

| Field | Value |
|-------|-------|
| **Transformation Summary** | Override requests → Enforced marketing restrictions with audit |

### Constants (Inputs)

_Immutable inputs received from outside this system. Reference: `doctrine/REPO_DOMAIN_SPEC.md §2`_

| Constant | Source | Description |
|----------|--------|-------------|
| `marketing_eligibility` | Sovereign Completion | Computed marketing tier |
| `override_request` | Human operators | Override creation request |
| `outreach_id` | Outreach Spine | Target company identifier |

### Variables (Outputs)

_Outputs this system produces. Reference: `doctrine/REPO_DOMAIN_SPEC.md §3`_

| Variable | Destination | Description |
|----------|-------------|-------------|
| `active_override` | manual_overrides | Active marketing override |
| `effective_tier` | Eligibility views | Effective marketing tier with overrides |
| `audit_record` | override_audit_log | Audit trail entry |

### Pass Structure

_Constitutional pass mapping per `PRD_CONSTITUTION.md §Pass-to-IMO Mapping`_

| Pass | Type | IMO Layer | Description |
|------|------|-----------|-------------|
| Override Intake | **CAPTURE** | I (Ingress) | Receive disable/enable override requests |
| Override Management | **COMPUTE** | M (Middle) | Process override creation, TTL expiration |
| Tier Enforcement | **GOVERN** | O (Egress) | Output effective tier with overrides applied |

### Scope Boundary

| Scope | Description |
|-------|-------------|
| **IN SCOPE** | Override creation, override expiration, effective tier computation, audit logging |
| **OUT OF SCOPE** | Marketing tier computation (Sovereign Completion owns), outreach decisions (Outreach Execution owns) |

---

## 4. Purpose

The Kill Switch System provides data-layer enforcement for marketing restrictions:

1. **Marketing Blackout** - Completely prevent marketing to specific companies
2. **Tier Capping** - Limit marketing intensity without full disable
3. **Cooldown Periods** - Temporary pauses with automatic expiration
4. **Legal Holds** - Compliance-driven freezes
5. **Customer Opt-outs** - Honor explicit customer requests

**Doctrine Requirement:** "Kill switches MUST be implemented BEFORE UI. No visual bypass possible."

---

## 4. CTB Placement

| Field | Value | CC Layer |
|-------|-------|----------|
| **Trunk** | sys | CC-02 |
| **Branch** | outreach | CC-02 |
| **Leaf** | kill-switch | CC-02 |

---

## 5. IMO Structure (CC-02)

| Layer | Role | Description | CC Layer |
|-------|------|-------------|----------|
| **I — Ingress** | Override requests | Receives disable/enable requests | CC-02 |
| **M — Middle** | Override management | Manages active overrides | CC-02 |
| **O — Egress** | Effective tier | Outputs effective tier with overrides applied | CC-02 |

---

## 6. Spokes (CC-03 Interfaces)

| Spoke Name | Type | Direction | Contract | CC Layer |
|------------|------|-----------|----------|----------|
| override-request | I | Inbound | Override creation | CC-03 |
| effective-tier | O | Outbound | Effective marketing tier | CC-03 |

---

## 7. Constants vs Variables

| Element | Type | Mutability | CC Layer |
|---------|------|------------|----------|
| Override Types | Constant | Immutable | CC-02 |
| Blocking Override Types | Constant | Immutable | CC-02 |
| Audit Log Schema | Constant | ADR-gated | CC-02 |
| TTL Expiration Logic | Constant | ADR-gated | CC-02 |

---

## 8. Tools

| Tool | Solution Type | CC Layer | IMO Layer | ADR Reference |
|------|---------------|----------|-----------|---------------|
| fn_disable_marketing | Deterministic | CC-02 | M | ADR-007 |
| fn_enable_marketing | Deterministic | CC-02 | M | ADR-007 |
| fn_set_tier_cap | Deterministic | CC-02 | M | ADR-007 |
| fn_expire_overrides | Deterministic | CC-02 | M | ADR-007 |

---

## 9. Guard Rails

| Guard Rail | Type | Threshold | CC Layer |
|------------|------|-----------|----------|
| RLS Enforcement | Security | Owner role only | CC-03 |
| Audit Immutability | Data Integrity | Append-only | CC-02 |
| TTL Validation | Business Rule | expires_at > now() | CC-02 |

---

## 10. Kill Switch

| Field | Value |
|-------|-------|
| **Activation Criteria** | This IS the kill switch system |
| **Trigger Authority** | CC-02 (Hub) / CC-01 (Sovereign) |
| **Emergency Contact** | Hub Owner, Legal Team |

---

## 11. Promotion Gates

| Gate | Artifact | CC Layer | Requirement |
|------|----------|----------|-------------|
| G1 | PRD | CC-02 | Hub definition approved |
| G2 | ADR | CC-03 | ADR-007 accepted |
| G3 | Work Item | CC-04 | Migration deployment |
| G4 | PR | CC-04 | Code reviewed and merged |
| G5 | Checklist | CC-04 | Security hardening complete |

---

## 12. Failure Modes

| Failure | Severity | CC Layer | Remediation |
|---------|----------|----------|-------------|
| RLS bypass | Critical | CC-02 | Verify policies active |
| Override not applied | Critical | CC-02 | Check view joins |
| Audit gap | High | CC-02 | Trigger verification |
| TTL not expiring | Medium | CC-02 | Run fn_expire_overrides |

---

## 13. PID Scope (CC-04)

| Field | Value |
|-------|-------|
| **PID Pattern** | `kill-switch-${TIMESTAMP}-${RANDOM_HEX}` |
| **Retry Policy** | New PID per operation |
| **Audit Trail** | Required (override_audit_log) |

---

## 14. Human Override Rules

| Role | Can Create | Override Types |
|------|------------|----------------|
| Hub Owner | Yes | All types |
| Legal Team | Yes | legal_hold |
| Customer Service | Yes | customer_requested, cooldown |
| Marketing Ops | Yes | marketing_disabled, tier_cap |

---

## 15. Observability

| Type | Description | CC Layer |
|------|-------------|----------|
| **Logs** | All changes in override_audit_log | CC-04 |
| **Metrics** | Active override count by type | CC-04 |
| **Alerts** | Override creation, legal holds | CC-03 |

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

## Data Model

### Tables

| Table | Purpose | Row Count |
|-------|---------|-----------|
| manual_overrides | Active overrides | Variable |
| override_audit_log | Audit trail | Append-only |

### Columns - manual_overrides

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

### Columns - override_audit_log

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

## Security

### Row-Level Security

| Table | Policy | Effect |
|-------|--------|--------|
| manual_overrides | owner_policy | Full access for owner role |
| override_audit_log | owner_policy | Full access for owner role |
| override_audit_log | read_policy | Read access for all |

### Roles

| Role | Permissions |
|------|-------------|
| Marketing DB_owner | Full access to both tables |
| authenticated | Read audit log |
| public | Read audit log |

---

## Approval

| Role | Name | Date |
|------|------|------|
| Sovereign (CC-01) | Barton Enterprises | 2026-01-19 |
| Hub Owner (CC-02) | Outreach Core | 2026-01-19 |
| Reviewer | Claude Code | 2026-01-19 |

---

## Traceability

| Artifact | Reference |
|----------|-----------|
| Canonical Doctrine | CANONICAL_ARCHITECTURE_DOCTRINE.md |
| Hub/Spoke Doctrine | HUB_SPOKE_ARCHITECTURE.md |
| ADR | ADR-007_Kill_Switch_System.md |
| PRD | PRD_SOVEREIGN_COMPLETION.md |

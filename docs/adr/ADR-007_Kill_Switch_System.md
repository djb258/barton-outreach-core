# ADR: Kill Switch System

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | CL Parent-Child Doctrine v1.1 |
| **CC Layer** | CC-02 |

---

## ADR Identity

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-007 |
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
| CC-02 (Hub) | [x] | Kill switch table and enforcement |
| CC-03 (Context) | [x] | Override view and RLS policies |
| CC-04 (Process) | [x] | Audit logging |

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
| **Mutability** | [x] Immutable (override types are fixed) |

---

## Context

Marketing automation must have a mechanism to:

1. Prevent marketing to specific companies regardless of computed eligibility
2. Cap marketing tier for companies with restrictions
3. Implement cooldown periods after outreach
4. Honor legal holds and customer opt-outs
5. Provide full audit trail for compliance

Doctrine requires: "Kill switches MUST be implemented BEFORE UI. No visual bypass possible - data layer enforcement."

---

## Decision

Implement a **Kill Switch System** consisting of:

1. **Override Type Enum** (`outreach.override_type_enum`)
   - `marketing_disabled` - Complete marketing blackout
   - `tier_cap` - Cap to specific tier
   - `hub_bypass` - Skip specific hub
   - `cooldown` - Temporary pause
   - `legal_hold` - Legal/compliance freeze
   - `customer_requested` - Customer opt-out

2. **Manual Overrides Table** (`outreach.manual_overrides`)
   - Company-level overrides
   - TTL support via `expires_at`
   - Soft delete via `is_active` flag
   - Metadata JSONB for tier caps, etc.

3. **Override Audit Log** (`outreach.override_audit_log`)
   - Append-only audit trail
   - Tracks CREATED, UPDATED, EXPIRED, DELETED actions
   - Never delete from this table

4. **Row-Level Security**
   - RLS enabled on both tables
   - Owner policy for write access
   - Read policy for audit visibility

5. **Helper Functions**
   - `fn_disable_marketing(company_id, reason, expires_at)`
   - `fn_enable_marketing(company_id, reason)`
   - `fn_set_tier_cap(company_id, max_tier, reason, expires_at)`
   - `fn_expire_overrides()` - TTL expiration

---

## Alternatives Considered

| Option | Why Not Chosen |
|--------|----------------|
| Application-level blocking | Can be bypassed; no audit trail |
| Database triggers on send_log | Reactive, not preventive |
| Separate blocklist service | Too much complexity; latency |
| Do Nothing | Doctrine violation; compliance risk |

---

## Consequences

### Enables

- Data-layer enforcement (cannot be bypassed)
- Full audit trail for compliance
- TTL-based temporary disablements
- Tier capping without full disable
- Legal hold support

### Prevents

- UI bypass of marketing restrictions
- Marketing to opted-out companies
- Marketing during legal holds
- Audit trail gaps
- Accidental marketing to restricted companies

---

## PID Impact (if CC-04 affected)

| Field | Value |
|-------|-------|
| **New PID required** | [x] No |
| **PID pattern change** | [x] No |
| **Audit trail impact** | All overrides logged to override_audit_log |

---

## Guard Rails

| Type | Value | CC Layer |
|------|-------|----------|
| Rate Limit | N/A | |
| Timeout | TTL via expires_at | CC-02 |
| Kill Switch | This IS the kill switch | CC-02 |

---

## Rollback

1. Disable RLS:
   ```sql
   ALTER TABLE outreach.manual_overrides DISABLE ROW LEVEL SECURITY;
   ALTER TABLE outreach.override_audit_log DISABLE ROW LEVEL SECURITY;
   ```

2. Drop policies:
   ```sql
   DROP POLICY IF EXISTS manual_overrides_owner_policy ON outreach.manual_overrides;
   DROP POLICY IF EXISTS override_audit_owner_policy ON outreach.override_audit_log;
   DROP POLICY IF EXISTS override_audit_read_policy ON outreach.override_audit_log;
   ```

3. Drop tables:
   ```sql
   DROP TABLE outreach.override_audit_log;
   DROP TABLE outreach.manual_overrides;
   ```

4. Drop enum:
   ```sql
   DROP TYPE outreach.override_type_enum;
   ```

Note: Rollback will lose all override history - export first!

---

## Traceability

| Artifact | Reference |
|----------|-----------|
| Canonical Doctrine | CANONICAL_ARCHITECTURE_DOCTRINE.md |
| PRD | docs/prd/PRD_KILL_SWITCH_SYSTEM.md |
| Work Items | Kill Switch Security Hardening |
| PR(s) | PR: Sovereign Completion Infrastructure v1.1.0 |
| Migration | migrations/2026-01-19-kill-switches.sql |

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner (CC-02) | Barton Enterprises | 2026-01-19 |
| Reviewer | Claude Code | 2026-01-19 |

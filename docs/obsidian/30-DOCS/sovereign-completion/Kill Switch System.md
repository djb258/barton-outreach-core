# Kill Switch System

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | CL Parent-Child Doctrine v1.1 |
| **CC Layer** | CC-02 (Hub) |

---

## Hub Identity

| Field | Value |
|-------|-------|
| **Sovereign ID** | barton-enterprises |
| **Hub Name** | Kill Switch System |
| **Hub ID** | 04.04.02.04.KS |

---

## Purpose

The Kill Switch System provides **data-layer enforcement** for marketing restrictions. It ensures that:

1. No company receives marketing if they have an active override
2. Overrides cannot be bypassed through the UI
3. Full audit trail exists for compliance

**Doctrine Requirement:** "Kill switches MUST be implemented BEFORE UI. No visual bypass possible."

---

## Override Types

| Type | Effect | Use Case |
|------|--------|----------|
| `marketing_disabled` | Tier = -1 | Complete marketing blackout |
| `tier_cap` | Tier = min(computed, cap) | Limited outreach intensity |
| `hub_bypass` | Skip specific hub | Testing/debugging |
| `cooldown` | Tier = -1 temporarily | Post-outreach pause |
| `legal_hold` | Tier = -1 | Legal/compliance freeze |
| `customer_requested` | Tier = -1 | Customer opt-out |

---

## Architecture

```
manual_overrides (kill switch table)
        │
        │ RLS: ENABLED
        │ Policy: owner_policy (Marketing DB_owner only)
        │
        ├──► vw_marketing_eligibility_with_overrides
        │         │
        │         ▼
        │    effective_tier (overrides applied)
        │
        └──► override_audit_log (append-only)
                  │
                  │ RLS: ENABLED
                  │ Policies: owner_policy, read_policy
                  │
                  ▼
             IMMUTABLE AUDIT TRAIL
```

---

## Key Tables

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

### override_audit_log

| Column | Type | Description |
|--------|------|-------------|
| audit_id | UUID | Primary key |
| action | TEXT | CREATED, UPDATED, EXPIRED, DELETED |
| old_value | JSONB | Previous state |
| new_value | JSONB | New state |
| performed_by | TEXT | Who made the change |
| performed_at | TIMESTAMPTZ | When |

---

## Usage

### Disable marketing for a company

```sql
SELECT outreach.fn_disable_marketing(
    'company-unique-id',
    'Customer requested opt-out',
    NULL  -- NULL = permanent, or pass a timestamp for TTL
);
```

### Re-enable marketing

```sql
SELECT outreach.fn_enable_marketing(
    'company-unique-id',
    'Customer opted back in'
);
```

### Set tier cap

```sql
SELECT outreach.fn_set_tier_cap(
    'company-unique-id',
    1,  -- Max tier
    'Limited outreach per account manager',
    '2026-06-01'::timestamptz  -- Expires June 1
);
```

### Check active overrides

```sql
SELECT * FROM outreach.manual_overrides
WHERE is_active = TRUE
AND (expires_at IS NULL OR expires_at > NOW());
```

### View audit trail

```sql
SELECT * FROM outreach.override_audit_log
WHERE company_unique_id = 'company-unique-id'
ORDER BY performed_at DESC;
```

---

## Security

### Row-Level Security

| Table | Policy | Effect |
|-------|--------|--------|
| manual_overrides | owner_policy | Only owner can write |
| override_audit_log | owner_policy | Only owner can write |
| override_audit_log | read_policy | Anyone can read |

### Who Can Create Overrides?

| Role | Override Types |
|------|----------------|
| Hub Owner | All types |
| Legal Team | legal_hold |
| Customer Service | customer_requested, cooldown |
| Marketing Ops | marketing_disabled, tier_cap |

---

## TTL Expiration

Overrides with `expires_at` set will automatically become inactive when the timestamp passes.

Run expiration manually:
```sql
SELECT outreach.fn_expire_overrides();
```

Set up a cron job to run this periodically.

---

## Related Documentation

- [[Sovereign Completion Overview]]
- [[ADR-007_Kill_Switch_System]]
- [[PRD_KILL_SWITCH_SYSTEM]]

---

## Tags

#hub/kill-switch #cc/cc-02 #status/active #type/system

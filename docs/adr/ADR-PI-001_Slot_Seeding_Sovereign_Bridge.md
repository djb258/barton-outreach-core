# ADR-PI-001: People Slot Bulk Seeding via Sovereign Bridge

**Status:** ACCEPTED  
**Date:** 2026-01-09  
**Deciders:** Architecture Team  
**Technical Story:** People Slot Infrastructure Seeding

## Context and Problem Statement

People Intelligence requires CEO/CFO/HR slots for all outreach-ready companies. The challenge was discovering the correct data path from `outreach_id` to a valid `company_unique_id` that satisfies the foreign key constraint to `company.company_master`.

Initial attempts failed because:
- `outreach.company_target.company_unique_id` is UUID format
- `company.company_master.company_unique_id` is string format (`04.04.01.xx.xxxxx.xxx`)
- These are **different ID systems** — not interchangeable

## Decision Drivers

1. **FK Constraint Compliance**: `people.company_slot.company_unique_id` → `company.company_master.company_unique_id`
2. **Unique Constraints**: Both `(outreach_id, slot_type)` and `(company_unique_id, slot_type)` must be unique
3. **Zero-Touch Safety**: No writes to `people_master`, `people_candidate`, or ingress control
4. **Performance**: 63,911 outreach_ids × 3 slot types = ~191k inserts needed

## Considered Options

1. **Domain-based lookup** (`outreach.domain` → `company_master.website_url` via ILIKE)
2. **Company Target UUID** (direct use of `company_target.company_unique_id`)
3. **Sovereign Bridge** (`outreach.sovereign_id` → `cl.company_identity_bridge` → `source_company_id`)

## Decision Outcome

**Chosen option:** "Sovereign Bridge"

### The Canonical Path

```
outreach.outreach.sovereign_id
    ↓ JOIN
cl.company_identity_bridge.company_sov_id
    ↓ SELECT
cl.company_identity_bridge.source_company_id  (format: 04.04.01.xx.xxxxx.xxx)
    ↓ FK VALIDATED
company.company_master.company_unique_id
```

### Why This Works

| Step | Table | Column | Format |
|------|-------|--------|--------|
| 1 | `outreach.outreach` | `sovereign_id` | UUID |
| 2 | `cl.company_identity_bridge` | `company_sov_id` | UUID (matches step 1) |
| 3 | `cl.company_identity_bridge` | `source_company_id` | `04.04.01.xx` string |
| 4 | `company.company_master` | `company_unique_id` | `04.04.01.xx` string (FK target) |

### Validation Results

```sql
-- 100% mapping coverage
SELECT COUNT(DISTINCT o.outreach_id)
FROM outreach.outreach o
JOIN cl.company_identity_bridge b ON b.company_sov_id = o.sovereign_id
JOIN company.company_master cm ON cm.company_unique_id = b.source_company_id;
-- Result: 63,911 (all outreach_ids mappable)
```

## Positive Consequences

- **100% coverage**: All 63,911 outreach_ids can be mapped
- **FK valid**: All generated slots pass FK constraint
- **Fast execution**: Single INSERT per slot type (~2 seconds each)
- **Idempotent**: `ON CONFLICT DO NOTHING` prevents duplicates

## Negative Consequences

- Requires `cl.company_identity_bridge` to exist (populated by CL pipeline)
- If bridge is incomplete, some outreach_ids won't get slots

## Explicit Rejections

| Approach | Rejection Reason |
|----------|------------------|
| Domain ILIKE lookup | Slow (no index), partial matches, ~10min+ |
| company_target.company_unique_id | Wrong ID format (UUID vs 04.04.xx) |
| Template company_id | Violates UNIQUE(company_unique_id, slot_type) |
| Generate 04.04.xx format | No FK guarantee to company_master |

## Technical Implementation

### Final Insert Query

```sql
INSERT INTO people.company_slot (
    company_slot_unique_id,
    company_unique_id,
    outreach_id,
    slot_type,
    slot_status,
    canonical_flag,
    creation_reason,
    created_at
)
SELECT 
    gen_random_uuid()::text,
    cm.company_unique_id,
    o.outreach_id,
    :slot_type,
    'open',
    TRUE,
    'bulk_seed',
    NOW()
FROM outreach.outreach o
JOIN cl.company_identity_bridge b ON b.company_sov_id = o.sovereign_id
JOIN company.company_master cm ON cm.company_unique_id = b.source_company_id
WHERE NOT EXISTS (
    SELECT 1 FROM people.company_slot cs 
    WHERE cs.outreach_id = o.outreach_id AND cs.slot_type = :slot_type
)
AND NOT EXISTS (
    SELECT 1 FROM people.company_slot cs2
    WHERE cs2.company_unique_id = cm.company_unique_id AND cs2.slot_type = :slot_type
);
```

### Execution Results (2026-01-09)

| Metric | Value |
|--------|-------|
| CEO slots inserted | 63,483 |
| CFO slots inserted | 63,483 |
| HR slots inserted | 63,483 |
| **Total inserted** | **190,449** |
| Unique outreach_ids | 63,585 |
| people_master delta | 0 ✓ |
| Kill switch | OFF ✓ |

## References

- Migration: `src/data/migrations/2026-01-08-people-slot-structure.sql`
- Script: `ops/scripts/people_slot_bulk_seed_v2.py`
- PRD: `docs/prd/PRD_PEOPLE_SUBHUB.md`

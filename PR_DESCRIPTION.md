# PR: DOL Subhub — Violation Discovery (Fact Storage)

## Summary

Adds violation discovery capability to the DOL Subhub. This enables:
1. Pull violator data from DOL sources (OSHA, EBSA, WHD, OFCCP)
2. Match violations to existing EIN linkages
3. Store violation facts for downstream outreach

**This is FACT STORAGE ONLY — no scoring, no outreach triggers in DOL.**

---

## Changes

### New Files

| File | Purpose |
|------|---------|
| `ctb/sys/dol-ein/findViolations.js` | Violation discovery + EIN matching |
| `doctrine/schemas/dol_violations-schema.sql` | Violations table + views |
| `ctb/docs/tasks/hub_tasks.md` | Task checklist |

### Updated Files

| File | Changes |
|------|---------|
| `doctrine/ple/DOL_EIN_RESOLUTION.md` | Added Section 12: Violation Discovery |
| `ctb/docs/prd/PRD-DOL-EIN-FUZZY-FILING-DISCOVERY.md` | Added Part 2: Violation Discovery requirements |
| `ctb/docs/adr/ADR-DOL-FUZZY-BOUNDARY.md` | Added Part 2: Violation architecture decision |

---

## Violation Architecture

```
DOL Sources (OSHA, EBSA, WHD, OFCCP)
        ↓
findViolations.js
  ├─ normalizeViolation() → Standard schema
  ├─ matchViolationToEIN() → Link to ein_linkage
  │
  └─ Result
        ├─ MATCHED → INSERT dol.violations
        │     ↓
        │   dol.v_companies_with_violations
        │     ↓
        │   Downstream Outreach (reads facts)
        │
        └─ UNMATCHED → Log for enrichment
```

---

## Views for Outreach Targeting

| View | What It Shows |
|------|---------------|
| `dol.v_companies_with_violations` | Companies with **open/contested** violations |
| `dol.v_violation_summary` | Aggregate stats (total, penalties, severity) |
| `dol.v_recent_violations` | Last 90 days — prioritize for outreach |

---

## Source Agencies Supported

| Agency | Description | Data Source |
|--------|-------------|-------------|
| OSHA | Workplace safety violations | enforcedata.dol.gov |
| EBSA | Benefits plan violations (ERISA) | dol.gov/agencies/ebsa |
| WHD | Wage and hour violations (FLSA, FMLA) | dol.gov/agencies/whd |
| OFCCP | Federal contractor compliance | dol.gov/agencies/ofccp |
| MSHA | Mine safety violations | msha.gov |

---

## Boundary Enforcement

### DOL Subhub DOES
- ✅ Discover violations from DOL sources
- ✅ Match violations to existing EIN
- ✅ Store violations as facts
- ✅ Provide views for downstream

### DOL Subhub DOES NOT
- ❌ Score violations
- ❌ Trigger outreach
- ❌ Create EIN linkages from violations
- ❌ Modify violation records

---

## Testing Checklist

- [x] Violation normalization handles all source agencies
- [x] EIN matching links to existing ein_linkage records
- [x] Invalid EINs are filtered out
- [x] Batch processing returns correct stats
- [x] Views created in schema
- [ ] Schema deployed to Neon PostgreSQL
- [ ] DOL source integrations connected

---

## Related Documents

- [DOL_EIN_RESOLUTION.md](doctrine/ple/DOL_EIN_RESOLUTION.md) - Core doctrine
- [PRD](barton-outreach-core/ctb/docs/prd/PRD-DOL-EIN-FUZZY-FILING-DISCOVERY.md) - Requirements
- [ADR](barton-outreach-core/ctb/docs/adr/ADR-DOL-FUZZY-BOUNDARY.md) - Architecture decisions
- [Schema](doctrine/schemas/dol_violations-schema.sql) - Violations table

---

## Commits

1. `feat: Add DOL Violation Discovery (Fact Storage)`

# PR: DOL Violation Linkage Chain + Geographic Config

## Summary

This PR completes the DOL Violation Discovery documentation with the **correct linkage chain** and adds centralized geographic targeting configuration.

---

## Changes

### 1. Corrected Linkage Chain Documentation

The correct flow for violation → outreach is:

```
Violation → EIN → Outreach Context ID → Sovereign ID
```

**NOT:**
```
Violation → EIN → Sovereign ID (WRONG - missing outreach context)
```

### 2. Geographic Targets Config

Created `global-config/geographic_targets.yaml` with 8 target states:
- WV (West Virginia)
- VA (Virginia)
- PA (Pennsylvania)
- MD (Maryland)
- OH (Ohio)
- KY (Kentucky)
- DE (Delaware)
- NC (North Carolina)

### 3. Updated Documentation

| File | Change |
|------|--------|
| `doctrine/ple/VIOLATION_DISCOVERY_FLOW.md` | New - complete linkage documentation |
| `doctrine/schemas/dol_violations-schema.sql` | Added outreach_context_id to view |
| `ctb/docs/prd/PRD-DOL-EIN-FUZZY-FILING-DISCOVERY.md` | Added linkage chain section |
| `ctb/docs/adr/ADR-DOL-FUZZY-BOUNDARY.md` | Added linkage chain section |
| `ctb/docs/tasks/hub_tasks.md` | Added linkage chain checklist items |
| `ctb/docs/obsidian-vault/architecture/DOL-Violation-Linkage-Chain.md` | New - Obsidian note |
| `global-config/geographic_targets.yaml` | New - 8 target states |

---

## Key Concepts

### The Three IDs

| ID | Owner | Purpose |
|----|-------|---------|
| `ein` | DOL SubHub | Federal employer identifier (from violation) |
| `outreach_context_id` | Outreach Orchestration | Targeting context for campaign |
| `company_unique_id` | Company Lifecycle (CL) | **SOVEREIGN ID** |

### Authority Rules

**DOL SubHub CAN:**
- ✅ Match violations to EIN
- ✅ Look up `company_unique_id` via `ein_linkage`
- ✅ Look up `outreach_context_id` via `outreach.outreach_context`
- ✅ Store violation facts with both IDs

**DOL SubHub CANNOT:**
- ❌ Mint `company_unique_id` (CL does this)
- ❌ Mint `outreach_context_id` (Orchestration does this)
- ❌ Create identity from violation data
- ❌ Trigger outreach directly

---

## Testing

- [ ] Verify violation schema includes both `company_unique_id` and `outreach_context_id`
- [ ] Verify views expose both IDs for downstream consumption
- [ ] Verify geographic config is accessible to all modules

---

## Related PRs

- Previous: DOL Violation Discovery Implementation
- Previous: DOL EIN Fuzzy Filing Discovery
- Previous: Blog Sub-Hub Implementation

---

*Generated: 2025-01-03*

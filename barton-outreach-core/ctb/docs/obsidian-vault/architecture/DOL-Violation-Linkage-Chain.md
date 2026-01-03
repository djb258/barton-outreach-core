# DOL Violation Linkage Chain

#dol #violation #ein #outreach #linkage #architecture

---

## Overview

This note documents the **correct linkage chain** for DOL violations to sovereign company identities.

---

## The Linkage Chain

```
VIOLATION  →  EIN  →  OUTREACH_CONTEXT_ID  →  SOVEREIGN_ID
```

### Step-by-Step

| Step | Source | Key Field | Links To |
|------|--------|-----------|----------|
| 1 | DOL API | `plan_ein` | Step 2 |
| 2 | `dol.ein_linkage` | `ein` → `company_unique_id` | Step 3 |
| 3 | `outreach.outreach_context` | `company_unique_id` → `outreach_context_id` | Step 4 |
| 4 | `marketing.company_master` | `company_unique_id` = **SOVEREIGN ID** | — |

---

## Visual Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     VIOLATION LINKAGE CHAIN                              │
└─────────────────────────────────────────────────────────────────────────┘

     DOL API (EBSA, OSHA, WHD)
            │
            │ plan_ein = "12-3456789"
            ▼
     ┌──────────────────────────────────────────────┐
     │ dol.ein_linkage                               │
     │                                               │
     │ ein = "12-3456789"                           │
     │      ↓                                       │
     │ company_unique_id = "CMP-ABC123"            │
     └───────────────────────────┬──────────────────┘
                                 │
                                 ▼
     ┌──────────────────────────────────────────────┐
     │ outreach.outreach_context                    │
     │                                               │
     │ company_unique_id = "CMP-ABC123"            │
     │      ↓                                       │
     │ outreach_context_id = "OC-2024-00123"       │
     └───────────────────────────┬──────────────────┘
                                 │
                                 ▼
     ┌──────────────────────────────────────────────┐
     │ marketing.company_master (CL)                │
     │                                               │
     │ company_unique_id = "CMP-ABC123"            │
     │                                               │
     │ THIS IS THE SOVEREIGN ID                     │
     └──────────────────────────────────────────────┘
```

---

## Key IDs

| ID | Owner | Purpose | DOL SubHub Can... |
|----|-------|---------|-------------------|
| `ein` | DOL SubHub | Federal employer identifier | ✅ Read, ✅ Link |
| `outreach_context_id` | Outreach Orchestration | Targeting context | ✅ Read |
| `company_unique_id` | Company Lifecycle (CL) | **SOVEREIGN ID** | ✅ Read |

---

## dol.violations Table

The violations table stores **both** IDs for the complete linkage:

```sql
CREATE TABLE dol.violations (
    violation_id VARCHAR(50) PRIMARY KEY,
    
    -- EIN (the link key)
    ein VARCHAR(10) NOT NULL,
    
    -- Sovereign ID (from CL via ein_linkage)
    company_unique_id VARCHAR(50),
    
    -- Outreach Context (from Outreach Orchestration)
    outreach_context_id VARCHAR(100),
    
    -- Violation facts...
    source_agency VARCHAR(20) NOT NULL,
    violation_type VARCHAR(100) NOT NULL,
    ...
);
```

---

## Authority Rules

### DOL SubHub CAN:
- ✅ Match violations to EIN
- ✅ Look up `company_unique_id` via `ein_linkage`
- ✅ Look up `outreach_context_id` via `outreach.outreach_context`
- ✅ Store violation facts with both IDs

### DOL SubHub CANNOT:
- ❌ Mint `company_unique_id` (CL does this)
- ❌ Mint `outreach_context_id` (Orchestration does this)
- ❌ Create identity from violation data
- ❌ Trigger outreach directly

---

## Related Notes

- [[DOL-EIN-Fuzzy-Discovery]]
- [[DOL-Violation-Discovery]]
- [[Company-Target-Identity]]

---

## Related Documents

- [VIOLATION_DISCOVERY_FLOW.md](../../../../doctrine/ple/VIOLATION_DISCOVERY_FLOW.md)
- [dol_violations-schema.sql](../../../../doctrine/schemas/dol_violations-schema.sql)
- [PRD-DOL-EIN-FUZZY-FILING-DISCOVERY.md](../../prd/PRD-DOL-EIN-FUZZY-FILING-DISCOVERY.md)

---

*Last Updated: 2025-01-03*

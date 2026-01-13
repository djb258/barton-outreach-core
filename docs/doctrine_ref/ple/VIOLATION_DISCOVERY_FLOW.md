# DOL Violation Discovery Flow

**Version:** 1.1.0  
**Last Updated:** 2025-01-03  
**Status:** Active

---

## Overview

This document describes the canonical flow for discovering DOL violations and connecting them to sovereign company identities for outreach.

---

## The Flow (Correct Linkage Chain)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    VIOLATION DISCOVERY PIPELINE                              │
│                                                                              │
│    The correct linkage chain is:                                             │
│                                                                              │
│    VIOLATION  →  EIN  →  OUTREACH_CONTEXT_ID  →  SOVEREIGN_ID               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

     ┌──────────────────┐
     │  1. VIOLATION    │
     │  (DOL API)       │
     │                  │
     │  • EBSA OCATS    │
     │  • OSHA          │
     │  • WHD           │
     │                  │
     │  Contains:       │
     │  • plan_ein      │
     │  • violation_type│
     │  • penalty_amt   │
     └────────┬─────────┘
              │
              │ Raw violation data includes:
              │ • plan_ein (employer EIN)
              │ • case_type (DEFICIENT, LATE, NON_FILER)
              │ • penalty_amount
              │ • plan_state
              │
              ▼
     ┌──────────────────┐
     │  2. EIN          │
     │  (Identifier)    │
     │                  │
     │  XX-XXXXXXX      │
     │  Federal EIN     │
     └────────┬─────────┘
              │
              │ Lookup EIN in dol.ein_linkage
              │ Get company_unique_id
              │
              ▼
     ┌──────────────────┐
     │  3. OUTREACH     │
     │     CONTEXT ID   │
     │                  │
     │  outreach_       │
     │  context_id      │
     │                  │
     │  From:           │
     │  outreach.       │
     │  outreach_context│
     └────────┬─────────┘
              │
              │ outreach_context_id is the
              │ targeting context that links
              │ to the sovereign company
              │
              ▼
     ┌──────────────────┐
     │  4. SOVEREIGN ID │
     │  (company_unique │
     │       _id)       │
     │                  │
     │  From:           │
     │  Company         │
     │  Lifecycle (CL)  │
     └────────┬─────────┘
              │
              │ Now we have:
              │ • Violation facts
              │ • Linked through outreach context
              │ • To sovereign company identity
              │
              ▼
     ┌──────────────────┐
     │  5. READY FOR    │
     │     OUTREACH     │
     │                  │
     │  dol.violations  │
     │  (Targeting)     │
     └──────────────────┘
```

---

## Detailed Step-by-Step

### Step 1: Identify Violation

**Source:** DOL Open Data API (data.dol.gov)

**EBSA OCATS Data:**
- Deficient filers (Form 5500 issues)
- Late filers
- Non-filers
- Civil penalty assessments

**Key Fields from API:**
```json
{
  "plan_ein": "12-3456789",
  "plan_name": "Acme Corp 401k Plan",
  "plan_admin_name": "Acme Corporation",
  "plan_state": "PA",
  "plan_yr_dte": "2023-12-31",
  "case_type_code": "DEFICIENT",
  "civil_penalty_amt": 1500.00
}
```

---

### Step 2: Connect to EIN

**Table:** `dol.ein_linkage`

The EIN from the violation (`plan_ein`) is matched against our existing EIN linkages:

```sql
-- Step 2A: Find the company_unique_id from EIN
SELECT 
    company_unique_id,
    ein,
    source,
    filing_year
FROM dol.ein_linkage
WHERE ein = '12-3456789';
```

**Result:**
```
company_unique_id | ein         | source        | filing_year
------------------|-------------|---------------|------------
CMP-ABC123        | 12-3456789  | DOL_FORM_5500 | 2023
```

---

### Step 3: Link to Outreach Context ID

**Table:** `outreach.outreach_context`

The `company_unique_id` from EIN linkage is used to find the **outreach context**:

```sql
-- Step 3: Get the outreach context for this company
SELECT 
    outreach_context_id,
    company_unique_id,
    target_status,
    created_at
FROM outreach.outreach_context
WHERE company_unique_id = 'CMP-ABC123'
  AND target_status = 'active';
```

**Result:**
```
outreach_context_id | company_unique_id | target_status | created_at
--------------------|-------------------|---------------|------------
OC-2024-00123       | CMP-ABC123        | active        | 2024-01-15
```

**Key Point:** The `outreach_context_id` is:
- The **targeting context** for outreach operations
- Minted by Outreach Orchestration (NOT by DOL, People, or Blog sub-hubs)
- Binds all outreach operations to a single campaign run
- New retries create NEW outreach_context_ids

---

### Step 4: Verify Sovereign ID

**Table:** `marketing.company_master` (via Company Lifecycle)

The `outreach_context_id` links back to the sovereign `company_unique_id`:

```sql
-- Step 4: Verify the sovereign identity exists in CL
SELECT 
    company_unique_id,
    company_name,
    domain,
    ein,
    address_state
FROM marketing.company_master
WHERE company_unique_id = 'CMP-ABC123';
```

**Result:**
```
company_unique_id | company_name     | domain      | ein         | address_state
------------------|------------------|-------------|-------------|---------------
CMP-ABC123        | Acme Corporation | acme.com    | 12-3456789  | PA
```

---

### Step 5: Store Violation for Outreach

**Table:** `dol.violations` (append-only)

The matched violation is stored with **both** identifiers:

```sql
INSERT INTO dol.violations (
    violation_id,
    company_unique_id,        -- Sovereign ID
    outreach_context_id,      -- Targeting context
    ein,
    source_agency,
    violation_type,
    violation_date,
    case_status,
    penalty_current,
    hash_fingerprint,
    created_at
) VALUES (
    'EBSA-2024-PA-001',
    'CMP-ABC123',             -- Links to sovereign
    'OC-2024-00123',          -- Links to outreach context
    '12-3456789',
    'EBSA',
    'EBSA_DEFICIENT_FILER',
    '2023-12-31',
    'OPEN',
    1500.00,
    'sha256...',
    NOW()
);
```

---

## The Complete Linkage Chain

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        LINKAGE CHAIN (CORRECT)                                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   DOL API                                                                    │
│      │                                                                       │
│      │ plan_ein = "12-3456789"                                               │
│      │                                                                       │
│      ▼                                                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ dol.ein_linkage                                                      │   │
│   │                                                                      │   │
│   │ ein = "12-3456789"  ──►  company_unique_id = "CMP-ABC123"           │   │
│   └───────────────────────────────────────────────────────────┬─────────┘   │
│                                                               │              │
│                                                               ▼              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ outreach.outreach_context                                            │   │
│   │                                                                      │   │
│   │ company_unique_id = "CMP-ABC123"  ──►  outreach_context_id =        │   │
│   │                                          "OC-2024-00123"            │   │
│   └───────────────────────────────────────────────────────────┬─────────┘   │
│                                                               │              │
│                                                               ▼              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ marketing.company_master (Company Lifecycle - CL)                    │   │
│   │                                                                      │   │
│   │ company_unique_id = "CMP-ABC123" (SOVEREIGN ID)                     │   │
│   │ • company_name                                                      │   │
│   │ • domain                                                            │   │
│   │ • ein                                                               │   │
│   │ • lifecycle_state                                                   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Authority Rules

### Who Owns What

| Entity | Owner | DOL SubHub Authority |
|--------|-------|---------------------|
| `company_unique_id` | Company Lifecycle (CL) | READ ONLY |
| `outreach_context_id` | Outreach Orchestration | READ ONLY |
| `ein` | DOL Subhub | OWNS (via ein_linkage) |
| `violation` facts | DOL Subhub | OWNS (via violations) |

### DOL Subhub Constraints

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         DOL SUBHUB CONSTRAINTS                                 ║
║                                                                               ║
║   ✅ CAN:                                                                     ║
║   • Match violations to EIN                                                   ║
║   • Look up company_unique_id via ein_linkage                                 ║
║   • Look up outreach_context_id via outreach.outreach_context                 ║
║   • Store violation facts with both IDs                                       ║
║                                                                               ║
║   ❌ CANNOT:                                                                  ║
║   • Mint company_unique_id (CL does this)                                     ║
║   • Mint outreach_context_id (Orchestration does this)                        ║
║   • Create identity from violation data                                       ║
║   • Trigger outreach directly                                                 ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## Error Handling

### No EIN Linkage Found

If a violation's EIN is not in `dol.ein_linkage`:

1. **Log to `shq.error_master`** with `VIOLATION_EIN_MISMATCH`
2. **Store in unmatched queue** for manual review
3. **Do NOT create a new EIN linkage** from violation data

```
DOCTRINE: Violations do NOT create identity.
          EIN linkage must come from Company Target / Form 5500 filings.
```

### No Outreach Context Found

If a `company_unique_id` exists but has no `outreach_context_id`:

1. **Store violation** with `company_unique_id` only
2. **Set `outreach_context_id` to NULL**
3. **Violation is stored but not yet targetable**
4. When outreach context is created later, violation becomes available

---

## Code Entry Points

### Full Discovery Pipeline

```javascript
const { runEBSADiscovery } = require('./ctb/sys/dol-ein/findViolations');

const result = await runEBSADiscovery({
  states: ['PA', 'OH', 'WV', 'KY', 'VA', 'MD', 'DE', 'NC'],
  years: 2023,
  einLinkages: existingLinkages,     // From dol.ein_linkage
  outreachContextId: 'OC-2024-00123' // From outreach.outreach_context
});

// result.matched = violations ready for dol.violations table
// result.unmatched = violations without EIN linkage (for review)
```

---

## Related Documentation

- [DOL_EIN_RESOLUTION.md](./DOL_EIN_RESOLUTION.md) - EIN Resolution doctrine
- [dol_violations-schema.sql](../schemas/dol_violations-schema.sql) - Violations table schema
- [geographic_targets.yaml](../../global-config/geographic_targets.yaml) - Target states config
- [Outreach Execution README](../../hubs/outreach-execution/README.md) - Company Target & Outreach Context

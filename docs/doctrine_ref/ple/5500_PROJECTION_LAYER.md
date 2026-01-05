# Form 5500 Projection Layer — Read-Only Analytics Views
## Barton Doctrine Framework | SVG-PLE Marketing Core

**Document ID**: `01.04.02.04.22100.001`
**Version**: 1.0.0
**Last Updated**: 2025-01-01
**Status**: Active | Production Ready

---

## Overview

This doctrine defines the **Form 5500 Projection Layer**, a set of **read-only SQL views** that expose renewal month signals and Schedule A / EZ facts from the ~1.3M Form 5500 corpus.

**CRITICAL**: These views are **read-only projections**. They do NOT modify the DOL Subhub or any source tables.

---

## Section 1: Doctrine Rules (LOCKED)

### What This Layer Does

| Function | Description |
|----------|-------------|
| **Renewal Month Extraction** | Derive month from coverage/plan year end dates |
| **Insurance Facts Projection** | Expose Schedule A and EZ fields on demand |
| **Confidence Tagging** | Explicitly flag certainty of derived values |

### What This Layer Does NOT Do

| Prohibited | Reason |
|------------|--------|
| ❌ Modify DOL Subhub | DOL is locked to EIN resolution only |
| ❌ Write new tables | Views only, no data storage |
| ❌ Infer beyond filed dates | No guessing, no assumptions |
| ❌ Guess renewal logic | Renewal month ≠ contractual renewal |
| ❌ Trigger campaigns | Data access, not behavior |
| ❌ Add scoring | No BIT integration |
| ❌ Create materialized views | Read-only SQL views only |

---

## Section 2: Canonical Views

### View 1: `analytics.v_5500_renewal_month`

**Purpose**: Extract renewal month from Form 5500 filings for campaign targeting.

| Column | Type | Description |
|--------|------|-------------|
| `company_unique_id` | VARCHAR | From EIN linkage |
| `ein` | VARCHAR | Employer EIN |
| `filing_year` | INTEGER | 5500 filing year |
| `source_form` | VARCHAR | `SCHEDULE_A` or `EZ` |
| `coverage_end_date` | DATE | Raw end date from filing |
| `renewal_month` | INTEGER | 1–12, or NULL if ambiguous |
| `confidence` | VARCHAR | `DECLARED` / `INFERRED` / `AMBIGUOUS` |
| `source_record_id` | VARCHAR | Filing reference |
| `created_at` | TIMESTAMPTZ | View timestamp |

### Renewal Month Logic (MANDATORY)

**Priority Order**:

1. **Schedule A** → Insurance contract / coverage period end date
   - `confidence = DECLARED`

2. **5500-EZ** → Plan year end date
   - `confidence = INFERRED`

3. **Multiple conflicting dates** in same filing year
   - `renewal_month = NULL`
   - `confidence = AMBIGUOUS`

**Derivation Rule**:

```sql
renewal_month = EXTRACT(MONTH FROM coverage_end_date)
```

**No offsets. No +1 month logic. No smoothing.**

---

### View 2: `analytics.v_5500_insurance_facts`

**Purpose**: General-purpose projection of Schedule A / EZ fields for any downstream system.

| Column | Type | Description |
|--------|------|-------------|
| `company_unique_id` | VARCHAR | From EIN linkage |
| `ein` | VARCHAR | Employer EIN |
| `filing_year` | INTEGER | 5500 filing year |
| `source_form` | VARCHAR | `SCHEDULE_A` or `EZ` |
| `insurer_name` | TEXT | From Schedule A only |
| `insurer_ein` | VARCHAR | From Schedule A only |
| `policy_number` | TEXT | From Schedule A only |
| `coverage_start_date` | DATE | Start of coverage/plan year |
| `coverage_end_date` | DATE | End of coverage/plan year |
| `funding_type` | TEXT | As filed |
| `commissions` | NUMERIC | Raw value (nullable) |
| `source_record_id` | VARCHAR | Filing reference |
| `created_at` | TIMESTAMPTZ | View timestamp |

**No transformations. No scoring. No enrichment.**

---

## Section 3: Confidence Flags

Consumers MUST respect confidence flags:

| Confidence | Meaning | Usage Guidance |
|------------|---------|----------------|
| `DECLARED` | From Schedule A insurance contract | Safe for campaign targeting |
| `INFERRED` | From EZ plan year end | Use with caution |
| `AMBIGUOUS` | Multiple conflicting dates | Do NOT use for targeting |

### Example: Safe Campaign Query

```sql
SELECT * FROM analytics.v_5500_renewal_month
WHERE renewal_month = 6
  AND confidence IN ('DECLARED', 'INFERRED')
  AND filing_year >= EXTRACT(YEAR FROM NOW()) - 2;
```

### Example: Carrier Lookup

```sql
SELECT * FROM analytics.v_5500_insurance_facts
WHERE company_unique_id = '04.04.02.04.30000.042'
  AND source_form = 'SCHEDULE_A'
ORDER BY filing_year DESC;
```

---

## Section 4: Join Discipline

All joins MUST flow in this direction:

```
EIN Linkage (dol.ein_linkage)
           ↓
5500 Filings (dol.form_5500_*)
           ↓
Projection Views (analytics.v_5500_*)
```

### Prohibited Joins

| Prohibited | Reason |
|------------|--------|
| ❌ Reverse joins | Views read from source, not vice versa |
| ❌ Lateral enrichment | No augmenting source data |
| ❌ Outreach joins | Views don't know about campaigns |
| ❌ BIT joins | Views don't know about scoring |
| ❌ People joins | Views don't know about contacts |

---

## Section 5: Consumer Responsibilities

Systems consuming these views MUST:

1. **Check confidence** before using renewal_month
2. **Handle NULL** values gracefully
3. **Not assume** renewal month = contractual renewal
4. **Not write back** to any source tables
5. **Not cache** without TTL (data can be amended)

### Renewal Month Is NOT:

- A contractual renewal date
- A guarantee of policy expiration
- A trigger for automated outreach
- An enrichment signal

**It is**: A filed fact or deterministic projection with explicit confidence.

---

## Section 6: Data Lineage

```
DOL EFAST2 Filings (raw)
         ↓
5500 Corpus Tables (dol.form_5500_*)
         ↓
EIN Linkage (dol.ein_linkage)
         ↓
Projection Views (analytics.v_5500_*)
         ↓
Downstream Consumers (Renewal, Outreach, Analytics)
```

### Source Tables (Expected)

| Table | Description |
|-------|-------------|
| `dol.ein_linkage` | EIN ↔ company_unique_id (from DOL Subhub) |
| `dol.form_5500_schedule_a` | Schedule A insurance contract data |
| `dol.form_5500_ez` | 5500-EZ simplified filing data |

---

## Section 7: Explicit Non-Goals

This layer does NOT:

| Non-Goal | Reason |
|----------|--------|
| Trigger campaigns | Data access, not behavior |
| Add alerts | No notification logic |
| Add scoring | No BIT integration |
| Add materialized views | Read-only SQL views only |
| Add indexes beyond required | No optimization scope |
| Modify DOL, BIT, or Company Target | Isolated layer |

---

## Section 8: Migration Reference

**File**: `ctb/data/infra/migrations/011_5500_projection_views.sql`

### Deployment

```bash
psql $DATABASE_URL -f ctb/data/infra/migrations/011_5500_projection_views.sql
```

### Verification

```sql
-- Check views exist
SELECT viewname FROM pg_views 
WHERE schemaname = 'analytics' 
  AND viewname LIKE 'v_5500%';
-- Expected: v_5500_renewal_month, v_5500_insurance_facts
```

---

## Section 9: What This Gives You

| Capability | Example |
|------------|---------|
| **Campaign Targeting** | `WHERE renewal_month = 6 AND confidence = 'DECLARED'` |
| **Carrier Analysis** | Pull insurer names and policy numbers |
| **Coverage Windows** | Start/end dates for timing decisions |
| **Renewal Intel** | Feed into Renewal spoke (when built) |
| **Pure DOL Corpus** | 5500 data becomes permanent fact reservoir |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-01-01 | Barton Outreach Team | Initial projection layer doctrine |

---

## Cross-References

### Related Doctrines

- [`DOL_EIN_RESOLUTION.md`](./DOL_EIN_RESOLUTION.md) — EIN linkage (source for joins)
- [`PLE-Doctrine.md`](./PLE-Doctrine.md) — Master PLE overview

### Migration Files

- `ctb/data/infra/migrations/011_5500_projection_views.sql`

---

**End of Form 5500 Projection Layer Doctrine**

*These views are READ-ONLY. All values are filed facts or deterministic projections.*
*Renewal month is NOT a contractual renewal. Confidence flags MUST be respected.*

# DOL Sub-Hub — Architecture Decision Records

> **IMPORTANT**: This file contains ADRs for the DOL Sub-Hub.
> The primary ADR for the EIN Lock-In backfill is ADR-DOL-002.

---

# ADR-DOL-001: EIN Matching — Exact Only

## ADR Identity

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-DOL-001 |
| **Status** | ✅ Accepted |
| **Date** | 2026-01-01 |

---

## Owning Hub

| Field | Value |
|-------|-------|
| **Hub Name** | DOL Filings |
| **Hub ID** | HUB-DOL |

---

## Context

DOL filings contain EINs that should match company_master records.
Fuzzy matching introduces false positives and compliance risk.

---

## Decision

DOL Filings uses **exact EIN matching only**:
- No fuzzy matching
- No retries on mismatch
- Fail closed — unmatched filings are not attached

---

## Alternatives Considered

| Option | Why Not Chosen |
|--------|----------------|
| Fuzzy EIN matching | False positive risk too high |
| Multiple match attempts | Compliance concern |
| Do Nothing | Would allow bad matches |

---

## Consequences

### Enables

- High confidence in filing attachments
- Clean audit trail
- Compliance-safe matching

### Prevents

- False positive attachments
- Bad data propagation

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner | Outreach Team | 2026-01-01 |
| Reviewer | | |

---

# ADR-DOL-002: EIN Lock-In Backfill (IMO-Compliant)

## ADR Identity

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-DOL-002 |
| **Status** | ✅ Accepted + Executed |
| **Date** | 2026-01-07 |
| **Executed** | 2026-01-07 |
| **Tag** | `dol-ein-lock-v1.0` |

---

## Owning Hub

| Field | Value |
|-------|-------|
| **Hub Name** | DOL Filings |
| **Hub ID** | HUB-DOL |
| **Process ID** | 01.04.02.04.22000 |
| **Agent ID** | DOL_EIN_BACKFILL_V1 |

---

## Context and Problem Statement

The `dol.ein_linkage` table was empty. Outreach records in `outreach.outreach` need
to be linked to companies via EIN for DOL filing intelligence. Without this linkage,
downstream processes (People Intelligence, Blog Content) cannot leverage Form 5500 data.

### Key Constraints

1. **No fuzzy logic** — Only exact EIN matches
2. **No AIR** — No automated intelligence resolution
3. **Errors only** — Failures go to `shq.error_master`, not retry queues
4. **IMO-compliant** — Single-pass Input → Middle → Output
5. **Deterministic** — Same input produces same output every time

---

## Decision Drivers

1. **Data Quality**: Exact EIN match prevents false positives
2. **Auditability**: All failures logged with context
3. **Cost Control**: No paid tools (FREE tier only)
4. **Simplicity**: Single-pass, no retry loops

---

## Considered Options

| Option | Description | Chosen |
|--------|-------------|--------|
| A | Direct company_master.ein lookup only | ❌ |
| B | Form 5500 exact name match only | ❌ |
| C | **Priority cascade**: company_master.ein → Form 5500 exact name | ✅ |
| D | Fuzzy name matching | ❌ Rejected |

---

## Decision Outcome

**Chosen option: C — Priority Cascade**

### EIN Resolution Priority

| Priority | Source | Condition |
|----------|--------|-----------|
| 1 | `company.company_master.ein` | Direct EIN from company record |
| 2 | `dol.form_5500.sponsor_dfe_ein` | Exact company name match (normalized) |

### Canonical Rule

```
IF outreach_id resolves to exactly 1 EIN → PASS → dol.ein_linkage
IF outreach_id resolves to 0 EINs → FAIL → shq.error_master (DOL_EIN_MISSING)
IF outreach_id resolves to 2+ EINs → FAIL → shq.error_master (DOL_EIN_AMBIGUOUS)
```

---

## Technical Details

### Join Path

```
outreach.outreach.sovereign_id
    ↓
cl.company_identity_bridge.company_sov_id
    ↓
cl.company_identity_bridge.source_company_id
    ↓
company.company_master.company_unique_id
    ↓
company.company_master.ein (Priority 1)
    OR
dol.form_5500.sponsor_dfe_ein (Priority 2 - exact name match)
```

### Target States (Geographic Filter)

| State | Code |
|-------|------|
| West Virginia | WV |
| Virginia | VA |
| Pennsylvania | PA |
| Maryland | MD |
| Ohio | OH |
| Kentucky | KY |
| Delaware | DE |
| North Carolina | NC |

### Script Location

`hubs/dol-filings/imo/middle/dol_ein_backfill.py`

### Write Targets

| Outcome | Target Table | Columns |
|---------|--------------|---------|
| PASS | `dol.ein_linkage` | linkage_id, company_unique_id, ein, source, source_url, filing_year, hash_fingerprint, outreach_context_id, created_at |
| FAIL | `shq.error_master` | error_id, process_id, agent_id, severity, error_type, message, company_unique_id, outreach_context_id, context, created_at |

---

## Execution Results

| Metric | Count |
|--------|-------|
| Outreach IDs scanned | 60,577 |
| **Linked successfully** | **9,365** (15.5%) |
| Missing EIN | 51,192 |
| Ambiguous EIN | 20 |
| Rows → dol.ein_linkage | 9,365 |
| Rows → shq.error_master | 51,212 |

---

## Positive Consequences

- **Clean EIN linkage**: 9,365 outreach records now have deterministic EIN binding
- **Audit trail**: All 51,212 failures logged with context for future enrichment
- **No false positives**: Exact match only prevents bad data
- **Idempotent**: Rerunning produces same results (hash-based dedup)

---

## Negative Consequences

- **Low initial rate**: 15.5% linkage rate (expected given company_master.ein sparsity)
- **Requires enrichment**: 51,192 companies need EIN enrichment from external sources

---

## Future Work (Outside Current Scope)

| Task | Owner | Priority |
|------|-------|----------|
| EIN Enrichment Hub | Enrichment Team | Medium |
| Manual resolution for ambiguous EINs (20) | Data Team | Low |

---

## Explicit Rejections

The following are **permanently rejected** for DOL EIN matching:

| Concept | Reason |
|---------|--------|
| Fuzzy EIN matching | False positive risk |
| Fuzzy name matching | Ambiguity and compliance risk |
| AIR (Automated Intelligence Resolution) | Out of scope for this hub |
| Retry queues | Single-pass doctrine |
| ID minting | CL's responsibility |

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner | Outreach Team | 2026-01-07 |
| Reviewer | | |
| Executor | Agent | 2026-01-07 |

---

# ADR-DOL-003: Table Ownership

## ADR Identity

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-DOL-003 |
| **Status** | ✅ Accepted |
| **Date** | 2026-01-08 |

---

## Owning Hub

| Field | Value |
|-------|-------|
| **Hub Name** | DOL Filings |
| **Hub ID** | HUB-DOL |

---

## Decision

DOL Sub-Hub owns the following tables:

### dol.* Schema (Owned)

| Table | Purpose |
|-------|---------|
| `dol.ein_linkage` | EIN-to-Company linkage (primary output) |
| `dol.form_5500` | Form 5500 annual filings |
| `dol.form_5500_sf` | Small plan filings |
| `dol.schedule_a` | Insurance broker/carrier data |
| `dol.ebsa_violations` | EBSA enforcement actions |
| `dol.violations` | (Reserved) |

### Staging Tables

| Table | Purpose |
|-------|---------|
| `dol.form_5500_staging` | Ingestion staging |
| `dol.form_5500_sf_staging` | SF ingestion staging |
| `dol.schedule_a_staging` | Schedule A staging |

### Views

| View | Purpose |
|------|---------|
| `dol.v_5500_summary` | Filing summary |
| `dol.v_schedule_a_carriers` | Carrier summary |

### Tables NOT Owned (Read-Only)

| Table | Owner |
|-------|-------|
| `outreach.outreach` | Outreach Orchestration |
| `company.company_master` | Company Hub |
| `cl.company_identity_bridge` | Company Lifecycle |

---

## Consequences

- Clear ownership boundaries
- No cross-hub write conflicts
- Audit trail for all DOL writes

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner | Outreach Team | 2026-01-08 |

---

**Last Updated**: 2026-01-08
**Version**: 1.0.0

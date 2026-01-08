---
id: dol-subhub
title: DOL Sub-Hub
desc: Department of Labor filings sub-hub - EIN Lock-In and regulatory intelligence
updated: 2026-01-08
created: 2026-01-01
tags:
  - hub
  - dol
  - ein
  - form-5500
  - imo
---

# DOL Sub-Hub

## Overview

The DOL Sub-Hub processes Department of Labor filing data to enrich companies with EIN linkage and regulatory intelligence. It is the **2nd sub-hub** in the canonical waterfall (after Company Target, before People Intelligence).

## Quick Reference

| Field | Value |
|-------|-------|
| **Hub ID** | HUB-DOL |
| **Doctrine ID** | 04.04.03 |
| **Process ID** | 01.04.02.04.22000 |
| **Version** | 3.0.0 |
| **Tag** | `dol-ein-lock-v1.0` |

## Ownership

### Owns

- `dol.ein_linkage` - EIN-to-Company bindings
- `dol.form_5500` - Annual benefit plan filings
- `dol.form_5500_sf` - Small plan filings
- `dol.schedule_a` - Insurance broker/carrier data
- `dol.ebsa_violations` - EBSA enforcement actions

### Does NOT Own

- Company identity (CL owns)
- Outreach spine (Orchestration owns)
- Email patterns (Company Target owns)
- People lifecycle (People Intel owns)

## IMO Architecture

```
INPUT (I)           MIDDLE (M)              OUTPUT (O)
──────────         ──────────              ───────────
outreach.outreach  Priority 1:            PASS:
    ↓              company_master.ein      → dol.ein_linkage
cl.bridge             ↓
    ↓              Priority 2:            FAIL:
company_master     form_5500 exact match   → shq.error_master
```

## EIN Resolution

### Priority Cascade

1. **Priority 1**: `company.company_master.ein` (direct EIN from company record)
2. **Priority 2**: `dol.form_5500.sponsor_dfe_ein` (exact company name match)

### Canonical Rule

| EIN Count | Result | Target Table |
|-----------|--------|--------------|
| 0 | FAIL | `shq.error_master` |
| 1 | PASS | `dol.ein_linkage` |
| 2+ | FAIL | `shq.error_master` |

## Target States

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

## Backfill Results (v1.0)

| Metric | Count |
|--------|-------|
| Outreach IDs scanned | 60,577 |
| **Linked successfully** | **9,365** (15.5%) |
| Missing EIN | 51,192 |
| Ambiguous EIN | 20 |

## Key Files

| File | Purpose |
|------|---------|
| [PRD.md](../hubs/dol-filings/PRD.md) | Product Requirements |
| [ADR.md](../hubs/dol-filings/ADR.md) | Architecture Decisions |
| [CHECKLIST.md](../hubs/dol-filings/CHECKLIST.md) | Compliance Checklist |
| [DOL_SUBHUB_ERD.md](../hubs/dol-filings/imo/DOL_SUBHUB_ERD.md) | Entity Relationship Diagram |
| [dol_ein_backfill.py](../hubs/dol-filings/imo/middle/dol_ein_backfill.py) | Backfill Script |

## Related Hubs

- **Upstream**: Company Target (provides outreach_id, domain)
- **Downstream**: People Intelligence, Blog Content

## Explicit Rejections

- ❌ Fuzzy EIN matching
- ❌ Fuzzy name matching
- ❌ Retry/backoff logic
- ❌ AIR (Automated Intelligence Resolution)
- ❌ ID minting

## Links

- [[company-target]] - Upstream hub
- [[people-intelligence]] - Downstream hub
- [[ein-linkage]] - EIN binding table
- [[form-5500]] - DOL filing format

# PRD — DOL Sub-Hub (EIN Lock-In) v3.0

> **DOCTRINE LOCK**: This PRD describes DOL Sub-Hub as a single-pass IMO gate.
> For full details, see `docs/prd/PRD_DOL_SUBHUB.md`.

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | 1.1.0 |
| **CTB Version** | 1.0.0 |
| **CC Layer** | CC-02 |
| **Architecture** | Single-Pass IMO Gate |
| **Tag** | `dol-ein-lock-v1.0` |

---

## 1. Sovereign Reference (CC-01)

| Field | Value |
|-------|-------|
| **Sovereign ID** | barton-enterprises |
| **Sovereign Boundary** | Marketing intelligence and executive enrichment operations |

---

## 2. Hub Identity (CC-02)

| Field | Value |
|-------|-------|
| **Hub Name** | DOL Filings |
| **Hub ID** | HUB-DOL |
| **Owner** | Outreach Team |
| **Version** | 3.0.0 |
| **Process ID** | 01.04.02.04.22000 |

---

## 3. Purpose

Lock regulatory filings (Form 5500, Schedule A) to **existing companies** via EIN.
Source of truth for EIN-to-company linkage in the Outreach program.

**Waterfall Position**: 2nd sub-hub in canonical waterfall (after Company Target, before People Intelligence).

### Ownership Statement

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           DOL SUB-HUB OWNERSHIP                               ║
║                                                                               ║
║   This sub-hub OWNS:                                                          ║
║   ├── EIN-to-Company linkage (dol.ein_linkage)                               ║
║   ├── Form 5500 data ingestion and processing                                ║
║   ├── Schedule A insurance broker data extraction                            ║
║   ├── Plan renewal date tracking                                             ║
║   ├── Broker change detection                                                ║
║   └── DOL compliance signal emission                                         ║
║                                                                               ║
║   This sub-hub DOES NOT OWN:                                                  ║
║   ├── Company identity creation (CL owns)                                    ║
║   ├── Outreach spine records (Orchestration owns)                            ║
║   ├── Email pattern discovery (Company Target owns)                          ║
║   ├── People lifecycle management (People Intel owns)                        ║
║   └── BIT Engine scoring (Company Hub owns)                                  ║
║                                                                               ║
║   This sub-hub EMITS: EIN linkage, filing signals                            ║
║   This sub-hub NEVER: Creates companies, retries failures, uses fuzzy logic  ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 4. CTB Placement

| Field | Value | CC Layer |
|-------|-------|----------|
| **Trunk** | sys | CC-02 |
| **Branch** | outreach | CC-02 |
| **Leaf** | dol-filings | CC-02 |

---

## 5. IMO Structure (CC-02)

| Layer | Role | Description | CC Layer |
|-------|------|-------------|----------|
| **I — Input** | Load from spine | Receives `outreach_id` via Company Target; loads domain, company_unique_id | CC-02 |
| **M — Middle** | EIN resolution | EIN matching via Priority 1 (company_master) or Priority 2 (Form 5500 exact match) | CC-02 |
| **O — Output** | Write linkage | PASS → `dol.ein_linkage`; FAIL → `shq.error_master` | CC-02 |

### IMO Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DOL SUB-HUB IMO FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

   OUTREACH SPINE                DOL IMO GATE                     OUTPUT
   ─────────────                 ────────────                     ──────

┌───────────────┐            ┌────────────────────┐
│ outreach.     │            │    INPUT (I)       │
│ outreach      │            │                    │
│               │  outreach_ │ • Load outreach_id │
│ • outreach_id ├───────────►│ • Join CL bridge   │
│ • sovereign_id│    id      │ • Get company_uid  │
│ • domain      │            │ • Validate state   │
└───────────────┘            └─────────┬──────────┘
                                       │
                                       ▼
                             ┌────────────────────┐
                             │   MIDDLE (M)       │
                             │                    │
                             │ Priority 1:        │
                             │ • company_master   │
                             │   .ein             │
                             │                    │
                             │ Priority 2:        │
                             │ • form_5500 exact  │
                             │   name match       │
                             │                    │
                             │ Rules:             │
                             │ • 0 EIN = FAIL     │
                             │ • 1 EIN = PASS     │
                             │ • 2+ EIN = FAIL    │
                             └─────────┬──────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    │                                     │
                    ▼                                     ▼
          ┌─────────────────┐               ┌─────────────────┐
          │  OUTPUT (O)     │               │  OUTPUT (O)     │
          │  PASS           │               │  FAIL           │
          │                 │               │                 │
          │ → dol.ein_      │               │ → shq.error_    │
          │   linkage       │               │   master        │
          │                 │               │                 │
          │ 9,365 rows      │               │ 51,212 rows     │
          └─────────────────┘               └─────────────────┘
```

---

## 6. Spokes (CC-03 Interfaces)

| Spoke Name | Type | Direction | Contract | CC Layer |
|------------|------|-----------|----------|----------|
| company-dol | I | Inbound | outreach_id, domain, company_unique_id | CC-03 |
| dol-people | O | Outbound | outreach_id, ein, filing_signals | CC-03 |
| dol-blog | O | Outbound | outreach_id, regulatory_data | CC-03 |

---

## 7. Constants vs Variables

| Element | Type | Mutability | CC Layer |
|---------|------|------------|----------|
| Hub ID | Constant | Immutable | CC-02 |
| Hub Name | Constant | ADR-gated | CC-02 |
| Doctrine ID (04.04.03) | Constant | Immutable | CC-02 |
| CTB Placement | Constant | ADR-gated | CC-02 |
| Primary Table | Constant | ADR-gated | CC-02 |
| Process ID (01.04.02.04.22000) | Constant | Immutable | CC-02 |
| Target States | Constant | ADR-gated | CC-02 |
| outreach_id | Variable | Runtime | CC-04 |
| ein | Variable | Runtime | CC-04 |
| filing_data | Variable | Runtime (from DOL) | CC-04 |

### Target States (Geographic Scope)

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

---

## 8. Tools

| Tool | Solution Type | CC Layer | IMO Layer | ADR Reference |
|------|---------------|----------|-----------|---------------|
| DOL CSV Parser | Deterministic | CC-02 | I | N/A (Bulk) |
| EIN Matcher | Deterministic | CC-02 | M | ADR-DOL-002 |
| Backfill Script | One-Time | CC-02 | M | ADR-DOL-002 |

### Tool Registry

| Tool ID | Name | Tier | Cost |
|---------|------|------|------|
| DOL-001 | CSV Ingestion | 0 | FREE |
| DOL-002 | EIN Resolution | 0 | FREE |
| DOL-003 | Form 5500 Parser | 0 | FREE |

---

## 9. Guard Rails

| Guard Rail | Type | Threshold | CC Layer |
|------------|------|-----------|----------|
| Company Target PASS | Validation | MUST have upstream PASS | CC-03 |
| Exact EIN match | Validation | No fuzzy matching allowed | CC-03 |
| No retries on mismatch | Rate Limit | Single attempt per outreach_id | CC-04 |
| State filter | Validation | MUST be in target states | CC-03 |
| Dedup check | Validation | Hash fingerprint unique | CC-04 |

---

## 10. Kill Switch

| Field | Value |
|-------|-------|
| **Activation Criteria** | EIN match fails (exact match only) |
| **Trigger Authority** | CC-02 (Hub) |
| **Emergency Contact** | Outreach Team |

---

## 11. Promotion Gates

| Gate | Artifact | CC Layer | Requirement |
|------|----------|----------|-------------|
| G1 | PRD | CC-02 | Hub definition approved |
| G2 | ADR | CC-03 | Architecture decision recorded (ADR-DOL-002) |
| G3 | Work Item | CC-04 | Execution item created |
| G4 | PR | CC-04 | Code reviewed and merged |
| G5 | Checklist | CC-04 | Compliance verification complete |
| G6 | Tag | CC-04 | Git tag created (`dol-ein-lock-v1.0`) |

---

## 12. Failure Modes

| Failure | Severity | CC Layer | Remediation |
|---------|----------|----------|-------------|
| Company Target not PASS | CRITICAL | CC-03 | STOP - upstream dependency |
| EIN not found (0 matches) | MEDIUM | CC-04 | Log to shq.error_master (DOL_EIN_MISSING) |
| EIN ambiguous (2+ matches) | MEDIUM | CC-04 | Log to shq.error_master (DOL_EIN_AMBIGUOUS) |
| Company not in target state | LOW | CC-04 | Skip record (expected) |
| Duplicate linkage | LOW | CC-04 | Dedupe, skip (idempotent) |

---

## 13. PID Scope (CC-04)

| Field | Value |
|-------|-------|
| **PID Pattern** | `HUB-DOL-{TIMESTAMP}-{RANDOM_HEX}` |
| **Retry Policy** | No retries (single-pass) |
| **Audit Trail** | Required |

---

## 14. Human Override Rules

Override requires CC-02 (Hub Owner) or CC-01 (Sovereign) approval:
- Manual EIN assignment for ambiguous cases
- Force linkage despite mismatch
- Bulk re-processing

---

## 15. Observability

| Type | Description | CC Layer |
|------|-------------|----------|
| **Logs** | EIN resolution attempts, linkage writes, errors | CC-04 |
| **Metrics** | EIN_LINKAGE_RATE (target >= 15%), records_processed | CC-04 |
| **Alerts** | Linkage rate drops, bulk failures | CC-03/CC-04 |

---

## 16. Backfill Results (v1.0)

| Metric | Count |
|--------|-------|
| Outreach IDs scanned | 60,577 |
| **Linked successfully** | **9,365** (15.5%) |
| Missing EIN | 51,192 |
| Ambiguous EIN | 20 |
| Rows → dol.ein_linkage | 9,365 |
| Rows → shq.error_master | 51,212 |

---

## Approval

| Role | Name | Date |
|------|------|------|
| Sovereign (CC-01) | | |
| Hub Owner (CC-02) | | |
| Reviewer | | |

---

## Traceability

| Artifact | Reference |
|----------|-----------|
| Canonical Doctrine | CANONICAL_ARCHITECTURE_DOCTRINE.md |
| Hub/Spoke Doctrine | HUB_SPOKE_ARCHITECTURE.md |
| ADR | ADR-DOL-002 (EIN Lock-In) |
| ERD | DOL_SUBHUB_ERD.md |
| Tag | `dol-ein-lock-v1.0` |

---

**Last Updated**: 2026-01-08
**Version**: 3.0.0

# Company Target Sub-Hub (04.04.01)
## Architecture Overview

**Created**: 2026-01-02
**Updated**: 2026-01-02
**Status**: CERTIFIED
**Links**: [[CL_ADMISSION_GATE_DOCTRINE]] | [[CROSS_REPO_REFERENCE]] | [[PLE-Doctrine]]

---

## Summary

Company Target is the **internal anchor** sub-hub within Barton Outreach Core. It receives `company_unique_id` from Company Lifecycle (CL) parent hub and provides the FK join point for all downstream sub-hubs.

---

## Position in Architecture

```
                    COMPANY LIFECYCLE (CL) - PARENT HUB
                    ─────────────────────────────────────
                    • Mints company_unique_id (SOVEREIGN)
                    • Owns cl.* schema
                                    │
                                    │ company_unique_id (downstream)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     COMPANY TARGET (04.04.01)                                │
│                     Internal Anchor Sub-Hub                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│   RECEIVES: company_unique_id from CL                                       │
│   OWNS: outreach.company_target, local_bit_scores                           │
│   CANNOT: Mint IDs, promote lifecycle, write to cl.*                        │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┬───────────────┐
        ▼           ▼           ▼               ▼
   People      DOL Filings    Blog        Outreach
   (04.04.02)  (04.04.03)   (04.04.05)   (04.04.04)
```

---

## Tables Owned

### Primary Tables (Write)

| Schema | Table | Purpose |
|--------|-------|---------|
| `outreach` | `company_target` | Internal anchor (FK to CL) |
| `outreach` | `column_registry` | Column metadata |

### Legacy Tables (Read + Write)

| Schema | Table | Migration Status |
|--------|-------|------------------|
| `marketing` | `company_master` | Migrating to CL |
| `marketing` | `pipeline_events` | Shared |

### Read-Only Tables (From CL)

| Schema | Table | Purpose |
|--------|-------|---------|
| `cl` | `company_identity` | Sovereign records |
| `cl` | `lifecycle_state` | Current state |

---

## ERD

```
cl.company_identity
        │
        │ company_unique_id (FK)
        │ ON DELETE RESTRICT
        ▼
outreach.company_target
├── target_id (PK)
├── company_unique_id (FK)
├── outreach_status
├── bit_score_snapshot
├── first_targeted_at
├── last_targeted_at
├── sequence_count
├── created_at
└── updated_at
        │
        │ target_id (FK)
        ├──► outreach.people
        ├──► outreach.dol_filings
        └──► outreach.blog_signals
```

---

## Pipeline Phases

| Phase | Name | Description |
|-------|------|-------------|
| 1 | Company Matching | Match against company_master |
| 1b | Unmatched Hold | Export for manual review |
| 2 | Domain Resolution | DNS/MX validation |
| 3 | Email Pattern Waterfall | Tier 0→1→2 discovery |
| 4 | Pattern Verification | SMTP/catch-all check |

---

## Cost Rules

| Tier | Tools | Limit |
|------|-------|-------|
| 0 | Firecrawl, Google Places | Unlimited (free) |
| 1 | Hunter, Clearbit, Apollo | Budget-gated |
| 2 | Prospeo, Snov, Clay | ONE per context |

---

## Boundary Rules

> **Golden Rule**: No processing without `company_unique_id` FROM CL.

### Cannot Do
- Mint company_unique_id (CL ONLY)
- Merge company identities (CL ONLY)
- Retire company identities (CL ONLY)
- Promote lifecycle state (CL ONLY)
- Write to cl.* schema (CL ONLY)
- Perform fuzzy matching to create identities (CL ONLY)

### Can Do
- Receive company_unique_id from CL
- Create outreach.company_target records
- Signal engagement events back to CL
- Calculate and store BIT scores locally

---

## Core Metric

**BIT_SCORE** (Buyer Intent Tool)
- Aggregation: weighted_average
- Healthy: >= 0.7
- Degraded: >= 0.4
- Critical: < 0.4

---

## Error Codes

| Code | Trigger | Resolver |
|------|---------|----------|
| `CT_UPSTREAM_CL_NOT_VERIFIED` | CL gate failed | CL repo |
| `CT_MATCH_*` | Phase 1 failure | Human |
| `CT_DOMAIN_*` | Phase 2 failure | Agent |
| `CT_PATTERN_*` | Phase 3 failure | Human |
| `CT_TIER2_EXHAUSTED` | All Tier-2 failed | Human |
| `CT_LIFECYCLE_GATE_FAIL` | Lifecycle < ACTIVE | Wait |

---

## Related Documents

- [[PRD_COMPANY_HUB]]
- [[ADR-001_Hub_Spoke_Architecture]]
- [[CL_ADMISSION_GATE_DOCTRINE]]
- [[BIT-Doctrine]]

---

## Key Files

| File | Purpose |
|------|---------|
| `hubs/company-target/hub.manifest.yaml` | Hub configuration |
| `hubs/company-target/PRD.md` | Product requirements |
| `hubs/company-target/ADR.md` | Architecture decisions |
| `hubs/company-target/CHECKLIST.md` | Compliance checklist |
| `hubs/company-target/DOCTRINE.md` | Governing context |
| `hubs/company-target/CERTIFICATION.md` | Verification record |

---

## Tags

#company-target #sub-hub #04-04-01 #internal-anchor #cl-child #architecture

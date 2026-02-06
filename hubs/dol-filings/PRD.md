# PRD — DOL Filings Sub-Hub

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | 1.1.0 |
| **CTB Version** | 1.0.0 |
| **CC Layer** | CC-03 (Context within CC-02 Hub) |

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
| **Parent Hub** | outreach-core |
| **Parent Hub ID** | outreach-core-001 |
| **Hub Name** | DOL Filings |
| **Hub ID** | HUB-DOL-001 |
| **Doctrine ID** | 04.04.03 |
| **Owner** | Outreach Team |
| **Version** | 2.0.0 |

---

## 3. Process Identity (CC-04)

| Field | Value |
|-------|-------|
| **PID Pattern** | `HUB-DOL-001-${TIMESTAMP}-${RANDOM_HEX}` |
| **Session Pattern** | `HUB-DOL-001-session-${SESSION_ID}` |
| **Context Binding** | outreach_context_id |

---

## 4. Purpose

Attach regulatory filings (Form 5500, 5500-SF, Schedule A/C/D/G/H/I) to **existing companies**.
Source of truth for plan renewal dates, broker relationships, service provider compensation, DFE participation, and financial information.

### Data Coverage (as of 2026-02-10)

| Metric | Value |
|--------|-------|
| **Filing Tables** | 26 (dol schema) |
| **Years Loaded** | 2023, 2024, 2025 |
| **Total Rows** | 10,970,626 |
| **Column Comments** | 1,081 (100% coverage) |
| **Column Metadata Catalog** | 1,081 entries in dol.column_metadata |

### Filing Table Inventory

| Group | Tables | Purpose |
|-------|--------|---------|
| Form 5500 | form_5500, form_5500_sf, form_5500_sf_part7 | Core filing data (full + short form) |
| Schedule A | schedule_a, schedule_a_part1 | Insurance contracts & broker commissions |
| Schedule C | schedule_c + 8 sub-tables | Service provider compensation |
| Schedule D | schedule_d + 3 sub-tables | DFE/pooled investment participation |
| Schedule DCG | schedule_dcg | D/C/G cross-reference |
| Schedule G | schedule_g + 3 sub-tables | Financial transactions (loans, non-exempt) |
| Schedule H | schedule_h + 1 sub-table | Large plan financial information |
| Schedule I | schedule_i + 1 sub-table | Small plan financial information |

---

## 3.1 Waterfall Position

**Position**: 3rd in canonical waterfall (after CT, before People)

```
1. CL ──────────► PASS ──┐  (EXTERNAL)
                         │ company_unique_id
                         ▼
2. COMPANY TARGET ► PASS ──┐
                           │ verified_pattern, domain
                           ▼
3. DOL FILINGS ───► PASS ──┐  ◄── YOU ARE HERE
                           │ ein, filing_signals
                           ▼
4. PEOPLE ────────► PASS ──┐
                           ▼
5. BLOG ──────────► PASS
```

### Upstream Dependencies

| Upstream | Required Signal | Gate |
|----------|-----------------|------|
| Company Target | company_unique_id | MUST have passed |
| Company Target | domain | MUST be resolved |

### Downstream Consumers

| Downstream | Signals Emitted | Binding |
|------------|-----------------|---------|
| People Intelligence | filing_signals, regulatory_data | outreach_context_id |
| Blog Content | filing_signals | outreach_context_id |

### Waterfall Rules (LOCKED)

- Company Target must PASS before this hub executes
- This hub must PASS before People Intelligence executes
- No retry/rescue from downstream hubs
- Failures stay local — downstream sees FAIL, not partial data

---

## 3.2 External Dependencies & Program Scope

### CL is EXTERNAL to Outreach

| Boundary | System | Ownership |
|----------|--------|-----------|
| **External** | Company Lifecycle (CL) | Mints company_unique_id, shared across all programs |
| **Program** | Outreach Orchestration | Mints outreach_context_id, program-scoped |
| **Sub-Hub** | DOL Filings (this hub) | Second enrichment sub-hub in waterfall |

### Key Doctrine

- **CL is external** — Outreach CONSUMES company_unique_id, does NOT invoke CL
- **No CL gating** — Outreach does NOT verify company existence (CL already did)
- **Run identity** — All operations bound by outreach_context_id from Orchestration
- **Context table** — outreach.outreach_context is the root audit record

### Explicit Prohibitions

- [ ] Does NOT invoke Company Lifecycle (CL is external)
- [ ] Does NOT mint company_unique_id (CL does)
- [ ] Does NOT verify company existence (CL already did)
- [ ] Does NOT create outreach_context_id (Orchestration does)

---

## 4. Lifecycle Gate

| Minimum Lifecycle State | Gate Condition |
|-------------------------|----------------|
| ACTIVE | Requires lifecycle >= ACTIVE |

---

## 5. Inputs

| Input | Source | Required |
|-------|--------|----------|
| company_sov_id | Company Lifecycle (external) | YES |
| DOL CSV files | Federal DOL data | YES |

---

## 6. Pipeline

```
Load DOL CSV ZIPs (26 table types per year)
 ↓
import_dol_year.py --year YYYY --load
 ↓
Parse and validate records (handle schema variations per year)
 ↓
Column deduplication + VARCHAR width enforcement
 ↓
Batch COPY into Neon (import_mode session variable)
 ↓
Verify ACK_ID cross-table integrity
 ↓
EIN Matching (exact match only, no fuzzy)
 ↓
Match found?
  ├─ YES → Attach filing to company → Emit signals
  └─ NO → STOP (no retries on mismatch)
```

### Multi-Year Load Summary

| Year | Tables | Rows | Notes |
|------|--------|------|-------|
| 2023 | 24 | ~6,012,077 | Full year, all schedules |
| 2024 | 26 | 4,951,258 | Full year, all 26 table types |
| 2025 | 26 | 7,291 | Partial (early filings) |
| **Total** | **26 unique** | **10,970,626** | **All tables have form_year index** |

---

## 7. Cost Rules

| Rule | Enforcement |
|------|-------------|
| DOL CSV | Bulk processing, free |
| No paid tools | This hub uses no paid enrichment |
| No retries | Exact EIN match or fail |

---

## 8. Tools

| Tool | Tier | Cost Class |
|------|------|------------|
| DOL CSV | Bulk | Free |

---

## 9. Signals Emitted

| Signal | BIT Impact |
|--------|-----------|
| FORM_5500_FILED | +5.0 |
| LARGE_PLAN | +8.0 |
| BROKER_CHANGE | +7.0 |

---

## 10. Constraints

- [ ] Bulk CSV only
- [ ] Exact EIN match (no fuzzy)
- [ ] No retries on mismatch
- [ ] Emits signals only — no enrichment

---

## 11. Core Metric

**FILING_MATCH_RATE** — Percentage of filings matched to company_master

Healthy Threshold: >= 90%

---

## 12. Upstream Dependencies, Signal Validity, and Downstream Effects

### Execution Position

**Second in canonical order** — After Company Target, before People Intelligence.

### Required Upstream PASS Conditions

| Upstream | Condition |
|----------|-----------|
| Company Target | PASS (company exists with company_sov_id) |
| Company Target | Domain resolved (for cross-reference) |

### Signals Consumed (Origin-Bound)

| Signal | Origin | Validity |
|--------|--------|----------|
| company_sov_id | Company Lifecycle (via CT) | Run-bound to outreach_context_id |
| domain | Company Target | Run-bound to outreach_context_id |

### Signals Emitted

| Signal | Consumers | Validity |
|--------|-----------|----------|
| FORM_5500_FILED | People, Blog | Run-bound to outreach_context_id |
| LARGE_PLAN | People, Blog | Run-bound to outreach_context_id |
| BROKER_CHANGE | People, Blog | Run-bound to outreach_context_id |
| filing_data | Monitoring | Run-bound to outreach_context_id |

### Downstream Effects

| If This Hub | Then |
|-------------|------|
| PASS | People Intelligence may execute |
| FAIL | People, Blog do NOT execute |

### Explicit Prohibitions

- [ ] May NOT consume People Intelligence or Blog signals
- [ ] May NOT unlock People Intelligence alone (CT must also PASS)
- [ ] May NOT fix Company Target errors
- [ ] May NOT refresh signals from prior contexts
- [ ] May NOT retry EIN matches (exact match or FAIL)

---

## Approval

| Role | Name | Date |
|------|------|------|
| Owner | | |
| Reviewer | | |

---

**Last Updated**: 2026-02-10
**Hub**: DOL Filings (04.04.03)
**Doctrine**: External CL + Outreach Program v1.0
**ERD Reference**: docs/diagrams/erd/DOL_SUBHUB.mmd
**Schema Reference**: hubs/dol-filings/SCHEMA.md

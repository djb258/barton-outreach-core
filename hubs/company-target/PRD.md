# PRD — Company Target Sub-Hub

## 1. Overview

- **System Name:** Barton Outreach Core
- **Hub Name:** Company Target
- **Owner:** Outreach Team
- **Version:** 1.0.0

---

## 2. Hub Identity

| Field | Value |
|-------|-------|
| **Hub ID** | HUB-CT-001 |
| **Doctrine ID** | 04.04.01 |
| **Process ID** | Set at runtime |

---

## 3. Purpose

Determine **outreach readiness** for lifecycle-qualified companies.
Internal anchor table that links all other sub-hubs together.
Receives `company_sov_id` from Company Lifecycle parent — does NOT mint companies.

---

## 3.1 Waterfall Position

**Position**: 2nd in canonical waterfall (after CL, before DOL)

```
1. CL ──────────► PASS ──┐
                         │ company_unique_id
                         ▼
2. COMPANY TARGET ► PASS ──┐  ◄── YOU ARE HERE
                           │ verified_pattern, domain
                           ▼
3. DOL FILINGS ───► PASS ──┐
                           │ ein, filing_signals
                           ▼
4. PEOPLE ────────► PASS ──┐
                           ▼
5. BLOG ──────────► PASS
```

### Upstream Dependencies

| Upstream | Required Signal | Gate |
|----------|-----------------|------|
| Company Lifecycle (CL) | company_unique_id | MUST exist in cl.company_identity |
| Company Lifecycle (CL) | lifecycle_state | MUST be >= ACTIVE |

### Downstream Consumers

| Downstream | Signals Emitted | Binding |
|------------|-----------------|---------|
| DOL Filings | company_unique_id, domain | outreach_context_id |
| People Intelligence | verified_pattern, domain | outreach_context_id |
| Blog Content | company_unique_id | outreach_context_id |

### Waterfall Rules (LOCKED)

- This hub must PASS before DOL Filings executes
- No retry/rescue from downstream hubs
- Failures stay local — downstream sees FAIL, not partial data
- May re-run if CL upstream unchanged

---

## 3.2 External Dependencies & Program Scope

### CL is EXTERNAL to Outreach

| Boundary | System | Ownership |
|----------|--------|-----------|
| **External** | Company Lifecycle (CL) | Mints company_unique_id, shared across all programs |
| **Program** | Outreach Orchestration | Mints outreach_context_id, program-scoped |
| **Sub-Hub** | Company Target (this hub) | First enrichment sub-hub in waterfall |

### Key Doctrine

- **CL is external** — Outreach CONSUMES company_unique_id, does NOT invoke CL
- **No CL gating** — Outreach does NOT verify company existence (CL already did)
- **Run identity** — All operations bound by outreach_context_id from Orchestration
- **Context table** — outreach.outreach_context is the root audit record

### outreach_context_id Source

This hub receives `outreach_context_id` from **Outreach Orchestration** (Context Authority):

```sql
-- outreach.outreach_context (owned by Orchestration, read by sub-hubs)
outreach_context_id   UUID PRIMARY KEY
company_unique_id     TEXT NOT NULL      -- from CL (external)
program_name          TEXT NOT NULL DEFAULT 'outreach'
run_reason            TEXT NULL          -- campaign, retry, refresh, etc.
initiated_by          TEXT NOT NULL      -- human / agent
initiated_at          TIMESTAMP NOT NULL
status                TEXT NOT NULL      -- OPEN | COMPLETE | FAILED
```

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
| lifecycle_state | Company Lifecycle (external) | YES |
| outreach_context_id | contexts/outreach_context | YES |

---

## 6. Pipeline

```
CL UPSTREAM GATE (FIRST - before ANY logic)
  ├─ Check company_sov_id exists in cl.company_identity
  ├─ EXISTS → EXISTENCE_PASS → proceed
  └─ MISSING → CT_UPSTREAM_CL_NOT_VERIFIED → STOP
 ↓
Validate lifecycle permission (>= ACTIVE)
 ↓
Phase 1: Company Matching
 ↓
Phase 2: Domain Resolution (DNS/MX check)
 ↓
Phase 3: Email Pattern Waterfall
    ├─ Tier 0 (Free): Firecrawl, Google Places
    ├─ Tier 1 (Low): Hunter, Clearbit, Apollo
    └─ Tier 2 (Premium): Prospeo, Snov, Clay [MAX 1 per context]
 ↓
Pattern found?
  ├─ YES → Phase 4: Pattern Verification → Emit signals
  └─ NO → Check BIT threshold
           ├─ BIT < 25 → STOP
           └─ BIT >= 25 → Queue for next context
```

---

## 7. Cost Rules

| Rule | Enforcement |
|------|-------------|
| Tier-0 tools | Unlimited (free) |
| Tier-1 tools | Gated by lifecycle >= ACTIVE |
| Tier-2 tools | Max ONE attempt per outreach_context |
| All spend | Logged against context + company_sov_id |
| Firewall | Must block illegal calls |

---

## 8. Tools

| Tool | Tier | Cost Class | ADR |
|------|------|------------|-----|
| Firecrawl | 0 | Free | N/A |
| Google Places | 0 | Low | N/A |
| Hunter.io | 1 | Low | ADR-CT-001 |
| Clearbit | 1 | Low | ADR-CT-001 |
| Apollo | 1 | Low | ADR-CT-001 |
| Prospeo | 2 | Premium | ADR-CT-002 |
| Snov | 2 | Premium | ADR-CT-002 |
| Clay | 2 | Premium | ADR-CT-002 |
| SMTP Check | Local | Free | N/A |

---

## 9. Outputs

| Output | Destination |
|--------|-------------|
| company_target record | outreach.company_target table |
| email_pattern | Stored with confidence score |
| BIT signals | Emitted to BIT Engine |

---

## 10. Constraints

- [ ] Does NOT mint companies (company_sov_id comes from CL)
- [ ] Does NOT mutate lifecycle state
- [ ] Does NOT implement CL existence checks (domain, name, state verification)
- [ ] Does NOT retry or repair missing CL signals
- [ ] Requires outreach_context_id for all operations
- [ ] Requires CL existence verification (EXISTENCE_PASS) before any logic
- [ ] Tier-2 tools limited to one attempt per context
- [ ] All spend logged to spend_log

---

## 11. Core Metric

**BIT_SCORE** — Buyer Intent Tool weighted average

---

## 12. Upstream Dependencies, Signal Validity, and Downstream Effects

### Execution Position

**First in canonical order** — No upstream sub-hub dependencies.

### Required Upstream PASS Conditions

| Upstream | Condition |
|----------|-----------|
| Company Lifecycle (CL) | company_sov_id exists and is valid |
| Company Lifecycle (CL) | lifecycle_state >= ACTIVE |

### Signals Consumed (Origin-Bound)

| Signal | Origin | Validity |
|--------|--------|----------|
| company_sov_id | Company Lifecycle | Run-bound to outreach_context_id |
| lifecycle_state | Company Lifecycle | Run-bound to outreach_context_id |

### Signals Emitted

| Signal | Consumers | Validity |
|--------|-----------|----------|
| domain | DOL, People, Blog | Run-bound to outreach_context_id |
| email_pattern | People Intelligence | Run-bound to outreach_context_id |
| pattern_confidence | People Intelligence | Run-bound to outreach_context_id |
| BIT_SCORE | All downstream | Run-bound to outreach_context_id |

### Downstream Effects

| If This Hub | Then |
|-------------|------|
| PASS | DOL Filings may execute |
| FAIL | DOL, People, Blog do NOT execute |

### Explicit Prohibitions

- [ ] May NOT consume signals from DOL, People, or Blog
- [ ] May NOT repair downstream failures
- [ ] May NOT re-query CL for "fresher" data within same context
- [ ] May NOT refresh signals from prior contexts

---

---

## 13. Tables Owned

This sub-hub owns or writes to the following tables:

### Primary Tables

| Schema | Table | Purpose | Row Count |
|--------|-------|---------|-----------|
| `outreach` | `company_target` | Internal anchor (FK to CL) | ~500 |
| `outreach` | `column_registry` | Column metadata registry | ~60 |

### Legacy Tables (Read + Write)

| Schema | Table | Purpose | Migration Status |
|--------|-------|---------|------------------|
| `marketing` | `company_master` | Master company records | Migrating to CL |
| `marketing` | `company_slot` | Slot assignments | Stays (People Hub) |
| `marketing` | `pipeline_events` | Pipeline audit trail | Shared |

### Read-Only Tables (From CL)

| Schema | Table | Purpose |
|--------|-------|---------|
| `cl` | `company_identity` | Sovereign company records |
| `cl` | `lifecycle_state` | Current lifecycle state |

---

## 14. ERD — Company Target Tables

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     COMPANY TARGET TABLE RELATIONSHIPS                       │
└─────────────────────────────────────────────────────────────────────────────┘

                    cl.company_identity (CL PARENT)
                    ──────────────────────────────
                    • company_unique_id PK (SOVEREIGN)
                    • legal_name
                    • created_at
                                    │
                                    │ company_unique_id (FK)
                                    │ ON DELETE RESTRICT
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     outreach.company_target (INTERNAL ANCHOR)                │
├─────────────────────────────────────────────────────────────────────────────┤
│ target_id              TEXT      PK   Target identifier                     │
│ company_unique_id      TEXT      FK   → cl.company_identity                 │
│ outreach_status        TEXT           queued, active, paused, completed     │
│ bit_score_snapshot     NUMERIC        Local BIT score cache                 │
│ first_targeted_at      TIMESTAMP      First outreach attempt                │
│ last_targeted_at       TIMESTAMP      Most recent attempt                   │
│ sequence_count         INTEGER        Number of sequences run               │
│ created_at             TIMESTAMP      Record creation                       │
│ updated_at             TIMESTAMP      Last modification                     │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    │ target_id (FK)
        ┌───────────┼───────────┬───────────────┐
        ▼           ▼           ▼               ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│ outreach │ │ outreach │ │ outreach │ │ marketing    │
│ .people  │ │ .dol_    │ │ .blog_   │ │ .company_    │
│          │ │ filings  │ │ signals  │ │ master       │
│ (PI Hub) │ │ (DOL Hub)│ │ (BC Hub) │ │ (Legacy)     │
└──────────┘ └──────────┘ └──────────┘ └──────────────┘
```

### Column Details — outreach.company_target

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `target_id` | TEXT | PK | Unique target identifier |
| `company_unique_id` | TEXT | NOT NULL, FK | Links to CL parent |
| `outreach_status` | TEXT | DEFAULT 'queued' | Current outreach state |
| `bit_score_snapshot` | NUMERIC | | Cached BIT score |
| `first_targeted_at` | TIMESTAMP | | First targeting timestamp |
| `last_targeted_at` | TIMESTAMP | | Most recent targeting |
| `sequence_count` | INTEGER | DEFAULT 0 | Sequences executed |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last update |

### Indexes

| Index Name | Columns | Purpose |
|------------|---------|---------|
| `idx_target_company` | `company_unique_id` | FK lookup performance |
| `idx_target_status` | `outreach_status` | Status filtering |

---

## Approval

| Role | Name | Date |
|------|------|------|
| Owner | | |
| Reviewer | | |

---

**Last Updated**: 2026-01-02
**Hub**: Company Target (04.04.01)
**Doctrine**: External CL + Outreach Program v1.0

# Waterfall Architecture — Outreach Program Flow

**Version:** 1.0.0
**Status:** ACTIVE
**Date:** 2026-01-09
**Author:** Claude Code (IMO-Creator)
**Barton ID:** `04.04.00.00.50000.001`

---

## Purpose

This document defines the **complete waterfall architecture** for the Barton Outreach Program. The waterfall enforces a strict execution order where each sub-hub must PASS before downstream hubs can execute.

**Golden Rule:**
```
WATERFALL = FORWARD ONLY
NO LATERAL READS | NO SPECULATIVE EXECUTION | NO BYPASS
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SYSTEM (NOT OUTREACH)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  COMPANY LIFECYCLE (CL)                                                      │
│  ══════════════════════                                                      │
│  Repository: https://github.com/djb258/company-lifecycle-cl.git              │
│                                                                              │
│  Purpose:                                                                    │
│    - Mints company_unique_id (SOVEREIGN, IMMUTABLE)                          │
│    - Owns cl.* schema (company_identity, lifecycle_state)                    │
│    - Shared across programs (Outreach, Client Intake, Analytics)             │
│                                                                              │
│  Key Table: cl.company_identity                                              │
│    - company_unique_id (UUID) — Sovereign identifier                         │
│    - identity_status (TEXT) — PASS | FAIL | PENDING                          │
│                                                                              │
│  Gate: identity_status = 'PASS' required for Outreach                        │
│                                                                              │
│  Current Stats:                                                              │
│    - Total: 71,823 records                                                   │
│    - PASS: 63,911 (88.99%)                                                   │
│    - FAIL: 7,912 (11.01%)                                                    │
│                                                                              │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        │ sovereign_id (WHERE identity_status = 'PASS')
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OUTREACH SPINE (Layer 0)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Table: outreach.outreach                                                    │
│  ═══════════════════════                                                     │
│                                                                              │
│  Purpose:                                                                    │
│    - Mints outreach_id (THE identity for all Outreach sub-hubs)              │
│    - sovereign_id is receipt to CL (sub-hubs DON'T see this)                 │
│    - Gate: Only identity_status = 'PASS' from CL allowed                     │
│                                                                              │
│  Key Columns:                                                                │
│    - outreach_id (UUID PK) — Program identity                                │
│    - sovereign_id (UUID FK) — Links to cl.company_identity                   │
│                                                                              │
│  Current Stats:                                                              │
│    - Total: 63,911 records                                                   │
│    - 100% linked to CL (no orphans)                                          │
│                                                                              │
│  FK Constraints:                                                             │
│    - fk_outreach_sovereign -> cl.company_identity(company_unique_id)         │
│                                                                              │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        │ outreach_id
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUB-HUB LAYER (Layers 1-4)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  All sub-hubs:                                                               │
│    - FK to outreach_id (never see sovereign_id directly)                     │
│    - Have dedicated error tables                                             │
│    - Follow IMO pattern (Input → Middle → Output)                            │
│                                                                              │
│         ┌─────────────────────────────────────────────────────────────┐      │
│         │                                                             │      │
│    ┌────┴────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐          │      │
│    │ COMPANY │    │   DOL   │    │  BLOG   │    │ PEOPLE  │          │      │
│    │ TARGET  │    │         │    │         │    │         │          │      │
│    │ (1)     │    │ (2)     │    │ (3)     │    │ (4)     │          │      │
│    └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘          │      │
│         │              │              │              │               │      │
│         │              │              │              │               │      │
│         ▼              ▼              ▼              ▼               │      │
│    outreach.      outreach.     outreach.     people.               │      │
│    company_       dol           blog          company_              │      │
│    target                                     slot                  │      │
│                                                                              │
│    Error:         Error:        Error:        Error:                        │
│    outreach.      outreach.     outreach.     people.                       │
│    company_       dol_errors    blog_errors   slot_errors                   │
│    target_errors                                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Sub-Hub Details

### 1. Company Target (04.04.01)

**Table:** `outreach.company_target`

| Column | Type | Purpose |
|--------|------|---------|
| `company_target_id` | UUID PK | Sub-hub identity |
| `outreach_id` | UUID FK | Links to spine |
| `company_unique_id` | TEXT | Legacy company reference |
| `domain` | TEXT | Verified company domain |
| `verified_pattern` | TEXT | Email pattern discovered |
| `bit_score` | INTEGER | Company targeting score |

**Purpose:**
- Domain resolution and email pattern discovery
- BIT score calculation for targeting priority
- Emits: `verified_pattern`, `domain`

**Error Table:** `outreach.company_target_errors`

---

### 2. DOL Filings (04.04.03)

**Table:** `outreach.dol`

| Column | Type | Purpose |
|--------|------|---------|
| `dol_id` | UUID PK | Sub-hub identity |
| `outreach_id` | UUID FK | Links to spine |
| `ein` | TEXT | Company EIN |
| `filing_type` | TEXT | Form type (5500, Schedule A) |
| `filing_signals` | JSONB | Extracted signals |

**Purpose:**
- EIN resolution and Form 5500 data
- Schedule A broker/consultant analysis
- Emits: `ein`, `filing_signals`, `funding_type`

**Error Table:** `outreach.dol_errors`

**Related:** `dol.ein_linkage` (9,365 records pending outreach_id backfill)

---

### 3. Blog Content (04.04.05)

**Table:** `outreach.blog`

| Column | Type | Purpose |
|--------|------|---------|
| `blog_id` | UUID PK | Sub-hub identity |
| `outreach_id` | UUID FK | Links to spine |
| `source_type` | ENUM | blog, news, press_release, etc. |
| `source_url` | TEXT | Content URL |
| `content_signals` | JSONB | Extracted content signals |

**Purpose:**
- Content signal extraction (news, blog posts, press releases)
- News monitoring for engagement triggers
- Emits: `content_signals`, `topic_tags`

**Error Table:** `outreach.blog_errors`

**Kill Switch:** `outreach.blog_ingress_control` (default: disabled)

---

### 4. People Intelligence (04.04.02)

**Table:** `people.company_slot`

| Column | Type | Purpose |
|--------|------|---------|
| `company_slot_unique_id` | TEXT PK | Slot identity |
| `outreach_id` | UUID FK | Links to spine [R0_003] |
| `company_unique_id` | TEXT | Legacy company reference |
| `slot_type` | TEXT | CEO, CFO, HR Director, etc. |
| `person_id` | UUID | Assigned person (nullable) |

**Purpose:**
- Slot assignment for target companies
- Consumes: `verified_pattern` (CT), `ein/signals` (DOL)
- Emits: `slot_assignments`, `people_records`

**Error Table:** `people.slot_errors`

**Current Stats:**
- Total: 191,808 slots
- Linked: 191,733 (99.96%)
- Quarantined: 75 (0.04%)

**FK Constraint:** `fk_company_slot_outreach` [R0_003]

---

## Bridge Tables

### CL Company Identity Bridge

**Table:** `cl.company_identity_bridge`

| Column | Type | Purpose |
|--------|------|---------|
| `company_sov_id` | UUID | Links to cl.company_identity.company_unique_id |
| `source_company_id` | TEXT | Links to company.company_master.company_unique_id |

**Purpose:**
- Resolves UUID ↔ TEXT datatype mismatch
- CL uses UUID, downstream schemas use TEXT
- Required for deriving outreach_id from legacy TEXT identifiers

**Derivation Path:**
```sql
-- Derive outreach_id from TEXT company_unique_id
SELECT o.outreach_id
FROM company.company_master cm
JOIN cl.company_identity_bridge cib ON cm.company_unique_id = cib.source_company_id
JOIN outreach.outreach o ON cib.company_sov_id = o.sovereign_id
WHERE cm.company_unique_id = 'some-text-id';
```

---

## Waterfall Rules

### Rule 1: Forward-Only Flow

```
CL → Spine → CT → DOL → Blog → People → BIT
          ↓     ↓      ↓       ↓
       ERROR  ERROR  ERROR   ERROR
```

Data flows FORWARD ONLY. No lateral reads between sub-hubs.

### Rule 2: PASS Gate

Each sub-hub must PASS before downstream hubs execute:

| Stage | Gate | Failure |
|-------|------|---------|
| CL | `identity_status = 'PASS'` | Record never enters Outreach |
| Spine | Valid `sovereign_id` | No `outreach_id` minted |
| CT | Domain resolved | Lands in `company_target_errors` |
| DOL | EIN matched | Lands in `dol_errors` |
| Blog | Content ingested | Lands in `blog_errors` |
| People | Slot assigned | Lands in `slot_errors` |

### Rule 3: No Speculative Execution

Sub-hubs do NOT execute speculatively. They wait for upstream PASS:

```
IF upstream_status != 'PASS':
    WAIT (do not execute)
```

### Rule 4: Error = Work Item

Failed records land in error tables, NOT deleted:

```
FAIL at any stage → record lands in that sub-hub's error table
Fix the issue → record re-enters pipeline at that stage
```

### Rule 5: Idempotent Re-execution

Sub-hubs may re-run if upstream unchanged (history sidecar tables prevent duplicate work):

```sql
-- Check if already processed
SELECT EXISTS (SELECT 1 FROM outreach.blog_source_history WHERE source_url = ?);
```

---

## FK Constraint Map

| Table | Constraint | References | ON DELETE | ON UPDATE |
|-------|------------|------------|-----------|-----------|
| `outreach.outreach` | `fk_outreach_sovereign` | `cl.company_identity` | RESTRICT | CASCADE |
| `outreach.company_target` | `fk_company_target_outreach` | `outreach.outreach` | RESTRICT | CASCADE |
| `outreach.dol` | `fk_dol_outreach` | `outreach.outreach` | RESTRICT | CASCADE |
| `outreach.blog` | `fk_blog_outreach` | `outreach.outreach` | RESTRICT | CASCADE |
| `people.company_slot` | `fk_company_slot_outreach` | `outreach.outreach` | RESTRICT | CASCADE |

**ON DELETE RESTRICT:** Cannot delete spine record if sub-hub records exist.
**ON UPDATE CASCADE:** If outreach_id changes (rare), sub-hub records follow.

---

## Data Flow Statistics

### Current Pipeline State

| Layer | Table | Records | Linked | Coverage |
|-------|-------|---------|--------|----------|
| CL | `cl.company_identity` | 71,823 | N/A | 100% |
| CL (PASS) | — | 63,911 | N/A | 88.99% |
| Spine | `outreach.outreach` | 63,911 | 63,911 | 100% |
| CT | `outreach.company_target` | 18,302 | 18,302 | 100% |
| DOL | `outreach.dol` | TBD | TBD | TBD |
| Blog | `outreach.blog` | TBD | TBD | TBD |
| People | `people.company_slot` | 191,808 | 191,733 | 99.96% |

### Quarantine Summary

| Table | Quarantined | Reason |
|-------|-------------|--------|
| `people.company_slot` | 75 | 18 NO_BRIDGE_ENTRY, 57 NO_OUTREACH_RECORD |

---

## Spoke Contracts

Spokes are I/O ONLY — no logic, no state, no transformation.

| Spoke | Direction | From | To | Payload |
|-------|-----------|------|-----|---------|
| `target-people` | Bidirectional | CT | People | slot_requirement / slot_assignment |
| `target-dol` | Bidirectional | CT | DOL | ein_lookup / filing_signal |
| `target-outreach` | Bidirectional | CT | Execution | target_selection / engagement_signal |
| `people-outreach` | Bidirectional | People | Execution | contact_selection / contact_state |
| `cl-identity` | Ingress Only | CL | Spine | sovereign_id |

---

## Kill Switches

| Switch | Table | Default | Purpose |
|--------|-------|---------|---------|
| Blog Ingress | `outreach.blog_ingress_control` | DISABLED | Gate blog content ingestion |
| Blog Canary | `outreach.blog_ingress_control.canary_enabled` | FALSE | Limit to allowlist only |
| Slot Ingress | `people.slot_ingress_control` | DISABLED | Gate slot assignment |

**Enabling Blog Ingress:**
```sql
UPDATE outreach.blog_ingress_control
SET enabled = TRUE,
    enabled_at = NOW(),
    enabled_by = 'operator',
    notes = 'Production enablement';
```

---

## Related Documents

- [[PATH_INTEGRITY_DOCTRINE]] — Waterfall join enforcement rules
- [[R0_REMEDIATION_REPORT]] — Path integrity remediation details
- [[P0_VALIDATION_CHECKLIST]] — Migration validation procedures
- [[CLAUDE.md]] — Bootstrap guide with architecture overview
- [[HUB_SPOKE_ARCHITECTURE]] — Hub-spoke design patterns
- [[ALTITUDE_DESCENT_MODEL]] — Altitude-based schema organization

---

## Audit Conformance

### Daily Audit Query

```sql
-- Run daily to detect path integrity drift
SELECT
    'outreach.company_target' AS table_name,
    COUNT(*) FILTER (WHERE outreach_id IS NULL) AS null_count,
    COUNT(*) FILTER (WHERE outreach_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM outreach.outreach o WHERE o.outreach_id = company_target.outreach_id
    )) AS orphan_count
FROM outreach.company_target

UNION ALL

SELECT
    'outreach.dol',
    COUNT(*) FILTER (WHERE outreach_id IS NULL),
    COUNT(*) FILTER (WHERE outreach_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM outreach.outreach o WHERE o.outreach_id = dol.outreach_id
    ))
FROM outreach.dol

UNION ALL

SELECT
    'outreach.blog',
    COUNT(*) FILTER (WHERE outreach_id IS NULL),
    COUNT(*) FILTER (WHERE outreach_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM outreach.outreach o WHERE o.outreach_id = blog.outreach_id
    ))
FROM outreach.blog

UNION ALL

SELECT
    'people.company_slot',
    COUNT(*) FILTER (WHERE outreach_id IS NULL),
    COUNT(*) FILTER (WHERE outreach_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM outreach.outreach o WHERE o.outreach_id = company_slot.outreach_id
    ))
FROM people.company_slot;
```

**Expected Results:**
- `null_count`: Should match quarantine table count (or 0 for fully backfilled tables)
- `orphan_count`: MUST be 0 (path integrity violation if > 0)

---

**Document Status:** ACTIVE
**Last Updated:** 2026-01-09
**Architecture Version:** CL Parent-Child Doctrine v1.1 (Spine Build)

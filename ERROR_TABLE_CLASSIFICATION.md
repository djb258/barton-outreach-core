# Error Table Classification

**Classification Date**: 2026-02-02
**Scope**: All error tables documented in ERDs and Neon
**Authority**: ERD SCHEMA.md files + Neon introspection (ERD_NEON_DRIFT_REPORT.md)

---

## Summary Table

| Error Table | Hub | Classification | Blocks Promotion | Records | TTL | Disposition |
|-------------|-----|----------------|------------------|---------|-----|-------------|
| `outreach.dol_errors` | DOL Filings | FIXABLE | **YES** | 37,319 | MISSING | MISSING |
| `outreach.company_target_errors` | Company Target | FIXABLE | **YES** | 5,539 | MISSING | MISSING |
| `people.people_errors` | People Intelligence | FIXABLE | YES | 1,053 | MISSING | MISSING |
| `company.url_discovery_failures` | Blog Content | STRUCTURAL | NO | 42,348 | MISSING | MISSING |
| `public.shq_error_log` | Global | STRUCTURAL | NO | 116,361 | MISSING | MISSING |
| `outreach.bit_errors` | BIT Engine | DEAD | NO | 0* | N/A | N/A |
| `outreach.blog_errors` | Blog Content | DEAD | NO | 0* | N/A | N/A |
| `outreach.people_errors` | People Intelligence | DEAD | NO | 0* | N/A | N/A |
| `outreach.outreach_errors` | Outreach Execution | DEAD | NO | 0* | N/A | N/A |
| `cl.cl_errors_archive` | CL Authority | DEAD | NO | 0* | N/A | Archive only |
| `company.pipeline_errors` | Company | DEAD | NO | 0* | N/A | N/A |
| `public.shq_orphan_errors` | Global | STRUCTURAL | NO | Unknown | MISSING | MISSING |
| `public.shq_master_error_log` | Global | STRUCTURAL | NO | Unknown | Defined | Append-only |

**\* = Table documented in ERD but columns not found in Neon (table may not exist)**

---

## Classification Definitions

| Classification | Definition |
|----------------|------------|
| **FIXABLE** | Errors that can be retried or reprocessed. Data exists, operation failed. |
| **STRUCTURAL** | Permanent failures requiring data fixes or manual intervention. |
| **DEAD** | Table documented but not created in Neon, or archived/deprecated. |

---

## Detailed Analysis

### Layer 1: Hub-Owned Error Tables (Local First)

#### outreach.dol_errors

| Field | Value |
|-------|-------|
| **Hub** | DOL Filings (04.04.03) |
| **ERD Source** | `hubs/dol-filings/SCHEMA.md` |
| **Classification** | FIXABLE |
| **Records** | 37,319 |
| **Blocks Promotion** | YES |
| **Schema Status** | ERD columns NOT in Neon (drift detected) |

**ERD-Documented Columns**:
- `error_id` (PK)
- `outreach_id` (FK)
- `pipeline_stage`
- `failure_code`
- `blocking_reason`
- `severity`
- `retry_allowed`
- `raw_input`

**Missing Metadata**:
- TTL: Not defined
- Disposition: Not defined (retry/park/archive)
- Ownership: DOL hub

**Error Type Breakdown**: Unknown - requires Neon query

---

#### outreach.company_target_errors

| Field | Value |
|-------|-------|
| **Hub** | Company Target (04.04.01) |
| **ERD Source** | `hubs/company-target/SCHEMA.md` |
| **Classification** | FIXABLE |
| **Records** | 5,539 |
| **Blocks Promotion** | YES |
| **Schema Status** | ERD columns NOT in Neon (drift detected) |

**ERD-Documented Columns**:
- `error_id` (PK)
- `outreach_id` (FK)
- `pipeline_stage`
- `failure_code`
- `blocking_reason`
- `severity`
- `retry_allowed`
- `raw_input`
- `stack_trace`

**Missing Metadata**:
- TTL: Not defined
- Disposition: Not defined
- Ownership: Company Target hub

---

#### people.people_errors

| Field | Value |
|-------|-------|
| **Hub** | People Intelligence (04.04.02) |
| **ERD Source** | `hubs/people-intelligence/SCHEMA.md` |
| **Classification** | FIXABLE |
| **Records** | 1,053 |
| **Blocks Promotion** | YES |
| **Schema Status** | ERD columns NOT in Neon (drift detected) |

**ERD-Documented Columns**:
- `error_id` (PK)
- `outreach_id` (FK)
- `person_id` (FK)
- `slot_id` (FK)
- `error_stage`
- `error_type`
- `error_code`
- `error_message`
- `raw_payload`
- `retry_strategy`
- `source_hints_used`

**Missing Metadata**:
- TTL: Not defined
- Disposition: Not defined
- Ownership: People hub

---

#### company.url_discovery_failures

| Field | Value |
|-------|-------|
| **Hub** | Blog Content (04.04.05) |
| **ERD Source** | `hubs/blog-content/SCHEMA.md` |
| **Classification** | STRUCTURAL |
| **Records** | 42,348 |
| **Blocks Promotion** | NO |
| **Schema Status** | ERD matches Neon |

**ERD-Documented Columns**:
- `failure_id` (PK)
- `company_unique_id` (FK)
- `domain`
- `failure_reason`
- `created_at`

**Failure Reasons** (from ERD):
- `dns_error` - Domain doesn't resolve
- `timeout` - Request timeout
- `base_url_error` - HTTP error on base URL
- `redirect_loop` - Too many redirects
- `blocked` - Access blocked

**Missing Metadata**:
- TTL: Not defined
- Disposition: Not defined (permanent failures, need data fix)
- Ownership: Blog Content hub

---

### Layer 2: Global Error Tables (Cross-Cutting)

#### public.shq_error_log

| Field | Value |
|-------|-------|
| **Owner** | Platform (Cross-Cutting) |
| **ERD Source** | `docs/prd/PRD_MASTER_ERROR_LOG.md` |
| **Classification** | STRUCTURAL |
| **Records** | 116,361 (~95K unresolved) |
| **Blocks Promotion** | NO |
| **Schema Status** | Exists in Neon |

**Purpose**: Global error visibility across all hubs

**Missing Metadata**:
- TTL: Not defined for individual records
- Disposition: Append-only (no updates/deletes per doctrine)
- Ownership: Platform team

---

#### public.shq_master_error_log

| Field | Value |
|-------|-------|
| **Owner** | Platform (Cross-Cutting) |
| **ERD Source** | `docs/prd/PRD_MASTER_ERROR_LOG.md` |
| **Classification** | STRUCTURAL |
| **Records** | Unknown |
| **Blocks Promotion** | NO |
| **Schema Status** | Defined in PRD, may be same as shq_error_log |

**Has TTL**: No (append-only by design)
**Has Disposition**: Yes (append-only, immutable per PRD v1.1)
**Has Ownership**: Yes (Platform team)

---

#### public.shq_orphan_errors

| Field | Value |
|-------|-------|
| **Owner** | Platform (Cross-Cutting) |
| **ERD Source** | `docs/prd/PRD_MASTER_ERROR_LOG.md` |
| **Classification** | STRUCTURAL |
| **Records** | Unknown |
| **Blocks Promotion** | NO |
| **Schema Status** | Defined in PRD |

**Purpose**: Errors rejected due to missing correlation_id

**Missing Metadata**:
- TTL: Not defined
- Disposition: Investigation queue (manual review)
- Ownership: Platform team

---

### Layer 3: DEAD Tables (Documented but not in Neon)

These tables are documented in ERD but have zero columns matching Neon introspection:

| Table | ERD Source | Status |
|-------|------------|--------|
| `outreach.bit_errors` | `hubs/outreach-execution/SCHEMA.md` | All columns in ERD, none in Neon |
| `outreach.blog_errors` | `hubs/blog-content/SCHEMA.md` | Not introspected |
| `outreach.people_errors` | `hubs/people-intelligence/SCHEMA.md` | All columns in ERD, none in Neon |
| `outreach.outreach_errors` | `hubs/outreach-execution/SCHEMA.md` | Not introspected |
| `cl.cl_errors_archive` | ERD drift report | Archive table |
| `company.pipeline_errors` | `docs/DATABASE_QUERY_RESULTS.md` | Not introspected |

**Action**: These tables should be:
1. Created in Neon if needed
2. Removed from ERD if deprecated
3. Marked as "PLANNED" in ERD if future work

---

## Missing Metadata Summary

| Error Table | TTL Defined | Ownership Defined | Disposition Defined |
|-------------|-------------|-------------------|---------------------|
| `outreach.dol_errors` | NO | YES (DOL hub) | NO |
| `outreach.company_target_errors` | NO | YES (CT hub) | NO |
| `people.people_errors` | NO | YES (People hub) | NO |
| `company.url_discovery_failures` | NO | YES (Blog hub) | NO |
| `public.shq_error_log` | NO | YES (Platform) | PARTIAL |
| `public.shq_master_error_log` | NO | YES (Platform) | YES (append-only) |
| `public.shq_orphan_errors` | NO | YES (Platform) | NO |

---

## Promotion Blocking Analysis

### Errors that BLOCK promotion (require resolution before proceeding):

| Table | Records | Blocking Mechanism |
|-------|---------|-------------------|
| `outreach.dol_errors` | 37,319 | EIN match failures block DOL enrichment |
| `outreach.company_target_errors` | 5,539 | Domain/pattern failures block company_target promotion |
| `people.people_errors` | 1,053 | People processing failures block slot fill |

### Errors that DO NOT block promotion:

| Table | Records | Reason |
|-------|---------|--------|
| `company.url_discovery_failures` | 42,348 | URL discovery is best-effort, not gating |
| `public.shq_error_log` | 116,361 | Global visibility only, no gating |

---

## Error Flow Doctrine (Two-Layer Model)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TWO-LAYER ERROR MODEL                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   LAYER 1: LOCAL (Hub-Owned)                                               │
│   ├── outreach.dol_errors         → DOL hub owns retry/resolution          │
│   ├── outreach.company_target_errors → CT hub owns retry/resolution        │
│   ├── people.people_errors        → People hub owns retry/resolution       │
│   └── company.url_discovery_failures → Blog hub owns retry/resolution      │
│                                                                             │
│   LAYER 2: GLOBAL (Platform-Owned)                                         │
│   ├── public.shq_error_log        → Global visibility, trending            │
│   ├── public.shq_master_error_log → Normalized global errors               │
│   └── public.shq_orphan_errors    → Rejected errors (no correlation_id)    │
│                                                                             │
│   EMISSION RULE:                                                            │
│   • Severity >= WARN → Emit to BOTH layers                                 │
│   • Severity < WARN → Local only                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Gaps Identified

### 1. Missing TTL Policy

No error tables have TTL (Time-To-Live) defined. Errors accumulate indefinitely.

**Impact**:
- `outreach.dol_errors`: 37,319 records with no expiration
- `public.shq_error_log`: 116,361 records (~95K unresolved)

### 2. Missing Disposition Field

No hub-owned error tables have disposition tracking:
- RETRY: Queue for reprocessing
- PARK: Hold for manual review
- ARCHIVE: Move to archive after TTL

### 3. ERD-Neon Drift on Error Tables

Multiple error tables documented in ERD do not exist in Neon:
- `outreach.bit_errors`
- `outreach.blog_errors`
- `outreach.people_errors`
- `outreach.outreach_errors`

### 4. Missing retry_allowed Semantic

Tables document `retry_allowed` column but no defined behavior for:
- When to retry
- Max retry count
- Backoff strategy

---

## Document Control

| Field | Value |
|-------|-------|
| Classification Date | 2026-02-02 |
| Performed By | claude-code |
| ERD Sources | `hubs/*/SCHEMA.md` |
| Data Sources | `docs/DATA_REGISTRY.md`, `ERD_NEON_DRIFT_REPORT.md` |
| Record Counts | From DATA_REGISTRY.md + COMPLETE_SYSTEM_ERD.md |

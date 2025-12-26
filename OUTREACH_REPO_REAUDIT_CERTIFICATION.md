# OUTREACH REPO RE-AUDIT CERTIFICATION

**Audit Date**: 2025-12-26
**Auditor**: Independent Doctrine Auditor
**Audit Type**: Full Repository Re-Audit (Post-Remediation Verification)
**Doctrine Version**: Barton / CL Parent-Child Doctrine v1.0

---

## EXECUTIVE SUMMARY

| Metric | Value |
|--------|-------|
| **OVERALL VERDICT** | **FAIL** |
| **Total Violations** | 30 |
| **CRITICAL** | 12 |
| **HIGH** | 13 |
| **MEDIUM** | 5 |
| **Phases Passed** | 0 / 6 |
| **Phases Partial Pass** | 1 / 6 |
| **Phases Failed** | 5 / 6 |

### Verdict Statement

> **This repository IS NOT doctrine-compliant as of 2025-12-26.**

The Outreach repository has undergone partial remediation (DV-001 directory rename completed), but multiple systemic violations remain across all audit phases. The codebase contains broken imports, incorrect terminology, unauthorized identity operations, missing database objects, and insufficient enforcement mechanisms.

---

## AUDIT SCOPE & GROUND TRUTH

### Locked Doctrine Principles

1. **CL is the SOLE identity authority** - Company Lifecycle (external repo) mints `company_unique_id`
2. **Outreach is a CHILD hub** - Zero identity authority, receives identity from CL
3. **Outreach owns ONLY `outreach.*` schema** - No ownership of `funnel.*`, `marketing.*`, `cl.*`
4. **Company Target is INTERNAL ANCHOR** - Sub-hub type, NOT hub, NOT axle
5. **Column Doctrine** - Every column must have: `column_unique_id`, `column_description`, `column_format`
6. **HARD_FAIL on missing `company_unique_id`** - Cannot proceed without CL identity
7. **Spoke Purity** - I/O only, zero business logic

---

## PHASE-BY-PHASE RESULTS

### PHASE 1: Architecture & Hub Doctrine Audit
**Result**: FAIL
**Violations**: 9 (2 CRITICAL, 6 HIGH, 1 MEDIUM)

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Hub type declaration | `sub-hub` | `sub-hub` | PASS |
| Parent declaration | `HUB-COMPANY-LIFECYCLE` | `HUB-COMPANY-LIFECYCLE` | PASS |
| Axle terminology removed | None | Found in 3+ files | FAIL |
| Import paths valid | All resolve | Multiple broken | FAIL |
| IMO structure | All 4 hubs | 3/4 partial | PARTIAL |

### PHASE 2: Authority & Identity Audit
**Result**: FAIL
**Violations**: 5 (4 CRITICAL, 1 HIGH)

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| No identity minting | Zero | fuzzy matching present | FAIL |
| CL deference pattern | Implemented | Not found | FAIL |
| HARD_FAIL on null ID | Enforced | Not enforced | FAIL |
| company_unique_id source | CL only | Local generation paths | FAIL |

### PHASE 3: Neon Schema Truth Audit
**Result**: FAIL
**Violations**: 4 (2 CRITICAL, 1 HIGH, 1 MEDIUM)

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| outreach.* tables exist | Yes | 4 tables present | PASS |
| funnel.* tables exist | Yes (if referenced) | Empty schema | FAIL |
| FK to cl.company_identity | Enforced | No constraint | FAIL |
| Column comments | All populated | 60/60 have comments | PASS |

### PHASE 4: Column Doctrine Audit
**Result**: PARTIAL PASS
**Violations**: 2 (1 HIGH, 1 MEDIUM)

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| column_registry populated | Yes | 48 entries (80%) | PARTIAL |
| Column unique IDs | OUT.TABLE.XXX | None follow pattern | FAIL |
| Column descriptions | All present | 48/60 documented | PARTIAL |

### PHASE 5: Pipeline & Logic Audit
**Result**: FAIL
**Violations**: 5 (4 CRITICAL, 1 HIGH)

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| No funnel.* references | Zero | Multiple found | FAIL |
| Hub isolation | Complete | Cross-imports exist | FAIL |
| Broken imports | Zero | 5+ broken paths | FAIL |
| Phase registry accurate | Yes | References old paths | FAIL |

### PHASE 6: Enforcement & Regression Audit
**Result**: FAIL
**Violations**: 5 (2 CRITICAL, 3 HIGH)

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| CI guards present | Yes | hub-spoke-guard.yml | PASS |
| Guards effective | Yes | Pattern gaps found | FAIL |
| Identity mint guard | Yes | Not present | FAIL |
| Fuzzy match guard | Yes | Not present | FAIL |

---

## FULL VIOLATIONS TABLE

| DV-ID | Severity | Phase | File / Location | Description |
|-------|----------|-------|-----------------|-------------|
| DV-002 | CRITICAL | 1 | `hubs/company-target/__init__.py` | Docstring declares "AXLE" - forbidden terminology |
| DV-003 | CRITICAL | 1 | `hubs/__init__.py` | Import from `.company_target` fails - directory is `company-target` |
| DV-004 | HIGH | 1 | `hubs/company-target/imo/middle/company_hub.py:1` | Docstring says "Company Intelligence Hub (AXLE)" |
| DV-005 | HIGH | 1 | `hubs/company-target/imo/middle/company_pipeline.py:1` | Docstring says "Company Pipeline (AXLE)" |
| DV-006 | HIGH | 1 | `hubs/company-target/imo/middle/bit_engine.py:1` | Docstring says "BIT Engine (AXLE)" |
| DV-007 | HIGH | 1 | `hubs/company-target/imo/output/neon_writer.py:1` | Docstring says "Neon Writer (AXLE)" |
| DV-008 | HIGH | 1 | `hubs/people-intelligence/__init__.py` | Broken import from `hub.company.company_hub` |
| DV-009 | HIGH | 1 | `hubs/dol-filings/__init__.py` | Broken import from `hub.company.company_hub` |
| DV-010 | MEDIUM | 1 | `hubs/outreach-execution/__init__.py` | Missing __all__ exports |
| DV-011 | CRITICAL | 2 | `hubs/company-target/imo/middle/company_hub.py:find_company_by_name` | Fuzzy matching for identity resolution (CL-only authority) |
| DV-012 | CRITICAL | 2 | `hubs/company-target/imo/middle/company_hub.py` | Uses rapidfuzz for company matching |
| DV-013 | CRITICAL | 2 | `hub/company/utils/fuzzy_arbitration.py` | Entire file dedicated to identity arbitration |
| DV-014 | CRITICAL | 2 | `hubs/company-target/imo/middle/company_hub.py` | No HARD_FAIL guard on null company_unique_id |
| DV-015 | HIGH | 2 | Multiple files | No CL deference pattern implemented |
| DV-016 | CRITICAL | 3 | Neon: `funnel.*` | Schema referenced in code but empty in database |
| DV-017 | CRITICAL | 3 | Neon: `outreach.company_target` | No FK constraint to `cl.company_identity` |
| DV-018 | HIGH | 3 | Neon: `cl.*` | Schema does not exist (expected - external repo) |
| DV-019 | MEDIUM | 3 | Neon: column comments | 60 columns have comments but none use OUT.TABLE.XXX pattern |
| DV-020 | HIGH | 4 | `outreach.column_registry` | Only 48/60 columns registered (80% coverage) |
| DV-021 | MEDIUM | 4 | `outreach.column_registry.column_unique_id` | IDs use `schema.table.column` not `OUT.TABLE.XXX` |
| DV-022 | CRITICAL | 5 | `hubs/company-target/imo/output/neon_writer.py` | INSERT to `funnel.bit_signal_log` - table doesn't exist |
| DV-023 | CRITICAL | 5 | `hubs/company-target/imo/output/neon_writer.py` | INSERT to `funnel.company_intel` - table doesn't exist |
| DV-024 | CRITICAL | 5 | `hubs/company-target/imo/output/neon_writer.py` | INSERT to `funnel.person_intel` - table doesn't exist |
| DV-025 | CRITICAL | 5 | `hubs/outreach-execution/imo/middle/outreach_hub.py` | Import from `hub.company.bit_engine` - path doesn't exist |
| DV-026 | HIGH | 5 | `ctb/sys/toolbox-hub/backend/outreach_phase_registry.py` | References old `backend/` paths |
| DV-027 | CRITICAL | 6 | `.github/workflows/hub-spoke-guard.yml` | Checks `hub_id` at root but manifests use `hub.id` nested |
| DV-028 | CRITICAL | 6 | CI/CD | No guard against identity minting operations |
| DV-029 | HIGH | 6 | CI/CD | No guard against fuzzy matching in Outreach |
| DV-030 | HIGH | 6 | CI/CD | Hub isolation check misses `from hub.company.*` pattern |
| DV-031 | HIGH | 6 | Regression | No automated test for CL deference |

---

## WHAT IS CERTIFIED

The following items PASS doctrine requirements:

1. **Hub Manifest Structure** - `hubs/company-target/hub.manifest.yaml` correctly declares:
   - `type: sub-hub`
   - `parent.hub_id: HUB-COMPANY-LIFECYCLE`
   - `parent.fk_column: company_unique_id`

2. **Directory Rename** - DV-001 remediated: `company-intelligence` renamed to `company-target`

3. **Outreach Schema Tables** - 4 tables exist in Neon:
   - `outreach.company_target`
   - `outreach.people`
   - `outreach.engagement_events`
   - `outreach.column_registry`

4. **Column Comments** - All 60 columns have PostgreSQL comments

5. **CI Workflow Exists** - `.github/workflows/hub-spoke-guard.yml` present

6. **Spoke Structure** - Spokes appear to be I/O only (no business logic found)

---

## WHAT IS NOT CERTIFIED

The following items FAIL doctrine requirements and BLOCK certification:

### CRITICAL (Must Fix Before Re-Certification)

1. **AXLE Terminology** - 4+ files still use "AXLE" in docstrings
2. **Broken Imports** - 5+ Python files have unresolvable import paths
3. **Identity Authority Violation** - Fuzzy matching present in Company Target hub
4. **Missing Tables** - `funnel.*` schema empty but code references 3+ tables
5. **Missing FK Constraint** - No referential integrity to CL
6. **CI Guard Gaps** - Enforcement workflow has pattern matching errors

### HIGH (Should Fix Before Re-Certification)

1. **Column Registry Incomplete** - 20% of columns not registered
2. **Column ID Pattern** - None follow `OUT.TABLE.XXX` format
3. **Phase Registry Stale** - References non-existent paths
4. **No CL Deference Pattern** - Code doesn't implement wait-for-CL logic

---

## REMEDIATION PRIORITY

### Immediate (P0) - Blocks All Progress

| Priority | DV-ID | Action |
|----------|-------|--------|
| P0-1 | DV-016 | Create `funnel.*` tables OR remove all references |
| P0-2 | DV-003,008,009,025 | Fix all broken Python imports |
| P0-3 | DV-011,012,013 | Remove fuzzy matching OR move to CL repo |

### Short-Term (P1) - Required for Certification

| Priority | DV-ID | Action |
|----------|-------|--------|
| P1-1 | DV-002,004,005,006,007 | Replace all "AXLE" with "Sub-Hub" |
| P1-2 | DV-017 | Add FK constraint when CL schema exists |
| P1-3 | DV-027,028,029,030 | Fix CI guard patterns |

### Medium-Term (P2) - Full Compliance

| Priority | DV-ID | Action |
|----------|-------|--------|
| P2-1 | DV-020 | Complete column_registry (100% coverage) |
| P2-2 | DV-021 | Migrate column IDs to OUT.TABLE.XXX format |
| P2-3 | DV-026 | Update phase registry paths |

---

## CERTIFICATION STATEMENT

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   CERTIFICATION STATUS: ❌ FAIL                                             │
│                                                                             │
│   This repository IS NOT doctrine-compliant as of 2025-12-26.              │
│                                                                             │
│   Violations Found: 30 (12 CRITICAL, 13 HIGH, 5 MEDIUM)                    │
│                                                                             │
│   Re-Certification Eligible After:                                          │
│   - All P0 items resolved (3 items)                                        │
│   - All P1 items resolved (3 items)                                        │
│   - CI guards passing                                                       │
│                                                                             │
│   Auditor: Independent Doctrine Auditor                                     │
│   Date: 2025-12-26                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## APPENDIX A: Files Audited

```
hubs/
├── company-target/
│   ├── __init__.py                    # DV-002
│   ├── hub.manifest.yaml              # PASS
│   └── imo/
│       ├── input/
│       ├── middle/
│       │   ├── company_hub.py         # DV-004, DV-011, DV-012
│       │   ├── company_pipeline.py    # DV-005
│       │   └── bit_engine.py          # DV-006
│       └── output/
│           └── neon_writer.py         # DV-007, DV-022-024
├── people-intelligence/
│   └── __init__.py                    # DV-008
├── dol-filings/
│   └── __init__.py                    # DV-009
└── outreach-execution/
    ├── __init__.py                    # DV-010
    └── imo/middle/outreach_hub.py     # DV-025

hub/company/utils/
└── fuzzy_arbitration.py               # DV-013

.github/workflows/
└── hub-spoke-guard.yml                # DV-027-030

infra/scripts/
└── populate_column_registry.py        # Column registry source

ctb/sys/toolbox-hub/backend/
└── outreach_phase_registry.py         # DV-026
```

## APPENDIX B: Neon Schema State

```sql
-- Schemas present
outreach    -- 4 tables (OWNED)
funnel      -- EMPTY (VIOLATION - code references)
cl          -- DOES NOT EXIST (expected - external)
marketing   -- Legacy tables (NOT OWNED)
bit         -- BIT engine tables

-- outreach.* tables
outreach.company_target      -- 11 columns, no FK to CL
outreach.people              -- 20 columns
outreach.engagement_events   -- 17 columns
outreach.column_registry     -- 48 entries (80% coverage)
```

---

**END OF CERTIFICATION REPORT**

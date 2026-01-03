# PRD: DOL Subhub — Filing Discovery & Violation Tracking
## Product Requirements Document

**Document ID**: `PRD-DOL-2025-001`
**Version**: 2.0.0
**Date**: 2025-01-02
**Status**: Approved
**Owner**: Barton Outreach Team

---

## Executive Summary

This PRD defines the requirements for the DOL Subhub capabilities:

1. **Fuzzy Filing Discovery** — Locate Form 5500 filings using approximate string matching
2. **Violation Discovery** — Pull DOL violator data (OSHA, EBSA, WHD) and match to EIN

Both features store **facts only** — downstream systems handle outreach and scoring.

---

## Problem Statement

Form 5500 filings contain inconsistent sponsor names (e.g., "Acme Corp" vs "ACME CORPORATION INC" vs "Acme Corporation, Inc."). The DOL Subhub needs to locate relevant filings for companies with resolved EINs, but exact string matching fails due to this inconsistency.

### Current State
- EIN is resolved upstream in Company Target (LOCKED)
- DOL Subhub requires exact sponsor name match to find filings
- Many valid filings are missed due to name variations

### Desired State
- DOL Subhub uses fuzzy matching to discover candidate filings
- Deterministic validation confirms EIN match before any write
- All failures are visible and actionable

---

## Goals & Non-Goals

### Goals
1. Enable fuzzy matching for Form 5500 filing discovery
2. Maintain strict deterministic EIN validation post-fuzzy
3. Implement `DOL_FILING_NOT_CONFIRMED` error for discovery failures
4. Keep fuzzy logic isolated to DOL Subhub only

### Non-Goals
1. ❌ Fuzzy matching for EIN resolution (Company Target only)
2. ❌ Fuzzy matching for identity resolution
3. ❌ Writing data based on fuzzy match alone
4. ❌ Modifying Company Target or Company Lifecycle

---

## Requirements

### Functional Requirements

#### FR-1: Fuzzy Filing Discovery
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1.1 | System SHALL match company_name against plan_sponsor_name | P0 |
| FR-1.2 | System SHALL match company_name against plan_name | P0 |
| FR-1.3 | System SHALL support company_domain matching (optional) | P1 |
| FR-1.4 | System SHALL support linkedin_company_name matching (optional) | P1 |
| FR-1.5 | System SHALL return ranked candidates with scores | P0 |
| FR-1.6 | System SHALL NOT return a decision, only candidates | P0 |

#### FR-2: Deterministic Validation
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | System SHALL verify EIN in filing exactly matches resolved EIN | P0 |
| FR-2.2 | System SHALL verify filing year is within TTL | P0 |
| FR-2.3 | System SHALL verify sponsor EIN matches (if present) | P0 |
| FR-2.4 | System SHALL reject candidate if any check fails | P0 |

#### FR-3: Error Handling
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | System SHALL emit `DOL_FILING_NOT_CONFIRMED` if all candidates rejected | P0 |
| FR-3.2 | System SHALL write to AIR log on failure | P0 |
| FR-3.3 | System SHALL write to `shq.error_master` on failure | P0 |
| FR-3.4 | System SHALL NOT retry on failure | P0 |

### Non-Functional Requirements

#### NFR-1: Performance
| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1.1 | Fuzzy search response time | < 500ms for 10K filings |
| NFR-1.2 | Maximum candidates returned | 10 |

#### NFR-2: Boundary Enforcement
| ID | Requirement | Status |
|----|-------------|--------|
| NFR-2.1 | Fuzzy logic ONLY in `ctb/sys/dol-ein/` | Enforced |
| NFR-2.2 | NO fuzzy logic in `ctb/sys/company-target/` | Verified |
| NFR-2.3 | NO fuzzy logic in `analytics.v_5500_*` | Verified |

---

## Technical Design

### Architecture

```
Company Target (PASS, EIN locked)
        ↓
DOL Subhub
  ├─ findCandidateFilings() → fuzzy discovery
  │     ├─ tokenSetSimilarity()
  │     ├─ levenshteinSimilarity()
  │     └─ combinedSimilarity()
  │
  ├─ validateCandidatesDeterministic() → EIN checks
  │     ├─ EIN exact match
  │     ├─ Filing TTL check
  │     └─ Sponsor EIN check
  │
  └─ Result
        ├─ PASS → append-only write
        └─ FAIL → DOL_FILING_NOT_CONFIRMED
```

### Files

| File | Purpose |
|------|---------|
| `ctb/sys/dol-ein/findCandidateFilings.js` | Fuzzy discovery + deterministic validation |
| `ctb/sys/dol-ein/ein_validator.js` | Error handling + `failHardFilingNotConfirmed()` |

---

## Part 2: Violation Discovery

### Problem Statement

DOL agencies (OSHA, EBSA, WHD) publish violation data for employers. Companies with violations are prime targets for outreach about remediation services. The DOL Subhub needs to:

1. Pull violator data from DOL sources
2. Match violations to existing EIN linkages
3. Store violation facts for downstream outreach

### Goals

1. Enable violation discovery from multiple DOL agencies
2. Match violations to companies via resolved EIN
3. Store violations as append-only facts
4. Provide views for outreach targeting

### Non-Goals

1. ❌ Scoring violations (downstream handles)
2. ❌ Triggering outreach (downstream handles)
3. ❌ Creating new EIN linkages from violations

### Functional Requirements

#### FR-4: Violation Discovery
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-4.1 | System SHALL pull violations from OSHA, EBSA, WHD, OFCCP | P0 |
| FR-4.2 | System SHALL normalize violations to standard schema | P0 |
| FR-4.3 | System SHALL match violations to EIN via `dol.ein_linkage` | P0 |
| FR-4.4 | System SHALL store violations in append-only table | P0 |
| FR-4.5 | System SHALL NOT create EIN linkages from violations | P0 |

#### FR-5: Violation Views
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-5.1 | System SHALL provide `v_companies_with_violations` view | P0 |
| FR-5.2 | System SHALL provide `v_violation_summary` view | P0 |
| FR-5.3 | System SHALL provide `v_recent_violations` view (90 days) | P0 |

### Violation Architecture — Linkage Chain

```
LINKAGE CHAIN (CORRECT):
  Violation → EIN → Outreach Context ID → Sovereign ID

DOL Sources (OSHA, EBSA, WHD, OFCCP)
        ↓
findViolations.js
  ├─ normalizeViolation() → Standard schema
  ├─ matchViolationToEIN() → Link to dol.ein_linkage
  │       ↓
  │   company_unique_id (from ein_linkage)
  │       ↓
  │   outreach_context_id (from outreach.outreach_context)
  │       ↓
  │   company_unique_id = SOVEREIGN ID
  │
  └─ Result
        ├─ MATCHED → INSERT dol.violations (with both IDs)
        └─ UNMATCHED → Log for enrichment
        
Downstream Outreach
        ↓
READ from dol.v_companies_with_violations
  (includes company_unique_id AND outreach_context_id)
        ↓
Message about remediation services
```

### Key Linkage Fields

| Field | Owner | Purpose |
|-------|-------|---------|
| `ein` | DOL Subhub | Federal identifier (from violation) |
| `outreach_context_id` | Outreach Orchestration | Targeting context for campaign |
| `company_unique_id` | Company Lifecycle (CL) | **SOVEREIGN ID** |

### Violation Files

| File | Purpose |
|------|---------|
| `ctb/sys/dol-ein/findViolations.js` | Violation discovery + EIN matching |
| `doctrine/schemas/dol_violations-schema.sql` | Violations table + views |

---

## Success Metrics

### Filing Discovery
| Metric | Target | Measurement |
|--------|--------|-------------|
| Filing discovery rate | > 85% | Filings found / companies with EIN |
| False positive rate | < 1% | Rejected by deterministic / found by fuzzy |
| Error visibility | 100% | All failures in `shq.error_master` |

### Violation Discovery
| Metric | Target | Measurement |
|--------|--------|-------------|
| Violation match rate | > 70% | Violations matched to EIN / total violations |
| Agency coverage | 4+ | OSHA, EBSA, WHD, OFCCP minimum |
| Outreach view freshness | < 24h | Time from DOL publish to view availability |

---

## Timeline

| Milestone | Date | Status |
|-----------|------|--------|
| PRD Approval | 2025-01-02 | ✅ Complete |
| Fuzzy Filing Implementation | 2025-01-02 | ✅ Complete |
| Violation Discovery Implementation | 2025-01-02 | ✅ Complete |
| Documentation | 2025-01-02 | ✅ Complete |
| Schema Deployment | TBD | Pending |
| DOL Source Integration | TBD | Pending |

---

## Appendix

### Related Documents
- [DOL_EIN_RESOLUTION.md](../../../doctrine/ple/DOL_EIN_RESOLUTION.md) - Doctrine
- [ADR-DOL-FUZZY-BOUNDARY.md](../adr/ADR-DOL-FUZZY-BOUNDARY.md) - Architecture Decision
- [COMPANY_TARGET_IDENTITY.md](../../../doctrine/ple/COMPANY_TARGET_IDENTITY.md) - Upstream doctrine

### Glossary
| Term | Definition |
|------|------------|
| Fuzzy matching | Approximate string matching using similarity algorithms |
| Deterministic validation | Exact match verification of critical fields |
| EIN | Employer Identification Number |
| Form 5500 | Annual return/report for employee benefit plans |

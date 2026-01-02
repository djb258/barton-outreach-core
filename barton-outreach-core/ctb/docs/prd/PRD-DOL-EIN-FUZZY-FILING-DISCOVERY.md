# PRD: DOL EIN Fuzzy Filing Discovery
## Product Requirements Document

**Document ID**: `PRD-DOL-2025-001`
**Version**: 1.0.0
**Date**: 2025-01-02
**Status**: Approved
**Owner**: Barton Outreach Team

---

## Executive Summary

This PRD defines the requirements for implementing fuzzy filing discovery within the DOL Subhub. The feature enables the DOL EIN Resolution Spoke to locate candidate Form 5500 filings using fuzzy matching against sponsor names, while maintaining strict deterministic validation before any data writes.

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

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Filing discovery rate | > 85% | Filings found / companies with EIN |
| False positive rate | < 1% | Rejected by deterministic / found by fuzzy |
| Error visibility | 100% | All failures in `shq.error_master` |

---

## Timeline

| Milestone | Date | Status |
|-----------|------|--------|
| PRD Approval | 2025-01-02 | ✅ Complete |
| Implementation | 2025-01-02 | ✅ Complete |
| Documentation | 2025-01-02 | ✅ Complete |
| Deployment | TBD | Pending |

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

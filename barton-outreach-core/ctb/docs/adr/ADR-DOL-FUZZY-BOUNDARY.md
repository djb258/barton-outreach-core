# ADR: DOL Fuzzy Matching Boundary Decision
## Architecture Decision Record

**ADR ID**: `ADR-DOL-2025-001`
**Date**: 2025-01-02
**Status**: Accepted
**Deciders**: Barton Outreach Team

---

## Context

The DOL Subhub needs to locate Form 5500 filings for companies with resolved EINs. Filing sponsor names are inconsistent (variations in capitalization, suffixes, punctuation). Two options were considered:

1. **Option A**: Add fuzzy matching to Company Target for EIN resolution
2. **Option B**: Add fuzzy matching to DOL Subhub for filing discovery only

---

## Decision

**We chose Option B**: Add fuzzy matching to DOL Subhub for filing discovery only.

---

## Rationale

### Why NOT Option A (Company Target fuzzy EIN resolution)
- Company Target is already locked and stable
- Fuzzy EIN resolution risks attaching wrong EIN to company
- EIN is a sovereign identifier that must be deterministic
- Upstream changes ripple through entire pipeline

### Why Option B (DOL fuzzy filing discovery)
- EIN is already locked from Company Target
- Fuzzy is used ONLY to find candidate filings
- Deterministic validation confirms EIN before any write
- Scope is limited to filing retrieval, not identity
- Failure is visible and actionable

---

## Consequences

### Positive
- Company identity resolution remains pure
- DOL can handle messy sponsor names realistically
- EIN remains the immutable source of truth
- Every failure is logged and traceable

### Negative
- Additional complexity in DOL Subhub
- Potential for `DOL_FILING_NOT_CONFIRMED` errors
- Requires tuning of similarity thresholds

### Neutral
- Fuzzy logic now exists in two places (Company Target for EIN, DOL for filings)
- Clear boundary documentation required

---

## Boundary Enforcement

### Allowed Locations
| Location | Fuzzy Purpose |
|----------|---------------|
| `ctb/sys/company-target/` | EIN resolution (upstream, locked) |
| `ctb/sys/dol-ein/` | Filing discovery only |

### Forbidden Locations
| Location | Reason |
|----------|--------|
| `analytics.v_5500_*` | Read-only views, no logic |
| Anywhere else | Scope containment |

---

## Implementation

### New Error Code
```
DOL_FILING_NOT_CONFIRMED
```

Triggered when fuzzy finds candidates but deterministic validation rejects all.

### Execution Flow
```
Company Target (PASS, EIN locked)
        ↓
DOL Subhub
  ├─ fuzzy → candidate filings
  ├─ deterministic validation
        ├─ PASS → append-only write
        └─ FAIL → error_master + AIR
```

---

## Related Documents

- [PRD-DOL-EIN-FUZZY-FILING-DISCOVERY.md](../prd/PRD-DOL-EIN-FUZZY-FILING-DISCOVERY.md)
- [DOL_EIN_RESOLUTION.md](../../../doctrine/ple/DOL_EIN_RESOLUTION.md)
- [COMPANY_TARGET_IDENTITY.md](../../../doctrine/ple/COMPANY_TARGET_IDENTITY.md)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-01-02 | Barton Outreach Team | Initial decision |

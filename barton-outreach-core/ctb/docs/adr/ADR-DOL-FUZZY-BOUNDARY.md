# ADR: DOL Subhub Architecture Decisions
## Architecture Decision Record

**ADR ID**: `ADR-DOL-2025-001`
**Date**: 2025-01-02
**Version**: 2.0.0
**Status**: Accepted
**Deciders**: Barton Outreach Team

---

# Part 1: Fuzzy Matching Boundary

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

# Part 2: Violation Discovery Architecture

## Context

DOL agencies (OSHA, EBSA, WHD, OFCCP) publish employer violation data. Companies with violations are prime targets for outreach about compliance remediation services. Options considered:

1. **Option A**: Add violation data to Company Target (enrich identity)
2. **Option B**: Add violation data to DOL Subhub (fact storage)
3. **Option C**: Create separate Violation Subhub (new spoke)

---

## Decision

**We chose Option B**: Add violation discovery to DOL Subhub as fact storage.

---

## Rationale

### Why NOT Option A (Company Target enrichment)
- Company Target is locked to identity resolution
- Violations are not identity attributes
- Would bloat Company Target scope

### Why NOT Option C (Separate spoke)
- Violations are DOL-sourced data
- Shares EIN as the key relationship
- Would fragment DOL-related logic unnecessarily

### Why Option B (DOL Subhub fact storage)
- Violations link TO existing EIN linkages
- DOL Subhub already handles DOL sources
- Maintains "facts only" principle
- Downstream systems read facts for outreach
- Natural scope extension, not new spoke

---

## Consequences

### Positive
- DOL Subhub is single source for all DOL facts
- Violations link via EIN (immutable)
- Downstream outreach has clean interface
- Append-only storage ensures audit trail

### Negative
- DOL Subhub has two responsibilities (EIN + Violations)
- Must maintain boundary: no scoring in DOL
- Must maintain boundary: no outreach triggers in DOL

### Neutral
- Violations table is append-only like ein_linkage
- Same error routing pattern (AIR + error_master)

---

## Violation Architecture

### Data Flow
```
DOL Sources (OSHA, EBSA, WHD, OFCCP)
        ↓
DOL Subhub
  ├─ findViolations.js → Discover + normalize
  ├─ matchViolationToEIN() → Link to ein_linkage
  │
  └─ Result
        ├─ MATCHED → dol.violations (append-only)
        │     ↓
        │   dol.v_companies_with_violations
        │     ↓
        │   Downstream Outreach (reads facts)
        │
        └─ UNMATCHED → Log for enrichment
```

### Source Agencies (LOCKED)
| Agency | Data Source |
|--------|-------------|
| OSHA | enforcedata.dol.gov |
| EBSA | dol.gov/agencies/ebsa |
| WHD | dol.gov/agencies/whd |
| OFCCP | dol.gov/agencies/ofccp |

### Views for Outreach
| View | Purpose |
|------|---------|
| `dol.v_companies_with_violations` | Open/contested violations with company |
| `dol.v_violation_summary` | Aggregate stats by company |
| `dol.v_recent_violations` | Last 90 days for prioritization |

---

## Boundary Enforcement

### DOL Subhub DOES
- ✅ Discover violations from DOL sources
- ✅ Match violations to existing EIN
- ✅ Store violations as facts
- ✅ Provide views for downstream

### DOL Subhub DOES NOT
- ❌ Score violations
- ❌ Trigger outreach
- ❌ Create EIN linkages from violations
- ❌ Modify violation records

### Downstream Systems MAY
- ✅ Read violation views
- ✅ Score based on violation facts
- ✅ Trigger outreach based on facts
- ❌ Write to DOL tables

---

## Related Documents

- [PRD-DOL-EIN-FUZZY-FILING-DISCOVERY.md](../prd/PRD-DOL-EIN-FUZZY-FILING-DISCOVERY.md)
- [DOL_EIN_RESOLUTION.md](../../../doctrine/ple/DOL_EIN_RESOLUTION.md)
- [COMPANY_TARGET_IDENTITY.md](../../../doctrine/ple/COMPANY_TARGET_IDENTITY.md)
- [dol_violations-schema.sql](../../../doctrine/schemas/dol_violations-schema.sql)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 2.0.0 | 2025-01-02 | Barton Outreach Team | Added violation discovery architecture |
| 1.0.0 | 2025-01-02 | Barton Outreach Team | Initial fuzzy boundary decision |

# Company Target — Identity Resolution Doctrine
## Barton Doctrine Framework | SVG-PLE Marketing Core

**Document ID**: `01.04.02.04.21000.001`
**Version**: 1.0.0
**Last Updated**: 2025-01-01
**Status**: Active | Production Ready

---

## Overview

This doctrine defines **Company Target Identity Resolution**, the process responsible for resolving company identities including EIN fuzzy matching. 

**CRITICAL**: Fuzzy matching to attach EIN ↔ company_unique_id is allowed **ONLY** in Company Target / Identity Resolution. The DOL Subhub requires a locked EIN and must **NEVER** see fuzzy logic.

---

## Section 1: Canonical Rule (LOCKED)

### The Boundary Rule

| Zone | Fuzzy Logic | EIN State |
|------|-------------|-----------|
| **Company Target** | ✅ ALLOWED | May be unresolved |
| **DOL Subhub** | ❌ PROHIBITED | MUST be locked |
| **Analytics Views** | ❌ PROHIBITED | Read-only facts |

### Execution Flow

```
Company Target (Identity Resolution)
    ↓
    [Fuzzy Match Allowed Here]
    ↓
    EIN Resolved? ──YES──→ company_target_status = PASS → DOL Subhub
                  │
                  NO
                  ↓
    EIN_NOT_RESOLVED → shq.error_master → ENRICHMENT Queue
```

---

## Section 2: EIN_NOT_RESOLVED Failure State

### When This Occurs

`EIN_NOT_RESOLVED` failure occurs when:

1. Fuzzy match returns **zero candidates** above threshold, OR
2. Candidates exist but **none meet confidence requirements**

### Failure Routing

On `EIN_NOT_RESOLVED`:

| Action | Target | Status |
|--------|--------|--------|
| Write AIR event | `air_log` | Authoritative |
| Write error | `shq.error_master` | Operational |
| Set status | `company_target_status` | `FAIL` |
| Route for | Enrichment | `ENRICHMENT` |

**No retries inside Company Target.**

---

## Section 3: Error Write Contract (MANDATORY)

### Required Fields

When writing to `shq.error_master` on `EIN_NOT_RESOLVED`:

```
process_id            = '01.04.02.04.21000'  (Company Target)
error_code            = 'EIN_NOT_RESOLVED'
severity              = 'HARD_FAIL'
agent_name            = 'COMPANY_TARGET'
handoff_target        = 'DOL_EIN'
remediation_required  = 'ENRICHMENT'
company_unique_id     = <from input>
outreach_context_id   = <from input>
created_at            = <timestamp>
```

### Payload (REQUIRED)

The payload must include enrichment context:

```json
{
  "company_name": "Acme Corporation",
  "company_domain": "acme.com",
  "linkedin_company_url": "linkedin.com/company/acme",
  "state": "CA",
  "fuzzy_candidates": [
    { "ein": "12-3456789", "company_name": "Acme Corp", "score": 0.72 },
    { "ein": "98-7654321", "company_name": "ACME Inc", "score": 0.68 }
  ],
  "fuzzy_method": "token_set",
  "threshold_used": 0.85
}
```

This payload is for **enrichment tools only**.

---

## Section 4: DOL Execution Guard (CRITICAL)

### Hard Gate Requirements

DOL Subhub execution requires:

```sql
ein IS NOT NULL
AND company_target_status = 'PASS'
```

### Violation Handling

If violated:

1. **Emit AIR** event
2. **Write to `shq.error_master`**
3. **Abort execution**

**No fallback logic.**

---

## Section 5: Boundary Enforcement

### Explicit Prohibitions

| Location | Fuzzy Logic Status |
|----------|-------------------|
| `ctb/sys/dol-ein/*` | ❌ PROHIBITED |
| `analytics.v_5500_*` | ❌ PROHIBITED |
| `ctb/sys/company-target/*` | ✅ ALLOWED |

### Verification Rule

If fuzzy utilities are imported anywhere other than Company Target, **remove them**.

---

## Section 6: Fuzzy Match Configuration

### Default Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `confidence_threshold` | 0.85 | Minimum score to accept |
| `ambiguity_delta` | 0.05 | Score difference for ambiguity |
| `max_candidates` | 10 | Maximum candidates in payload |

### Match Methods (Supported)

| Method | Code | Use Case |
|--------|------|----------|
| Token Set | `token_set` | Default, handles word order |
| Levenshtein | `levenshtein` | Character-level distance |
| Jaro-Winkler | `jaro_winkler` | Prefix-weighted similarity |
| Exact | `exact` | No fuzzy, exact match only |

---

## Section 7: Enrichment Queue

### Queue Location

```
shq.v_pending_enrichment_queue
```

### Consumer Contract

Enrichment tools consuming this queue:

1. **MUST** attempt to resolve EIN
2. **MUST** update company record with resolved EIN
3. **MUST** mark error as resolved in `shq.error_master`
4. **MUST NOT** proceed to DOL until EIN is locked

---

## Section 8: Explicit Non-Goals

Company Target Identity Resolution does **NOT**:

| Prohibited Action | Reason |
|-------------------|--------|
| ❌ Execute DOL scraping | DOL is downstream |
| ❌ Assign BIT scores | Out of scope |
| ❌ Trigger outreach | Out of scope |
| ❌ Retry failed matches | Route to enrichment |
| ❌ Infer EIN from partial data | Ambiguity = FAIL |

---

## Section 9: Doctrine Statement

> "Failure to resolve EIN via fuzzy matching results in `EIN_NOT_RESOLVED` and automatic routing to `shq.error_master` for enrichment remediation. DOL Subhub execution is **prohibited** until EIN is resolved."

---

## Appendix A: File References

| File | Purpose |
|------|---------|
| `ctb/sys/company-target/identity_validator.js` | Identity resolution logic |
| `ctb/sys/dol-ein/ein_validator.js` | DOL execution gate |
| `ctb/data/infra/migrations/012_company_target_ein_error_routing.sql` | Error indexes and views |
| `doctrine/ple/DOL_EIN_RESOLUTION.md` | DOL doctrine (downstream) |

---

## Appendix B: Process IDs

| Process | Barton ID |
|---------|-----------|
| Company Target | `01.04.02.04.21000` |
| DOL Subhub | `01.04.02.04.22000` |

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2025-01-01 | Initial doctrine |

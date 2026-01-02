# Fan-Out Audit Report — Doctrine Propagation

**Audit Date**: 2026-01-01
**Reference Hub**: `hubs/company-target` (CERTIFIED)
**Auditor**: Doctrine Propagation Auditor (Claude Code)

---

## Executive Summary

| Hub | Parity With Company Target | Recommendation |
|-----|---------------------------|----------------|
| people-intelligence | **NO** | BLOCK FAN-OUT |
| dol-filings | PARTIAL | CLONE WITH FIXES |
| blog-content | PARTIAL | CLONE WITH FIXES |

---

## Hub: people-intelligence

**Parity With Company Target**: NO

### Violations

| Violation | Severity | File + Line Reference |
|-----------|----------|----------------------|
| `run()` method missing `outreach_context_id` param | CRITICAL | `imo/middle/phases/phase7_enrichment_queue.py:204` |
| No `context_manager.py` truth source | CRITICAL | Missing file |
| MillionVerifier calls without context logging | CRITICAL | `imo/middle/sub_wheels/email_verification/bulk_verifier_spoke.py:109-171` |
| No `can_attempt_tier2()` guard for Clay | CRITICAL | `imo/middle/phases/phase7_enrichment_queue.py` (waterfall integration) |
| Phase 5-8 phases missing context params | HIGH | `imo/middle/phases/phase5_email_generation.py`, etc. |
| No `log_tool_attempt()` calls | HIGH | All paid tool files |
| CHECKLIST references DG-013/014 but code doesn't enforce | HIGH | `CHECKLIST.md:182` vs actual code |

### Missing Artifacts

| Artifact | Status |
|----------|--------|
| DOCTRINE.md | MISSING |
| CHECKLIST.md | EXISTS (but unchecked boxes not enforced) |
| CERTIFICATION.md | MISSING |
| Context truth source (`context_manager.py`) | MISSING |

### Paid Tool Analysis

| Tool | File | Context Logged | Cost Logged | Guard Present |
|------|------|----------------|-------------|---------------|
| MillionVerifier | `bulk_verifier_spoke.py` | NO | NO | NO |
| Clay (Tier-2) | Referenced in waterfall | NO | NO | NO |

### Recommendation

**BLOCK FAN-OUT**

Cannot proceed until:
1. Create `context_manager.py` truth source (clone from company-target)
2. Add `outreach_context_id` and `company_sov_id` params to all phase `run()` methods
3. Wire `can_attempt_tier2()` guard into waterfall processor
4. Add `log_tool_attempt()` to MillionVerifier spoke
5. Add CI guards equivalent to DG-013/014

---

## Hub: dol-filings

**Parity With Company Target**: PARTIAL

### Violations

| Violation | Severity | File + Line Reference |
|-----------|----------|----------------------|
| Uses `correlation_id` only, not `outreach_context_id` | MEDIUM | `imo/middle/dol_hub.py:112` |
| No cost context (no paid tools, so lower severity) | LOW | N/A |

### Missing Artifacts

| Artifact | Status |
|----------|--------|
| DOCTRINE.md | MISSING |
| CHECKLIST.md | EXISTS |
| CERTIFICATION.md | MISSING |
| Context truth source | NOT REQUIRED (no paid tools) |

### Identity Boundary Check

| Check | Result |
|-------|--------|
| company_unique_id read-only | PASS (reads only, no writes) |
| EIN matching is exact | PASS (fail closed on ambiguity) |
| No company minting | PASS |

### Positive Findings

- Uses `correlation_id` for tracing (good)
- Has hub gate validation (`validate_company_anchor`)
- EIN matching is deterministic (exact match only)
- No paid tools used (bulk CSV only)
- CHECKLIST is comprehensive and matches company-target structure

### Recommendation

**CLONE WITH FIXES**

Required fixes:
1. Create DOCTRINE.md (clone structure from company-target, adapt content)
2. Create CERTIFICATION.md (after CI guards pass)
3. Consider adding `outreach_context_id` param even for tracing consistency

---

## Hub: blog-content

**Parity With Company Target**: PARTIAL

### Violations

| Violation | Severity | File + Line Reference |
|-----------|----------|----------------------|
| No IMO middle logic present | LOW | `imo/middle/__init__.py` (empty) |
| Hub is scaffold only | MEDIUM | All files are stubs |

### Missing Artifacts

| Artifact | Status |
|----------|--------|
| DOCTRINE.md | MISSING |
| CHECKLIST.md | EXISTS (comprehensive) |
| CERTIFICATION.md | MISSING |
| Context truth source | NOT REQUIRED (no paid tools, signal-only) |

### Identity Boundary Check

| Check | Result |
|-------|--------|
| company_sov_id read-only | PASS (per CHECKLIST) |
| Cannot mint companies | PASS (per CHECKLIST) |
| Cannot revive dead companies | PASS (per CHECKLIST) |
| Signal-only (no enrichment) | PASS (per CHECKLIST) |

### Positive Findings

- CHECKLIST explicitly prohibits identity minting
- CHECKLIST explicitly prohibits paid tools
- CHECKLIST explicitly prohibits enrichment triggers
- Hub is last in execution order (correct)

### Recommendation

**CLONE WITH FIXES**

Required fixes:
1. Create DOCTRINE.md (clone structure from company-target, adapt content)
2. Create CERTIFICATION.md (after implementation and CI guards pass)
3. Implement actual hub logic per PRD

---

## Canonical Rules Compliance Matrix

| Rule | people-intelligence | dol-filings | blog-content |
|------|---------------------|-------------|--------------|
| CL owns sovereign identity | UNTESTED | PASS | PASS |
| company_unique_id read-only | PASS | PASS | PASS |
| Cost-first waterfall | FAIL | N/A | N/A |
| Premium tools context-bound | FAIL | N/A | N/A |
| Premium tools fuse-protected | FAIL | N/A | N/A |
| Premium tools single-shot | FAIL | N/A | N/A |
| outreach_context_id mandatory | FAIL | PARTIAL | UNTESTED |
| correlation_id for tracing only | FAIL | PASS | UNTESTED |
| Binary exits (PASS/FAIL) | PASS | PASS | PASS |
| Bridge-only joins | UNTESTED | PASS | UNTESTED |

---

## Priority Order for Remediation

1. **people-intelligence** (CRITICAL)
   - Has paid tools without cost discipline
   - Violates core doctrine rules
   - Must be fixed before any production use

2. **dol-filings** (MEDIUM)
   - No paid tools = lower risk
   - Add doctrine artifacts for consistency

3. **blog-content** (LOW)
   - Signal-only hub with no paid tools
   - Scaffold needs implementation
   - Add doctrine artifacts when implementing

---

## Next Steps

### Immediate (Before Next Audit)

1. Clone `context_manager.py` to `people-intelligence`
2. Wire context params into people-intelligence phases
3. Add Tier-2 guard to waterfall processor
4. Add `log_tool_attempt()` to MillionVerifier spoke

### Short-Term

1. Create DOCTRINE.md for all three hubs
2. Add DG-013/014 equivalent CI guards for people-intelligence
3. Run kill-switch tests for people-intelligence

### Certification Gate

No hub may ship unless:
- [ ] DOCTRINE.md exists
- [ ] CHECKLIST.md has all boxes checkable
- [ ] CERTIFICATION.md documents test results
- [ ] CI guards pass
- [ ] Kill-switch tests pass (for hubs with paid tools)

---

## Signatures

- **Doctrine Propagation Auditor**: Claude Code
- **Reference Implementation**: Company Target (CERTIFIED)
- **Audit Version**: 1.0

---

**This audit is VOID if Company Target CERTIFICATION.md is revoked.**

# Company Target Documentation Alignment Report

**Date**: 2026-01-07
**Version**: v3.0 (Spine-First Architecture)
**Author**: Claude Code
**Authoritative Source**: ADR-CT-IMO-001

---

## Executive Summary

This report documents the documentation alignment pass performed to synchronize all documentation with the Company Target IMO refactor (v3.0). All documentation now reflects:

- **Single-pass IMO gate** architecture
- **`outreach_id`** as the only identity (never `sovereign_id`, never `company_id`)
- **Terminal failure** semantics (no retries)
- **Phase 1/1b deprecation** (moved to Company Lifecycle)

---

## Files Updated

### Primary Documents

| File | Change | Status |
|------|--------|--------|
| `docs/prd/PRD_COMPANY_HUB.md` | Updated waterfall tiers to SNAP_ON_TOOLBOX.yaml tools, fixed guard rails, aligned error codes | Updated |
| `docs/adr/ADR-001_Hub_Spoke_Architecture.md` | Updated Golden Rule to `outreach_id`, added v3.0 notes | Updated |
| `docs/adr/ADR-CT-IMO-001.md` | Created - authoritative ADR for IMO gate | Created |
| `docs/CHECKLIST_PRD_COMPLIANCE.md` | Updated Hub Gate to use `outreach_id`, added ADR-CT-IMO-001 | Updated |

### Hub Documents

| File | Change | Status |
|------|--------|--------|
| `hubs/company-target/CHECKLIST.md` | Already v3.0 aligned (IMO compliance) | Verified |
| `hubs/company-target/pipeline.md` | Already v3.0 aligned (IMO flow) | Verified |
| `hubs/company-target/ADR.md` | Updated footer with authoritative ADR reference | Updated |
| `hubs/company-target/__init__.py` | Exports new IMO entrypoints | Updated |

### Doctrine Reference

| File | Change | Status |
|------|--------|--------|
| `docs/doctrine_ref/README.md` | Updated version to 1.1.0, added v3.0 note | Updated |
| `docs/doctrine_ref/ple/COMPANY_TARGET_IDENTITY.md` | Already marked DEPRECATED | Verified |

---

## Concepts Removed/Deprecated

| Concept | Previous Location | Status | Now Owned By |
|---------|-------------------|--------|--------------|
| Phase 1 (Company Matching) | `phase1_company_matching.py` | DELETED | Company Lifecycle (CL) |
| Phase 1b (Unmatched Hold) | `phase1b_unmatched_hold_export.py` | DELETED | Company Lifecycle (CL) |
| Fuzzy matching | `fuzzy.py`, `fuzzy_arbitration.py` | DELETED | Company Lifecycle (CL) |
| Retry/backoff logic | Various | REMOVED | N/A (terminal failure) |
| `company_id` / `sovereign_id` references | Various | REPLACED | `outreach_id` |
| CL table access | Various | PROHIBITED | Spine provides `outreach_id` |

---

## Terminology Alignment

| Old Term | New Term | Notes |
|----------|----------|-------|
| `company_id` | `outreach_id` | Program-scoped identity |
| `sovereign_id` | (hidden) | Spine abstracts CL identity |
| "Company Hub" | "Company Target (IMO gate)" | Execution-readiness, not identity |
| "matching" | (deprecated) | CL's responsibility |
| "retry" | (deprecated) | FAIL is terminal |
| "Phase 1-4" | "IMO (I→M→O)" | Single-pass execution |

---

## Error Code Alignment

| Old Codes | New Codes | IMO Stage |
|-----------|-----------|-----------|
| CH-P1-* | (deprecated) | N/A |
| CH-P1B-* | (deprecated) | N/A |
| CT-P2-* | CT-I-* | I (Input) |
| CT-P3-* | CT-M-* | M (Middle) |
| CT-P4-* | CT-M-* | M (Middle) |

### Current Error Codes (v3.0)

| Code | Stage | Description |
|------|-------|-------------|
| `CT-I-NOT-FOUND` | I | outreach_id not in spine |
| `CT-I-NO-DOMAIN` | I | No domain in spine record |
| `CT-I-ALREADY-PROCESSED` | I | Already PASS or FAIL |
| `CT-M-NO-MX` | M | No MX records |
| `CT-M-NO-PATTERN` | M | All patterns rejected |
| `CT-M-SMTP-FAIL` | M | SMTP connection failure |
| `CT-M-VERIFY-FAIL` | M | Tier-2 verification failed |

---

## Tool Registry Alignment

All tool references now use `SNAP_ON_TOOLBOX.yaml`:

| Tool | Tool ID | Tier | Company Target Stage |
|------|---------|------|---------------------|
| MXLookup | TOOL-004 | 0 (FREE) | M1 |
| SMTPCheck | TOOL-005 | 0 (FREE) | M3 |
| EmailVerifier | TOOL-019 | 2 (GATED) | M5 |

### Banned Providers Removed from Documentation

- Clearbit (now Breeze, pricing changed)
- Prospeo (redundant)
- Snov (redundant)
- Clay (margin on vendors)

---

## Remaining Known Gaps

| Gap | Priority | Notes |
|-----|----------|-------|
| `docs/prd/PRD_COMPANY_HUB_PIPELINE.md` | LOW | Marked DEPRECATED in checklist, consider deletion |
| Legacy audit docs | LOW | Historical references acceptable with DEPRECATED labels |
| Some older PRDs | MEDIUM | May reference `company_id` - update as touched |

---

## Validation Checklist

- [x] No document implies Company Target owns identity
- [x] No document implies retries or matching
- [x] All flows reference `outreach_id`
- [x] All error codes match `company_target_imo.py` ErrorCode enum
- [x] Tool references use SNAP_ON_TOOLBOX.yaml tool IDs
- [x] ADR-CT-IMO-001 is referenced as authoritative

---

## Cross-References

| Document | References ADR-CT-IMO-001 |
|----------|---------------------------|
| PRD_COMPANY_HUB.md | Yes (Out of Scope section) |
| ADR-001_Hub_Spoke_Architecture.md | Yes (Golden Rule section) |
| CHECKLIST_PRD_COMPLIANCE.md | Yes (ADR Inventory) |
| doctrine_ref/README.md | Yes (Company Target section) |
| hubs/company-target/ADR.md | Yes (header + footer) |
| hubs/company-target/CHECKLIST.md | Yes (header) |
| hubs/company-target/pipeline.md | Yes (header) |

---

## Summary

The documentation alignment pass is **COMPLETE**. All primary documentation now reflects the Company Target v3.0 IMO architecture:

- **Architecture**: Single-pass IMO gate (I→M→O)
- **Identity**: `outreach_id` only (spine hides `sovereign_id`)
- **Failure Mode**: Terminal (no retries, no rescue)
- **Scope**: Execution-readiness, not identity authority
- **Tools**: SNAP_ON_TOOLBOX.yaml registry

---

**Report Generated**: 2026-01-07
**Alignment Status**: COMPLETE
**Next Review**: As needed when docs are modified

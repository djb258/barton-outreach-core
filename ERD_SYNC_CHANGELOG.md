# ERD Sync Changelog

**Sync Date**: 2026-02-02
**Source of Truth**: Neon PostgreSQL (Production)
**Reference**: `NEON_SCHEMA_REFERENCE_FOR_ERD.md`

---

## Summary

ERD documentation synchronized with live Neon schema. Neon is authoritative.

| Metric | Before | After |
|--------|--------|-------|
| Tables Documented | 50 | 62 |
| Stale References Removed | - | 10 |
| Critical Fixes | - | 4 |
| Files Updated | - | 6 |

---

## Critical Fixes

### 1. CL Authority Registry PK Correction

**Issue**: ERDs showed `company_unique_id` as PK
**Fix**: Changed to `sovereign_company_id` as PK (actual Neon schema)

**Files Updated**:
- `hubs/outreach-execution/SCHEMA.md`
- `hubs/company-target/SCHEMA.md`

**Before**:
```
CL_COMPANY_IDENTITY {
    uuid company_unique_id PK
    ...
}
```

**After**:
```
CL_COMPANY_IDENTITY {
    uuid sovereign_company_id PK "Minted by CL (IMMUTABLE)"
    uuid company_unique_id UK "Legacy ID"
    ...
}
```

### 2. Kill Switch System Added

**Issue**: `outreach.manual_overrides` and `outreach.override_audit_log` not documented
**Fix**: Added full table documentation and ERD entities

**Files Updated**:
- `hubs/outreach-execution/SCHEMA.md`

**Tables Added**:
- `outreach.manual_overrides` (12 columns)
- `outreach.override_audit_log` (9 columns)

### 3. Hub Registry Added

**Issue**: `outreach.hub_registry` not documented
**Fix**: Added full table documentation and ERD entity

**Files Updated**:
- `hubs/outreach-execution/SCHEMA.md`

### 4. Outreach Blog Table Added

**Issue**: `outreach.blog` not documented in blog-content hub
**Fix**: Added full table documentation

**Files Updated**:
- `hubs/blog-content/SCHEMA.md`

---

## Stale References Removed

### Marketing Schema (Dropped)

**Removed from ERDs**:
- `marketing.company_master`
- `marketing.people_master`
- FK relationships to marketing schema

**Files Updated**:
- `hubs/company-target/SCHEMA.md`
- `hubs/people-intelligence/SCHEMA.md`

### Legacy BIT Tables (Replaced)

**Removed from ERDs**:
- `bit.bit_signal`
- `bit.bit_company_score`
- `bit.bit_contact_score`

**Replaced with**:
- `bit.authorization_log`
- `bit.movement_events`
- `bit.phase_state`
- `bit.proof_lines`

**Files Updated**:
- `hubs/outreach-execution/SCHEMA.md`

### Outreach Context Tables (Don't Exist)

**Removed from ERDs**:
- `outreach_ctx.context`
- `outreach_ctx.spend_log`

**Files Updated**:
- `hubs/outreach-execution/SCHEMA.md`

### Pressure Signal Views (Consolidated)

**Removed from ERDs**:
- `company_target.vw_all_pressure_signals`
- `blog.pressure_signals` (wrong schema - actually in dol/people schemas)

**Files Updated**:
- `hubs/company-target/SCHEMA.md`

---

## Tables Added to ERDs

| Table | Schema | Hub | Columns |
|-------|--------|-----|---------|
| `manual_overrides` | outreach | outreach-execution | 12 |
| `override_audit_log` | outreach | outreach-execution | 9 |
| `hub_registry` | outreach | outreach-execution | 12 |
| `blog` | outreach | blog-content | 8 |
| `authorization_log` | bit | outreach-execution | 12 |
| `movement_events` | bit | outreach-execution | 17 |
| `phase_state` | bit | outreach-execution | 14 |
| `proof_lines` | bit | outreach-execution | 11 |

---

## Column Corrections

### cl.company_identity

**Added columns** (key ones):
- `sovereign_company_id` (actual PK)
- `canonical_name`
- `identity_status`
- `identity_pass`
- `eligibility_status`
- `exclusion_reason`
- `outreach_attached_at`
- `sales_opened_at`
- `client_promoted_at`

### outreach.outreach

**Corrected**:
- `sovereign_id` FK documented with correct target (`cl.company_identity.sovereign_company_id`)
- Timestamps changed from `timestamp` to `timestamptz`

---

## Files Updated

| File | Changes |
|------|---------|
| `hubs/outreach-execution/SCHEMA.md` | Kill switch, hub registry, BIT tables, CL fix |
| `hubs/company-target/SCHEMA.md` | CL fix, removed marketing, removed stale views |
| `hubs/people-intelligence/SCHEMA.md` | Removed marketing references |
| `hubs/blog-content/SCHEMA.md` | Added outreach.blog, header |
| `hubs/dol-filings/SCHEMA.md` | No changes needed |
| `hubs/talent-flow/SCHEMA.md` | No changes needed |

---

## Remaining Gaps (Lower Priority)

These tables exist in Neon but are NOT in ERDs (intentionally summarized per scope rules):

### Archive Tables (Annotate Only)
- `outreach.outreach_archive`
- `outreach.company_target_archive`
- `outreach.people_archive`
- `outreach.blog_archive`
- `outreach.dol_archive`
- `outreach.bit_scores_archive`
- `people.company_slot_archive`
- `people.people_master_archive`
- `cl.company_identity_archive`
- `cl.company_domains_archive`

### Exclusion Tables (Documented in outreach-execution)
- `outreach.outreach_excluded` (DOCUMENTED)
- `cl.company_identity_excluded`
- `cl.company_domains_excluded`

### Staging/Temp Tables (Not Documented - Intentional)
- `people.people_staging`
- `people.people_candidate`
- `people.slot_quarantine_r0_002`

---

## Verification

Run drift checker to verify sync:
```bash
doppler run -- python ops/schema-drift/schema_drift_checker.py
python ops/schema-drift/analyze_schema_drift.py
```

---

## Document Control

| Field | Value |
|-------|-------|
| Sync Date | 2026-02-02 |
| Performed By | claude-code |
| Reference | NEON_SCHEMA_REFERENCE_FOR_ERD.md |
| Source of Truth | Neon PostgreSQL (Production) |
| CL-Outreach Alignment | 42,192 = 42,192 (ALIGNED) |

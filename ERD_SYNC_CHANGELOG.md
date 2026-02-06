# ERD Sync Changelog

**Sync Date**: 2026-02-10
**Source of Truth**: Neon PostgreSQL (Production)
**Reference**: `NEON_SCHEMA_REFERENCE_FOR_ERD.md`

---

## Summary

ERD documentation synchronized with live Neon schema. Neon is authoritative.

| Metric | Before | After |
|--------|--------|-------|
| Tables Documented | 62 | 82 |
| Stale References Removed | - | 10 |
| Critical Fixes | - | 5 |
| Files Updated | - | 9 |

---

## 2026-02-10 DOL Filing Tables Expansion (20 tables added)

### DOL Schedule Tables Added to ERDs

**Issue**: Only 3 DOL filing tables (form_5500, form_5500_sf, schedule_a) were documented. 21 additional schedule tables loaded from DOL FOIA data were missing from all ERDs.

**Fix**: Added all 26 DOL filing tables to ERD documentation with full relationship mapping.

**Tables Added (grouped by schedule)**:

| Table Group | Tables Added | Total in Group |
|------------|-------------|----------------|
| Form 5500 | form_5500_sf_part7 | 3 |
| Schedule A | schedule_a_part1 | 2 |
| Schedule C | schedule_c, schedule_c_part1_item1, schedule_c_part1_item2, schedule_c_part1_item3, schedule_c_part1_item4, schedule_c_part2, schedule_c_part1_item1_ele, schedule_c_part1_item2_ele, schedule_c_part1_item4_ele | 9 |
| Schedule D | schedule_d, schedule_d_part1, schedule_d_part2, schedule_dcg | 4 |
| Schedule G | schedule_g, schedule_g_part1, schedule_g_part2, schedule_g_part3 | 4 |
| Schedule H | schedule_h, schedule_h_part1 | 2 |
| Schedule I | schedule_i, schedule_i_part1 | 2 |
| **Total** | **20 new + 6 existing** | **26** |

**Files Updated**:
- `docs/diagrams/erd/DOL_SUBHUB.mmd` — Complete rewrite (8 → 32 entities)
- `docs/diagrams/erd/CORE_SCHEMA.mmd` — Added 7 DOL schedule entity groups
- `repo-data-diagrams/PLE_SCHEMA_ERD.md` — Added 7 DOL schedule entities
- `hubs/dol-filings/SCHEMA.md` — Added all 26 filing tables with documentation
- `hubs/dol-filings/PRD.md` — Major update v1.0 → v2.0
- `ERD_QUICK_REFERENCE.md` — Added DOL filing tables section
- `NEON_SCHEMA_REFERENCE_FOR_ERD.md` — Added Section 7 (DOL tables)
- `docs/ui/UI_PRD_DOL.md` — Added schedule views
- `PRD_ERD_ALIGNMENT_CHANGELOG.md` — Added 2026-02-10 entry

### DOL Data Coverage

| Year | Tables | Rows |
|------|--------|------|
| 2023 | 24 | ~6,012,077 |
| 2024 | 26 | 4,951,258 |
| 2025 | 26 | 7,291 |
| **Total** | **26 unique** | **10,970,626** |

### DOL Metadata Coverage

| Metadata Type | Count | Coverage |
|--------------|-------|---------|
| Table comments (COMMENT ON TABLE) | 26 | 100% |
| Column comments (COMMENT ON COLUMN) | 1,081 | 100% |
| form_year indexes | 23 | All tables with form_year |
| Composite (ack_id, form_year) indexes | 18 | All schedule tables |
| EIN indexes | 8 | Header tables with sponsor_dfe_ein |
| dol.column_metadata catalog entries | 1,081 | 100% |

---

## Critical Fixes (2026-02-02)

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
| Sync Date | 2026-02-10 |
| Performed By | claude-code |
| Reference | NEON_SCHEMA_REFERENCE_FOR_ERD.md |
| Source of Truth | Neon PostgreSQL (Production) |
| CL-Outreach Alignment | 42,192 = 42,192 (ALIGNED) |
| DOL Filing Tables | 26 (10,970,626 rows) |
| DOL Years | 2023, 2024, 2025 |
| DOL Column Metadata | 1,081 entries (100% coverage) |

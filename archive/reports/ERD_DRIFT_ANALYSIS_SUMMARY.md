# ERD Drift Analysis Summary

**Date**: 2026-02-02
**Status**: CRITICAL DRIFT DETECTED
**Alignment**: 40 of 103 tables documented (38.8%)

## Executive Summary

A comprehensive drift check between ERD documentation (SCHEMA.md files in hub directories) and the actual Neon PostgreSQL database reveals significant schema drift across all hubs.

### Key Findings

| Metric | Count | Severity |
|--------|-------|----------|
| **Total Neon Tables** | 103 | - |
| **Documented Tables** | 50 | - |
| **Matching Tables** | 40 | - |
| **Undocumented Tables** | 63 | HIGH |
| **Stale/Missing Tables** | 10 | MEDIUM |
| **Column Mismatches** | 40 | HIGH |

### Documentation Coverage by Schema

| Schema | Neon Tables | Documented | Coverage | Status |
|--------|-------------|------------|----------|--------|
| `outreach` | 40 | 15 | 37.5% | CRITICAL |
| `cl` | 15 | 2 | 13.3% | CRITICAL |
| `people` | 13 | 9 | 69.2% | NEEDS WORK |
| `dol` | 7 | 6 | 85.7% | GOOD |
| `company` | 12 | 7 | 58.3% | NEEDS WORK |
| `bit` | 4 | 3 | 75.0% | GOOD |

## Critical Issues

### 1. Undocumented Operational Tables (63 tables)

These tables exist in production but have NO documentation:

#### CL Schema (15 tables undocumented)
- **Archive tables**: `company_domains_archive`, `company_identity_archive`, `company_names_archive`, `domain_hierarchy_archive`, `identity_confidence_archive`
- **Exclusion tables**: `company_domains_excluded`, `company_identity_excluded`, `company_names_excluded`, `identity_confidence_excluded`
- **Bridging tables**: `company_identity_bridge`, `domain_hierarchy`
- **Error tracking**: `cl_err_existence`, `cl_errors_archive`
- **Candidate management**: `company_candidate`
- **Name resolution**: `company_names`, `company_names_archive`, `company_names_excluded`
- **Confidence scoring**: `identity_confidence`, `identity_confidence_archive`, `identity_confidence_excluded`

**IMPACT**: CL is the AUTHORITY REGISTRY. Missing documentation here is a v1.0 certification violation.

#### Outreach Schema (24 tables undocumented)
- **Archive tables**: `bit_scores_archive`, `blog_archive`, `company_target_archive`, `dol_archive`, `outreach_archive`, `people_archive`, `outreach_orphan_archive`
- **Error tracking**: `blog_errors`, `outreach_errors`
- **Control/Registry**: `hub_registry`, `column_registry`, `entity_resolution_queue`
- **Override system**: `manual_overrides`, `override_audit_log` (KILL SWITCH)
- **Blog hub**: `blog`, `blog_ingress_control`, `blog_source_history`
- **DOL enrichment**: `dol_url_enrichment`
- **BIT tracking**: `bit_input_history`
- **Quarantine**: `outreach_excluded`, `outreach_legacy_quarantine`
- **Operational**: `pipeline_audit_log`, `mv_credit_usage`

**IMPACT**: Missing documentation for KILL SWITCH system (`manual_overrides`, `override_audit_log`) is HIGH SEVERITY.

#### People Schema (13 tables undocumented)
- **Archive tables**: `company_slot_archive`, `people_master_archive`
- **Resolution queues**: `company_resolution_log`, `people_resolution_history`, `people_resolution_queue`
- **Enrichment**: `paid_enrichment_queue`
- **Staging/Validation**: `people_staging`, `people_invalid`
- **Audit**: `people_promotion_audit`
- **Scoring**: `person_scores`
- **Mapping**: `title_slot_mapping`
- **Quarantine**: `slot_orphan_snapshot_r0_002`, `slot_quarantine_r0_002`

**IMPACT**: Missing documentation for enrichment queue and slot quarantine tables.

### 2. Stale Documentation (10 tables documented but missing)

These tables are in ERD but DON'T exist in Neon:

| Table | Hub | Reason |
|-------|-----|--------|
| `bit.bit_company_score` | Company Target | Replaced by `outreach.bit_scores`? |
| `bit.bit_contact_score` | Company Target | Replaced by `outreach.bit_scores`? |
| `bit.bit_signal` | Company Target | Replaced by `outreach.bit_signals`? |
| `blog.pressure_signals` | Blog Content | Wrong schema - should be `dol.pressure_signals`? |
| `company.target_vw_all_pressure_signals` | Company Target | View missing |
| `marketing.company_master` | Company Target | Legacy schema dropped? |
| `marketing.people_master` | People Intelligence | Legacy schema dropped? |
| `outreach.ctx_context` | Outreach Execution | Context tracking deprecated? |
| `outreach.ctx_spend_log` | Outreach Execution | Spend tracking deprecated? |
| `talent.flow_movement_history` | Talent Flow | Wrong schema - exists as `people.person_movement_history`? |

**ACTION REQUIRED**: Remove these from ERD or document as deprecated.

### 3. Column Mismatches (40 tables)

**Most Critical:**

#### `cl.company_identity` (26 columns missing from ERD)
Missing critical fields:
- `sovereign_company_id` - PRIMARY KEY
- `outreach_id` - Outreach hub claim (WRITE-ONCE)
- `sales_process_id` - Sales hub claim (WRITE-ONCE)
- `client_id` - Client hub claim (WRITE-ONCE)
- `canonical_name` - Normalized company name
- `eligibility_status` - Marketing eligibility
- `lifecycle_run_id` - Processing batch ID
- `identity_pass` - Gate pass status
- `final_outcome` - Lifecycle outcome

**IMPACT**: ERD shows only 4 columns when table has 30+ columns. CRITICAL MISMATCH.

#### `dol.form_5500` and `dol.form_5500_sf` (hundreds of columns missing)
ERD shows minimal column sets (8-10 columns), but actual tables have 100+ columns including:
- All sponsor address fields
- Administrator details
- Preparer information
- Plan characteristics
- Filing metadata
- Signature validation

**IMPACT**: DOL tables are severely under-documented.

#### Error Tables Pattern
All error tables have column mismatches:
- `outreach.company_target_errors`
- `outreach.dol_errors`
- `outreach.people_errors`
- `outreach.bit_errors`

Missing standard error fields:
- `error_id` (PK)
- `failure_code`
- `severity`
- `blocking_reason`
- `retry_allowed`
- `stack_trace`

**IMPACT**: Error tracking schema not documented consistently.

## Timestamp Drift Pattern

**Common Issue**: ERD uses `timestamp` but Neon uses `timestamp with time zone` (timestamptz)

Affected tables:
- `cl.company_domains.checked_at`
- `cl.company_identity.created_at`
- `outreach.outreach.created_at`
- `outreach.people.email_verified_at`
- `outreach.people.last_event_ts`
- `outreach.bit_scores.last_signal_at`
- `outreach.bit_scores.last_scored_at`
- `people.company_slot.filled_at`

**ACTION**: Update all ERD timestamp fields to `timestamptz` for accuracy.

## Missing Critical Tables (Not in Either)

Based on CLAUDE.md and doctrine, these tables should exist but were not found:

1. **Spoke Tables** - No spoke-specific tables found in Neon
2. **CL Lifecycle Views**:
   - `cl.v_company_lifecycle_status` (documented in CLAUDE.md)
3. **Outreach Views**:
   - `outreach.vw_marketing_eligibility_with_overrides` (v1.0 FROZEN)
   - `outreach.vw_sovereign_completion` (v1.0 FROZEN)

**ACTION**: Verify if these are views (not tables) or if documentation is outdated.

## Recommendations

### Immediate Actions (Next 48 Hours)

1. **Document Kill Switch System**
   - Add `outreach.manual_overrides` to outreach-execution/SCHEMA.md
   - Add `outreach.override_audit_log` to outreach-execution/SCHEMA.md
   - Document override workflow and safety gates

2. **Document CL Authority Registry**
   - Update company-target/SCHEMA.md with complete `cl.company_identity` schema
   - Add all 26+ missing columns
   - Document WRITE-ONCE semantics for hub claims

3. **Document Archive Pattern**
   - Create dedicated section in each SCHEMA.md for archive tables
   - Document archive triggers and retention policies

4. **Fix Stale References**
   - Remove 10 tables documented but not in Neon
   - Mark as deprecated with reason codes

### Short-Term Actions (Next 2 Weeks)

5. **Document Error Tables**
   - Create standard error table template
   - Apply to all *_errors tables
   - Document error codes and severity levels

6. **Complete DOL Documentation**
   - Add all Form 5500 columns to dol-filings/SCHEMA.md
   - Add all Form 5500-SF columns
   - Document EIN resolution workflow

7. **Document People Hub Gaps**
   - Add enrichment queue tables
   - Document slot quarantine tables
   - Add title mapping table

8. **Fix Timestamp Types**
   - Update all `timestamp` to `timestamptz` in ERD
   - Document timezone handling strategy

### Long-Term Actions (Next Month)

9. **Create Schema Governance Process**
   - Require ERD updates in all PRs that modify schema
   - Add drift checker to CI/CD pipeline
   - Weekly automated drift reports

10. **Implement Schema Versioning**
    - Add schema version tags to tables
    - Track schema changes in ADRs
    - Link migrations to ERD updates

11. **Document Views**
    - Add views to SCHEMA.md files
    - Document materialized views separately
    - Include refresh schedules

12. **Create Cross-Hub Reference Guide**
    - Map spoke contracts to actual tables
    - Document FK relationships visually
    - Show data flow through waterfall

## Compliance Check Against v1.0 Baseline

**Status**: PARTIAL COMPLIANCE

| Requirement | Status | Evidence |
|-------------|--------|----------|
| CL authority registry documented | FAIL | Missing 26 columns in ERD |
| Operational spine documented | PARTIAL | `outreach.outreach` documented but incomplete |
| Kill switch documented | FAIL | `manual_overrides` and `override_audit_log` missing |
| Archive tables documented | FAIL | 7 archive tables undocumented |
| Error tracking documented | FAIL | All error tables have column mismatches |
| Hub registry documented | FAIL | `outreach.hub_registry` undocumented |

**RECOMMENDATION**: Before declaring v1.1 or any future baseline, ERD documentation MUST align with Neon schema.

## Automated Drift Detection

The drift checker script has been created at:
- `schema_drift_checker.py` - Extracts Neon schema snapshot
- `analyze_schema_drift.py` - Compares ERD vs Neon
- `neon_schema_snapshot.json` - Cached snapshot (can be versioned)
- `ERD_NEON_DRIFT_REPORT.md` - Full detailed report

**Recommendation**: Add to weekly ops checklist:
```bash
# Weekly schema drift check
doppler run -- python schema_drift_checker.py
python analyze_schema_drift.py
git diff ERD_NEON_DRIFT_REPORT.md  # Review changes
```

## Next Steps

1. Review this summary with architecture team
2. Prioritize documentation updates by severity
3. Create tasks for each recommendation
4. Update DO_NOT_MODIFY_REGISTRY.md if ERD changes affect frozen components
5. Schedule ERD alignment sprint

---

**Report Generated**: 2026-02-02 05:27 AM
**Database**: Neon PostgreSQL (Production)
**Connection**: ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech
**Schemas Analyzed**: outreach, cl, people, dol, company, bit
**Total Drift Score**: 63 (HIGH)

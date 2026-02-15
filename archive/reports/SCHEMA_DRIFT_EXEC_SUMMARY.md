# Schema Drift Detection - Executive Summary

**Date**: 2026-02-02
**Reporter**: Database Specialist
**Status**: CRITICAL DRIFT DETECTED
**Action Required**: YES - Immediate

---

## What Was Done

A comprehensive schema drift analysis comparing ERD documentation (SCHEMA.md files in hub directories) against the actual Neon PostgreSQL production database.

### Tools Created

1. **Schema Drift Checker** (`ops/schema-drift/schema_drift_checker.py`)
   - Connects to Neon PostgreSQL
   - Extracts complete schema snapshot (tables, views, columns, FK relationships)
   - Saves to `neon_schema_snapshot.json`

2. **Schema Drift Analyzer** (`ops/schema-drift/analyze_schema_drift.py`)
   - Parses Mermaid ERD diagrams from all SCHEMA.md files
   - Compares ERD against Neon snapshot
   - Generates detailed drift report

3. **Documentation**
   - `ERD_NEON_DRIFT_REPORT.md` - Full detailed drift report (1,100+ lines)
   - `ERD_DRIFT_ANALYSIS_SUMMARY.md` - Analysis with recommendations
   - `ERD_DRIFT_ACTION_CHECKLIST.md` - Prioritized action items
   - `ops/schema-drift/README.md` - Tool usage guide

---

## Key Findings

### Drift Metrics

| Metric | Value | Status |
|--------|-------|--------|
| **Total Neon Tables** | 103 | - |
| **Documented in ERD** | 50 | LOW |
| **Matching Tables** | 40 | - |
| **Undocumented Tables** | 63 | CRITICAL |
| **Stale/Missing Tables** | 10 | MEDIUM |
| **Column Mismatches** | 40 | HIGH |
| **Documentation Coverage** | 38.8% | CRITICAL |

### Critical Issues Found

1. **CL Authority Registry Incomplete** (CRITICAL)
   - `cl.company_identity` shows 4 columns in ERD but has 30+ in Neon
   - Missing critical fields: `sovereign_company_id`, `outreach_id`, `sales_process_id`, `client_id`
   - **Impact**: v1.0 certification violation - CL is authority registry

2. **Kill Switch System Undocumented** (HIGH)
   - `outreach.manual_overrides` - not documented
   - `outreach.override_audit_log` - not documented
   - **Impact**: Critical safety mechanism has no ERD documentation

3. **63 Tables Completely Undocumented** (HIGH)
   - All archive tables (7 tables)
   - All exclusion tables (5 tables)
   - All error tracking tables (8 tables)
   - Hub registry and control tables
   - Quarantine and staging tables

4. **DOL Tables Severely Under-Documented** (HIGH)
   - Form 5500: Shows 8 columns, actual has 100+
   - Form 5500-SF: Shows 10 columns, actual has 200+
   - **Impact**: Cannot understand DOL data model from ERD

5. **10 Tables in ERD Don't Exist in Neon** (MEDIUM)
   - Includes references to dropped `marketing` schema
   - Old BIT table references
   - Context tracking tables that may be deprecated

---

## Documentation Coverage by Schema

| Schema | Tables in Neon | Documented | Coverage | Grade |
|--------|----------------|------------|----------|-------|
| `outreach` | 40 | 15 | 37.5% | **F** |
| `cl` | 15 | 2 | 13.3% | **F** |
| `people` | 13 | 9 | 69.2% | **D** |
| `dol` | 7 | 6 | 85.7% | **B** |
| `company` | 12 | 7 | 58.3% | **D** |
| `bit` | 4 | 3 | 75.0% | **C** |
| **TOTAL** | **103** | **50** | **38.8%** | **F** |

---

## What This Means

### For v1.0 Certification

**Status**: PARTIAL COMPLIANCE

The v1.0 operational baseline (certified 2026-01-19, frozen 2026-01-20) requires:
- CL authority registry fully documented ❌ FAIL
- Kill switch system documented ❌ FAIL
- Operational spine documented ⚠️ PARTIAL
- Archive pattern documented ❌ FAIL

**Recommendation**: v1.0 certification is DATA VERIFIED but DOCUMENTATION INCOMPLETE.

### For Future Development

Without accurate ERD documentation:
- New developers cannot understand schema
- Schema changes risk breaking undocumented dependencies
- No reference for what tables are operational vs deprecated
- Cannot validate spoke contracts against actual tables
- Migration planning is risky without complete schema map

### For Compliance

Missing documentation for:
- Override/kill switch system (governance requirement)
- Error tracking tables (audit requirement)
- Archive tables (retention policy requirement)
- Exclusion tables (marketing safety requirement)

---

## Immediate Actions Required

### Priority 1: Fix v1.0 Violations (48 Hours)

1. **Update `cl.company_identity` ERD**
   - Add all 26+ missing columns
   - Document WRITE-ONCE semantics
   - File: `hubs/company-target/SCHEMA.md`

2. **Document Kill Switch System**
   - Add `outreach.manual_overrides` table
   - Add `outreach.override_audit_log` table
   - Document override workflow
   - File: `hubs/outreach-execution/SCHEMA.md`

3. **Document Hub Registry**
   - Add `outreach.hub_registry` table
   - Document waterfall execution order
   - File: `hubs/outreach-execution/SCHEMA.md`

### Priority 2: Clean Stale References (1 Week)

Remove or mark as deprecated 10 tables that are documented but don't exist:
- `bit.bit_company_score`, `bit.bit_contact_score`, `bit.bit_signal`
- `marketing.company_master`, `marketing.people_master`
- `blog.pressure_signals`
- `outreach.ctx_context`, `outreach.ctx_spend_log`
- `company.target_vw_all_pressure_signals`
- `talent.flow_movement_history`

### Priority 3: Document Critical Gaps (2 Weeks)

1. Complete DOL tables (add 100+ missing columns to Form 5500)
2. Add all archive tables (7 tables)
3. Add all error tracking tables (8 tables)
4. Add all exclusion tables (5 tables)
5. Fix timestamp types (`timestamp` → `timestamptz` everywhere)

---

## Long-Term Recommendations

### Schema Governance (1 Month)

1. **PR Requirements**
   - All schema changes must update ERD
   - Drift report must show zero drift
   - Link migrations to ERD updates

2. **Automated Checks**
   - Add drift checker to CI/CD pipeline
   - Weekly automated drift reports
   - Alert if drift exceeds threshold

3. **Snapshot Versioning**
   - Version control schema snapshots
   - Compare snapshots across releases
   - Track schema evolution over time

### Documentation Standards (1 Month)

1. **ERD Templates**
   - Standard format for error tables
   - Standard format for archive tables
   - Standard format for audit tables

2. **Maintenance Schedule**
   - Weekly drift checks
   - Monthly schema reviews
   - Quarterly documentation audits

3. **Cross-Reference Guides**
   - Map spoke contracts to actual tables
   - Document FK relationships visually
   - Show data flow through waterfall

---

## Files Generated

All files are in the repository root:

1. **Reports**
   - `ERD_NEON_DRIFT_REPORT.md` - Full detailed report
   - `ERD_DRIFT_ANALYSIS_SUMMARY.md` - Analysis and recommendations
   - `SCHEMA_DRIFT_EXEC_SUMMARY.md` - This file

2. **Action Items**
   - `ERD_DRIFT_ACTION_CHECKLIST.md` - Prioritized checklist (17 priorities)

3. **Tools**
   - `ops/schema-drift/schema_drift_checker.py` - Neon schema extractor
   - `ops/schema-drift/analyze_schema_drift.py` - Drift analyzer
   - `ops/schema-drift/README.md` - Tool documentation

4. **Snapshot**
   - `neon_schema_snapshot.json` - Complete Neon schema (cached)

---

## Next Steps

1. **Review** - Architecture team reviews this summary
2. **Prioritize** - Confirm priority order for action items
3. **Assign** - Assign owners to each priority
4. **Execute** - Begin P1 tasks (48-hour deadline)
5. **Track** - Weekly standup to review progress
6. **Verify** - Re-run drift checker after updates
7. **Close Loop** - Update DO_NOT_MODIFY_REGISTRY.md if needed

---

## Questions?

**Tool Location**: `ops/schema-drift/`
**Usage**: See `ops/schema-drift/README.md`
**Action Checklist**: See `ERD_DRIFT_ACTION_CHECKLIST.md`
**Detailed Report**: See `ERD_NEON_DRIFT_REPORT.md`

**Contact**: Database Engineering Team
**Escalation**: Architecture Team (if drift >10 tables or >50 columns)

---

**Report Generated**: 2026-02-02 05:27 AM
**Database**: Neon PostgreSQL (Production)
**Schemas Analyzed**: outreach, cl, people, dol, company, bit
**Total Tables Analyzed**: 103
**Documentation Coverage**: 38.8%
**Status**: CRITICAL - ACTION REQUIRED

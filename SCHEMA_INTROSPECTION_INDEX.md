# Schema Introspection Index

**Date**: 2026-02-02
**Purpose**: Central index for Neon schema introspection documentation
**Status**: COMPLETE

---

## DELIVERABLES (5 FILES)

### 1. NEON_SCHEMA_REFERENCE_FOR_ERD.md
**Purpose**: Complete schema reference for ERD updates
**Size**: ~13 KB
**Contents**:
- 12 critical tables with full column definitions
- Data types, nullability, defaults
- Table relationships and foreign keys
- CL parent-child doctrine patterns
- Kill switch system (manual_overrides, override_audit_log)
- BIT analytics layer (authorization_log, movement_events, phase_state, proof_lines)

**Use Case**: Primary reference when updating ERD diagrams

---

### 2. ERD_SCHEMA_AUDIT_FINDINGS.md
**Purpose**: Specific corrections needed for ERD updates
**Size**: ~11 KB
**Contents**:
- Structural corrections (PK/FK changes)
- Missing tables to add
- Column name mismatches
- ENUM types to document
- Prioritized update checklist

**Use Case**: Step-by-step ERD correction guide

**Key Findings**:
- `cl.company_identity` PK is `sovereign_company_id` (not `company_unique_id`)
- `outreach.outreach` FK column is `sovereign_id` (not `sovereign_company_id`)
- Kill switch tables exist and need to be added if missing
- ENUM types need legends in ERD

---

### 3. NEON_ENUM_TYPES_REFERENCE.md
**Purpose**: Complete catalog of PostgreSQL ENUM types
**Size**: ~11 KB
**Contents**:
- 13 ENUM types across 4 schemas
- 69 total ENUM values
- Usage matrix (which tables use which ENUMs)
- Color coding recommendations for ERD
- Migration notes for deprecated ENUMs

**Use Case**: ERD legend creation and color scheme design

**Key ENUMs**:
- `bit.authorization_band` (6 tiers: SILENT → DIRECT)
- `outreach.override_type_enum` (6 types: marketing_disabled, tier_cap, etc.)
- `outreach.lifecycle_state` (8 states: SUSPECT → CLIENT)
- `outreach.hub_status_enum` (4 states: PASS, IN_PROGRESS, FAIL, BLOCKED)

---

### 4. SCHEMA_INTROSPECTION_SUMMARY.md
**Purpose**: Executive summary and action plan
**Size**: ~15 KB
**Contents**:
- Deliverable overview
- Key schema corrections
- Alignment verification (51,148 = 51,148 ✓)
- Next actions with priorities
- Schema health metrics
- Verification queries

**Use Case**: High-level overview and project management

---

### 5. ERD_QUICK_REFERENCE.md
**Purpose**: Fast lookup card for ERD updates
**Size**: ~9 KB
**Contents**:
- Critical PK/FK changes (one-liners)
- Table schemas (condensed)
- Key ENUM values with color codes
- Relationship diagrams (ASCII)
- v1.0 alignment rule
- Doctrine reminders

**Use Case**: Quick lookup while editing ERD diagrams

---

## RAW DATA

### schema_introspection_results.json
**Purpose**: Programmatic access to schema data
**Size**: ~29 KB
**Format**: JSON
**Contents**:
- All 12 tables with full column metadata
- Nested arrays of column definitions
- Can be parsed by automated tools

**Use Case**: Automated ERD generation or schema validation tools

---

## QUICK ACCESS

### I need to update an ERD diagram
1. Start with `ERD_QUICK_REFERENCE.md` (fast lookup)
2. Reference `NEON_SCHEMA_REFERENCE_FOR_ERD.md` (full details)
3. Use `ERD_SCHEMA_AUDIT_FINDINGS.md` (correction checklist)

### I need to add ENUM legends
1. Use `NEON_ENUM_TYPES_REFERENCE.md`
2. Apply color coding recommendations
3. Add to ERD legend section

### I need to verify schema alignment
1. Use `SCHEMA_INTROSPECTION_SUMMARY.md` (alignment verification section)
2. Run verification queries
3. Check v1.0 alignment rule (51,148 = 51,148)

### I need to build automated tools
1. Parse `schema_introspection_results.json`
2. Reference `NEON_ENUM_TYPES_REFERENCE.md` for ENUM values
3. Use `ERD_SCHEMA_AUDIT_FINDINGS.md` for known issues

---

## KEY CORRECTIONS SUMMARY

### 1. Primary Key Change
**Table**: cl.company_identity
**Old**: company_unique_id (PK)
**New**: sovereign_company_id (PK)
**Status**: company_unique_id is LEGACY

### 2. Foreign Key Column Name
**Table**: outreach.outreach
**Column**: sovereign_id (NOT sovereign_company_id)
**FK Target**: cl.company_identity.sovereign_company_id
**Status**: Column name mismatch

### 3. New Tables to Add
- outreach.manual_overrides (kill switch)
- outreach.override_audit_log (kill switch audit)
- cl.company_domains (multi-domain support)

### 4. ENUM Documentation
- Add legends for 13 ENUM types
- Use color coding for visual clarity
- Document migration paths for deprecated ENUMs

---

## TABLES DOCUMENTED (12)

| Schema | Table | Columns | Purpose |
|--------|-------|---------|---------|
| cl | company_identity | 33 | CL authority registry (PARENT) |
| cl | company_domains | 7 | Multi-domain support (1:N) |
| outreach | manual_overrides | 12 | Kill switch controls |
| outreach | override_audit_log | 9 | Kill switch audit trail |
| outreach | hub_registry | 12 | Waterfall execution order |
| outreach | outreach | 5 | Operational spine (CHILD) |
| outreach | outreach_excluded | 10 | Exclusion tracking |
| outreach | blog | 8 | Content signals |
| bit | authorization_log | 12 | BIT authorization requests |
| bit | movement_events | 17 | Movement detection |
| bit | phase_state | 14 | Phase state tracking |
| bit | proof_lines | 11 | Human-readable proofs |

**Total Columns Documented**: 143

---

## ENUM TYPES DOCUMENTED (13)

| Schema | ENUM Name | Values | Purpose |
|--------|-----------|--------|---------|
| bit | authorization_band | 6 | BIT tier levels (SILENT → DIRECT) |
| bit | movement_direction | 4 | Intent direction (INCREASING, etc.) |
| bit | movement_domain | 3 | Signal categories |
| bit | pressure_class | 5 | Pressure types |
| outreach | blog_source_type | 7 | Content source types |
| outreach | event_type | 10 | Engagement events |
| outreach | funnel_membership | 4 | Funnel classification |
| outreach | hub_status_enum | 4 | Hub execution status |
| outreach | lifecycle_state | 8 | Lifecycle stages |
| outreach | override_type_enum | 6 | Override types |
| people | email_status_t | 4 | Email verification status |
| public | pressure_class_type | 5 | DEPRECATED (→ bit.pressure_class) |
| public | pressure_domain | 3 | DEPRECATED (→ bit.movement_domain) |

**Total ENUM Values**: 69

---

## ALIGNMENT VERIFICATION

### v1.0 FROZEN Rule
```sql
-- MUST ALWAYS BE EQUAL
SELECT COUNT(*) FROM outreach.outreach = 51,148
SELECT COUNT(*) FROM cl.company_identity WHERE outreach_id IS NOT NULL = 51,148
```

**Current Status**: ALIGNED ✓

---

## USAGE WORKFLOW

### For ERD Diagram Updates

1. **Read Quick Reference**
   - File: `ERD_QUICK_REFERENCE.md`
   - Time: 5 minutes
   - Purpose: Get critical changes at a glance

2. **Review Audit Findings**
   - File: `ERD_SCHEMA_AUDIT_FINDINGS.md`
   - Time: 10 minutes
   - Purpose: Understand what needs to be fixed

3. **Consult Full Reference**
   - File: `NEON_SCHEMA_REFERENCE_FOR_ERD.md`
   - Time: As needed
   - Purpose: Look up specific column details

4. **Add ENUM Legends**
   - File: `NEON_ENUM_TYPES_REFERENCE.md`
   - Time: 15 minutes
   - Purpose: Add color-coded legends to ERD

5. **Verify Completion**
   - File: `SCHEMA_INTROSPECTION_SUMMARY.md`
   - Time: 5 minutes
   - Purpose: Check off completed tasks

---

## RELATED DOCUMENTATION

### Existing ERD Files
- `docs/MASTER_ERD.md` - Current master ERD
- `docs/COMPLETE_SYSTEM_ERD.md` - Complete system view
- `docs/ERD_DIAGRAM.md` - Legacy ERD
- `docs/ERD_SUMMARY.md` - ERD summary

### Schema Documentation
- `docs/SCHEMA_REFERENCE.md` - Legacy schema reference
- `docs/NEON_DATABASE_INVENTORY.md` - Database inventory
- `NEON_TABLE_OWNERSHIP.md` - Table ownership matrix

### Drift Reports
- `ERD_NEON_DRIFT_REPORT.md` - ERD vs Neon drift
- `ERD_DRIFT_ANALYSIS_SUMMARY.md` - Drift analysis
- `ERD_DRIFT_ACTION_CHECKLIST.md` - Drift action items
- `docs/reports/SCHEMA_DRIFT_CHECK_2026-01-30.md` - Recent drift check

---

## INTROSPECTION METHODOLOGY

### Data Collection
1. Queried `information_schema.columns` for 12 critical tables
2. Queried `pg_type`, `pg_enum`, `pg_namespace` for ENUM types
3. Extracted column names, data types, nullability, defaults
4. Cataloged ENUM values with sort order

### Validation
1. Verified CL-Outreach alignment (51,148 = 51,148 ✓)
2. Confirmed kill switch tables exist
3. Verified BIT layer schema
4. Checked ENUM type consistency

### Documentation
1. Created 5 markdown files (58 KB total)
2. Exported raw JSON data (29 KB)
3. Cross-referenced with v1.0 doctrine
4. Prioritized corrections by impact

---

## MAINTENANCE

### When to Re-Introspect

1. **After schema migrations** - Verify new columns/tables
2. **Before major releases** - Ensure ERD accuracy
3. **Quarterly** - Catch schema drift
4. **After sovereignty changes** - Verify alignment

### Re-Introspection Command

```bash
# Run from repo root with Doppler
doppler run -- python query_schemas.py
doppler run -- python query_enums.py
```

**Note**: Scripts are temporary and were removed after execution

---

## CONTACT

**Generated By**: Neon Database Introspection
**Date**: 2026-02-02
**v1.0 Certification**: 2026-01-19
**CL-Outreach Alignment**: 51,148 = 51,148 ✓

**For Questions**: Reference `CLAUDE.md` for bootstrap guide

---

## QUICK LINKS

| Need | File | Section |
|------|------|---------|
| Critical PK/FK changes | ERD_QUICK_REFERENCE.md | Top of file |
| Full table schemas | NEON_SCHEMA_REFERENCE_FOR_ERD.md | By schema |
| Correction checklist | ERD_SCHEMA_AUDIT_FINDINGS.md | Update Checklist |
| ENUM color codes | NEON_ENUM_TYPES_REFERENCE.md | ERD Legend Recommendations |
| Alignment verification | SCHEMA_INTROSPECTION_SUMMARY.md | Alignment Verification |
| Raw JSON data | schema_introspection_results.json | N/A |

---

**Last Updated**: 2026-02-02
**Status**: SCHEMA INTROSPECTION COMPLETE
**Next Action**: Apply findings to ERD diagrams

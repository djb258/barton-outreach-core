# Schema Introspection Summary

**Date**: 2026-02-02
**Purpose**: Neon database schema introspection for ERD updates
**Status**: COMPLETE

---

## DELIVERABLES

### 1. Full Schema Reference
**File**: `NEON_SCHEMA_REFERENCE_FOR_ERD.md`

**Contents**:
- 12 critical tables with exact column definitions
- Data types, nullability, and default values
- Table relationships and foreign keys
- CL parent-child doctrine patterns
- Kill switch system schema
- BIT analytics layer schema

**Key Findings**:
- `cl.company_identity` has 33 columns (not the simplified version often referenced)
- `sovereign_company_id` is the actual PK (not `company_unique_id`)
- `outreach.outreach` uses `sovereign_id` as FK (column name mismatch)
- Kill switch tables exist and match v1.0 doctrine

---

### 2. ERD Audit Findings
**File**: `ERD_SCHEMA_AUDIT_FINDINGS.md`

**Contents**:
- Structural corrections needed for ERD
- Missing tables that should be added
- FK relationship corrections
- Column name mismatches
- Update checklist with priorities

**Critical Corrections**:
1. cl.company_identity PK → `sovereign_company_id` (not `company_unique_id`)
2. outreach.outreach FK → `sovereign_id` (not `sovereign_company_id`)
3. Add kill switch tables if missing
4. Add cl.company_domains (1:N relationship)
5. Document ENUM types in legend

---

### 3. ENUM Types Reference
**File**: `NEON_ENUM_TYPES_REFERENCE.md`

**Contents**:
- 13 ENUM types across 4 schemas
- 69 total ENUM values
- Usage matrix showing which tables use each ENUM
- Color coding recommendations for ERD
- Migration notes for deprecated ENUMs

**Key ENUMs**:
- `bit.authorization_band` (6 tiers: SILENT → DIRECT)
- `outreach.override_type_enum` (6 types: marketing_disabled, tier_cap, etc.)
- `outreach.lifecycle_state` (8 states: SUSPECT → CLIENT)
- `outreach.hub_status_enum` (4 states: PASS, IN_PROGRESS, FAIL, BLOCKED)
- `people.email_status_t` (4 colors: green, yellow, red, gray)

**Deprecated**:
- `public.pressure_class_type` → Migrate to `bit.pressure_class`
- `public.pressure_domain` → Migrate to `bit.movement_domain`

---

### 4. Raw Schema Data
**File**: `schema_introspection_results.json`

**Contents**:
- JSON export of all 12 tables
- Programmatic access to column definitions
- Can be used for automated ERD generation

**Size**: 986 lines
**Format**: JSON with nested arrays

---

## TABLES INTROSPECTED (12)

### CL Authority Registry (2)
1. `cl.company_identity` (33 columns) - PARENT REGISTRY
2. `cl.company_domains` (7 columns) - MULTI-DOMAIN SUPPORT

### Kill Switch System (2)
3. `outreach.manual_overrides` (12 columns) - OVERRIDE CONTROLS
4. `outreach.override_audit_log` (9 columns) - IMMUTABLE AUDIT

### Hub Registry (1)
5. `outreach.hub_registry` (12 columns) - WATERFALL ORDER

### Outreach Spine (2)
6. `outreach.outreach` (5 columns) - OPERATIONAL SPINE
7. `outreach.outreach_excluded` (10 columns) - EXCLUSION TRACKING

### Outreach Blog (1)
8. `outreach.blog` (8 columns) - CONTENT SIGNALS

### BIT Analytics (4)
9. `bit.authorization_log` (12 columns) - BIT AUTHORIZATION
10. `bit.movement_events` (17 columns) - MOVEMENT DETECTION
11. `bit.phase_state` (14 columns) - PHASE STATE TRACKING
12. `bit.proof_lines` (11 columns) - HUMAN-READABLE PROOFS

---

## KEY SCHEMA CORRECTIONS FOR ERD

### 1. Primary Key Corrections
**BEFORE**: cl.company_identity.company_unique_id (PK)
**AFTER**: cl.company_identity.sovereign_company_id (PK)
**STATUS**: company_unique_id is LEGACY, still present but not authoritative

### 2. Foreign Key Corrections
**BEFORE**: outreach.outreach → cl.company_identity.sovereign_company_id
**AFTER**: outreach.outreach.sovereign_id → cl.company_identity.sovereign_company_id
**STATUS**: Column name is `sovereign_id` (not `sovereign_company_id`)

### 3. New Tables to Add
- outreach.manual_overrides (kill switch)
- outreach.override_audit_log (kill switch)
- cl.company_domains (multi-domain)
- (If not already present in ERD)

### 4. ENUM Documentation
- Add ENUM legends to ERD
- Use color coding for lifecycle_state, hub_status_enum, email_status_t
- Document authorization_band tiers (SILENT → DIRECT)

---

## ALIGNMENT VERIFICATION

### CL-Outreach Alignment (v1.0 FROZEN)
```sql
-- MUST ALWAYS BE EQUAL
SELECT COUNT(*) FROM outreach.outreach = 51,148
SELECT COUNT(*) FROM cl.company_identity WHERE outreach_id IS NOT NULL = 51,148
```

**Status**: ALIGNED ✓

---

## NEXT ACTIONS

### Priority 1: Structural ERD Updates
1. [ ] Update cl.company_identity to show `sovereign_company_id` as PK
2. [ ] Add dotted line from `company_unique_id` (legacy) to `sovereign_company_id`
3. [ ] Update outreach.outreach FK label to `sovereign_id`
4. [ ] Add cl.company_domains with 1:N relationship

### Priority 2: Kill Switch System
1. [ ] Add outreach.manual_overrides table to ERD
2. [ ] Add outreach.override_audit_log table to ERD
3. [ ] Show FK: override_audit_log.override_id → manual_overrides.override_id
4. [ ] Add ENUM legend for override_type_enum

### Priority 3: ENUM Legends
1. [ ] Add authorization_band legend (6 tiers with color scale)
2. [ ] Add lifecycle_state legend (8 states with color coding)
3. [ ] Add hub_status_enum legend (4 states - traffic light)
4. [ ] Add email_status_t legend (4 colors)

### Priority 4: BIT Layer
1. [ ] Verify all BIT table relationships
2. [ ] Show movement_events → proof_lines linkage (via movement_ids array)
3. [ ] Document phase_state PK = FK pattern

---

## SCHEMA HEALTH

### Total Columns Documented: 143
- CL Authority: 40 columns (2 tables)
- Kill Switch: 21 columns (2 tables)
- Hub Registry: 12 columns (1 table)
- Outreach Spine: 15 columns (2 tables)
- Outreach Blog: 8 columns (1 table)
- BIT Analytics: 54 columns (4 tables)

### ENUM Types: 13
- bit schema: 4 ENUMs
- outreach schema: 6 ENUMs
- people schema: 1 ENUM
- public schema: 2 ENUMs (DEPRECATED)

### Foreign Key Relationships: 8+
- CL → Outreach (1:1)
- Outreach → Sub-hubs (1:N)
- CL → Domains (1:N)
- Manual Overrides → Audit Log (1:N)
- Movement Events → Proof Lines (N:N)
- Phase State → Company (1:1)

---

## VERIFICATION QUERIES

### Count Active Overrides
```sql
SELECT COUNT(*) FROM outreach.manual_overrides WHERE is_active = true;
```

### Check BIT Band Distribution
```sql
SELECT current_band, COUNT(*) FROM bit.phase_state GROUP BY current_band ORDER BY current_band;
```

### Verify Hub Waterfall Order
```sql
SELECT hub_id, hub_name, waterfall_order, gates_completion FROM outreach.hub_registry ORDER BY waterfall_order;
```

### List All ENUMs
```sql
SELECT n.nspname, t.typname FROM pg_type t JOIN pg_namespace n ON t.typnamespace = n.oid WHERE t.typtype = 'e' AND n.nspname IN ('bit', 'outreach', 'people', 'public') ORDER BY n.nspname, t.typname;
```

---

## FILES GENERATED

| File | Size | Purpose |
|------|------|---------|
| NEON_SCHEMA_REFERENCE_FOR_ERD.md | ~13KB | Complete schema reference |
| ERD_SCHEMA_AUDIT_FINDINGS.md | ~11KB | Corrections needed |
| NEON_ENUM_TYPES_REFERENCE.md | ~11KB | ENUM documentation |
| schema_introspection_results.json | ~29KB | Raw data export |
| SCHEMA_INTROSPECTION_SUMMARY.md | This file | Executive summary |

**Total Documentation**: ~64KB

---

## SCHEMA FREEZE STATUS

### v1.0 FROZEN Components
The following are FROZEN and require change request:

1. **CL Authority Registry**
   - cl.company_identity structure
   - WRITE-ONCE columns (outreach_id, sales_process_id, client_id)

2. **Kill Switch System**
   - outreach.manual_overrides
   - outreach.override_audit_log
   - override_type_enum values

3. **Hub Registry**
   - Waterfall execution order
   - gates_completion flags

4. **Outreach Spine**
   - outreach.outreach structure
   - CL-Outreach alignment rule

5. **BIT Layer**
   - authorization_band tiers
   - pressure_class values
   - movement_domain values

---

## DOCTRINE COMPLIANCE

### CL Parent-Child Pattern ✓
- CL mints `sovereign_company_id` (IMMUTABLE)
- Outreach mints `outreach_id` and registers in CL (WRITE-ONCE)
- Schema enforces 1:1 relationship with affected_rows checks

### Waterfall Execution ✓
- hub_registry defines execution order
- gates_completion blocks downstream
- hub_status_enum tracks state (PASS, FAIL, BLOCKED)

### Kill Switch Enforcement ✓
- manual_overrides table exists
- override_audit_log provides immutable trail
- override_type_enum covers all control types

### Alignment Rule ✓
- CL count = Outreach count (51,148 = 51,148)
- No orphaned outreach_ids after sovereign cleanup

---

**Last Updated**: 2026-02-02
**Status**: SCHEMA INTROSPECTION COMPLETE
**Next Action**: Apply findings to ERD documentation and diagrams
**Certification**: v1.0 BASELINE (2026-01-19)

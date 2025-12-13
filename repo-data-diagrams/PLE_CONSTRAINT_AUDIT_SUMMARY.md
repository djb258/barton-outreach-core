# PLE CONSTRAINT AUDIT SUMMARY

**Generated:** 2025-11-26 7:44 AM
**Barton ID:** 04.04.02.04.50000.001
**Status:** ⚠️ PARTIAL COMPLIANCE - Data Cleanup Required

---

## EXECUTIVE SUMMARY

The PLE (Pipeline Lifecycle Engine) constraint audit has been completed for the three core marketing schema tables: `company_master`, `company_slot`, and `people_master`. The audit evaluated NOT NULL, CHECK, and UNIQUE constraints required for data integrity.

### Key Findings

| Category | Required | Compliant | Missing/Issues | Compliance % |
|----------|----------|-----------|----------------|--------------|
| **NOT NULL Constraints** | 11 | 9 | 2 | 82% |
| **CHECK Constraints** | 4 | 0 | 4 | 0% |
| **UNIQUE Constraints** | 3 | 3 | 0 | 100% |
| **Data Violations** | 0 expected | 16 found | 16 | ⚠️ Blocking |

### Critical Issues

1. **16 employee_count violations** - Values outside 50-2000 range
2. **2 tables missing NOT NULL on created_at** - Required for audit trail
3. **4 CHECK constraints completely missing** - No validation at database level
4. **71 existing CHECK constraints** - Many auto-generated NOT NULL checks from migrations

---

## DETAILED FINDINGS

### 1. NOT NULL CONSTRAINTS (82% Compliant)

#### ✅ COMPLIANT (9/11)

| Table | Column | Status |
|-------|--------|--------|
| company_master | company_unique_id | ✅ NOT NULL |
| company_master | company_name | ✅ NOT NULL |
| company_master | source_system | ✅ NOT NULL |
| company_slot | company_slot_unique_id | ✅ NOT NULL |
| company_slot | company_unique_id | ✅ NOT NULL |
| company_slot | slot_type | ✅ NOT NULL |
| people_master | unique_id | ✅ NOT NULL |
| people_master | company_unique_id | ✅ NOT NULL |
| people_master | first_name | ✅ NOT NULL |
| people_master | last_name | ✅ NOT NULL |

#### ⚠️ NON-COMPLIANT (2/11)

| Table | Column | Current Status | Required | Action |
|-------|--------|----------------|----------|--------|
| **company_master** | **created_at** | Nullable | NOT NULL | Add constraint after fixing NULL values |
| **people_master** | **created_at** | Nullable | NOT NULL | Add constraint after fixing NULL values |

**Impact:** Audit trails incomplete without NOT NULL on created_at. Must fix NULL values first.

---

### 2. CHECK CONSTRAINTS (0% Compliant)

#### ❌ ALL MISSING (4/4)

| Constraint Name | Table | Column(s) | Condition | Purpose |
|-----------------|-------|-----------|-----------|---------|
| **chk_employee_range** | company_master | employee_count | >= 50 AND <= 2000 | PLE targeting criteria |
| **chk_state_valid** | company_master | address_state | IN (PA,VA,MD,OH,WV,KY + full names) | Geographic targeting |
| **chk_slot_type** | company_slot | slot_type | LOWER(slot_type) IN (ceo,cfo,hr) | Role validation |
| **chk_contact_required** | people_master | linkedin_url, email | At least one NOT NULL | Outreach requirement |

**Impact:** No database-level validation for business rules. Invalid data can be inserted silently.

#### Existing CHECK Constraints

The audit found **71 existing CHECK constraints**, primarily:
- Auto-generated NOT NULL checks from migrations (naming pattern: `81920_*_not_null`)
- Barton ID format validation (e.g., `company_master_barton_id_format`)
- Domain value checks (e.g., `company_slot_slot_type_check`)
- Email format validation (e.g., `people_master_email_format`)

**Note:** There are **2 duplicate slot_type CHECK constraints** on `company_slot`:
1. `company_slot_slot_type_check` - Validates CEO/CFO/HR only (3 values)
2. `company_slot_slot_type_check` - Validates CEO/CFO/HR/CTO/CMO/COO/VP_SALES/VP_MARKETING/DIRECTOR/MANAGER (10 values)

This conflict needs to be resolved before adding the new `chk_slot_type` constraint.

---

### 3. UNIQUE CONSTRAINTS (100% Compliant)

#### ✅ ALL COMPLIANT (3/3)

| Constraint Name | Table | Type | Columns | Status |
|-----------------|-------|------|---------|--------|
| company_master_pkey | company_master | PRIMARY KEY | company_unique_id | ✅ Active |
| unique_company_slot | company_slot | UNIQUE | company_unique_id, slot_type | ✅ Active |
| people_master_pkey | people_master | PRIMARY KEY | unique_id | ✅ Active |

**Status:** All required unique constraints are in place. No duplicates detected.

---

## DATA VIOLATIONS (16 Total)

### Violation Breakdown

| Violation Type | Count | Severity | Blocking Constraint |
|----------------|-------|----------|---------------------|
| Employee count < 50 or > 2000 | 16 | High | chk_employee_range |
| NULL created_at (company_master) | TBD | High | NOT NULL constraint |
| NULL created_at (people_master) | TBD | High | NOT NULL constraint |
| Invalid state codes | 0 | - | - |
| Invalid slot types | 0 | - | - |
| Missing contact info | 0 | - | - |
| Duplicate slots | 0 | - | - |

### Details on Employee Count Violations

**16 companies** have employee_count values outside the PLE targeting range (50-2000):
- Some may be < 50 (too small for PLE criteria)
- Some may be > 2000 (too large for PLE criteria)

**Action Required:**
1. Run detailed violation query: `ple_data_violations_detailed.sql`
2. Review each company individually
3. Either:
   - Correct the employee_count if data is wrong
   - Set to NULL if unknown (allows record to bypass CHECK constraint)
   - Remove company from PLE targeting if intentionally outside range

---

## RECOMMENDED REMEDIATION PLAN

### Phase 1: Data Investigation (Priority 1)

```sql
-- Run this query to see exact violations
\i C:/Users/CUSTOM PC/Desktop/Cursor Builds/barton-outreach-core/ctb/sys/enrichment/ple_data_violations_detailed.sql
```

**Expected Output:**
- List of 16 companies with out-of-range employee counts
- Count of NULL created_at in company_master
- Count of NULL created_at in people_master

### Phase 2: Data Cleanup (Priority 2)

#### Option A: Conservative Approach (Recommended)

```sql
BEGIN;

-- 1. Set created_at from promoted_from_intake_at where available
UPDATE marketing.company_master
SET created_at = promoted_from_intake_at, updated_at = NOW()
WHERE created_at IS NULL AND promoted_from_intake_at IS NOT NULL;

UPDATE marketing.people_master
SET created_at = promoted_from_intake_at, updated_at = NOW()
WHERE created_at IS NULL AND promoted_from_intake_at IS NOT NULL;

-- 2. Set remaining NULL created_at to NOW()
UPDATE marketing.company_master
SET created_at = NOW(), updated_at = NOW()
WHERE created_at IS NULL;

UPDATE marketing.people_master
SET created_at = NOW(), updated_at = NOW()
WHERE created_at IS NULL;

-- 3. Set out-of-range employee_count to NULL (allows bypass of CHECK constraint)
UPDATE marketing.company_master
SET employee_count = NULL, updated_at = NOW()
WHERE employee_count IS NOT NULL
AND (employee_count < 50 OR employee_count > 2000);

-- Verify changes before committing
SELECT 'company_master NULL created_at' as check, COUNT(*) FROM marketing.company_master WHERE created_at IS NULL
UNION ALL
SELECT 'people_master NULL created_at', COUNT(*) FROM marketing.people_master WHERE created_at IS NULL
UNION ALL
SELECT 'employee_count violations', COUNT(*) FROM marketing.company_master WHERE employee_count IS NOT NULL AND (employee_count < 50 OR employee_count > 2000);

-- If all 0, commit. Otherwise, rollback and investigate.
COMMIT;
-- ROLLBACK;
```

#### Option B: Manual Review Approach

1. Export violation list to CSV
2. Review each company with business stakeholders
3. Correct data based on accurate sources (LinkedIn, company websites, etc.)
4. Re-import corrected data
5. Re-run audit to verify 0 violations

### Phase 3: Add Constraints (Priority 3)

**ONLY after Phase 2 shows 0 violations:**

```sql
-- Execute the migration script
\i C:/Users/CUSTOM PC/Desktop/Cursor Builds/barton-outreach-core/ctb/sys/enrichment/ple_constraint_migration.sql
```

**Important:** Review the migration script before execution. It includes:
- NOT NULL on created_at columns
- All 4 CHECK constraints
- Verification queries

### Phase 4: Verification (Priority 4)

```sql
-- Re-run the audit
cd "C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core"
node ctb/sys/enrichment/ple_constraint_audit.js

-- Expected: 0 violations, 100% compliance
```

---

## CONSTRAINT CONFLICT RESOLUTION

### Duplicate slot_type CHECK Constraint

**Issue:** Two constraints with same name `company_slot_slot_type_check` but different rules:
1. Constraint 1: `slot_type IN ('CEO','CFO','HR')` (3 values)
2. Constraint 2: `slot_type IN ('CEO','CFO','HR','CTO','CMO','COO','VP_SALES','VP_MARKETING','DIRECTOR','MANAGER')` (10 values)

**Resolution Required:**

```sql
-- 1. Check which constraint is currently active
SELECT constraint_name, check_clause
FROM information_schema.check_constraints cc
JOIN information_schema.table_constraints tc ON cc.constraint_name = tc.constraint_name
WHERE tc.table_schema = 'marketing'
AND tc.table_name = 'company_slot'
AND tc.constraint_name LIKE '%slot_type%';

-- 2. Drop duplicate/incorrect constraints
ALTER TABLE marketing.company_slot
DROP CONSTRAINT IF EXISTS company_slot_slot_type_check;

-- 3. Add the PLE-specific constraint (CEO/CFO/HR only)
ALTER TABLE marketing.company_slot
ADD CONSTRAINT chk_slot_type
CHECK (LOWER(slot_type) IN ('ceo','cfo','hr'));
```

**Business Rule Clarification Needed:**
- Should PLE support only 3 roles (CEO/CFO/HR)?
- Or should it expand to 10 roles including CTO, CMO, etc.?
- Current PLE documentation specifies 3 roles only

---

## FILES GENERATED

| File | Location | Purpose |
|------|----------|---------|
| **PLE_CONSTRAINT_AUDIT_REPORT.md** | Root directory | Full audit results with detailed tables |
| **ple_constraint_migration.sql** | ctb/sys/enrichment/ | SQL script to add missing constraints |
| **ple_data_violations_detailed.sql** | ctb/sys/enrichment/ | Queries to identify specific violation records |
| **ple_constraint_audit.js** | ctb/sys/enrichment/ | Reusable audit script |
| **PLE_CONSTRAINT_AUDIT_SUMMARY.md** | Root directory | This executive summary |

---

## NEXT STEPS (Action Items)

### Immediate (Today)

- [ ] Run `ple_data_violations_detailed.sql` to identify specific violations
- [ ] Review 16 companies with employee_count issues
- [ ] Decide on Option A (set to NULL) or Option B (manual correction)

### Short-term (This Week)

- [ ] Execute Phase 2 data cleanup (after review)
- [ ] Verify 0 violations with re-run of audit
- [ ] Resolve slot_type CHECK constraint conflict
- [ ] Execute Phase 3 migration script

### Medium-term (This Month)

- [ ] Update PLE ingestion pipeline to validate data BEFORE insertion
- [ ] Add application-level validation for employee_count range
- [ ] Document constraint rules in developer handbook
- [ ] Create monitoring dashboard for constraint violations

---

## COMPLIANCE ROADMAP

### Current State (2025-11-26)

```
NOT NULL:     ████████░░ 82%
CHECK:        ░░░░░░░░░░  0%
UNIQUE:       ██████████ 100%
DATA QUALITY: ░░░░░░░░░░  0% (16 violations)
────────────────────────────────
OVERALL:      ████░░░░░░ 46%
```

### Target State (After Remediation)

```
NOT NULL:     ██████████ 100%
CHECK:        ██████████ 100%
UNIQUE:       ██████████ 100%
DATA QUALITY: ██████████ 100% (0 violations)
────────────────────────────────
OVERALL:      ██████████ 100%
```

---

## RISK ASSESSMENT

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| Data loss during cleanup | High | Low | Use transactions (BEGIN/ROLLBACK/COMMIT) |
| Constraint addition fails | Medium | Medium | Fix violations first, test in transaction |
| Application breaks after constraints | Medium | Low | Test in staging environment first |
| Incorrect data correction | High | Medium | Manual review by business stakeholders |
| Downtime during migration | Low | Low | Run during maintenance window |

---

## APPENDIX A: CONSTRAINT DEFINITIONS

### NOT NULL Constraints

```sql
-- company_master
ALTER TABLE marketing.company_master ALTER COLUMN created_at SET NOT NULL;

-- people_master
ALTER TABLE marketing.people_master ALTER COLUMN created_at SET NOT NULL;
```

### CHECK Constraints

```sql
-- Employee count range (PLE targeting)
ALTER TABLE marketing.company_master
ADD CONSTRAINT chk_employee_range
CHECK (employee_count >= 50 AND employee_count <= 2000);

-- State validation (mid-Atlantic region)
ALTER TABLE marketing.company_master
ADD CONSTRAINT chk_state_valid
CHECK (address_state IN ('PA','VA','MD','OH','WV','KY','Pennsylvania','Virginia','Maryland','Ohio','West Virginia','Kentucky'));

-- Slot type validation (CEO/CFO/HR only)
ALTER TABLE marketing.company_slot
ADD CONSTRAINT chk_slot_type
CHECK (LOWER(slot_type) IN ('ceo','cfo','hr'));

-- Contact info required (LinkedIn OR email)
ALTER TABLE marketing.people_master
ADD CONSTRAINT chk_contact_required
CHECK (linkedin_url IS NOT NULL OR email IS NOT NULL);
```

### UNIQUE Constraints

```sql
-- Already in place, no action needed:
-- company_master: PRIMARY KEY (company_unique_id)
-- company_slot: UNIQUE (company_unique_id, slot_type)
-- people_master: PRIMARY KEY (unique_id)
```

---

## APPENDIX B: AUDIT COMMAND

To re-run this audit at any time:

```bash
cd "C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core"
node ctb/sys/enrichment/ple_constraint_audit.js
```

This will regenerate all audit files with current database state.

---

**Audit Completed By:** PLE Constraint Audit Script (Barton ID: 04.04.02.04.50000.001)
**Report Generated:** 2025-11-26 7:44 AM
**Database:** Neon PostgreSQL (Marketing DB)
**Schema:** marketing
**Tables Audited:** company_master, company_slot, people_master

---

**Status:** ⚠️ ACTION REQUIRED - Review violations and execute remediation plan


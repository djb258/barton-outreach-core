# ERD Schema Audit Findings

**Audit Date**: 2026-02-02
**Purpose**: Identify discrepancies between Neon actual schema and ERD documentation
**Scope**: Critical tables for v1.0 baseline

---

## EXECUTIVE SUMMARY

### Tables Audited: 12
- CL Authority Registry: 2 tables
- Kill Switch System: 2 tables
- Hub Registry: 1 table
- Outreach Spine: 2 tables
- Outreach Blog: 1 table
- BIT Tables: 4 tables

### Key Findings

1. **cl.company_identity** has 33 columns (PRIMARY KEY is `sovereign_company_id`, not `company_unique_id`)
2. **Kill Switch tables** exist and match v1.0 doctrine (manual_overrides + override_audit_log)
3. **BIT tables** all present with correct schema
4. **outreach.outreach** uses `sovereign_id` as FK (not `sovereign_company_id`)
5. **Custom ENUM types** present in several tables (override_type, source_type_enum)

---

## CRITICAL SCHEMA CORRECTIONS

### 1. cl.company_identity

**ISSUE**: Documentation may show `company_unique_id` as PK, but actual PK is `sovereign_company_id`

| Column | Status | Notes |
|--------|--------|-------|
| company_unique_id | LEGACY | uuid, NOT NULL, gen_random_uuid() |
| sovereign_company_id | **ACTUAL PK** | uuid, NULLABLE but UNIQUE constraint |
| outreach_id | CORRECT | uuid, NULLABLE, WRITE-ONCE |
| sales_process_id | CORRECT | uuid, NULLABLE, WRITE-ONCE |
| client_id | CORRECT | uuid, NULLABLE, WRITE-ONCE |

**Action Required**: ERD must show `sovereign_company_id` as PK with dotted line to `company_unique_id` (legacy)

---

### 2. outreach.outreach

**ISSUE**: FK uses `sovereign_id` not `sovereign_company_id`

| Column | Actual Schema | Expected | Notes |
|--------|---------------|----------|-------|
| outreach_id | uuid, NOT NULL, PK | ✓ CORRECT | |
| **sovereign_id** | **uuid, NOT NULL, FK** | **sovereign_company_id** | **Column name mismatch** |
| domain | varchar(255), NULLABLE | ✓ CORRECT | |

**Action Required**: ERD must show FK as `sovereign_id` → `cl.company_identity.sovereign_company_id`

---

### 3. outreach.manual_overrides (Kill Switch)

**NEW TABLE** - May not be in existing ERD

| Column | Data Type | Constraints | Notes |
|--------|-----------|-------------|-------|
| override_id | uuid | PK, NOT NULL | |
| company_unique_id | text | NOT NULL | |
| override_type | USER-DEFINED | NOT NULL | ENUM: HARD_FAIL, SKIP, FORCE_TIER, etc. |
| reason | text | NOT NULL | |
| metadata | jsonb | DEFAULT '{}' | |
| created_at | timestamptz | NOT NULL, DEFAULT now() | |
| created_by | text | NOT NULL, DEFAULT CURRENT_USER | |
| expires_at | timestamptz | NULLABLE | Optional expiration |
| is_active | boolean | NOT NULL, DEFAULT true | Soft delete flag |
| deactivated_at | timestamptz | NULLABLE | |
| deactivated_by | text | NULLABLE | |
| deactivation_reason | text | NULLABLE | |

**Action Required**: Add to ERD if missing

---

### 4. outreach.override_audit_log (Kill Switch)

**NEW TABLE** - May not be in existing ERD

| Column | Data Type | Constraints | Notes |
|--------|-----------|-------------|-------|
| audit_id | uuid | PK, NOT NULL | |
| company_unique_id | text | NOT NULL | |
| override_id | uuid | NULLABLE | FK to manual_overrides |
| action | text | NOT NULL | CREATED, DEACTIVATED, etc. |
| override_type | USER-DEFINED | NULLABLE | |
| old_value | jsonb | NULLABLE | Previous state |
| new_value | jsonb | NULLABLE | New state |
| performed_by | text | NOT NULL, DEFAULT CURRENT_USER | |
| performed_at | timestamptz | NOT NULL, DEFAULT now() | |

**Action Required**: Add to ERD if missing

---

### 5. outreach.hub_registry

**STATUS**: Likely exists but verify waterfall_order values

| hub_id | hub_name | doctrine_id | waterfall_order | gates_completion |
|--------|----------|-------------|-----------------|------------------|
| cl | Company Lifecycle | PARENT | 1 | true |
| company-target | Company Target | 04.04.01 | 2 | true |
| dol-filings | DOL Filings | 04.04.03 | 3 | true |
| people-intelligence | People Intelligence | 04.04.02 | 4 | true |
| blog-content | Blog Content | 04.04.05 | 5 | false |

**Action Required**: Verify ERD shows correct waterfall order (DOL before People)

---

### 6. outreach.blog

**POTENTIAL ISSUE**: Has TWO source_type columns

| Column | Data Type | Notes |
|--------|-----------|-------|
| source_type | text | Legacy text field |
| source_type_enum | USER-DEFINED | New ENUM field |

**Action Required**: ERD should show migration path from text to ENUM

---

### 7. BIT Tables

**STATUS**: All present and correct

| Table | PK Column | FK to CL | Notes |
|-------|-----------|----------|-------|
| bit.authorization_log | log_id | company_unique_id | ✓ |
| bit.movement_events | movement_id | company_unique_id | ✓ |
| bit.phase_state | company_unique_id | company_unique_id | PK is FK |
| bit.proof_lines | proof_id | company_unique_id | ✓ |

**Action Required**: Verify ERD shows correct relationships

---

### 8. cl.company_domains

**STATUS**: Correct - multi-domain support

| Column | Data Type | Notes |
|--------|-----------|-------|
| domain_id | uuid, PK | |
| company_unique_id | uuid, FK | FK to cl.company_identity |
| domain | text, NOT NULL | Domain string |
| domain_health | text | Health status |
| mx_present | boolean | MX record check |
| domain_name_confidence | integer | Confidence score |
| checked_at | timestamptz | Last health check |

**Action Required**: ERD should show 1:N relationship from cl.company_identity

---

## ENUM TYPES TO DOCUMENT

The following ENUM types are in use but show as "USER-DEFINED" in schema:

1. **outreach.override_type_enum**
   - Used in: manual_overrides, override_audit_log
   - Likely values: HARD_FAIL, SKIP, FORCE_TIER, etc.

2. **outreach.source_type_enum**
   - Used in: blog
   - Likely values: BLOG_POST, NEWS_ARTICLE, PRESS_RELEASE, etc.

**Action Required**: Query actual ENUM values for ERD legend

---

## MISSING TABLES (Expected but Not Queried)

The following tables were referenced in doctrine but not queried:

1. **outreach.company_target** (Company Target sub-hub)
2. **outreach.people** (People Intelligence sub-hub)
3. **outreach.dol** (DOL Filings sub-hub)
4. **outreach.company_target_archive** (Sovereign cleanup)
5. **outreach.people_archive** (Sovereign cleanup)
6. **people.company_slot** (Slot assignments)
7. **people.people_master** (Contact data)

**Action Required**: Query these tables in follow-up if needed for ERD

---

## ERD UPDATE CHECKLIST

### Priority 1: Structural Corrections

- [ ] Update cl.company_identity PK to show `sovereign_company_id` (not company_unique_id)
- [ ] Update outreach.outreach FK to show `sovereign_id` (not sovereign_company_id)
- [ ] Add cl.company_domains with 1:N relationship

### Priority 2: Kill Switch System

- [ ] Add outreach.manual_overrides table
- [ ] Add outreach.override_audit_log table
- [ ] Show FK relationship: override_audit_log → manual_overrides
- [ ] Document override_type_enum values

### Priority 3: Hub Registry

- [ ] Verify outreach.hub_registry waterfall order
- [ ] Show gates_completion flags
- [ ] Document core metrics and thresholds

### Priority 4: BIT Layer

- [ ] Verify bit.authorization_log relationships
- [ ] Verify bit.movement_events relationships
- [ ] Verify bit.phase_state (PK = FK pattern)
- [ ] Verify bit.proof_lines relationships
- [ ] Show movement_events → proof_lines linkage

### Priority 5: Blog Schema

- [ ] Document source_type → source_type_enum migration
- [ ] Show correct FK: blog → outreach.outreach

---

## QUERY COMMANDS FOR ENUM VALUES

If you need to document ENUM values, run:

```sql
-- Get override_type enum values
SELECT enumlabel
FROM pg_enum
WHERE enumtypid = 'outreach.override_type_enum'::regtype
ORDER BY enumsortorder;

-- Get source_type enum values
SELECT enumlabel
FROM pg_enum
WHERE enumtypid = 'outreach.source_type_enum'::regtype
ORDER BY enumsortorder;
```

---

## RELATIONSHIPS REQUIRING ERD UPDATES

### 1. CL Parent-Child Pattern

```
cl.company_identity (sovereign_company_id)
    ↓ 1:1 FK
outreach.outreach (sovereign_id)  ← NOTE: Column name is sovereign_id
    ↓ 1:N FK
[company_target, people, dol, blog] (outreach_id)
```

### 2. Kill Switch Overlay

```
Any company_unique_id
    ← N:1 lookup
outreach.manual_overrides (company_unique_id)
    ↓ 1:N FK
outreach.override_audit_log (override_id)
```

### 3. BIT Analytics Layer

```
Any company_unique_id
    ← 1:1
bit.phase_state (company_unique_id)  ← PK is FK

Any company_unique_id
    ← N:1
bit.movement_events (company_unique_id)
    ↓ N:N via movement_ids ARRAY
bit.proof_lines (movement_ids[])
```

---

## SCHEMA VERIFICATION QUERIES

Use these to verify counts and relationships:

```sql
-- Verify CL-Outreach alignment (MUST BE EQUAL)
SELECT
    (SELECT COUNT(*) FROM outreach.outreach) AS outreach_count,
    (SELECT COUNT(*) FROM cl.company_identity WHERE outreach_id IS NOT NULL) AS cl_outreach_count;
-- Expected: 51,148 = 51,148

-- Count manual overrides
SELECT is_active, COUNT(*)
FROM outreach.manual_overrides
GROUP BY is_active;

-- Count override audit entries
SELECT action, COUNT(*)
FROM outreach.override_audit_log
GROUP BY action;

-- BIT phase distribution
SELECT phase_status, COUNT(*)
FROM bit.phase_state
GROUP BY phase_status;

-- BIT band distribution
SELECT current_band, COUNT(*)
FROM bit.phase_state
GROUP BY current_band
ORDER BY current_band;
```

---

**Last Updated**: 2026-02-02
**Status**: READY FOR ERD UPDATES
**Next Action**: Apply findings to ERD diagrams + update mermaid/drawio files

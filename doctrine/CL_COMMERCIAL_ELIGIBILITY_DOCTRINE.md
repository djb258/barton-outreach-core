# CL Commercial Eligibility Doctrine

**Doctrine Version**: 1.0
**Status**: ACTIVE
**Authority**: Company Lifecycle (CL) — Sovereign Identity Hub
**Created**: 2026-01-29
**Last Modified**: 2026-01-29

---

## Foundational Principle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│              ADMISSION ≠ ELIGIBILITY. IDENTITY ≠ MARKETABILITY.            │
│                                                                             │
│   A company may be a valid identity but NOT a valid marketing target.      │
│   Commercial eligibility is evaluated AFTER admission succeeds.            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Doctrine Summary

| Concept | Definition |
|---------|------------|
| **Admission** | Company meets identity criteria (domain OR LinkedIn). Results in `company_unique_id`. |
| **Eligibility** | Company is a valid commercial marketing target. Results in `eligibility_status = 'ELIGIBLE'`. |
| **Exclusion** | Company is NOT a valid marketing target. Results in `eligibility_status = 'INELIGIBLE'`. |

---

## Two-Gate Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CL TWO-GATE ADMISSION MODEL                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   GATE 1: ADMISSION (Identity)                                              │
│   ─────────────────────────────                                             │
│   Question: "Is this a real, identifiable company?"                         │
│   Criteria: Domain OR LinkedIn URL present                                  │
│   Outcome:  ADMIT → mint company_unique_id                                  │
│             REJECT → no CL record                                           │
│                                                                             │
│                              ↓ (if admitted)                                │
│                                                                             │
│   GATE 2: ELIGIBILITY (Commercial Filter)                                   │
│   ────────────────────────────────────────                                  │
│   Question: "Is this a valid commercial marketing target?"                  │
│   Criteria: NOT in excluded categories                                      │
│   Outcome:  ELIGIBLE → may receive outreach_id                              │
│             INELIGIBLE → blocked from marketing pipeline                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Commercial Exclusion Categories

### The following entity types are **INELIGIBLE** for commercial marketing:

| Category | Code | Description |
|----------|------|-------------|
| **Government** | `GOV` | Federal, state, local government entities |
| **Education** | `EDU` | Schools, colleges, universities, districts |
| **Healthcare** | `HCF` | Hospitals, health systems, medical centers |
| **Religious** | `REL` | Churches, religious organizations, ministries |
| **Insurance** | `INS` | Insurance carriers, underwriters |
| **Non-Profit** | `NPO` | 501(c)(3) organizations (optional) |

---

## Exclusion Pattern Definitions

### 1. Government (GOV)

**Exclusion Reason**: `GOVERNMENT_ENTITY`

#### Domain Patterns
```sql
-- TLD exclusions
company_domain LIKE '%.gov'
company_domain LIKE '%.gov.%'
company_domain LIKE '%.mil'

-- Subdomain patterns
company_domain LIKE '%state.%.us'
company_domain LIKE '%county.%'
company_domain LIKE '%city.%'
```

#### Name Patterns
```sql
-- Federal
LOWER(company_name) LIKE '%federal government%'
LOWER(company_name) LIKE '%u.s. government%'
LOWER(company_name) LIKE '%department of%'

-- State/Local
LOWER(company_name) LIKE '%state of%'
LOWER(company_name) LIKE '%county of%'
LOWER(company_name) LIKE '%city of%'
LOWER(company_name) LIKE '%township%'
LOWER(company_name) LIKE '%municipality%'
```

---

### 2. Education (EDU)

**Exclusion Reason**: `EDUCATIONAL_INSTITUTION`

#### Domain Patterns
```sql
-- TLD exclusions
company_domain LIKE '%.edu'
company_domain LIKE '%.edu.%'

-- K-12 patterns
LOWER(company_domain) LIKE '%k12%'
LOWER(company_domain) LIKE '%.k12.%'

-- School patterns
LOWER(company_domain) LIKE '%school%'
LOWER(company_domain) LIKE '%academy%'
LOWER(company_domain) LIKE '%college%'
LOWER(company_domain) LIKE '%university%'
```

#### Name Patterns
```sql
-- School districts
LOWER(company_name) LIKE '%school district%'
LOWER(company_name) LIKE '%school system%'
LOWER(company_name) LIKE '%public schools%'
LOWER(company_name) LIKE '% isd'           -- Independent School District
LOWER(company_name) LIKE '%isd %'
LOWER(company_name) LIKE '% isd,%'

-- K-12 schools
LOWER(company_name) LIKE '%elementary school%'
LOWER(company_name) LIKE '%middle school%'
LOWER(company_name) LIKE '%high school%'
LOWER(company_name) LIKE '%junior high%'
LOWER(company_name) LIKE '%charter school%'
LOWER(company_name) LIKE '%public school%'
LOWER(company_name) LIKE '%private school%'
LOWER(company_name) LIKE '%montessori%'

-- Higher education
LOWER(company_name) LIKE '%college%'
LOWER(company_name) LIKE '%university%'
LOWER(company_name) LIKE '%community college%'
LOWER(company_name) LIKE '%technical college%'

-- Other education
LOWER(company_name) LIKE '%academy%'
LOWER(company_name) LIKE '%k12%'
LOWER(company_name) LIKE '%k-12%'
```

#### Exceptions (MAY be commercial)
```sql
-- These patterns may indicate commercial entities, not schools:
-- "Academy Sports" (retail)
-- "School Supplies Inc" (vendor)
-- "University Partners" (consulting)
-- Review manually if name contains: supplies, vendor, partner, consulting, software
```

---

### 3. Healthcare (HCF)

**Exclusion Reason**: `HEALTHCARE_FACILITY`

#### Domain Patterns
```sql
LOWER(company_domain) LIKE '%hospital%'
LOWER(company_domain) LIKE '%health%'
LOWER(company_domain) LIKE '%medical%'
LOWER(company_domain) LIKE '%clinic%'
```

#### Name Patterns
```sql
LOWER(company_name) LIKE '%hospital%'
LOWER(company_name) LIKE '%medical center%'
LOWER(company_name) LIKE '%health system%'
LOWER(company_name) LIKE '%healthcare system%'
LOWER(company_name) LIKE '%health department%'
LOWER(company_name) LIKE '%clinic%'
LOWER(company_name) LIKE '%nursing home%'
LOWER(company_name) LIKE '%assisted living%'
```

#### Exceptions (MAY be commercial)
```sql
-- Healthcare vendors/consultants may be valid targets:
-- "Hospital Equipment Co" (vendor)
-- "Healthcare Software Inc" (SaaS)
-- "Medical Staffing Agency" (staffing)
```

---

### 4. Religious (REL)

**Exclusion Reason**: `RELIGIOUS_ORGANIZATION`

#### Domain Patterns
```sql
LOWER(company_domain) LIKE '%church%'
LOWER(company_domain) LIKE '%ministry%'
LOWER(company_domain) LIKE '%baptist%'
LOWER(company_domain) LIKE '%methodist%'
LOWER(company_domain) LIKE '%catholic%'
LOWER(company_domain) LIKE '%lutheran%'
LOWER(company_domain) LIKE '%synagogue%'
LOWER(company_domain) LIKE '%mosque%'
LOWER(company_domain) LIKE '%temple%'
```

#### Name Patterns
```sql
LOWER(company_name) LIKE '%church%'
LOWER(company_name) LIKE '%ministry%'
LOWER(company_name) LIKE '%ministries%'
LOWER(company_name) LIKE '%congregation%'
LOWER(company_name) LIKE '%parish%'
LOWER(company_name) LIKE '%diocese%'
LOWER(company_name) LIKE '%baptist%'
LOWER(company_name) LIKE '%methodist%'
LOWER(company_name) LIKE '%lutheran%'
LOWER(company_name) LIKE '%presbyterian%'
LOWER(company_name) LIKE '%episcopal%'
LOWER(company_name) LIKE '%catholic%'
LOWER(company_name) LIKE '%synagogue%'
LOWER(company_name) LIKE '%mosque%'
LOWER(company_name) LIKE '%temple%'
LOWER(company_name) LIKE '%faith-based%'
```

---

### 5. Insurance (INS)

**Exclusion Reason**: `INSURANCE_CARRIER`

#### Domain Patterns
```sql
-- Major carriers (explicit list preferred)
company_domain IN (
    'aetna.com', 'anthem.com', 'bcbs.com', 'cigna.com',
    'humana.com', 'unitedhealthcare.com', 'kaiser.com'
)
```

#### Name Patterns
```sql
LOWER(company_name) LIKE '%insurance company%'
LOWER(company_name) LIKE '%insurance carrier%'
LOWER(company_name) LIKE '%mutual insurance%'
LOWER(company_name) LIKE '%life insurance%'
LOWER(company_name) LIKE '%health insurance%'
LOWER(company_name) LIKE '%underwriters%'
```

#### Exceptions (MAY be commercial)
```sql
-- Insurance brokers/agencies ARE valid targets:
-- "ABC Insurance Agency" (broker)
-- "Insurance Consultants LLC" (consulting)
-- These sell TO carriers, not AS carriers
```

---

## Database Implementation

### Required Columns in cl.company_identity

| Column | Type | Description |
|--------|------|-------------|
| `eligibility_status` | VARCHAR(20) | `ELIGIBLE`, `INELIGIBLE`, `PENDING` |
| `exclusion_reason` | VARCHAR(50) | Category code if ineligible |
| `exclusion_pattern` | VARCHAR(100) | Pattern that triggered exclusion |
| `eligibility_evaluated_at` | TIMESTAMPTZ | When eligibility was determined |

### Eligibility Status Values

| Status | Meaning | Can Receive outreach_id? |
|--------|---------|--------------------------|
| `ELIGIBLE` | Valid commercial target | YES |
| `INELIGIBLE` | Excluded category | NO |
| `PENDING` | Not yet evaluated | NO (until evaluated) |

---

## Evaluation SQL Template

```sql
-- Master eligibility evaluation query
UPDATE cl.company_identity
SET
    eligibility_status = CASE
        -- Government
        WHEN company_domain LIKE '%.gov' OR company_domain LIKE '%.mil'
            THEN 'INELIGIBLE'

        -- Education
        WHEN company_domain LIKE '%.edu'
            OR LOWER(company_domain) LIKE '%k12%'
            OR LOWER(company_domain) LIKE '%school%'
            OR LOWER(company_name) LIKE '%school district%'
            OR LOWER(company_name) LIKE '%school system%'
            OR LOWER(company_name) LIKE '% isd'
            OR LOWER(company_name) LIKE '%isd %'
            OR LOWER(company_name) LIKE '%college%'
            OR LOWER(company_name) LIKE '%university%'
            OR LOWER(company_name) LIKE '%academy%'
            OR LOWER(company_name) LIKE '%k12%'
            OR LOWER(company_name) LIKE '%k-12%'
            THEN 'INELIGIBLE'

        -- Healthcare
        WHEN LOWER(company_name) LIKE '%hospital%'
            OR LOWER(company_name) LIKE '%medical center%'
            OR LOWER(company_name) LIKE '%health system%'
            THEN 'INELIGIBLE'

        -- Religious
        WHEN LOWER(company_name) LIKE '%church%'
            OR LOWER(company_name) LIKE '%ministry%'
            OR LOWER(company_name) LIKE '%ministries%'
            THEN 'INELIGIBLE'

        -- Insurance carriers (not brokers)
        WHEN LOWER(company_name) LIKE '%insurance company%'
            OR LOWER(company_name) LIKE '%mutual insurance%'
            THEN 'INELIGIBLE'

        ELSE 'ELIGIBLE'
    END,

    exclusion_reason = CASE
        WHEN company_domain LIKE '%.gov' OR company_domain LIKE '%.mil'
            THEN 'GOVERNMENT_ENTITY'
        WHEN company_domain LIKE '%.edu'
            OR LOWER(company_domain) LIKE '%k12%'
            OR LOWER(company_domain) LIKE '%school%'
            OR LOWER(company_name) LIKE '%school%'
            OR LOWER(company_name) LIKE '%college%'
            OR LOWER(company_name) LIKE '%university%'
            OR LOWER(company_name) LIKE '%academy%'
            OR LOWER(company_name) LIKE '%k12%'
            OR LOWER(company_name) LIKE '% isd'
            THEN 'EDUCATIONAL_INSTITUTION'
        WHEN LOWER(company_name) LIKE '%hospital%'
            OR LOWER(company_name) LIKE '%medical center%'
            THEN 'HEALTHCARE_FACILITY'
        WHEN LOWER(company_name) LIKE '%church%'
            OR LOWER(company_name) LIKE '%ministry%'
            THEN 'RELIGIOUS_ORGANIZATION'
        WHEN LOWER(company_name) LIKE '%insurance company%'
            THEN 'INSURANCE_CARRIER'
        ELSE NULL
    END,

    eligibility_evaluated_at = NOW()

WHERE eligibility_status IS NULL OR eligibility_status = 'PENDING';
```

---

## Pipeline Integration

### When Eligibility Is Evaluated

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ELIGIBILITY EVALUATION TIMING                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   1. IMMEDIATE (On Admission)                                               │
│      When CL admits a new company, eligibility is evaluated immediately.    │
│      company_unique_id is minted, then eligibility_status is set.           │
│                                                                             │
│   2. BATCH (Cleanup/Reprocessing)                                           │
│      Periodic job evaluates any records with eligibility_status = NULL      │
│      or PENDING, applying latest exclusion patterns.                        │
│                                                                             │
│   3. ON-DEMAND (Manual Review)                                              │
│      Operator can trigger re-evaluation for specific companies.             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Outreach Gating

```sql
-- Outreach may ONLY attach to ELIGIBLE companies
INSERT INTO outreach.outreach (outreach_id, sovereign_id, ...)
SELECT gen_random_uuid(), ci.company_unique_id, ...
FROM cl.company_identity ci
WHERE ci.eligibility_status = 'ELIGIBLE'  -- HARD GATE
  AND ci.outreach_id IS NULL;

-- INELIGIBLE companies are BLOCKED from marketing pipeline
```

---

## Exclusion Count Impact

### Current Baseline (2026-01-29)

| Category | Count | % of Total |
|----------|-------|------------|
| Total in CL | 51,913 | 100% |
| Government | ~124 | 0.2% |
| Education | ~1,506 | 2.9% |
| Healthcare | ~124 | 0.2% |
| Religious | ~63 | 0.1% |
| Insurance | ~13 | 0.0% |
| **Total Excluded** | **~1,830** | **3.5%** |
| **Commercial Eligible** | **~50,083** | **96.5%** |

### Post-Exclusion Target

| Metric | Count |
|--------|-------|
| CL with outreach_id | ~50,083 |
| company_target | ~44,000 |
| With email patterns | ~40,000 |

---

## Audit Trail

All eligibility changes must be logged:

```sql
-- Eligibility audit log
CREATE TABLE cl.eligibility_audit_log (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_unique_id UUID NOT NULL,
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    exclusion_reason VARCHAR(50),
    changed_by VARCHAR(100),
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    change_source VARCHAR(50)  -- 'BATCH', 'MANUAL', 'ADMISSION'
);
```

---

## Invariants

### INV-ELIG-001: Eligibility Is Post-Admission

```yaml
invariant: ELIG-001
rule: "Eligibility evaluation occurs AFTER successful admission"
meaning: |
  A company must first have a company_unique_id before eligibility is evaluated.
  Eligibility does not affect admission. Admission does not imply eligibility.
enforcement: Eligibility column requires company_unique_id to exist
```

### INV-ELIG-002: Ineligible Companies Cannot Receive outreach_id

```yaml
invariant: ELIG-002
rule: "INELIGIBLE companies are blocked from marketing pipeline"
meaning: |
  If eligibility_status = 'INELIGIBLE', outreach_id must remain NULL.
  No marketing operations may reference ineligible companies.
enforcement: Outreach init gate checks eligibility_status = 'ELIGIBLE'
```

### INV-ELIG-003: Exclusion Patterns Are Centralized

```yaml
invariant: ELIG-003
rule: "All exclusion patterns are defined in this doctrine"
meaning: |
  Downstream hubs do not define their own exclusion logic.
  CL is the single source of truth for commercial eligibility.
enforcement: Outreach trusts cl.eligibility_status without re-evaluation
```

---

## Change Log

| Date | Version | Change |
|------|---------|--------|
| 2026-01-29 | 1.0 | Initial doctrine - GOV, EDU, HCF, REL, INS exclusions |

---

## Traceability

| Artifact | Reference |
|----------|-----------|
| Admission Gate | `doctrine/CL_ADMISSION_GATE_DOCTRINE.md` |
| School Analysis | `school_exclusion_analysis.md` |
| PRD | `docs/prd/PRD_COMPANY_HUB.md` |

---

**END OF COMMERCIAL ELIGIBILITY DOCTRINE**

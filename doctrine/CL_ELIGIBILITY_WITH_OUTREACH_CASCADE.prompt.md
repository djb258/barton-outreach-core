# CL Commercial Eligibility Filter

**Status**: ACTIVE
**Authority**: OPERATIONAL
**Version**: 2.1.0
**Change Protocol**: ADR + HUMAN APPROVAL REQUIRED

---

## ROLE

You are a **Commercial Eligibility Enforcement Agent** operating in the **CL (Company Lifecycle) repository**.

Your responsibilities:
1. **Identify non-commercial entities** in `cl.company_identity`
2. **Mark them as INELIGIBLE** with proper exclusion_reason
3. **Report completion** so barton-outreach-core can run its cascade cleanup

**You do NOT clean up Outreach data.** That happens automatically when barton-outreach-core queries your INELIGIBLE records.

---

## WHAT IS NON-COMMERCIAL?

**Our target market is commercial businesses** — companies that buy employee benefits (health insurance, retirement plans, etc.) through insurance brokers.

### Categories We Exclude

| Category | Why Exclude | Examples |
|----------|-------------|----------|
| **Government** | Mandated procurement (RFPs, GSA). Don't buy through commercial brokers. | City of Houston, Texas DPS, any .gov/.mil domain |
| **Schools & Universities** | Government-funded with public procurement requirements. | Springfield School District, Harvard University, any .edu domain |
| **Hospitals & Health Systems** | Self-insure or specialized group purchasing. Not standard commercial. | Memorial Hospital, Mayo Clinic Health System |
| **Churches & Religious Orgs** | Non-profit with denominational benefits programs. | First Baptist Church, Catholic Diocese of Austin |
| **Insurance (ALL)** | They ARE the insurance industry. Carriers sell it, brokers/agencies distribute it. Not our market. | State Farm, Allstate Insurance Agency, ABC Insurance Brokers |
| **Financial Services** | Financial advisors and wealth managers have their own benefits arrangements. Not standard commercial buyers. | Edward Jones, Morgan Stanley, Ameriprise Financial, Raymond James |

---

## DATABASE CONNECTION

```bash
# Via Doppler
doppler run -- python script.py

# Connection string in DATABASE_URL
```

---

## EXCLUSION CATEGORIES

| Code | Category | What to Exclude |
|------|----------|-----------------|
| `GOVERNMENT_ENTITY` | Government | Federal, state, local gov, .gov, .mil |
| `EDUCATIONAL_INSTITUTION` | Education | Schools, colleges, universities, .edu, k12 |
| `HEALTHCARE_FACILITY` | Healthcare | Hospitals, medical centers, health systems |
| `RELIGIOUS_ORGANIZATION` | Religious | Churches, ministries, religious orgs |
| `INSURANCE_ENTITY` | Insurance | ALL insurance: carriers, agencies, brokers, underwriters |
| `FINANCIAL_SERVICES` | Financial | Financial advisors, wealth management, investment firms |

---

## EXCLUSION PATTERNS

### 1. Government (GOVERNMENT_ENTITY)

```sql
-- Domain patterns
company_domain LIKE '%.gov'
company_domain LIKE '%.mil'
LOWER(company_domain) LIKE '%state.%.us'

-- Name patterns
LOWER(company_name) LIKE '%department of%'
LOWER(company_name) LIKE '%state of %'
LOWER(company_name) LIKE '%county of %'
LOWER(company_name) LIKE '%city of %'
LOWER(company_name) LIKE '%township%'
LOWER(company_name) LIKE '%municipality%'
```

### 2. Education (EDUCATIONAL_INSTITUTION)

```sql
-- Domain patterns
company_domain LIKE '%.edu'
LOWER(company_domain) LIKE '%k12%'
LOWER(company_domain) LIKE '%school%'

-- Name patterns
LOWER(company_name) LIKE '%school district%'
LOWER(company_name) LIKE '%school system%'
LOWER(company_name) LIKE '%public schools%'
LOWER(company_name) LIKE '% isd'
LOWER(company_name) LIKE '%isd %'
LOWER(company_name) LIKE '%elementary school%'
LOWER(company_name) LIKE '%middle school%'
LOWER(company_name) LIKE '%high school%'
LOWER(company_name) LIKE '%charter school%'
LOWER(company_name) LIKE '%college%'
LOWER(company_name) LIKE '%university%'
LOWER(company_name) LIKE '%academy%'
LOWER(company_name) LIKE '%k12%'
LOWER(company_name) LIKE '%k-12%'
```

### 3. Healthcare (HEALTHCARE_FACILITY)

```sql
LOWER(company_name) LIKE '%hospital%'
LOWER(company_name) LIKE '%medical center%'
LOWER(company_name) LIKE '%health system%'
LOWER(company_name) LIKE '%healthcare system%'
LOWER(company_name) LIKE '%health department%'
```

### 4. Religious (RELIGIOUS_ORGANIZATION)

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
LOWER(company_name) LIKE '%catholic%'
LOWER(company_name) LIKE '%synagogue%'
LOWER(company_name) LIKE '%mosque%'
LOWER(company_name) LIKE '%temple%'
```

### 5. Insurance — ALL (INSURANCE_ENTITY)

```sql
-- Carriers
LOWER(company_name) LIKE '%insurance company%'
LOWER(company_name) LIKE '%insurance carrier%'
LOWER(company_name) LIKE '%mutual insurance%'
LOWER(company_name) LIKE '%life insurance%'
LOWER(company_name) LIKE '%health insurance%'

-- Brokers and Agencies
LOWER(company_name) LIKE '%insurance agency%'
LOWER(company_name) LIKE '%insurance agencies%'
LOWER(company_name) LIKE '%insurance broker%'
LOWER(company_name) LIKE '%insurance brokerage%'
LOWER(company_name) LIKE '%insurance group%'
LOWER(company_name) LIKE '%insurance services%'

-- Underwriters
LOWER(company_name) LIKE '%underwriters%'
LOWER(company_name) LIKE '%underwriting%'
```

### 6. Financial Services (FINANCIAL_SERVICES)

```sql
-- Financial advisors
LOWER(company_name) LIKE '%financial advisor%'
LOWER(company_name) LIKE '%financial advisors%'
LOWER(company_name) LIKE '%financial planning%'
LOWER(company_name) LIKE '%financial services%'
LOWER(company_name) LIKE '%financial group%'

-- Wealth management
LOWER(company_name) LIKE '%wealth management%'
LOWER(company_name) LIKE '%wealth advisor%'
LOWER(company_name) LIKE '%investment advisor%'
LOWER(company_name) LIKE '%investment management%'

-- Known firms
LOWER(company_name) LIKE '%edward jones%'
LOWER(company_name) LIKE '%raymond james%'
LOWER(company_name) LIKE '%ameriprise%'
LOWER(company_name) LIKE '%morgan stanley%'
LOWER(company_name) LIKE '%merrill lynch%'
LOWER(company_name) LIKE '%charles schwab%'
LOWER(company_name) LIKE '%fidelity%'
LOWER(company_name) LIKE '%vanguard%'
```

---

## STEP 1: DISCOVERY — Count What Will Be Affected

```sql
SELECT
    CASE
        -- Government
        WHEN company_domain LIKE '%.gov' OR company_domain LIKE '%.mil'
            THEN 'GOVERNMENT_ENTITY'

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
            OR LOWER(company_name) LIKE '%elementary school%'
            OR LOWER(company_name) LIKE '%middle school%'
            OR LOWER(company_name) LIKE '%high school%'
            OR LOWER(company_name) LIKE '%charter school%'
            THEN 'EDUCATIONAL_INSTITUTION'

        -- Healthcare
        WHEN LOWER(company_name) LIKE '%hospital%'
            OR LOWER(company_name) LIKE '%medical center%'
            OR LOWER(company_name) LIKE '%health system%'
            THEN 'HEALTHCARE_FACILITY'

        -- Religious
        WHEN LOWER(company_name) LIKE '%church%'
            OR LOWER(company_name) LIKE '%ministry%'
            OR LOWER(company_name) LIKE '%ministries%'
            THEN 'RELIGIOUS_ORGANIZATION'

        -- Insurance (ALL)
        WHEN LOWER(company_name) LIKE '%insurance company%'
            OR LOWER(company_name) LIKE '%insurance carrier%'
            OR LOWER(company_name) LIKE '%mutual insurance%'
            OR LOWER(company_name) LIKE '%insurance agency%'
            OR LOWER(company_name) LIKE '%insurance agencies%'
            OR LOWER(company_name) LIKE '%insurance broker%'
            OR LOWER(company_name) LIKE '%insurance brokerage%'
            OR LOWER(company_name) LIKE '%insurance group%'
            OR LOWER(company_name) LIKE '%insurance services%'
            OR LOWER(company_name) LIKE '%underwriters%'
            THEN 'INSURANCE_ENTITY'

        -- Financial Services
        WHEN LOWER(company_name) LIKE '%financial advisor%'
            OR LOWER(company_name) LIKE '%financial advisors%'
            OR LOWER(company_name) LIKE '%financial planning%'
            OR LOWER(company_name) LIKE '%financial services%'
            OR LOWER(company_name) LIKE '%wealth management%'
            OR LOWER(company_name) LIKE '%investment advisor%'
            OR LOWER(company_name) LIKE '%edward jones%'
            OR LOWER(company_name) LIKE '%raymond james%'
            OR LOWER(company_name) LIKE '%ameriprise%'
            OR LOWER(company_name) LIKE '%morgan stanley%'
            OR LOWER(company_name) LIKE '%merrill lynch%'
            THEN 'FINANCIAL_SERVICES'

        ELSE 'COMMERCIAL'
    END AS category,
    COUNT(*) as count
FROM cl.company_identity
WHERE eligibility_status IS NULL
   OR eligibility_status != 'INELIGIBLE'
GROUP BY 1
ORDER BY 2 DESC;
```

---

## STEP 2: MARK AS INELIGIBLE

```sql
BEGIN;

UPDATE cl.company_identity
SET
    eligibility_status = 'INELIGIBLE',
    exclusion_reason = CASE
        -- Government
        WHEN company_domain LIKE '%.gov' OR company_domain LIKE '%.mil'
            THEN 'GOVERNMENT_ENTITY'

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
            OR LOWER(company_name) LIKE '%elementary school%'
            OR LOWER(company_name) LIKE '%middle school%'
            OR LOWER(company_name) LIKE '%high school%'
            OR LOWER(company_name) LIKE '%charter school%'
            THEN 'EDUCATIONAL_INSTITUTION'

        -- Healthcare
        WHEN LOWER(company_name) LIKE '%hospital%'
            OR LOWER(company_name) LIKE '%medical center%'
            OR LOWER(company_name) LIKE '%health system%'
            THEN 'HEALTHCARE_FACILITY'

        -- Religious
        WHEN LOWER(company_name) LIKE '%church%'
            OR LOWER(company_name) LIKE '%ministry%'
            OR LOWER(company_name) LIKE '%ministries%'
            THEN 'RELIGIOUS_ORGANIZATION'

        -- Insurance (ALL)
        WHEN LOWER(company_name) LIKE '%insurance company%'
            OR LOWER(company_name) LIKE '%insurance carrier%'
            OR LOWER(company_name) LIKE '%mutual insurance%'
            OR LOWER(company_name) LIKE '%insurance agency%'
            OR LOWER(company_name) LIKE '%insurance agencies%'
            OR LOWER(company_name) LIKE '%insurance broker%'
            OR LOWER(company_name) LIKE '%insurance brokerage%'
            OR LOWER(company_name) LIKE '%insurance group%'
            OR LOWER(company_name) LIKE '%insurance services%'
            OR LOWER(company_name) LIKE '%underwriters%'
            THEN 'INSURANCE_ENTITY'

        -- Financial Services
        WHEN LOWER(company_name) LIKE '%financial advisor%'
            OR LOWER(company_name) LIKE '%financial advisors%'
            OR LOWER(company_name) LIKE '%financial planning%'
            OR LOWER(company_name) LIKE '%financial services%'
            OR LOWER(company_name) LIKE '%wealth management%'
            OR LOWER(company_name) LIKE '%investment advisor%'
            OR LOWER(company_name) LIKE '%edward jones%'
            OR LOWER(company_name) LIKE '%raymond james%'
            OR LOWER(company_name) LIKE '%ameriprise%'
            OR LOWER(company_name) LIKE '%morgan stanley%'
            OR LOWER(company_name) LIKE '%merrill lynch%'
            THEN 'FINANCIAL_SERVICES'
    END,
    eligibility_evaluated_at = NOW()
WHERE (
    -- Government
    company_domain LIKE '%.gov'
    OR company_domain LIKE '%.mil'
    -- Education
    OR company_domain LIKE '%.edu'
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
    OR LOWER(company_name) LIKE '%elementary school%'
    OR LOWER(company_name) LIKE '%middle school%'
    OR LOWER(company_name) LIKE '%high school%'
    OR LOWER(company_name) LIKE '%charter school%'
    -- Healthcare
    OR LOWER(company_name) LIKE '%hospital%'
    OR LOWER(company_name) LIKE '%medical center%'
    OR LOWER(company_name) LIKE '%health system%'
    -- Religious
    OR LOWER(company_name) LIKE '%church%'
    OR LOWER(company_name) LIKE '%ministry%'
    OR LOWER(company_name) LIKE '%ministries%'
    -- Insurance (ALL)
    OR LOWER(company_name) LIKE '%insurance company%'
    OR LOWER(company_name) LIKE '%insurance carrier%'
    OR LOWER(company_name) LIKE '%mutual insurance%'
    OR LOWER(company_name) LIKE '%insurance agency%'
    OR LOWER(company_name) LIKE '%insurance agencies%'
    OR LOWER(company_name) LIKE '%insurance broker%'
    OR LOWER(company_name) LIKE '%insurance brokerage%'
    OR LOWER(company_name) LIKE '%insurance group%'
    OR LOWER(company_name) LIKE '%insurance services%'
    OR LOWER(company_name) LIKE '%underwriters%'
    -- Financial Services
    OR LOWER(company_name) LIKE '%financial advisor%'
    OR LOWER(company_name) LIKE '%financial advisors%'
    OR LOWER(company_name) LIKE '%financial planning%'
    OR LOWER(company_name) LIKE '%financial services%'
    OR LOWER(company_name) LIKE '%wealth management%'
    OR LOWER(company_name) LIKE '%investment advisor%'
    OR LOWER(company_name) LIKE '%edward jones%'
    OR LOWER(company_name) LIKE '%raymond james%'
    OR LOWER(company_name) LIKE '%ameriprise%'
    OR LOWER(company_name) LIKE '%morgan stanley%'
    OR LOWER(company_name) LIKE '%merrill lynch%'
)
AND (eligibility_status IS NULL OR eligibility_status != 'INELIGIBLE');

-- Check what was updated
SELECT eligibility_status, exclusion_reason, COUNT(*)
FROM cl.company_identity
WHERE eligibility_status = 'INELIGIBLE'
GROUP BY 1, 2
ORDER BY 3 DESC;

-- If looks correct:
COMMIT;
```

---

## STEP 3: MARK REMAINING AS ELIGIBLE

```sql
UPDATE cl.company_identity
SET
    eligibility_status = 'ELIGIBLE',
    eligibility_evaluated_at = NOW()
WHERE eligibility_status IS NULL
   OR eligibility_status = 'PENDING';
```

---

## STEP 4: VERIFY AND REPORT

```sql
-- Final state
SELECT
    eligibility_status,
    exclusion_reason,
    COUNT(*) as count,
    COUNT(outreach_id) as with_outreach_id
FROM cl.company_identity
GROUP BY 1, 2
ORDER BY 1, 3 DESC;
```

**Produce this report:**

```
================================================================================
CL COMMERCIAL ELIGIBILITY FILTER COMPLETE
================================================================================

Execution Date: [DATE]
Database: cl.company_identity

INELIGIBLE RECORDS MARKED:
─────────────────────────────────────────────────────────────────────────────────
Category                    | Total | With outreach_id | Needs Outreach Cleanup
─────────────────────────────────────────────────────────────────────────────────
GOVERNMENT_ENTITY           | [X]   | [X]              | YES
EDUCATIONAL_INSTITUTION     | [X]   | [X]              | YES
HEALTHCARE_FACILITY         | [X]   | [X]              | YES
RELIGIOUS_ORGANIZATION      | [X]   | [X]              | YES
INSURANCE_ENTITY            | [X]   | [X]              | YES
FINANCIAL_SERVICES          | [X]   | [X]              | YES
─────────────────────────────────────────────────────────────────────────────────
TOTAL INELIGIBLE            | [X]   | [X]              |
─────────────────────────────────────────────────────────────────────────────────

ELIGIBLE RECORDS:           | [X]   | [X]              |
─────────────────────────────────────────────────────────────────────────────────

STATUS: COMPLETE

================================================================================
NEXT STEP FOR BARTON-OUTREACH-CORE
================================================================================

CL eligibility filter is complete. [X] ineligible records have outreach_ids
that need to be cleaned up from the outreach schema.

Run this in barton-outreach-core:

    OUTREACH_CASCADE_CLEANUP.prompt.md

That prompt will:
1. Query cl.company_identity for INELIGIBLE records with outreach_id
2. Archive affected outreach records
3. Delete in FK order through all sub-hubs
4. Clear outreach_id in CL
5. Verify alignment

No export file needed — barton-outreach-core queries CL directly.

================================================================================
```

---

## WHAT BARTON-OUTREACH-CORE WILL DO

Once you're done, barton-outreach-core runs `OUTREACH_CASCADE_CLEANUP.prompt.md` which:

1. **Queries CL directly:**
   ```sql
   SELECT outreach_id FROM cl.company_identity
   WHERE eligibility_status = 'INELIGIBLE'
     AND outreach_id IS NOT NULL;
   ```

2. **Archives affected records** to `*_archive` tables

3. **Deletes in FK order:**
   - send_log → sequences → campaigns
   - manual_overrides, bit_signals, bit_scores
   - blog, people, dol, company_target
   - company_slot, people_master
   - outreach (spine, last)

4. **Clears outreach_id in CL:**
   ```sql
   UPDATE cl.company_identity
   SET outreach_id = NULL
   WHERE eligibility_status = 'INELIGIBLE';
   ```

5. **Verifies alignment:**
   - CL ELIGIBLE with outreach_id = outreach.outreach count

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-29 |
| Last Modified | 2026-01-29 |
| Version | 2.1.0 |
| Status | ACTIVE |
| Authority | OPERATIONAL |
| Downstream | OUTREACH_CASCADE_CLEANUP.prompt.md (barton-outreach-core) |

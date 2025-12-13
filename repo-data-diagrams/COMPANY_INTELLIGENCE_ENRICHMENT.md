# Company Intelligence Enrichment Layer

**Date Created:** 2025-11-27
**Architecture Principle:** COMPANY = asset (rich, permanent), PEOPLE = occupants (minimal, replaceable)
**Status:** ✅ Production Ready

---

## Overview

The Company Intelligence Enrichment Layer adds federal data, regulatory compliance, and contact pattern intelligence to the PLE system. This layer treats **companies as the asset** to be enriched, not people.

### Key Philosophy

- **Company-Centric**: Enrichment attaches to company records, not people
- **Role-Based Phone**: Phone numbers belong to slots (CEO role), not people
- **Pattern Detection**: Email patterns belong to companies (domain-level intelligence)
- **Federal IDs**: EIN, DUNS, CAGE codes track companies through government systems

---

## New Tables (3)

### 1. `marketing.form_5500`

**Purpose:** Store DOL Form 5500 data (retirement plan filings)

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PK | Auto-increment |
| company_unique_id | TEXT FK | Link to company (nullable - may not match initially) |
| ack_id | VARCHAR(30) | DOL acknowledgment ID |
| **ein** | VARCHAR(9) NOT NULL | Employer Identification Number |
| plan_number | VARCHAR(3) | Plan number (company may have multiple) |
| plan_name | VARCHAR(140) | Name of retirement plan |
| sponsor_name | VARCHAR(70) | Plan sponsor name (company name) |
| address | VARCHAR(35) | Company address |
| city | VARCHAR(22) | City |
| state | VARCHAR(2) | State abbreviation |
| zip | VARCHAR(12) | ZIP code |
| date_received | DATE | Date DOL received filing |
| plan_codes | VARCHAR(59) | Plan type codes |
| participant_count | INT | Number of plan participants |
| total_assets | NUMERIC(15,2) | Total plan assets |
| filing_year | INT | Year of filing |
| raw_payload | JSONB | Complete raw data |
| created_at | TIMESTAMP | Insert timestamp |
| updated_at | TIMESTAMP | Last update |

**Indexes:**
- `idx_5500_ein` on (ein)
- `idx_5500_company` on (company_unique_id)
- `idx_5500_state` on (state)
- `idx_5500_year` on (filing_year)

**Purpose:** Track company retirement plans, employee counts, and fiduciary responsibility. High-quality federal data source that can:
- Validate employee counts
- Provide EIN for matching across systems
- Identify companies with benefit plans (BIT signal: HR investment)
- Track plan participant growth (hiring/layoff indicator)

---

### 2. `marketing.dol_violations`

**Purpose:** Track DOL violations and penalties

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PK | Auto-increment |
| company_unique_id | TEXT FK | Link to company (nullable) |
| **ein** | VARCHAR(9) NOT NULL | Employer Identification Number |
| violation_type | VARCHAR(100) | Type of violation |
| violation_date | DATE | Date of violation |
| resolution_date | DATE | Date resolved (nullable) |
| penalty_amount | NUMERIC(12,2) | Penalty assessed |
| description | TEXT | Violation details |
| source_url | VARCHAR(500) | DOL source URL |
| raw_payload | JSONB | Complete raw data |
| detected_at | TIMESTAMP | When we detected this |

**Indexes:**
- `idx_violations_ein` on (ein)
- `idx_violations_company` on (company_unique_id)
- `idx_violations_type` on (violation_type)

**Purpose:** Compliance risk scoring. DOL violations indicate:
- Fiduciary problems (HR leadership instability)
- Financial stress (unpaid contributions)
- Regulatory scrutiny (BIT risk factor)

---

### 3. `marketing.form_5500_staging`

**Purpose:** Staging table for CSV import of Form 5500 data

| Column | Type | Description |
|--------|------|-------------|
| ack_id | VARCHAR(30) | DOL acknowledgment ID |
| ein | VARCHAR(9) | Employer ID |
| plan_number | VARCHAR(3) | Plan number |
| plan_name | VARCHAR(140) | Plan name |
| sponsor_name | VARCHAR(70) | Company name |
| address | VARCHAR(35) | Address |
| city | VARCHAR(22) | City |
| state | VARCHAR(2) | State |
| zip | VARCHAR(12) | ZIP |
| date_received | VARCHAR(10) | Date as string (MM/DD/YYYY) |
| plan_codes | VARCHAR(59) | Codes |
| participant_count | VARCHAR(20) | Count as string |
| total_assets | VARCHAR(30) | Assets as string |
| imported_at | TIMESTAMP | When imported |

**Usage:**
```sql
-- Import CSV
COPY marketing.form_5500_staging FROM '/path/to/5500_data.csv' CSV HEADER;

-- Process staging
CALL marketing.process_5500_staging();

-- Result: Staging cleared, records moved to form_5500, companies matched and updated with EIN
```

---

## New Columns (10)

### company_master (7 columns)

| Column | Type | Purpose |
|--------|------|---------|
| **ein** | VARCHAR(9) | Employer Identification Number (federal tax ID) |
| **duns** | VARCHAR(9) | Dun & Bradstreet Number (business credit ID) |
| **cage_code** | VARCHAR(5) | Commercial And Government Entity Code (govt contracting) |
| **email_pattern** | VARCHAR(50) | Detected email format (e.g., `{f}{last}@`) |
| **email_pattern_confidence** | INT | Confidence 0-100 |
| **email_pattern_source** | VARCHAR(50) | Source: hunter, manual, enrichment |
| **email_pattern_verified_at** | TIMESTAMP | Last verification timestamp |

**Purpose:**
- **EIN**: Primary federal ID for matching Form 5500, DOL violations, IRS data
- **DUNS**: Business credit and vendor management systems
- **CAGE**: Government contracting eligibility
- **email_pattern**: Generate emails for discovered executives without needing 3rd party API

**Index:**
- `idx_company_ein` on (ein)

---

### company_slot (3 columns)

| Column | Type | Purpose |
|--------|------|---------|
| **phone** | VARCHAR(20) | Phone number for this role (not person-specific) |
| **phone_extension** | VARCHAR(10) | Extension |
| **phone_verified_at** | TIMESTAMP | Last verification |

**Philosophy:** Phone numbers belong to **roles**, not people. When a CEO leaves, their phone number stays with the CEO slot. The new CEO gets that number.

**Example:**
- CEO slot at Acme Corp has phone: (555) 123-4567 x100
- John Smith fills CEO slot (phone inherited)
- John leaves, Jane Doe fills CEO slot (same phone inherited)
- Phone moves with role, not person

---

## New Functions (3)

### 1. `marketing.generate_email(first_name, last_name, pattern, domain)`

**Returns:** VARCHAR (generated email)

**Purpose:** Generate email address from detected pattern

**Supported Patterns:**
- `{first}.{last}@` → john.smith@acme.com
- `{f}{last}@` → jsmith@acme.com
- `{first}{last}@` → johnsmith@acme.com
- `{first}{l}@` → johns@acme.com
- `{f}.{last}@` → j.smith@acme.com
- `{first}_{last}@` → john_smith@acme.com
- `{last}.{first}@` → smith.john@acme.com
- `{last}{f}@` → smithj@acme.com
- `{first}@` → john@acme.com
- `{last}@` → smith@acme.com

**Example:**
```sql
SELECT marketing.generate_email('John', 'Smith', '{f}{last}@', 'acme.com');
-- Returns: jsmith@acme.com

-- Generate email for all unfilled CEO slots at companies with known pattern
SELECT
    cs.company_slot_unique_id,
    cs.company_unique_id,
    cm.company_name,
    cm.email_pattern,
    marketing.generate_email('UNKNOWN', 'CEO', cm.email_pattern, cm.website_url) as guessed_ceo_email
FROM marketing.company_slot cs
JOIN marketing.company_master cm ON cm.company_unique_id = cs.company_unique_id
WHERE cs.slot_type = 'CEO'
AND cs.person_unique_id IS NULL
AND cm.email_pattern IS NOT NULL
AND cm.website_url IS NOT NULL;
```

---

### 2. `marketing.match_5500_to_company(sponsor_name, city, state)`

**Returns:** TEXT (company_unique_id or NULL)

**Purpose:** Match Form 5500 sponsor to existing company record

**Matching Logic:**
1. **Exact Match**: `LOWER(company_name) = LOWER(sponsor_name) AND address_state = state`
2. **Fuzzy Match**: `company_name LIKE '%sponsor_name%' AND city = city AND state = state`

**Example:**
```sql
-- Find company for a 5500 filing
SELECT marketing.match_5500_to_company('ACME CORPORATION', 'Pittsburgh', 'PA');
-- Returns: 04.04.01.01.00123.001 (if matched)

-- Match all unmatched 5500 records
UPDATE marketing.form_5500 f
SET company_unique_id = marketing.match_5500_to_company(f.sponsor_name, f.city, f.state)
WHERE company_unique_id IS NULL;
```

---

### 3. `marketing.detect_email_pattern(email, first_name, last_name)`

**Returns:** VARCHAR (detected pattern or NULL)

**Purpose:** Reverse-engineer email pattern from known email address

**Example:**
```sql
SELECT marketing.detect_email_pattern('jsmith@acme.com', 'John', 'Smith');
-- Returns: {f}{last}@

SELECT marketing.detect_email_pattern('john.smith@acme.com', 'John', 'Smith');
-- Returns: {first}.{last}@

-- Detect pattern from all verified emails
SELECT DISTINCT
    cm.company_unique_id,
    cm.company_name,
    marketing.detect_email_pattern(pm.email, pm.first_name, pm.last_name) as pattern,
    COUNT(*) as sample_size
FROM marketing.people_master pm
JOIN marketing.company_master cm ON cm.company_unique_id = pm.company_unique_id
WHERE pm.email IS NOT NULL
AND pm.first_name IS NOT NULL
AND pm.last_name IS NOT NULL
GROUP BY cm.company_unique_id, cm.company_name, pattern
HAVING COUNT(*) >= 2;  -- Only trust pattern if 2+ samples agree
```

---

## New Procedures (2)

### 1. `marketing.process_5500_staging()`

**Purpose:** Process staging table into main form_5500 table

**Logic:**
1. For each record in staging:
   - Try to match to existing company using `match_5500_to_company()`
   - Insert into `form_5500` with matched company_unique_id (or NULL)
   - If matched: Update company with EIN (if company.ein IS NULL)
2. Clear staging table
3. Return count of processed/matched records

**Example:**
```sql
-- Import CSV
COPY marketing.form_5500_staging FROM '/data/5500_2024.csv' CSV HEADER;

-- Process
CALL marketing.process_5500_staging();
-- NOTICE: Processed 1500 records, matched 1200 to existing companies

-- Check unmatched records
SELECT * FROM marketing.form_5500 WHERE company_unique_id IS NULL;
```

---

### 2. `marketing.update_company_email_pattern(company_unique_id, email, first_name, last_name, source)`

**Purpose:** Update company email pattern from verified email

**Logic:**
1. Detect pattern from email using `detect_email_pattern()`
2. Extract domain from email
3. Update company with:
   - email_pattern
   - email_pattern_confidence = 80
   - email_pattern_source
   - email_pattern_verified_at = NOW()
   - website_url = domain (if currently NULL)
4. Only updates if company.email_pattern IS NULL (don't overwrite existing)

**Example:**
```sql
-- After enriching a CEO with email
CALL marketing.update_company_email_pattern(
    '04.04.01.01.00123.001',
    'jsmith@acme.com',
    'John',
    'Smith',
    'apify'
);

-- Company now has:
-- email_pattern = '{f}{last}@'
-- email_pattern_confidence = 80
-- email_pattern_source = 'apify'
-- website_url = 'acme.com' (if was NULL)
```

---

## New Views (2)

### 1. `marketing.v_company_enrichment_status`

**Purpose:** Enrichment completeness score per company (0-100)

**Columns:**
- company_unique_id
- company_name
- address_state
- has_ein (1/0)
- has_email_pattern (1/0)
- has_linkedin (1/0)
- has_website (1/0)
- has_5500 (1/0)
- slots_filled (count)
- slots_with_phone (count)
- **enrichment_score** (0-100)

**Scoring:**
- EIN: 15 points
- Email pattern: 20 points
- LinkedIn: 10 points
- Website: 10 points
- Form 5500: 15 points
- Each filled slot: 10 points (max 30 points for 3 slots)

**Example:**
```sql
-- Companies with lowest enrichment scores
SELECT
    company_name,
    address_state,
    enrichment_score,
    CASE
        WHEN NOT has_ein THEN 'Missing EIN'
        WHEN NOT has_email_pattern THEN 'Missing email pattern'
        WHEN slots_filled < 3 THEN 'Incomplete slots'
        ELSE 'Needs Form 5500'
    END as next_action
FROM marketing.v_company_enrichment_status
WHERE enrichment_score < 50
ORDER BY enrichment_score ASC
LIMIT 20;
```

---

### 2. `marketing.v_companies_need_enrichment`

**Purpose:** Prioritized list of companies needing enrichment

**Columns:**
- company_unique_id
- company_name
- address_state
- next_enrichment_needed (ein, email_pattern, or complete)
- missing_ein (1/0)
- missing_email_pattern (1/0)
- missing_linkedin (1/0)
- missing_website (1/0)

**Ordering:**
1. Missing both EIN and email_pattern
2. Missing EIN only
3. Missing email_pattern only
4. Complete

**Example:**
```sql
-- Get next 10 companies to enrich
SELECT * FROM marketing.v_companies_need_enrichment LIMIT 10;

-- Companies needing EIN (for Form 5500 matching)
SELECT * FROM marketing.v_companies_need_enrichment WHERE missing_ein = 1;

-- Companies ready for email pattern detection (have people, need pattern)
SELECT
    c.*,
    COUNT(p.unique_id) as people_count
FROM marketing.v_companies_need_enrichment c
JOIN marketing.people_master p ON p.company_unique_id = c.company_unique_id
WHERE c.missing_email_pattern = 1
AND p.email IS NOT NULL
GROUP BY c.company_unique_id, c.company_name, c.address_state, c.next_enrichment_needed,
         c.missing_ein, c.missing_email_pattern, c.missing_linkedin, c.missing_website
HAVING COUNT(p.unique_id) >= 2;  -- Need 2+ people to establish pattern
```

---

## Integration Workflows

### Workflow 1: Import Form 5500 Data

**Frequency:** Annual (DOL releases data once per year)

**Steps:**
```sql
-- 1. Download CSV from DOL website
-- https://www.dol.gov/agencies/ebsa/researchers/data/retirement-bulletin

-- 2. Import to staging
COPY marketing.form_5500_staging
FROM '/data/dol/form_5500_2024.csv'
CSV HEADER;

-- 3. Process staging (matches companies, updates EINs)
CALL marketing.process_5500_staging();

-- 4. Review unmatched records
SELECT
    sponsor_name,
    city,
    state,
    participant_count,
    total_assets
FROM marketing.form_5500
WHERE company_unique_id IS NULL
ORDER BY participant_count DESC;

-- 5. Manual matching for high-value unmatched records
UPDATE marketing.form_5500
SET company_unique_id = '04.04.01.01.XXXXX.XXX'
WHERE sponsor_name = 'SPECIFIC COMPANY NAME'
AND state = 'PA'
AND company_unique_id IS NULL;

-- 6. Update company EINs for matched records
UPDATE marketing.company_master cm
SET ein = f.ein
FROM marketing.form_5500 f
WHERE f.company_unique_id = cm.company_unique_id
AND cm.ein IS NULL;
```

**Result:**
- Companies matched to federal EINs
- Employee counts validated
- Retirement plan data available for BIT scoring

---

### Workflow 2: Email Pattern Detection

**Frequency:** Continuous (after each person enrichment)

**Trigger:** After enriching person with email

**Steps:**
```sql
-- After Apify returns CEO email for company_uid = '04.04.01.01.00123.001'
-- Email: jsmith@acme.com
-- Name: John Smith

-- 1. Update person record
UPDATE marketing.people_master
SET
    email = 'jsmith@acme.com',
    email_verified = true,
    email_verification_source = 'apify'
WHERE unique_id = '04.04.02.01.00456.001';

-- 2. Update company email pattern
CALL marketing.update_company_email_pattern(
    '04.04.01.01.00123.001',
    'jsmith@acme.com',
    'John',
    'Smith',
    'apify'
);

-- 3. Generate emails for other unfilled slots at same company
SELECT
    cs.slot_type,
    marketing.generate_email('UNKNOWN', cs.slot_type, cm.email_pattern, cm.website_url) as generated_email
FROM marketing.company_slot cs
JOIN marketing.company_master cm ON cm.company_unique_id = cs.company_unique_id
WHERE cs.company_unique_id = '04.04.01.01.00123.001'
AND cs.person_unique_id IS NULL
AND cm.email_pattern IS NOT NULL;

-- Result:
-- CFO: cfo@acme.com (if pattern was {first}@)
-- HR: hr@acme.com
```

---

### Workflow 3: Enrichment Prioritization

**Frequency:** Daily batch job

**Steps:**
```sql
-- 1. Get companies needing enrichment (prioritized)
SELECT
    company_unique_id,
    company_name,
    next_enrichment_needed,
    enrichment_score
FROM marketing.v_company_enrichment_status
WHERE enrichment_score < 70
ORDER BY
    CASE next_enrichment_needed
        WHEN 'ein' THEN 1
        WHEN 'email_pattern' THEN 2
        ELSE 3
    END,
    employee_count DESC
LIMIT 100;

-- 2. For EIN needed: Search Form 5500 by name/state
SELECT
    f.ein,
    f.sponsor_name,
    f.participant_count
FROM marketing.form_5500 f
WHERE LOWER(f.sponsor_name) LIKE LOWER('%TARGET_COMPANY_NAME%')
AND f.state = 'PA';

-- 3. For email_pattern needed: Trigger Hunter.io API
-- (Hunter.io domain search for domain=company.website_url)

-- 4. For slots needing fill: Trigger Apify LinkedIn search
SELECT
    cs.company_slot_unique_id,
    cs.slot_type,
    cm.company_name,
    cm.linkedin_url
FROM marketing.company_slot cs
JOIN marketing.company_master cm ON cm.company_unique_id = cs.company_unique_id
WHERE cs.person_unique_id IS NULL
AND cm.linkedin_url IS NOT NULL
ORDER BY cm.employee_count DESC
LIMIT 50;
```

---

## Data Sources

### 1. DOL Form 5500

**URL:** https://www.dol.gov/agencies/ebsa/researchers/data/retirement-bulletin

**Format:** CSV (annual release)

**Coverage:** All retirement plans with 100+ participants

**Key Fields:**
- EIN (Employer Identification Number)
- Sponsor name
- Plan participants
- Total assets
- Address

**Use Cases:**
- Match EIN to companies
- Validate employee counts
- Identify companies with retirement plans (BIT signal: HR maturity)
- Track plan participant growth (hiring indicator)

---

### 2. DOL Violations

**URL:** https://www.dol.gov/agencies/ebsa/about-ebsa/our-activities/enforcement

**Format:** HTML (scrape) or API

**Coverage:** ERISA violations and penalties

**Key Fields:**
- EIN
- Violation type
- Penalty amount
- Resolution status

**Use Cases:**
- Compliance risk scoring
- HR leadership instability indicators
- Financial stress signals

---

### 3. Hunter.io

**API:** https://hunter.io/api

**Purpose:** Email pattern detection and verification

**Endpoints:**
- Domain search: Find emails for domain
- Email finder: Find specific person's email
- Email verifier: Verify email deliverability

**Use Cases:**
- Detect company email pattern
- Find executive emails
- Verify generated emails

**Rate Limits:** 50 requests/month (free), 500/month (starter $49)

---

### 4. MillionVerifier

**API:** https://www.millionverifier.com/api

**Purpose:** Email verification at scale

**Use Cases:**
- Bulk verify generated emails
- Check deliverability before outreach
- Reduce bounce rate

**Rate Limits:** Pay per verification ($0.004/email)

---

## Example Queries

### Find companies with multiple retirement plans
```sql
SELECT
    cm.company_unique_id,
    cm.company_name,
    cm.employee_count,
    COUNT(f.id) as plan_count,
    SUM(f.participant_count) as total_participants,
    SUM(f.total_assets) as total_plan_assets
FROM marketing.company_master cm
JOIN marketing.form_5500 f ON f.company_unique_id = cm.company_unique_id
GROUP BY cm.company_unique_id, cm.company_name, cm.employee_count
HAVING COUNT(f.id) > 1
ORDER BY plan_count DESC;
```

### Find companies with DOL violations (high-risk)
```sql
SELECT
    cm.company_unique_id,
    cm.company_name,
    COUNT(v.id) as violation_count,
    SUM(v.penalty_amount) as total_penalties,
    MAX(v.violation_date) as most_recent_violation
FROM marketing.company_master cm
JOIN marketing.dol_violations v ON v.company_unique_id = cm.company_unique_id
WHERE v.resolution_date IS NULL  -- Unresolved violations
GROUP BY cm.company_unique_id, cm.company_name
ORDER BY total_penalties DESC;
```

### Generate emails for all unfilled CEO slots
```sql
SELECT
    cs.company_unique_id,
    cm.company_name,
    cm.email_pattern,
    marketing.generate_email('Unknown', 'CEO', cm.email_pattern, SPLIT_PART(cm.website_url, '//', 2)) as generated_ceo_email
FROM marketing.company_slot cs
JOIN marketing.company_master cm ON cm.company_unique_id = cs.company_unique_id
WHERE cs.slot_type = 'CEO'
AND cs.person_unique_id IS NULL
AND cm.email_pattern IS NOT NULL
AND cm.website_url IS NOT NULL
ORDER BY cm.employee_count DESC;
```

### Email pattern consensus (find reliable patterns)
```sql
WITH pattern_samples AS (
    SELECT
        pm.company_unique_id,
        marketing.detect_email_pattern(pm.email, pm.first_name, pm.last_name) as pattern,
        COUNT(*) as sample_count
    FROM marketing.people_master pm
    WHERE pm.email IS NOT NULL
    AND pm.first_name IS NOT NULL
    AND pm.last_name IS NOT NULL
    GROUP BY pm.company_unique_id, pattern
)
SELECT
    cm.company_unique_id,
    cm.company_name,
    ps.pattern,
    ps.sample_count,
    CASE
        WHEN ps.sample_count >= 3 THEN 'High confidence'
        WHEN ps.sample_count = 2 THEN 'Medium confidence'
        ELSE 'Low confidence'
    END as confidence_level
FROM pattern_samples ps
JOIN marketing.company_master cm ON cm.company_unique_id = ps.company_unique_id
WHERE ps.pattern IS NOT NULL
ORDER BY ps.sample_count DESC, cm.employee_count DESC;
```

### Enrichment queue (prioritized by value)
```sql
SELECT
    cm.company_unique_id,
    cm.company_name,
    cm.employee_count,
    es.enrichment_score,
    es.has_ein,
    es.has_email_pattern,
    es.slots_filled,
    CASE
        WHEN NOT es.has_ein THEN 'Search Form 5500 for EIN'
        WHEN NOT es.has_email_pattern AND es.slots_filled > 0 THEN 'Detect pattern from existing emails'
        WHEN es.slots_filled < 3 THEN 'Enrich slots (Apify LinkedIn)'
        ELSE 'Low priority'
    END as next_action
FROM marketing.v_company_enrichment_status es
JOIN marketing.company_master cm ON cm.company_unique_id = es.company_unique_id
WHERE es.enrichment_score < 80
ORDER BY
    cm.employee_count DESC,  -- Prioritize larger companies
    es.enrichment_score ASC  -- Lowest scores first
LIMIT 50;
```

---

## Next Steps

### Immediate (This Week)

1. ✅ Schema deployed to Neon
2. ✅ Functions and procedures tested
3. ⏳ **Download 2024 Form 5500 data from DOL**
   - URL: https://www.dol.gov/agencies/ebsa/researchers/data/retirement-bulletin
   - Format: CSV
   - Import to `marketing.form_5500_staging`
4. ⏳ **Run `process_5500_staging()` to match companies**
5. ⏳ **Test email pattern detection on existing people**

### Short Term (This Month)

6. Set up Hunter.io API integration for email pattern discovery
7. Set up MillionVerifier for email verification
8. Create Grafana panels:
   - Enrichment score distribution
   - Companies by data source (Form 5500, DOL violations, etc.)
   - Email pattern confidence distribution
9. Create n8n workflow: "Daily Enrichment Queue Processor"

### Long Term (Next Quarter)

10. Integrate additional federal data sources:
    - IRS nonprofit filings (Form 990)
    - SEC filings (10-K, 8-K for public companies)
    - USPTO patent filings (innovation indicator)
11. Build predictive model: "Enrichment ROI Score"
    - Which companies are worth enriching?
    - Which data sources provide highest BIT signal?
12. Automate DOL violation monitoring (scraper + alerts)

---

## Success Metrics

### Data Quality

| Metric | Target | Current |
|--------|--------|---------|
| Companies with EIN | >70% | TBD |
| Companies with email pattern | >50% | TBD |
| Companies with Form 5500 match | >60% | TBD |
| Email pattern confidence (avg) | >75 | TBD |

### Enrichment Coverage

| Metric | Target | Current |
|--------|--------|---------|
| Enrichment score >70 | >80% of companies | TBD |
| Slots with phone | >60% | TBD |
| Companies with federal ID (EIN/DUNS/CAGE) | >70% | TBD |

### Operational

| Metric | Target | Current |
|--------|--------|---------|
| Form 5500 records processed | 1,000+ | 0 |
| DOL violations tracked | 100+ | 0 |
| Email patterns detected | 500+ | 0 |

---

**Status:** ✅ Schema deployed and ready for data import
**Next Action:** Download and import Form 5500 data (2024)
**Owner:** Data Engineering Team

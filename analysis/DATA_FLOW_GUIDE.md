# Executive Enrichment - Data Flow Guide

**Date**: 2025-10-21
**Purpose**: Visual guide to how data moves through the enrichment pipeline

---

## 🗺️ High-Level Data Flow

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  CSV Upload     │ ───▶ │ intake schema   │ ───▶ │ marketing schema│
│  446 companies  │      │ company_raw_    │      │ company_master  │
│                 │      │ intake          │      │ people_master   │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                               │                         │
                               │                         │
                               ▼                         ▼
                         [VALIDATION]              [ENRICHMENT]
                         Check quality             Add executives
```

---

## 📋 Detailed Step-by-Step Process

### Phase 1: CSV Import → intake.company_raw_intake (COMPLETED ✅)

**What Happens:**
1. Upload CSV file with 446 West Virginia companies
2. PostgreSQL assigns sequential IDs (1-446)
3. Data validated and stored in intake schema
4. Timestamps recorded

**Data Format**:
```sql
-- INPUT: CSV Row
company_name, website, linkedin_url, industry, num_employees, city, state
"Concord University", "http://www.concord.edu", "http://www.linkedin.com/school/concorduniversity", "higher education", 500, "Athens", "West Virginia"

-- OUTPUT: Database Row
INSERT INTO intake.company_raw_intake (
  id,                    -- Auto: 1
  company,               -- "Concord University"
  website,               -- "http://www.concord.edu"
  company_linkedin_url,  -- "http://www.linkedin.com/school/concorduniversity"
  industry,              -- "higher education"
  num_employees,         -- 500
  company_city,          -- "Athens"
  company_state,         -- "West Virginia"
  created_at            -- 2025-10-21T...
) VALUES (...);
```

**Result**: 446 rows in `intake.company_raw_intake`

---

### Phase 2: Intake → company_master Promotion (COMPLETED ✅)

**What Happens:**
1. Script reads all rows from `intake.company_raw_intake`
2. Generates Barton IDs for each company
3. Transforms field names (company → company_name, etc.)
4. Inserts into `marketing.company_master`
5. Links via `source_record_id`

**Data Transformation**:
```sql
-- FROM: intake.company_raw_intake
{
  id: 1,
  company: "Concord University",
  website: "http://www.concord.edu",
  num_employees: 500
}

-- TRANSFORM: Generate Barton ID
company_unique_id = '04.04.01.' +
  LPAD((EPOCH % 100), 2, '0') +     -- 84
  '.' +
  LPAD((RANDOM * 100000), 5, '0') + -- 48151
  '.' +
  LPAD((id % 1000), 3, '0')         -- 001

= "04.04.01.84.48151.001"

-- TO: marketing.company_master
{
  company_unique_id: "04.04.01.84.48151.001",
  company_name: "Concord University",
  website_url: "http://www.concord.edu",
  employee_count: 500,
  source_system: "intake_promotion",
  source_record_id: "1",           -- Links back to intake
  promoted_from_intake_at: "2025-10-21T19:51:23.668Z"
}
```

**Field Mapping**:
| Before (intake) | After (marketing) | Notes |
|----------------|-------------------|-------|
| `id` | `source_record_id` | Tracking link |
| `company` | `company_name` | Renamed |
| `website` | `website_url` | Renamed |
| `num_employees` | `employee_count` | Renamed |
| N/A | `company_unique_id` | **GENERATED**: Barton ID |
| N/A | `source_system` | **STATIC**: "intake_promotion" |

**Result**: 446 rows in `marketing.company_master` with Barton IDs

---

### Phase 3: Enrichment Preparation (NEXT STEP ⏳)

**What Happens:**
1. Select companies from `company_master` for enrichment
2. Extract clean domains from website URLs
3. Prepare Apify API call

**Domain Extraction**:
```javascript
// FROM: website_url
"http://www.advantage.tech"

// EXTRACT: Clean domain
function extractDomain(url) {
  const parsed = new URL(url);
  return parsed.hostname.replace('www.', '');
}

// TO: domain
"advantage.tech"
```

**SQL Query for Trial**:
```sql
-- Select 3 companies for trial enrichment
SELECT
  company_unique_id,
  company_name,
  website_url,
  industry,
  employee_count
FROM marketing.company_master
WHERE website_url IS NOT NULL
  AND website_url != 'https://example.com'
ORDER BY employee_count DESC
LIMIT 3;

-- Results:
-- 1. Advantage Technology (advantage.tech)
-- 2. Valley Health Systems (valleyhealth.org)
-- 3. TMC Technologies (tmctechnologies.com)
```

---

### Phase 4: Apify Leads Finder Call (NEXT STEP ⏳)

**What Happens:**
1. Send company domains to Apify via Composio
2. Apify searches LinkedIn and other sources
3. Returns executive contact information
4. Filters for target roles (CEO, CFO, CHRO, CTO)

**API Call**:
```javascript
POST https://backend.composio.dev/api/v2/actions/APIFY_RUN_ACTOR_SYNC_GET_DATASET_ITEMS/execute

Headers:
  X-API-Key: ak_t-F0AbvfZHUZSUrqAGNn
  Content-Type: application/json

Body:
{
  "connectedAccountId": "f81a8a4a-c602-4adf-be02-fadec17cc378",
  "appName": "apify",
  "input": {
    "actorId": "code_crafter~leads-finder",
    "runInput": {
      "company_domain": [
        "advantage.tech",
        "valleyhealth.org",
        "tmctechnologies.com"
      ],
      "contact_job_title": [
        "CEO",
        "Chief Executive Officer",
        "President",
        "CFO",
        "Chief Financial Officer",
        "CHRO",
        "Chief Human Resources Officer",
        "HR Director",
        "CTO",
        "Chief Technology Officer"
      ],
      "contact_seniority": ["c-suite", "vp"],
      "contact_location": ["united states"],
      "contact_state": ["west virginia, us"],
      "max_leads": 15
    },
    "timeout": 300
  }
}
```

**Response Example**:
```json
{
  "success": true,
  "data": {
    "executionId": "exec_abc123",
    "items": [
      {
        "firstName": "Jane",
        "lastName": "Doe",
        "title": "CEO",
        "seniority": "c-suite",
        "email": "jane.doe@advantage.tech",
        "phone": "+1-304-555-0100",
        "linkedin_url": "https://linkedin.com/in/janedoe",
        "company_name": "Advantage Technology",
        "company_domain": "advantage.tech",
        "company_industry": "information technology & services",
        "location": "Charleston, West Virginia, United States"
      },
      {
        "firstName": "John",
        "lastName": "Smith",
        "title": "CFO",
        "seniority": "c-suite",
        "email": "john.smith@advantage.tech",
        "linkedin_url": "https://linkedin.com/in/johnsmith",
        "company_domain": "advantage.tech"
      },
      // ... more executives
    ]
  }
}
```

**Filtering Logic**:
```javascript
const executives = response.data.items.filter(person => {
  const title = person.title?.toLowerCase() || '';

  return (
    // CEO
    title.includes('ceo') ||
    title.includes('chief executive') ||
    title.includes('president') ||

    // CFO
    title.includes('cfo') ||
    title.includes('chief financial') ||

    // CHRO
    title.includes('chro') ||
    title.includes('hr director') ||
    title.includes('human resources') ||

    // CTO
    title.includes('cto') ||
    title.includes('chief technology')
  ) &&

  // Only c-suite and VP level
  (person.seniority === 'c-suite' || person.seniority === 'vp');
});
```

---

### Phase 5: Company Matching (NEXT STEP ⏳)

**What Happens:**
1. For each executive from Apify
2. Match their `company_domain` to a company in `company_master`
3. Get the company's `company_unique_id` for linking

**Matching Query**:
```sql
-- For executive with company_domain: "advantage.tech"
SELECT
  company_unique_id,
  company_name,
  website_url
FROM marketing.company_master
WHERE website_url ILIKE '%advantage.tech%'
LIMIT 1;

-- Result:
{
  company_unique_id: "04.04.01.84.33265.002",
  company_name: "Advantage Technology",
  website_url: "http://www.advantage.tech"
}
```

**JavaScript Implementation**:
```javascript
async function matchCompanyByDomain(apifyExec) {
  const domain = apifyExec.company_domain;

  const result = await query(`
    SELECT company_unique_id, company_name
    FROM marketing.company_master
    WHERE website_url ILIKE $1
    LIMIT 1
  `, [`%${domain}%`]);

  if (result.rows.length === 0) {
    console.error(`No match for domain: ${domain}`);
    return null;
  }

  return result.rows[0].company_unique_id;
}
```

---

### Phase 6: Barton ID Generation for Executives (NEXT STEP ⏳)

**What Happens:**
1. For each executive to be inserted
2. Generate a unique Barton ID in format `04.04.02.XX.XXXXX.XXX`
3. Use sequential counter for last 3 digits

**ID Generation**:
```sql
-- For executive #1 (sequence = 1)
unique_id = '04.04.02.' +                      -- Table: people_master
  LPAD((EPOCH % 100)::TEXT, 2, '0') +         -- Timestamp segment: 85
  '.' +
  LPAD((RANDOM() * 100000)::INT::TEXT, 5, '0') + -- Random: 12345
  '.' +
  LPAD((sequence % 1000)::TEXT, 3, '0')       -- Sequence: 001

= "04.04.02.85.12345.001"

-- For executive #2 (sequence = 2)
= "04.04.02.85.67890.002"

-- For executive #3 (sequence = 3)
= "04.04.02.85.11111.003"
```

---

### Phase 7: INSERT into people_master (NEXT STEP ⏳)

**What Happens:**
1. For each filtered executive
2. Generate Barton ID
3. Link to company via `company_unique_id`
4. Handle `company_slot_unique_id` ⚠️ (BLOCKER)
5. Insert into `marketing.people_master`

**INSERT Statement**:
```sql
INSERT INTO marketing.people_master (
  unique_id,                    -- Generated: "04.04.02.85.12345.001"
  company_unique_id,            -- Matched: "04.04.01.84.33265.002"
  company_slot_unique_id,       -- TBD: Need to handle ⚠️
  first_name,                   -- From Apify: "Jane"
  last_name,                    -- From Apify: "Doe"
  -- full_name auto-generated  -- "Jane Doe"
  title,                        -- From Apify: "CEO"
  seniority,                    -- From Apify: "c-suite"
  department,                   -- Inferred: "Executive"
  email,                        -- From Apify: "jane.doe@advantage.tech"
  work_phone_e164,             -- Formatted: "+1-304-555-0100"
  linkedin_url,                 -- From Apify: "https://linkedin.com/in/janedoe"
  source_system,                -- Static: "apify_leads_finder"
  source_record_id,             -- Apify run ID: "exec_abc123"
  promoted_from_intake_at,      -- NOW()
  created_at,                   -- NOW()
  updated_at                    -- NOW()
) VALUES (
  '04.04.02.85.12345.001',
  '04.04.01.84.33265.002',
  '04.04.05.XX.XXXXX.XXX',     -- ⚠️ PLACEHOLDER
  'Jane',
  'Doe',
  'CEO',
  'c-suite',
  'Executive',
  'jane.doe@advantage.tech',
  '+1-304-555-0100',
  'https://linkedin.com/in/janedoe',
  'apify_leads_finder',
  'exec_abc123',
  NOW(),
  NOW(),
  NOW()
);
```

**Complete Flow for One Executive**:
```
Apify Response
     ↓
{ firstName: "Jane", lastName: "Doe", company_domain: "advantage.tech", ... }
     ↓
[Match Company]
     ↓
SELECT company_unique_id WHERE website LIKE '%advantage.tech%'
     ↓
company_unique_id = "04.04.01.84.33265.002"
     ↓
[Generate Barton ID]
     ↓
unique_id = "04.04.02.85.12345.001"
     ↓
[Handle Slot ID] ⚠️
     ↓
company_slot_unique_id = "04.04.05.XX.XXXXX.XXX" (TBD)
     ↓
[INSERT]
     ↓
marketing.people_master row created ✅
```

---

### Phase 8: Data Verification (NEXT STEP ⏳)

**What Happens:**
1. Query `people_master` for statistics
2. Verify data quality (email format, LinkedIn URLs)
3. Check company linkage
4. Generate summary report

**Verification Queries**:

```sql
-- 1. Count executives by role
SELECT
  COUNT(*) as total_executives,
  COUNT(DISTINCT company_unique_id) as companies_with_executives,
  COUNT(*) FILTER (WHERE title ILIKE '%ceo%') as ceos,
  COUNT(*) FILTER (WHERE title ILIKE '%cfo%') as cfos,
  COUNT(*) FILTER (WHERE title ILIKE '%chro%' OR title ILIKE '%hr%') as chros,
  COUNT(*) FILTER (WHERE title ILIKE '%cto%') as ctos
FROM marketing.people_master;

-- Expected Result:
-- total_executives: 12
-- companies_with_executives: 3
-- ceos: 3
-- cfos: 3
-- chros: 2
-- ctos: 4
```

```sql
-- 2. Data quality metrics
SELECT
  COUNT(*) as total,
  COUNT(email) as with_email,
  ROUND(COUNT(email)::DECIMAL / COUNT(*) * 100, 2) as email_coverage_pct,
  COUNT(linkedin_url) as with_linkedin,
  ROUND(COUNT(linkedin_url)::DECIMAL / COUNT(*) * 100, 2) as linkedin_coverage_pct,
  COUNT(work_phone_e164) as with_phone,
  ROUND(COUNT(work_phone_e164)::DECIMAL / COUNT(*) * 100, 2) as phone_coverage_pct
FROM marketing.people_master;

-- Expected Result:
-- total: 12
-- with_email: 11
-- email_coverage_pct: 91.67%
-- with_linkedin: 12
-- linkedin_coverage_pct: 100%
-- with_phone: 8
-- phone_coverage_pct: 66.67%
```

```sql
-- 3. Verify company linkage
SELECT
  pm.unique_id,
  pm.full_name,
  pm.title,
  pm.email,
  cm.company_name,
  cm.website_url,
  cm.company_unique_id
FROM marketing.people_master pm
JOIN marketing.company_master cm
  ON pm.company_unique_id = cm.company_unique_id
ORDER BY cm.company_name, pm.title;

-- Verify all executives link correctly to companies
```

```sql
-- 4. Check for duplicates
SELECT
  company_unique_id,
  title,
  COUNT(*) as count
FROM marketing.people_master
GROUP BY company_unique_id, title
HAVING COUNT(*) > 1;

-- Should return 0 rows (no duplicate CEO/CFO per company)
```

---

## 🔄 Complete Data Journey

### Visual Representation

```
┌──────────────────────────────────────────────────────────────────┐
│                        CSV IMPORT                                 │
│  File: west_virginia_companies.csv                               │
│  Rows: 446                                                        │
└──────────┬───────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│              intake.company_raw_intake                            │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ id: 1                                                       │  │
│  │ company: "Concord University"                              │  │
│  │ website: "http://www.concord.edu"                          │  │
│  │ num_employees: 500                                          │  │
│  │ company_state: "West Virginia"                             │  │
│  └────────────────────────────────────────────────────────────┘  │
│  Total: 446 rows                                                  │
└──────────┬───────────────────────────────────────────────────────┘
           │
           │ [PROMOTION SCRIPT]
           │ - Generate Barton IDs
           │ - Transform field names
           │ - Link via source_record_id
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│            marketing.company_master                               │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ company_unique_id: "04.04.01.84.48151.001"                │  │
│  │ company_name: "Concord University"                         │  │
│  │ website_url: "http://www.concord.edu"                      │  │
│  │ employee_count: 500                                         │  │
│  │ source_record_id: "1" ─────────┐                          │  │
│  │ source_system: "intake_promotion"                          │  │
│  └────────────────────────────────┼───────────────────────────┘  │
│  Total: 446 rows                  │                               │
└───────────────────────────────────┼───────────────────────────────┘
                                    │
                                    │ LINKS BACK TO
                                    │
                ┌───────────────────┘
                │
                ▼
       [SOURCE TRACKING]
    intake.id → company_master.source_record_id
                │
                │
                ▼
┌──────────────────────────────────────────────────────────────────┐
│                 ENRICHMENT PHASE                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ 1. SELECT companies from company_master                   │    │
│  │ 2. Extract domains: "advantage.tech"                     │    │
│  │ 3. Call Apify via Composio                               │    │
│  │ 4. Receive executives: Jane Doe, CEO                     │    │
│  │ 5. Match domain → company_unique_id                       │    │
│  │ 6. Generate Barton ID for executive                      │    │
│  │ 7. INSERT into people_master                             │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────┬───────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│            marketing.people_master                                │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ unique_id: "04.04.02.85.12345.001"                        │  │
│  │ company_unique_id: "04.04.01.84.48151.001" ──┐            │  │
│  │ first_name: "Jane"                            │            │  │
│  │ last_name: "Doe"                              │            │  │
│  │ full_name: "Jane Doe" (auto-generated)        │            │  │
│  │ title: "CEO"                                   │            │  │
│  │ email: "jane.doe@company.com"                 │            │  │
│  │ linkedin_url: "linkedin.com/in/janedoe"       │            │  │
│  │ source_system: "apify_leads_finder"           │            │  │
│  └───────────────────────────────────────────────┼────────────┘  │
│  Total: 0 → 1500-2500 expected                   │                │
└──────────────────────────────────────────────────┼────────────────┘
                                                    │
                                                    │ LINKS TO
                                                    │
                        ┌───────────────────────────┘
                        │
                        ▼
              [FOREIGN KEY RELATIONSHIP]
          people_master.company_unique_id
                        │
                        ▼
          company_master.company_unique_id
```

---

## 🎯 Data Capture Summary

### What We Have (From Intake)
✅ 446 West Virginia companies
✅ 99% have websites
✅ 95% have LinkedIn pages
✅ 100% have location data
✅ All promoted to company_master with Barton IDs

### What We're About to Get (From Enrichment)
⏳ 1,500-2,500 executives across 446 companies
⏳ CEO, CFO, CHRO, CTO for each company
⏳ Email addresses (expected 80%+ coverage)
⏳ LinkedIn profiles (expected 90%+ coverage)
⏳ Phone numbers (expected 50%+ coverage)

### What's Missing (Gaps)
❌ Company financial data (revenue, funding)
❌ Company tech stack
❌ Executive photos
❌ Executive start dates
❌ Executive work history
❌ Outreach tracking (contacted, responded)

---

## ⚠️ Current Blocker

**Issue**: `marketing.people_master.company_slot_unique_id` is NOT NULL

**Impact**: Cannot insert executives without a valid slot ID

**Solutions**:

**Option A: Generate Default Slots** (RECOMMENDED)
```sql
-- Generate one slot per company
INSERT INTO marketing.company_slots (
  slot_unique_id,
  company_unique_id,
  slot_type,
  created_at
)
SELECT
  '04.04.05.' ||
    LPAD((EXTRACT(EPOCH FROM NOW())::BIGINT % 100)::TEXT, 2, '0') || '.' ||
    LPAD((RANDOM() * 100000)::INT::TEXT, 5, '0') || '.' ||
    LPAD((ROW_NUMBER() OVER())::TEXT, 3, '0'),
  company_unique_id,
  'default',
  NOW()
FROM marketing.company_master;
```

**Option B: Relax Constraint** (QUICK FIX)
```sql
ALTER TABLE marketing.people_master
ALTER COLUMN company_slot_unique_id DROP NOT NULL;
```

**Option C: Use Placeholder** (TEMPORARY)
```sql
-- Use a static placeholder for trial
company_slot_unique_id = '04.04.05.00.00000.000'
```

---

## 📈 Expected Results After Trial

### Trial Parameters
- **Companies**: 3 (Advantage Technology, Valley Health, TMC Technologies)
- **Expected Executives**: 10-15
- **Cost**: ~$0.08
- **Time**: 5-10 minutes

### Expected Data in people_master
```sql
-- After trial enrichment
SELECT COUNT(*) FROM marketing.people_master;
-- Expected: 12-15 rows

SELECT
  cm.company_name,
  COUNT(pm.unique_id) as exec_count,
  STRING_AGG(pm.title, ', ') as roles
FROM marketing.people_master pm
JOIN marketing.company_master cm
  ON pm.company_unique_id = cm.company_unique_id
GROUP BY cm.company_name;

-- Expected Result:
-- Advantage Technology | 4 | CEO, CFO, CTO, VP Engineering
-- Valley Health Systems | 5 | CEO, CFO, CHRO, HR Director, VP HR
-- TMC Technologies | 4 | CEO, CFO, CTO, VP Operations
```

---

**Next Action**: Resolve `company_slot_unique_id` blocker to proceed with enrichment trial

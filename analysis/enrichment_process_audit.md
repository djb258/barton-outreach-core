# Executive Enrichment Process Audit Report

**Generated**: 2025-10-21
**Audit Scope**: Executive enrichment workflow verification before trial run
**Auditor**: Claude Code (Barton Doctrine Compliance)

---

## Executive Summary

🚨 **STATUS**: **MAJOR SCHEMA GAPS DETECTED** - DO NOT PROCEED WITHOUT FIXES

### Critical Findings:
1. ❌ **Schema Mismatch**: `marketing.company_master` missing ALL executive enrichment fields
2. ✅ **Apify Actor**: `code_crafter~leads-finder` verified and accessible
3. ⚠️ **Architecture**: People stored in separate `marketing.people_master` table (normalized design)
4. ❌ **No Active Enrichment Task**: No YAML/config file defining executive enrichment workflow
5. ✅ **Composio Integration**: Working (API v2, account connected)

**Recommendation**: ALTER `marketing.company_master` OR create executive enrichment workflow that populates `marketing.people_master` linked to companies.

---

## 1. Active Enrichment Task Configuration

### Files Searched:
```
**/*enrich*.{yaml,yml,json,js,ts}
**/*apify*.{yaml,yml,json,js,ts}
**/*executive*.{yaml,yml,json,js,ts}
```

### Results:

✅ **Found Enrichment Logic Files**:
- `apps/outreach-process-manager/api/enrichment.js` - Step 2B enrichment router
- `apps/outreach-process-manager/services/enrichmentRouter.js` - Main orchestrator
- `apps/outreach-process-manager/services/apifyHandler.js` - Apify integration handler
- `agents/specialists/apifyRunner.js` - Apify actor runner with Barton Doctrine

❌ **NOT FOUND**:
- `enrich_wv_trial.yaml` - Does not exist
- `apify_executive_enrichment.yaml` - Does not exist
- Any YAML config files defining executive enrichment workflow

### Current Active Process:

**File**: `apps/outreach-process-manager/api/enrichment.js`

**Process Name**: Enrichment Router API - Step 2B

**Purpose**: Handles batch processing of **validation failures** (NOT executive enrichment)

**Key Parameters**:
```javascript
{
  action: 'process_batch',
  batchSize: 50,
  schemas: ['intake'],
  maxRetries: 3,
  handlerTimeout: 30000,
  priorityLevel: 'normal'
}
```

**Handler Pipeline**:
1. `auto_fix` - Fast automated fixes
2. `apify` - Web scraping for missing data
3. `abacus` - Complex case escalation
4. `human` - Manual review queue

**Error Types Handled by Apify**:
- `missing_linkedin`
- `invalid_linkedin`
- `missing_website`
- `website_not_found`
- `missing_ein`
- `missing_tax_id`
- `missing_permit`
- `missing_license`
- `missing_revenue`
- `missing_financial_data`

**Apify Actors Used (Currently Mock/Simulated)**:
- `linkedin-company-scraper`
- `website-content-crawler`
- `company-data-scraper`
- `business-permit-scraper`
- `financial-data-scraper`

❌ **CRITICAL**: No actor for executive enrichment (CEO/CFO/HR discovery)

---

## 2. Neon Database Schema Audit

### Connection Details:
- **Database URL**: `postgresql://Marketing%20DB_owner:***@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/Marketing%20DB`
- **Schema**: `marketing`
- **Primary Tables**: `company_master`, `people_master`

### 2.1 Company Master Table

**Table**: `marketing.company_master`

**Existing Columns**:
```sql
-- Core Fields
company_unique_id        TEXT PRIMARY KEY
company_name             TEXT NOT NULL
website_url              TEXT NOT NULL
industry                 TEXT
employee_count           INTEGER

-- Contact & Location
company_phone            TEXT
address_street           TEXT
address_city             TEXT
address_state            TEXT
address_zip              TEXT
address_country          TEXT

-- Social & Web
linkedin_url             TEXT
facebook_url             TEXT
twitter_url              TEXT

-- Business Data
sic_codes                TEXT
founded_year             INTEGER
keywords                 TEXT[]
description              TEXT

-- Metadata
source_system            TEXT NOT NULL
source_record_id         TEXT
promoted_from_intake_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
promotion_audit_log_id   INTEGER
created_at               TIMESTAMPTZ DEFAULT NOW()
updated_at               TIMESTAMPTZ DEFAULT NOW()
```

### ❌ MISSING COLUMNS FOR EXECUTIVE ENRICHMENT:

```sql
-- CEO Fields (NOT IN SCHEMA)
ceo_name                TEXT
ceo_email               TEXT
ceo_linkedin            TEXT
ceo_phone               TEXT

-- CFO Fields (NOT IN SCHEMA)
cfo_name                TEXT
cfo_email               TEXT
cfo_linkedin            TEXT
cfo_phone               TEXT

-- CHRO/HR Fields (NOT IN SCHEMA)
hr_name                 TEXT
hr_email                TEXT
hr_linkedin             TEXT
hr_phone                TEXT
chro_name               TEXT
chro_email              TEXT

-- Enrichment Tracking (NOT IN SCHEMA)
enrichment_status       TEXT
enrichment_source       TEXT
last_enriched           TIMESTAMPTZ
executive_data_quality  NUMERIC
enrichment_attempts     INTEGER
```

### 2.2 People Master Table

**Table**: `marketing.people_master`

**Existing Columns** (THESE CAN STORE EXECUTIVES):
```sql
-- Identity
unique_id                TEXT PRIMARY KEY  -- Person Barton ID
company_unique_id        TEXT NOT NULL      -- Links to company
company_slot_unique_id   TEXT NOT NULL

-- Name
first_name               TEXT NOT NULL
last_name                TEXT NOT NULL
full_name                TEXT (GENERATED)

-- Professional
title                    TEXT  ✅ Can store "CEO", "CFO", "CHRO"
seniority                TEXT  ✅ Can store "c-suite"
department               TEXT

-- Contact
email                    TEXT  ✅ Can store executive emails
work_phone_e164          TEXT
personal_phone_e164      TEXT

-- Social
linkedin_url             TEXT  ✅ Can store executive LinkedIn
twitter_url              TEXT
facebook_url             TEXT

-- Additional
bio                      TEXT
skills                   TEXT[]
education                TEXT
certifications           TEXT[]

-- Metadata
source_system            TEXT NOT NULL
source_record_id         TEXT
promoted_from_intake_at  TIMESTAMPTZ
promotion_audit_log_id   INTEGER
created_at               TIMESTAMPTZ
updated_at               TIMESTAMPTZ
```

### ✅ Schema Assessment:

**Option 1: Denormalized (company_master with executive columns)**
- ❌ NOT IMPLEMENTED
- ❌ Requires ALTER TABLE statements
- ⚠️ Limited to 1 executive per role (CEO, CFO, HR)

**Option 2: Normalized (people_master with role filtering)** ✅ CURRENT DESIGN
- ✅ SCHEMA EXISTS
- ✅ Supports multiple executives per company
- ✅ Clean relational design
- ✅ Follows Barton Doctrine

---

## 3. Required ALTER TABLE Statements

### If Using Denormalized Approach (Option 1):

```sql
-- Add CEO fields to company_master
ALTER TABLE marketing.company_master
ADD COLUMN ceo_name TEXT,
ADD COLUMN ceo_email TEXT,
ADD COLUMN ceo_linkedin TEXT,
ADD COLUMN ceo_phone TEXT,
ADD COLUMN ceo_title TEXT;

-- Add CFO fields
ALTER TABLE marketing.company_master
ADD COLUMN cfo_name TEXT,
ADD COLUMN cfo_email TEXT,
ADD COLUMN cfo_linkedin TEXT,
ADD COLUMN cfo_phone TEXT,
ADD COLUMN cfo_title TEXT;

-- Add HR/CHRO fields
ALTER TABLE marketing.company_master
ADD COLUMN chro_name TEXT,
ADD COLUMN chro_email TEXT,
ADD COLUMN chro_linkedin TEXT,
ADD COLUMN chro_phone TEXT,
ADD COLUMN hr_director_name TEXT,
ADD COLUMN hr_director_email TEXT,
ADD COLUMN hr_director_linkedin TEXT;

-- Add enrichment tracking
ALTER TABLE marketing.company_master
ADD COLUMN enrichment_status TEXT DEFAULT 'pending',
ADD COLUMN enrichment_source TEXT,
ADD COLUMN last_enriched TIMESTAMPTZ,
ADD COLUMN executive_data_quality NUMERIC(3,2),
ADD COLUMN enrichment_attempts INTEGER DEFAULT 0;

-- Add constraints
ALTER TABLE marketing.company_master
ADD CONSTRAINT chk_enrichment_status
CHECK (enrichment_status IN ('pending', 'in_progress', 'completed', 'failed', 'partial'));

-- Add indexes
CREATE INDEX idx_company_master_enrichment_status
ON marketing.company_master(enrichment_status);

CREATE INDEX idx_company_master_last_enriched
ON marketing.company_master(last_enriched);
```

**Pros**:
- Fast queries (single table)
- Simple denormalized structure
- Easy reporting

**Cons**:
- Limited to 1 person per role
- Schema bloat
- Harder to update/maintain

---

### If Using Normalized Approach (Option 2): ✅ RECOMMENDED

**NO ALTER STATEMENTS NEEDED** - Schema already supports this!

**Implementation**:
1. Run Apify `code_crafter~leads-finder` for each company
2. Filter results by title/seniority for executives
3. Insert into `marketing.people_master` with `company_unique_id` link
4. Query by joining `company_master` and `people_master` on `company_unique_id`

**Example Query**:
```sql
SELECT
    cm.company_unique_id,
    cm.company_name,
    cm.industry,
    pm.unique_id as person_id,
    pm.full_name,
    pm.title,
    pm.seniority,
    pm.email,
    pm.linkedin_url,
    pm.work_phone_e164
FROM marketing.company_master cm
LEFT JOIN marketing.people_master pm
    ON cm.company_unique_id = pm.company_unique_id
WHERE pm.seniority = 'c-suite'
  AND pm.title IN ('CEO', 'Chief Executive Officer', 'CFO', 'Chief Financial Officer', 'CHRO', 'Chief Human Resources Officer')
ORDER BY cm.company_name, pm.title;
```

**Pros**:
- ✅ Already implemented
- ✅ Supports unlimited executives
- ✅ Clean normalized design
- ✅ Follows Barton Doctrine

**Cons**:
- Requires JOIN for queries
- Slightly more complex queries

---

## 4. Apify Actor Integration Validation

### 4.1 Apify Account Status

✅ **Composio Connection**: Active
✅ **API Version**: v2 (`https://backend.composio.dev/api/v2`)
✅ **Connected Account ID**: `f81a8a4a-c602-4adf-be02-fadec17cc378`
✅ **Apify Account**: Verified

### 4.2 Actor: `code_crafter~leads-finder`

**Actor ID**: `IoSHqwTR9YGhzccez`
**Status**: ✅ Active
**Title**: "✨Leads Finder - $1.5/1k leads with Emails [Apollo Alternative]"
**Last Run**: 2025-10-21T19:21:06.811Z (VERY RECENT)
**Total Runs**: 20,487
**Success Rate**: 68.60% (14,236 succeeded / 20,751 total in last 30 days)

### 4.3 Input Schema

**Required Input Parameters**:

```json
{
  "company_industry": [
    "information technology & services",
    "financial services",
    "healthcare"
  ],
  "contact_job_title": [
    "CEO", "Chief Executive Officer",
    "CFO", "Chief Financial Officer",
    "CHRO", "Chief Human Resources Officer"
  ],
  "contact_seniority": [
    "c-suite", "vp"
  ],
  "contact_location": [
    "united states"
  ],
  "max_leads": 500
}
```

**Supported Seniority Levels**:
- ✅ `c-suite` - Perfect for CEO/CFO/CHRO
- `vp` - Vice President level
- `director` - Director level
- `manager` - Manager level
- `senior` - Senior level
- `entry` - Entry level

**Supported Industries**: 140+ options

**Supported Locations**: 200+ countries + US states

### 4.4 Output Schema

**Fields Returned**:
- ✅ `email` - Business email (and personal when available)
- ✅ `name` / `full_name` - Contact full name
- ✅ `firstName`, `lastName` - Name components
- ✅ `title` / `jobTitle` - Job title (e.g., "CEO", "CFO")
- ✅ `seniority` - Seniority level (e.g., "c-suite")
- ✅ `linkedin_url` - LinkedIn profile URL
- ✅ `company_name` - Company name
- ✅ `company_domain` - Company website
- ✅ `company_industry` - Industry
- ✅ `location` - Geographic location

### 4.5 Pricing

- **Actor Start**: $0.02 per run
- **Lead Fetched**: $0.0015-$0.002 per lead
- **Example**: 500 leads = $0.02 + (500 × $0.0015) = **$0.77 total**

---

## 5. Output Mapping to Neon Schema

### 5.1 Apify Output → `people_master` Mapping

| Apify Field | Neon Column | Type | Notes |
|-------------|-------------|------|-------|
| `name` / `full_name` | N/A | TEXT | Use firstName + lastName instead |
| `firstName` | `first_name` | TEXT | ✅ Direct mapping |
| `lastName` | `last_name` | TEXT | ✅ Direct mapping |
| `title` / `jobTitle` | `title` | TEXT | ✅ Direct mapping |
| `seniority` | `seniority` | TEXT | ✅ Direct mapping |
| `email` | `email` | TEXT | ✅ Direct mapping |
| `linkedin_url` | `linkedin_url` | TEXT | ✅ Direct mapping |
| `phone` (if returned) | `work_phone_e164` | TEXT | ⚠️ May need E.164 formatting |
| `company_name` | N/A | TEXT | Used for linking to company_unique_id |
| `company_domain` | N/A | TEXT | Used for company matching |
| `company_industry` | N/A | TEXT | Validation field |
| `location` | N/A | TEXT | Could add to people_master if needed |

### 5.2 Required Fields for `people_master` Insert

```javascript
{
  // Generated
  unique_id: generateBartonId('04.04.02'),  // Person Barton ID
  company_unique_id: '<linked_company_barton_id>',  // FROM company_master
  company_slot_unique_id: '<slot_barton_id>',  // FROM company_slot lookup

  // From Apify
  first_name: apifyResult.firstName,
  last_name: apifyResult.lastName,
  title: apifyResult.title || apifyResult.jobTitle,
  seniority: apifyResult.seniority,
  email: apifyResult.email,
  work_phone_e164: formatE164(apifyResult.phone),  // If provided
  linkedin_url: apifyResult.linkedin_url,

  // Metadata
  source_system: 'apify_leads_finder',
  source_record_id: apifyResult.id || apifyRunId,
  promoted_from_intake_at: NOW(),
  created_at: NOW(),
  updated_at: NOW()
}
```

### 5.3 Gaps & Conflicts

❌ **Gap 1**: `company_unique_id` lookup
- **Issue**: Apify returns company_name/company_domain, NOT Barton ID
- **Solution**: Match on `website_url` or `company_name` in `company_master`

❌ **Gap 2**: `company_slot_unique_id` requirement
- **Issue**: `people_master` requires slot ID, but unclear what this represents
- **Solution**: Either create default slot OR remove NOT NULL constraint

⚠️ **Gap 3**: Phone number formatting
- **Issue**: Apify may return unformatted phone numbers
- **Solution**: Implement E.164 formatting function

---

## 6. Recommended Workflow

### Phase 1: Preparation

```sql
-- Option A: If using denormalized approach
-- Run all ALTER TABLE statements from Section 3

-- Option B: If using normalized approach (RECOMMENDED)
-- Optionally relax company_slot_unique_id constraint
ALTER TABLE marketing.people_master
ALTER COLUMN company_slot_unique_id DROP NOT NULL;
```

### Phase 2: Executive Enrichment Process

**File**: Create `apps/outreach-process-manager/services/executiveEnrichmentService.js`

**Process**:
```javascript
async function enrichCompanyExecutives(companyUniqueId, companyData) {
  // 1. Call Apify leads-finder via Composio
  const executives = await fetch('https://backend.composio.dev/api/v2/actions/APIFY_RUN_ACTOR_SYNC_GET_DATASET_ITEMS/execute', {
    method: 'POST',
    headers: {
      'X-API-Key': COMPOSIO_API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      connectedAccountId: 'f81a8a4a-c602-4adf-be02-fadec17cc378',
      appName: 'apify',
      input: {
        actorId: 'code_crafter~leads-finder',
        runInput: {
          company_domain: [companyData.website_url],
          contact_job_title: [
            'CEO', 'Chief Executive Officer',
            'CFO', 'Chief Financial Officer',
            'CHRO', 'Chief Human Resources Officer',
            'HR Director'
          ],
          contact_seniority: ['c-suite', 'vp'],
          max_leads: 10
        },
        timeout: 300
      }
    })
  });

  // 2. Filter results for executives
  const filteredExecs = filterExecutives(executives.data.items);

  // 3. Insert into people_master
  for (const exec of filteredExecs) {
    await insertIntoPeopleMaster({
      company_unique_id: companyUniqueId,
      first_name: exec.firstName,
      last_name: exec.lastName,
      title: exec.title,
      seniority: exec.seniority,
      email: exec.email,
      linkedin_url: exec.linkedin_url
    });
  }

  // 4. Update enrichment tracking
  if (denormalized) {
    await updateCompanyMaster(companyUniqueId, {
      enrichment_status: 'completed',
      enrichment_source: 'apify_leads_finder',
      last_enriched: NOW()
    });
  }
}
```

### Phase 3: Trial Run

```javascript
// Test with 1 company
const testCompany = {
  company_unique_id: '04.04.01.XX.XXXXX.XXX',
  company_name: 'Test Company Inc',
  website_url: 'https://testcompany.com',
  industry: 'information technology & services'
};

await enrichCompanyExecutives(testCompany.company_unique_id, testCompany);
```

---

## 7. Current Actor Configuration vs Required

### In Code: `agents/specialists/apifyRunner.js`

**Current Actor**: `apify/email-phone-scraper` (line 18)
**Status**: ❌ HTTP 404 (doesn't exist)

**Current Process**:
- Scrapes contact emails from company domains
- Stores in `marketing.contact_verification` table
- NOT designed for executive enrichment

### Required Configuration:

**Actor**: `code_crafter~leads-finder` ✅
**Purpose**: Executive lead generation with B2B filters
**Integration**: Via Composio API v2

**Update Required**:
```javascript
// OLD (apifyRunner.js:18)
const APIFY_ACTOR_ID = process.env.APIFY_ACTOR_ID || "apify/email-phone-scraper";

// NEW
const APIFY_ACTOR_ID = process.env.APIFY_ACTOR_ID || "code_crafter~leads-finder";
```

---

## 8. Environment Variables

### Current .env Configuration:

```bash
# Verified ✅
COMPOSIO_API_KEY=ak_t-F0AbvfZHUZSUrqAGNn
NEON_DATABASE_URL=postgresql://Marketing%20DB_owner:***@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/Marketing%20DB

# Missing/Invalid ❌
APIFY_TOKEN=xxx  # Placeholder
APIFY_API_KEY=xxx  # Placeholder
```

### Required Updates:

```bash
# Add real Apify API key (if using direct API)
APIFY_API_KEY=<your_real_apify_key>

# OR rely on Composio (RECOMMENDED)
# No changes needed - Composio handles auth
```

---

## 9. Verification Checklist

### ❌ Neon Schema Match
- [ ] `company_master` has executive enrichment fields
- [x] `people_master` has title/seniority/email fields ✅
- [ ] Enrichment tracking columns exist
- [ ] Foreign key relationships defined

### ✅ Actor Input Schema
- [x] Actor supports `company_domain` filter
- [x] Actor supports `contact_job_title` filter
- [x] Actor supports `contact_seniority` filter
- [x] Actor returns email addresses
- [x] Actor returns LinkedIn profiles

### ⚠️ Field Mapping
- [x] Apify `firstName` → Neon `first_name` ✅
- [x] Apify `lastName` → Neon `last_name` ✅
- [x] Apify `title` → Neon `title` ✅
- [x] Apify `email` → Neon `email` ✅
- [ ] Company linking strategy defined
- [ ] Phone formatting implemented

### ⚠️ Potential Gaps/Conflicts
- ❌ No executive enrichment workflow file exists
- ❌ `company_master` missing enrichment columns (if denormalized)
- ⚠️ `company_slot_unique_id` requirement unclear
- ⚠️ Phone number formatting not implemented
- ⚠️ Company matching logic not defined

---

## 10. Recommendations

### 🚨 CRITICAL - DO NOT PROCEED UNTIL:

1. **Choose Architecture**:
   - **Option A**: Add executive columns to `company_master` (denormalized)
   - **Option B**: Use `people_master` table (normalized) ✅ RECOMMENDED

2. **If Option A (Denormalized)**:
   ```sql
   -- Run ALTER TABLE statements from Section 3
   -- Create enrichment workflow targeting company_master
   ```

3. **If Option B (Normalized)** ✅:
   ```sql
   -- Relax slot constraint
   ALTER TABLE marketing.people_master
   ALTER COLUMN company_slot_unique_id DROP NOT NULL;

   -- Create enrichment workflow targeting people_master
   ```

4. **Create Enrichment Workflow File**:
   - File: `apps/outreach-process-manager/services/executiveEnrichmentService.js`
   - Implements Apify → Neon pipeline
   - Handles company matching
   - Manages enrichment tracking

5. **Implement Company Matching Logic**:
   ```javascript
   async function findCompanyByDomain(domain) {
     const query = `
       SELECT company_unique_id
       FROM marketing.company_master
       WHERE website_url ILIKE $1
       LIMIT 1
     `;
     return await bridge.query(query, [`%${domain}%`]);
   }
   ```

6. **Test with 1 Company**:
   - Select test company from `company_master`
   - Run enrichment
   - Verify results in `people_master`
   - Validate data quality

---

## 11. Next Steps After Approval

1. **User Decision**:
   - Which architecture? (Denormalized vs Normalized)
   - ALTER TABLE approval if denormalized

2. **Implementation**:
   - Create `executiveEnrichmentService.js`
   - Implement company matching
   - Add phone formatting
   - Create test script

3. **Testing**:
   - Test with 1 company
   - Validate output
   - Check data quality
   - Verify cost

4. **Deployment**:
   - Run trial (5-10 companies)
   - Monitor success rate
   - Adjust filters
   - Scale up

---

## 12. Cost Estimate

### Trial Run (10 Companies):

**Assumptions**:
- 10 companies
- 5 executives per company average
- 50 total leads

**Cost Calculation**:
- Actor starts: 10 runs × $0.02 = $0.20
- Leads: 50 leads × $0.0015 = $0.075
- **Total**: ~$0.28

### Production Run (100 Companies):

**Assumptions**:
- 100 companies
- 5 executives per company average
- 500 total leads

**Cost Calculation**:
- Actor starts: 100 runs × $0.02 = $2.00
- Leads: 500 leads × $0.0015 = $0.75
- **Total**: ~$2.75

---

## 13. Audit Conclusion

### Status: 🚨 NOT READY FOR TRIAL

### Blockers:
1. ❌ Schema missing executive enrichment fields (if denormalized)
2. ❌ No enrichment workflow file
3. ❌ Company matching logic undefined
4. ❌ Slot ID requirement unclear

### Ready Components:
1. ✅ Apify actor verified and accessible
2. ✅ Composio integration working
3. ✅ `people_master` schema supports normalized design
4. ✅ Apify input/output schemas documented

### Estimated Implementation Time:
- **Option A (Denormalized)**: 2-3 hours
- **Option B (Normalized)**: 1-2 hours ✅ FASTER

---

**WAITING FOR USER APPROVAL TO PROCEED**

**Questions for User**:
1. Which architecture: Denormalized (company_master) or Normalized (people_master)?
2. Approve ALTER TABLE if denormalized?
3. How to handle `company_slot_unique_id` requirement?
4. Proceed with trial after fixes?

---

**Report Generated By**: Claude Code
**Barton Doctrine Compliance**: ✅ STAMPED
**Altitude**: 10000 (Execution Layer)
**Process ID**: enrichment_process_audit

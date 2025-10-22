# Executive Enrichment Trial - READY TO RUN

**Date**: 2025-10-21
**Status**: ✅ **ALL SYSTEMS GO**
**Companies Available**: 446 in `intake.company_raw_intake`
**Ready for Enrichment**: 442 companies (99%)

---

## Executive Summary

🎉 **DISCOVERY COMPLETE**: Found 446 companies in West Virginia ready for executive enrichment via Apify `code_crafter~leads-finder` actor.

### What We Found:

✅ **Companies**: 446 in `intake.company_raw_intake` table
✅ **Data Quality**: 99% have website OR LinkedIn (442/446)
✅ **Apify Actor**: `code_crafter~leads-finder` verified and working
✅ **Composio**: Connected and operational
✅ **Storage Table**: `people.contact` exists with all required fields

### Critical Decision Needed:

**Where to store enriched executives?**

**Option A**: `people.contact` table (EXISTS NOW) ✅ RECOMMENDED
**Option B**: `people.marketing_people` table (EXISTS NOW, has enrichment tracking)
**Option C**: Create `marketing.people_master` table (requires migration)

---

## Company Dataset Summary

### Geographic Distribution:
- **100% West Virginia companies**
- All US-based
- Mix of urban and rural locations

### Industry Breakdown (Top 10):
1. Higher Education (15+ universities/colleges)
2. Information Technology & Services
3. Healthcare / Medical Practice
4. Construction
5. Hospitality
6. Automotive
7. Banking / Financial Services
8. Nonprofit Organization Management
9. Primary/Secondary Education
10. Manufacturing

### Company Size Distribution:
- **Small (50-100 employees)**: ~40%
- **Medium (100-300 employees)**: ~35%
- **Large (300-1000+ employees)**: ~25%

### Data Quality Metrics:
| Field | Coverage | Count |
|-------|----------|-------|
| Website | 99% | 442/446 |
| LinkedIn URL | 95% | 424/446 |
| Industry | 98% | 437/446 |
| Employee Count | 100% | 446/446 |
| Location (State) | 100% | 446/446 |
| Phone Number | 92% | 410/446 |

---

## Sample Companies (Top 5 for Trial)

### 1. Concord University [ID: 1]
- **Industry**: Higher Education
- **Size**: 500 employees
- **Website**: http://www.concord.edu
- **LinkedIn**: http://www.linkedin.com/school/concorduniversity
- **Why Good for Trial**: Large org, likely has clear C-suite structure
- **Expected Executives**: CEO/President, CFO, CHRO

### 2. Advantage Technology [ID: 2]
- **Industry**: Information Technology & Services
- **Size**: 93 employees
- **Website**: http://www.advantage.tech
- **LinkedIn**: http://www.linkedin.com/company/advantage-technology
- **Why Good for Trial**: Tech company, modern leadership structure
- **Expected Executives**: CEO, CTO, CFO

### 3. Valley Health Systems, Inc. [ID: 3]
- **Industry**: Nonprofit Organization Management / Healthcare
- **Size**: 250 employees
- **Website**: http://www.valleyhealth.org
- **LinkedIn**: http://www.linkedin.com/company/valley-health-systems-inc-
- **Why Good for Trial**: Healthcare, likely has CHRO
- **Expected Executives**: CEO, CFO, CHRO

### 4. TMC Technologies [ID: 5]
- **Industry**: Information Technology & Services
- **Size**: 110 employees
- **Website**: http://www.tmctechnologies.com
- **LinkedIn**: http://www.linkedin.com/company/tmc-technologies-of-wv
- **Why Good for Trial**: Mid-size tech, clear executive roles
- **Expected Executives**: CEO, CTO, CFO

### 5. The Greenbrier [ID: 80]
- **Industry**: Hospitality
- **Size**: 830 employees
- **Website**: http://www.greenbrier.com
- **LinkedIn**: http://www.linkedin.com/company/the-greenbrier
- **Why Good for Trial**: Large hospitality, complex org structure
- **Expected Executives**: CEO, CFO, CHRO, VP HR

---

## Trial Parameters

### Recommended Trial Size:

**Option 1: Micro Trial (1 company)**
- Company: Advantage Technology [ID: 2]
- Expected leads: 3-5 executives
- Estimated cost: $0.02 + (5 × $0.0015) = **$0.03**
- Time: 2-5 minutes

**Option 2: Small Trial (3 companies)** ✅ RECOMMENDED
- Companies: IDs 2, 3, 5
- Expected leads: 10-15 executives
- Estimated cost: $0.06 + (15 × $0.0015) = **$0.08**
- Time: 5-10 minutes

**Option 3: Medium Trial (10 companies)**
- Companies: IDs 1-10
- Expected leads: 30-50 executives
- Estimated cost: $0.20 + (50 × $0.0015) = **$0.28**
- Time: 15-20 minutes

---

## Apify Actor Configuration

### Input Parameters for West Virginia Companies:

```json
{
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
    "Director of Human Resources",
    "VP of HR",
    "CTO",
    "Chief Technology Officer"
  ],
  "contact_seniority": [
    "c-suite",
    "vp",
    "director"
  ],
  "contact_location": [
    "united states"
  ],
  "contact_state": [
    "west virginia, us"
  ],
  "max_leads": 5
}
```

### Expected Output Fields:

```json
{
  "firstName": "John",
  "lastName": "Smith",
  "title": "CEO",
  "seniority": "c-suite",
  "email": "john.smith@company.com",
  "linkedin_url": "https://linkedin.com/in/johnsmith",
  "company_name": "Advantage Technology",
  "company_domain": "advantage.tech",
  "company_industry": "information technology & services",
  "location": "Charleston, West Virginia, United States"
}
```

---

## Database Storage Strategy

### Recommended: Use `people.contact` Table ✅

**Existing Schema** (VERIFIED):
```sql
CREATE TABLE people.contact (
  contact_id BIGINT PRIMARY KEY,
  first_name TEXT,
  last_name TEXT,
  full_name TEXT,
  title TEXT,              -- Store "CEO", "CFO", "CHRO"
  seniority TEXT,          -- Store "c-suite"
  email TEXT,
  email_status TEXT,
  linkedin_url TEXT,
  company_unique_id TEXT,  -- Link to company
  work_phone_e164 TEXT,
  department TEXT,
  source_system TEXT,
  source_record_id TEXT,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ,
  -- ... 35 columns total
);
```

**Insert Pattern**:
```javascript
INSERT INTO people.contact (
  contact_id,
  first_name,
  last_name,
  full_name,
  title,
  seniority,
  email,
  linkedin_url,
  company_unique_id,
  source_system,
  source_record_id,
  created_at,
  updated_at
) VALUES (
  nextval('people.contact_contact_id_seq'),
  'John',
  'Smith',
  'John Smith',
  'CEO',
  'c-suite',
  'john.smith@company.com',
  'https://linkedin.com/in/johnsmith',
  '<company_barton_id_from_intake>',
  'apify_leads_finder',
  '<apify_run_id>',
  NOW(),
  NOW()
);
```

### Company Matching Strategy:

```javascript
// Match Apify company_domain to intake.company_raw_intake
const companyMatch = await query(`
  SELECT id as intake_id, company, website
  FROM intake.company_raw_intake
  WHERE website ILIKE $1
  LIMIT 1
`, [`%${apifyResult.company_domain}%`]);

// Use intake_id as company_unique_id for now
// OR generate proper Barton ID if needed
```

---

## Enrichment Workflow

### Step-by-Step Process:

#### 1. Select Companies for Trial
```sql
SELECT
  id,
  company,
  website,
  company_linkedin_url,
  industry,
  num_employees
FROM intake.company_raw_intake
WHERE id IN (2, 3, 5)
ORDER BY id;
```

#### 2. Extract Domains
```javascript
const domains = companies.map(c => {
  const url = c.website || c.company_linkedin_url;
  return extractDomain(url); // e.g., "advantage.tech"
});
```

#### 3. Call Apify via Composio
```javascript
const response = await fetch('https://backend.composio.dev/api/v2/actions/APIFY_RUN_ACTOR_SYNC_GET_DATASET_ITEMS/execute', {
  method: 'POST',
  headers: {
    'X-API-Key': 'ak_t-F0AbvfZHUZSUrqAGNn',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    connectedAccountId: 'f81a8a4a-c602-4adf-be02-fadec17cc378',
    appName: 'apify',
    input: {
      actorId: 'code_crafter~leads-finder',
      runInput: {
        company_domain: domains,
        contact_job_title: ['CEO', 'CFO', 'CHRO', 'HR Director'],
        contact_seniority: ['c-suite', 'vp'],
        contact_location: ['united states'],
        contact_state: ['west virginia, us'],
        max_leads: 15
      },
      timeout: 300
    }
  })
});
```

#### 4. Filter & Normalize Results
```javascript
const executives = results.data.items.filter(person => {
  const isCEO = person.title?.toLowerCase().includes('ceo') ||
                person.title?.toLowerCase().includes('chief executive');
  const isCFO = person.title?.toLowerCase().includes('cfo') ||
                person.title?.toLowerCase().includes('chief financial');
  const isCHRO = person.title?.toLowerCase().includes('chro') ||
                 person.title?.toLowerCase().includes('hr director') ||
                 person.title?.toLowerCase().includes('human resources');
  const isCTO = person.title?.toLowerCase().includes('cto') ||
                person.title?.toLowerCase().includes('chief technology');

  return isCEO || isCFO || isCHRO || isCTO;
});
```

#### 5. Insert into people.contact
```javascript
for (const exec of executives) {
  // Match to company in intake
  const company = await matchCompanyByDomain(exec.company_domain);

  await insertContact({
    first_name: exec.firstName,
    last_name: exec.lastName,
    full_name: exec.name || `${exec.firstName} ${exec.lastName}`,
    title: exec.title,
    seniority: exec.seniority || 'c-suite',
    email: exec.email,
    linkedin_url: exec.linkedin_url,
    company_unique_id: company.id.toString(),
    source_system: 'apify_leads_finder',
    source_record_id: apifyRunId
  });
}
```

#### 6. Query Results
```sql
SELECT
  c.contact_id,
  c.first_name,
  c.last_name,
  c.title,
  c.seniority,
  c.email,
  c.linkedin_url,
  cri.company,
  cri.website,
  cri.industry
FROM people.contact c
JOIN intake.company_raw_intake cri
  ON c.company_unique_id = cri.id::text
WHERE c.source_system = 'apify_leads_finder'
  AND c.seniority = 'c-suite'
ORDER BY cri.company, c.title;
```

---

## Trial Execution Script

I'll create `analysis/run_enrichment_trial.js` with the following features:

1. ✅ Select companies from `intake.company_raw_intake`
2. ✅ Call Apify `code_crafter~leads-finder` via Composio
3. ✅ Filter for executives only (CEO, CFO, CHRO, CTO)
4. ✅ Match companies by domain
5. ✅ Insert into `people.contact` table
6. ✅ Generate summary report
7. ✅ Calculate costs
8. ✅ Validate data quality

---

## Cost Breakdown

### Trial Scenarios:

**1 Company** (5 leads expected):
- Actor start: $0.02
- Leads: 5 × $0.0015 = $0.0075
- **Total**: ~$0.03

**3 Companies** (15 leads expected):
- Actor starts: 3 × $0.02 = $0.06
- Leads: 15 × $0.0015 = $0.0225
- **Total**: ~$0.08

**10 Companies** (50 leads expected):
- Actor starts: 10 × $0.02 = $0.20
- Leads: 50 × $0.0015 = $0.075
- **Total**: ~$0.28

**All 446 Companies** (2,230 leads expected @ 5 per company):
- Actor starts: 446 × $0.02 = $8.92
- Leads: 2,230 × $0.0015 = $3.35
- **Total**: ~$12.27

---

## Success Criteria

### Trial Success Metrics:

✅ **Data Quality**:
- 80%+ executives have valid email addresses
- 90%+ executives have LinkedIn profiles
- 95%+ correct job titles (CEO, CFO, etc.)

✅ **Coverage**:
- Find at least 1 executive per company
- Find CEO for 70%+ of companies
- Find CFO for 50%+ of companies

✅ **Accuracy**:
- Emails pass basic validation (format check)
- LinkedIn URLs are valid and accessible
- Seniority matches job title

---

## Next Steps

### BEFORE RUNNING TRIAL:

1. **Decide Storage Table**:
   - [ ] Use `people.contact` (simplest)
   - [ ] Use `people.marketing_people` (has enrichment tracking)
   - [ ] Create `marketing.people_master` (most structured)

2. **Approve Trial Size**:
   - [ ] 1 company ($0.03)
   - [ ] 3 companies ($0.08) ✅ RECOMMENDED
   - [ ] 10 companies ($0.28)

3. **Review Script**:
   - I'll create `analysis/run_enrichment_trial.js`
   - You review and approve before execution

### AFTER APPROVAL:

1. Run trial script
2. Review results in chosen table
3. Validate data quality
4. Calculate actual costs
5. Decide on full rollout (all 446 companies)

---

## Files Created

1. ✅ `analysis/enrichment_process_audit.md` - Full audit report
2. ✅ `analysis/list_companies_for_enrichment.js` - Company discovery script
3. ✅ `analysis/companies_for_enrichment.json` - 446 companies in JSON
4. ✅ `analysis/ENRICHMENT_TRIAL_READY.md` - This document
5. ⏳ `analysis/run_enrichment_trial.js` - Trial execution script (NEXT)

---

## Questions for You

1. **Which table should I use for storage?**
   - `people.contact` (RECOMMENDED - exists, simple)
   - `people.marketing_people` (exists, has enrichment tracking)
   - Create `marketing.people_master` (requires migration)

2. **What trial size?**
   - 1 company ($0.03)
   - 3 companies ($0.08) ✅ RECOMMENDED
   - 10 companies ($0.28)
   - Custom number?

3. **Should I create the trial execution script now?**
   - YES - create and show you before running
   - NO - wait for more review

---

**Status**: ✅ **READY TO PROCEED**
**Waiting for**: Your decision on storage table and trial size
**Estimated Time to Trial**: 10 minutes after approval


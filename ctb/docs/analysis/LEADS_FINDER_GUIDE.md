<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/analysis
Barton ID: 06.01.01
Unique ID: CTB-23417E1E
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
-->

# Leads Finder Actor - Complete Guide

## Actor Information

**Actor ID**: `code_crafter~leads-finder` (IoSHqwTR9YGhzccez)
**Full Name**: ✨Leads Finder - $1.5/1k leads with Emails [Apollo Alternative]
**Categories**: LEAD_GENERATION, AGENTS
**Status**: ✅ Active and Working

---

## Performance Statistics

- **Total Runs**: 20,487
- **Total Users**: 2,836
- **Last Run**: 2025-10-21 (Very Recent!)
- **30-Day Success Rate**: 68.60% (14,236 succeeded out of 20,751 total)

---

## Pricing

**Model**: Pay Per Event
**Minimum Charge**: $0.50

**Event Pricing**:
- **Actor Start**: $0.02 per run
- **Lead Fetched**:
  - FREE/BRONZE: $0.002 per lead
  - SILVER: $0.0018 per lead
  - GOLD/PLATINUM/DIAMOND: $0.0015 per lead

**Example Cost**:
- Fetching 1,000 leads = $0.02 (start) + $1.50 (leads at $0.0015 each) = **$1.52 total**

---

## Default Run Settings

- **Memory**: 512 MB
- **Timeout**: 3000 seconds (50 minutes)
- **Max Items**: Unlimited
- **Build**: latest (v0.0.18)

---

## Key Input Parameters

### 🏢 **Company Filters**

#### `company_domain` (array of strings)
Target specific company websites/domains.

**Examples**:
```json
["google.com", "https://apple.com", "www.tesla.com"]
```

#### `company_industry` (array of strings - select from enum)
Filter by industry. Choose from 140+ industries including:
- `information technology & services`
- `financial services`
- `health, wellness & fitness`
- `real estate`
- `management consulting`
- `retail`
- `marketing & advertising`
- `hospital & health care`
- And 130+ more...

**Example**:
```json
["information technology & services", "financial services", "management consulting"]
```

#### `company_not_industry` (array of strings)
Exclude specific industries.

**Example**:
```json
["retail", "restaurants"]
```

#### `company_keywords` (array of strings)
Include companies with these keywords in their description.

**Examples**:
```json
["software development", "AI", "fintech", "SaaS"]
```

#### `company_not_keywords` (array of strings)
Exclude companies with these keywords.

---

### 👔 **Contact/People Filters**

#### `contact_job_title` (array of strings) ⭐ **KEY FOR EXECUTIVE ENRICHMENT**
Target specific job titles.

**Examples for Executive Enrichment**:
```json
[
  "CEO", "Chief Executive Officer",
  "CFO", "Chief Financial Officer",
  "CTO", "Chief Technology Officer",
  "CHRO", "Chief Human Resources Officer",
  "HR Director", "Director of Human Resources",
  "VP of Human Resources",
  "President", "Managing Director"
]
```

#### `contact_seniority` (array of strings - select from enum)
Filter by seniority level.

**Options**:
- `c-suite` ⭐ **Perfect for CEO/CFO/CTO**
- `vp` - Vice President level
- `director` - Director level
- `manager` - Manager level
- `senior` - Senior level
- `entry` - Entry level
- `training` - Training/Intern

**Example for Executive Enrichment**:
```json
["c-suite", "vp"]
```

#### `contact_location` (array of strings - select from enum)
Filter by country/region. Choose from 200+ locations including:
- `united states`
- `united kingdom`
- `canada`
- `germany`
- `india`
- And 200+ more...

**Example**:
```json
["united states", "canada"]
```

#### `contact_state` (array of strings - select from enum)
Filter by US state or international region.

**Examples**:
```json
["california, us", "new york, us", "texas, us"]
```

#### `contact_city` (array of strings)
Target specific cities.

**Examples**:
```json
["San Francisco", "New York", "Austin"]
```

---

### 📊 **Lead Count & Limits**

#### `max_leads` (integer)
Maximum number of leads to fetch.

**Default**: Unlimited (but costs apply per lead)
**Free Plan Limit**: 100 leads per run

**Example**:
```json
1000
```

---

## Executive Enrichment Example Input

Here's a complete example for finding C-suite executives in tech companies:

```json
{
  "company_industry": [
    "information technology & services",
    "computer software",
    "internet",
    "financial services"
  ],
  "company_keywords": [
    "software", "SaaS", "AI", "fintech", "cloud"
  ],
  "contact_job_title": [
    "CEO", "Chief Executive Officer",
    "CFO", "Chief Financial Officer",
    "CTO", "Chief Technology Officer",
    "CHRO", "Chief Human Resources Officer",
    "HR Director", "VP of HR"
  ],
  "contact_seniority": [
    "c-suite", "vp"
  ],
  "contact_location": [
    "united states"
  ],
  "contact_state": [
    "california, us",
    "new york, us",
    "texas, us",
    "massachusetts, us"
  ],
  "max_leads": 500
}
```

**Estimated Cost**: $0.02 (start) + $0.75 (500 leads × $0.0015) = **$0.77**

---

## Example: Target HR Leaders at Healthcare Companies

```json
{
  "company_industry": [
    "hospital & health care",
    "health, wellness & fitness",
    "medical practice",
    "pharmaceuticals"
  ],
  "contact_job_title": [
    "CHRO",
    "Chief Human Resources Officer",
    "HR Director",
    "Director of Human Resources",
    "VP of Human Resources",
    "Head of People",
    "Chief People Officer"
  ],
  "contact_seniority": [
    "c-suite",
    "vp",
    "director"
  ],
  "contact_location": [
    "united states"
  ],
  "max_leads": 300
}
```

---

## Example: Financial Executives at Large Companies

```json
{
  "company_industry": [
    "financial services",
    "banking",
    "investment management",
    "insurance"
  ],
  "contact_job_title": [
    "CFO",
    "Chief Financial Officer",
    "VP of Finance",
    "Finance Director",
    "Treasurer",
    "Controller"
  ],
  "contact_seniority": [
    "c-suite",
    "vp"
  ],
  "contact_location": [
    "united states"
  ],
  "contact_state": [
    "new york, us",
    "illinois, us",
    "california, us"
  ],
  "max_leads": 250
}
```

---

## Expected Output Fields

Based on the actor description, you should receive:

- **Business Email** ✅
- **Personal Email** ✅ (when available)
- **LinkedIn Profile URL** ✅
- **Full Name**
- **Job Title**
- **Company Name**
- **Company Domain**
- **Company Industry**
- **Location**
- **Seniority Level**

---

## Integration with Composio

To run this actor via Composio:

```javascript
const payload = {
  connectedAccountId: 'f81a8a4a-c602-4adf-be02-fadec17cc378',
  appName: 'apify',
  input: {
    company_industry: ['information technology & services'],
    contact_job_title: ['CEO', 'CFO', 'CTO'],
    contact_seniority: ['c-suite'],
    contact_location: ['united states'],
    max_leads: 100
  }
};

const response = await fetch('https://backend.composio.dev/api/v2/actions/APIFY_RUN_ACTOR/execute', {
  method: 'POST',
  headers: {
    'X-API-Key': 'ak_t-F0AbvfZHUZSUrqAGNn',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(payload)
});
```

---

## Best Practices

1. **Start Small**: Test with `max_leads: 10-50` first to verify results
2. **Use Multiple Filters**: Combine industry + job title + seniority for precision
3. **Monitor Costs**: Each lead costs $0.0015-$0.002
4. **Check Success Rate**: Current 68% success rate - expect some failed runs
5. **Timeout**: 50-minute timeout means large requests (1000+ leads) should complete
6. **Free Plan Limit**: Limited to 100 leads per run on free tier

---

## Recommended Use Cases for Barton Outreach

### 1. **Executive Enrichment** (Your Primary Use Case)
Filter for C-suite (CEO, CFO, CTO, CHRO) at target companies by industry.

### 2. **HR Leader Targeting**
Specifically find HR Directors and CHROs for people-focused outreach.

### 3. **Industry-Specific Campaigns**
Target all executives in specific industries (e.g., healthcare, fintech).

### 4. **Geographic Expansion**
Find executives in specific states or cities for regional campaigns.

### 5. **Company-Specific Research**
Use `company_domain` to enrich known companies with leadership contact info.

---

## Next Steps

1. ✅ **Actor Found**: code_crafter~leads-finder is accessible
2. ✅ **Schema Documented**: All input parameters identified
3. **Test Run**: Execute a small test with 10-20 leads
4. **Integrate**: Add to your outreach pipeline
5. **Scale**: Increase lead volume once validated

---

**Support**: codecrafter70@gmail.com (from actor description)

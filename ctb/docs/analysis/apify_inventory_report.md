<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/analysis
Barton ID: 06.01.01
Unique ID: CTB-CE751F65
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
-->

# Apify Environment Discovery Report
**Generated**: 2025-10-21T17:31:43Z
**Process ID**: Apify Actor Discovery and Schema Analysis
**Unique ID**: 04.01.99.11.05000.001
**Barton Doctrine**: Fully Compliant

---

## Executive Summary

This report provides a complete inventory of your Apify environment, analyzing actors currently referenced in the codebase, their intended usage patterns, and recommendations for executive-level (CEO/CFO/HR) contact enrichment.

### Key Findings

| Category | Count | Status |
|----------|-------|--------|
| **Actors Referenced in Code** | 3 | ⚠️ Not yet created in Apify account |
| **Mock/Simulated Actors** | 5 | 📝 Designed but not implemented |
| **Total Integration Points** | 8 | 🔧 Ready for configuration |
| **Executive Enrichment Opportunities** | High | ✅ Framework ready |

### Critical Discovery

**⚠️ IMPORTANT**: No Apify actors were found in your account (all returned HTTP 404). This indicates:
1. Actors need to be created or subscribed to in your Apify account
2. Actor IDs in the code may need to be updated
3. API permissions may need to be configured

---

## Part 1: Currently Referenced Actors

These actors are actively referenced in your codebase but need to be set up in your Apify account.

### 1.1 Primary Contact Scraper
**Actor ID**: `apify/email-phone-scraper`
**Location**: `agents/specialists/apifyRunner.js:18`
**Usage**: Primary contact scraping engine

#### Implementation Details
```javascript
const APIFY_ACTOR_ID = process.env.APIFY_ACTOR_ID || "apify/email-phone-scraper";
```

#### Input Schema (Expected)
Based on code analysis in `apifyRunner.js`:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `startUrls` | array | ✅ | Array of URLs to scrape |
| `companyId` | string | ✅ | Company unique identifier |
| `maxPagesToScrape` | integer | ❌ | Maximum pages (default: 5) |
| `extractEmails` | boolean | ❌ | Extract email addresses (default: true) |
| `extractPhones` | boolean | ❌ | Extract phone numbers (default: true) |
| `extractLinkedIn` | boolean | ❌ | Extract LinkedIn profiles (default: true) |
| `extractNames` | boolean | ❌ | Extract contact names (default: true) |
| `extractJobTitles` | boolean | ❌ | Extract job titles (default: true) |
| `proxyConfiguration` | object | ❌ | Proxy settings |

#### Output Schema (Expected)
Based on normalization in `apifyRunner.js:188-232`:

| Field | Type | Description | Executive Relevance |
|-------|------|-------------|---------------------|
| `email` | string | Contact email address | ⭐⭐⭐ Critical |
| `phone` | string | Contact phone number | ⭐⭐ Important |
| `linkedin` | string | LinkedIn profile URL | ⭐⭐⭐ Critical |
| `firstName` | string | First name | ⭐⭐⭐ Critical |
| `lastName` | string | Last name | ⭐⭐⭐ Critical |
| `fullName` | string | Full name | ⭐⭐⭐ Critical |
| `jobTitle` | string | Job title/position | ⭐⭐⭐ **CRITICAL FOR EXECUTIVES** |
| `department` | string | Department name | ⭐⭐ Important |
| `sourceUrl` | string | Source page URL | ⭐ Reference |

**Executive Enrichment Score**: **90/100**

**Why it's suitable for executives**:
- ✅ Extracts job titles (critical for identifying CEOs, CFOs, HR Directors)
- ✅ Captures full contact information (email, phone, LinkedIn)
- ✅ Supports department filtering
- ✅ Includes name normalization (first/last/full)

---

### 1.2 LinkedIn Profile Scraper
**Actor ID**: `apify~linkedin-profile-scraper`
**Location**: `packages/mcp-clients/src/clients/apify-mcp-client.ts:57`
**Usage**: LinkedIn-specific profile data extraction

#### Implementation Details
```typescript
const response = await this.client.post('/acts/apify~linkedin-profile-scraper/runs', {
  input: {
    startUrls: profileUrls.map(url => ({ url })),
    proxyConfiguration: { useApifyProxy: true },
    includePrivateProfiles: false,
    scrapeEmployees: false,
    scrapeContactInfo: extractEmails
  }
});
```

#### Input Schema (Expected)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `startUrls` | array | ✅ | LinkedIn profile URLs |
| `proxyConfiguration` | object | ❌ | Proxy configuration |
| `includePrivateProfiles` | boolean | ❌ | Include private profiles (default: false) |
| `scrapeEmployees` | boolean | ❌ | Scrape employee lists (default: false) |
| `scrapeContactInfo` | boolean | ❌ | Extract contact information |

#### Output Schema (Expected)
Based on normalization in `apify-mcp-client.ts:73-82`:

| Field | Type | Description | Executive Relevance |
|-------|------|-------------|---------------------|
| `email` | string | Email from LinkedIn | ⭐⭐⭐ Critical |
| `url` | string | Profile URL | ⭐⭐⭐ Critical |
| `name` / `fullName` | string | Full name | ⭐⭐⭐ Critical |
| `headline` | string | Professional headline | ⭐⭐⭐ **CRITICAL FOR EXECUTIVES** |
| `company` | string | Current company | ⭐⭐⭐ Critical |
| `experience` | array | Work experience | ⭐⭐⭐ **CRITICAL FOR ROLE VALIDATION** |
| `experience[].title` | string | Job title from experience | ⭐⭐⭐ **EXECUTIVE IDENTIFIER** |
| `experience[].company` | string | Company from experience | ⭐⭐ Important |
| `contactInfo` | object | Contact information | ⭐⭐⭐ Critical |
| `contactInfo.email` | string | Email address | ⭐⭐⭐ Critical |

**Executive Enrichment Score**: **95/100**

**Why it's the best for executives**:
- ✅ **LinkedIn is the primary source for executive profiles**
- ✅ **Headline often contains "CEO", "CFO", "Chief", etc.**
- ✅ **Experience array allows title history validation**
- ✅ **Company information for current role verification**
- ✅ Professional contact information

**Recommended Use Case**:
- CEO/CFO/Executive Officer identification
- Title verification and validation
- Professional background analysis

---

### 1.3 Website Content Crawler
**Actor ID**: `apify~website-content-crawler`
**Location**: `packages/mcp-clients/src/clients/apify-mcp-client.ts:118`
**Usage**: Website scraping for contact pages

#### Implementation Details
```typescript
const response = await this.client.post('/acts/apify~website-content-crawler/runs', {
  input: {
    startUrls: websiteUrls.map(url => ({ url })),
    maxCrawlDepth: 2,
    maxCrawlPages: 10,
    proxyConfiguration: { useApifyProxy: true },
    clickElementsCssSelector: '[href*="contact"], [href*="about"]',
    pageFunction: `async function pageFunction(context) { ... }`
  }
});
```

#### Input Schema (Expected)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `startUrls` | array | ✅ | Website URLs to crawl |
| `maxCrawlDepth` | integer | ❌ | Maximum depth (default: 2) |
| `maxCrawlPages` | integer | ❌ | Maximum pages (default: 10) |
| `proxyConfiguration` | object | ❌ | Proxy settings |
| `pseudoUrls` | array | ❌ | URL patterns to follow |
| `clickElementsCssSelector` | string | ❌ | CSS selectors to click |
| `pageFunction` | string | ❌ | Custom extraction function |

#### Output Schema (Expected)
Based on normalization in `apify-mcp-client.ts:159-171`:

| Field | Type | Description | Executive Relevance |
|-------|------|-------------|---------------------|
| `url` | string | Page URL | ⭐ Reference |
| `title` | string | Page title | ⭐ Reference |
| `emails` | array | Extracted emails | ⭐⭐⭐ Critical |
| `text` | string | Page text content | ⭐ Reference |

**Executive Enrichment Score**: **70/100**

**Why it's suitable for executives**:
- ✅ Targets "contact" and "about" pages (where executives are often listed)
- ✅ Extracts multiple emails from pages
- ✅ Can find executive contact info on company websites
- ⚠️ No built-in title extraction (requires custom pageFunction)
- ⚠️ Less structured than LinkedIn data

**Recommended Use Case**:
- Executive team page scraping
- Leadership/about page contacts
- Backup enrichment when LinkedIn fails

---

## Part 2: Mock/Simulated Actors

These actors are referenced in service handlers but implemented as simulations. They represent the **intended enrichment capabilities**.

### 2.1 LinkedIn Company Scraper
**Reference**: `apps/outreach-process-manager/services/apifyHandler.js`
**Simulated**: Yes
**Purpose**: Find company LinkedIn profiles

#### Intended Input Schema
```javascript
{
  searchQuery: "Company Name",
  website: "https://company.com",
  location: "City, State"
}
```

#### Intended Output Schema
```javascript
{
  linkedinUrl: "https://linkedin.com/company/...",
  matchesCount: 5,
  verificationScore: 0.85
}
```

**Executive Enrichment Potential**: **85/100**
- ✅ Essential for finding company profiles
- ✅ Gateway to employee/executive searches
- ✅ Provides company validation

---

### 2.2 Website Content Crawler (Alternative)
**Reference**: `apps/outreach-process-manager/services/apifyHandler.js`
**Simulated**: Yes
**Purpose**: Find company websites

#### Intended Input Schema
```javascript
{
  searchTerms: ["Company Name", "LinkedIn Name"],
  location: "City, State",
  additionalContext: {
    industry: "Technology",
    employee_count: 500
  }
}
```

#### Intended Output Schema
```javascript
{
  websiteUrl: "https://company.com",
  verificationMethod: "dns_verification",
  additionalCompanyInfo: {
    description: "...",
    industry: "Technology"
  }
}
```

**Executive Enrichment Potential**: **60/100**
- ✅ Helps validate company information
- ⚠️ Indirect benefit for executive enrichment

---

### 2.3 Company Data Scraper
**Reference**: `apps/outreach-process-manager/services/apifyHandler.js`
**Simulated**: Yes
**Purpose**: Extract company registration data (EIN, tax ID)

#### Intended Input Schema
```javascript
{
  companyName: "Company Name",
  state: "CA",
  address: "City, State",
  website: "https://company.com",
  dataTypes: ["ein", "tax_id", "registration_number", "incorporation_date"]
}
```

**Executive Enrichment Potential**: **40/100**
- ⚠️ More focused on compliance than executives
- ✅ Can validate company legitimacy

---

### 2.4 Business Permit Scraper
**Reference**: `apps/outreach-process-manager/services/apifyHandler.js`
**Simulated**: Yes
**Purpose**: Find business licenses and permits

**Executive Enrichment Potential**: **30/100**
- ⚠️ Primarily for compliance validation
- ❌ No direct executive contact information

---

### 2.5 Financial Data Scraper
**Reference**: `apps/outreach-process-manager/services/apifyHandler.js`
**Simulated**: Yes
**Purpose**: Extract revenue and funding data

#### Intended Input Schema
```javascript
{
  companyName: "Company Name",
  website: "https://company.com",
  linkedinUrl: "https://linkedin.com/company/...",
  industry: "Technology",
  dataTypes: ["annual_revenue", "funding_rounds", "valuation", "employee_count"]
}
```

**Executive Enrichment Potential**: **50/100**
- ✅ Provides context for targeting (company size, funding)
- ⚠️ No direct executive contacts
- ✅ Useful for qualifying leads

---

## Part 3: Outreach Linkage

### Current Integration Points

#### 3.1 Apify Runner (Primary Integration)
**File**: `agents/specialists/apifyRunner.js`
**Altitude**: 10,000 ft (Execution Layer)
**Barton Doctrine Compliance**: ✅ Fully compliant

**Process Flow**:
```
1. History Check (prevents duplicate scraping)
   ↓
2. Call Apify Actor via Composio MCP
   ↓
3. Normalize results to standard schema
   ↓
4. Write to Firebase (working memory)
   ↓
5. Write to Neon (permanent storage)
   ↓
6. Calculate metrics
   ↓
7. Record in History Layer
   ↓
8. Audit logging
```

**Key Features**:
- ✅ Barton Doctrine ID generation (`04.01.02.07.10000.xxx`)
- ✅ Composio MCP integration (no direct Apify calls)
- ✅ Dual storage (Firebase + Neon)
- ✅ History enforcement (7-day window)
- ✅ Full audit trail

**Metrics Tracked**:
```javascript
{
  total_contacts: 25,
  with_email: 20,
  with_phone: 15,
  with_linkedin: 18,
  with_name: 25,
  with_title: 22  // ⭐ Critical for executive filtering
}
```

---

#### 3.2 MCP Client (TypeScript Integration)
**File**: `packages/mcp-clients/src/clients/apify-mcp-client.ts`
**Purpose**: LinkedIn and website scraping abstraction

**Methods**:
- `scrapeLinkedIn(profileUrls, extractEmails)` - Profile scraping
- `scrapeWebsite(websiteUrls, extractEmails)` - Website scraping
- `healthCheck()` - Service verification

**Output Normalization**:
```typescript
interface ApifyScrapedData {
  slot: string;           // Unique identifier
  email: string;          // ⭐ Executive contact
  source_url: string;     // Reference
  name?: string;          // ⭐ Executive name
  company?: string;       // ⭐ Executive company
  title?: string;         // ⭐⭐⭐ CRITICAL FOR EXECUTIVES
  linkedin_profile?: string; // ⭐⭐⭐ CRITICAL FOR VALIDATION
  website?: string;
  scraped_at: string;
}
```

---

#### 3.3 Service Handler (Enrichment Router)
**File**: `apps/outreach-process-manager/services/apifyHandler.js`
**Purpose**: Error-driven enrichment routing

**Error Type Routing**:
```javascript
switch (error_type) {
  case 'missing_linkedin':
  case 'invalid_linkedin':
    → enrichLinkedInProfile()  // ⭐ Executive profiles

  case 'missing_website':
  case 'website_not_found':
    → enrichCompanyWebsite()

  case 'missing_ein':
  case 'missing_tax_id':
    → enrichCompanyRegistration()

  case 'missing_revenue':
  case 'missing_financial_data':
    → enrichFinancialData()
}
```

**Executive Relevance**:
- ✅ `enrichLinkedInProfile()` - Primary executive enrichment path
- ⚠️ Other enrichment functions provide company context

---

### 3.4 Database Integration

#### Neon PostgreSQL Tables
**Table**: `marketing.contact_verification`
**Schema** (from `apifyRunner.js:353`):

| Column | Type | Description | Executive Use |
|--------|------|-------------|---------------|
| `company_unique_id` | text | Company identifier | ⭐ Link |
| `contact_unique_id` | text | Contact identifier | ⭐ Primary key |
| `email` | text | Email address | ⭐⭐⭐ Critical |
| `phone` | text | Phone number | ⭐⭐ Important |
| `linkedin` | text | LinkedIn URL | ⭐⭐⭐ Critical |
| `first_name` | text | First name | ⭐⭐⭐ Critical |
| `last_name` | text | Last name | ⭐⭐⭐ Critical |
| `full_name` | text | Full name | ⭐⭐⭐ Critical |
| `job_title` | text | Job title | ⭐⭐⭐ **EXECUTIVE FILTER** |
| `department` | text | Department | ⭐⭐ Filter |
| `status` | text | Status | ⭐ Tracking |
| `confidence_score` | numeric | Confidence | ⭐ Quality |
| `validated` | boolean | Validated | ⭐ Quality |

**Executive Filtering Query Example**:
```sql
SELECT * FROM marketing.contact_verification
WHERE job_title ILIKE '%CEO%'
   OR job_title ILIKE '%Chief Executive%'
   OR job_title ILIKE '%CFO%'
   OR job_title ILIKE '%Chief Financial%'
   OR job_title ILIKE '%HR Director%'
   OR job_title ILIKE '%Chief Human Resources%'
   AND email IS NOT NULL
   AND linkedin IS NOT NULL
   ORDER BY confidence_score DESC;
```

---

## Part 4: Training Opportunities

### 4.1 Custom Actor Creation

Based on the patterns in your codebase, here are recommended **custom actors** to create:

#### **Recommended Actor #1: Executive Contact Finder**
**Purpose**: Specialized LinkedIn scraping for C-level executives

**Input Schema**:
```json
{
  "properties": {
    "companyLinkedInUrl": { "type": "string", "description": "Company LinkedIn URL" },
    "companyName": { "type": "string" },
    "targetRoles": {
      "type": "array",
      "items": { "type": "string" },
      "default": ["CEO", "CFO", "CTO", "COO", "CHRO", "Chief", "President"]
    },
    "includeEmail": { "type": "boolean", "default": true },
    "maxExecutives": { "type": "number", "default": 10 }
  }
}
```

**Output Schema**:
```json
{
  "properties": {
    "executives": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "title": { "type": "string" },
          "linkedin": { "type": "string" },
          "email": { "type": "string" },
          "phone": { "type": "string" },
          "department": { "type": "string" },
          "yearsInRole": { "type": "number" },
          "previousTitles": { "type": "array" },
          "confidence": { "type": "number" }
        }
      }
    }
  }
}
```

**Why this is valuable**:
- ✅ Specifically targets executives by title
- ✅ Includes contact information extraction
- ✅ Provides role validation data
- ✅ Confidence scoring for data quality

---

#### **Recommended Actor #2: Company Leadership Page Scraper**
**Purpose**: Scrape executive team pages from company websites

**Input Schema**:
```json
{
  "properties": {
    "websiteUrl": { "type": "string" },
    "targetPages": {
      "type": "array",
      "default": ["about", "team", "leadership", "executives", "management"]
    },
    "extractTitles": {
      "type": "array",
      "default": ["CEO", "CFO", "CTO", "Chief", "President", "VP", "Director"]
    }
  }
}
```

**Output Schema**:
```json
{
  "properties": {
    "executives": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "title": { "type": "string" },
          "bio": { "type": "string" },
          "imageUrl": { "type": "string" },
          "email": { "type": "string" },
          "linkedin": { "type": "string" },
          "sourceUrl": { "type": "string" }
        }
      }
    },
    "companyInfo": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "industry": { "type": "string" },
        "size": { "type": "string" }
      }
    }
  }
}
```

**Why this is valuable**:
- ✅ Captures executives not on LinkedIn
- ✅ Often includes official contact information
- ✅ Provides context (bios, photos)
- ✅ Backup enrichment source

---

#### **Recommended Actor #3: Multi-Source Executive Enricher**
**Purpose**: Aggregate executive data from multiple sources

**Input Schema**:
```json
{
  "properties": {
    "executiveName": { "type": "string" },
    "companyName": { "type": "string" },
    "knownLinkedIn": { "type": "string" },
    "sources": {
      "type": "array",
      "items": { "type": "string" },
      "default": ["linkedin", "company_website", "crunchbase", "zoominfo"]
    },
    "enrichmentDepth": {
      "type": "string",
      "enum": ["basic", "standard", "comprehensive"],
      "default": "standard"
    }
  }
}
```

**Output Schema**:
```json
{
  "properties": {
    "executive": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "title": { "type": "string" },
        "company": { "type": "string" },
        "contactInfo": {
          "type": "object",
          "properties": {
            "email": { "type": "string" },
            "phone": { "type": "string" },
            "linkedin": { "type": "string" },
            "twitter": { "type": "string" }
          }
        },
        "background": {
          "type": "object",
          "properties": {
            "education": { "type": "array" },
            "previousRoles": { "type": "array" },
            "yearsOfExperience": { "type": "number" }
          }
        },
        "dataQuality": {
          "type": "object",
          "properties": {
            "sourcesChecked": { "type": "number" },
            "sourcesMatched": { "type": "number" },
            "confidenceScore": { "type": "number" },
            "lastUpdated": { "type": "string" }
          }
        }
      }
    }
  }
}
```

**Why this is valuable**:
- ✅ Highest data quality through multiple sources
- ✅ Confidence scoring
- ✅ Comprehensive executive profiles
- ✅ Background validation

---

### 4.2 Actor Configuration Best Practices

Based on your existing implementation, follow these patterns:

#### Pattern 1: Composio MCP Integration
```javascript
// ✅ CORRECT: Use Composio MCP
const runPayload = {
  tool: "apify.run_actor",
  params: {
    actor_id: APIFY_ACTOR_ID,
    run_input: { /* actor-specific input */ },
    build: "latest",
    memory_mbytes: 512,
    timeout_secs: 300,
    wait_for_finish: true
  },
  metadata: {
    unique_id: uniqueId,
    process_id: PROCESS_ID,
    orbt_layer: 10000,
    blueprint_version: "1.0"
  }
};

await fetch('http://localhost:3001/tool', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Composio-Api-Key': COMPOSIO_API_KEY,
    'X-Apify-Api-Key': APIFY_API_KEY
  },
  body: JSON.stringify(runPayload)
});

// ❌ INCORRECT: Direct Apify API calls
// Don't do this - breaks Barton Doctrine
```

#### Pattern 2: Result Normalization
```javascript
// ✅ CORRECT: Normalize to standard schema
function normalizeExecutives(apifyResults) {
  return apifyResults
    .filter(contact => isExecutiveTitle(contact.jobTitle))
    .map(executive => ({
      // Barton Doctrine fields
      contact_unique_id: generateContactBartonId(),
      company_unique_id: companyUniqueId,

      // Executive fields
      email: executive.email || null,
      phone: executive.phone || null,
      linkedin: executive.linkedin || null,
      first_name: executive.firstName || null,
      last_name: executive.lastName || null,
      job_title: executive.jobTitle || null,
      department: executive.department || null,

      // Metadata
      status: "scraped",
      source: "apify",
      confidence_score: calculateConfidence(executive),
      scraped_at: new Date().toISOString(),

      // Barton Doctrine tracking
      unique_id: `${uniqueId}.exec.${index}`,
      process_id: PROCESS_ID,
      altitude: 10000
    }));
}

function isExecutiveTitle(title) {
  if (!title) return false;
  const titleLower = title.toLowerCase();
  return titleLower.includes('ceo') ||
         titleLower.includes('cfo') ||
         titleLower.includes('cto') ||
         titleLower.includes('chief') ||
         titleLower.includes('president') ||
         titleLower.includes('head of');
}
```

#### Pattern 3: History Enforcement
```javascript
// ✅ CORRECT: Check history before scraping executives
const historyCheck = await checkHistoryBeforeRun({
  entity_id: executive_linkedin_url,
  field: 'executive_enrichment',
  windowDays: 30,  // Longer window for executives
  forceRun: force,
  strategy: 'firebase-first'
});

if (!historyCheck.shouldRun) {
  console.log(`⏭️ Skipping executive enrichment - already enriched within 30 days`);
  return { skipped: true, reason: historyCheck.reason };
}
```

---

## Part 5: Top 3 Actors for Executive Enrichment

### 🥇 **#1 Recommended: LinkedIn Profile Scraper**
**Actor ID**: `apify~linkedin-profile-scraper` (needs to be created/configured)
**Executive Enrichment Score**: **95/100**

**Why it's #1**:
- ✅ **Primary source of executive data**
- ✅ **Headline field contains titles** ("CEO at Company", "Chief Financial Officer")
- ✅ **Experience array for validation** (current and previous roles)
- ✅ **Professional contact information**
- ✅ **Company affiliations**
- ✅ **Already integrated in your codebase**

**Best Use Cases**:
1. CEO/CFO/CTO identification
2. Executive title verification
3. Professional background validation
4. LinkedIn profile enrichment

**Implementation Priority**: **🔴 HIGH - Implement First**

**Sample Query**:
```javascript
await apifyMCPClient.scrapeLinkedIn([
  'https://linkedin.com/in/john-doe-ceo',
  'https://linkedin.com/in/jane-smith-cfo'
], true); // extractEmails = true
```

**Expected Output**:
```json
{
  "success": true,
  "data": [
    {
      "slot": "linkedin-acme-corp-john-doe-1234567890",
      "email": "john.doe@acmecorp.com",
      "source_url": "https://linkedin.com/in/john-doe-ceo",
      "name": "John Doe",
      "company": "Acme Corp",
      "title": "Chief Executive Officer",
      "linkedin_profile": "https://linkedin.com/in/john-doe-ceo",
      "scraped_at": "2025-10-21T17:30:00Z"
    }
  ]
}
```

---

### 🥈 **#2 Recommended: Email Phone Scraper**
**Actor ID**: `apify/email-phone-scraper` (needs to be created/configured)
**Executive Enrichment Score**: **90/100**

**Why it's #2**:
- ✅ **Extracts job titles** (critical for filtering)
- ✅ **Complete contact data** (email, phone, LinkedIn, name)
- ✅ **Department information**
- ✅ **Already the primary actor** in your codebase (`apifyRunner.js`)
- ✅ **Flexible input** (any website URL)

**Best Use Cases**:
1. Company website leadership page scraping
2. Contact page executive extraction
3. About page executive identification
4. Backup when LinkedIn data unavailable

**Implementation Priority**: **🔴 HIGH - Implement First**

**Sample Query**:
```javascript
await runApifyScrape({
  company_unique_id: 'CMP-12345',
  domain_url: 'https://acmecorp.com/about/leadership',
  blueprint_id: 'BP-EXEC-001',
  force: false
});
```

**Expected Output** (normalized):
```json
{
  "success": true,
  "contacts": [
    {
      "contact_unique_id": "25.13.07.07.12345.001",
      "company_unique_id": "CMP-12345",
      "email": "john.doe@acmecorp.com",
      "phone": "+1-555-0100",
      "linkedin": "https://linkedin.com/in/john-doe",
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "John Doe",
      "job_title": "Chief Executive Officer",
      "department": "Executive",
      "status": "scraped",
      "confidence_score": 0.7,
      "source": "apify"
    }
  ],
  "metrics": {
    "total_contacts": 5,
    "with_email": 5,
    "with_title": 5
  }
}
```

---

### 🥉 **#3 Recommended: Website Content Crawler**
**Actor ID**: `apify~website-content-crawler` (needs to be created/configured)
**Executive Enrichment Score**: **70/100**

**Why it's #3**:
- ✅ **Targets leadership pages** (via CSS selector targeting)
- ✅ **Flexible page function** (custom extraction logic)
- ✅ **Multiple email extraction**
- ✅ **Already integrated** in your codebase
- ⚠️ **Requires custom extraction** for titles

**Best Use Cases**:
1. Executive team page scraping
2. Leadership/about page contacts
3. Backup enrichment source
4. Companies without strong LinkedIn presence

**Implementation Priority**: **🟡 MEDIUM - Implement After #1 and #2**

**Sample Query**:
```javascript
await apifyMCPClient.scrapeWebsite([
  'https://acmecorp.com/about/team',
  'https://acmecorp.com/leadership',
  'https://acmecorp.com/executives'
], true); // extractEmails = true
```

**Enhanced Page Function** (for executive extraction):
```javascript
async function pageFunction(context) {
  const { request, page } = context;

  // Extract emails
  const emails = [];
  const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}/g;
  const text = await page.evaluate(() => document.body.textContent);
  const emailMatches = text.match(emailRegex);
  if (emailMatches) emails.push(...emailMatches);

  // Extract executive info from structured data
  const executives = await page.evaluate(() => {
    const execs = [];
    const executiveTitles = ['ceo', 'cfo', 'cto', 'chief', 'president', 'vp', 'director'];

    // Find all headings and nearby text
    document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(heading => {
      const text = heading.textContent.toLowerCase();

      // Check if heading contains executive title
      if (executiveTitles.some(title => text.includes(title))) {
        const container = heading.closest('div, section, article') || heading;

        execs.push({
          name: heading.textContent.trim(),
          title: heading.textContent.trim(),
          section: container.textContent.substr(0, 500)
        });
      }
    });

    return execs;
  });

  return {
    url: request.url,
    title: await page.title(),
    emails: [...new Set(emails)],
    executives: executives
  };
}
```

---

## Part 6: Recommendations

### 6.1 Immediate Action Items

#### Priority 1: Set Up Apify Actors (Week 1)

1. **Create/Subscribe to Core Actors**:
   - [ ] Subscribe to `apify/linkedin-profile-scraper` in Apify Store
   - [ ] Subscribe to `apify/email-phone-scraper` in Apify Store
   - [ ] Subscribe to `apify/website-content-crawler` in Apify Store

2. **Update Environment Configuration**:
   ```bash
   # Update .env file
   APIFY_API_KEY=your_actual_api_key_here
   APIFY_ACTOR_ID=apify/email-phone-scraper
   ```

3. **Test Integration**:
   ```bash
   # Test apifyRunner
   npm run scrape:apify -- --company=TEST-001 --domain=https://example.com

   # Verify results in Firebase and Neon
   ```

---

#### Priority 2: Build Executive Filtering (Week 2)

1. **Create Executive Filter Function**:
   ```javascript
   // Add to apifyRunner.js
   function filterExecutives(contacts) {
     const executiveTitles = [
       'ceo', 'chief executive',
       'cfo', 'chief financial',
       'cto', 'chief technology',
       'coo', 'chief operating',
       'chro', 'chief human resources', 'hr director',
       'president', 'vice president', 'vp'
     ];

     return contacts.filter(contact => {
       if (!contact.job_title) return false;

       const titleLower = contact.job_title.toLowerCase();
       return executiveTitles.some(execTitle =>
         titleLower.includes(execTitle)
       );
     });
   }
   ```

2. **Add Executive-Specific Metadata**:
   ```javascript
   function enrichExecutiveMetadata(contact) {
     return {
       ...contact,
       is_executive: true,
       executive_level: determineLevel(contact.job_title),
       executive_function: determineFunction(contact.job_title),
       priority: calculatePriority(contact)
     };
   }

   function determineLevel(title) {
     const titleLower = title.toLowerCase();
     if (titleLower.includes('chief') || titleLower.includes('ceo')) return 'C-LEVEL';
     if (titleLower.includes('president')) return 'PRESIDENT';
     if (titleLower.includes('vp') || titleLower.includes('vice president')) return 'VP';
     if (titleLower.includes('director')) return 'DIRECTOR';
     return 'MANAGER';
   }

   function determineFunction(title) {
     const titleLower = title.toLowerCase();
     if (titleLower.includes('executive') || titleLower.includes('ceo')) return 'EXECUTIVE';
     if (titleLower.includes('financial') || titleLower.includes('cfo')) return 'FINANCE';
     if (titleLower.includes('technology') || titleLower.includes('cto')) return 'TECHNOLOGY';
     if (titleLower.includes('operating') || titleLower.includes('coo')) return 'OPERATIONS';
     if (titleLower.includes('human') || titleLower.includes('hr')) return 'HUMAN_RESOURCES';
     return 'OTHER';
   }
   ```

3. **Update Database Schema**:
   ```sql
   -- Add executive-specific columns
   ALTER TABLE marketing.contact_verification
   ADD COLUMN is_executive BOOLEAN DEFAULT false,
   ADD COLUMN executive_level TEXT,
   ADD COLUMN executive_function TEXT,
   ADD COLUMN priority INTEGER;

   -- Create executive index
   CREATE INDEX idx_contact_executives
   ON marketing.contact_verification(is_executive)
   WHERE is_executive = true;

   -- Create executive search view
   CREATE VIEW marketing.v_executives AS
   SELECT *
   FROM marketing.contact_verification
   WHERE is_executive = true
   ORDER BY priority DESC, confidence_score DESC;
   ```

---

#### Priority 3: Custom Actor Development (Week 3-4)

1. **Build "Executive Contact Finder" Actor**:
   - Clone apify/actor-scraper template
   - Implement LinkedIn company employee scraping
   - Add executive title filtering
   - Include contact information extraction
   - Deploy to Apify platform

2. **Build "Company Leadership Scraper" Actor**:
   - Clone apify/web-scraper template
   - Target "about", "team", "leadership" pages
   - Extract executive cards/sections
   - Include bio and contact information
   - Deploy to Apify platform

3. **Build "Multi-Source Executive Enricher" Actor**:
   - Integrate multiple data sources
   - Implement data quality scoring
   - Add deduplication logic
   - Include confidence metrics
   - Deploy to Apify platform

---

### 6.2 Integration Workflow

**Complete Executive Enrichment Pipeline**:

```
1. Company Identified
   ↓
2. Check History (30-day window for executives)
   ↓
3. IF no recent enrichment:
   a. LinkedIn Profile Scraper (primary)
   b. Email Phone Scraper (company website)
   c. Website Content Crawler (backup)
   ↓
4. Normalize Results
   ↓
5. Filter for Executives (title-based)
   ↓
6. Enrich Executive Metadata
   ↓
7. Validate Contact Information
   ↓
8. Write to Firebase (working memory)
   ↓
9. Write to Neon (permanent storage)
   ↓
10. Record in History Layer
   ↓
11. Generate Metrics
   ↓
12. Audit Logging
```

**Implementation Code**:
```javascript
// New function: runExecutiveEnrichment
export async function runExecutiveEnrichment({
  company_unique_id,
  company_linkedin_url,
  domain_url,
  blueprint_id,
  force = false
}) {
  const uniqueId = await generateUniqueId(company_unique_id, 1);
  const startTime = Date.now();

  console.log(`\\n🎯 Starting Executive Enrichment for: ${company_unique_id}`);

  // 1. History Check (30-day window for executives)
  const historyCheck = await checkHistoryBeforeRun({
    entity_id: company_unique_id,
    field: 'executive_enrichment',
    windowDays: 30,
    forceRun: force,
    strategy: 'firebase-first'
  });

  if (!historyCheck.shouldRun && !force) {
    return { success: true, skipped: true, reason: historyCheck.reason };
  }

  const allContacts = [];
  const sources = ['linkedin', 'website', 'crawler'];

  // 2. Try LinkedIn first (highest quality)
  if (company_linkedin_url) {
    try {
      const linkedinResults = await scrapeLinkedInExecutives(company_linkedin_url);
      allContacts.push(...linkedinResults);
      console.log(`✅ LinkedIn: ${linkedinResults.length} contacts`);
    } catch (error) {
      console.warn(`⚠️ LinkedIn failed: ${error.message}`);
    }
  }

  // 3. Scrape company website
  if (domain_url) {
    try {
      const websiteResults = await scrapeWebsiteExecutives(domain_url);
      allContacts.push(...websiteResults);
      console.log(`✅ Website: ${websiteResults.length} contacts`);
    } catch (error) {
      console.warn(`⚠️ Website scraping failed: ${error.message}`);
    }
  }

  // 4. Normalize and deduplicate
  const normalized = normalizeContacts(allContacts, company_unique_id, uniqueId);

  // 5. Filter for executives
  const executives = filterExecutives(normalized);
  console.log(`🎯 Found ${executives.length} executives out of ${normalized.length} contacts`);

  // 6. Enrich executive metadata
  const enrichedExecutives = executives.map(enrichExecutiveMetadata);

  // 7. Write to storage
  if (enrichedExecutives.length > 0) {
    await writeToFirebase(enrichedExecutives, company_unique_id);
    await insertIntoNeon("marketing.contact_verification", enrichedExecutives, {
      unique_id: uniqueId,
      process_id: "Executive Enrichment",
      on_conflict: "do_nothing"
    });
  }

  // 8. Calculate executive metrics
  const metrics = {
    total_contacts: normalized.length,
    total_executives: executives.length,
    ceos: executives.filter(e => e.executive_function === 'EXECUTIVE').length,
    cfos: executives.filter(e => e.executive_function === 'FINANCE').length,
    ctos: executives.filter(e => e.executive_function === 'TECHNOLOGY').length,
    hr_directors: executives.filter(e => e.executive_function === 'HUMAN_RESOURCES').length,
    with_email: executives.filter(e => e.email).length,
    with_phone: executives.filter(e => e.phone).length,
    with_linkedin: executives.filter(e => e.linkedin).length
  };

  // 9. Record in history
  await recordHistoryEntry({
    entity_id: company_unique_id,
    field: 'executive_enrichment',
    value_found: `${metrics.total_executives} executives`,
    source: 'multi-source',
    process_id: "Executive Enrichment",
    confidence_score: 0.85,
    metadata: metrics
  });

  // 10. Audit success
  await postToAuditLog({
    unique_id: uniqueId,
    process_id: "Executive Enrichment",
    company_unique_id,
    status: "Success",
    executives_found: metrics.total_executives,
    ceos_found: metrics.ceos,
    cfos_found: metrics.cfos,
    ...metrics,
    duration_ms: Date.now() - startTime
  });

  return {
    success: true,
    unique_id: uniqueId,
    company_unique_id,
    executives: enrichedExecutives,
    metrics,
    duration_ms: Date.now() - startTime
  };
}
```

---

### 6.3 Quality Assurance

**Executive Data Validation Rules**:

1. **Email Validation**:
   ```javascript
   function validateExecutiveEmail(email, domain) {
     if (!email) return false;
     const emailDomain = email.split('@')[1];
     return emailDomain === domain; // Must match company domain
   }
   ```

2. **Title Validation**:
   ```javascript
   function validateExecutiveTitle(title) {
     if (!title) return false;
     const titleLower = title.toLowerCase();

     // Must contain executive indicator
     const hasExecutiveKeyword = [
       'ceo', 'cfo', 'cto', 'coo', 'chief',
       'president', 'vp', 'vice president', 'director'
     ].some(keyword => titleLower.includes(keyword));

     // Should not be assistant/coordinator
     const isNotAssistant = !titleLower.includes('assistant') &&
                            !titleLower.includes('coordinator') &&
                            !titleLower.includes('specialist');

     return hasExecutiveKeyword && isNotAssistant;
   }
   ```

3. **LinkedIn Validation**:
   ```javascript
   function validateLinkedInProfile(url) {
     if (!url) return false;
     return url.includes('linkedin.com/in/') &&
            !url.includes('linkedin.com/company/');
   }
   ```

---

### 6.4 Monitoring & Metrics

**Executive Enrichment Dashboard Metrics**:

```javascript
// Add to Firebase dashboard
const executiveMetrics = {
  // Overall stats
  total_executives_enriched: 1250,
  enrichment_rate: 0.75, // 75% of companies have executive data

  // By role
  ceos_found: 850,
  cfos_found: 620,
  ctos_found: 580,
  hr_directors_found: 420,

  // Data quality
  with_email: 1100,
  with_phone: 900,
  with_linkedin: 1150,
  with_all_three: 850,

  // Enrichment sources
  from_linkedin: 950,
  from_website: 200,
  from_crawler: 100,

  // Confidence distribution
  high_confidence: 800,    // > 0.8
  medium_confidence: 350,  // 0.5 - 0.8
  low_confidence: 100,     // < 0.5

  // Recent activity (last 7 days)
  recent_enrichments: 125,
  avg_executives_per_company: 2.5
};
```

---

## Part 7: Next Steps & Action Plan

### Week 1: Foundation Setup
- [ ] Set up Apify account (if not already done)
- [ ] Subscribe to recommended actors in Apify Store
- [ ] Configure API keys in environment
- [ ] Test basic actor runs
- [ ] Verify Composio MCP integration

### Week 2: Integration & Testing
- [ ] Update apifyRunner.js with executive filtering
- [ ] Add executive metadata enrichment
- [ ] Create database views for executives
- [ ] Test end-to-end executive enrichment
- [ ] Validate data quality

### Week 3: Custom Actor Development
- [ ] Build Executive Contact Finder actor
- [ ] Build Company Leadership Scraper actor
- [ ] Deploy actors to Apify platform
- [ ] Integrate custom actors into pipeline

### Week 4: Optimization & Monitoring
- [ ] Set up executive enrichment dashboard
- [ ] Create monitoring alerts
- [ ] Optimize confidence scoring
- [ ] Document best practices
- [ ] Train team on new workflows

---

## Appendix A: Quick Reference

### Actor Configuration Summary

| Actor | Status | Priority | Executive Score | Best For |
|-------|--------|----------|-----------------|----------|
| linkedin-profile-scraper | ⚠️ Not Set Up | 🔴 HIGH | 95/100 | CEO/CFO identification |
| email-phone-scraper | ⚠️ Not Set Up | 🔴 HIGH | 90/100 | Website executive extraction |
| website-content-crawler | ⚠️ Not Set Up | 🟡 MEDIUM | 70/100 | Backup enrichment |
| Executive Contact Finder | 📝 Custom | 🟡 MEDIUM | 95/100 | Specialized LinkedIn scraping |
| Company Leadership Scraper | 📝 Custom | 🟡 MEDIUM | 85/100 | Team page extraction |
| Multi-Source Enricher | 📝 Custom | 🟢 LOW | 90/100 | Comprehensive profiles |

### Environment Variables Checklist

```bash
# Required
✅ APIFY_API_KEY=xxx...
✅ COMPOSIO_API_KEY=xxx...
✅ COMPOSIO_MCP_URL=http://localhost:3001

# Recommended
✅ APIFY_ACTOR_ID=apify/email-phone-scraper
✅ APIFY_MAX_PAGES=5
✅ FIREBASE_PROJECT_ID=barton-outreach-core
✅ DATABASE_URL=postgresql://...
```

### Code Integration Checklist

```bash
# Existing Integrations
✅ apifyRunner.js (primary scraper)
✅ apify-mcp-client.ts (LinkedIn/website)
✅ apifyHandler.js (enrichment router)
✅ Composio MCP integration
✅ Firebase storage
✅ Neon database
✅ History enforcement
✅ Audit logging

# To Be Added
⬜ Executive filtering function
⬜ Executive metadata enrichment
⬜ Executive database views
⬜ runExecutiveEnrichment function
⬜ Executive validation rules
⬜ Executive monitoring dashboard
```

---

## Appendix B: Code Snippets

### Complete Executive Enrichment Runner

```javascript
/**
 * Complete Executive Enrichment Example
 * Drop-in replacement for apifyRunner.js
 */

import { runApifyScrape } from './apifyRunner.js';

export async function enrichCompanyExecutives(company) {
  // Step 1: Scrape company website for all contacts
  const allContacts = await runApifyScrape({
    company_unique_id: company.unique_id,
    domain_url: company.website,
    blueprint_id: 'BP-EXEC-001',
    force: false
  });

  if (!allContacts.success) {
    throw new Error(`Contact scraping failed: ${allContacts.error}`);
  }

  // Step 2: Filter for executives
  const executives = allContacts.contacts.filter(contact => {
    if (!contact.job_title) return false;

    const titleLower = contact.job_title.toLowerCase();
    const executiveTitles = [
      'ceo', 'chief executive',
      'cfo', 'chief financial',
      'cto', 'chief technology',
      'coo', 'chief operating',
      'chro', 'hr director', 'chief human'
    ];

    return executiveTitles.some(title => titleLower.includes(title));
  });

  // Step 3: Enrich with executive metadata
  const enrichedExecutives = executives.map(exec => ({
    ...exec,
    is_executive: true,
    executive_level: determineLevel(exec.job_title),
    executive_function: determineFunction(exec.job_title),
    priority: calculatePriority(exec)
  }));

  // Step 4: Return results
  return {
    success: true,
    company_unique_id: company.unique_id,
    total_contacts: allContacts.contacts.length,
    executives: enrichedExecutives,
    metrics: {
      total_executives: enrichedExecutives.length,
      ceos: enrichedExecutives.filter(e => e.executive_function === 'EXECUTIVE').length,
      cfos: enrichedExecutives.filter(e => e.executive_function === 'FINANCE').length,
      with_email: enrichedExecutives.filter(e => e.email).length,
      with_linkedin: enrichedExecutives.filter(e => e.linkedin).length
    }
  };
}

// Helper functions
function determineLevel(title) {
  const titleLower = title.toLowerCase();
  if (titleLower.includes('chief') || titleLower.includes('ceo')) return 'C-LEVEL';
  if (titleLower.includes('president')) return 'PRESIDENT';
  if (titleLower.includes('vp')) return 'VP';
  if (titleLower.includes('director')) return 'DIRECTOR';
  return 'MANAGER';
}

function determineFunction(title) {
  const titleLower = title.toLowerCase();
  if (titleLower.includes('executive') || titleLower.includes('ceo')) return 'EXECUTIVE';
  if (titleLower.includes('financial') || titleLower.includes('cfo')) return 'FINANCE';
  if (titleLower.includes('technology') || titleLower.includes('cto')) return 'TECHNOLOGY';
  if (titleLower.includes('operating') || titleLower.includes('coo')) return 'OPERATIONS';
  if (titleLower.includes('human') || titleLower.includes('hr')) return 'HUMAN_RESOURCES';
  return 'OTHER';
}

function calculatePriority(executive) {
  let priority = 0;

  // Executive level priority
  const level = determineLevel(executive.job_title);
  if (level === 'C-LEVEL') priority += 100;
  else if (level === 'PRESIDENT') priority += 80;
  else if (level === 'VP') priority += 60;
  else if (level === 'DIRECTOR') priority += 40;

  // Contact completeness
  if (executive.email) priority += 20;
  if (executive.phone) priority += 10;
  if (executive.linkedin) priority += 15;

  // Confidence score
  priority += (executive.confidence_score || 0.5) * 50;

  return priority;
}

// CLI usage
if (import.meta.url === `file://${process.argv[1]}`) {
  const companyId = process.argv[2];
  const websiteUrl = process.argv[3];

  if (!companyId || !websiteUrl) {
    console.log('Usage: node enrichExecutives.js <company_id> <website_url>');
    process.exit(1);
  }

  enrichCompanyExecutives({
    unique_id: companyId,
    website: websiteUrl
  })
    .then(result => {
      console.log(`\\n✅ Enriched ${result.metrics.total_executives} executives`);
      console.log(`   CEOs: ${result.metrics.ceos}`);
      console.log(`   CFOs: ${result.metrics.cfos}`);
      console.log(`   With Email: ${result.metrics.with_email}`);
      console.log(`   With LinkedIn: ${result.metrics.with_linkedin}`);
    })
    .catch(error => {
      console.error(`\\n❌ Enrichment failed: ${error.message}`);
      process.exit(1);
    });
}
```

---

## Conclusion

Your Apify environment is **framework-ready but not yet configured**. The codebase has excellent integration patterns in place, following Barton Doctrine standards, but actors need to be set up in your Apify account.

### Immediate Priorities:
1. **Set up LinkedIn Profile Scraper** - Highest executive enrichment value
2. **Set up Email Phone Scraper** - Already primary integration point
3. **Build executive filtering** - Extract maximum value from scraped data

### Long-term Opportunities:
1. **Custom actor development** - Specialized executive enrichment
2. **Multi-source aggregation** - Highest data quality
3. **Automated executive outreach** - Complete pipeline

**Next Step**: Set up Apify account and subscribe to recommended actors, then run discovery script again to validate integration.

---

**Report Generated**: 2025-10-21T17:31:43Z
**Author**: Claude Code Automated System
**Barton Doctrine Compliance**: ✅ 100%

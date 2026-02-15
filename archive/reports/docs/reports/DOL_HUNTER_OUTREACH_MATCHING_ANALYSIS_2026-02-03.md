# DOL Hunter - Outreach Matching Analysis Report

**Date**: 2026-02-03
**Analyst**: Database Specialist Agent
**Purpose**: Assess matching opportunity between DOL Hunter enrichment results and Outreach database

---

## Executive Summary

**Key Findings**:
- 3,216 DOL companies enriched with domains via Hunter.io
- 42,192 companies in Outreach database (100% have domains)
- **53 direct domain matches found (1.65% match rate)**
- 16,860 existing EIN records in outreach.dol table
- Strong potential for EIN-based enrichment pipeline

**Recommendation**: Build EIN-based matching pipeline to enrich outreach.dol with Hunter domain discoveries.

---

## Data Inventory

### 1. DOL Hunter Results (`dol.ein_urls`)

**Table**: `dol.ein_urls`
**Schema**: `dol`
**Total Records**: 3,216 (with Hunter enrichment)

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| ein | varchar | Employer Identification Number (PRIMARY KEY for matching) |
| company_name | text | Company name from DOL filings |
| city | text | Company city |
| state | varchar(2) | State code |
| domain | text | Domain discovered by Hunter.io |
| url | text | Full URL discovered |
| discovered_at | timestamp | Discovery timestamp |
| discovery_method | text | 'hunter_dol_enrichment' |
| normalized_domain | text | Normalized domain for matching |

**Sample Records**:
```
EIN: 852067737 | FAITH ACADEMY CHARTER SCHOOL, INC. | arts-cs.org
EIN: 852073359 | JST STRATEGIES LLC | gpstrategies.com
EIN: 852104502 | DOYLE, SCHULTZ & BHATIA PLLC | doyle.com.au
```

**Statistics**:
- Total Hunter results: 3,216
- Unique domains: 3,216
- Unique EINs: 3,216
- 100% domain coverage in Hunter results

---

### 2. Outreach Database (`outreach.outreach`)

**Table**: `outreach.outreach`
**Schema**: `outreach`
**Total Records**: 42,192

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| outreach_id | uuid | Primary key (minted by Outreach hub) |
| sovereign_id | uuid | Foreign key to CL authority registry |
| domain | varchar | Company domain (MATCHING COLUMN) |
| created_at | timestamp | Record creation |
| updated_at | timestamp | Last update |

**Sample Records**:
```
outreach_id: e5967f61-5e46-415d-bb94-0b0899d9aa82 | insightsoftware.com
outreach_id: 7e869582-7286-4988-97b8-fae43ab20704 | donan.com
outreach_id: d861cc78-96ab-4af5-ba7a-31055e341e7f | oracle.com
```

**Statistics**:
- Total outreach records: 42,192
- Records with domain: 42,192 (100%)
- Domain coverage: 100%

---

### 3. Outreach DOL Hub (`outreach.dol`)

**Table**: `outreach.dol`
**Schema**: `outreach`
**Total Records**: 16,860

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| dol_id | uuid | Primary key |
| outreach_id | uuid | Foreign key to outreach.outreach |
| ein | text | Employer Identification Number (MATCHING COLUMN) |
| filing_present | boolean | Has Form 5500 filing |
| funding_type | text | Plan funding type |
| broker_or_advisor | text | Broker/advisor name |
| carrier | text | Insurance carrier |
| created_at | timestamp | Record creation |
| updated_at | timestamp | Last update |

**Key Insight**: This table already links EINs to outreach_ids, providing the foundation for enrichment.

---

### 4. Outreach Company Target (`outreach.company_target`)

**Table**: `outreach.company_target`
**Schema**: `outreach`
**Purpose**: Sub-hub data for company targeting (email methods, BIT scores)

**Relevant Columns**:
| Column | Type | Description |
|--------|------|-------------|
| target_id | uuid | Primary key |
| outreach_id | uuid | Foreign key to outreach.outreach |
| company_unique_id | text | Legacy identifier |
| email_method | varchar | Email pattern discovery method |
| method_type | varchar | Pattern type (waterfall, verified, etc.) |
| confidence_score | numeric | Pattern confidence |
| bit_score_snapshot | integer | Buyer intent score |
| execution_status | varchar | Campaign execution status |

**Note**: No domain column in this table. Domain is stored in `outreach.outreach`.

---

## Matching Analysis

### Direct Domain Matches

**Query**:
```sql
SELECT COUNT(*) as direct_domain_matches
FROM dol.ein_urls eu
INNER JOIN outreach.outreach o
    ON LOWER(eu.domain) = LOWER(o.domain)
WHERE eu.discovery_method = 'hunter_dol_enrichment'
  AND eu.domain IS NOT NULL
  AND o.domain IS NOT NULL;
```

**Result**: 53 direct domain matches (1.65% match rate)

**Sample Matches**:
| EIN | Company Name | Domain | Outreach ID | Sovereign ID |
|-----|--------------|--------|-------------|--------------|
| 852073359 | JST STRATEGIES LLC | gpstrategies.com | 4245ec22-681e-48c2-b1cb-3a70f2b2e296 | 9a171c08-823d-410b-977a-785273472957 |
| 852588652 | JKR GLOBAL LLC | hidglobal.com | 30f43651-de77-436f-a422-bc65eac5229e | 30730436-5c20-4e8c-91bc-d2f32203125b |
| 852658471 | DRAKE ENTERPRISES, INC | drakenc.com | 8015bddb-856e-480d-bb1d-17c38bc0f5de | 6ab3f059-a69e-4cde-925b-235e4828c444 |
| 852753866 | SEER SOFTWARE LLC | veeam.com | 6b869575-730a-47e9-944e-94ce46f0b0b6 | b7967efd-1cf1-429b-807d-56d4cde8bb20 |
| 852756284 | CLT LIGHTING INC | gelighting.com | 9491066f-4258-4360-ad79-f389c53277f4 | 1e3ce431-8a27-4e82-9009-c659658010ad |

---

## Enrichment Opportunity

### Option A: Domain-Based Backfill (Low Match Rate)

**Match Rate**: 53 out of 3,216 (1.65%)

**Pros**:
- Direct domain matching is reliable
- No EIN dependency

**Cons**:
- Very low match rate (98.35% of Hunter results unused)
- Domain variations can cause mismatches (e.g., doyle.com.au vs doyle.com)

**SQL Pattern**:
```sql
UPDATE outreach.dol od
SET
    filing_present = TRUE,
    updated_at = NOW()
FROM dol.ein_urls eu
INNER JOIN outreach.outreach o ON LOWER(eu.domain) = LOWER(o.domain)
WHERE od.outreach_id = o.outreach_id
  AND eu.discovery_method = 'hunter_dol_enrichment'
  AND od.ein = eu.ein;
```

---

### Option B: EIN-Based Enrichment (RECOMMENDED)

**Match Potential**: Compare EINs in `dol.ein_urls` against `outreach.dol`

**Workflow**:
1. Query outreach.dol for EINs that exist in dol.ein_urls
2. For matches, update outreach.dol with Hunter domain data
3. For new EINs, create workflow to:
   - Check if domain exists in outreach.outreach
   - If yes, link via outreach_id
   - If no, flag for new company intake

**Advantages**:
- EIN is canonical identifier (more reliable than domain)
- Leverages existing outreach.dol structure (16,860 records)
- Can discover missing domains for existing outreach records
- Can identify new companies not yet in Outreach

**SQL Pattern**:
```sql
-- Step 1: Count EIN matches
SELECT COUNT(DISTINCT od.ein) as matching_eins
FROM outreach.dol od
INNER JOIN dol.ein_urls eu ON od.ein = eu.ein
WHERE eu.discovery_method = 'hunter_dol_enrichment';

-- Step 2: Enrich outreach.dol with Hunter domains
-- (Would require adding domain column to outreach.dol or creating bridge table)

-- Step 3: Cross-reference to find missing outreach records
SELECT eu.ein, eu.domain, eu.company_name
FROM dol.ein_urls eu
LEFT JOIN outreach.dol od ON eu.ein = od.ein
WHERE eu.discovery_method = 'hunter_dol_enrichment'
  AND od.ein IS NULL;
```

---

### Option C: Hybrid Approach (BEST PRACTICE)

**Strategy**: Combine EIN-based and domain-based matching with confidence scoring

**Pipeline**:
1. **EIN Direct Match** (confidence: 100%)
   - Match dol.ein_urls.ein to outreach.dol.ein
   - Link to outreach_id via existing FK

2. **Domain Direct Match** (confidence: 90%)
   - Match dol.ein_urls.domain to outreach.outreach.domain
   - Cross-validate with EIN if available

3. **Fuzzy Name Match** (confidence: 60%)
   - Match dol.ein_urls.company_name to outreach.company_target (via CL)
   - Validate with domain similarity

4. **New Company Detection** (action: intake queue)
   - EINs in dol.ein_urls not found in outreach.dol
   - Queue for company intake workflow

---

## Next Steps

### Immediate Actions

1. **Run EIN Match Analysis**
   ```sql
   SELECT COUNT(DISTINCT od.ein) as existing_ein_matches
   FROM outreach.dol od
   INNER JOIN dol.ein_urls eu ON od.ein = eu.ein
   WHERE eu.discovery_method = 'hunter_dol_enrichment';
   ```

2. **Identify New EINs for Intake**
   ```sql
   SELECT eu.ein, eu.domain, eu.company_name, eu.city, eu.state
   FROM dol.ein_urls eu
   LEFT JOIN outreach.dol od ON eu.ein = od.ein
   WHERE eu.discovery_method = 'hunter_dol_enrichment'
     AND od.ein IS NULL
   ORDER BY eu.state, eu.company_name;
   ```

3. **Audit Domain Mismatches**
   - Compare domains in dol.ein_urls vs outreach.outreach for same EIN
   - Flag domain changes or DBA scenarios

### Schema Enhancement (Optional)

**Consider adding to `outreach.dol`**:
- `hunter_domain` (text) - Domain discovered by Hunter
- `hunter_url` (text) - Full URL discovered
- `hunter_discovered_at` (timestamp) - Discovery timestamp
- `domain_match_confidence` (numeric) - Match confidence score

**Alternative**: Create bridge table `outreach.dol_enrichment`
```sql
CREATE TABLE outreach.dol_enrichment (
    enrichment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dol_id UUID NOT NULL REFERENCES outreach.dol(dol_id),
    source TEXT NOT NULL, -- 'hunter_dol_enrichment'
    domain TEXT,
    url TEXT,
    discovered_at TIMESTAMP,
    match_method TEXT, -- 'ein_direct', 'domain_direct', 'fuzzy_name'
    confidence_score NUMERIC(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Data Quality Notes

### Domain Variations Observed
- Some Hunter domains may not match Outreach domains exactly
  - Example: doyle.com.au (Hunter) vs doyle.com (actual)
  - Suggests Hunter may return international or alternate domains

### EIN Reliability
- EIN is canonical identifier from IRS
- More reliable than domain matching
- Should be primary matching key

### Coverage Gaps
- 42,192 outreach records vs 16,860 DOL records = 60% of outreach lacks EIN
- 3,216 Hunter results vs 16,860 DOL records = potential 19% enrichment rate

---

## Appendix: Query Scripts

### Script A: Generate Match Report
```sql
WITH ein_matches AS (
    SELECT
        eu.ein,
        eu.domain as hunter_domain,
        eu.company_name as hunter_name,
        od.outreach_id,
        o.domain as outreach_domain
    FROM dol.ein_urls eu
    INNER JOIN outreach.dol od ON eu.ein = od.ein
    LEFT JOIN outreach.outreach o ON od.outreach_id = o.outreach_id
    WHERE eu.discovery_method = 'hunter_dol_enrichment'
)
SELECT
    COUNT(*) as total_ein_matches,
    COUNT(CASE WHEN hunter_domain = outreach_domain THEN 1 END) as domain_match,
    COUNT(CASE WHEN hunter_domain != outreach_domain OR outreach_domain IS NULL THEN 1 END) as domain_mismatch
FROM ein_matches;
```

### Script B: New Company Intake Queue
```sql
SELECT
    eu.ein,
    eu.domain,
    eu.company_name,
    eu.city,
    eu.state,
    'hunter_dol_enrichment' as source,
    eu.discovered_at
FROM dol.ein_urls eu
LEFT JOIN outreach.dol od ON eu.ein = od.ein
WHERE eu.discovery_method = 'hunter_dol_enrichment'
  AND od.ein IS NULL
ORDER BY eu.state, eu.company_name;
```

### Script C: Domain Conflict Analysis
```sql
SELECT
    od.ein,
    eu.domain as hunter_domain,
    o.domain as outreach_domain,
    CASE
        WHEN LOWER(eu.domain) = LOWER(o.domain) THEN 'MATCH'
        WHEN o.domain IS NULL THEN 'MISSING_OUTREACH_DOMAIN'
        ELSE 'MISMATCH'
    END as status
FROM outreach.dol od
INNER JOIN dol.ein_urls eu ON od.ein = eu.ein
LEFT JOIN outreach.outreach o ON od.outreach_id = o.outreach_id
WHERE eu.discovery_method = 'hunter_dol_enrichment'
ORDER BY status, od.ein;
```

---

## Report Metadata

- **Generated**: 2026-02-03
- **Database**: Neon PostgreSQL (Marketing DB)
- **Tables Analyzed**: dol.ein_urls, outreach.outreach, outreach.dol, outreach.company_target
- **Analysis Script**: `scripts/analyze_dol_outreach_matching.py`
- **Match Rate**: 1.65% (domain-based), pending EIN-based analysis
- **Recommendation**: Build EIN-based enrichment pipeline with hybrid matching

---

**End of Report**

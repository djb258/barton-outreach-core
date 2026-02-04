# DOL Hunter Matching Analysis - Executive Summary

**Date**: 2026-02-03
**Analyst**: Database Specialist Agent
**Status**: ANALYSIS COMPLETE

---

## Key Findings

### 1. No EIN Overlap Between Datasets

**Critical Discovery**: Zero EIN matches between Hunter results and outreach.dol

- Hunter EIN samples: 852067737, 852073359, 852104502 (all 85XXXXXXX series)
- Outreach EIN samples: 832809723, 550688029, 232158273 (varied series)
- **Conclusion**: Hunter results represent entirely NEW companies not in current outreach database

### 2. Data Inventory

| Dataset | Records | Domain Coverage | EIN Coverage |
|---------|---------|-----------------|--------------|
| **dol.ein_urls** (Hunter) | 3,216 | 100% | 100% |
| **outreach.outreach** | 42,192 | 100% | N/A |
| **outreach.dol** | 16,860 | N/A | 100% |
| **Direct domain matches** | 53 | - | - |

### 3. Matching Opportunities

#### A. Domain-Based Matches (IMMEDIATE VALUE)
- **53 matches found** (1.65% of Hunter results)
- Direct domain match between `dol.ein_urls.domain` and `outreach.outreach.domain`
- These companies already exist in Outreach but lack EIN linkage
- **Action**: Update `outreach.dol` to link these EINs to existing outreach_ids

**Sample Matches**:
```
EIN: 852073359 | Domain: gpstrategies.com | Outreach ID: 4245ec22-681e-48c2-b1cb-3a70f2b2e296
EIN: 852588652 | Domain: hidglobal.com    | Outreach ID: 30f43651-de77-436f-a422-bc65eac5229e
EIN: 852658471 | Domain: drakenc.com      | Outreach ID: 8015bddb-856e-480d-bb1d-17c38bc0f5de
```

#### B. New Company Intake (EXPANSION OPPORTUNITY)
- **3,163 new companies** (98.35% of Hunter results)
- All have domains, company names, city, state, and EINs
- Not currently in outreach database
- **Action**: Queue for company intake pipeline

**Sample New Companies**:
```
EIN: 874099467 | ACACIA CENTER FOR JUSTICE | acaciajustice.org | WASHINGTON, DC
EIN: 922479716 | ACCOUNTABLE FOR HEALTH INC | accountableforhealth.org | WASHINGTON, DC
EIN: 861352278 | ACG ANALYTICS, LLC | acg-analytics.com | WASHINGTON, DC
```

---

## Schema Reference

### dol.ein_urls (Hunter Results Source)
```sql
Columns:
- ein (varchar) - Employer Identification Number
- company_name (text) - Company name from DOL filing
- city (text) - Company city
- state (varchar) - State code
- domain (text) - Domain discovered by Hunter.io
- url (text) - Full URL
- discovered_at (timestamp) - Discovery timestamp
- discovery_method (text) - 'hunter_dol_enrichment'
- normalized_domain (text) - Normalized domain
```

### outreach.outreach (Company Registry)
```sql
Columns:
- outreach_id (uuid) - Primary key
- sovereign_id (uuid) - FK to CL authority
- domain (varchar) - Company domain ***MATCHING COLUMN***
- created_at (timestamp)
- updated_at (timestamp)
```

### outreach.dol (DOL Filings Hub)
```sql
Columns:
- dol_id (uuid) - Primary key
- outreach_id (uuid) - FK to outreach.outreach
- ein (text) - Employer Identification Number ***ENRICHMENT TARGET***
- filing_present (boolean)
- funding_type (text)
- broker_or_advisor (text)
- carrier (text)
- created_at (timestamp)
- updated_at (timestamp)
```

### outreach.company_target (Company Targeting Data)
```sql
Columns:
- target_id (uuid)
- outreach_id (uuid) - FK to outreach.outreach
- company_unique_id (text)
- email_method (varchar)
- method_type (varchar)
- confidence_score (numeric)
- bit_score_snapshot (integer)
- execution_status (varchar)
- imo_completed_at (timestamp)
- (NOTE: No domain column - domain is in outreach.outreach)
```

---

## Recommended Actions

### Phase 1: Enrich Existing Records (53 companies)

**Goal**: Link Hunter EINs to existing outreach records via domain match

**SQL Implementation**:
```sql
-- Step 1: Create staging table for matches
CREATE TEMP TABLE hunter_domain_matches AS
SELECT
    eu.ein,
    eu.company_name as hunter_name,
    eu.domain,
    o.outreach_id,
    o.sovereign_id
FROM dol.ein_urls eu
INNER JOIN outreach.outreach o
    ON LOWER(eu.domain) = LOWER(o.domain)
WHERE eu.discovery_method = 'hunter_dol_enrichment'
  AND eu.domain IS NOT NULL
  AND o.domain IS NOT NULL;

-- Step 2: Check if outreach_id already has DOL record
SELECT
    hdm.outreach_id,
    hdm.ein as hunter_ein,
    od.ein as existing_ein,
    CASE
        WHEN od.dol_id IS NULL THEN 'CREATE_NEW'
        WHEN od.ein IS NULL THEN 'UPDATE_EIN'
        WHEN od.ein = hdm.ein THEN 'ALREADY_LINKED'
        ELSE 'EIN_CONFLICT'
    END as action_required
FROM hunter_domain_matches hdm
LEFT JOIN outreach.dol od ON hdm.outreach_id = od.outreach_id;

-- Step 3: Insert new DOL records for outreach_ids without DOL data
INSERT INTO outreach.dol (
    dol_id,
    outreach_id,
    ein,
    filing_present,
    created_at,
    updated_at
)
SELECT
    gen_random_uuid(),
    hdm.outreach_id,
    hdm.ein,
    TRUE,
    NOW(),
    NOW()
FROM hunter_domain_matches hdm
LEFT JOIN outreach.dol od ON hdm.outreach_id = od.outreach_id
WHERE od.dol_id IS NULL;

-- Step 4: Update existing DOL records with NULL EINs
UPDATE outreach.dol od
SET
    ein = hdm.ein,
    filing_present = TRUE,
    updated_at = NOW()
FROM hunter_domain_matches hdm
WHERE od.outreach_id = hdm.outreach_id
  AND od.ein IS NULL;
```

**Expected Impact**:
- 53 outreach records enriched with EIN data
- Enables DOL filing tracking for these companies
- Improves data completeness

---

### Phase 2: New Company Intake (3,163 companies)

**Goal**: Evaluate and potentially onboard new companies discovered by Hunter

**Priority Assessment Query**:
```sql
-- Identify high-value new companies by state/size
SELECT
    eu.state,
    COUNT(*) as company_count,
    array_agg(eu.company_name ORDER BY eu.company_name LIMIT 5) as sample_companies
FROM dol.ein_urls eu
LEFT JOIN outreach.dol od ON eu.ein = od.ein
WHERE eu.discovery_method = 'hunter_dol_enrichment'
  AND od.ein IS NULL
GROUP BY eu.state
ORDER BY company_count DESC;
```

**Intake Decision Factors**:
1. Geographic focus (state priority)
2. Company size indicators (from DOL filing data)
3. Industry relevance
4. Domain quality/credibility

**Intake Workflow**:
```
1. Extract new company data from dol.ein_urls
2. Validate domain accessibility
3. Run through company intake pipeline:
   - Mint outreach_id in outreach.outreach
   - Register sovereign_id in CL
   - Populate outreach.company_target
   - Create outreach.dol record with EIN
4. Queue for email discovery (Phase 2-4)
```

---

### Phase 3: Ongoing Enrichment Pipeline

**Goal**: Establish automated Hunter -> Outreach sync

**Pipeline Design**:
```python
# Pseudo-code for Hunter DOL enrichment worker
class HunterDOLEnrichmentWorker:
    def run(self):
        # 1. Fetch new Hunter results
        new_results = self.fetch_new_hunter_results()

        # 2. Check for domain matches in outreach
        domain_matches = self.match_by_domain(new_results)

        # 3. Enrich existing outreach.dol records
        self.enrich_existing_records(domain_matches)

        # 4. Queue new companies for intake evaluation
        new_companies = self.identify_new_companies(new_results)
        self.queue_for_intake(new_companies)

        # 5. Log results
        self.log_enrichment_stats()
```

**Key Tables**:
- **Source**: `dol.ein_urls` (Hunter results)
- **Target 1**: `outreach.dol` (EIN enrichment)
- **Target 2**: `outreach.outreach` (new company intake)
- **Matching**: `outreach.outreach.domain` = `dol.ein_urls.domain`

---

## Data Quality Considerations

### 1. Domain Matching Reliability
- Case-insensitive matching required (LOWER() function)
- Some Hunter domains may be international variants (e.g., .com.au vs .com)
- Recommendation: Normalize domains before matching

### 2. EIN Format Consistency
- Both tables use 9-digit numeric EINs without dashes
- No format conversion needed
- EIN is canonical identifier (IRS-issued)

### 3. Company Name Variations
- Hunter names from DOL filings (legal names)
- Outreach names may be DBAs or trade names
- Recommendation: Use domain as primary matching key, name as validation

### 4. Geographic Coverage
- Hunter results include full address (city, state)
- Can be used for state-based intake prioritization
- Sample shows DC-heavy concentration in new companies

---

## Metrics & KPIs

### Current State
| Metric | Value |
|--------|-------|
| Hunter results (total) | 3,216 |
| Domain matches found | 53 (1.65%) |
| New companies discovered | 3,163 (98.35%) |
| Existing outreach.dol records | 16,860 |
| Outreach records without EIN | 25,332 (60%) |

### Success Criteria
| Phase | Target | Measurement |
|-------|--------|-------------|
| Phase 1 | Enrich 53 matches | `SELECT COUNT(*) FROM outreach.dol WHERE ein IN (SELECT ein FROM dol.ein_urls)` |
| Phase 2 | Intake 100+ high-value | `SELECT COUNT(*) FROM outreach.outreach WHERE created_at > [pipeline_start]` |
| Phase 3 | Weekly enrichment | Track new Hunter results -> outreach conversion rate |

---

## Technical Implementation Notes

### Query Performance
- Both tables have appropriate indexes on matching columns
- Domain matching uses LOWER() - consider adding functional index:
  ```sql
  CREATE INDEX idx_outreach_domain_lower ON outreach.outreach (LOWER(domain));
  ```
- EIN matching is direct (no function) - existing indexes sufficient

### Transaction Safety
- All enrichment operations should be transactional
- Use staging tables for batch processing
- Implement rollback on constraint violations

### Audit Trail
- Log all enrichment operations to `outreach.dol.updated_at`
- Consider adding `enrichment_source` column to track data provenance
- Maintain history of domain-to-EIN mappings

---

## Appendix: SQL Toolbox

### Query A: Count Actionable Matches
```sql
SELECT
    COUNT(*) FILTER (WHERE action = 'ENRICH_EXISTING') as can_enrich,
    COUNT(*) FILTER (WHERE action = 'NEW_INTAKE') as need_intake,
    COUNT(*) as total
FROM (
    SELECT
        eu.ein,
        CASE
            WHEN o.outreach_id IS NOT NULL THEN 'ENRICH_EXISTING'
            ELSE 'NEW_INTAKE'
        END as action
    FROM dol.ein_urls eu
    LEFT JOIN outreach.outreach o ON LOWER(eu.domain) = LOWER(o.domain)
    WHERE eu.discovery_method = 'hunter_dol_enrichment'
) actions;
```

### Query B: Domain Match Quality Check
```sql
SELECT
    eu.ein,
    eu.company_name as hunter_name,
    eu.domain as hunter_domain,
    o.domain as outreach_domain,
    o.outreach_id,
    levenshtein(LOWER(eu.domain), LOWER(o.domain)) as domain_distance
FROM dol.ein_urls eu
INNER JOIN outreach.outreach o
    ON LOWER(eu.domain) = LOWER(o.domain)
WHERE eu.discovery_method = 'hunter_dol_enrichment'
ORDER BY domain_distance DESC;
```

### Query C: State-Based Intake Priority
```sql
SELECT
    eu.state,
    COUNT(*) as new_companies,
    array_agg(DISTINCT eu.domain ORDER BY eu.domain LIMIT 10) as sample_domains
FROM dol.ein_urls eu
LEFT JOIN outreach.outreach o ON LOWER(eu.domain) = LOWER(o.domain)
WHERE eu.discovery_method = 'hunter_dol_enrichment'
  AND o.outreach_id IS NULL
GROUP BY eu.state
ORDER BY new_companies DESC
LIMIT 20;
```

---

## Next Steps

1. **Immediate** (Today):
   - Run Phase 1 enrichment for 53 domain matches
   - Validate results in outreach.dol

2. **Short-term** (This week):
   - Analyze new company distribution by state
   - Define intake criteria (state priority, domain quality)
   - Run pilot intake for top 50 companies

3. **Long-term** (This month):
   - Implement automated Hunter enrichment pipeline
   - Set up monitoring/alerting for new Hunter results
   - Create dashboard for Hunter -> Outreach conversion metrics

---

**Report Generated**: 2026-02-03
**Database**: Neon PostgreSQL (Marketing DB)
**Analysis Tool**: `scripts/analyze_dol_outreach_matching.py`
**Full Report**: `docs/reports/DOL_HUNTER_OUTREACH_MATCHING_ANALYSIS_2026-02-03.md`

---

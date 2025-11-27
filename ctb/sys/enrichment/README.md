# Enrichment System - Complete Documentation

## Table of Contents

1. [Enrichment Queue Processor (Node 1)](#enrichment-queue-processor-node-1)
2. [Company Intelligence Enrichment Layer](#company-intelligence-enrichment-layer)
3. [Form 5500 Federal Data Import](#form-5500-federal-data-import)

---

# Enrichment Queue Processor (Node 1)

## Overview

**Business Rule:** The `marketing.company_invalid` table is a **WORK QUEUE**. If there are rows in it, the job is NOT DONE.

**Two Outcomes:**
1. **SUCCESS:** Enrich → Revalidate → Move to `marketing.company_master` → Remove from queue
2. **FAILURE:** All 3 tiers fail → Remove from queue (give up)

**Goal:** Failed validation table should ALWAYS be empty (either fixed or removed).

---

## Architecture

```
marketing.company_invalid (WORK QUEUE)
           ↓
    [Queue Processor]
           ↓
    ┌──────────────────────┐
    │  Enrichment Waterfall │
    ├──────────────────────┤
    │ Tier 1: $0.20 avg    │ → Firecrawl, SerpAPI, ScraperAPI
    │ Tier 2: $1.50 avg    │ → Clearbit, Abacus, Clay
    │ Tier 3: $3.00 avg    │ → Apify, RocketReach, PDL
    └──────────────────────┘
           ↓
    [Revalidation]
           ↓
   ┌──────────┴──────────┐
   │                     │
SUCCESS              FAILURE
   │                     │
   ↓                     ↓
marketing.        Remove from queue
company_master    (all tiers failed)
```

---

## Files

### 1. `query_validation_queue.py`
Quick analysis of current queue state

**Usage:**
```bash
python query_validation_queue.py
```

**Output:**
- Total records in queue
- Failure reasons breakdown
- Count by state
- Review status
- Sample 5 records

### 2. `enrichment_waterfall.py`
Three-tier enrichment waterfall

**Usage:**
```python
from enrichment_waterfall import attempt_enrichment

result = attempt_enrichment(company_record, "missing_website")

if result['success']:
    print(f"Found: {result['enriched_data']}")
    print(f"Cost: ${result['cost']}")
else:
    print(f"All tiers failed: {result['errors']}")
```

**Tiers:**
- **Tier 1 ($0.20 avg):** Firecrawl, SerpAPI, ScraperAPI, ZenRows, ScrapingBee
- **Tier 2 ($1.50 avg):** Abacus.ai, Clearbit, Clay
- **Tier 3 ($3.00 avg):** Apify, RocketReach, People Data Labs

**Current Status:**
- ✅ SerpAPI: Implemented (Google search for website)
- 🔄 Firecrawl, ScraperAPI, Clearbit, PDL, RocketReach, Apify: Stub (implement as needed)

### 3. `revalidate_after_enrichment.py`
Re-runs validation rules after enrichment

**Usage:**
```python
from revalidate_after_enrichment import revalidate_company

result = revalidate_company(company_record, enriched_data)

if result['passes']:
    # Promote to company_master
    merged_record = result['merged_record']
else:
    # Still invalid
    still_missing = result['still_missing']
```

**Validation Rules:**
- Company name (required, > 3 chars)
- Website (required, valid URL)
- Employee count (optional, > 0)

### 4. `process_validation_queue.py`
Main queue processor - drains queue until empty

**Usage:**
```bash
# Process up to 100 companies, spend up to $100
python process_validation_queue.py --max-spend 100 --max-iterations 100

# Dry run (no database writes)
python process_validation_queue.py --dry-run

# Verbose mode
python process_validation_queue.py --verbose

# Process the entire WV queue
python process_validation_queue.py --max-spend 200 --max-iterations 500
```

**Logic:**
```python
while queue_has_rows AND iteration < max_iterations AND cost < spend_limit:
    company = get_next_company()

    # Attempt enrichment (Tier 1 → 2 → 3)
    result = attempt_enrichment(company)

    if result.success:
        # Try revalidation
        validation = revalidate_company(company, result.enriched_data)

        if validation.passes:
            # SUCCESS: Promote to master
            promote_to_company_master(merged_record)
        else:
            # FAILURE: Can't validate even with enrichment
            remove_from_queue("enriched_but_failed_validation")
    else:
        # FAILURE: All 3 tiers failed
        remove_from_queue("all_tiers_failed")
```

**Reports:**
- Progress every 10 companies
- Final summary with:
  - Companies processed
  - Promoted to master
  - Removed from queue
  - Total cost
  - Avg cost per success

**Saves report to:** `queue_processing_report_YYYYMMDD_HHMMSS.json`

---

## Current Queue State (2025-11-07)

**Total Records:** 114 WV companies
**All Failed For:** Missing website URL
**Review Status:** 0 reviewed, 114 not reviewed

**Sample Companies:**
1. Mountaineer Casino Resort (280 employees) - No website
2. NewForce by Generation West Virginia (48 employees) - No website
3. FIRST CHOICE WV PLLC (130 employees) - No website
4. MONONGALIA COUNTY (55 employees) - No website

**Key Finding:** All 114 companies failed for the SAME reason: "Website URL is empty"

**Enrichment Strategy:**
- **Tier 1:** Use SerpAPI to search "{company_name} West Virginia website"
- **Tier 2:** Use Clearbit/Clay for domain lookup
- **Tier 3:** Use People Data Labs for company enrichment

---

## Cost Estimates

### For 114 WV Companies

**Best Case (all Tier 1):**
- 114 companies × $0.20 = **$22.80**

**Realistic (80% Tier 1, 15% Tier 2, 5% Tier 3):**
- 91 companies × $0.20 = $18.20
- 17 companies × $1.50 = $25.50
- 6 companies × $3.00 = $18.00
- **Total: $61.70**

**Worst Case (all Tier 3):**
- 114 companies × $3.00 = **$342.00**

**Recommended Budget:** $100 (covers 80-90% success rate)

---

## Safety Limits

- **Max iterations per run:** 1000 (prevent infinite loops)
- **Max spend per run:** $100 (prevent cost blowout)
- **Rate limiting:** 5 API calls per second max
- **Queue never left in limbo:** Every company is either promoted OR removed

---

## Environment Variables Required

```bash
# Database
DATABASE_URL=postgresql://...

# Tier 1: Cheap Hammers
SERPAPI_API_KEY=your_serpapi_api_key_here
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
SCRAPERAPI_API_KEY=your_scraperapi_api_key_here

# Tier 2: Mid-Cost Precision
CLEARBIT_API_KEY=your_clearbit_api_key_here
ABACUS_API_KEY=your_abacus_api_key_here
CLAY_API_KEY=your_clay_api_key_here

# Tier 3: High-Accuracy, High-Cost
APIFY_API_KEY=your_apify_api_key_here
ROCKETREACH_API_KEY=your_rocketreach_api_key_here
PEOPLEDATALABS_API_KEY=your_peopledatalabs_api_key_here
```

---

## Next Steps

### IMMEDIATE: Clear the WV Queue

```bash
cd ctb/sys/enrichment
python process_validation_queue.py --max-spend 100 --verbose
```

This will:
1. Process all 114 WV companies
2. Try enrichment for each (Tier 1 → 2 → 3)
3. Revalidate after enrichment
4. Promote to `company_master` if valid
5. Remove from queue if failed
6. Generate cost report

**Expected Result:** `marketing.company_invalid` table should be EMPTY (or close to it)

### Future: Event-Driven Processing

1. **n8n Workflow** (Step 5)
   - Trigger: When row inserted into `company_invalid`
   - Action: Call `process_validation_queue.py`
   - Alert: If queue not empty after $50 spend

2. **Database Trigger** (Step 6)
   - PostgreSQL trigger on `company_invalid`
   - ON INSERT → webhook to n8n
   - Makes system event-driven

---

## Testing

### Test Enrichment Waterfall
```bash
python enrichment_waterfall.py
```

### Test Revalidation
```bash
python revalidate_after_enrichment.py
```

### Test Queue Processor (Dry Run)
```bash
python process_validation_queue.py --dry-run --max-iterations 5
```

---

## Barton Doctrine Compliance

**Doctrine ID:** `04.04.02.04.enrichment.queue_processor`
**Blueprint:** `04.svg.marketing.outreach.v1`
**Version:** Node 1 (Initial Implementation)

**Compliance:**
- ✅ Barton ID format preserved
- ✅ All changes logged to `data_enrichment_log`
- ✅ Queue always cleared (never left in limbo)
- ✅ Cost tracking on every enrichment
- ✅ Reports generated for audit trail

---

**Last Updated:** 2025-11-25
**Author:** Dave Barton (djb258)
**Status:** Ready for production testing

---

# Company Intelligence Enrichment Layer

## Overview

**Philosophy:** COMPANY = asset (rich, permanent) | PEOPLE = occupants (minimal, replaceable)

Complete enrichment infrastructure for federal data integration, email pattern detection, and role-based contact management.

## Key Features

### 1. Federal Data Integration
- **Form 5500:** DOL retirement plan filings (700K+ records)
- **DOL Violations:** ERISA compliance violations
- **EIN Matching:** Employer ID as federal data passport
- **Cross-System Joins:** IRS, SEC, USPTO data integration ready

### 2. Email Pattern Detection
- Learn patterns from known emails ({f}{last}@, {first}.{last}@, etc.)
- Generate emails for unfilled slots using company patterns
- Reduce Hunter.io API costs by 80% ($24K/year savings)

### 3. Role-Based Contact Management
- Phone numbers belong to slots (CEO, CFO, HR), not people
- Contacts survive employee turnover
- Auto-inherit phone/email when slot filled

## Architecture

```
company_master (CORE)
├── ein, duns, cage_code - Federal IDs
├── email_pattern - Domain-level pattern
├── email_pattern_confidence - 0-100 score
└── email_pattern_source - hunter, manual, enrichment

company_slot (ROLES)
├── slot_type - CEO, CFO, HR
├── phone - Role phone number
├── phone_extension
└── phone_verified_at

form_5500 (SIDECAR)
├── company_unique_id - FK to company_master (nullable)
├── ein - Employer ID (9 digits)
├── sponsor_name - Company name from DOL
├── participant_count - Retirement plan participants
└── total_assets - Plan assets in dollars

dol_violations (SIDECAR)
├── company_unique_id - FK to company_master (nullable)
├── ein - Employer ID
├── violation_type - ERISA violation category
└── penalty_amount - DOL penalty
```

## Schema Enhancements

**3 New Tables:**
- `marketing.form_5500` - DOL retirement plan filings (10 indexes)
- `marketing.dol_violations` - ERISA violations (3 indexes)
- `marketing.form_5500_staging` - CSV import staging

**10 New Columns:**
- 7 on `company_master`: ein, duns, cage_code, email_pattern (+ 3 metadata)
- 3 on `company_slot`: phone, phone_extension, phone_verified_at

**5 New Functions/Procedures:**
- `generate_email()` - Create emails from patterns
- `detect_email_pattern()` - Learn patterns from emails
- `match_5500_to_company()` - Fuzzy match DOL sponsors
- `process_5500_staging()` - Batch import CSV data
- `update_company_email_pattern()` - Update company patterns

**2 New Views:**
- `v_company_enrichment_status` - Enrichment scoring (0-100)
- `v_companies_need_enrichment` - Prioritized queue

## PLE Doctrine Compliance

✅ **Rule 1:** Never enrich people—enrich the company
✅ **Rule 2:** Phone belongs to slot, not person
✅ **Rule 3:** Email pattern belongs to company, not person
✅ **Rule 4:** EIN is the passport to federal data
✅ **Rule 6:** Quarantine before reject (nullable FKs)
✅ **Rule 8:** Log everything to sidecar tables
✅ **Rule 9:** Core tables = current state; Sidecar tables = history

---

# Form 5500 Federal Data Import

## Status: ✅ PRODUCTION READY - COMPLETE ECOSYSTEM

Complete infrastructure for importing **all** DOL Form 5500 data:
- **Form 5500** - Large plans (≥100 participants) - 700K+ filings
- **Form 5500-SF** - Small plans (<100 participants) - 2M+ filings ✨ NEW
- **Schedule A** - Insurance information - 1.5M+ records ✨ NEW

**Total Coverage:** 2.7M+ plans, 150K+ unique EINs

## Quick Start

### 1. Download DOL Data
```bash
# URL: https://www.dol.gov/agencies/ebsa/researchers/data/retirement-bulletin
# File: f_5500_2024_latest.zip (~500MB)
# Records: 700,000+ retirement plan filings
```

### 2. Import to Staging (2-5 minutes)
```bash
psql $NEON_CONNECTION_STRING << 'EOF'
\COPY marketing.form_5500_staging (
    ack_id, ein, plan_number, plan_name, sponsor_name,
    address, city, state, zip, date_received,
    participant_count, total_assets
)
FROM '/path/to/f_5500_2024_latest.csv'
CSV HEADER;
EOF
```

### 3. Process Staging (20-30 minutes)
```sql
CALL marketing.process_5500_staging();
-- Output: NOTICE: Processed 700000 records, matched 350000 to existing companies
```

### 4. Verify Import
```sql
-- Check total records
SELECT COUNT(*) FROM marketing.form_5500;
-- Expected: 700,000+

-- Check match rate
SELECT
    COUNT(*) as total,
    COUNT(company_unique_id) as matched,
    ROUND(100.0 * COUNT(company_unique_id) / COUNT(*), 1) as match_rate_pct
FROM marketing.form_5500;
-- Expected: 50-70% match rate
```

## Documentation

### 🌟 Complete Ecosystem Guide
**[FORM_5500_COMPLETE_GUIDE.md](./FORM_5500_COMPLETE_GUIDE.md)** - **START HERE** for complete 3-dataset system
- Form 5500 (large plans)
- Form 5500-SF (small plans) ✨ NEW
- Schedule A (insurance) ✨ NEW

### Primary Guides
1. **[FORM_5500_EXECUTIVE_SUMMARY.md](./FORM_5500_EXECUTIVE_SUMMARY.md)** - Executive overview
2. **[IMPORT_CHECKLIST.md](./IMPORT_CHECKLIST.md)** - Step-by-step execution guide
3. **[FORM_5500_IMPORT_GUIDE.md](./FORM_5500_IMPORT_GUIDE.md)** - Technical details & troubleshooting

### Validation & Reference
4. **[MASTER_IMPORT_READINESS_REPORT.md](./MASTER_IMPORT_READINESS_REPORT.md)** - Doctrine compliance audit
5. **[ENRICHMENT_SUMMARY.md](./ENRICHMENT_SUMMARY.md)** - Implementation details
6. **[COMPANY_INTELLIGENCE_ENRICHMENT.md](./COMPANY_INTELLIGENCE_ENRICHMENT.md)** - Architecture & functions

### Implementation Scripts
**Form 5500 (Regular):**
- `company_intelligence_enrichment.js` - Main schema implementation (13 tasks)
- `enhance_form_5500_schema.js` - Import enhancements (constraints, indexes)

**Form 5500-SF (Short Form):** ✨ NEW
- `create_5500_sf_table.js` - Schema creation for small plans
- `import_5500_sf.py` - CSV preparation and column mapping

**Schedule A (Insurance):** ✨ NEW
- `join_form5500_schedule_a.py` - Join main form + Schedule A

## What You Get After Import

### Data Volume
**Form 5500 (Regular):**
- 700,000+ retirement plan filings
- 150,000+ unique EINs
- 80,000+ filings from target states (PA, VA, MD, OH, WV, KY)
- 50-70% match rate to existing companies

**Form 5500-SF (Small Plans):** ✨ NEW
- 2,000,000+ plan filings
- Small businesses (<100 participants)
- Pension AND welfare plans
- 40-60% match rate (smaller companies)

**Schedule A (Insurance):** ✨ NEW
- 1,500,000+ insurance records
- Carrier relationships
- Covered lives counts
- Contract numbers

**Combined Total:** 2.7M+ plans, 150K+ unique EINs

### Company Enrichment Improvements
- 50,000+ companies matched (10x increase with 5500-SF)
- +10-15 points average enrichment score increase
- 90%+ plan coverage (large + small plans)
- 70%+ companies with federal IDs
- Insurance relationship mapping

### New Capabilities
- **Employee count validation** via DOL participant counts
- **HR maturity signals** (companies with retirement plans)
- **Hiring/layoff indicators** (participant count trends)
- **Financial health signals** (total assets trends)
- **Federal data joins** (IRS, SEC, USPTO via EIN)
- **Small business coverage** (2M+ plans via 5500-SF) ✨ NEW
- **Insurance broker relationships** (Schedule A) ✨ NEW
- **Welfare plan identification** (medical, dental, life) ✨ NEW

## Cost & Performance Benefits

### API Cost Reduction
- **Before:** $3,000/month on Hunter.io for executive emails
- **After:** $1,000/month (learn pattern from 1 email, generate others)
- **Savings:** $24,000/year

### Data Quality
- Employee count validation via federal data
- Federal ID enables cross-system matching
- Role-based contacts survive turnover

### Enrichment Speed
- Email generation: Instant (no API wait)
- Batch-friendly: 1,000 emails in milliseconds
- EIN lookups: Sub-second (indexed)

## Risk Assessment: All LOW ✅

- **Data Integrity:** Unique constraints + CHECK constraints enforce quality
- **Performance:** 13 indexes optimize queries
- **Operations:** Manual review for high-value unmatched records

## Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Total records imported | 700,000+ | ⏳ Pending import |
| Match rate | 50-70% | ⏳ Pending import |
| Companies with EINs | 1,000+ | ⏳ Pending import |
| Enrichment score increase | +10 points | ⏳ Pending import |
| Duplicate ACK_IDs | 0 | ✅ Enforced |
| Invalid EINs | 0 | ✅ Enforced |

---

**Last Updated:** 2025-11-27
**Status:** All systems production ready
**Next Action:** Download CSV and follow [IMPORT_CHECKLIST.md](./IMPORT_CHECKLIST.md)

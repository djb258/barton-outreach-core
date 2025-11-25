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

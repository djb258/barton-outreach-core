# State Blog → People Extraction Pipeline

## ✅ PIPELINE COMPLETION STATUS - 2026-01-30

> **ALL 9 STATES COMPLETE** - FREE extraction finished for all target states.

## Quick Reference

```bash
# Run for single state
doppler run -- python scripts/state_extraction_pipeline.py --state PA --batch-size 500

# Run for all 9 target states
doppler run -- python scripts/state_extraction_pipeline.py --state ALL --batch-size 500

# Check extraction status
doppler run -- python scripts/correct_status.py

# Full status report
doppler run -- python scripts/full_status_check.py
```

## Target States (9 Total) - FINAL STATUS 2026-01-30

| State | Code | Companies | People | FREE Status | Paid Queue |
|-------|------|-----------|--------|-------------|------------|
| Pennsylvania | PA | 16,571 | 16,433 | ✅ COMPLETE | 6,966 |
| Ohio | OH | 14,843 | 18,546 | ✅ COMPLETE | 6,215 |
| Virginia | VA | 11,983 | 13,786 | ✅ COMPLETE | 4,576 |
| North Carolina | NC | 10,794 | 8,924 | ✅ COMPLETE | 3,333 |
| Maryland | MD | 8,344 | 11,963 | ✅ COMPLETE | 2,939 |
| Kentucky | KY | 3,864 | 3,516 | ✅ COMPLETE | 996 |
| Oklahoma | OK | 3,743 | 2,106 | ✅ COMPLETE | 1,210 |
| Delaware | DE | 3,159 | 1,322 | ✅ COMPLETE | 841 |
| West Virginia | WV | 1,340 | 660 | ✅ COMPLETE | 262 |

> **Total People Extracted:** 77,256  
> **Paid Enrichment Queue:** 27,338 URLs (ready for Clay API)

---

## Extraction Final Summary (2026-01-30)

```
======================================================================
         FREE EXTRACTION PIPELINE - COMPLETION REPORT
======================================================================

FREE Extraction Status:
  complete:        14,630 URLs
  queued_for_paid: 27,338 URLs (awaiting PAID enrichment)
  pending:              0 URLs ← ALL PROCESSED
  failed:               9 URLs

Total People Extracted: 77,256

Slot Coverage (Overall):
  CEO: 15,759/42,361 (37.2%)
  CFO:  4,975/42,361 (11.7%)
  HR:   6,636/42,361 (15.7%)

PAID Enrichment Queue: 27,338 URLs (ready for Clay)
======================================================================
```

### Final Results By State

| State | Complete | Paid Queue | Pending | People |
|-------|----------|------------|---------|--------|
| PA | 3,451 | 6,966 | 0 | 16,433 |
| OH | 3,054 | 6,215 | 0 | 18,546 |
| VA | 2,426 | 4,576 | 0 | 13,786 |
| NC | 1,457 | 3,333 | 0 | 8,924 |
| MD | 1,529 | 2,939 | 0 | 11,963 |
| KY | 525 | 996 | 0 | 3,516 |
| OK | 496 | 1,210 | 0 | 2,106 |
| DE | 341 | 841 | 0 | 1,322 |
| WV | 115 | 262 | 0 | 660 |

---

## Pipeline Stages

### Stage 1: CHECK_BASELINE
Gathers pre-extraction metrics:
- Company count for state
- URLs available (leadership_page, team_page, about_page, blog)
- Existing people count
- Current slot coverage (CEO/CFO/HR)

### Stage 2: MINT_ORPHANS
Creates identity bridge entries for "orphan" companies (companies in company_master without bridge entries).

**Bridge Schema:**
```
cl.company_identity_bridge
├── bridge_id: UUID (PK)
├── source_company_id: TEXT (DOCTRINE ID: 04.04.01.XX.XXXXX.XXX)
├── company_sov_id: UUID (sovereign ID)
└── source_system: TEXT ('orphan_mint')
```

### Stage 3: INIT_SLOTS
Creates CEO/CFO/HR slots for companies with outreach records but no slots.

**Requirements:**
- Company must have `outreach.outreach` record
- `outreach_id` is required FK for slots

### Stage 4: FREE_EXTRACT
Pure FREE extraction using:
- **httpx** - HTTP client
- **selectolax** - HTML parser
- **regex** - Pattern matching

**NO API CALLS. NO LLM. ZERO COST.**

**Title Patterns:**
```python
CEO: chief executive officer, ceo, president, owner, founder, principal, managing director
CFO: chief financial officer, cfo, controller, treasurer, finance director
HR: chief human resources officer, hr manager, director of people/talent
```

### Stage 5: ASSIGN_STAGED
Promotes extracted people from staging to `people_master`:

1. Generates DOCTRINE ID for person: `04.04.02.XX.XXXXX.XXX`
2. Derives slot DOCTRINE ID: `04.04.05.XX.XXXXX.XXX`
3. Links to company DOCTRINE ID: `04.04.01.XX.XXXXX.XXX`
4. Marks slot as filled
5. Updates staging status to 'promoted'

### Stage 6: CREATE_MISSING_OUTREACH
Creates outreach records + slots for companies that have extracted people but no outreach.

### Stage 7: REPORT
Generates before/after comparison report.

---

## DOCTRINE ID Formats

| Entity | Format | Example |
|--------|--------|---------|
| Company | 04.04.01.XX.XXXXX.XXX | 04.04.01.37.00000.001 |
| Person | 04.04.02.XX.XXXXX.XXX | 04.04.02.99.62340.340 |
| Slot | 04.04.05.XX.XXXXX.XXX | 04.04.05.99.62340.340 |

**Key Insight:** Person ID and Slot ID share the same suffix. Replace `02` with `05`.

---

## Database Tables

### Input Tables
| Table | Purpose |
|-------|---------|
| `company.company_master` | Source companies with state info |
| `company.company_source_urls` | URLs to extract from |
| `cl.company_identity_bridge` | DOCTRINE → UUID mapping |
| `outreach.outreach` | Outreach records (required for slots) |

### Output Tables
| Table | Purpose |
|-------|---------|
| `people.people_staging` | Extracted people (pre-assignment) |
| `people.people_master` | Final people records |
| `people.company_slot` | CEO/CFO/HR slots per company |
| `people.paid_enrichment_queue` | URLs that failed FREE extraction |

---

## Slot Fill Rules

1. **Name + Title = Fill Slot** (contact info optional)
2. One person per slot type per company
3. Duplicates remain in staging as 'pending'
4. Contact info (email, LinkedIn) enriched later

---

## Expected Results

### Success Metrics
| Metric | Target | Notes |
|--------|--------|-------|
| Extraction Rate | 15-30% | URLs yielding people |
| People per URL | 1-5 | When extraction succeeds |
| Slot Fill Rate | 20-30% | After extraction complete |

### Failure Categories
| Status | Meaning | Action |
|--------|---------|--------|
| `complete` | Extracted people | ✅ Done |
| `queued_for_paid` | No patterns found | → Clay queue |
| `failed` | HTTP error/timeout | Retry later |
| `pending` (staging) | Duplicate/no slot | Normal |

---

## WV Pilot Results

```
============================================================
         WV EXTRACTION PIPELINE - FINAL SUMMARY
============================================================

WV Companies: 1,340
People from FREE extraction: 262
WV Total People: 643

WV Slot Coverage:
  CEO: 244/891 (27.4%)
  CFO: 105/891 (11.8%)
  HR: 160/891 (18.0%)
  TOTAL: 509/2,673 (19.0%)

Staging:
  Promoted: 262
  Pending (duplicates/no slots): 336

Paid Enrichment Queue: 344 URLs
============================================================
```

---

## Troubleshooting

### "No orphans found" but companies exist
Check if companies already have bridge entries:
```sql
SELECT COUNT(*) FROM company.company_master cm
LEFT JOIN cl.company_identity_bridge cib ON cm.company_unique_id = cib.source_company_id
WHERE cm.address_state = 'WV' AND cib.source_company_id IS NULL;
```

### "No new slots needed" but slots missing
Companies need outreach records first:
```sql
SELECT COUNT(DISTINCT cm.company_unique_id) 
FROM company.company_master cm
JOIN cl.company_identity_bridge cib ON cm.company_unique_id = cib.source_company_id
LEFT JOIN outreach.outreach o ON o.sovereign_id = cib.company_sov_id
WHERE cm.address_state = 'WV' AND o.outreach_id IS NULL;
```

### Assignments failing with duplicate key
Sequence number collision - check max sequence:
```sql
SELECT MAX(CAST(SPLIT_PART(unique_id, '.', 5) AS INTEGER)) 
FROM people.people_master WHERE unique_id LIKE '04.04.02.%';
```

### Many pending but should be assignable
Check if slots are already filled:
```sql
SELECT cs.slot_type, cs.is_filled, COUNT(*)
FROM people.people_staging ps
JOIN people.company_slot cs ON cs.company_unique_id = ps.company_unique_id
WHERE ps.status = 'pending'
GROUP BY 1, 2;
```

---

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `state_extraction_pipeline.py` | Main pipeline (all stages) |
| `quick_assign.py` | Standalone assignment |
| `wv_summary.py` | Generate summary report |
| `wv_baseline_check.py` | Pre-extraction baseline |

---

## Next Steps

### ✅ COMPLETED (2026-01-30)
1. ~~Run VA~~ → DONE - 13,786 people
2. ~~Run NC~~ → DONE - 8,924 people  
3. ~~Complete WV~~ → DONE - 660 people
4. ~~Complete DE~~ → DONE - 1,322 people
5. ~~Run KY~~ → DONE - 3,516 people
6. ~~Run OK~~ → DONE - 2,106 people
7. ~~Run PA~~ → DONE - 16,433 people
8. ~~Run OH~~ → DONE - 18,546 people
9. ~~Run MD~~ → DONE - 11,963 people

### NEXT: PAID Enrichment
- **27,338 URLs** in `queued_for_paid` status
- These are URLs where FREE extraction found no patterns
- Ready to send to Clay API for paid enrichment

```sql
-- Check paid queue by state
SELECT cm.address_state, COUNT(*) 
FROM company.company_source_urls csu
JOIN company.company_master cm ON csu.company_unique_id = cm.company_unique_id
WHERE csu.extraction_status = 'queued_for_paid'
GROUP BY cm.address_state
ORDER BY COUNT(*) DESC;
```

---

## Connection Stability Fix (2026-01-28)

SSL connection timeouts were encountered during long-running extractions. Resolution:

```python
def _refresh_connection(self):
    """Refresh the database connection."""
    try:
        self.conn.close()
    except:
        pass
    self.conn = psycopg2.connect(DATABASE_URL)

# In extraction loop - ping before each write:
try:
    cur.execute("SELECT 1")
except:
    self._refresh_connection()
    cur = self.conn.cursor()

# Commit after each URL (not batched)
self.conn.commit()
```

---

## COMPLIANCE CHECKLIST

### Source Types Used by Pipeline
The pipeline ONLY processes these 4 source types:
```python
PEOPLE_SOURCE_TYPES = ['leadership_page', 'team_page', 'about_page', 'blog']
```

> ⚠️ **WARNING:** Do NOT include `contact_page`, `careers_page`, or `press_page` when checking status.
> The pipeline does not process these types.

### Status Check Query (CORRECT)
```sql
-- CORRECT: Uses only pipeline source types
SELECT cm.address_state,
    COUNT(*) FILTER (WHERE extraction_status = 'pending') as pending,
    COUNT(*) FILTER (WHERE extraction_status = 'queued_for_paid') as queued_paid,
    COUNT(*) FILTER (WHERE extraction_status = 'complete') as complete
FROM company.company_source_urls csu
JOIN company.company_master cm ON csu.company_unique_id = cm.company_unique_id
WHERE csu.source_type IN ('leadership_page', 'team_page', 'about_page', 'blog')
GROUP BY cm.address_state;
```

### Status Check Scripts
- `scripts/correct_status.py` - Uses correct source types
- `scripts/full_status_check.py` - Comprehensive status report

---

*Last Updated: January 30, 2026*
*Pipeline Version: 1.2 - COMPLETE*

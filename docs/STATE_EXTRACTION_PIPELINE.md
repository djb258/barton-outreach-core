# State Blog → People Extraction Pipeline

## Quick Reference

```bash
# Run for single state
doppler run -- python scripts/state_extraction_pipeline.py --state PA --batch-size 500

# Run for all 9 target states
doppler run -- python scripts/state_extraction_pipeline.py --state ALL --batch-size 500

# Quick assignment (after pipeline completes)
doppler run -- python scripts/quick_assign.py

# Summary report
doppler run -- python scripts/wv_summary.py
```

## Target States (9 Total) - REVISED 2026-01-28

| State | Code | Companies | People | Status |
|-------|------|-----------|--------|--------|
| Pennsylvania | PA | 16,571 | 16,433 | 🔄 IN PROGRESS |
| Ohio | OH | 14,843 | 18,546 | 🔄 IN PROGRESS |
| Virginia | VA | 11,983 | 4,234 | ⏳ PENDING |
| North Carolina | NC | 10,794 | 4,816 | ⏳ PENDING |
| Maryland | MD | 8,344 | 11,963 | 🔄 IN PROGRESS |
| Kentucky | KY | 3,864 | 1,687 | ⏳ PENDING |
| Oklahoma | OK | 3,743 | 128 | ⏳ PENDING |
| West Virginia | WV | 1,340 | 660 | 🔄 IN PROGRESS |
| Delaware | DE | 3,159 | 1,173 | 🔄 IN PROGRESS |

> **Note:** Previous target states (VT, WY, AK, ND, SD, MT, RI) were deprecated on 2026-01-28.
> See [ADR-018](adr/ADR-018_FREE_Extraction_Pipeline_Progress.md) for details.

---

## Extraction Progress Summary (2026-01-28)

```
======================================================================
         FREE EXTRACTION PIPELINE - PROGRESS REPORT
======================================================================

Extraction Status Distribution:
  pending:          71,511 URLs (73.6%)
  queued_for_paid:  17,092 URLs (17.6%)
  complete:          8,439 URLs (8.7%)
  failed:                9 URLs (0.0%)

Total People Extracted: 59,640

Paid Enrichment Queue: 17,174 URLs (ready for Clay)
======================================================================
```

### By State

| State | Complete | Paid Queue | Pending | People |
|-------|----------|------------|---------|--------|
| PA | 3,451 | 6,966 | 14,416 | 16,433 |
| OH | 3,054 | 6,215 | 12,912 | 18,546 |
| MD | 1,529 | 2,939 | 5,720 | 11,963 |
| VA | 0 | 0 | 16,404 | 4,234 |
| NC | 0 | 0 | 12,259 | 4,816 |
| WV | 115 | 262 | 610 | 660 |
| DE | 290 | 710 | 1,604 | 1,173 |
| KY | 0 | 0 | 3,661 | 1,687 |
| OK | 0 | 0 | 3,925 | 128 |

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

1. **Run VA:** `doppler run -- python scripts/state_extraction_pipeline.py --state VA --batch-size 500`
2. **Run NC:** `doppler run -- python scripts/state_extraction_pipeline.py --state NC --batch-size 500`
3. **Complete WV:** `doppler run -- python scripts/state_extraction_pipeline.py --state WV --batch-size 500`
4. **Complete DE:** `doppler run -- python scripts/state_extraction_pipeline.py --state DE --batch-size 500`
5. **Run KY:** `doppler run -- python scripts/state_extraction_pipeline.py --state KY --batch-size 500`
6. **Run OK:** `doppler run -- python scripts/state_extraction_pipeline.py --state OK --batch-size 500`
7. **Paid enrichment:** Send 17,174 queued URLs to Clay

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

*Last Updated: January 28, 2026*
*Pipeline Version: 1.1*
*See: [ADR-018](adr/ADR-018_FREE_Extraction_Pipeline_Progress.md)*

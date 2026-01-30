# ADR-019: FREE Extraction Pipeline - COMPLETE

**Status:** APPROVED  
**Date:** January 30, 2026  
**Author:** Copilot + David Barton  

---

## Context

The FREE Extraction Pipeline was designed to extract leadership contact information from company websites using zero-cost methods (httpx + selectolax + regex) before resorting to paid API enrichment (Clay).

## Decision

The FREE extraction phase is **COMPLETE** for all 9 target states as of January 30, 2026.

## Final Results

### Extraction Status
| Metric | Count |
|--------|-------|
| Total URLs Processed | 41,977 |
| Completed (people found) | 14,630 |
| Queued for Paid | 27,338 |
| Failed | 9 |
| Pending | **0** |

### People Extracted by State
| State | Companies | People | Slot Coverage |
|-------|-----------|--------|---------------|
| PA | 16,571 | 16,433 | ~37% |
| OH | 14,843 | 18,546 | ~37% |
| VA | 11,983 | 13,786 | ~37% |
| NC | 10,794 | 8,924 | ~38% |
| MD | 8,344 | 11,963 | ~37% |
| KY | 3,864 | 3,516 | ~37% |
| OK | 3,743 | 2,106 | ~37% |
| DE | 3,159 | 1,322 | ~37% |
| WV | 1,340 | 660 | ~27% |
| **TOTAL** | **74,641** | **77,256** | **37.2%** |

### Slot Coverage (Overall)
| Slot Type | Filled | Total | Coverage |
|-----------|--------|-------|----------|
| CEO | 15,759 | 42,361 | 37.2% |
| CFO | 4,975 | 42,361 | 11.7% |
| HR | 6,636 | 42,361 | 15.7% |

## Technical Implementation

### Pipeline Stages
1. **CHECK_BASELINE** - Pre-extraction metrics
2. **MINT_ORPHANS** - Create identity bridge entries
3. **INIT_SLOTS** - Create CEO/CFO/HR slots
4. **FREE_EXTRACT** - httpx + selectolax + regex (ZERO COST)
5. **ASSIGN_STAGED** - Promote to people_master with DOCTRINE IDs
6. **CREATE_MISSING_OUTREACH** - Create outreach records
7. **REPORT** - Generate comparison report

### Source Types Processed
```python
PEOPLE_SOURCE_TYPES = ['leadership_page', 'team_page', 'about_page', 'blog']
```

> ⚠️ **IMPORTANT:** `contact_page`, `careers_page`, and `press_page` are NOT processed by this pipeline.

### DOCTRINE ID Formats
| Entity | Format |
|--------|--------|
| Company | `04.04.01.XX.XXXXX.XXX` |
| Person | `04.04.02.XX.XXXXX.XXX` |
| Slot | `04.04.05.XX.XXXXX.XXX` |

## Scripts Created

| Script | Purpose |
|--------|---------|
| `scripts/state_extraction_pipeline.py` | Main 7-stage pipeline |
| `scripts/correct_status.py` | Status check (correct source types) |
| `scripts/full_status_check.py` | Comprehensive status report |
| `scripts/check_state_status.py` | State-by-state status |

## Database Tables

### Input
- `company.company_master` - Source companies
- `company.company_source_urls` - URLs to extract
- `cl.company_identity_bridge` - DOCTRINE mapping
- `outreach.outreach` - Outreach records

### Output
- `people.people_staging` - Extracted people (pre-promotion)
- `people.people_master` - Final people records
- `people.company_slot` - CEO/CFO/HR slots
- `people.paid_enrichment_queue` - URLs for paid enrichment

## Next Phase

### PAID Enrichment Queue
- **27,338 URLs** queued for paid enrichment
- These are URLs where FREE regex patterns found no matches
- Ready for Clay API enrichment

```sql
-- Check paid queue
SELECT extraction_status, COUNT(*)
FROM company.company_source_urls
WHERE source_type IN ('leadership_page', 'team_page', 'about_page', 'blog')
GROUP BY extraction_status;
```

## Compliance Notes

### Status Check Gotcha
When checking extraction status, ALWAYS filter by the correct source types:
```sql
WHERE source_type IN ('leadership_page', 'team_page', 'about_page', 'blog')
```

DO NOT include `contact_page`, `careers_page`, or `press_page` - the pipeline doesn't process these.

### Verification Script
```bash
doppler run -- python scripts/correct_status.py
```

## Consequences

### Positive
- 77,256 people extracted at ZERO COST
- 37.2% CEO slot coverage achieved
- Foundation for paid enrichment established
- Clear audit trail via DOCTRINE IDs

### Risks Mitigated
- Connection stability: Auto-reconnect on timeout
- Duplicate prevention: Staging buffer before promotion
- ID collision: Sequence-based DOCTRINE ID generation

## Related Documents

- [STATE_EXTRACTION_PIPELINE.md](../STATE_EXTRACTION_PIPELINE.md)
- [ADR-018: FREE Extraction Pipeline Progress](ADR-018_FREE_Extraction_Pipeline_Progress.md)
- [PRD: People Subhub](../prd/PRD_PEOPLE_SUBHUB.md)
- [COMPLETE_SYSTEM_ERD.md](../COMPLETE_SYSTEM_ERD.md)

---

*Signed off: January 30, 2026*

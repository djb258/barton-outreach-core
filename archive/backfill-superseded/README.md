# Backfill Superseded Scripts

**Archived**: 2026-02-20
**Reason**: Phase 3 Legacy Collapse dropped the source tables these scripts read from.

## Scripts

| Script | Dropped Table | Notes |
|--------|---------------|-------|
| `backfill_linkedin_from_clay.py` | `intake.people_raw_intake` | Clay intake data now in `vendor.people` |
| `backfill_company_linkedin.py` | `intake.company_raw_intake` | Intake data now in `vendor.ct` |

## Data Location

All historical data from these intake tables lives in vendor staging:
- `vendor.people WHERE source_table = 'intake.people_raw_intake'` (120,045 rows)
- `vendor.ct WHERE source_table = 'intake.company_raw_intake'` (563 rows)

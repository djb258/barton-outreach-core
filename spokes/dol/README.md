# DOL Spoke (Spoke #2)

**PRD Reference**: `docs/prd/PRD_DOL_SUBHUB.md`

## Purpose

The DOL Spoke processes Department of Labor Form 5500 and Schedule A data, linking benefit plan information to Company Hub records.

## Directory Structure

```
spokes/dol/
├── __init__.py
├── dol_spoke.py            # Main spoke implementation
├── form5500_processor.py   # Form 5500 processing
├── schedule_a_processor.py # Schedule A renewals
├── ein_matcher.py          # EIN-to-company matching
└── importers/              # Data importers
    ├── import_5500.py
    ├── import_5500_sf.py
    └── import_schedule_a.py
```

## Data Flow

1. Import raw DOL data via importers
2. Match EINs to Company Hub records
3. Extract renewal dates and broker information
4. Link to company_master via company_id

## Key Outputs

- Renewal date intelligence
- Broker relationship mapping
- Plan participant counts

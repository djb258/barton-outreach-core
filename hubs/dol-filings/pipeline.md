# DOL Filings — Pipeline Definition

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    DOL FILINGS PIPELINE                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ INGEST: Load DOL CSV Files                                   │
│ ─────────────────────────────────────────────────────────── │
│ • Form 5500 (large plans >= 100 participants)               │
│ • Form 5500-SF (small plans < 100 participants)             │
│ • Schedule A (insurance broker data)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ PARSE: Extract and Validate Records                          │
│ ─────────────────────────────────────────────────────────── │
│ • Parse: ACK_ID, EIN, PLAN_YEAR, PARTICIPANTS, ASSETS       │
│ • Validate: Required fields present                         │
│ • Stage to: marketing.form_5500_staging                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ MATCH: EIN Matching (Exact Only)                             │
│ ─────────────────────────────────────────────────────────── │
│ • Query company_master by EIN                               │
│ • EXACT MATCH ONLY — no fuzzy                               │
│ • No retries on mismatch                                    │
│ • Doctrine: Fail closed                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Match Found?   │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
        ┌─────────┐                   ┌─────────┐
        │   YES   │                   │   NO    │
        └────┬────┘                   └────┬────┘
             │                              │
             ▼                              ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│ ATTACH: Link Filing     │    │ LOG: Unmatched Filing   │
│ ─────────────────────── │    │ ─────────────────────── │
│ • Attach to company     │    │ • Log to error_log      │
│ • Store in form_5500    │    │ • Do NOT retry          │
│ • Store in schedule_a   │    │ • STOP processing       │
└────────────┬────────────┘    └─────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│ EMIT: BIT Signals                                            │
│ ─────────────────────────────────────────────────────────── │
│ • FORM_5500_FILED (+5.0)                                    │
│ • LARGE_PLAN (+8.0) if participants >= 100                  │
│ • BROKER_CHANGE (+7.0) if broker differs from prior year    │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Files

| Component | File |
|-----------|------|
| Form 5500 Importer | `imo/middle/importers/import_5500.py` |
| Form 5500-SF Importer | `imo/middle/importers/import_5500_sf.py` |
| Schedule A Importer | `imo/middle/importers/import_schedule_a.py` |
| EIN Matcher | `imo/middle/ein_matcher.py` |
| Form 5500 Processor | `imo/middle/processors/form5500_processor.py` |
| Schedule A Processor | `imo/middle/processors/schedule_a_processor.py` |

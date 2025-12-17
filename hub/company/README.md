# Company Hub (Master Node)

**PRD Reference**: `docs/prd/PRD_COMPANY_HUB.md`, `docs/prd/PRD_COMPANY_HUB_PIPELINE.md`

## Purpose

The Company Hub is the **master node** of the Barton Hub-and-Spoke architecture. All data pipelines anchor to company records first.

## Directory Structure

```
hub/company/
├── __init__.py
├── company_hub.py          # Core hub implementation
├── bit_engine.py           # BIT scoring engine
├── phases/                 # Company pipeline phases (1-4)
│   ├── phase1_company_matching.py
│   ├── phase1b_unmatched_hold_export.py
│   ├── phase2_domain_resolution.py
│   ├── phase3_email_pattern_waterfall.py
│   └── phase4_pattern_verification.py
├── email/                  # Email pattern discovery
│   ├── bulk_verifier.py
│   ├── pattern_discovery_pipeline.py
│   └── pattern_guesser.py
├── movement_engine/        # Movement detection
│   ├── movement_engine.py
│   ├── movement_rules.py
│   └── state_machine.py
└── utils/                  # Shared utilities
    ├── fuzzy.py
    ├── normalization.py
    └── patterns.py
```

## The Golden Rule

```
IF company_id IS NULL OR domain IS NULL OR email_pattern IS NULL:
    STOP. DO NOT PROCEED.
    → Route to Company Identity Pipeline first.
```

No spoke pipeline should EVER process a record that lacks a valid company anchor.

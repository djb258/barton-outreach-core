# People Spoke (Spoke #1)

**PRD Reference**: `docs/prd/PRD_PEOPLE_SUBHUB.md`

## Purpose

The People Spoke handles all person-related data after it has been anchored to a valid Company Hub record.

## Directory Structure

```
spokes/people/
├── __init__.py
├── people_spoke.py         # Main spoke implementation
├── hub_gate.py             # Company anchor validation
├── slot_assignment.py      # CEO/CFO/HR slot logic
├── phases/                 # People pipeline phases (0, 5-8)
│   ├── phase0_people_ingest.py
│   ├── phase5_email_generation.py
│   ├── phase6_slot_assignment.py
│   ├── phase7_enrichment_queue.py
│   └── phase8_output_writer.py
└── sub_wheels/             # Sub-wheel components
    └── email_verification/
        ├── bulk_verifier_spoke.py
        ├── email_verification_wheel.py
        └── pattern_guesser_spoke.py
```

## Hub Gate Requirement

Every record entering this spoke MUST pass through `hub_gate.py` to validate:
- `company_id` is not NULL
- `domain` is not NULL
- `email_pattern` is not NULL

Records failing the hub gate are routed to failure spokes.

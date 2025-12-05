# Pipeline Engine - Multi-Phase People Enrichment

## Architecture Overview

```
                    ┌────────────────────────────────┐
                    │     INPUT PEOPLE (Clay, CSV)    │
                    │  first, last, title, company    │
                    └────────────────────────────────┘
                                      │
                                      ▼
                ┌────────────────────────────────────┐
                │     PHASE 1 — COMPANY MATCHING      │
                │  • normalize names                  │
                │  • exact match                      │
                │  • fuzzy match (JW + city guardrail)│
                │  • domain join if available         │
                │  • collision handling               │
                └────────────────────────────────────┘
                                      │
                                      ▼
                ┌────────────────────────────────────┐
                │     PHASE 2 — DOMAIN RESOLUTION     │
                │  • get domain from matched company  │
                │  • if missing → scrape website      │
                │  • if still missing → enrichment T0 │
                └────────────────────────────────────┘
                                      │
                                      ▼
        ┌──────────────────────────────────────────────────────────┐
        │      PHASE 3 — EMAIL PATTERN WATERFALL (T0 → T2)         │
        │  Tier 0: Firecrawl / ScraperAPI / Google Places          │
        │  Tier 1: Hunter.io / Clearbit / Apollo                   │
        │  Tier 2: Prospeo / Snov / Clay                           │
        └──────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                ┌────────────────────────────────────┐
                │    PHASE 4 — PATTERN VERIFICATION   │
                │  • validate pattern with known data │
                │  • test pattern on sample emails    │
                │  • fallback if verification fails   │
                └────────────────────────────────────┘
                                      │
                                      ▼
                ┌────────────────────────────────────┐
                │   PHASE 5 — MASS EMAIL GENERATION   │
                │  • apply pattern to all people      │
                │  • no enrichment cost               │
                │  • attach to person_id              │
                └────────────────────────────────────┘
                                      │
                                      ▼
         ┌─────────────────────────────────────────────────────────┐
         │     PHASE 6 — TITLE CLASSIFY & SLOT ASSIGNMENT          │
         │  • classify title (CEO, CFO, HR, Benefits, etc.)        │
         │  • assign to company slot                                │
         │  • handle slot conflicts                                 │
         └─────────────────────────────────────────────────────────┘
                                      │
                                      ▼
              ┌────────────────────────────────────────┐
              │     PHASE 7 — ENRICHMENT QUEUE         │
              │  • unmatched people → queue            │
              │  • missing emails → queue              │
              │  • failed patterns → queue             │
              └────────────────────────────────────────┘
                                      │
                                      ▼
            ┌──────────────────────────────────────────────┐
            │            PHASE 8 — FINAL OUTPUT             │
            │  • matched_people                             │
            │  • company_email_pattern                      │
            │  • generated_emails                           │
            │  • slot_assignments                           │
            │  • enrichment_queue                           │
            └──────────────────────────────────────────────┘
```

## Project Structure

```
/pipeline_engine
    /phases
        talentflow_phase0_company_gate.py # Talent Flow company gate (Phase 0)
        phase1_company_matching.py      # Company name/domain matching
        phase1b_unmatched_hold_export.py # Export unmatched to HOLD CSV
        phase2_domain_resolution.py     # Domain lookup & scraping
        phase3_email_pattern_waterfall.py # Tiered email pattern discovery
        phase4_pattern_verification.py  # Pattern validation
        phase5_email_generation.py      # Mass email generation
        phase6_slot_assignment.py       # Title classification & slots
        phase7_enrichment_queue.py      # Queue unresolved items
        phase8_output_writer.py         # Final output generation
    /utils
        normalization.py                # Name & string normalization
        fuzzy.py                        # Fuzzy matching algorithms
        providers.py                    # External API providers
        patterns.py                     # Email pattern utilities
        verification.py                 # Email verification helpers
        logging.py                      # Pipeline logging
        config.py                       # Configuration management
    main.py                             # Pipeline orchestrator
    README.md                           # This file
```

## Phase Descriptions

### Phase 1: Company Matching
Matches input people to companies in `company_master` using:
- Exact name matching
- Fuzzy matching (Jaro-Winkler with city guardrail)
- Domain-based joining
- Collision resolution for ambiguous matches

### Phase 2: Domain Resolution
Ensures each matched company has a valid domain:
- Pull domain from matched company record
- Scrape website if domain missing
- Queue for Tier 0 enrichment if still unresolved

### Phase 3: Email Pattern Waterfall
Discovers email patterns using tiered approach:
- **Tier 0 (Free)**: Firecrawl, ScraperAPI, Google Places
- **Tier 1 (Low Cost)**: Hunter.io, Clearbit, Apollo
- **Tier 2 (Premium)**: Prospeo, Snov, Clay

### Phase 4: Pattern Verification
Validates discovered patterns:
- Test against known valid emails
- Confidence scoring
- Fallback to next tier if verification fails

### Phase 5: Mass Email Generation
Applies verified pattern to generate emails:
- Pattern application: `{first}.{last}@domain.com`
- No per-email enrichment cost
- Links email to person_id

### Phase 6: Title Classify & Slot Assignment
Classifies job titles and assigns to company slots:
- Title normalization and classification
- Slot type matching (CEO, CFO, HR, Benefits)
- Conflict resolution for filled slots

### Phase 7: Enrichment Queue
Queues unresolved items for manual review or future enrichment:
- Unmatched people
- Missing email patterns
- Failed verifications

### Phase 8: Final Output
Generates final output files:
- `matched_people.csv`
- `company_email_patterns.csv`
- `generated_emails.csv`
- `slot_assignments.csv`
- `enrichment_queue.csv`

## Usage

```python
from pipeline_engine.main import PipelineOrchestrator

# Initialize pipeline
pipeline = PipelineOrchestrator(config_path='config.yaml')

# Run full pipeline
results = pipeline.run(
    people_file='input_people.csv',
    companies_source='database'  # or 'csv'
)

# Access results
print(f"Matched: {results.matched_count}")
print(f"Emails Generated: {results.emails_generated}")
print(f"Queued: {results.queued_count}")
```

## Configuration

See `utils/config.py` for configuration options:
- Database connection settings
- API provider credentials
- Matching thresholds
- Tier progression rules

## Dependencies

- pandas
- rapidfuzz
- psycopg2
- requests

## Status

**SHELL ONLY** - Logic not yet implemented.

## Unmatched People HOLD Pipeline

People who cannot be matched to a company during Phase 1 are not enriched immediately.
Instead, they are exported into:

    people_unmatched_hold.csv

This file acts as a temporary staging area.
Once the remaining ~6,000 companies have been enriched and domains resolved, the pipeline
is re-run. The newly enriched company data dramatically improves matching accuracy.

This avoids premature enrichment and prevents corruption of emails, domains, slots,
and Neon records.

### HOLD Export Flow

```
Phase 1: Company Matching
         │
         ├─── Matched ──────► Phase 2+ (continue pipeline)
         │
         └─── Unmatched ────► Phase 1b: HOLD Export
                                    │
                                    ▼
                          people_unmatched_hold.csv
                                    │
                                    ▼
                          [Wait for company enrichment]
                                    │
                                    ▼
                          Re-run pipeline with improved data
```

### HOLD Reasons

Records are placed in HOLD for the following reasons:
- `no_match` - No company match found
- `low_confidence` - Match score below threshold
- `collision` - Multiple ambiguous matches
- `missing_data` - Insufficient data for matching

### Implementation

```python
from pipeline_engine.phases import Phase1bUnmatchedHoldExport

# After Phase 1 determines unmatched rows
phase1b = Phase1bUnmatchedHoldExport()
phase1b.run(unmatched_people_df, output_path="people_unmatched_hold.csv")
```

## Talent Flow Pipeline (Phase 0)

Talent Flow requires the ability to reprocess people when they change employers.

Process:
1. Normalize the new company name.
2. Check if the company already exists in the company master dataset.
3. If missing:
      -> Run the Company Identity Pipeline (Phases 1-4)
4. Once enriched:
      -> Run the People Pipeline (Phases 5-8) to update email, pattern, slot, and BIT signals.
5. This ensures repeatability and clean handling of executive and HR movement.

Implemented in:
    /phases/talentflow_phase0_company_gate.py

### Talent Flow Architecture

```
                    ┌────────────────────────────────────┐
                    │       MOVEMENT EVENT DETECTED       │
                    │  (LinkedIn, news, BIT signal)       │
                    └────────────────────────────────────┘
                                      │
                                      ▼
                ┌────────────────────────────────────────┐
                │    PHASE 0 — TALENT FLOW COMPANY GATE   │
                │  • normalize new company name           │
                │  • check if company exists              │
                │  • trigger enrichment if missing        │
                └────────────────────────────────────────┘
                                      │
                     ┌────────────────┴────────────────┐
                     │                                 │
                     ▼                                 ▼
        ┌───────────────────────┐        ┌───────────────────────┐
        │   Company EXISTS      │        │   Company MISSING     │
        │   in company_master   │        │   not in master       │
        └───────────────────────┘        └───────────────────────┘
                     │                                 │
                     │                                 ▼
                     │              ┌─────────────────────────────────┐
                     │              │  COMPANY IDENTITY PIPELINE      │
                     │              │  Phases 1-4                     │
                     │              │  (match, domain, pattern, etc.) │
                     │              └─────────────────────────────────┘
                     │                                 │
                     └────────────────┬────────────────┘
                                      │
                                      ▼
                    ┌────────────────────────────────────┐
                    │       PEOPLE PIPELINE              │
                    │       Phases 5-8                   │
                    │  • email generation                │
                    │  • slot assignment                 │
                    │  • BIT signal update               │
                    └────────────────────────────────────┘
```

### Talent Flow Usage

```python
from pipeline_engine.main import CompanyIdentityPipeline
from pipeline_engine.phases import TalentFlowCompanyGate

# Initialize pipeline
pipeline = CompanyIdentityPipeline(config=config)

# Process a single movement event
movement_event = {
    'person_id': 'person_123',
    'new_company_name': 'Acme Corporation',
    'previous_company_id': 'company_456',
    'movement_type': 'job_change',
    'detected_at': '2024-01-15T10:30:00Z',
    'source': 'linkedin_profile_update'
}

result = pipeline.run_talent_flow_pipeline(movement_event)
```

### Movement Event Schema

| Field | Type | Description |
|-------|------|-------------|
| `person_id` | string | ID of person who changed employers |
| `new_company_name` | string | Name of new employer |
| `previous_company_id` | string | Optional - ID of previous employer |
| `movement_type` | string | Type: job_change, promotion, company_exit |
| `detected_at` | datetime | When the change was detected |
| `source` | string | Source of the signal (linkedin, news, etc.)

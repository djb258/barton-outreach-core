# People Intelligence — Pipeline Definition

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│                 PEOPLE INTELLIGENCE PIPELINE                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ GATE: Validate Prerequisites                                 │
│ ─────────────────────────────────────────────────────────── │
│ • Requires: company_sov_id                                  │
│ • Requires: lifecycle_state >= TARGETABLE                   │
│ • Requires: verified_pattern from Company Target            │
│ • Requires: outreach_context_id                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 5: Email Generation                                    │
│ ─────────────────────────────────────────────────────────── │
│ • Use verified pattern from Company Target                  │
│ • Generate emails for people records                        │
│ • Confidence levels: VERIFIED, DERIVED, LOW_CONFIDENCE      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 6: Slot Assignment                                     │
│ ─────────────────────────────────────────────────────────── │
│ • Slot Types (by seniority):                                │
│   - CHRO (100)                                              │
│   - HR_MANAGER (80)                                         │
│   - BENEFITS_LEAD (60)                                      │
│   - PAYROLL_ADMIN (50)                                      │
│   - HR_SUPPORT (30)                                         │
│   - UNSLOTTED (0)                                           │
│ • One person per slot per company                           │
│ • Conflicts resolved by seniority                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 7: Enrichment Queue                                    │
│ ─────────────────────────────────────────────────────────── │
│ • Queue only for MEASURED slot deficit                      │
│ • Priority: HIGH (missing CHRO/Benefits) → LOW (HR Support) │
│ • Enrichment tools gated by lifecycle + context             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 8: Output Writer                                       │
│ ─────────────────────────────────────────────────────────── │
│ • CSV OUTPUT ONLY (never canonical)                         │
│ • Files: people_final.csv, slot_assignments.csv,            │
│          enrichment_queue.csv, pipeline_summary.txt         │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Files

| Phase | File |
|-------|------|
| Phase 5 | `imo/middle/phases/phase5_email_generation.py` |
| Phase 6 | `imo/middle/phases/phase6_slot_assignment.py` |
| Phase 7 | `imo/middle/phases/phase7_enrichment_queue.py` |
| Phase 8 | `imo/middle/phases/phase8_output_writer.py` |
| Movement | `imo/middle/movement_engine/movement_engine.py` |
| Verification | `imo/middle/email/bulk_verifier.py` |
| CEO Pipeline | `imo/middle/phases/ceo_email_pipeline.py` |
| Hunter Slot Fill | `imo/middle/phases/fill_slots_from_hunter.py` |

---

## Hunter Enrichment Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    HUNTER SLOT FILL FLOW                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ INPUT: Hunter-enriched CSV                                   │
│ ─────────────────────────────────────────────────────────── │
│ • outreach_id (required for slot matching)                  │
│ • Email, First name, Last name, Job title                   │
│ • Phone number, LinkedIn URL (optional)                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Slot Type Detection                                  │
│ ─────────────────────────────────────────────────────────── │
│ • CEO: ceo, president, owner, founder, managing director    │
│ • CFO: cfo, chief financial, controller, treasurer          │
│ • HR: hr, human resources, chro, people operations          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Slot Lookup                                          │
│ ─────────────────────────────────────────────────────────── │
│ • Match by outreach_id + slot_type in people.company_slot   │
│ • Skip if slot already filled (is_filled = TRUE)            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Person Creation                                      │
│ ─────────────────────────────────────────────────────────── │
│ • Create people.people_master with Barton ID                │
│ • Format: 04.04.02.YY.NNNNNN.NNN                            │
│ • Link company_unique_id + company_slot_unique_id           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Slot Update                                          │
│ ─────────────────────────────────────────────────────────── │
│ • Set person_unique_id, is_filled = TRUE                    │
│ • Add slot_phone if phone number present                    │
│ • Set source_system = 'hunter'                              │
└─────────────────────────────────────────────────────────────┘
```

**Usage:**
```bash
doppler run -- python hubs/people-intelligence/imo/middle/phases/fill_slots_from_hunter.py <csv_path> [--dry-run]
```

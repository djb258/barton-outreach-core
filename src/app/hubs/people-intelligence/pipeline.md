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

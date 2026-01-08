# Follow-Up Prompt — Slot Resolution Ingestion

**Status:** ✅ EXECUTED → See P2_CANARY_INGESTION_VALIDATION.md

---

## Execution Summary

P2 Canary Ingestion was implemented on 2026-01-08 with:

- `people.slot_ingress_canary` — Canary allowlist table
- Augmented `people.slot_can_accept_candidate()` with 6 checks
- `people.v_candidate_canary_activity` — Observability view
- `people.v_canary_queue_depth` — Queue depth metrics
- Kill switch prepared (human must enable)

**Migration:** `2026-01-08-people-slot-canary-ingestion.sql`  
**Validation:** `P2_CANARY_INGESTION_VALIDATION.md`

---

## Next Phase: P3 Slot Resolution (DISABLED)

```
Claude Code Prompt — Slot Resolution Ingestion (Phase 2)

Mode: PEOPLE SUB-HUB SLOT INGESTION ENABLEMENT
Repo: barton-outreach-core
Database: Neon
Scope: Ingestion logic + worker wiring
Rules:

Candidates enter via people.people_candidate only

Guard function people.slot_can_accept_candidate() must pass

Kill switch people.slot_ingress_control must be ON

Tasks:

1. Create candidate_ingress_worker.py that:
   - Reads from people.people_candidate WHERE status = 'pending'
   - Calls people.slot_can_accept_candidate() for each
   - On success: Updates candidate status to 'accepted', links to slot
   - On failure: Updates candidate status to 'rejected' with reason

2. Add error codes:
   - PI-E601: Candidate submission failed (slot not found)
   - PI-E602: Candidate submission failed (slot not open)
   - PI-E603: Candidate submission failed (resolution pending)
   - PI-E604: Candidate submission failed (kill switch off)
   - PI-E605: Candidate duplicate detected

3. Create view people.v_candidate_queue_depth for observability

4. Wire worker into execution.yaml with:
   - Rate limit: 100 candidates/minute
   - Batch size: 10
   - Kill switch check before each batch

5. Update kill_switches.yaml with ingestion-specific controls

Hard Stop:

DO NOT enable kill switch — leave OFF
DO NOT backfill existing data
DO NOT touch people_master (that's Phase 3)
```

---

## Activation Gate

This prompt is LOCKED until:

1. P1 Slot Structure is in production for 48+ hours
2. No errors in `people.people_errors` related to slot structure
3. Business approval for candidate ingestion source
4. Kill switch tested in staging (enable → test → disable)

---

**Last Updated:** 2026-01-08  
**Author:** Claude Code (Doctrine Enforcer)  
**Phase:** P2 (DISABLED)

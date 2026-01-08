# Claude Code Prompt — Phase 2 Spine Enforcement

Use this prompt after P0 migrations are validated and all `NO_SPINE_RECORD` entries resolved.

---

## Context

P0 migrations have been applied:
- `P0_001_dol_spine_alignment.sql` — DOL tables have `outreach_id` column
- `P0_002_talent_flow_spine_alignment.sql` — Talent Flow tables have `outreach_id` columns
- `P0_003_outreach_execution_spine_alignment.sql` — Outreach Execution tables created with FK

All backfill coverage is now at 100%.

---

## Claude Code Prompt

```
You are operating in PHASE 2 ENFORCEMENT MODE
Repo: barton-outreach-core
Database: Neon (PostgreSQL)
Doctrine: Spine-First, CC, IMO, Binary Outcomes
Scope: DOL, Talent Flow, Outreach Execution

## Prerequisites (VERIFY FIRST)
- P0_001, P0_002, P0_003 migrations applied
- Validation checklist PASSED
- All NO_SPINE_RECORD entries resolved
- Backfill coverage at 100%

## Rules
- No data deletion
- Application code changes ALLOWED
- Triggers CAN be rewritten
- FK constraints CAN be enforced
- Legacy columns CAN be deprecated (not dropped yet)

## Step 1 — DOL FK Enforcement

1. Add NOT NULL constraint to dol.ein_linkage.outreach_id
2. Add FK constraint: dol.ein_linkage.outreach_id -> outreach.outreach(outreach_id)
3. Mark company_unique_id as DEPRECATED in column comment
4. Update any DOL Python code to use outreach_id

## Step 2 — Talent Flow FK Enforcement + Trigger Rewrite

1. Add FK constraints:
   - talent_flow.movements.from_outreach_id -> outreach.outreach(outreach_id)
   - talent_flow.movements.to_outreach_id -> outreach.outreach(outreach_id)
   - svg_marketing.talent_flow_movements.outreach_id -> outreach.outreach(outreach_id)

2. Rewrite trg_movements_create_bit_event trigger:
   - Remove: INSERT INTO bit.events with company_unique_id
   - Add: INSERT INTO outreach.bit_signals with outreach_id
   - Ensure correlation_id is passed through

3. Mark old_company_id/new_company_id as DEPRECATED

## Step 3 — Code Alignment

1. Update dol_hub.py to use outreach_id instead of company_unique_id
2. Update ein_matcher.py to use outreach_id
3. Update any Talent Flow Python code
4. Add doctrine guards to prevent company_unique_id usage

## Step 4 — Output

Produce:
- SQL migration files (P1_001, P1_002, P1_003)
- Rollback SQL for each
- Updated Python code with diffs
- Test queries to verify enforcement

## Hard Stop Conditions

STOP and report if:
- Any table has records with NULL outreach_id
- Any FK constraint would violate referential integrity
- Any trigger rewrite would lose data
```

---

## Expected Deliverables

| Artifact | Purpose |
|----------|---------|
| `P1_001_dol_fk_enforcement.sql` | Add FK constraint to DOL |
| `P1_002_talent_flow_fk_enforcement.sql` | Add FK constraints + trigger rewrite |
| `P1_003_code_alignment.py` | Python code updates |
| `P1_VALIDATION_CHECKLIST.md` | Phase 2 validation |
| Updated Python files | Code aligned to outreach_id |

---

## Phase 3 Preview (After Phase 2)

Phase 3 will handle:
- Dropping legacy columns (company_unique_id, old_company_id, new_company_id)
- Removing deprecated triggers
- Final schema cleanup
- Documentation updates

---

**Last Updated:** 2026-01-08
**Author:** Claude Code (Schema Remediation Engineer)
**Status:** READY FOR PHASE 2 (after P0 validation passes)

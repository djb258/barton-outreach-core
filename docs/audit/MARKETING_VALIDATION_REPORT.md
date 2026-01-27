# Marketing Readiness & Ops Validation Report
**Generated:** 2026-01-19T12:00:00Z  
**Mode:** READ-ONLY / DRY-RUN  
**Agent:** Marketing Readiness & Ops Validation Agent

---

## Executive Summary

⚠️ **CRITICAL FINDING:** The sovereign completion views and kill switch tables have not been deployed to production. The migrations created on 2026-01-19 are pending execution.

---

## 1. Marketing Tier Distribution Audit

### Current Schema State

| Component | Status | Notes |
|-----------|--------|-------|
| `outreach.vw_marketing_eligibility_with_overrides` | ❌ NOT EXISTS | Migration required |
| `outreach.vw_sovereign_completion` | ❌ NOT EXISTS | Migration required |
| `outreach.vw_marketing_eligibility` | ❌ NOT EXISTS | Migration required |
| `outreach.hub_registry` | ❌ NOT EXISTS | Migration required |
| `outreach.manual_overrides` | ❌ NOT EXISTS | Migration required |
| `outreach.company_target` | ✅ EXISTS | 74,173 rows |
| `outreach.bit_scores` | ✅ EXISTS | 1 row |
| `outreach.bit_signals` | ✅ EXISTS | 1 row |

### Simulated Tier Distribution (from base tables)

Since the marketing eligibility view doesn't exist, tier distribution was simulated from `bit_score_snapshot`:

| Tier | Name | Count | Percentage | Notes |
|------|------|-------|------------|-------|
| -1 | INELIGIBLE | 74,173 | 100.0% | All records have NULL bit_score_snapshot |
| 0 | Cold | 0 | 0.0% | |
| 1 | Persona | 0 | 0.0% | |
| 2 | Trigger | 0 | 0.0% | |
| 3 | Aggressive | 0 | 0.0% | |
| **Total** | | **74,173** | | |

### Analysis of Base Data

```
Company Target Stats:
- Total records: 74,173
- With company_unique_id: 33,921 (45.7%)
- With bit_score_snapshot: 0 (0%)
- Outreach status: queued=74,062, disqualified=111
```

### Tier 3 Entries Analysis

**No Tier 3 entries exist** - this is expected since:
1. Views are not deployed
2. No bit_score_snapshot values are populated
3. Hub status tracking tables don't exist

---

## 2. Override & Kill Switch Validation

### Table Status

| Table | Status |
|-------|--------|
| `outreach.manual_overrides` | ❌ NOT EXISTS |
| `outreach.override_audit_log` | ❌ NOT EXISTS |
| `outreach.hub_registry` | ❌ NOT EXISTS |
| `outreach.company_hub_status` | ❌ NOT EXISTS |
| `outreach.gate_registry` | ❌ NOT EXISTS |

### TTL Expiration

**Cannot validate** - tables not created.

### Tier Cap Enforcement

**Cannot validate** - views not created.

### Audit Logging

**Cannot validate** - audit log table not created.

---

## 3. Campaign Assignment DRY RUN

### Would-Have-Sent Counts by Tier

Since views don't exist, using simulated data:

| Tier | Eligible | Blocked by Override | Would Send |
|------|----------|---------------------|------------|
| -1 | 74,173 | N/A | 0 (EXCLUDED) |
| 0 | 0 | 0 | 0 |
| 1 | 0 | 0 | 0 |
| 2 | 0 | 0 | 0 |
| 3 | 0 | 0 | 0 |

**Tier -1 Excluded:** 74,173 (100% of records)

### Kill Switch Validation

**Cannot validate** - `manual_overrides` table does not exist.

### Campaign Readiness Assessment

| Check | Status | Details |
|-------|--------|---------|
| Tier exclusion logic | ⚠️ UNVERIFIED | Views not deployed |
| Tier cap enforcement | ⚠️ UNVERIFIED | Override tables not deployed |
| marketing_disabled blocking | ⚠️ UNVERIFIED | Override tables not deployed |
| Audit trail | ⚠️ UNVERIFIED | Audit log not deployed |

---

## 4. Regression Simulation

### Scenario: Required Hub PASS → FAIL

**Cannot simulate full regression** - views not created.

However, based on the migration code review:

#### Expected Behavior (per design)

1. **If company-target regresses PASS → FAIL:**
   - `overall_status` would change to `BLOCKED`
   - `effective_tier` would drop to `-1` (INELIGIBLE)
   - `missing_requirements` JSONB would populate with failure details
   - Company excluded from all campaigns

2. **If People Intelligence regresses PASS → FAIL:**
   - `people_status` would change to `FAIL`
   - `overall_status` would change to `BLOCKED` (required hub failed)
   - Marketing tier would drop to `-1`

3. **Kill switch activation on regression:**
   - Per design, regression triggers `overall_status = BLOCKED`
   - No automatic `marketing_disabled` override is created
   - Manual intervention required for explicit disable

#### Design Verification

| Behavior | Implementation Status |
|----------|----------------------|
| Tier downgrade on hub failure | ✅ Coded in `vw_sovereign_completion` |
| BLOCKED status propagation | ✅ Coded in tier logic |
| UI-facing status reflection | ✅ Designed in `vw_marketing_eligibility_with_overrides` |
| Automatic kill switch | ❌ NOT IMPLEMENTED (requires manual override) |

---

## 5. Anomalies Detected

### Critical Issues

⚠️ **SCHEMA_INCOMPLETE:** Views not yet created. Migrations need to be run:
- `2026-01-19-hub-registry.sql`
- `2026-01-19-sovereign-completion-view.sql`
- `2026-01-19-kill-switches.sql`

⚠️ **KILL_SWITCH_MISSING:** `manual_overrides` table does not exist - kill switches not implemented

⚠️ **DATA_GAP:** 40,252 records (54.3%) have NULL `company_unique_id` - CL-gate violation risk

⚠️ **BIT_SCORE_EMPTY:** 0 records have `bit_score_snapshot` populated

### Data Quality Issues

| Issue | Count | Impact |
|-------|-------|--------|
| NULL company_unique_id | 40,252 | Cannot link to CL, blocks completion |
| NULL bit_score_snapshot | 74,173 | All companies at Tier -1 |
| NULL first_targeted_at | 74,173 | Targeting history incomplete |

---

## 6. Existing System Analysis

### Current BIT Infrastructure

The existing `outreach.bit_scores` and `outreach.bit_signals` tables show:

```
BIT Scores (1 record):
- outreach_id: 801d5139-e50c-41d3-b9d8-4d2aef864f9b
- score: 10.00
- score_tier: COLD
- people_score: 10.00
- dol_score: 0.00
- blog_score: 0.00
- talent_flow_score: 0.00

BIT Signals (1 record):
- signal_type: slot_filled
- signal_impact: 10.00
- source_spoke: people_subhub
```

This indicates the BIT engine is functional but only 1 company has been scored.

### Gap Analysis

| Expected (per migrations) | Actual | Gap |
|---------------------------|--------|-----|
| hub_registry table | None | CREATE TABLE required |
| company_hub_status table | None | CREATE TABLE required |
| vw_sovereign_completion view | None | CREATE VIEW required |
| vw_marketing_eligibility view | None | CREATE VIEW required |
| vw_marketing_eligibility_with_overrides view | None | CREATE VIEW required |
| manual_overrides table | None | CREATE TABLE required |
| override_audit_log table | None | CREATE TABLE required |

---

## 7. Deployment Checklist

### Required Actions Before Live Sends

- [ ] Run migration: `2026-01-19-hub-registry.sql`
- [ ] Run migration: `2026-01-19-sovereign-completion-view.sql`
- [ ] Run migration: `2026-01-19-kill-switches.sql`
- [ ] Backfill `company_hub_status` for existing companies
- [ ] Verify `vw_marketing_eligibility_with_overrides` returns correct data
- [ ] Test kill switch functions (`fn_disable_marketing`, etc.)
- [ ] Re-run this validation after migrations

### Post-Migration Verification

- [ ] Query tier distribution from authoritative view
- [ ] Verify Tier 3 entries qualify correctly
- [ ] Test TTL expiration with test override
- [ ] Simulate regression scenario
- [ ] Verify audit logging

---

## 8. Final Verdict

### ❌ Safe to enable live sends: **NO**

**Reasons:**
1. Views not created - migrations required
2. Kill switch tables not created - cannot block companies
3. Hub status tracking not deployed - cannot compute completion
4. 0% of companies have BIT scores populated
5. 54.3% of companies have NULL company_unique_id (CL-gate violation)

### Recommended Actions

1. **IMMEDIATE:** Run the three 2026-01-19 migrations in order:
   ```bash
   doppler run -- psql -f infra/migrations/2026-01-19-hub-registry.sql
   doppler run -- psql -f infra/migrations/2026-01-19-sovereign-completion-view.sql
   doppler run -- psql -f infra/migrations/2026-01-19-kill-switches.sql
   ```

2. **THEN:** Backfill hub statuses for existing companies

3. **THEN:** Re-run this validation report

4. **THEN:** Review Tier 3 entries for correctness

5. **FINALLY:** If all validations pass, safe to enable live sends

---

## Appendix: Migration Files Ready for Deployment

| File | Purpose | Dependencies |
|------|---------|--------------|
| `2026-01-19-hub-registry.sql` | Hub classification, status tracking | None |
| `2026-01-19-sovereign-completion-view.sql` | Completion and marketing tier views | hub-registry |
| `2026-01-19-kill-switches.sql` | Override system, audit logging | sovereign-completion-view |

---

*Report generated by Marketing Readiness & Ops Validation Agent*  
*Mode: READ-ONLY / DRY-RUN*  
*No production data was modified during this validation*

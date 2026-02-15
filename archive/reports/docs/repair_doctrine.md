# Repair Doctrine

**Status:** LOCKED — NO EXCEPTIONS
**Version:** 1.0
**Last Updated:** 2026-01-01

---

## Purpose

This document defines **how failures are repaired** without corrupting lineage, signals, or cost accounting.

Repairs are the mechanism by which blocked pipelines become unblocked. This doctrine ensures that repairs:

- Never rewrite history
- Never fabricate signals
- Never grant retroactive authority
- Always maintain auditability

**This is doctrine, not guidance. There are no exceptions.**

---

## Core Repair Principles

### Principle 1: Repairs Never Modify History

| Artifact | Immutability |
|----------|--------------|
| Error rows | IMMUTABLE — `resolved_at` may be set, row never deleted |
| Signals already emitted | IMMUTABLE — never modified, never deleted |
| Prior contexts | IMMUTABLE — never edited, never reopened |
| Cost logs | IMMUTABLE — never adjusted retroactively |
| Finalized contexts | IMMUTABLE — `final_state` never changes after set |

**Consequence:** If you need "different" data, you create a new context. You do not edit the old one.

---

### Principle 2: Repairs Unblock, They Do Not Rewrite

A repair resolves an error so that:

- A new context can attempt the same work
- The system state is consistent
- Future runs are not blocked

A repair **does not**:

- Alter upstream outputs
- Fabricate missing signals
- Backfill data that wasn't collected
- Grant retroactive permissions

| Valid Repair | Invalid Repair |
|--------------|----------------|
| Fix source data, create new context | Edit error row to "pretend" it succeeded |
| Deploy code fix, create new context | Modify signal emitted in prior context |
| Manual data entry, create new context | Backdate a signal to prior context |
| Mark error as resolved with note | Delete error row |

---

### Principle 3: Repairs Always Create a New Context

Any re-attempt after a failure requires a **new `outreach_context_id`**.

```
FAILED Context A
      ↓
   [REPAIR]
      ↓
NEW Context B (starts fresh, no inherited signals)
```

### Context Lineage Rules

| Rule | Enforcement |
|------|-------------|
| New context starts with zero authoritative signals | Signals must be re-acquired |
| Prior context signals are informational only | Cannot be used for gating |
| Cost accounting starts fresh | New context, new spend tracking |
| Prior context remains for audit | Never deleted, never modified |

### Context Inheritance is FORBIDDEN

A new context may **not**:

- Inherit signals from a prior context
- Reference prior context signals as authoritative
- "Resume" a prior context's state
- Merge prior context data as if it were current

---

### Principle 4: No Cross-Hub Repair Authority

A hub may repair **only its own errors**.

| Hub | May Repair | May NOT Repair |
|-----|------------|----------------|
| Company Target | CT_* errors | PI_*, DOL_*, OE_*, BC_* errors |
| People Intelligence | PI_* errors | CT_*, DOL_*, OE_*, BC_* errors |
| DOL Filings | DOL_* errors | CT_*, PI_*, OE_*, BC_* errors |
| Blog Content | BC_* errors | CT_*, PI_*, DOL_*, OE_* errors |

### Cross-Hub Repair Flow

If a downstream error requires upstream repair:

```
PI_NO_PATTERN_AVAILABLE (People Intelligence error)
      ↓
   Requires CT repair first
      ↓
   Human repairs CT root cause
      ↓
   NEW Company Target context runs
      ↓
   CT emits pattern signal
      ↓
   NEW People Intelligence context can now proceed
```

**The downstream hub does not repair the upstream hub. It waits.**

---

## What Qualifies as a Repair

### Valid Repairs

| Repair Type | Description | Example |
|-------------|-------------|---------|
| **Source data fix** | Fix input data quality issue | Correct malformed CSV, fix EIN format |
| **Code deployment** | Deploy bug fix | Fix regex pattern that caused match failure |
| **Configuration update** | Update tool registry, thresholds | Add new tool to registry, adjust BIT threshold |
| **Manual data entry** | Human provides missing data | Manual domain entry after all tools exhausted |
| **Error resolution** | Mark error as resolved with note | `resolved_at = NOW(), resolution_note = "..."` |

### Invalid Repairs (FORBIDDEN)

| Forbidden Action | Why It's Forbidden |
|------------------|-------------------|
| Edit signal value | Corrupts lineage |
| Delete error row | Destroys audit trail |
| Reopen finalized context | Violates immutability |
| Backdate signal | Fabricates history |
| Import prior context signals as authoritative | Violates run-bound invariant |
| Modify cost logs | Corrupts financial audit |
| Force-pass a failed gate | Bypasses doctrine |

---

## Explicitly Forbidden Repair Patterns

### Forbidden: History Mutation

```python
# FORBIDDEN — Modifying error row
UPDATE outreach_errors.company_target_errors
SET failure_code = 'CT_PASS'  -- NEVER
WHERE error_id = '...';
```

### Forbidden: Signal Fabrication

```python
# FORBIDDEN — Creating signal for past context
INSERT INTO signals (context_id, signal_type)
VALUES ('old-context-id', 'domain_verified');  -- NEVER
```

### Forbidden: Context Resurrection

```python
# FORBIDDEN — Reopening finalized context
UPDATE outreach_ctx.context
SET final_state = NULL,  -- NEVER
    is_active = TRUE
WHERE outreach_context_id = '...';
```

### Forbidden: Cross-Hub Repair

```python
# FORBIDDEN — People Intelligence fixing Company Target
def repair_missing_pattern():
    # People hub cannot create patterns
    company_target.emit_pattern_signal(...)  -- NEVER
```

### Forbidden: Inheritance

```python
# FORBIDDEN — Using old context signals in new context
def new_context_run():
    old_signals = get_signals(old_context_id)
    if old_signals.pattern:
        # Using old signal as authoritative
        proceed_with(old_signals.pattern)  -- NEVER
```

---

## Human vs Agent Repair Authority

### Human Repairs

Humans may:

| Action | Example |
|--------|---------|
| Fix source data | Correct CSV, update company_master |
| Deploy code fixes | Bug fixes, new error codes |
| Resolve errors | Mark error as resolved with note |
| Create new context | Request new run with fixed data |
| Update configuration | Tool registry, thresholds |

Humans may NOT:

| Forbidden | Reason |
|-----------|--------|
| Edit signals | Corrupts lineage |
| Delete errors | Destroys audit trail |
| Bypass gates | Violates doctrine |
| Reopen contexts | Violates immutability |

### Agent Repairs

Agents may:

| Action | Example |
|--------|---------|
| Create new context | Automatic retry with new context |
| Re-run pipeline | With new context ID |
| Log retry attempt | Audit trail of retry |

Agents may NOT:

| Forbidden | Reason |
|-----------|--------|
| Edit signals | Corrupts lineage |
| Fix source data | Human judgment required |
| Deploy code | Human approval required |
| Resolve errors | Human judgment required |
| Bypass gates | Violates doctrine |

---

## Context Lineage Examples

### Example 1: Pattern Discovery Failure → Repair → Success

**Before (Failed Context A)**
```
Context A (FAIL)
├── company_sov_id: abc-123
├── phase: phase3_email_pattern_waterfall
├── error: CT_TIER2_EXHAUSTED
├── cost: $2.50
├── final_state: FAIL
└── finalized_at: 2026-01-01 10:00:00
```

**Repair Action**
```
Human investigates → finds company website has unusual structure
Human manually discovers pattern → enters in company_master
Human marks error as resolved → resolution_note: "Manual pattern entry"
```

**After (New Context B)**
```
Context B (PASS)
├── company_sov_id: abc-123
├── phases: all PASS
├── pattern: (manual entry) first.last@domain.com
├── cost: $0.00 (no tool calls needed)
├── final_state: PASS
└── finalized_at: 2026-01-01 11:00:00

Context A (FAIL) — UNCHANGED, still exists for audit
```

### Example 2: Cross-Hub Dependency Repair

**Before**
```
Context A - Company Target: PASS (pattern emitted)
Context A - DOL Filings: PASS
Context A - People Intelligence: FAIL (PI_SLOT_COLLISION)
Context A - Blog: NOT EXECUTED
```

**Repair Action**
```
Human investigates slot collision → two people claiming same slot
Human chooses winner → updates people_master
Human marks error as resolved
```

**After**
```
Context A - UNCHANGED (FAIL overall, PI failed)

Context B - Company Target: PASS (re-acquired pattern)
Context B - DOL Filings: PASS (re-processed filings)
Context B - People Intelligence: PASS (collision resolved)
Context B - Blog: PASS
Context B - final_state: PASS
```

**Key:** Context B re-acquired ALL signals. It did not inherit Context A's signals.

---

## Repair Resolution Workflow

### Step 1: Identify Error

```sql
SELECT * FROM outreach_errors.all_unresolved_errors
WHERE severity = 'blocking'
ORDER BY created_at DESC;
```

### Step 2: Determine Repair Owner

| Error Prefix | Repair Owner |
|--------------|--------------|
| CT_* | Company Target team |
| PI_* | People Intelligence team |
| DOL_* | DOL Filings team |
| BC_* | Blog Content team |
| OE_* | Outreach Execution team |

### Step 3: Execute Repair

1. Fix root cause (source data, code, config)
2. Mark error as resolved:
   ```sql
   SELECT outreach_errors.resolve_error(
       'company_target_errors',
       'error-uuid',
       'Root cause: malformed domain. Fix: corrected in company_master.',
       'human@example.com'
   );
   ```

### Step 4: Create New Context

```sql
SELECT outreach_ctx.create_context(
    'company-sov-id',
    'run',
    'ACTIVE',
    24,  -- TTL hours
    'Retry after repair',
    'human@example.com'
);
```

### Step 5: Re-run Pipeline

Execute pipeline with new context. All signals re-acquired fresh.

---

## Repair Audit Requirements

Every repair must be auditable:

| Requirement | How |
|-------------|-----|
| Who repaired | `resolved_by` column on error |
| When repaired | `resolved_at` column on error |
| What was done | `resolution_note` column on error |
| New context link | Optional `retry_context_id` reference |

---

## Post-Repair Invariants

After any repair:

1. Old context remains IMMUTABLE
2. Old signals remain IMMUTABLE
3. Old errors remain (with `resolved_at` set)
4. New context starts fresh
5. New signals acquired independently
6. Cost accounting is separate per context

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-01-01 | 1.0 | Initial doctrine lock |

---

*This document is LOCKED. Changes require architecture review.*

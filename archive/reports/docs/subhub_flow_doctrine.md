# Sub-Hub Flow Doctrine

**Status:** LOCKED — NO EXCEPTIONS
**Version:** 1.0
**Last Updated:** 2026-01-01

---

## Purpose

This document defines the **only valid execution order**, **signal flow rules**, and **signal validity constraints** for all outreach sub-hubs.

This doctrine exists to:
- Eliminate interpretive ambiguity
- Prevent future maintainers from introducing lateral dependencies
- Lock signal semantics against "creative" workarounds

**This is doctrine, not guidance. There are no exceptions.**

---

## Canonical Sub-Hub Execution Order

```
Company Target
      ↓
DOL Filings
      ↓
People Intelligence
      ↓
Blog / Content
```

### Execution Rules

1. **Order is mandatory** — Sub-hubs execute in exactly this sequence
2. **FAIL propagates forward** — If any sub-hub FAILs, the `outreach_context_id` is finalized as FAIL
3. **No continuation after FAIL** — All downstream sub-hubs must not execute
4. **No implicit continuation** — Execution does not "skip and continue"

### Failure Propagation

| Failing Hub | Effect |
|-------------|--------|
| Company Target | DOL, People, Blog do NOT execute |
| DOL Filings | People, Blog do NOT execute |
| People Intelligence | Blog does NOT execute |
| Blog / Content | Context finalized (no downstream) |

---

## Flow Principle 1: One-Way Signal Flow

Sub-hubs may **only consume signals from upstream hubs**.

### Signal Rules

- Signals are **read-only context**
- Signals flow **forward only**
- No hub may:
  - Modify upstream outputs
  - Repair upstream failures
  - Backfill missing upstream data
  - Re-query upstream for "fresher" data

> **Signals inform decisions; they do not grant authority.**

### Visual Flow

```
Company Target ──────────────────────────────────────────────────→
       │                                                          │
       │ domain, pattern, BIT                                     │
       ↓                                                          │
DOL Filings ───────────────────────────────────────────→          │
       │                                                │         │
       │ regulatory_signals                             │         │
       ↓                                                ↓         ↓
People Intelligence ─────────────────────────────────────────────→
       │                                                          │
       │ slot_fill, contacts                                      │
       ↓                                                          ↓
Blog / Content ←───────────────────────────────────────(read all)─┘
       │
       ↓
  (timing signals only — NO spend, NO enrichment)
```

---

## Flow Principle 2: Authority Boundaries

Each sub-hub has **explicit ownership** and **explicit prohibitions**.

| Sub-Hub | Owns | May Consume | Forbidden |
|---------|------|-------------|-----------|
| **Company Target** | Domain, pattern, BIT score | Lifecycle state from CL | Any downstream signal |
| **DOL Filings** | Regulatory signals, filing data | Company Target outputs | Unlocking People alone |
| **People Intelligence** | Slot fill, people records | Company Target + DOL signals | Fixing Company Target errors |
| **Blog / Content** | Timing signals only | All upstream signals | Triggering enrichment or spend |

### Boundary Violations

The following are **doctrine violations**:

- People Intelligence consuming a Blog signal
- DOL Filings modifying Company Target's pattern
- Blog Content triggering a Clay enrichment
- Any hub "helping" another hub by backfilling data

---

## Signal Validity Doctrine

All downstream hubs must treat signals as **contextual artifacts**, subject to the following invariants.

### Invariant 1: Origin-Bound

A signal must originate from its declared upstream sub-hub.

- Signals may not be reused outside their origin contract
- A signal from Company Target cannot be "relabeled" as a DOL signal
- If origin is unclear, the signal is invalid

### Invariant 2: Run-Bound

Signals are valid **only within the same `outreach_context_id`**.

- Signals from prior contexts are informational at best
- Signals from prior contexts are **never authoritative**
- A new context starts with zero authoritative signals

### Invariant 3: Non-Refreshing

Downstream hubs may **not re-enrich, refresh, or recompute** upstream signals.

- If a signal is missing → do nothing
- If a signal is stale → do nothing
- The correct action is **FAIL**, not "try again"

### Invariant 4: Age is Informational Only

Signal age may be observed or logged, but **must not**:

- Trigger retries
- Trigger enrichment
- Justify overrides
- Unlock gated behaviors

> **A signal existing "somewhere" is not permission to use it.**

---

## Explicitly Forbidden Patterns

The following patterns are **doctrine violations**:

### Forbidden: Lateral Exception Paths

```
# FORBIDDEN
if upstream_missing:
    try_alternative_source()
```

### Forbidden: Soft-Fail Language

```
# FORBIDDEN
if signal_stale:
    log_warning("proceeding anyway")
    continue_execution()
```

### Forbidden: Rescue Semantics

```
# FORBIDDEN
try:
    get_upstream_signal()
except MissingSignal:
    generate_fallback_signal()
```

### Forbidden: Override Verbs

```
# FORBIDDEN
force_proceed = True
skip_validation = True
bypass_gate = True
```

### Forbidden: Retry Implications

```
# FORBIDDEN
if signal_age > threshold:
    refresh_from_source()
```

---

## PASS and FAIL Remain Binary

There is no third state. There is no "partial success."

| State | Meaning | Downstream Effect |
|-------|---------|-------------------|
| **PASS** | All signals emitted, all gates met | Next hub may execute |
| **FAIL** | Blocking error emitted, context finalized | All downstream halted |

### Ambiguous States Are FAIL

If you cannot determine PASS, the answer is FAIL.

- "Mostly worked" → FAIL
- "Some signals emitted" → FAIL
- "Waiting for retry" → FAIL
- "Needs human review" → FAIL

---

## Post-Doctrine Invariants

After this doctrine is adopted, the system **must guarantee**:

1. Exactly one valid sub-hub execution order
2. Signals flow forward only
3. Signals are origin-bound (declared source only)
4. Signals are run-bound (same `outreach_context_id` only)
5. Signal age cannot justify action
6. No downstream hub rescues upstream failures
7. Blog never triggers spend or enrichment
8. PASS and FAIL are binary with no third state

---

## Enforcement

This doctrine is enforced through:

1. **Code review** — PRs that violate doctrine are rejected
2. **CHECKLIST verification** — Each sub-hub has doctrine compliance items
3. **Error emission** — Violations emit blocking errors
4. **CI guards** — Static analysis for forbidden patterns

---

## Doctrine Violations

If you observe a doctrine violation:

1. **STOP** — Do not work around it
2. **Document** — Record the violation in the error log
3. **Escalate** — Surface to the architecture owner
4. **Do not infer** — Do not guess what "should" happen

If ambiguity exists in this doctrine:

1. **STOP** — Do not interpret
2. **Explain** — Document the ambiguity
3. **Propose** — Offer one deterministic clarification
4. **Wait** — Do not proceed until resolved

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-01-01 | 1.0 | Initial doctrine lock |

---

*This document is LOCKED. Changes require architecture review.*

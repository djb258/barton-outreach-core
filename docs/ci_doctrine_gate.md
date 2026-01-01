# CI Doctrine Gate

**Status:** LOCKED — NO EXCEPTIONS
**Version:** 1.0
**Last Updated:** 2026-01-01

---

## Purpose

This document defines **CI rules that prevent doctrine drift** and make violations impossible to merge silently.

CI is **doctrine-aware**, not feature-aware. It enforces invariants, not business logic.

**Doctrine violations must block merges. There are no soft warnings.**

---

## CI Philosophy

### What CI Does

| Action | Description |
|--------|-------------|
| Parse code | Detect forbidden patterns |
| Diff documentation | Ensure PRD/CHECKLIST consistency |
| Validate imports | Detect cross-hub violations |
| Check tool usage | Ensure context enforcement |
| Fail loudly | Block merges on violation |

### What CI Does NOT Do

| Forbidden | Why |
|-----------|-----|
| Make decisions | Doctrine is deterministic |
| Auto-fix violations | Human judgment required |
| Silence warnings | All violations are blocking |
| Approve with conditions | No conditional approvals |
| Create exceptions | Exceptions create drift |

---

## CI Guard Rules (MANDATORY)

All rules are blocking. There are no warnings.

---

### Rule 1: Tool Usage Violations

**CI must FAIL if:**

| Violation | Detection |
|-----------|-----------|
| Paid tool invoked without `outreach_context_id` | Grep for tool calls without context param |
| Tool not listed in `tooling/tool_registry.md` | Cross-reference tool calls against registry |
| Tier-2 tool called without single-attempt guard | Check for `can_attempt_tier2()` call |
| Tool spend not logged | Check for `log_tool_attempt()` call |

**Example Detection:**

```yaml
# Fail if Hunter.io called without context
- name: Check tool context enforcement
  run: |
    if grep -r "hunter\.io" hubs/ --include="*.py" | grep -v "outreach_context_id"; then
      echo "FAIL: Hunter.io called without context enforcement"
      exit 1
    fi
```

---

### Rule 2: Sub-Hub Boundary Violations

**CI must FAIL if:**

| Violation | Detection |
|-----------|-----------|
| Hub imports from downstream hub | Check import statements |
| Hub consumes undeclared signal | Cross-reference PRD signal declarations |
| Hub emits to wrong consumer | Check signal routing |
| Lateral hub-to-hub calls | Detect non-spoke cross-hub imports |

**Forbidden Import Patterns:**

```python
# Company Target (first) importing from People (third) - FORBIDDEN
from hubs.people_intelligence import ...

# People Intelligence importing from Blog (fourth) - FORBIDDEN
from hubs.blog_content import ...

# Any hub importing non-spoke from another hub - FORBIDDEN
from hubs.other_hub.imo.middle import ...
```

**Allowed Import Patterns:**

```python
# Spoke imports are allowed (they're I/O only)
from spokes.company_people import ...

# Shared utilities are allowed
from shared.logger import ...
```

---

### Rule 3: Doctrine Drift

**CI must FAIL if:**

| Violation | Detection |
|-----------|-----------|
| PRD updated without CHECKLIST update | Diff both files in same PR |
| Pipeline logic added without doctrine section | Check for new phases without docs |
| New error code without error_codes.md update | Cross-reference error codes |
| New tool without tool_registry.md update | Cross-reference tool calls |

**Example Detection:**

```yaml
- name: Check doctrine consistency
  run: |
    # If PRD changed, CHECKLIST must also change
    if git diff --name-only HEAD~1 | grep "PRD.md"; then
      if ! git diff --name-only HEAD~1 | grep "CHECKLIST.md"; then
        echo "FAIL: PRD updated without CHECKLIST update"
        exit 1
      fi
    fi
```

---

### Rule 4: Signal Doctrine Violations

**CI must FAIL if:**

| Violation | Detection |
|-----------|-----------|
| Signal reused across contexts | Check for context_id in signal queries |
| Signal consumed from non-declared hub | Cross-reference PRD signal tables |
| Signal age used to justify action | Grep for age-based conditionals |
| Signal refresh attempted | Grep for re-query patterns |

**Forbidden Patterns:**

```python
# Signal from old context - FORBIDDEN
old_signal = get_signal(old_context_id)
if old_signal.valid:
    proceed()  # FORBIDDEN

# Signal age justifying action - FORBIDDEN
if signal.age < timedelta(hours=24):
    use_signal(signal)  # FORBIDDEN

# Signal refresh - FORBIDDEN
if signal.stale:
    signal = refresh_from_source()  # FORBIDDEN
```

---

### Rule 5: Lifecycle Violations

**CI must FAIL if:**

| Violation | Detection |
|-----------|-----------|
| Any write to lifecycle state | Grep for lifecycle UPDATE statements |
| Lifecycle mutation in sub-hub code | Check for state change calls |
| Lifecycle bypass | Check for lifecycle gate skips |

**Forbidden Patterns:**

```python
# FORBIDDEN - Sub-hub mutating lifecycle
company.lifecycle_state = 'ENGAGED'

# FORBIDDEN - Direct UPDATE
UPDATE cl.company_identity SET lifecycle_state = ...

# FORBIDDEN - Bypassing gate
skip_lifecycle_check = True
```

---

### Rule 6: Repair Doctrine Violations

**CI must FAIL if:**

| Violation | Detection |
|-----------|-----------|
| Error row deletion | Grep for DELETE on error tables |
| Signal modification | Grep for UPDATE on signal tables |
| Context resurrection | Grep for reopening finalized contexts |
| Cross-hub repair | Check repair functions for hub boundaries |

**Forbidden Patterns:**

```sql
-- FORBIDDEN
DELETE FROM outreach_errors.company_target_errors ...

-- FORBIDDEN
UPDATE signals SET value = ... WHERE context_id = ...

-- FORBIDDEN
UPDATE outreach_ctx.context SET final_state = NULL ...
```

---

## CI Workflow Structure

### Workflow: `doctrine_guard.yml`

```yaml
name: Doctrine Guard

on:
  pull_request:
    branches: [main]

jobs:
  tool-usage:
    # Check tool context enforcement

  hub-boundaries:
    # Check import boundaries

  doctrine-consistency:
    # Check PRD/CHECKLIST consistency

  signal-validity:
    # Check signal doctrine

  lifecycle-protection:
    # Check lifecycle immutability

  repair-protection:
    # Check repair doctrine
```

---

## Violation Response

### On CI Failure

1. **Merge is BLOCKED** — No exceptions
2. **Violation is logged** — For audit trail
3. **PR author notified** — Must fix before merge
4. **No manual override** — No "merge anyway" button

### Fixing Violations

| Violation Type | Fix |
|----------------|-----|
| Tool usage | Add context enforcement |
| Hub boundary | Remove forbidden import |
| Doctrine drift | Update missing documentation |
| Signal validity | Fix signal consumption |
| Lifecycle | Remove lifecycle mutation |
| Repair | Remove forbidden pattern |

---

## CI Bypass Policy

**There is no CI bypass.**

| Request | Answer |
|---------|--------|
| "Can we merge with warning?" | NO |
| "Can we fix it later?" | NO |
| "It's just a small change" | NO |
| "We need this urgently" | NO |
| "Management approved" | NO |

If a legitimate case exists where doctrine must change:

1. **Update doctrine first** — Not the code
2. **Get architecture review** — Doctrine changes are serious
3. **Update CI rules** — To match new doctrine
4. **Then merge code** — Now it passes CI

---

## CI Scope Boundaries

### In Scope

| Check | Why |
|-------|-----|
| Import statements | Hub boundaries |
| Tool call sites | Context enforcement |
| Documentation diffs | Doctrine consistency |
| Error handling code | Repair doctrine |
| Signal queries | Signal validity |

### Out of Scope

| Not Checked | Why |
|-------------|-----|
| Business logic correctness | Not CI's job |
| Performance | Not doctrine-related |
| Code style | Separate linter |
| Test coverage | Separate check |

---

## Adding New CI Rules

To add a new CI rule:

1. **Document the invariant** — In relevant doctrine doc
2. **Define the violation** — What pattern is forbidden
3. **Create detection** — Grep, AST parse, or diff
4. **Add to workflow** — As blocking check
5. **Test with known violation** — Ensure it catches it

New CI rules must be:

- Deterministic (no judgment calls)
- Fast (< 60 seconds)
- Blocking (no warnings)
- Documented (in this file)

---

## CI Rule Registry

| Rule ID | Name | Checks | Blocking |
|---------|------|--------|----------|
| DG-001 | Tool Context | Paid tools have context | YES |
| DG-002 | Tool Registry | Tools in registry | YES |
| DG-003 | Hub Imports | No downstream imports | YES |
| DG-004 | Signal Declared | Signals in PRD | YES |
| DG-005 | PRD-CHECKLIST Sync | Both updated together | YES |
| DG-006 | Error Code Registry | Codes in error_codes.md | YES |
| DG-007 | Signal Context | Signals run-bound | YES |
| DG-008 | No Signal Refresh | No re-query patterns | YES |
| DG-009 | Lifecycle Immutable | No state writes | YES |
| DG-010 | Error Immutable | No DELETE on errors | YES |
| DG-011 | Context Immutable | No reopening contexts | YES |
| DG-012 | Signal Immutable | No UPDATE on signals | YES |

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-01-01 | 1.0 | Initial doctrine lock |

---

*This document is LOCKED. Changes require architecture review.*

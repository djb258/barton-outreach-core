# Sales / Client Hub — Non-Operational Enforcement Lock

**Doctrine Version**: 1.0
**Status**: LOCKED
**Applies To**: Sales Hub, Client Hub (when created)

---

## Absolute Authority Rule

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   SALES/CLIENT DECIDES. SALES/CLIENT RECORDS. SALES/CLIENT NEVER EXECUTES. │
│                                                                             │
│   If something must be DONE, it is done in a CHILD HUB, never in Sales.    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## What Sales/Client Hub IS

Sales/Client is a **constitutional parent hub** that exists to:

| Responsibility | Description |
|----------------|-------------|
| **Own Identity** | Mint and own `client_unique_id`, `opportunity_unique_id` |
| **Record State** | Track client lifecycle state (prospect, qualified, proposal, closed) |
| **Enforce Rules** | Evaluate promotion/demotion criteria |
| **Maintain Audit** | Immutable history of all state transitions |

---

## What Sales/Client Hub IS NOT

Sales/Client **does NOT**:

| Prohibition | Reason |
|-------------|--------|
| Run proposals | Execution logic belongs in child hubs |
| Send contracts | Outreach/Delivery hub responsibility |
| Execute pricing | Calculation belongs in child hubs |
| Pull CRM data | Integration hubs handle API calls |
| Call external APIs | All API calls forbidden in constitutional hubs |
| Orchestrate workflows | Workflow engines live in child hubs |
| Trigger jobs | Job scheduling forbidden |
| Contain workers | Worker processes forbidden |
| Contain pipelines | Pipeline execution forbidden |
| Act as a "brain" | Intelligence logic belongs in child hubs |

---

## Explicit Prohibitions (Enforced by CI)

The following patterns are **BLOCKED** in Sales/Client hub code:

### Forbidden Imports
```python
# BLOCKED - these indicate operational logic
import requests
import httpx
import aiohttp
import celery
import rq
import apscheduler
from salesforce import *
from hubspot import *
```

### Forbidden Patterns
```python
# BLOCKED - execution verbs
def run_*()
def process_*()
def execute_*()
def handle_*()
def fetch_*()
def sync_*()
def trigger_*()

# BLOCKED - operational classes
class *Worker:
class *Pipeline:
class *Task:
class *Job:
class *Engine:
```

### Allowed Patterns
```python
# ALLOWED - decision/record verbs
def evaluate_*()
def record_*()
def authorize_*()
def block_*()
def validate_*()
def audit_*()

# ALLOWED - state classes
class *State:
class *Validator:
class *Guard:
class *Recorder:
```

---

## Language Standards

### Forbidden Language

Never use in Sales/Client documentation or code:

| Forbidden | Replacement |
|-----------|-------------|
| "Sales runs..." | "Sales evaluates..." |
| "Sales processes..." | "Sales records..." |
| "Sales handles..." | "Sales authorizes..." |
| "Sales executes..." | "Sales blocks..." |
| "Sales fetches..." | (Move to child hub) |
| "Sales syncs..." | (Move to child hub) |

### Required Language

Always use in Sales/Client documentation:

- "Sales evaluates client readiness"
- "Sales records opportunity state"
- "Sales authorizes promotion to next stage"
- "Sales blocks invalid transitions"
- "Sales audits all state changes"

---

## Invariants (Must Always Be True)

```yaml
invariants:
  - id: SALES-INV-001
    rule: "Sales/Client performs no work"
    enforcement: CI + code review

  - id: SALES-INV-002
    rule: "All execution occurs in child hubs"
    enforcement: CI + code review

  - id: SALES-INV-003
    rule: "Sales/Client is a decision and record system only"
    enforcement: CI + code review

  - id: SALES-INV-004
    rule: "Any operational logic appearing in Sales/Client is a doctrine violation"
    enforcement: CI guard blocks merge
```

---

## Child Hub Delegation

All operational work MUST be delegated to child hubs:

| Operation | Delegated To |
|-----------|--------------|
| Send proposals | Outreach Execution Hub |
| Generate contracts | Document Generation Hub |
| Calculate pricing | Pricing Engine Hub |
| Sync CRM data | CRM Integration Hub |
| Schedule follow-ups | Calendar Hub |
| Track engagement | Engagement Hub |

---

## Validation Checklist

Before any PR to Sales/Client hub is merged, confirm:

- [ ] "Sales/Client performs no work"
- [ ] "All execution occurs in child hubs"
- [ ] "Sales/Client is a decision and record system only"
- [ ] No forbidden imports present
- [ ] No forbidden patterns present
- [ ] All new code uses allowed verbs only

**If any checkbox cannot be confirmed, the PR is REJECTED.**

---

## CI Enforcement

This doctrine is enforced by:

1. **`.github/workflows/constitutional-hub-guard.yml`** - Blocks operational patterns
2. **Pre-commit hooks** - Local enforcement
3. **Code review checklist** - Human verification

---

## Doctrine Lock Statement

```
This document is LOCKED.

No changes to the operational prohibition rules are permitted
without explicit doctrine council approval.

Sales/Client is a constitutional hub. It decides. It records.
It NEVER executes.
```

---

**Last Updated**: 2025-12-26
**Locked By**: Doctrine Enforcement Auditor

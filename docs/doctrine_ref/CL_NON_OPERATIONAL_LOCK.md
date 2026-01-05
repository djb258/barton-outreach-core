# Company Lifecycle (CL) — Non-Operational Enforcement Lock

**Doctrine Version**: 1.0
**Status**: LOCKED
**Authority Level**: CONSTITUTIONAL PARENT HUB

---

## Absolute Authority Rule

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│            CL DECIDES. CL RECORDS. CL NEVER EXECUTES.                       │
│                                                                             │
│   If something must be DONE, it is done in a CHILD HUB, never in CL.       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## What CL IS

The **Company Lifecycle (CL)** is a **constitutional parent hub**.

CL exists to:

| Responsibility | Description |
|----------------|-------------|
| **Own Identity** | Mint and own `company_unique_id` (SOLE authority) |
| **Record State** | Track company lifecycle state transitions |
| **Enforce Rules** | Evaluate promotion/demotion criteria |
| **Maintain Audit** | Immutable history of all state changes |

**CL is the SOVEREIGN identity authority.** No other hub may mint company identities.

---

## What CL IS NOT

CL **does NOT** perform work. All work is performed in **child sub-hubs**.

### Explicit Prohibitions

CL **MUST NOT**:

| Prohibition | Reason |
|-------------|--------|
| Run enrichment | Outreach/People hubs handle enrichment |
| Perform outreach | Outreach Execution hub responsibility |
| Execute fuzzy matching | CL IS identity - it doesn't search for it |
| Resolve people | People Intelligence hub responsibility |
| Pull DOL data | DOL Filings hub responsibility |
| Call external APIs | All API calls forbidden in CL |
| Orchestrate workflows | Workflow engines live in child hubs |
| Trigger jobs | Job scheduling forbidden |
| Contain "workers" | Worker processes forbidden |
| Contain "pipelines" | Pipeline execution forbidden |
| Contain "tasks" | Task execution forbidden |
| Act as a "brain" | Intelligence logic belongs in child hubs |
| Act as an "engine" | Engine terminology forbidden |

Any reference implying the above **MUST be removed or corrected**.

---

## CL Is Non-Operational (Required README Section)

The following statement MUST appear in CL's README.md:

```markdown
## CL Is Non-Operational

Company Lifecycle (CL) is a constitutional hub. It does not perform actions.

- CL has no execution responsibilities
- CL never initiates work
- CL only evaluates and records outcomes
- All operational logic lives in child hubs

If you need to DO something, do it in a child hub (Outreach, People, DOL).
If you need to DECIDE or RECORD something, CL handles it.
```

---

## Language Standards

### Forbidden Language (Remove or Rewrite)

| Forbidden | Correct Replacement |
|-----------|---------------------|
| "CL runs..." | "CL records..." |
| "CL processes..." | "CL evaluates..." |
| "CL handles..." | "CL authorizes..." |
| "CL executes..." | "CL blocks..." |
| "CL fetches..." | (Move to child hub) |
| "CL enriches..." | (Move to child hub) |
| "CL scrapes..." | (Move to child hub) |
| "CL syncs..." | (Move to child hub) |
| "CL triggers..." | (Move to child hub) |
| "CL orchestrates..." | (Move to child hub) |

### Required Language

| Use This | Meaning |
|----------|---------|
| "CL records" | Writes state to database |
| "CL evaluates" | Checks criteria |
| "CL authorizes" | Approves state transition |
| "CL blocks" | Rejects invalid transition |
| "CL audits" | Maintains history |

---

## Invariants (Absolute Rules)

```yaml
invariants:
  - id: CL-INV-001
    rule: "CL performs no work"
    enforcement: CI blocks merge

  - id: CL-INV-002
    rule: "All execution occurs in child hubs"
    enforcement: CI blocks merge

  - id: CL-INV-003
    rule: "CL is a decision and record system only"
    enforcement: CI blocks merge

  - id: CL-INV-004
    rule: "Any operational logic appearing in CL is a doctrine violation"
    enforcement: CI blocks merge

  - id: CL-INV-005
    rule: "CL is the SOLE identity authority"
    enforcement: CI blocks merge
```

---

## Child Hub Delegation Matrix

All operational work MUST be delegated:

| Operation | Delegated To | CL Role |
|-----------|--------------|---------|
| Enrich company data | Company Target Hub | Record enrichment state |
| Find executive contacts | People Intelligence Hub | Record slot fill status |
| Match DOL filings | DOL Filings Hub | Record match status |
| Send outreach | Outreach Execution Hub | Record campaign state |
| Scrape websites | Integration Hubs | Record scrape results |
| Call APIs | Integration Hubs | Record API responses |
| Calculate BIT scores | Company Target Hub | Record score |
| Fuzzy match companies | FORBIDDEN | CL IS identity |

---

## Forbidden Import Patterns

The following imports are **BLOCKED** in CL code:

```python
# HTTP clients (indicate API calls)
import requests          # BLOCKED
import httpx             # BLOCKED
import aiohttp           # BLOCKED

# Task queues (indicate workers)
import celery            # BLOCKED
import rq                # BLOCKED
import dramatiq          # BLOCKED

# Schedulers (indicate jobs)
import apscheduler       # BLOCKED
import schedule          # BLOCKED

# External SDKs (indicate integrations)
from salesforce import * # BLOCKED
from hubspot import *    # BLOCKED
import boto3             # BLOCKED

# Fuzzy matching (identity resolution)
from rapidfuzz import *  # BLOCKED
from fuzzywuzzy import * # BLOCKED
from thefuzz import *    # BLOCKED
```

---

## Forbidden Function Patterns

The following function prefixes are **BLOCKED** in CL code:

```python
def run_*()        # BLOCKED - execution
def process_*()    # BLOCKED - execution
def execute_*()    # BLOCKED - execution
def handle_*()     # BLOCKED - execution
def fetch_*()      # BLOCKED - API call
def sync_*()       # BLOCKED - integration
def trigger_*()    # BLOCKED - workflow
def enrich_*()     # BLOCKED - enrichment
def scrape_*()     # BLOCKED - scraping
def crawl_*()      # BLOCKED - crawling
def match_*()      # BLOCKED - identity resolution
```

### Allowed Function Patterns

```python
def evaluate_*()   # ALLOWED - decision making
def record_*()     # ALLOWED - state recording
def authorize_*()  # ALLOWED - approval
def block_*()      # ALLOWED - rejection
def validate_*()   # ALLOWED - validation
def audit_*()      # ALLOWED - history
def get_*()        # ALLOWED - read-only
def check_*()      # ALLOWED - verification
```

---

## Forbidden Class Patterns

The following class suffixes are **BLOCKED** in CL code:

```python
class *Worker      # BLOCKED
class *Pipeline    # BLOCKED
class *Task        # BLOCKED
class *Job         # BLOCKED
class *Engine      # BLOCKED
class *Processor   # BLOCKED
class *Handler     # BLOCKED
class *Executor    # BLOCKED
class *Runner      # BLOCKED
class *Orchestrator # BLOCKED
class *Fetcher     # BLOCKED
class *Enricher    # BLOCKED
class *Scraper     # BLOCKED
```

### Allowed Class Patterns

```python
class *State       # ALLOWED
class *Validator   # ALLOWED
class *Guard       # ALLOWED
class *Recorder    # ALLOWED
class *Evaluator   # ALLOWED
class *Auditor     # ALLOWED
```

---

## CI Enforcement

This doctrine is enforced by:

| Mechanism | File | Blocks Merge |
|-----------|------|--------------|
| Constitutional Hub Guard | `.github/workflows/constitutional-hub-guard.yml` | Yes |
| Forbidden Import Check | Same workflow | Yes |
| Forbidden Function Check | Same workflow | Yes |
| Forbidden Class Check | Same workflow | Yes |
| AXLE Terminology Check | Same workflow | Yes |
| Identity Resolution Check | Same workflow | Yes |

---

## Validation Checklist

Before any PR to CL is merged, confirm ALL of the following:

- [ ] "CL performs no work"
- [ ] "All execution occurs in child hubs"
- [ ] "CL is a decision and record system only"
- [ ] No forbidden imports present
- [ ] No forbidden function patterns present
- [ ] No forbidden class patterns present
- [ ] No execution language in docstrings
- [ ] No AXLE terminology anywhere

**If ANY checkbox cannot be confirmed, the PR is REJECTED.**

---

## Doctrine Lock Statement

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   This document is LOCKED.                                                  │
│                                                                             │
│   No changes to the non-operational prohibition rules are permitted        │
│   without explicit doctrine council approval.                               │
│                                                                             │
│   CL is a constitutional hub.                                               │
│   It decides. It records. It NEVER executes.                                │
│                                                                             │
│   Locked By: Doctrine Enforcement Auditor                                   │
│   Locked On: 2025-12-26                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

**END OF DOCTRINE LOCK**

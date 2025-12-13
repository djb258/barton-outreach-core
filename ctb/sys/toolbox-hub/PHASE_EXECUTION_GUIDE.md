# Phase Execution Guide - Barton Toolbox Hub

**Purpose:** Complete guide for executing outreach pipeline phases using the Phase Executor
**Status:** ✅ Production Ready
**Date:** 2025-11-17
**Related:** Outreach Phase Registry, Phase 1b People Validation

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Phase Executor API](#phase-executor-api)
3. [Database Schema](#database-schema)
4. [Claude Code Integration](#claude-code-integration)
5. [Usage Examples](#usage-examples)
6. [Phase Tracking](#phase-tracking)
7. [Error Handling](#error-handling)
8. [Production Deployment](#production-deployment)

---

## Overview

### What is the Phase Executor?

The **Phase Executor** (`backend/phase_executor.py`) is a Claude-callable orchestration layer that:
- Executes outreach pipeline phases by ID
- Tracks phase completion per company
- Validates phase dependencies
- Logs all actions to `pipeline_events` and `audit_log`
- Handles failures and retries

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     PHASE EXECUTOR                          │
│                                                             │
│  1. run_outreach_phase(phase_id, context)                  │
│     ├─ Get phase entry from registry                       │
│     ├─ Validate dependencies                               │
│     ├─ Execute phase function                              │
│     ├─ Log to pipeline_events + audit_log                  │
│     └─ Update company_master.current_phase                 │
│                                                             │
│  2. run_phase_sequence([1, 1.1, 3], context)               │
│     ├─ Validate sequence order                             │
│     ├─ Execute phases in order                             │
│     ├─ Stop on first failure (if enabled)                  │
│     └─ Return list of results                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Doctrine Reference

**Doctrine ID:** `04.04.02.04.ple.validation_pipeline`

**Integration Points:**
- `shq.error_master.phase_id` - Error tracking
- `marketing.pipeline_events.phase_id` - Event logging
- `marketing.phase_completion_log` - Phase execution history
- `marketing.company_master.current_phase` - Current phase per company

---

## Phase Executor API

### run_outreach_phase()

Execute a single phase by ID.

```python
from backend.phase_executor import run_outreach_phase

result = run_outreach_phase(
    phase_id,           # Phase identifier (int or float, e.g., 1, 1.1, 2, 3)
    context={},         # Context dictionary with inputs for phase function
    validate_deps=True, # Validate phase dependencies before execution
    log_execution=True  # Log to pipeline_events and audit_log
)
```

**Returns:**
```python
{
    "phase_id": 1.1,
    "phase_name": "Phase 1b: People Validation Trigger",
    "status": "complete",          # or "failed"
    "duration_seconds": 45.2,
    "result": { /* phase function result */ },
    "error_message": None          # or error string if failed
}
```

---

### run_phase_sequence()

Execute multiple phases in order.

```python
from backend.phase_executor import run_phase_sequence

results = run_phase_sequence(
    phase_ids=[1, 1.1, 3],  # List of phase IDs in order
    context={},             # Shared context for all phases
    stop_on_error=True      # Stop if any phase fails
)
```

**Returns:**
```python
[
    {"phase_id": 1, "status": "complete", ...},
    {"phase_id": 1.1, "status": "complete", ...},
    {"phase_id": 3, "status": "failed", "error_message": "..."}
]
```

---

### Helper Functions

#### execute_phase_by_name()

Execute phase by name instead of ID.

```python
from backend.phase_executor import execute_phase_by_name

result = execute_phase_by_name(
    "Phase 1b: People Validation Trigger",
    context={"state": "WV"}
)
```

#### retry_failed_phase()

Retry a failed phase.

```python
from backend.phase_executor import retry_failed_phase

result = retry_failed_phase(1.1, context={"state": "WV"})
```

---

## Database Schema

### company_master.current_phase

Tracks which phase each company is currently in.

**Column Type:** `DECIMAL(3,1)`
**Default:** `0` (intake phase)
**Values:** `0, 1, 1.1, 2, 3, 4, 5, 6`

```sql
-- Get companies in Phase 1.1 (People Validation)
SELECT company_unique_id, company_name, current_phase
FROM marketing.company_master
WHERE current_phase = 1.1;

-- Get companies ready for Phase 3 (Outreach Readiness)
SELECT company_unique_id, company_name, current_phase
FROM marketing.company_master
WHERE current_phase >= 2 AND current_phase < 3;
```

---

### phase_completion_log

Tracks complete phase execution history for each company.

**Table:** `marketing.phase_completion_log`

**Columns:**
| Column | Type | Description |
|--------|------|-------------|
| `log_id` | SERIAL | Primary key |
| `company_unique_id` | TEXT | FK to company_master |
| `phase_id` | DECIMAL(3,1) | Phase identifier (0, 1, 1.1, 2, etc.) |
| `phase_name` | TEXT | Human-readable phase name |
| `status` | TEXT | complete, failed, skipped, running |
| `started_at` | TIMESTAMPTZ | When phase started |
| `completed_at` | TIMESTAMPTZ | When phase completed (NULL if running) |
| `duration_seconds` | DECIMAL(10,2) | Execution duration |
| `error_message` | TEXT | Error if status=failed |
| `result_summary` | JSONB | Summarized result data |

**Indexes:**
- `idx_phase_log_company` - On company_unique_id
- `idx_phase_log_phase_id` - On phase_id
- `idx_phase_log_status` - On status
- `idx_phase_log_company_phase` - Composite (company + phase)
- `idx_phase_log_completed_at` - On completed_at

```sql
-- Get phase history for a company
SELECT
    phase_id,
    phase_name,
    status,
    duration_seconds,
    completed_at
FROM marketing.phase_completion_log
WHERE company_unique_id = '04.04.02.04.30000.001'
ORDER BY completed_at DESC;

-- Get failed phases in last 24 hours
SELECT
    company_unique_id,
    phase_id,
    phase_name,
    error_message,
    completed_at
FROM marketing.phase_completion_log
WHERE status = 'failed'
  AND completed_at >= NOW() - INTERVAL '24 hours'
ORDER BY completed_at DESC;
```

---

### Helper Views

#### v_companies_by_phase

Summary of companies grouped by current phase.

```sql
SELECT * FROM marketing.v_companies_by_phase;

-- Output:
-- current_phase | company_count | validated_count | ready_count | latest_completion
-- --------------|---------------|-----------------|-------------|-------------------
-- 0             | 100           | 0               | 0           | NULL
-- 1             | 50            | 45              | 0           | 2025-11-17 10:00:00
-- 1.1           | 30            | 30              | 0           | 2025-11-17 11:00:00
-- 3             | 20            | 20              | 15          | 2025-11-17 12:00:00
```

#### v_recent_phase_completions

Recent phase completions in last 24 hours.

```sql
SELECT * FROM marketing.v_recent_phase_completions LIMIT 10;

-- Output: log_id, company_unique_id, company_name, phase_id, phase_name,
--         status, duration_seconds, completed_at, error_message
```

#### v_failed_phases

Failed phases in last 7 days (need retry).

```sql
SELECT * FROM marketing.v_failed_phases;

-- Output: log_id, company_unique_id, company_name, phase_id, phase_name,
--         error_message, failed_at, company_current_phase
```

---

## Claude Code Integration

### Standard Execution Pattern

When user says: **"Run Phase 1b for WV people"**

```python
from backend.phase_executor import run_outreach_phase

# Execute phase
result = run_outreach_phase(1.1, context={"state": "WV", "dry_run": False})

# Report results
if result["status"] == "complete":
    print(f"✅ Phase {result['phase_id']} completed successfully")
    print(f"   Duration: {result['duration_seconds']:.2f}s")

    # Extract statistics from result
    if "statistics" in result["result"]:
        stats = result["result"]["statistics"]
        print(f"   Valid: {stats['valid']}")
        print(f"   Invalid: {stats['invalid']}")
else:
    print(f"❌ Phase {result['phase_id']} failed: {result['error_message']}")
```

---

### Retry Pattern

When user says: **"Retry failed Phase 1.1"**

```python
from backend.phase_executor import retry_failed_phase

# Retry phase
result = retry_failed_phase(1.1, context={"state": "WV"})

if result["status"] == "complete":
    print(f"✅ Retry succeeded")
else:
    print(f"❌ Retry failed: {result['error_message']}")
```

---

### Sequence Execution Pattern

When user says: **"Run the full validation pipeline for WV"**

```python
from backend.phase_executor import run_phase_sequence

# Execute Phase 1, 1.1, and 3 in sequence
results = run_phase_sequence(
    phase_ids=[1, 1.1, 3],
    context={"state": "WV"},
    stop_on_error=True
)

# Report results
for result in results:
    if result["status"] == "complete":
        print(f"✅ Phase {result['phase_id']}: {result['phase_name']}")
    else:
        print(f"❌ Phase {result['phase_id']}: {result['error_message']}")
```

---

### Phase Status Query Pattern

When user says: **"Show me companies in Phase 1.1"**

```python
import psycopg2
from backend.validator.db_utils import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

query = """
SELECT
    company_unique_id,
    company_name,
    current_phase,
    last_phase_completed_at
FROM marketing.company_master
WHERE current_phase = 1.1
ORDER BY last_phase_completed_at DESC
LIMIT 20;
"""

cursor.execute(query)
companies = cursor.fetchall()

for company in companies:
    print(f"  {company[1]} ({company[0]}) - Phase {company[2]}")

cursor.close()
conn.close()
```

---

## Usage Examples

### Example 1: Execute Phase 1 (Company Validation)

```python
from backend.phase_executor import run_outreach_phase

# NOTE: Phase 1 uses low-level validate_company() function (single record)
# For batch validation, use retro_validate_neon.py

company = {
    "company_name": "Acme Corp",
    "website": "https://acme.com",
    "employee_count": 500,
    "linkedin_url": "https://linkedin.com/company/acme",
    "industry": "Technology"
}

result = run_outreach_phase(1, context={"company": company})

if result["status"] == "complete":
    validation_result = result["result"]
    if validation_result["valid"]:
        print(f"✅ Company is valid")
    else:
        print(f"❌ Company is invalid: {validation_result['reason']}")
```

---

### Example 2: Execute Phase 1.1 (People Validation Trigger)

```python
from backend.phase_executor import run_outreach_phase

# Execute Phase 1.1 for WV people
result = run_outreach_phase(1.1, context={
    "state": "WV",
    "dry_run": False,
    "limit": 100
})

if result["status"] == "complete":
    stats = result["result"]["statistics"]
    print(f"✅ Phase 1.1 completed")
    print(f"   Total: {stats['total']}")
    print(f"   Valid: {stats['valid']}")
    print(f"   Invalid: {stats['invalid']}")
    print(f"   Routed to Sheets: {stats['routed_to_sheets']}")
```

---

### Example 3: Execute Phase 3 (Outreach Readiness)

```python
from backend.phase_executor import run_outreach_phase

# Execute Phase 3 for validated WV companies
result = run_outreach_phase(3, context={
    "state": "WV",
    "only_validated": True
})

if result["status"] == "complete":
    stats = result["result"]["statistics"]
    print(f"✅ Phase 3 completed")
    print(f"   Ready: {stats['ready']}")
    print(f"   Not Ready: {stats['not_ready']}")
```

---

### Example 4: Execute Full Pipeline Sequence

```python
from backend.phase_executor import run_phase_sequence

# Execute phases 1, 1.1, and 3 in sequence for WV
results = run_phase_sequence(
    phase_ids=[1, 1.1, 3],
    context={"state": "WV"},
    stop_on_error=True
)

# Print summary
for result in results:
    status_icon = "✅" if result["status"] == "complete" else "❌"
    print(f"{status_icon} Phase {result['phase_id']}: {result['phase_name']}")
    print(f"   Duration: {result['duration_seconds']:.2f}s")

    if result["error_message"]:
        print(f"   Error: {result['error_message']}")
```

---

### Example 5: CLI Usage

```bash
# Execute Phase 1.1 for WV people
python backend/phase_executor.py 1.1 --state WV

# Execute Phase 1.1 with dry-run
python backend/phase_executor.py 1.1 --state WV --dry-run --limit 10

# Execute Phase 3 for validated companies
python backend/phase_executor.py 3 --state WV --verbose
```

---

## Phase Tracking

### Check Company's Current Phase

```sql
SELECT
    company_unique_id,
    company_name,
    current_phase,
    last_phase_completed_at
FROM marketing.company_master
WHERE company_unique_id = '04.04.02.04.30000.001';
```

---

### Get Phase Completion History

```sql
SELECT
    phase_id,
    phase_name,
    status,
    duration_seconds,
    completed_at,
    error_message
FROM marketing.phase_completion_log
WHERE company_unique_id = '04.04.02.04.30000.001'
ORDER BY completed_at DESC;
```

---

### Find Companies Stuck in a Phase

```sql
-- Companies in Phase 1.1 for more than 24 hours
SELECT
    cm.company_unique_id,
    cm.company_name,
    cm.current_phase,
    cm.last_phase_completed_at,
    NOW() - cm.last_phase_completed_at as time_in_phase
FROM marketing.company_master cm
WHERE cm.current_phase = 1.1
  AND cm.last_phase_completed_at < NOW() - INTERVAL '24 hours'
ORDER BY cm.last_phase_completed_at ASC;
```

---

### Get Failed Phases for Retry

```sql
SELECT
    company_unique_id,
    phase_id,
    phase_name,
    error_message,
    completed_at as failed_at
FROM marketing.phase_completion_log
WHERE status = 'failed'
  AND completed_at >= NOW() - INTERVAL '7 days'
ORDER BY completed_at DESC;
```

---

## Error Handling

### Phase Execution Errors

If a phase fails, the Phase Executor:
1. **Logs error to `marketing.phase_completion_log`** with `status='failed'`
2. **Logs error to `shq.audit_log`** with component `phase_executor`
3. **Does NOT update `company_master.current_phase`** (stays at previous phase)
4. **Returns error result** with `status="failed"` and `error_message`

```python
result = run_outreach_phase(1.1, context={"state": "WV"})

if result["status"] == "failed":
    print(f"❌ Phase failed: {result['error_message']}")

    # Phase can be retried
    retry_result = retry_failed_phase(1.1, context={"state": "WV"})
```

---

### Dependency Validation Errors

If phase dependencies are not met:

```python
# Phase 3 requires Phase 1 and Phase 2 to be complete
result = run_outreach_phase(3, context={"state": "WV"})

# If dependencies not met, execution fails with clear error
# Error: "Phase 3 requires Phase 1 and Phase 2 to be complete first"
```

---

### Database Connection Errors

If database connection fails:
- Phase execution fails with error message
- Logged to console (not database, since connection failed)
- Can be retried when database is available

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Run database migration `002_add_phase_tracking.sql`
- [ ] Verify `current_phase` column exists in `company_master`
- [ ] Verify `phase_completion_log` table exists
- [ ] Verify trigger `trg_update_company_current_phase` exists
- [ ] Test phase execution with dry-run mode
- [ ] Verify logging to `pipeline_events` and `audit_log`
- [ ] Set up monitoring for failed phases
- [ ] Document retry procedures

---

### Deployment Steps

#### Step 1: Run Database Migration

```bash
# Connect to Neon database
psql $NEON_CONNECTION_STRING

# Run migration
\i backend/migrations/002_add_phase_tracking.sql

# Verify migration
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'marketing'
  AND table_name = 'company_master'
  AND column_name = 'current_phase';

-- Should return: current_phase | numeric(3,1)
```

---

#### Step 2: Test Phase Execution

```bash
# Test with dry-run
python backend/phase_executor.py 1.1 --state WV --dry-run --limit 5

# Test with small batch
python backend/phase_executor.py 1.1 --state WV --limit 10

# Verify logging
psql -c "SELECT * FROM marketing.phase_completion_log ORDER BY created_at DESC LIMIT 5;"
```

---

#### Step 3: Production Run

```python
from backend.phase_executor import run_outreach_phase

# Execute Phase 1.1 for all WV people
result = run_outreach_phase(1.1, context={"state": "WV"})

if result["status"] == "complete":
    print(f"✅ Phase 1.1 completed: {result['result']['statistics']}")
else:
    print(f"❌ Phase 1.1 failed: {result['error_message']}")
```

---

#### Step 4: Monitor Results

```sql
-- Check phase completion summary
SELECT * FROM marketing.v_companies_by_phase;

-- Check recent completions
SELECT * FROM marketing.v_recent_phase_completions LIMIT 20;

-- Check for failures
SELECT * FROM marketing.v_failed_phases;
```

---

### Post-Deployment Monitoring

**Daily Checks:**
```sql
-- Companies by phase
SELECT current_phase, COUNT(*) as count
FROM marketing.company_master
GROUP BY current_phase
ORDER BY current_phase;

-- Failed phases in last 24 hours
SELECT phase_id, COUNT(*) as failures
FROM marketing.phase_completion_log
WHERE status = 'failed'
  AND completed_at >= NOW() - INTERVAL '24 hours'
GROUP BY phase_id;

-- Average phase durations
SELECT
    phase_id,
    phase_name,
    AVG(duration_seconds) as avg_duration,
    MAX(duration_seconds) as max_duration
FROM marketing.phase_completion_log
WHERE status = 'complete'
  AND completed_at >= NOW() - INTERVAL '7 days'
GROUP BY phase_id, phase_name
ORDER BY phase_id;
```

---

## Related Documentation

- **Outreach Phase Registry:** `backend/outreach_phase_registry.py`
- **Phase 1b People Validation:** `PHASE1_PEOPLE_VALIDATION.md`
- **Phase 2 Outreach Readiness:** `PHASE2_OUTREACH_READINESS.md`
- **Validation Pipeline Quick Start:** `VALIDATION_PIPELINE_QUICKSTART.md`

---

**Last Updated:** 2025-11-17
**Status:** ✅ Production Ready
**Maintainer:** Barton Outreach Core Team
**Version:** 1.0.0

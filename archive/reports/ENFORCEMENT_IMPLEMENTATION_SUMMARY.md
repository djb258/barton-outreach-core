# Enforcement Implementation Summary

**Implementation Date**: 2026-02-02
**Version**: 1.0.0
**Authority**: ERROR_TTL_PARKING_POLICY.md, TOOL_CANON_ENFORCEMENT.md, DONE_STATE_DEFINITIONS.md

---

## Overview

This document summarizes the mechanical enforcement implementation for:
1. Error TTL + Parking Policy
2. Promotion Gate Checks
3. Tool Canon Guard
4. CI Enforcement Checks

---

## 1. Database Migrations

### 1.1 Error Governance Columns

**File**: `infra/migrations/2026-02-02-error-governance-columns.sql`

**Columns Added** to all hub-owned error tables:

| Column | Type | Purpose |
|--------|------|---------|
| `disposition` | ENUM | RETRY, PARKED, ARCHIVED, IGNORE, RESOLVED |
| `retry_count` | INTEGER | Current retry attempts |
| `max_retries` | INTEGER | Maximum allowed retries |
| `archived_at` | TIMESTAMPTZ | When error was archived |
| `parked_at` | TIMESTAMPTZ | When error was parked |
| `parked_by` | TEXT | System/user that parked |
| `park_reason` | TEXT | Why parked (MAX_RETRIES_EXCEEDED, etc.) |
| `escalation_level` | INTEGER | 0-3 escalation tier |
| `escalated_at` | TIMESTAMPTZ | Last escalation time |
| `ttl_tier` | ENUM | SHORT (7d), MEDIUM (30d), LONG (90d), INFINITE |
| `last_retry_at` | TIMESTAMPTZ | Last retry timestamp |
| `next_retry_at` | TIMESTAMPTZ | Scheduled next retry |
| `retry_exhausted` | BOOLEAN | True if retry_count >= max_retries |

**Tables Modified**:
- `outreach.dol_errors` (max_retries=5 for DOL override)
- `outreach.company_target_errors`
- `people.people_errors`
- `company.url_discovery_failures`
- `public.shq_error_log`

### 1.2 Archive Tables

**File**: `infra/migrations/2026-02-02-error-archive-tables.sql`

**Archive Tables Created**:

| Archive Table | Source Table | Retention |
|---------------|--------------|-----------|
| `outreach.dol_errors_archive` | `outreach.dol_errors` | 1 year |
| `outreach.company_target_errors_archive` | `outreach.company_target_errors` | 1 year |
| `people.people_errors_archive` | `people.people_errors` | 1 year |
| `company.url_discovery_failures_archive` | `company.url_discovery_failures` | 1 year |
| `public.shq_error_log_archive` | `public.shq_error_log` | 2 years |

**Archive Metadata Fields**:
- `archived_at` - When archived
- `archived_by` - Who/what archived
- `archive_reason` - TTL_EXPIRED, MANUAL, RESOLVED, SUPERSEDED
- `final_disposition` - Disposition at time of archive
- `retention_expires_at` - When archive record can be deleted

### 1.3 TTL + Archive Functions

**File**: `infra/migrations/2026-02-02-error-ttl-archive-functions.sql`

**Functions Created**:

| Function | Purpose | Schedule |
|----------|---------|----------|
| `shq.fn_get_ttl_interval(ttl_tier)` | Convert TTL tier to interval | Helper |
| `shq.fn_archive_expired_errors()` | Archive errors past TTL | Daily |
| `shq.fn_auto_park_exhausted_retries()` | Park errors with retry_count >= max_retries | After retry batch |
| `shq.fn_escalate_stale_parked_errors()` | Escalate parked errors by time | Daily |
| `shq.fn_cleanup_expired_archives()` | Delete archives past retention | Weekly |
| `shq.fn_run_error_governance_jobs()` | Master runner for all jobs | Daily |

**Views Created**:
- `shq.vw_error_governance_summary` - Error state across all tables
- `shq.vw_blocking_errors_by_outreach` - Outreach IDs with blocking errors

### 1.4 Promotion Gate Functions

**File**: `infra/migrations/2026-02-02-promotion-gate-functions.sql`

**DONE State Checkers**:

| Function | Hub | DONE Criteria |
|----------|-----|---------------|
| `shq.fn_check_company_target_done(outreach_id)` | Company Target | execution_status='ready', email_method NOT NULL, confidence_score NOT NULL, imo_completed_at NOT NULL |
| `shq.fn_check_dol_done(outreach_id)` | DOL | ein NOT NULL, filing_present=TRUE |
| `shq.fn_check_people_done(outreach_id, min_slots)` | People | >= min_slots filled |
| `shq.fn_check_blog_done(outreach_id)` | Blog | Record exists |
| `shq.fn_check_bit_done(outreach_id)` | BIT | score NOT NULL, signal_count > 0 |

**Blocking Error Checkers**:

| Function | Table |
|----------|-------|
| `shq.fn_has_blocking_dol_errors(outreach_id)` | outreach.dol_errors |
| `shq.fn_has_blocking_company_target_errors(outreach_id)` | outreach.company_target_errors |
| `shq.fn_has_blocking_people_errors(outreach_id)` | people.people_errors |

**Promotion Functions**:

| Function | Purpose |
|----------|---------|
| `shq.fn_get_promotion_blockers(outreach_id)` | Get all blockers for an entity |
| `shq.fn_can_promote_to_hub(outreach_id, target_hub)` | Check if can promote to hub |
| `shq.fn_is_tier1_marketing_ready(outreach_id)` | Tier 1 check (high confidence) |
| `shq.fn_is_tier2_enrichment_complete(outreach_id)` | Tier 2 check (all hubs done) |
| `shq.fn_is_tier3_campaign_ready(outreach_id)` | Tier 3 check (people verified) |

**Views Created**:
- `shq.vw_promotion_readiness` - DONE states and blockers per outreach_id
- `shq.vw_promotion_readiness_summary` - Summary counts by tier

---

## 2. Python Enforcement Module

### 2.1 Tool Canon Guard

**File**: `ops/enforcement/tool_canon_guard.py`

**Classes**:
- `ToolCanonGuard` - Pre-invocation validation
- `ToolViolation` - Violation data class
- `ValidationResult` - Validation result

**Enums**:
- `ToolTier` - TIER_0 (Free), TIER_1 (Cheap), TIER_2 (Surgical)
- `InteractionType` - READ, WRITE, ENRICH, VALIDATE
- `ViolationSeverity` - CRITICAL, HIGH, MEDIUM, LOW
- `ViolationDisposition` - PARK, RETRY, ARCHIVE, IGNORE

**Usage**:
```python
from ops.enforcement.tool_canon_guard import ToolCanonGuard, InteractionType

guard = ToolCanonGuard()
result = guard.validate(
    tool_id="TOOL-008",
    hub_id="HUB-COMPANY-TARGET",
    interaction_type=InteractionType.ENRICH,
    gate_state={"domain_verified": True, "mx_present": True}
)
if not result.is_valid:
    raise ToolCanonViolationError(result.violation)
```

**Decorator**:
```python
from ops.enforcement.tool_canon_guard import enforce_tool_canon, InteractionType

@enforce_tool_canon("TOOL-008", "HUB-COMPANY-TARGET", InteractionType.ENRICH)
def call_hunter_api(domain: str, gate_state: dict):
    ...
```

### 2.2 CI Enforcement Checks

**File**: `ops/enforcement/ci_enforcement_checks.py`

**Checks**:

| Check | Description |
|-------|-------------|
| `check_banned_libraries()` | Scan requirements.txt for banned libs |
| `check_banned_imports()` | Scan Python files for banned imports |
| `check_tool_registry_coverage()` | Find suspicious patterns (unregistered tools) |
| `check_done_state_contracts()` | Validate DONE_STATE_DEFINITIONS.md |

**Usage**:
```bash
# Run all CI checks
python -m ops.enforcement.ci_enforcement_checks

# Output: ci_enforcement_report.json
```

---

## 3. Migration Execution Order

Execute in this order:

```bash
# 1. Add governance columns to error tables
psql $DATABASE_URL < infra/migrations/2026-02-02-error-governance-columns.sql

# 2. Create archive tables
psql $DATABASE_URL < infra/migrations/2026-02-02-error-archive-tables.sql

# 3. Create TTL/archive functions
psql $DATABASE_URL < infra/migrations/2026-02-02-error-ttl-archive-functions.sql

# 4. Create promotion gate functions
psql $DATABASE_URL < infra/migrations/2026-02-02-promotion-gate-functions.sql
```

---

## 4. Scheduled Jobs

### 4.1 Daily Error Governance Job

```sql
-- Run daily via scheduler
SELECT * FROM shq.fn_run_error_governance_jobs();
```

This runs:
1. Archive expired errors
2. Auto-park exhausted retries
3. Escalate stale parked errors

### 4.2 Weekly Archive Cleanup

```sql
-- Run weekly
SELECT * FROM shq.fn_cleanup_expired_archives();
```

---

## 5. Views for Monitoring

### Error Governance

```sql
-- Overall error state
SELECT * FROM shq.vw_error_governance_summary;

-- Outreach IDs blocked by errors
SELECT * FROM shq.vw_blocking_errors_by_outreach;
```

### Promotion Readiness

```sql
-- Individual readiness
SELECT * FROM shq.vw_promotion_readiness WHERE outreach_id = 'uuid-here';

-- Summary by tier
SELECT * FROM shq.vw_promotion_readiness_summary;
```

---

## 6. Backfill Commands

After running migrations, backfill existing data:

```sql
-- Set disposition based on resolved status
UPDATE outreach.dol_errors SET disposition = 'RETRY' WHERE resolved_at IS NULL AND disposition IS NULL;
UPDATE outreach.dol_errors SET disposition = 'RESOLVED' WHERE resolved_at IS NOT NULL AND disposition IS NULL;

-- Set TTL tier based on error type (customize per hub)
UPDATE outreach.dol_errors SET ttl_tier = 'SHORT' WHERE failure_code IN ('RATE_LIMIT', 'TIMEOUT');
UPDATE outreach.dol_errors SET ttl_tier = 'MEDIUM' WHERE failure_code IN ('VALIDATION_ERROR', 'MISSING_DATA');

-- Mark exhausted retries
UPDATE outreach.dol_errors
SET retry_exhausted = TRUE,
    disposition = 'PARKED',
    parked_at = NOW(),
    parked_by = 'backfill',
    park_reason = 'MAX_RETRIES_EXCEEDED'
WHERE retry_count >= max_retries AND disposition = 'RETRY';
```

---

## 7. Violation Handling

### Violation Codes

| Code | Severity | Description |
|------|----------|-------------|
| V-TOOL-001 | CRITICAL | Tool not in registry |
| V-TOOL-002 | CRITICAL | Banned vendor/library |
| V-TOOL-003 | HIGH | Missing API key |
| V-TYPE-001 | HIGH | Wrong interaction type |
| V-SCOPE-001 | CRITICAL | Tool out of hub scope |
| V-GATE-001 | CRITICAL | Gate conditions not met |
| V-GATE-002 | CRITICAL | Human approval required |

### Disposition Actions

| Disposition | Action |
|-------------|--------|
| PARK | Hold for manual review, blocks promotion |
| RETRY | Queue for reprocessing, blocks promotion |
| ARCHIVE | Move to archive, no block |
| IGNORE | Log only, no action |

---

## 8. CI Integration

Add to CI pipeline:

```yaml
# .github/workflows/enforcement.yml
enforcement-check:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    - name: Run enforcement checks
      run: python -m ops.enforcement.ci_enforcement_checks
    - name: Upload report
      uses: actions/upload-artifact@v4
      with:
        name: enforcement-report
        path: ci_enforcement_report.json
```

---

## Document Control

| Field | Value |
|-------|-------|
| Implementation Date | 2026-02-02 |
| Version | 1.0.0 |
| Author | claude-code |
| Status | READY FOR DEPLOYMENT |
| Source Documents | ERROR_TTL_PARKING_POLICY.md, TOOL_CANON_ENFORCEMENT.md, DONE_STATE_DEFINITIONS.md |

---

## Files Created

| File | Type | Purpose |
|------|------|---------|
| `infra/migrations/2026-02-02-error-governance-columns.sql` | Migration | Add governance columns |
| `infra/migrations/2026-02-02-error-archive-tables.sql` | Migration | Create archive tables |
| `infra/migrations/2026-02-02-error-ttl-archive-functions.sql` | Migration | TTL/archive functions |
| `infra/migrations/2026-02-02-promotion-gate-functions.sql` | Migration | DONE state/promotion gates |
| `ops/enforcement/tool_canon_guard.py` | Python | Tool canon validation |
| `ops/enforcement/ci_enforcement_checks.py` | Python | CI checks |
| `ENFORCEMENT_IMPLEMENTATION_SUMMARY.md` | Doc | This document |

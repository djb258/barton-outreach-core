# Error TTL + Parking Policy

**Policy Version**: 1.0.0
**Effective Date**: 2026-02-02
**Authority**: CC-03 (Cross-Cutting Observability)
**Source**: `ERROR_TABLE_CLASSIFICATION.md`

---

## 1. TTL Tier Definitions

| Tier | Duration | Use Case | Auto-Archive |
|------|----------|----------|--------------|
| **SHORT** | 7 days | Transient failures (rate limits, timeouts, API errors) | YES |
| **MEDIUM** | 30 days | Operational failures (validation, missing data) | YES |
| **LONG** | 90 days | Structural failures (bad data, schema mismatch) | YES |
| **INFINITE** | Never expires | Audit/compliance records, immutable logs | NO |

### TTL Behavior

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TTL LIFECYCLE                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ERROR CREATED                                                             │
│        │                                                                    │
│        ▼                                                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  ACTIVE                                                             │   │
│   │  • Error is visible in hub error table                              │   │
│   │  • Error counts toward metrics                                      │   │
│   │  • Error may block promotion (if blocking=true)                     │   │
│   └─────────────────────────────────┬───────────────────────────────────┘   │
│                                     │                                       │
│                                     │ TTL expires                           │
│                                     ▼                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  ARCHIVED                                                           │   │
│   │  • Moved to *_archive table (if exists)                            │   │
│   │  • No longer counts toward metrics                                  │   │
│   │  • No longer blocks promotion                                       │   │
│   │  • Retained for audit/analysis                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   INFINITE TTL: Errors remain in ACTIVE state permanently.                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Disposition Definitions

| Disposition | Definition | State Transition | Blocks Promotion |
|-------------|------------|------------------|------------------|
| **RETRY** | Error is retryable. Queue for reprocessing. | ACTIVE → RETRY_PENDING → (SUCCESS or FAIL) | YES (until resolved) |
| **PARK** | Error requires manual review. Hold for investigation. | ACTIVE → PARKED | YES (until unparked) |
| **ARCHIVE** | Error is terminal. Move to archive after TTL. | ACTIVE → ARCHIVED | NO |
| **IGNORE** | Error is informational only. No action required. | ACTIVE → (stays ACTIVE until TTL) | NO |

### Disposition State Machine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DISPOSITION STATE MACHINE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                            ┌──────────────┐                                 │
│                            │   CREATED    │                                 │
│                            └──────┬───────┘                                 │
│                                   │                                         │
│                                   ▼                                         │
│                            ┌──────────────┐                                 │
│                            │    ACTIVE    │                                 │
│                            └──────┬───────┘                                 │
│                                   │                                         │
│         ┌─────────────────────────┼─────────────────────────┐               │
│         │                         │                         │               │
│         ▼                         ▼                         ▼               │
│  ┌──────────────┐          ┌──────────────┐          ┌──────────────┐       │
│  │    RETRY     │          │    PARK      │          │   IGNORE     │       │
│  │   PENDING    │          │   (PARKED)   │          │              │       │
│  └──────┬───────┘          └──────┬───────┘          └──────┬───────┘       │
│         │                         │                         │               │
│    ┌────┴────┐              ┌─────┴─────┐                   │               │
│    │         │              │           │                   │               │
│    ▼         ▼              ▼           ▼                   │               │
│ SUCCESS    FAIL         UNPARK      ESCALATE               │               │
│    │         │              │           │                   │               │
│    ▼         │              ▼           ▼                   │               │
│ RESOLVED     └──────►  ACTIVE    ESCALATED                 │               │
│    │                       │           │                   │               │
│    └───────────────────────┼───────────┴───────────────────┘               │
│                            │                                                │
│                            ▼                                                │
│                     ┌──────────────┐                                        │
│                     │   ARCHIVED   │ (after TTL expires)                    │
│                     └──────────────┘                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Error Table Policy Mapping

### Hub-Owned Error Tables (Layer 1)

| Error Table | TTL Tier | Default Disposition | Allowed Dispositions | Blocks Promotion |
|-------------|----------|---------------------|----------------------|------------------|
| `outreach.dol_errors` | MEDIUM (30d) | RETRY | RETRY, PARK, ARCHIVE | **YES** |
| `outreach.company_target_errors` | MEDIUM (30d) | RETRY | RETRY, PARK, ARCHIVE | **YES** |
| `people.people_errors` | MEDIUM (30d) | RETRY | RETRY, PARK, ARCHIVE | **YES** |
| `company.url_discovery_failures` | LONG (90d) | ARCHIVE | RETRY, ARCHIVE | NO |

### Global Error Tables (Layer 2)

| Error Table | TTL Tier | Default Disposition | Allowed Dispositions | Blocks Promotion |
|-------------|----------|---------------------|----------------------|------------------|
| `public.shq_error_log` | LONG (90d) | IGNORE | IGNORE, ARCHIVE | NO |
| `public.shq_master_error_log` | INFINITE | IGNORE | IGNORE | NO |
| `public.shq_orphan_errors` | MEDIUM (30d) | PARK | PARK, ARCHIVE | NO |

### DEAD Tables (No Policy - Not in Neon)

| Error Table | Status | Action |
|-------------|--------|--------|
| `outreach.bit_errors` | DEAD | Create table or remove from ERD |
| `outreach.blog_errors` | DEAD | Create table or remove from ERD |
| `outreach.people_errors` | DEAD | Create table or remove from ERD |
| `outreach.outreach_errors` | DEAD | Create table or remove from ERD |
| `cl.cl_errors_archive` | DEAD | Archive table, no active policy |
| `company.pipeline_errors` | DEAD | Create table or remove from ERD |

---

## 4. Parking Semantics

### 4.1 What "Parked" Means

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PARKING DEFINITION                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   A PARKED error is an error that:                                          │
│                                                                             │
│   1. CANNOT be automatically retried                                        │
│      • Retry attempts exhausted, OR                                         │
│      • Error type is not retryable, OR                                      │
│      • Manual investigation required                                        │
│                                                                             │
│   2. REQUIRES human review before resolution                                │
│      • Data quality issue                                                   │
│      • Business rule ambiguity                                              │
│      • External dependency failure                                          │
│                                                                             │
│   3. BLOCKS downstream processing (if blocking=true)                        │
│      • Entity cannot progress until parked error resolved                   │
│      • Other entities in same batch may proceed                             │
│                                                                             │
│   4. HAS a defined owner responsible for resolution                         │
│      • Hub team owns hub-level parked errors                               │
│      • Platform team owns global parked errors                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Parked Error State

| Field | Definition |
|-------|------------|
| `disposition` | `PARKED` |
| `parked_at` | Timestamp when error was parked |
| `parked_by` | System or user that parked the error |
| `park_reason` | Why the error was parked (code or text) |
| `assigned_to` | Owner responsible for resolution (nullable) |
| `escalation_level` | 0 = not escalated, 1+ = escalation tier |
| `last_reviewed_at` | Last time a human reviewed this error |

### 4.3 Parking Triggers

An error MUST be parked when:

| Trigger | Description | Example |
|---------|-------------|---------|
| **MAX_RETRIES_EXCEEDED** | Retry count exceeds threshold | 3 retries failed for API call |
| **NON_RETRYABLE_ERROR** | Error code marked as non-retryable | Data validation failure |
| **ESCALATION_REQUIRED** | Business rule requires human decision | Duplicate company resolution |
| **EXTERNAL_DEPENDENCY** | Requires external party action | Vendor API permanently changed |
| **DATA_QUALITY** | Source data is malformed or missing | Missing required field in source |

### 4.4 Parking Exit Conditions

A parked error exits PARKED state when:

| Exit | Target State | Trigger |
|------|--------------|---------|
| **UNPARK** | ACTIVE → RETRY_PENDING | Human marks for retry after fix |
| **RESOLVE** | RESOLVED | Human manually resolves the issue |
| **ESCALATE** | ESCALATED | Human escalates to higher tier |
| **ARCHIVE** | ARCHIVED | TTL expires or human archives |

---

## 5. Retry Policy

### 5.1 Retry Configuration by Error Type

| Error Category | Max Retries | Backoff Strategy | Retry Window |
|----------------|-------------|------------------|--------------|
| **TRANSIENT** (rate limit, timeout) | 5 | Exponential (2^n seconds) | 24 hours |
| **OPERATIONAL** (validation, missing data) | 3 | Linear (5 minutes) | 7 days |
| **STRUCTURAL** (bad data, schema) | 1 | None | Manual only |

### 5.2 Retry State Fields

| Field | Definition |
|-------|------------|
| `retry_count` | Number of retry attempts |
| `max_retries` | Maximum allowed retries for this error type |
| `last_retry_at` | Timestamp of last retry attempt |
| `next_retry_at` | Scheduled time for next retry (nullable) |
| `retry_exhausted` | Boolean: true if retry_count >= max_retries |

### 5.3 Retry → Park Escalation

```
IF retry_count >= max_retries:
    disposition = PARKED
    park_reason = MAX_RETRIES_EXCEEDED
    parked_at = NOW()
    parked_by = 'system'
```

---

## 6. Promotion Blocking Rules

### 6.1 What "Blocks Promotion" Means

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PROMOTION BLOCKING SEMANTICS                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   An error BLOCKS PROMOTION when:                                           │
│                                                                             │
│   1. The error is in a BLOCKING error table (see mapping)                   │
│   2. The error's disposition is RETRY or PARK                               │
│   3. The error is not ARCHIVED or RESOLVED                                  │
│                                                                             │
│   BLOCKING BEHAVIOR:                                                         │
│   • Entity with blocking error CANNOT progress to next hub/phase            │
│   • Entity remains in current state until error resolved                    │
│   • Other entities are NOT affected (isolation)                             │
│                                                                             │
│   NON-BLOCKING BEHAVIOR:                                                     │
│   • Error is logged for visibility                                          │
│   • Entity proceeds normally                                                │
│   • Error does not affect downstream processing                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Blocking Error Tables

| Table | Blocks | Reason |
|-------|--------|--------|
| `outreach.dol_errors` | YES | EIN match required for DOL enrichment |
| `outreach.company_target_errors` | YES | Domain/pattern required for targeting |
| `people.people_errors` | YES | People processing required for slot fill |
| `company.url_discovery_failures` | NO | URL discovery is best-effort |
| `public.shq_error_log` | NO | Global visibility only |
| `public.shq_master_error_log` | NO | Audit log only |

### 6.3 Promotion Check Query Pattern

```sql
-- Check if entity has blocking errors
SELECT COUNT(*) > 0 AS is_blocked
FROM {error_table}
WHERE outreach_id = $1
  AND disposition IN ('RETRY', 'PARKED')
  AND archived_at IS NULL;
```

---

## 7. Archive Policy

### 7.1 Archive Trigger

Errors are archived when:

| Trigger | Condition |
|---------|-----------|
| **TTL_EXPIRED** | `NOW() - created_at > TTL_DURATION` |
| **MANUAL_ARCHIVE** | Human explicitly archives |
| **RESOLVED** | Error was successfully resolved |
| **SUPERSEDED** | Newer error replaces this one |

### 7.2 Archive Destination

| Source Table | Archive Table | Retention |
|--------------|---------------|-----------|
| `outreach.dol_errors` | `outreach.dol_errors_archive` | 1 year |
| `outreach.company_target_errors` | `outreach.company_target_errors_archive` | 1 year |
| `people.people_errors` | `people.people_errors_archive` | 1 year |
| `company.url_discovery_failures` | `company.url_discovery_failures_archive` | 1 year |
| `public.shq_error_log` | `public.shq_error_log_archive` | 2 years |

### 7.3 Archive Record Structure

Archived records retain all original fields plus:

| Field | Definition |
|-------|------------|
| `archived_at` | Timestamp when archived |
| `archived_by` | System or user that archived |
| `archive_reason` | TTL_EXPIRED, MANUAL, RESOLVED, SUPERSEDED |
| `final_disposition` | Disposition at time of archive |

---

## 8. Error Severity → Disposition Mapping

| Severity | Default Disposition | TTL Override | Blocks Promotion |
|----------|---------------------|--------------|------------------|
| **CRITICAL** | PARK | None (immediate park) | YES |
| **HIGH** | RETRY | SHORT (7d) | YES |
| **MEDIUM** | RETRY | MEDIUM (30d) | Depends on table |
| **LOW** | IGNORE | LONG (90d) | NO |

---

## 9. Hub-Specific Policy Overrides

### 9.1 DOL Filings Hub

| Policy | Override | Reason |
|--------|----------|--------|
| Max Retries | 5 (vs default 3) | EIN matching benefits from retries with updated data |
| Park Threshold | 50 errors/day | High volume expected during batch imports |

### 9.2 Company Target Hub

| Policy | Override | Reason |
|--------|----------|--------|
| TTL | MEDIUM (30d) | Pattern discovery may succeed on retry |
| Auto-Park | After 3 failed domain lookups | Prevent infinite retry loops |

### 9.3 People Intelligence Hub

| Policy | Override | Reason |
|--------|----------|--------|
| TTL | MEDIUM (30d) | Standard policy |
| Park on Missing Name | YES | Cannot generate email without name |

---

## 10. Escalation Policy

### 10.1 Escalation Tiers

| Tier | Owner | Trigger | SLA |
|------|-------|---------|-----|
| **0** | System | Initial error | Auto-retry within backoff window |
| **1** | Hub Team | MAX_RETRIES_EXCEEDED | Review within 24 hours |
| **2** | Hub Lead | Parked > 48 hours | Review within 8 hours |
| **3** | Platform Team | Parked > 7 days | Review within 4 hours |

### 10.2 Escalation State

| Field | Definition |
|-------|------------|
| `escalation_level` | Current tier (0-3) |
| `escalated_at` | Timestamp of last escalation |
| `escalated_to` | Owner at current tier |
| `escalation_reason` | Why escalated |

---

## 11. Metrics & Alerting Thresholds

### 11.1 Error Metrics

| Metric | Definition | Alert Threshold |
|--------|------------|-----------------|
| `error_rate` | Errors / Total processed | > 5% |
| `park_rate` | Parked / Total errors | > 20% |
| `retry_exhaustion_rate` | Exhausted / Retried | > 30% |
| `average_ttl_utilization` | Time in ACTIVE / TTL | > 80% |
| `escalation_rate` | Escalated / Parked | > 10% |

### 11.2 Alert Rules

| Condition | Severity | Action |
|-----------|----------|--------|
| `error_rate > 5%` | WARNING | Notify hub team |
| `error_rate > 10%` | HIGH | Page on-call |
| `park_rate > 20%` | WARNING | Review park queue |
| `parked_errors > 1000` | HIGH | Escalate to platform |
| `blocking_errors > 100` | CRITICAL | Page platform on-call |

---

## 12. Policy Enforcement (Future)

This policy document defines semantics only. Enforcement requires:

| Enforcement Layer | Status | Location |
|-------------------|--------|----------|
| Database columns (disposition, TTL fields) | NOT IMPLEMENTED | Schema migration |
| Archive cron job | NOT IMPLEMENTED | Scheduled task |
| Promotion gate check | NOT IMPLEMENTED | Hub pipelines |
| Escalation automation | NOT IMPLEMENTED | Alerting system |
| Metrics collection | NOT IMPLEMENTED | Observability layer |

---

## Document Control

| Field | Value |
|-------|-------|
| Policy Version | 1.0.0 |
| Created | 2026-02-02 |
| Author | claude-code |
| Authority | CC-03 (Cross-Cutting Observability) |
| Dependencies | `ERROR_TABLE_CLASSIFICATION.md` |
| Enforcement Status | POLICY ONLY - NOT ENFORCED |

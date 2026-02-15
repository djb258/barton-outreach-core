# Technical Architecture Specification: Completeness Contract

**Repository**: barton-outreach-core
**Version**: 1.0.0
**Generated**: 2026-01-28
**Purpose**: Generic, system-level completeness framework for sub-hub evaluation

---

## Overview

This document defines the **completeness contract** that applies to ALL sub-hubs in any repository adopting this system. It provides deterministic answers to:

1. Is this sub-hub COMPLETE for a given entity?
2. If not, WHY? (closed ENUM, not free text)

---

## Completeness Contract Schema

### Core Concepts

| Concept | Definition | Column |
|---------|------------|--------|
| `entity_id` | The unifying key across all sub-hubs | `company_unique_id` (TEXT) |
| `sub_hub_name` | Identifier for the sub-hub | `hub_id` (VARCHAR) |
| `completeness_status` | Is this entity complete for this hub? | `status` (ENUM) |
| `blocker_type` | WHY it's incomplete (closed ENUM) | **PROPOSED**: `blocker_type` (ENUM) |
| `blocker_evidence` | Structured evidence, not prose | **PROPOSED**: `blocker_evidence` (JSONB) |
| `last_checked_at` | When was this last evaluated? | `last_processed_at` (TIMESTAMPTZ) |

---

## Status Enum (EXISTING)

```sql
CREATE TYPE hub_status_enum AS ENUM (
    'IN_PROGRESS',  -- Currently being processed
    'PASS',         -- Sub-hub requirements met
    'FAIL',         -- Sub-hub requirements not met (recoverable)
    'BLOCKED'       -- Cannot proceed (external dependency)
);
```

| Status | Meaning | Action |
|--------|---------|--------|
| `IN_PROGRESS` | Processing not complete | Wait |
| `PASS` | All requirements met for this hub | Proceed to next hub |
| `FAIL` | Requirements not met, can retry | Retry after remediation |
| `BLOCKED` | External blocker, cannot proceed | Escalate or wait |

---

## Blocker Type Enum (PROPOSED)

**CRITICAL GAP**: The current system uses free-text `status_reason`. This must be replaced with a closed ENUM.

```sql
CREATE TYPE blocker_type_enum AS ENUM (
    'DATA_MISSING',            -- Required data not present
    'DATA_UNDISCOVERABLE',     -- Data cannot be found via available methods
    'DATA_CONFLICT',           -- Conflicting data, cannot resolve
    'SOURCE_UNAVAILABLE',      -- External source not responding
    'NOT_APPLICABLE',          -- Sub-hub does not apply to this entity
    'HUMAN_DECISION_REQUIRED', -- Ambiguous, needs human review
    'UPSTREAM_BLOCKED',        -- Previous hub in waterfall not complete
    'THRESHOLD_NOT_MET',       -- Metric below required threshold
    'EXPIRED'                  -- Data exists but is stale
);
```

### Blocker Type Definitions

| Blocker Type | Definition | Example | Recovery Action |
|--------------|------------|---------|-----------------|
| `DATA_MISSING` | Required field is NULL | `email_method IS NULL` | Retry enrichment |
| `DATA_UNDISCOVERABLE` | Searched, not found | No DOL filing for EIN | Mark as N/A or manual |
| `DATA_CONFLICT` | Multiple conflicting values | Two different EINs match | Human decision |
| `DATA_CONFLICT` | Multiple conflicting values | Two different EINs match | Human decision |
| `SOURCE_UNAVAILABLE` | API/service down | DOL API timeout | Retry later |
| `NOT_APPLICABLE` | Entity doesn't need this hub | Company too small for DOL | Skip, mark N/A |
| `HUMAN_DECISION_REQUIRED` | Cannot resolve automatically | Ambiguous company match | Escalate |
| `UPSTREAM_BLOCKED` | Previous hub not PASS | Company Target not done | Wait for upstream |
| `THRESHOLD_NOT_MET` | Metric below minimum | `slot_fill_rate < 0.5` | Improve data |
| `EXPIRED` | Data older than freshness window | People data > 90 days | Refresh |

---

## Blocker Evidence Structure (PROPOSED)

Instead of free-text `status_reason`, use structured JSONB:

```json
{
  "blocker_type": "DATA_MISSING",
  "missing_fields": ["email_method", "confidence_score"],
  "checked_sources": ["domain_discovery", "manual_lookup"],
  "last_attempt_at": "2026-01-28T10:00:00Z",
  "retry_count": 3,
  "upstream_hub_status": {
    "company-target": "PASS",
    "dol-filings": "IN_PROGRESS"
  }
}
```

### Evidence Schema by Blocker Type

| Blocker Type | Required Evidence Fields |
|--------------|--------------------------|
| `DATA_MISSING` | `missing_fields[]` |
| `DATA_UNDISCOVERABLE` | `checked_sources[]`, `last_attempt_at` |
| `DATA_CONFLICT` | `conflicting_values{}`, `sources[]` |
| `SOURCE_UNAVAILABLE` | `source_name`, `error_code`, `last_attempt_at` |
| `NOT_APPLICABLE` | `reason` |
| `HUMAN_DECISION_REQUIRED` | `decision_context`, `options[]` |
| `UPSTREAM_BLOCKED` | `blocking_hub`, `blocking_status` |
| `THRESHOLD_NOT_MET` | `metric_name`, `actual_value`, `required_value` |
| `EXPIRED` | `data_timestamp`, `freshness_window_days` |

---

## Completeness Evaluation Logic

### Per-Hub Completeness Rules

| Hub | Complete When | Incomplete When |
|-----|---------------|-----------------|
| **Company Target** | `email_method IS NOT NULL AND confidence_score >= 0.5` | Missing or low confidence |
| **DOL Filings** | `form_5500_matched = true` OR `NOT_APPLICABLE` | No EIN match |
| **People Intelligence** | `slot_fill_rate >= metric_critical_threshold` | Insufficient slots filled |
| **Talent Flow** | `movement_detection_rate >= threshold` OR age < 90 days | No movements, stale data |
| **Blog Content** | `signal_count >= 1` | No blog detected |
| **Outreach Execution** | `campaign_status IN ('active', 'completed')` | Not started |

### Waterfall Dependency Rules

```
Company Target (1) ─► PASS required before DOL Filings (2)
DOL Filings (2) ─► PASS required before People Intelligence (3)
People Intelligence (3) ─► PASS required before Talent Flow (4)
Talent Flow (4) ─► Optional: Blog Content (5)
                ─► Optional: Outreach Execution (6)
```

If upstream hub is not PASS:
- Set `status = 'BLOCKED'`
- Set `blocker_type = 'UPSTREAM_BLOCKED'`
- Set `blocker_evidence = { "blocking_hub": "<hub_id>", "blocking_status": "<status>" }`

---

## Response Protocol by Blocker Type

### For AI Agents

| Blocker Type | Agent Action |
|--------------|--------------|
| `DATA_MISSING` | Trigger enrichment pipeline |
| `DATA_UNDISCOVERABLE` | Log, mark NOT_APPLICABLE or escalate |
| `DATA_CONFLICT` | Escalate to human |
| `SOURCE_UNAVAILABLE` | Retry with exponential backoff |
| `NOT_APPLICABLE` | Mark as N/A, proceed |
| `HUMAN_DECISION_REQUIRED` | Create task, wait |
| `UPSTREAM_BLOCKED` | Do nothing, wait for upstream |
| `THRESHOLD_NOT_MET` | Analyze gaps, trigger remediation |
| `EXPIRED` | Trigger refresh pipeline |

### For Humans

| Blocker Type | Human Action |
|--------------|--------------|
| `DATA_MISSING` | Verify enrichment ran, check sources |
| `DATA_UNDISCOVERABLE` | Decide: manual entry or mark N/A |
| `DATA_CONFLICT` | Review conflicts, pick winner |
| `SOURCE_UNAVAILABLE` | Check service status, contact provider |
| `NOT_APPLICABLE` | Confirm entity doesn't need this hub |
| `HUMAN_DECISION_REQUIRED` | Make decision, record reason |
| `UPSTREAM_BLOCKED` | Check upstream hub issues |
| `THRESHOLD_NOT_MET` | Review metric, decide if acceptable |
| `EXPIRED` | Approve refresh or accept stale data |

---

## Migration Path

### Current State

```sql
-- Existing column (FREE TEXT - violation)
status_reason TEXT
```

### Target State

```sql
-- Add structured columns
ALTER TABLE outreach.company_hub_status
ADD COLUMN blocker_type blocker_type_enum,
ADD COLUMN blocker_evidence JSONB;

-- Migrate existing data
UPDATE outreach.company_hub_status
SET blocker_type = CASE
    WHEN status = 'PASS' THEN NULL
    WHEN status_reason LIKE '%missing%' THEN 'DATA_MISSING'
    WHEN status_reason LIKE '%not found%' THEN 'DATA_UNDISCOVERABLE'
    WHEN status_reason LIKE '%conflict%' THEN 'DATA_CONFLICT'
    WHEN status_reason LIKE '%upstream%' THEN 'UPSTREAM_BLOCKED'
    WHEN status_reason LIKE '%threshold%' THEN 'THRESHOLD_NOT_MET'
    ELSE 'DATA_MISSING'  -- Default for unmapped
END
WHERE status != 'PASS';

-- Eventually deprecate status_reason
-- ALTER TABLE outreach.company_hub_status DROP COLUMN status_reason;
```

---

## Completeness View (PROPOSED)

```sql
CREATE OR REPLACE VIEW outreach.vw_entity_completeness AS
SELECT
    chs.company_unique_id AS entity_id,
    hr.hub_id AS sub_hub_name,
    hr.hub_name AS sub_hub_display_name,
    hr.waterfall_order,
    hr.gates_completion AS is_required,
    chs.status AS completeness_status,
    chs.blocker_type,
    chs.blocker_evidence,
    chs.metric_value,
    hr.metric_critical_threshold AS required_threshold,
    chs.last_processed_at AS last_checked_at,
    CASE
        WHEN chs.status = 'PASS' THEN 'COMPLETE'
        WHEN chs.status = 'BLOCKED' AND chs.blocker_type = 'NOT_APPLICABLE' THEN 'NOT_APPLICABLE'
        ELSE 'INCOMPLETE'
    END AS simple_status
FROM outreach.company_hub_status chs
JOIN outreach.hub_registry hr ON hr.hub_id = chs.hub_id
ORDER BY chs.company_unique_id, hr.waterfall_order;
```

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-28 |
| Version | 1.0.0 |
| Author | Claude Code (AI Employee) |
| Status | READY (migration verified, evaluator implemented) |

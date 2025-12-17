# PRD: Master Error Log v1.1

**Status:** Active
**Version:** 1.1 (Hardened)
**Last Updated:** 2025-12-17
**Doctrine:** Bicycle Wheel v1.1 / Barton Doctrine
**Type:** Cross-Cutting Observability Process (NOT a Hub)

---

## Ownership Statement

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                     MASTER ERROR LOG — CROSS-CUTTING PROCESS                 ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   This is a CROSS-CUTTING OBSERVABILITY PROCESS, not a hub or sub-hub.      ║
║                                                                               ║
║   PURPOSE:                                                                    ║
║   ├── Global visibility into all pipeline failures                          ║
║   ├── Trend analysis across hubs                                            ║
║   ├── Alerting and monitoring                                               ║
║   └── Troubleshooting correlation                                           ║
║                                                                               ║
║   NOT RESPONSIBLE FOR:                                                        ║
║   ├── Remediation (owned by local sub-hub)                                  ║
║   ├── Retry logic (owned by local sub-hub)                                  ║
║   ├── Resolution workflow (owned by local sub-hub)                          ║
║   └── Decision making (owned by BIT Engine)                                 ║
║                                                                               ║
║   DOCTRINE: "Local First, Global Visibility"                                 ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 1. Core Doctrine (Non-Negotiable)

### 1.1 Local First

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LOCAL FIRST DOCTRINE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   RULE: Errors MUST be written to local sub-hub failure tables FIRST.      │
│                                                                             │
│   FLOW:                                                                     │
│   1. Error occurs in pipeline phase                                         │
│   2. Log to LOCAL sub-hub failure table (owner: sub-hub)                   │
│   3. Normalize error event                                                  │
│   4. Emit to Master Error Log (global visibility)                          │
│                                                                             │
│   LOCAL TABLES (owned by sub-hubs):                                         │
│   ├── people_processing_errors (People Sub-Hub)                            │
│   ├── dol_processing_errors (DOL Sub-Hub)                                  │
│   ├── blog_processing_errors (Blog Sub-Hub)                                │
│   ├── pipeline_errors (Company Hub Pipeline)                               │
│   └── outreach_errors (Outreach Node)                                      │
│                                                                             │
│   Sub-hubs retain FULL ownership of remediation and retry logic.           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Read-Only Global

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         READ-ONLY GLOBAL DOCTRINE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   RULE: The Master Error Log is APPEND-ONLY.                               │
│                                                                             │
│   PROHIBITED OPERATIONS:                                                    │
│   ├── UPDATE — No hub may modify existing records                          │
│   ├── DELETE — No hub may remove records                                   │
│   └── TRUNCATE — Never truncate the master log                            │
│                                                                             │
│   PERMITTED OPERATIONS:                                                     │
│   ├── INSERT — Append new error events only                                │
│   └── SELECT — Read for analysis, alerting, troubleshooting               │
│                                                                             │
│   ENFORCEMENT:                                                              │
│   • PostgreSQL RLS policy: DENY UPDATE/DELETE                              │
│   • Application layer: Only insert_error() function exposed                │
│   • Audit: Log any attempted modifications                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Correlation Required

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CORRELATION REQUIRED DOCTRINE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   RULE: Every master error record MUST include a valid correlation_id.     │
│                                                                             │
│   ENFORCEMENT:                                                              │
│   • NOT NULL constraint on correlation_id column                           │
│   • CHECK constraint: correlation_id ~ UUID v4 format                      │
│   • Application: Reject errors without correlation_id                      │
│                                                                             │
│   RATIONALE:                                                                │
│   • Enables end-to-end tracing across pipeline phases                      │
│   • Links master log to local sub-hub logs                                 │
│   • Supports troubleshooting: "Show me all errors for batch X"            │
│                                                                             │
│   ERRORS WITHOUT CORRELATION_ID:                                            │
│   • REJECTED at insert time                                                 │
│   • Logged to separate orphan_errors table for investigation              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Master Error Log Table Schema

### 2.1 Table Definition

**Table Name:** `shq_master_error_log`
**Schema:** `public`
**Owner:** Platform team (cross-cutting)

```sql
-- ============================================================================
-- MASTER ERROR LOG TABLE
-- ============================================================================
-- Purpose: Global visibility into all pipeline failures
-- Owner: Platform team (NOT a hub — cross-cutting observability)
-- Doctrine: Append-only, correlation required
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.shq_master_error_log (
    -- Primary Key
    error_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Temporal
    timestamp_utc       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Correlation (REQUIRED)
    correlation_id      UUID NOT NULL,

    -- Location (Hub/Sub-Hub/Process/Phase)
    hub                 VARCHAR(50) NOT NULL,
    sub_hub             VARCHAR(50),
    process_id          VARCHAR(100) NOT NULL,
    pipeline_phase      VARCHAR(50) NOT NULL,

    -- Entity Context
    entity_type         VARCHAR(50) NOT NULL,
    entity_id           VARCHAR(100),

    -- Error Classification
    severity            VARCHAR(20) NOT NULL,
    error_code          VARCHAR(50) NOT NULL,
    error_message       TEXT NOT NULL,

    -- Source Context
    source_tool         VARCHAR(100),
    operating_mode      VARCHAR(20) NOT NULL,

    -- Actionability
    retryable           BOOLEAN NOT NULL DEFAULT false,

    -- Cost Impact
    cost_impact_usd     DECIMAL(10, 4),

    -- Raw Context
    metadata            JSONB,

    -- Constraints
    CONSTRAINT chk_correlation_id_format
        CHECK (correlation_id IS NOT NULL),
    CONSTRAINT chk_hub_valid
        CHECK (hub IN ('company', 'people', 'dol', 'blog_news', 'outreach', 'platform')),
    CONSTRAINT chk_severity_valid
        CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    CONSTRAINT chk_entity_type_valid
        CHECK (entity_type IN ('company', 'person', 'filing', 'article', 'batch', 'unknown')),
    CONSTRAINT chk_operating_mode_valid
        CHECK (operating_mode IN ('BURN_IN', 'STEADY_STATE'))
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Primary lookup patterns
CREATE INDEX idx_master_error_correlation
    ON public.shq_master_error_log (correlation_id);

CREATE INDEX idx_master_error_timestamp
    ON public.shq_master_error_log (timestamp_utc DESC);

CREATE INDEX idx_master_error_hub_subhub
    ON public.shq_master_error_log (hub, sub_hub);

CREATE INDEX idx_master_error_process_id
    ON public.shq_master_error_log (process_id);

CREATE INDEX idx_master_error_severity
    ON public.shq_master_error_log (severity)
    WHERE severity IN ('HIGH', 'CRITICAL');

CREATE INDEX idx_master_error_entity
    ON public.shq_master_error_log (entity_type, entity_id);

CREATE INDEX idx_master_error_error_code
    ON public.shq_master_error_log (error_code);

CREATE INDEX idx_master_error_operating_mode
    ON public.shq_master_error_log (operating_mode, timestamp_utc DESC);

-- Composite index for common alerting queries
CREATE INDEX idx_master_error_alerting
    ON public.shq_master_error_log (operating_mode, severity, timestamp_utc DESC);

-- ============================================================================
-- READ-ONLY ENFORCEMENT (RLS)
-- ============================================================================

-- Enable RLS
ALTER TABLE public.shq_master_error_log ENABLE ROW LEVEL SECURITY;

-- Allow INSERT from all authenticated roles
CREATE POLICY insert_errors ON public.shq_master_error_log
    FOR INSERT
    TO authenticated
    WITH CHECK (true);

-- Allow SELECT from all authenticated roles
CREATE POLICY select_errors ON public.shq_master_error_log
    FOR SELECT
    TO authenticated
    USING (true);

-- DENY UPDATE (no policy = denied)
-- DENY DELETE (no policy = denied)

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE public.shq_master_error_log IS
    'Global error visibility across all hubs/sub-hubs. Append-only. Correlation required.';

COMMENT ON COLUMN public.shq_master_error_log.correlation_id IS
    'End-to-end trace ID. REQUIRED. Links to local sub-hub logs.';

COMMENT ON COLUMN public.shq_master_error_log.process_id IS
    'Canonical process identifier. Format: hub.subhub.pipeline.phase';

COMMENT ON COLUMN public.shq_master_error_log.operating_mode IS
    'BURN_IN or STEADY_STATE. Affects alerting thresholds.';
```

### 2.2 Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `error_id` | UUID | Yes (auto) | Primary key, auto-generated |
| `timestamp_utc` | TIMESTAMP | Yes (auto) | When the error occurred, UTC |
| `correlation_id` | UUID | **YES** | End-to-end trace ID (REQUIRED) |
| `hub` | VARCHAR(50) | Yes | company, people, dol, blog_news, outreach, platform |
| `sub_hub` | VARCHAR(50) | No | Specific sub-hub or NULL for hub-level |
| `process_id` | VARCHAR(100) | Yes | Canonical process identifier (see Section 3) |
| `pipeline_phase` | VARCHAR(50) | Yes | Phase name or number |
| `entity_type` | VARCHAR(50) | Yes | company, person, filing, article, batch, unknown |
| `entity_id` | VARCHAR(100) | No | company_id, person_id, filing_id, etc. |
| `severity` | VARCHAR(20) | Yes | LOW, MEDIUM, HIGH, CRITICAL |
| `error_code` | VARCHAR(50) | Yes | Machine-readable code (e.g., PSH-P5-001) |
| `error_message` | TEXT | Yes | Human-readable description |
| `source_tool` | VARCHAR(100) | No | Tool or service that failed (e.g., Hunter.io, Firecrawl) |
| `operating_mode` | VARCHAR(20) | Yes | BURN_IN or STEADY_STATE |
| `retryable` | BOOLEAN | Yes | Can the system retry automatically? |
| `cost_impact_usd` | DECIMAL(10,4) | No | Estimated cost impact in USD |
| `metadata` | JSONB | No | Raw context payload (stack trace, request/response, etc.) |

---

## 3. Process ID Standard (Mandatory)

### 3.1 Format Specification

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         PROCESS ID FORMAT                                     ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   FORMAT: <hub>.<subhub>.<pipeline>.<phase>                                  ║
║                                                                               ║
║   COMPONENTS:                                                                 ║
║   ├── hub:       company | people | dol | blog_news | outreach | platform   ║
║   ├── subhub:    identity | talentflow | form5500 | news | campaign | core  ║
║   ├── pipeline:  Specific pipeline name                                      ║
║   └── phase:     Phase name or number                                        ║
║                                                                               ║
║   RULES:                                                                      ║
║   • All lowercase                                                            ║
║   • No spaces (use underscores)                                              ║
║   • 4 components separated by dots                                           ║
║   • Max length: 100 characters                                               ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### 3.2 Process ID Registry

#### Company Hub Pipeline

| Process ID | Description |
|------------|-------------|
| `company.identity.matching.phase1` | Phase 1: Company Matching |
| `company.identity.matching.phase1b` | Phase 1b: Unmatched Hold Export |
| `company.identity.domain.phase2` | Phase 2: Domain Resolution |
| `company.identity.pattern.phase3` | Phase 3: Email Pattern Waterfall |
| `company.identity.verification.phase4` | Phase 4: Pattern Verification |
| `company.bit.aggregation.score` | BIT Engine: Signal Aggregation |
| `company.bit.decision.threshold` | BIT Engine: Decision Threshold |
| `company.movement.state.transition` | Movement Engine: State Transition |

#### People Sub-Hub

| Process ID | Description |
|------------|-------------|
| `people.lifecycle.ingest.phase0` | Phase 0: People Ingest |
| `people.lifecycle.email.phase5` | Phase 5: Email Generation |
| `people.lifecycle.slot.phase6` | Phase 6: Slot Assignment |
| `people.lifecycle.queue.phase7` | Phase 7: Enrichment Queue |
| `people.lifecycle.output.phase8` | Phase 8: Output Writer |
| `people.talentflow.gate.company` | Talent Flow: Company Gate |
| `people.talentflow.detect.movement` | Talent Flow: Movement Detection |

#### DOL Sub-Hub

| Process ID | Description |
|------------|-------------|
| `dol.form5500.ingest.parse` | Form 5500: File Parsing |
| `dol.form5500.match.ein` | Form 5500: EIN Matching |
| `dol.form5500.extract.schedule_a` | Form 5500: Schedule A Extraction |
| `dol.form5500.signal.emit` | Form 5500: Signal Emission |
| `dol.broker.detect.change` | Broker: Change Detection |

#### Blog/News Sub-Hub

| Process ID | Description |
|------------|-------------|
| `blog_news.news.ingest.crawl` | News: Article Crawl |
| `blog_news.news.extract.entity` | News: Entity Extraction |
| `blog_news.news.match.company` | News: Company Matching |
| `blog_news.news.classify.event` | News: Event Classification |
| `blog_news.news.signal.emit` | News: Signal Emission |

#### Outreach Node

| Process ID | Description |
|------------|-------------|
| `outreach.campaign.promote.log` | Campaign: Promote to Log |
| `outreach.campaign.enroll.sequence` | Campaign: Sequence Enrollment |
| `outreach.campaign.send.schedule` | Campaign: Send Scheduling |

---

## 4. Error Emission Contract

### 4.1 JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MasterErrorEvent",
  "description": "Error event emitted to shq_master_error_log",
  "type": "object",
  "required": [
    "correlation_id",
    "hub",
    "process_id",
    "pipeline_phase",
    "entity_type",
    "severity",
    "error_code",
    "error_message",
    "operating_mode",
    "retryable"
  ],
  "properties": {
    "correlation_id": {
      "type": "string",
      "format": "uuid",
      "description": "End-to-end trace ID (REQUIRED)"
    },
    "hub": {
      "type": "string",
      "enum": ["company", "people", "dol", "blog_news", "outreach", "platform"],
      "description": "Source hub"
    },
    "sub_hub": {
      "type": "string",
      "description": "Specific sub-hub or null for hub-level errors"
    },
    "process_id": {
      "type": "string",
      "pattern": "^[a-z_]+\\.[a-z_]+\\.[a-z_]+\\.[a-z0-9_]+$",
      "maxLength": 100,
      "description": "Canonical process identifier"
    },
    "pipeline_phase": {
      "type": "string",
      "description": "Phase name or number"
    },
    "entity_type": {
      "type": "string",
      "enum": ["company", "person", "filing", "article", "batch", "unknown"],
      "description": "Type of entity involved"
    },
    "entity_id": {
      "type": "string",
      "description": "ID of the entity (company_id, person_id, etc.)"
    },
    "severity": {
      "type": "string",
      "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
      "description": "Error severity level"
    },
    "error_code": {
      "type": "string",
      "pattern": "^[A-Z]+-[A-Z0-9]+-[0-9]+$",
      "description": "Machine-readable error code"
    },
    "error_message": {
      "type": "string",
      "description": "Human-readable error description"
    },
    "source_tool": {
      "type": "string",
      "description": "Tool or service that failed"
    },
    "operating_mode": {
      "type": "string",
      "enum": ["BURN_IN", "STEADY_STATE"],
      "description": "Current operational mode"
    },
    "retryable": {
      "type": "boolean",
      "description": "Can the system retry automatically?"
    },
    "cost_impact_usd": {
      "type": "number",
      "minimum": 0,
      "description": "Estimated cost impact in USD"
    },
    "metadata": {
      "type": "object",
      "description": "Additional context (stack trace, request/response, etc.)"
    }
  }
}
```

### 4.2 Example Error Events

#### Example 1: Company Matching Failure (People Sub-Hub)

```json
{
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "hub": "company",
  "sub_hub": "identity",
  "process_id": "company.identity.matching.phase1",
  "pipeline_phase": "phase1",
  "entity_type": "company",
  "entity_id": null,
  "severity": "MEDIUM",
  "error_code": "PIPE-101",
  "error_message": "No company match found for input 'Acme Corp' - score below threshold",
  "source_tool": "jaro_winkler",
  "operating_mode": "STEADY_STATE",
  "retryable": false,
  "cost_impact_usd": null,
  "metadata": {
    "input_company_name": "Acme Corp",
    "best_match_score": 0.72,
    "threshold": 0.85,
    "candidates_evaluated": 5
  }
}
```

#### Example 2: API Rate Limit (Pattern Waterfall)

```json
{
  "correlation_id": "550e8400-e29b-41d4-a716-446655440001",
  "hub": "company",
  "sub_hub": "identity",
  "process_id": "company.identity.pattern.phase3",
  "pipeline_phase": "phase3",
  "entity_type": "company",
  "entity_id": "04.04.02.04.30000.001",
  "severity": "HIGH",
  "error_code": "PIPE-301",
  "error_message": "Hunter.io API rate limit exceeded",
  "source_tool": "hunter.io",
  "operating_mode": "STEADY_STATE",
  "retryable": true,
  "cost_impact_usd": 0.01,
  "metadata": {
    "api_response_code": 429,
    "retry_after_seconds": 3600,
    "tier": 1,
    "domain": "acme.com"
  }
}
```

#### Example 3: DOL Filing Parse Error

```json
{
  "correlation_id": "550e8400-e29b-41d4-a716-446655440002",
  "hub": "dol",
  "sub_hub": "form5500",
  "process_id": "dol.form5500.ingest.parse",
  "pipeline_phase": "ingest",
  "entity_type": "filing",
  "entity_id": "2024-5500-123456",
  "severity": "MEDIUM",
  "error_code": "DOL-002",
  "error_message": "Invalid XML structure in Form 5500 filing",
  "source_tool": "dol_parser",
  "operating_mode": "BURN_IN",
  "retryable": false,
  "cost_impact_usd": null,
  "metadata": {
    "filing_year": 2024,
    "ein": "12-3456789",
    "xml_error": "Unexpected element at line 42"
  }
}
```

#### Example 4: Email Generation Failure (People Sub-Hub)

```json
{
  "correlation_id": "550e8400-e29b-41d4-a716-446655440003",
  "hub": "people",
  "sub_hub": "lifecycle",
  "process_id": "people.lifecycle.email.phase5",
  "pipeline_phase": "phase5",
  "entity_type": "person",
  "entity_id": "04.04.02.04.20000.042",
  "severity": "MEDIUM",
  "error_code": "PSH-P5-001",
  "error_message": "Cannot generate email - missing first_name",
  "source_tool": "pattern_template",
  "operating_mode": "STEADY_STATE",
  "retryable": false,
  "cost_impact_usd": null,
  "metadata": {
    "company_id": "04.04.02.04.30000.001",
    "pattern": "{first}.{last}",
    "last_name": "Smith",
    "first_name": null
  }
}
```

---

## 5. Error Emission Flow

### 5.1 Emission Sequence

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ERROR EMISSION FLOW                                  │
└─────────────────────────────────────────────────────────────────────────────┘

    PIPELINE PHASE (Error Occurs)
              │
              │ 1. Catch exception/failure
              │
              ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                    LOCAL FAILURE TABLE                               │
    │                    (Sub-Hub Owned)                                   │
    │                                                                      │
    │   INSERT INTO people_processing_errors (                            │
    │       correlation_id, phase, person_id, error_code, ...            │
    │   );                                                                 │
    │                                                                      │
    │   Sub-hub retains ownership for:                                    │
    │   • Remediation workflow                                            │
    │   • Retry logic                                                     │
    │   • Resolution tracking                                             │
    └───────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    │ 2. Local write succeeds
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                    NORMALIZE ERROR EVENT                             │
    │                                                                      │
    │   error_event = {                                                   │
    │       "correlation_id": correlation_id,                             │
    │       "hub": "people",                                              │
    │       "sub_hub": "lifecycle",                                       │
    │       "process_id": "people.lifecycle.email.phase5",               │
    │       "pipeline_phase": "phase5",                                   │
    │       "entity_type": "person",                                      │
    │       "entity_id": person_id,                                       │
    │       "severity": "MEDIUM",                                         │
    │       "error_code": "PSH-P5-001",                                   │
    │       "error_message": "Cannot generate email - missing first_name",│
    │       "operating_mode": get_operating_mode(),                       │
    │       "retryable": false,                                           │
    │       ...                                                           │
    │   }                                                                  │
    └───────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    │ 3. Normalize complete
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                    MASTER ERROR LOG                                  │
    │                    (Global Visibility)                               │
    │                                                                      │
    │   INSERT INTO shq_master_error_log (                                │
    │       correlation_id, hub, sub_hub, process_id, ...                │
    │   ) VALUES (...);                                                   │
    │                                                                      │
    │   APPEND-ONLY — No updates, no deletes                             │
    └─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Emission Rules

| Rule | Description |
|------|-------------|
| One record per failure | Each failure event creates exactly one master error record |
| Retries emit new records | If a retry fails, a NEW record is created (same correlation_id) |
| Local first | Local sub-hub table MUST be written before master log |
| Correlation required | Errors without correlation_id are REJECTED |
| No duplicates | Same error_id cannot be inserted twice |
| Append-only | No UPDATE or DELETE operations allowed |

### 5.3 Recovery Events (Optional)

When an error is resolved, sub-hubs MAY emit a RESOLVED event:

```json
{
  "correlation_id": "550e8400-e29b-41d4-a716-446655440003",
  "hub": "people",
  "sub_hub": "lifecycle",
  "process_id": "people.lifecycle.email.phase5",
  "pipeline_phase": "phase5",
  "entity_type": "person",
  "entity_id": "04.04.02.04.20000.042",
  "severity": "LOW",
  "error_code": "PSH-P5-001-RESOLVED",
  "error_message": "Previously failed email generation now succeeded after data enrichment",
  "operating_mode": "STEADY_STATE",
  "retryable": false,
  "metadata": {
    "original_error_id": "uuid-of-original-error",
    "resolution_method": "data_enrichment",
    "resolved_at": "2025-12-17T14:30:00Z"
  }
}
```

---

## 6. Alerting & Thresholds

### 6.1 Mode-Based Alerting

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ALERTING RULES BY MODE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   BURN-IN MODE                                                              │
│   ════════════════════════════════════════════════════════════════════      │
│   Purpose: Allow noise, focus on patterns                                   │
│                                                                             │
│   • Aggregate alerts only (no individual paging)                           │
│   • Daily summary of all errors                                            │
│   • Alert if CRITICAL count > 10 in 24 hours                               │
│   • Alert if error rate > 20% (vs expected)                                │
│   • NO paging on single failures                                           │
│                                                                             │
│   STEADY-STATE MODE                                                         │
│   ════════════════════════════════════════════════════════════════════      │
│   Purpose: Catch regressions immediately                                    │
│                                                                             │
│   • Any CRITICAL error → Immediate alert + page on-call                    │
│   • Any HIGH error → Immediate alert (no page)                             │
│   • MEDIUM error count > 5 in 15 minutes → Alert                           │
│   • LOW errors → Daily summary only                                        │
│   • Error rate spike > 3x baseline → Alert + page                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Alert Threshold Table

| Operating Mode | Severity | Threshold | Action |
|----------------|----------|-----------|--------|
| BURN_IN | CRITICAL | > 10 in 24h | Aggregate alert |
| BURN_IN | HIGH | > 50 in 24h | Aggregate alert |
| BURN_IN | MEDIUM | > 200 in 24h | Daily summary |
| BURN_IN | LOW | — | Daily summary |
| STEADY_STATE | CRITICAL | Any | Immediate alert + page |
| STEADY_STATE | HIGH | Any | Immediate alert |
| STEADY_STATE | MEDIUM | > 5 in 15 min | Alert |
| STEADY_STATE | LOW | — | Daily summary |

### 6.3 Alert Query Examples

#### CRITICAL Errors (Steady-State, Last Hour)

```sql
SELECT
    hub,
    sub_hub,
    process_id,
    error_code,
    COUNT(*) as error_count
FROM public.shq_master_error_log
WHERE
    operating_mode = 'STEADY_STATE'
    AND severity = 'CRITICAL'
    AND timestamp_utc >= NOW() - INTERVAL '1 hour'
GROUP BY hub, sub_hub, process_id, error_code
ORDER BY error_count DESC;
```

#### Error Rate by Hub (Last 24 Hours)

```sql
SELECT
    hub,
    COUNT(*) as total_errors,
    COUNT(*) FILTER (WHERE severity = 'CRITICAL') as critical,
    COUNT(*) FILTER (WHERE severity = 'HIGH') as high,
    COUNT(*) FILTER (WHERE severity = 'MEDIUM') as medium,
    COUNT(*) FILTER (WHERE severity = 'LOW') as low
FROM public.shq_master_error_log
WHERE timestamp_utc >= NOW() - INTERVAL '24 hours'
GROUP BY hub
ORDER BY total_errors DESC;
```

#### Errors by Correlation ID (Troubleshooting)

```sql
SELECT
    timestamp_utc,
    process_id,
    pipeline_phase,
    severity,
    error_code,
    error_message
FROM public.shq_master_error_log
WHERE correlation_id = '550e8400-e29b-41d4-a716-446655440000'
ORDER BY timestamp_utc ASC;
```

---

## 7. Integration with Existing PRDs

### 7.1 PRD Cross-Reference

| PRD | Error Code Prefix | Local Table | Integration Status |
|-----|-------------------|-------------|-------------------|
| PRD_COMPANY_HUB.md v2.1 | PIPE- | `pipeline_errors` | Integrated |
| PRD_PEOPLE_SUBHUB.md v2.1 | PSH- | `people_processing_errors` | Integrated |
| PRD_DOL_SUBHUB.md v2.1 | DOL- | `dol_processing_errors` | Integrated |
| PRD_BLOG_NEWS_SUBHUB.md v2.1 | BLOG- | `blog_processing_errors` | Integrated |
| PRD_COMPANY_HUB_PIPELINE.md v2.1 | PIPE- | `pipeline_errors` | Integrated |

### 7.2 Error Code Alignment

All error codes from v2.1 PRDs follow the format: `{PREFIX}-{CATEGORY}{NUMBER}`

| Hub | Prefix | Example |
|-----|--------|---------|
| Company Hub Pipeline | PIPE- | PIPE-001, PIPE-101, PIPE-301 |
| People Sub-Hub | PSH- | PSH-P0-001, PSH-P5-001 |
| DOL Sub-Hub | DOL- | DOL-001, DOL-002, DOL-007 |
| Blog/News Sub-Hub | BLOG- | BLOG-001, BLOG-101, BLOG-201 |

### 7.3 Two-Layer Error Model (From v2.1 PRDs)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TWO-LAYER ERROR MODEL (v2.1 ALIGNMENT)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   LAYER 1: LOCAL (Sub-Hub Owned)                                           │
│   ├── Table: {subhub}_processing_errors                                    │
│   ├── Owner: Sub-hub team                                                  │
│   ├── Purpose: Operational remediation, retry logic                        │
│   └── Fields: correlation_id, phase, entity_id, error_code, timestamp      │
│                                                                             │
│   LAYER 2: GLOBAL (Platform Owned)                                         │
│   ├── Table: shq_master_error_log (THIS PRD)                               │
│   ├── Owner: Platform team                                                 │
│   ├── Purpose: Trend analysis, alerting, troubleshooting                   │
│   └── Fields: Full error event (see Section 2)                             │
│                                                                             │
│   EMISSION RULE:                                                            │
│   • Severity >= WARN → Emit to BOTH layers                                 │
│   • Severity < WARN → Local only (optional global)                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Implementation

### 8.1 Python Error Emitter

```python
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class Hub(Enum):
    COMPANY = "company"
    PEOPLE = "people"
    DOL = "dol"
    BLOG_NEWS = "blog_news"
    OUTREACH = "outreach"
    PLATFORM = "platform"

class Severity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class EntityType(Enum):
    COMPANY = "company"
    PERSON = "person"
    FILING = "filing"
    ARTICLE = "article"
    BATCH = "batch"
    UNKNOWN = "unknown"

class OperatingMode(Enum):
    BURN_IN = "BURN_IN"
    STEADY_STATE = "STEADY_STATE"

class MasterErrorEmitter:
    """
    Emits normalized error events to shq_master_error_log.

    DOCTRINE:
    - Local First: Write to local sub-hub table before emitting here
    - Correlation Required: All errors MUST have correlation_id
    - Append-Only: No updates or deletes
    """

    def __init__(self, db_connection, operating_mode: OperatingMode):
        self.db = db_connection
        self.operating_mode = operating_mode

    def emit(
        self,
        correlation_id: str,  # REQUIRED
        hub: Hub,
        process_id: str,
        pipeline_phase: str,
        entity_type: EntityType,
        severity: Severity,
        error_code: str,
        error_message: str,
        sub_hub: Optional[str] = None,
        entity_id: Optional[str] = None,
        source_tool: Optional[str] = None,
        retryable: bool = False,
        cost_impact_usd: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Emit error event to master error log.

        Returns: error_id of inserted record

        Raises:
            ValueError: If correlation_id is missing or invalid
        """
        # Validate correlation_id (REQUIRED)
        if not correlation_id:
            raise ValueError("correlation_id is REQUIRED per Barton Doctrine")

        try:
            uuid.UUID(correlation_id)
        except ValueError:
            raise ValueError(f"correlation_id must be valid UUID: {correlation_id}")

        # Validate process_id format
        if not self._validate_process_id(process_id):
            raise ValueError(f"Invalid process_id format: {process_id}")

        # Generate error_id
        error_id = str(uuid.uuid4())

        # Insert into master error log
        query = """
            INSERT INTO public.shq_master_error_log (
                error_id, timestamp_utc, correlation_id,
                hub, sub_hub, process_id, pipeline_phase,
                entity_type, entity_id,
                severity, error_code, error_message,
                source_tool, operating_mode, retryable,
                cost_impact_usd, metadata
            ) VALUES (
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s
            )
        """

        self.db.execute(query, (
            error_id,
            datetime.utcnow(),
            correlation_id,
            hub.value,
            sub_hub,
            process_id,
            pipeline_phase,
            entity_type.value,
            entity_id,
            severity.value,
            error_code,
            error_message,
            source_tool,
            self.operating_mode.value,
            retryable,
            cost_impact_usd,
            json.dumps(metadata) if metadata else None
        ))

        return error_id

    def _validate_process_id(self, process_id: str) -> bool:
        """Validate process_id format: hub.subhub.pipeline.phase"""
        import re
        pattern = r'^[a-z_]+\.[a-z_]+\.[a-z_]+\.[a-z0-9_]+$'
        return bool(re.match(pattern, process_id)) and len(process_id) <= 100


# Usage Example
def example_usage():
    emitter = MasterErrorEmitter(db_connection, OperatingMode.STEADY_STATE)

    # First, write to local sub-hub table (LOCAL FIRST)
    # ... local_table.insert(error_record) ...

    # Then emit to master error log
    error_id = emitter.emit(
        correlation_id="550e8400-e29b-41d4-a716-446655440000",
        hub=Hub.PEOPLE,
        sub_hub="lifecycle",
        process_id="people.lifecycle.email.phase5",
        pipeline_phase="phase5",
        entity_type=EntityType.PERSON,
        entity_id="04.04.02.04.20000.042",
        severity=Severity.MEDIUM,
        error_code="PSH-P5-001",
        error_message="Cannot generate email - missing first_name",
        source_tool="pattern_template",
        retryable=False,
        metadata={
            "company_id": "04.04.02.04.30000.001",
            "pattern": "{first}.{last}",
            "last_name": "Smith",
            "first_name": None
        }
    )

    print(f"Error emitted with ID: {error_id}")
```

---

## 9. Migration Script

```sql
-- ============================================================================
-- MIGRATION: Create shq_master_error_log table
-- ============================================================================
-- Run this migration to create the master error log infrastructure
-- ============================================================================

-- 1. Create the table
CREATE TABLE IF NOT EXISTS public.shq_master_error_log (
    error_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp_utc       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    correlation_id      UUID NOT NULL,
    hub                 VARCHAR(50) NOT NULL,
    sub_hub             VARCHAR(50),
    process_id          VARCHAR(100) NOT NULL,
    pipeline_phase      VARCHAR(50) NOT NULL,
    entity_type         VARCHAR(50) NOT NULL,
    entity_id           VARCHAR(100),
    severity            VARCHAR(20) NOT NULL,
    error_code          VARCHAR(50) NOT NULL,
    error_message       TEXT NOT NULL,
    source_tool         VARCHAR(100),
    operating_mode      VARCHAR(20) NOT NULL,
    retryable           BOOLEAN NOT NULL DEFAULT false,
    cost_impact_usd     DECIMAL(10, 4),
    metadata            JSONB,
    CONSTRAINT chk_correlation_id_format CHECK (correlation_id IS NOT NULL),
    CONSTRAINT chk_hub_valid CHECK (hub IN ('company', 'people', 'dol', 'blog_news', 'outreach', 'platform')),
    CONSTRAINT chk_severity_valid CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    CONSTRAINT chk_entity_type_valid CHECK (entity_type IN ('company', 'person', 'filing', 'article', 'batch', 'unknown')),
    CONSTRAINT chk_operating_mode_valid CHECK (operating_mode IN ('BURN_IN', 'STEADY_STATE'))
);

-- 2. Create indexes
CREATE INDEX IF NOT EXISTS idx_master_error_correlation ON public.shq_master_error_log (correlation_id);
CREATE INDEX IF NOT EXISTS idx_master_error_timestamp ON public.shq_master_error_log (timestamp_utc DESC);
CREATE INDEX IF NOT EXISTS idx_master_error_hub_subhub ON public.shq_master_error_log (hub, sub_hub);
CREATE INDEX IF NOT EXISTS idx_master_error_process_id ON public.shq_master_error_log (process_id);
CREATE INDEX IF NOT EXISTS idx_master_error_severity ON public.shq_master_error_log (severity) WHERE severity IN ('HIGH', 'CRITICAL');
CREATE INDEX IF NOT EXISTS idx_master_error_entity ON public.shq_master_error_log (entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_master_error_error_code ON public.shq_master_error_log (error_code);
CREATE INDEX IF NOT EXISTS idx_master_error_operating_mode ON public.shq_master_error_log (operating_mode, timestamp_utc DESC);
CREATE INDEX IF NOT EXISTS idx_master_error_alerting ON public.shq_master_error_log (operating_mode, severity, timestamp_utc DESC);

-- 3. Enable RLS
ALTER TABLE public.shq_master_error_log ENABLE ROW LEVEL SECURITY;

-- 4. Create policies (INSERT and SELECT only - NO UPDATE/DELETE)
DROP POLICY IF EXISTS insert_errors ON public.shq_master_error_log;
CREATE POLICY insert_errors ON public.shq_master_error_log
    FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS select_errors ON public.shq_master_error_log;
CREATE POLICY select_errors ON public.shq_master_error_log
    FOR SELECT USING (true);

-- 5. Add comments
COMMENT ON TABLE public.shq_master_error_log IS 'Global error visibility across all hubs/sub-hubs. Append-only. Correlation required.';
COMMENT ON COLUMN public.shq_master_error_log.correlation_id IS 'End-to-end trace ID. REQUIRED. Links to local sub-hub logs.';
COMMENT ON COLUMN public.shq_master_error_log.process_id IS 'Canonical process identifier. Format: hub.subhub.pipeline.phase';
COMMENT ON COLUMN public.shq_master_error_log.operating_mode IS 'BURN_IN or STEADY_STATE. Affects alerting thresholds.';

-- 6. Create orphan_errors table for rejected errors (missing correlation_id)
CREATE TABLE IF NOT EXISTS public.shq_orphan_errors (
    orphan_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp_utc       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    raw_event           JSONB NOT NULL,
    rejection_reason    TEXT NOT NULL
);

COMMENT ON TABLE public.shq_orphan_errors IS 'Errors rejected due to missing correlation_id or validation failures.';

-- Done
SELECT 'Migration complete: shq_master_error_log created' AS status;
```

---

## 10. Enforcement Controls (v1.1 Hardening)

### 10.1 Process ID is Mandatory (FAIL HARD)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    PROCESS ID ENFORCEMENT (v1.1)                              ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   DOCTRINE: process_id is MANDATORY. FAIL HARD if missing or malformed.      ║
║                                                                               ║
║   VALIDATION RULES:                                                           ║
║   ├── NOT NULL — process_id cannot be NULL                                   ║
║   ├── NOT EMPTY — process_id cannot be empty string or whitespace            ║
║   ├── FORMAT — Must match: hub.subhub.pipeline.phase                         ║
║   ├── CASE — All lowercase (no uppercase allowed)                            ║
║   ├── LENGTH — Min 10 chars, max 100 chars                                   ║
║   └── COMPONENTS — Exactly 4 dot-separated non-empty parts                   ║
║                                                                               ║
║   FAIL CONDITIONS:                                                            ║
║   • process_id is NULL → ValidationError (FAIL HARD)                         ║
║   • process_id is "" or whitespace → ValidationError (FAIL HARD)             ║
║   • process_id has wrong format → ValidationError (FAIL HARD)                ║
║   • process_id has < 4 or > 4 components → ValidationError (FAIL HARD)       ║
║                                                                               ║
║   ENFORCEMENT LAYERS:                                                         ║
║   1. Python: master_error_emitter.py validates before DB call               ║
║   2. SQL Function: emit_master_error() validates before INSERT              ║
║   3. DB Constraint: chk_master_error_process_id_format enforces regex       ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### 10.2 Database Immutability (Physical Enforcement)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    IMMUTABILITY ENFORCEMENT (v1.1)                            ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   DOCTRINE: Error history is immutable.                                       ║
║             Corrections are new records, never edits.                         ║
║                                                                               ║
║   ENFORCEMENT LAYERS:                                                         ║
║                                                                               ║
║   1. ROLE-BASED ACCESS CONTROL:                                              ║
║      └── error_log_writer role: INSERT-only permissions                      ║
║      └── UPDATE, DELETE, TRUNCATE: NOT GRANTED to any role                   ║
║                                                                               ║
║   2. ROW-LEVEL SECURITY (RLS):                                               ║
║      └── INSERT policy: ALLOW (append-only)                                  ║
║      └── SELECT policy: ALLOW (read access)                                  ║
║      └── UPDATE policy: NONE (denied by default)                             ║
║      └── DELETE policy: NONE (denied by default)                             ║
║                                                                               ║
║   3. TRIGGER ENFORCEMENT (NUCLEAR OPTION):                                   ║
║      └── trg_master_error_immutability_update: BLOCKS all UPDATE             ║
║      └── trg_master_error_immutability_delete: BLOCKS all DELETE             ║
║      └── Triggers fire BEFORE operation (fail fast)                          ║
║      └── Even superuser cannot bypass triggers                               ║
║                                                                               ║
║   4. PERMISSION REVOCATION:                                                  ║
║      └── REVOKE UPDATE FROM PUBLIC                                           ║
║      └── REVOKE DELETE FROM PUBLIC                                           ║
║      └── REVOKE TRUNCATE FROM PUBLIC                                         ║
║                                                                               ║
║   BLOCKED OPERATIONS:                                                         ║
║   • UPDATE → EXCEPTION raised with error_id                                  ║
║   • DELETE → EXCEPTION raised with error_id                                  ║
║   • TRUNCATE → EXCEPTION raised (if event trigger enabled)                   ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### 10.3 Error Messages on Violation

| Violation | Error Message |
|-----------|---------------|
| Missing correlation_id | `FAIL HARD: correlation_id is MANDATORY per Barton Doctrine` |
| Missing process_id | `FAIL HARD: process_id is MANDATORY per Barton Doctrine` |
| Malformed process_id | `FAIL HARD: Malformed process_id: {value}. Expected format: hub.subhub.pipeline.phase` |
| Attempted UPDATE | `UPDATE BLOCKED: shq_master_error_log is immutable per Barton Doctrine. Error history cannot be modified. Corrections must be new records.` |
| Attempted DELETE | `DELETE BLOCKED: shq_master_error_log is immutable per Barton Doctrine. Error history cannot be deleted. Records are permanent.` |

### 10.4 Migration Files

| Migration | File | Purpose |
|-----------|------|---------|
| 002 | `002_create_master_error_log.sql` | Create table, indexes, RLS, views |
| 003 | `003_enforce_master_error_immutability.sql` | Hardening: role, triggers, constraints |

---

## 11. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-17 | Initial Master Error Log PRD |
| 1.1 | 2025-12-17 | Added Section 10: Enforcement Controls (process_id mandatory, DB immutability) |

---

*Document Version: 1.1*
*Last Updated: 2025-12-17*
*Type: Cross-Cutting Observability Process*
*Owner: Platform Team*
*Doctrine: Bicycle Wheel v1.1 / Barton Doctrine*

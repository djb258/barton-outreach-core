# Technical Architecture Specification: Completeness Evaluator

**Repository**: barton-outreach-core
**Version**: 1.0.0
**Script**: `scripts/completeness/evaluate_completeness.py`

---

## Purpose

The Completeness Evaluator is a deterministic script that evaluates entity completeness across all sub-hubs based on the rules defined in `TAS_COMPLETENESS_CONTRACT.md`.

---

## Key Properties

| Property | Value |
|----------|-------|
| **Unifying Key** | `outreach_id` (UUID) |
| **Read Tables** | Source data tables (company_target, dol, people, blog, outreach) |
| **Write Table** | `outreach.company_hub_status` ONLY |
| **Idempotent** | YES - safe to re-run |
| **Destructive** | NO - never mutates source data |

---

## How It Works

### 1. Waterfall Evaluation

The evaluator processes hubs in waterfall order:

```
1. Company Target    (REQUIRED) → Must PASS before #2
2. DOL Filings       (REQUIRED) → Must PASS before #3
3. People Intelligence (REQUIRED) → Must PASS before #4
4. Talent Flow       (REQUIRED) → Must PASS before #5/#6
5. Blog Content      (OPTIONAL)
6. Outreach Execution (OPTIONAL)
```

### 2. Upstream Dependency Check

Before evaluating a hub, the script checks if the upstream hub has status = PASS.

If upstream is NOT PASS:
- Status: `BLOCKED`
- Blocker Type: `UPSTREAM_BLOCKED`
- Evidence: `{ "blocking_hub": "<hub>", "blocking_status": "<status>" }`

### 3. Per-Hub Rules

| Hub | PASS When | FAIL When |
|-----|-----------|-----------|
| **Company Target** | `email_method IS NOT NULL AND confidence_score >= 0.5` | Missing or low confidence |
| **DOL Filings** | `form_5500_matched = true` OR `employee_count < 100` (N/A) | No EIN match |
| **People Intelligence** | `slot_fill_rate >= threshold` | Below threshold |
| **Talent Flow** | `movement_rate >= threshold` OR `age < 90 days` | Stale, no movements |
| **Blog Content** | `signal_count >= 1` | No signals |
| **Outreach Execution** | `campaign_status IN ('active', 'completed')` | Not started |

### 4. Output Format

All output is structured JSON to stdout:

```json
{"timestamp": "2026-01-28T12:00:00Z", "event": "result", "entity_id": "abc-123", "hub_id": "company-target", "status": "PASS", "blocker_type": null, "metric_value": 0.85}
```

---

## Usage

### Evaluate All Entities (Limited)

```bash
# Evaluate up to 100 entities
doppler run -- python scripts/completeness/evaluate_completeness.py --limit 100
```

### Evaluate Single Entity

```bash
# Evaluate specific entity across all hubs
doppler run -- python scripts/completeness/evaluate_completeness.py --entity-id "abc-123-def-456"
```

### Evaluate Single Entity + Hub

```bash
# Evaluate specific entity for specific hub
doppler run -- python scripts/completeness/evaluate_completeness.py --entity-id "abc-123" --hub "company-target"
```

### Dry Run (No Database Writes)

```bash
# Preview what would be written
python scripts/completeness/evaluate_completeness.py --dry-run --entity-id "abc-123"
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NEON_HOST` | YES | Neon PostgreSQL host |
| `NEON_DATABASE` | YES | Database name |
| `NEON_USER` | YES | Database user |
| `NEON_PASSWORD` | YES | Database password |

Use Doppler to inject: `doppler run -- python ...`

---

## Database Writes

The script ONLY writes to `outreach.company_hub_status`:

```sql
INSERT INTO outreach.company_hub_status (
    company_unique_id,  -- outreach_id
    hub_id,             -- e.g., 'company-target'
    status,             -- PASS | FAIL | BLOCKED
    blocker_type,       -- ENUM value or NULL
    blocker_evidence,   -- JSONB or NULL
    metric_value,       -- Numeric metric
    last_processed_at   -- Evaluation timestamp
)
ON CONFLICT DO UPDATE ...
```

**NEVER WRITES TO:**
- `outreach.outreach`
- `outreach.company_target`
- `outreach.dol`
- `outreach.people`
- `outreach.blog`
- Any other source data table

---

## When to Run

| Trigger | Frequency | Command |
|---------|-----------|---------|
| **After pipeline run** | Per batch | `--limit 1000` |
| **Single entity debug** | On demand | `--entity-id <id>` |
| **Full refresh** | Weekly | `--limit 50000` |
| **Dry run audit** | Before deployment | `--dry-run --limit 100` |

---

## Blocker Type Assignment

The evaluator assigns blocker types per `TAS_COMPLETENESS_CONTRACT.md`:

| Scenario | Blocker Type |
|----------|--------------|
| Required field NULL | `DATA_MISSING` |
| Searched, not found | `DATA_UNDISCOVERABLE` |
| Multiple conflicts | `DATA_CONFLICT` |
| API down | `SOURCE_UNAVAILABLE` |
| Hub doesn't apply | `NOT_APPLICABLE` |
| Needs human | `HUMAN_DECISION_REQUIRED` |
| Upstream not PASS | `UPSTREAM_BLOCKED` |
| Below threshold | `THRESHOLD_NOT_MET` |
| Data > 90 days | `EXPIRED` |

---

## Viewing Results

After running, query the canonical views:

```sql
-- Per-entity, per-hub status
SELECT * FROM outreach.vw_entity_completeness
WHERE entity_id = 'abc-123';

-- Overall entity status
SELECT * FROM outreach.vw_entity_overall_status
WHERE entity_id = 'abc-123';

-- Blocker distribution
SELECT * FROM outreach.vw_blocker_analysis;
```

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-28 |
| Author | Claude Code (AI Employee) |
| Script | scripts/completeness/evaluate_completeness.py |
| Contract | TAS_COMPLETENESS_CONTRACT.md |

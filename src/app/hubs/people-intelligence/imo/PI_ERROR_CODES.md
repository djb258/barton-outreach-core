# People Intelligence Error Codes

**Version:** 1.0.0
**Date:** 2026-01-08
**Doctrine:** Barton IMO v1.1

---

## Overview

This document defines the **stable machine keys** for all People Intelligence errors.
Error codes are permanent and NEVER reused. New errors get new codes.

---

## Error Code Format

```
PI-E[stage][sequence]

Where:
  PI     = People Intelligence
  E      = Error
  stage  = 1-digit stage code (1-5, 9)
  sequence = 2-digit sequence (01-99)
```

### Stage Codes

| Code | Stage | Description |
|------|-------|-------------|
| 1 | `slot_creation` | Creating slots for outreach_id |
| 2 | `slot_fill` | Filling slots with people |
| 3 | `movement_detect` | Detecting job changes |
| 4 | `enrichment` | External data enrichment |
| 5 | `promotion` | Exporting to outreach.people |
| 9 | `system` | Kill switches, infrastructure |

---

## Error Codes Reference

### Slot Creation Errors (PI-E1xx)

| Code | Type | Message | Recovery |
|------|------|---------|----------|
| `PI-E101` | validation | Invalid slot type: {slot_type}. Must be CEO\|CFO\|HR\|BEN. | manual_fix |
| `PI-E102` | validation | Outreach ID {outreach_id} already has slots created. Duplicate creation blocked. | discard |
| `PI-E103` | missing_data | Cannot create slots: company_unique_id missing for outreach {outreach_id}. | manual_fix |

### Slot Fill Errors (PI-E2xx)

| Code | Type | Message | Recovery |
|------|------|---------|----------|
| `PI-E201` | ambiguity | Multiple candidates for slot {slot_id}: confidence gap {gap}% < 15% threshold. | manual_fix |
| `PI-E202` | conflict | LinkedIn title '{linkedin_title}' conflicts with slot type {slot_type}. | manual_fix |
| `PI-E203` | missing_data | LinkedIn URL missing for candidate. Cannot verify identity. | manual_fix |
| `PI-E204` | validation | Slot {slot_id} already filled. Cannot overwrite. | discard |

### Movement Detection Errors (PI-E3xx)

| Code | Type | Message | Recovery |
|------|------|---------|----------|
| `PI-E301` | ambiguity | Movement type ambiguous for person {person_id}: {context}. | manual_fix |
| `PI-E302` | stale_data | LinkedIn data stale for person {person_id}. Last update: {last_update}. | auto_retry (24h) |
| `PI-E303` | conflict | Blog hint says '{blog_hint}' but LinkedIn shows '{linkedin_status}'. | manual_fix |

### Enrichment Errors (PI-E4xx)

| Code | Type | Message | Recovery |
|------|------|---------|----------|
| `PI-E401` | external_fail | Clay API timeout after {timeout_seconds}s for person {person_id}. | auto_retry (15m) |
| `PI-E402` | external_fail | Clay API blocked: rate limit exceeded. Cool-off required. | auto_retry (1h) |
| `PI-E403` | external_fail | Cost guardrail triggered: enrichment budget exhausted. | manual_fix |
| `PI-E404` | missing_data | No email found for person {person_id} after enrichment. | manual_fix |

### Promotion Errors (PI-E5xx)

| Code | Type | Message | Recovery |
|------|------|---------|----------|
| `PI-E501` | validation | Cannot promote slot {slot_id}: email not verified. | manual_fix |
| `PI-E502` | validation | Cannot promote slot {slot_id}: person_status is '{status}', expected 'active'. | manual_fix |
| `PI-E503` | external_fail | Database error promoting to outreach.people: {db_error}. | auto_retry (5m) |

### System Errors (PI-E9xx)

| Code | Type | Message | Recovery |
|------|------|---------|----------|
| `PI-E901` | validation | Kill switch PEOPLE_SLOT_AUTOFILL_ENABLED is disabled. Operations halted. | manual_fix |
| `PI-E902` | validation | Kill switch PEOPLE_MOVEMENT_DETECT_ENABLED is disabled. Operations halted. | manual_fix |
| `PI-E903` | validation | Kill switch PEOPLE_AUTO_REPLAY_ENABLED is disabled. Replay halted. | manual_fix |

---

## Error Types

| Type | Description | Typical Recovery |
|------|-------------|------------------|
| `validation` | Data fails validation rules | manual_fix or discard |
| `ambiguity` | Insufficient confidence gap | manual_fix |
| `conflict` | Source data contradicts | manual_fix |
| `missing_data` | Required data unavailable | manual_fix |
| `stale_data` | Data expired/outdated | auto_retry |
| `external_fail` | Third-party API failure | auto_retry |

---

## Retry Strategies

| Strategy | Description | Next Steps |
|----------|-------------|------------|
| `manual_fix` | Requires human intervention | Edit data, mark error as 'fixed', await replay |
| `auto_retry` | System will retry after delay | Wait for retry_after timestamp, automatic replay |
| `discard` | Cannot be recovered | Mark as 'abandoned', no replay |

---

## Error Lifecycle

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌───────────┐
│   open   │ ──► │  fixed   │ ──► │ replayed │     │ abandoned │
└──────────┘     └──────────┘     └──────────┘     └───────────┘
      │                                                   ▲
      │                                                   │
      └───────────────────────────────────────────────────┘
                    (if recovery impossible)
```

### State Transitions

| From | To | Trigger |
|------|-----|---------|
| `open` | `fixed` | Data corrected by operator |
| `open` | `abandoned` | Recovery deemed impossible |
| `fixed` | `replayed` | Replay worker processed successfully |
| `fixed` | `open` (new row) | Replay failed, new error created |

---

## Audit Requirements

Every People worker run MUST log:

- `process_id` — unique run identifier
- `slots_attempted` — number of slots tried
- `fills_succeeded` — successful slot fills
- `errors_emitted` — count of errors written
- `error_ids` — list of error UUIDs created

**No silent failures. Ever.**

---

## SQL Quick Reference

### Find open errors for outreach
```sql
SELECT * FROM people.people_errors
WHERE outreach_id = '<uuid>'
  AND status = 'open'
ORDER BY created_at;
```

### Count errors by stage
```sql
SELECT error_stage, COUNT(*)
FROM people.people_errors
WHERE status = 'open'
GROUP BY error_stage;
```

### Find errors ready for auto-retry
```sql
SELECT * FROM people.people_errors
WHERE status = 'open'
  AND retry_strategy = 'auto_retry'
  AND retry_after <= now();
```

### Get error details with slot context
```sql
SELECT 
    e.error_id,
    e.error_code,
    e.error_message,
    e.created_at,
    cs.slot_type,
    cs.slot_status
FROM people.people_errors e
LEFT JOIN people.company_slot cs ON e.slot_id::text = cs.slot_id
WHERE e.status = 'open'
ORDER BY e.created_at DESC
LIMIT 20;
```

---

## Adding New Error Codes

1. **Pick next available sequence** in the appropriate stage range
2. **Add to ERROR_CODES dict** in `people_errors.py`
3. **Update this document**
4. **Never reuse codes** — deprecated codes stay documented forever

### Template

```python
'PI-E{stage}{seq}': ErrorCodeDef(
    code='PI-E{stage}{seq}',
    stage=ErrorStage.{STAGE},
    error_type=ErrorType.{TYPE},
    message_template="{descriptive message with {placeholders}}",
    retry_strategy=RetryStrategy.{STRATEGY},
    retry_delay_minutes={N or None},
),
```

---

**Last Updated:** 2026-01-08
**Author:** People Intelligence Team
**Doctrine Version:** Barton IMO v1.1

# Marketing Safety Gate

#safety #enforcement #hard-fail #v1 #frozen

## Overview

The Marketing Safety Gate enforces HARD_FAIL before any marketing send. It reads from the authoritative view and prevents all sends to ineligible companies.

> [!danger] DO NOT MODIFY
> This component is FROZEN at v1.0. Any modification requires formal Change Request.

---

## Enforcement Points

| Condition | Action | Recoverable |
|-----------|--------|-------------|
| effective_tier = -1 | HARD_FAIL | No |
| marketing_disabled = true | HARD_FAIL | No (until cleared) |
| has_active_override (blocking) | HARD_FAIL | No (until cleared) |
| DB error or missing data | HARD_FAIL | No (fail closed) |

---

## Data Source

```python
AUTHORITATIVE_VIEW = "outreach.vw_marketing_eligibility_with_overrides"
```

> [!warning] No Fallback
> The safety gate reads ONLY from the authoritative view. There is no fallback to underlying tables or views.

---

## Usage

```python
from hubs.outreach_execution.imo.middle.marketing_safety_gate import MarketingSafetyGate

gate = MarketingSafetyGate(db_connection)

try:
    result = gate.check_eligibility_or_fail(
        company_unique_id=company_id,
        campaign_id=campaign_id,
        correlation_id=correlation_id
    )

    if result.is_eligible:
        # Proceed with send
        perform_send(company_id, campaign_id)
    else:
        # Should not reach here - raises exception
        pass

except IneligibleTierError:
    # Company is tier -1
    log_blocked_send(company_id, "INELIGIBLE")

except MarketingDisabledError:
    # Kill switch active
    log_blocked_send(company_id, "MARKETING_DISABLED")
```

---

## Audit Logging

Every send attempt is logged to `outreach.send_attempt_audit`:

| Column | Description |
|--------|-------------|
| audit_id | Unique identifier |
| company_unique_id | Target company |
| campaign_id | Campaign identifier |
| correlation_id | Request correlation |
| computed_tier | Tier before overrides |
| effective_tier | Tier after overrides |
| was_blocked | Whether send was blocked |
| block_reason | Why send was blocked |
| attempt_timestamp | When attempt occurred |

> [!note] Append-Only
> The audit table is APPEND-ONLY. Updates and deletes are blocked by triggers.

---

## Error Types

### IneligibleTierError
Raised when effective_tier = -1.

### MarketingDisabledError
Raised when marketing_disabled = true.

### BlockingOverrideError
Raised when blocking override is active.

### EligibilityCheckFailedError
Raised on DB error or missing data. System fails CLOSED.

---

## Integration

The safety gate is integrated into OutreachHub:

```python
class OutreachHub:
    def execute_send(self, company_id, campaign_id, template_id):
        # Safety gate check FIRST
        result = self.safety_gate.check_eligibility_or_fail(
            company_id, campaign_id, self.correlation_id
        )

        # Only proceed if eligible
        return self._perform_send(company_id, template_id)
```

---

## Related Documents

- [[V1 Operational Baseline]]
- [[Kill Switch System]]
- [[Sovereign Completion Overview]]
- ADR-010: Marketing Safety Gate

---

## References

- `hubs/outreach-execution/imo/middle/marketing_safety_gate.py`
- `infra/migrations/2026-01-20-send-attempt-audit.sql`
- `infra/migrations/2026-01-19-kill-switches.sql`

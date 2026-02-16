# ADR-010: Marketing Safety Gate with HARD_FAIL Enforcement

## Status
**ACCEPTED**

## Date
2026-01-20

## Context

Before any marketing outreach can be sent, we must ensure the target company is eligible. This requires enforcement at the data layer, not just the UI layer, to prevent any bypass.

### Problem Statement

1. **Ineligible sends are unacceptable** - Sending to tier -1 companies must be prevented
2. **Kill switches must work** - Manual overrides must take effect immediately
3. **Audit trail required** - Every send attempt must be logged for compliance
4. **No fallback logic** - System must fail closed, not open

### Requirements

- HARD_FAIL if `effective_tier = -1`
- HARD_FAIL if `marketing_disabled = true`
- HARD_FAIL if any blocking override active
- Read from `vw_marketing_eligibility_with_overrides` ONLY
- Append-only audit logging

## Decision

### 1. Implement MarketingSafetyGate Class

Location: `hubs/outreach-execution/imo/middle/marketing_safety_gate.py`

```python
class MarketingSafetyGate:
    AUTHORITATIVE_VIEW = "outreach.vw_marketing_eligibility_with_overrides"

    def check_eligibility_or_fail(self, company_unique_id, campaign_id, correlation_id):
        # HARD_FAIL if ineligible
        # Log to send_attempt_audit
        # Return EligibilityResult or raise MarketingSafetyError
```

### 2. HARD_FAIL Error Types

| Error | Trigger | Recoverable |
|-------|---------|-------------|
| `IneligibleTierError` | effective_tier = -1 | No |
| `MarketingDisabledError` | marketing_disabled = true | No (until cleared) |
| `BlockingOverrideError` | Active blocking override | No (until cleared) |
| `EligibilityCheckFailedError` | DB error or missing data | No (fail closed) |

### 3. Create Append-Only Audit Table

Location: `migrations/2026-01-20-send-attempt-audit.sql`

Table: `outreach.send_attempt_audit`
- Logs every send attempt (allowed or blocked)
- Captures full eligibility snapshot at time of attempt
- Protected by triggers preventing UPDATE/DELETE

### 4. Integration with OutreachHub

```python
class OutreachHub:
    def execute_send(self, company_id, campaign_id, template_id):
        # Safety gate check FIRST
        result = self.safety_gate.check_eligibility_or_fail(company_id, ...)

        if not result.is_eligible:
            raise result.to_exception()  # HARD_FAIL

        # Only proceed if eligible
        return self._perform_send(...)
```

### 5. No Fallback Logic

Removed all fallback patterns:
- No `try/except` swallowing eligibility errors
- No default-to-eligible on missing data
- No bypass for "urgent" campaigns
- System fails CLOSED, not open

## Consequences

### Positive
- Zero risk of ineligible sends
- Kill switches work immediately
- Complete audit trail for compliance
- Fail-closed design prevents accidents

### Negative
- Legitimate sends blocked if data issues occur
- Requires operational monitoring for false positives

### Risks Mitigated
- Sending to opted-out customers
- Violating marketing regulations
- Legal liability from unauthorized contact
- Audit failures

## Alternatives Considered

### Alternative 1: UI-Only Enforcement
- Pro: Simpler implementation
- Con: Can be bypassed by direct API calls
- **Rejected**: Unacceptable security risk

### Alternative 2: Soft Warnings
- Pro: More flexible
- Con: Warnings can be ignored
- **Rejected**: Must be HARD_FAIL

### Alternative 3: Best-Effort Logging
- Pro: Less overhead
- Con: Incomplete audit trail
- **Rejected**: Compliance requires complete logging

## References

- `hubs/outreach-execution/imo/middle/marketing_safety_gate.py`
- `migrations/2026-01-20-send-attempt-audit.sql`
- `migrations/2026-01-19-kill-switches.sql`
- ADR-007: Kill Switch System

## Author
IMO-Creator: Outreach Execution Safety Auditor
Date: 2026-01-20

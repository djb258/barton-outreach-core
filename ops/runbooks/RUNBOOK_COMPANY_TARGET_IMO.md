# Company Target IMO — Operations Runbook

**Version**: 1.0
**Last Updated**: 2026-01-07
**Hub**: Company Target (04.04.01)
**Architecture**: Single-Pass IMO Gate

---

## What This Is

Company Target is a **single-pass IMO gate** that determines whether Outreach execution is possible for a given `outreach_id`.

- **It is NOT** an identity authority
- **It is NOT** a matching system
- **It is NOT** a retry queue

It derives email methodology via MX/SMTP checks and routes to PASS or terminal FAIL.

---

## Inputs

| Field | Type | Source | Required |
|-------|------|--------|----------|
| `outreach_id` | UUID | Outreach Spine | YES |
| `domain` | string | Spine record | YES |

The IMO loads these from `outreach.outreach` spine. It does NOT access CL tables.

---

## Outcomes

| Outcome | Table | Status | Downstream |
|---------|-------|--------|------------|
| **PASS** | `outreach.company_target` | `execution_status = 'ready'` | Proceeds to DOL, People, Blog |
| **FAIL** | `outreach.company_target_errors` | Terminal | BLOCKED — no downstream |

---

## Common Failure Codes

| Code | Stage | Meaning | Ops Action |
|------|-------|---------|------------|
| `CT-I-NOT-FOUND` | Input | `outreach_id` not in spine | Check spine ingestion |
| `CT-I-NO-DOMAIN` | Input | No domain in spine record | Check data quality upstream |
| `CT-I-ALREADY-PROCESSED` | Input | Already PASS/FAIL | No action (idempotent) |
| `CT-M-NO-MX` | Middle | No MX records for domain | Domain has no mail server |
| `CT-M-NO-PATTERN` | Middle | All SMTP patterns rejected | No discoverable email format |
| `CT-M-SMTP-FAIL` | Middle | SMTP connection failure | Transient network issue |
| `CT-M-VERIFY-FAIL` | Middle | Tier-2 verification failed | Email pattern invalid |

---

## What Ops CAN Do

1. **Inspect error reason** in `outreach.company_target_errors`
2. **Query failure distribution** to identify systemic issues
3. **Escalate data quality issues** to upstream (CL, intake)
4. **Decide manual override** (requires ADR + approval)
5. **Monitor metrics** (pass rate, fail rate, runtime)

---

## What Ops Must NOT Do

| Forbidden Action | Why |
|------------------|-----|
| Retry failed jobs | FAIL is terminal by design |
| Patch domains manually | Data quality is upstream's job |
| Add logic without ADR | Company Target is frozen |
| Access CL tables directly | Spine hides CL from sub-hubs |
| Bypass IMO gate | All records must go through IMO |

---

## Queries

### View Recent Failures

```sql
SELECT outreach_id, failure_code, blocking_reason, created_at
FROM outreach.company_target_errors
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC
LIMIT 100;
```

### Failure Distribution

```sql
SELECT failure_code, COUNT(*) as count
FROM outreach.company_target_errors
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY failure_code
ORDER BY count DESC;
```

### Pass Rate (Last 24h)

```sql
SELECT
  COUNT(*) FILTER (WHERE execution_status = 'ready') as passed,
  COUNT(*) FILTER (WHERE execution_status = 'failed') as failed,
  ROUND(100.0 * COUNT(*) FILTER (WHERE execution_status = 'ready') / COUNT(*), 2) as pass_rate
FROM outreach.company_target
WHERE imo_completed_at > NOW() - INTERVAL '24 hours';
```

---

## Escalation Path

| Issue | Escalate To |
|-------|-------------|
| High NO-MX rate | Data Quality team (domain validation) |
| High NO-PATTERN rate | Review email pattern list |
| SMTP timeouts | Infrastructure (network/DNS) |
| Unexpected failures | Engineering (check logs) |

---

## Tools Used

| Tool | Tool ID | Tier | Purpose |
|------|---------|------|---------|
| MXLookup | TOOL-004 | 0 (FREE) | DNS MX record check |
| SMTPCheck | TOOL-005 | 0 (FREE) | SMTP RCPT TO validation |
| EmailVerifier | TOOL-019 | 2 (GATED) | Optional Tier-2 verification |

See `ops/tooling/SNAP_ON_TOOLBOX.yaml` for throttle limits and guardrails.

---

## Change Control

Company Target is **frozen**.

Any modification requires:
1. New ADR
2. PRD version bump
3. CI guard updates
4. Ops runbook update

**No exceptions.**

---

## References

- **PRD**: `docs/prd/PRD_COMPANY_HUB.md` (v3.0)
- **ADR**: `docs/adr/ADR-CT-IMO-001.md`
- **Code**: `hubs/company-target/imo/middle/company_target_imo.py`
- **CI Guard**: `.github/workflows/company_target_imo_guard.yml`
- **Tool Registry**: `ops/tooling/SNAP_ON_TOOLBOX.yaml`

---

**Runbook Owner**: Ops Team
**Last Reviewed**: 2026-01-07

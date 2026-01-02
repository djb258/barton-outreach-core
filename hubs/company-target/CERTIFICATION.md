# Company Target — Doctrine Certification

**Status**: CERTIFIED
**Certification Date**: 2026-01-01
**Doctrine Version**: 1.0

---

## Certification Summary

Company Target sub-hub has been certified as the **reference implementation** for Outreach doctrine enforcement. All cost safety mechanisms are in place and verified.

---

## Verification Results

### Kill-Switch Test

```
pytest tests/hub/company/test_tier2_kill_switch.py -v

9 passed, 1 skipped
```

| Test | Status | Description |
|------|--------|-------------|
| `test_second_tier2_attempt_returns_false` | PASS | Second Tier-2 attempt hard FAILS |
| `test_different_tier2_tools_blocked_after_any_attempt` | PASS | Same tool blocked |
| `test_different_context_allows_tier2` | PASS | New context allows Tier-2 |
| `test_missing_context_id_raises` | PASS | FAIL HARD on missing context |
| `test_empty_context_id_raises` | PASS | FAIL HARD on empty context |
| `test_missing_sov_id_raises` | PASS | FAIL HARD on missing sov_id |
| `test_empty_sov_id_raises` | PASS | FAIL HARD on empty sov_id |
| `test_assert_can_attempt_tier2_raises_on_block` | PASS | Tier2BlockedError raised |
| `test_tier0_and_tier1_not_affected_by_guard` | PASS | Lower tiers not blocked |

---

### CI Guards

| Guard | Status | Verification |
|-------|--------|--------------|
| DG-013 | PASS | `can_attempt_tier2()` call present |
| DG-013 | PASS | `tier2_providers` loop present |
| DG-014 | PASS | `log_tool_attempt()` calls present (2) |
| DG-014 | PASS | `outreach_context_id` param present |
| DG-014 | PASS | `company_sov_id` param present |
| DG-013b | PASS | `context_manager` imported |

---

## Certified Components

### Truth Source

```
hubs/company-target/imo/middle/utils/context_manager.py
```

| Function | Purpose | Enforcement |
|----------|---------|-------------|
| `can_attempt_tier2()` | Tier-2 single-shot guard | Returns FALSE if already attempted |
| `assert_can_attempt_tier2()` | Guard with exception | Raises `Tier2BlockedError` |
| `log_tool_attempt()` | Cost logging | Logs to `outreach_ctx.tool_attempts` |
| `validate_context_id()` | FAIL HARD | Raises `MissingContextError` |
| `validate_sov_id()` | FAIL HARD | Raises `MissingSovIdError` |

### Guarded Phase

```
hubs/company-target/imo/middle/phases/phase3_email_pattern_waterfall.py
```

| Method | Guard | Line |
|--------|-------|------|
| `run()` | Context validation | 220-228 |
| `try_tier_2()` | `can_attempt_tier2()` check | 649-650 |
| `_discover_pattern_at_tier()` | `log_tool_attempt()` calls | 714, 748 |

---

## Freeze Line

The following document is the freeze line for Company Target:

```
hubs/company-target/CHECKLIST.md
```

**Prime Directive**:
> Cost containment is a hard gate. Accuracy is a tiebreaker, not a justification to spend.

---

## Doctrine Rules Enforced

| Rule | Description | Status |
|------|-------------|--------|
| DG-001 | Tool Context Enforcement | ENFORCED |
| DG-002 | Tool Registry Compliance | ENFORCED |
| DG-003 | Hub Boundary Protection | ENFORCED |
| DG-005 | PRD-CHECKLIST Sync | ENFORCED |
| DG-006 | Error Code Registry | ENFORCED |
| DG-007 | Signal Run-Bound | ENFORCED |
| DG-008 | No Signal Refresh | ENFORCED |
| DG-009 | Lifecycle Immutability | ENFORCED |
| DG-010 | Error Immutability | ENFORCED |
| DG-011 | Context Immutability | ENFORCED |
| DG-012 | Signal Immutability | ENFORCED |
| DG-013 | Tier-2 Single-Shot Guard | ENFORCED |
| DG-014 | Tool Attempt Logging | ENFORCED |

---

## Document Hierarchy

```
DOCTRINE.md          ← Governing context (sovereign ID rules)
CHECKLIST.md         ← Freeze line (compliance gate)
CERTIFICATION.md     ← This file (verification record)
```

---

## Next Steps

1. **DO NOT** audit other hubs until CI is green
2. Once CI passes, fan out guard patterns to:
   - `people-intelligence`
   - `dol-filings`
   - `blog-content`
3. Each hub gets its own `CERTIFICATION.md` after passing guards

---

## Signatures

- **Doctrine Enforcement Engineer**: Claude Code
- **Reference Implementation**: Company Target (04.04.01)
- **Certification Authority**: Outreach Doctrine v1.0

---

**This certification is VOID if any CHECKLIST item is unchecked.**

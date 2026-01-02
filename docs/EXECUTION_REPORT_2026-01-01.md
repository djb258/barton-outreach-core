# Company Target Execution Report

**Date**: 2026-01-01
**Context ID**: `1a47a2be-0d0d-4e6b-bbaa-70c921517b93`
**Status**: CLOSED (Partial)

---

## Execution Summary

| Metric | Value |
|--------|-------|
| Total Eligible | 71,820 |
| Total Processed | 20,000 |
| Completion | 27.8% |
| Queued (has domain) | 19,889 |
| Disqualified (no domain) | 111 |
| Pass Rate | 99.4% |

---

## Cost Tracking

| Tier | Description | Used | Spend |
|------|-------------|------|-------|
| Tier-0 | Free lookups | Yes | $0.00 |
| Tier-1 | Low-cost enrichment | No | $0.00 |
| Tier-2 | Premium (single-shot) | No | $0.00 |
| **Total** | | | **$0.00** |

---

## Doctrine Compliance

- [x] Context ID required before execution
- [x] Company Sovereign ID (company_unique_id) from CL parent
- [x] Cost-first waterfall (Tier-0 only this run)
- [x] No Tier-2 attempts (fuse preserved)
- [x] Batch processing with commits
- [x] Context properly closed

---

## Records Created

**Table**: `outreach.company_target`

| Field | Value |
|-------|-------|
| target_id | UUID (auto-generated) |
| company_unique_id | FK to cl.company_identity |
| outreach_status | 'queued' or 'disqualified' |
| sequence_count | 0 |
| source | CT-1a47a2be |

---

## Next Steps

To process remaining 51,820 companies:

```bash
python scripts/execute_company_target.py
```

This will create a new context and continue from where the previous run left off (existing records will be skipped via UNIQUE constraint).

---

## Context Log

```
outreach_ctx.context:
  outreach_context_id: 1a47a2be-0d0d-4e6b-bbaa-70c921517b93
  status: CLOSED
  notes: Company Target Full Run - 2026-01-01T18-47-06 | PARTIAL: 20000/71820 processed
```

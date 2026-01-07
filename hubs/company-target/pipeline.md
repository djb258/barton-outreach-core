# Company Target — IMO Pipeline Definition (v3.0)

> **DOCTRINE LOCK**: This document describes the Company Target IMO gate.
> Phase 1-4 are DEPRECATED. See `ADR-CT-IMO-001.md` for details.

## Overview

Company Target is a **single-pass IMO gate** that determines email methodology for outreach-ready companies.

**Key Principle**: Company Target receives `outreach_id` from the Outreach Spine. It NEVER sees `sovereign_id` directly and NEVER performs identity minting or fuzzy matching.

---

## IMO Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│                 COMPANY TARGET IMO GATE                      │
│                    (Single-Pass Execution)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ I — INPUT STAGE                                              │
│ ─────────────────────────────────────────────────────────── │
│ • Load record from outreach.outreach spine                  │
│ • Validate outreach_id exists                               │
│ • Load domain from spine record                             │
│ • Check idempotency (already PASS/FAIL?)                    │
│                                                              │
│ FAIL CONDITIONS:                                             │
│   • outreach_id not found → CT-I-NOT-FOUND → STOP           │
│   • domain missing → CT-I-NO-DOMAIN → STOP                  │
│   • already processed → exit (idempotent)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ M — MIDDLE STAGE                                             │
│ ─────────────────────────────────────────────────────────── │
│                                                              │
│ M1: MX Gate (TOOL-004: MXLookup)                            │
│   • DNS MX record lookup                                     │
│   • No MX → CT-M-NO-MX → STOP                               │
│                                                              │
│ M2: Pattern Generation                                       │
│   • Generate patterns in FIXED order:                        │
│     1. first.last@domain                                     │
│     2. firstlast@domain                                      │
│     3. f.last@domain                                         │
│     4. first.l@domain                                        │
│     5. first@domain                                          │
│     6. last@domain                                           │
│     7. info@domain                                           │
│     8. contact@domain                                        │
│                                                              │
│ M3: SMTP Validation (TOOL-005: SMTPCheck)                   │
│   • RCPT TO check for each pattern                          │
│   • Accept → PASS (stop)                                     │
│   • Reject → try next pattern                                │
│   • Catch-all → flag, use first.last                         │
│                                                              │
│ M4: Catch-All Handling                                       │
│   • If catch-all: confidence = 0.5, is_catchall = true      │
│   • Pattern: first.last@domain                               │
│                                                              │
│ M5: Optional Tier-1 Verification (GATED)                    │
│   • Only if Tier-0 inconclusive                              │
│   • Only if ALLOW_TIER1 = true                               │
│   • ONE attempt only (TOOL-019: EmailVerifier)              │
│   • Invalid → CT-M-VERIFY-FAIL → STOP                        │
│                                                              │
│ FAIL CONDITIONS:                                             │
│   • All patterns rejected → CT-M-NO-PATTERN → STOP          │
│   • SMTP failure → CT-M-SMTP-FAIL → STOP                    │
│   • Tier-1 verification failed → CT-M-VERIFY-FAIL → STOP    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ O — OUTPUT STAGE                                             │
│ ─────────────────────────────────────────────────────────── │
│                                                              │
│ PASS → Write to outreach.company_target:                     │
│   • execution_status = 'ready'                               │
│   • email_method = <discovered pattern>                      │
│   • method_type = 'SMTP_VERIFIED' | 'CATCHALL'              │
│   • confidence_score = 0.5 - 1.0                             │
│   • is_catchall = true | false                               │
│   • imo_completed_at = <timestamp>                           │
│                                                              │
│ FAIL → Write to outreach.company_target_errors:             │
│   • failure_code = CT-*-* error code                         │
│   • blocking_reason = <human readable>                       │
│   • imo_stage = I | M                                        │
│   • retry_allowed = FALSE (always)                           │
│   • Downstream execution BLOCKED                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Tool Registry (SNAP_ON_TOOLBOX.yaml)

| Tool | Tool ID | Tier | Stage | Gate |
|------|---------|------|-------|------|
| MXLookup | TOOL-004 | 0 (FREE) | M1 | None |
| SMTPCheck | TOOL-005 | 0 (FREE) | M3 | None |
| EmailVerifier | TOOL-019 | 2 (GATED) | M5 | ALLOW_TIER1 + no prior verification |

---

## Error Codes

| Code | Stage | Description |
|------|-------|-------------|
| `CT-I-NOT-FOUND` | I | outreach_id not in spine |
| `CT-I-NO-DOMAIN` | I | No domain in spine record |
| `CT-I-ALREADY-PROCESSED` | I | Already PASS or FAIL |
| `CT-M-NO-MX` | M | No MX records for domain |
| `CT-M-NO-PATTERN` | M | All patterns rejected |
| `CT-M-SMTP-FAIL` | M | SMTP connection failure |
| `CT-M-VERIFY-FAIL` | M | Tier-1 verification failed |

---

## Key Files

| Component | File |
|-----------|------|
| IMO Gate | `imo/middle/company_target_imo.py` |
| BIT Engine | `imo/middle/bit_engine.py` |

---

## DEPRECATED Files (DO NOT USE)

The following files have been deleted per ADR-CT-IMO-001:

| File | Status |
|------|--------|
| `imo/middle/phases/phase1_company_matching.py` | DELETED |
| `imo/middle/phases/phase1b_unmatched_hold_export.py` | DELETED |
| `imo/middle/utils/fuzzy.py` | DELETED |
| `imo/middle/utils/fuzzy_arbitration.py` | DELETED |

---

## Explicit Prohibitions

Company Target IMO does **NOT**:

| Forbidden Action | Reason |
|------------------|--------|
| Reference sovereign_id | Hidden by spine |
| Read from cl.* tables | Spine provides outreach_id only |
| Write to marketing.* tables | Only outreach.* writes allowed |
| Perform fuzzy matching | CL's responsibility |
| Mint any IDs | Spine mints outreach_id |
| Retry failed records | FAIL is terminal |
| Use hold queues | No rescue patterns |

---

**Last Updated**: 2026-01-07
**Architecture**: Single-Pass IMO Gate
**PRD Version**: 3.0

# Company Target — Pipeline Definition

## Overview

The Company Target pipeline determines outreach readiness for lifecycle-qualified companies.

---

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    COMPANY TARGET PIPELINE                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ GATE: Validate Lifecycle Permission                         │
│ ─────────────────────────────────────────────────────────── │
│ • Requires: company_sov_id (from Company Lifecycle)         │
│ • Requires: lifecycle_state >= ACTIVE                       │
│ • Requires: outreach_context_id                             │
│ • FAIL: If any requirement missing → STOP                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: Company Matching                                    │
│ ─────────────────────────────────────────────────────────── │
│ • Match incoming record to company_master                   │
│ • Hierarchy: GOLD (domain) → SILVER (exact) → BRONZE (fuzzy)│
│ • NO identity minting — match or fail                       │
│ • Output: company_match_result                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: Domain Resolution                                   │
│ ─────────────────────────────────────────────────────────── │
│ • Verify domain via DNS check                               │
│ • Verify domain via MX record check                         │
│ • NO external API calls — local checks only                 │
│ • Output: domain_result (RESOLVED / UNRESOLVED)             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: Email Pattern Waterfall                             │
│ ─────────────────────────────────────────────────────────── │
│ • TIER 0 (Free): Firecrawl, Google Places                   │
│   └─ No gate, unlimited calls                               │
│ • TIER 1 (Low Cost): Hunter, Clearbit, Apollo               │
│   └─ Gate: lifecycle >= ACTIVE                              │
│ • TIER 2 (Premium): Prospeo, Snov, Clay                     │
│   └─ Gate: lifecycle >= ACTIVE + BIT >= 25                  │
│   └─ LIMIT: ONE attempt per outreach_context                │
│ • Waterfall STOPS on first pattern found                    │
│ • All spend logged to outreach_ctx.spend_log                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Pattern Found?  │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
        ┌─────────┐                   ┌─────────┐
        │   YES   │                   │   NO    │
        └────┬────┘                   └────┬────┘
             │                              │
             ▼                              ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│ PHASE 4: Verification   │    │ Check BIT Threshold     │
│ ─────────────────────── │    │ ─────────────────────── │
│ • SMTP check            │    │ • BIT < 25 → STOP       │
│ • MX validation         │    │ • BIT >= 25 → Queue     │
│ • Format verification   │    │   for next context      │
│ • Output: verified      │    └─────────────────────────┘
│   pattern + confidence  │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│ OUTPUT: Emit Signals                                         │
│ ─────────────────────────────────────────────────────────── │
│ • Write to outreach.company_target                          │
│ • Emit BIT signals (PATTERN_FOUND, DOMAIN_VERIFIED)         │
│ • Log to spend_log with outreach_context_id                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Cost Rules

| Tier | Tools | Gate | Limit |
|------|-------|------|-------|
| 0 | Firecrawl, Google Places | None | Unlimited |
| 1 | Hunter, Clearbit, Apollo | lifecycle >= ACTIVE | Monitored |
| 2 | Prospeo, Snov, Clay | lifecycle >= ACTIVE + BIT >= 25 | **1 per context** |

---

## Key Files

| Phase | File |
|-------|------|
| Phase 1 | `imo/middle/phases/phase1_company_matching.py` |
| Phase 2 | `imo/middle/phases/phase2_domain_resolution.py` |
| Phase 3 | `imo/middle/phases/phase3_email_pattern_waterfall.py` |
| Phase 4 | `imo/middle/phases/phase4_pattern_verification.py` |
| BIT Engine | `imo/middle/bit_engine.py` |
| Pipeline | `imo/middle/company_pipeline.py` |
| Providers | `imo/middle/utils/providers.py` |

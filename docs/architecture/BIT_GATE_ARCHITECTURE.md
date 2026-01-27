# BIT (Buyer Intent Tool) Architecture
## Classification: GATE (Not a Hub)

> **DOCTRINE CLARIFICATION**: BIT is a scoring gate that lives INSIDE the Company Target hub.
> It is NOT a separate hub and does NOT gate completion. It gates marketing tier advancement.

## Position in Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      COMPLETION GATES                           │
│    (Hubs that must PASS for overall completion)                 │
├─────────────────────────────────────────────────────────────────┤
│  company-target → dol-filings → people-intelligence → talent-flow│
│       [04.04.01]    [04.04.03]      [04.04.02]        [04.04.06]│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MARKETING GATES                             │
│    (Thresholds that determine tier eligibility)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   BIT SCORE ≥ 25  →  "Intent Signal Present"                    │
│   BIT SCORE ≥ 50  →  "Strong Intent" (Tier 3 threshold)          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## What BIT Does

1. **Aggregates Signals** from all hubs:
   - Slot signals from People Hub
   - DOL signals from DOL Hub
   - Event signals from Blog Hub
   - Movement signals from Talent Flow Hub

2. **Computes a Score** (0-100):
   - Stored in `outreach.company_target.bit_score`
   - Updated whenever hub data changes

3. **Gates Tier Advancement**:
   - Does NOT gate completion (a company can be "complete" with BIT=0)
   - DOES gate Tier 3 (Aggressive) marketing eligibility

## What BIT Does NOT Do

- ❌ It is not a separate hub
- ❌ It does not appear in `hub_registry` as a hub
- ❌ It does not have its own `hub.manifest.yaml`
- ❌ Its score does NOT affect `overall_status` in completion view
- ❌ Failure to reach BIT threshold does NOT mark company as BLOCKED

## Code Location

BIT engine lives in:
```
hubs/company-target/imo/middle/bit_engine.py
```

This is correct - it's part of the Company Target hub's middle layer.

## Database Schema

```sql
-- BIT score lives ON the company_target table (not a separate table)
outreach.company_target.bit_score INTEGER DEFAULT 0

-- Signal log for audit trail
outreach.bit_signal_log (
    signal_id UUID,
    company_unique_id UUID,
    signal_type TEXT,
    signal_value JSONB,
    impact NUMERIC,
    created_at TIMESTAMPTZ
)
```

## Marketing Tier Logic

```sql
-- From vw_marketing_eligibility:
CASE
    -- Tier 3: ALL required hubs PASS + BIT >= 50
    WHEN overall_status = 'COMPLETE' AND bit_score >= 50 THEN 3
    
    -- Tier 2: Talent Flow PASS (regardless of BIT)
    WHEN talent_flow_status = 'PASS' THEN 2
    
    -- etc.
END AS marketing_tier
```

Note: BIT >= 50 is required for Tier 3, but it's an AND condition with completion, not an OR.

## Summary

| Aspect | BIT |
|--------|-----|
| Type | Scoring Gate |
| Lives In | Company Target Hub |
| Own Hub | No |
| Gates Completion | No |
| Gates Tier 3 | Yes |
| Score Range | 0-100 |
| Tier 3 Threshold | ≥50 |

# Messaging System Handoff

**Status**: COMPLETE
**Date**: 2026-02-07
**Author**: Claude Code

## Overview

This document describes the complete messaging handoff from the Barton Outreach Core system to downstream execution systems. The messaging system is responsible for generating outreach communications based on detected pressure signals.

## Three Audiences

Every message goes to exactly one of three audiences, each with different authorization requirements:

| Audience | Description | Band Required | Proof Required |
|----------|-------------|---------------|----------------|
| **CEO** | Chief Executive Officer | Band 3+ | Single-source |
| **CFO** | Chief Financial Officer | Band 3+ | Single-source |
| **HR** | Human Resources Decision Maker | Band 3+ | Single-source |

## Current Slot Status (2026-02-07)

| Slot Type | Filled | Total | Fill Rate |
|-----------|--------|-------|-----------|
| CEO | 62,289 | 95,004 | 65.6% |
| CFO | 57,327 | 95,004 | 60.3% |
| HR | 58,141 | 95,004 | 61.2% |
| **Total** | **177,757** | **285,012** | **62.4%** |

## Message Authorization Flow

```
BIT Score Calculation
         │
         ▼
┌────────────────────┐
│ Get Current Band   │
│ (0-5 scale)        │
└────────────────────┘
         │
         ▼
┌────────────────────┐
│ Band < 3?          │──► No outreach permitted
└────────────────────┘
         │ Band 3+
         ▼
┌────────────────────┐
│ Get Valid Proof    │
│ Line for Band      │
└────────────────────┘
         │
         ▼
┌────────────────────┐
│ Select Slot        │
│ (CEO/CFO/HR)       │
└────────────────────┘
         │
         ▼
┌────────────────────┐
│ Generate Message   │
│ with Proof Line    │
└────────────────────┘
         │
         ▼
┌────────────────────┐
│ Send via Execution │
│ Hub                │
└────────────────────┘
```

## Proof Line Requirements

### Band 3 (Targeted)
```
[PRESSURE_CLASS] detected via [SOURCE]: [SPECIFIC_EVIDENCE]
```

Example:
```
COST_PRESSURE detected via DOL: employer contribution +18% YoY, renewal in 75 days
```

### Band 4 (Engaged)
```
[PRESSURE_CLASS] convergence: [DOL_EVIDENCE] + [PEOPLE_EVIDENCE] + [BLOG_EVIDENCE if present]
```

### Band 5 (Direct)
```
PHASE TRANSITION: [PRESSURE_CLASS] — [DOL] + [PEOPLE] + [BLOG] — Decision window: [X] days
```

## Message Framing Rule

Lead with **system failure**, not product.

### WRONG (Product-first)
- "We offer better benefits plans..."
- "Our advisory services can help..."
- "I'd love to show you our platform..."

### RIGHT (Pressure-first)
- "Your employer contribution rose 18% last year while headcount stayed flat — that's a cost visibility gap we can close."
- "You've changed brokers twice in three years. That pattern usually means the underlying data infrastructure isn't transferring. We fix that layer."
- "Your new CHRO inherited a renewal in 75 days with no decision history. We build the continuity system that prevents this."

## Slot Selection Logic

```python
def select_slot(company_id: str, pressure_class: str) -> str:
    """
    Select the appropriate slot based on pressure class.

    Returns: 'CEO' | 'CFO' | 'HR'
    """
    # Pressure class → Primary slot mapping
    slot_map = {
        'COST_PRESSURE': 'CFO',           # Cost = CFO first
        'VENDOR_DISSATISFACTION': 'HR',   # Vendor = HR first
        'DEADLINE_PROXIMITY': 'HR',       # Deadline = HR first
        'ORGANIZATIONAL_RECONFIGURATION': 'CEO',  # Org change = CEO first
        'OPERATIONAL_CHAOS': 'CFO',       # Ops = CFO first
    }

    primary = slot_map.get(pressure_class, 'CEO')

    # Check if primary slot is filled
    if is_slot_filled(company_id, primary):
        return primary

    # Fallback waterfall: CEO → CFO → HR
    for slot in ['CEO', 'CFO', 'HR']:
        if is_slot_filled(company_id, slot):
            return slot

    return None  # No valid slot
```

## Data Dependencies

| Dependency | Source | Join Key |
|------------|--------|----------|
| Company Target | `outreach.company_target` | `outreach_id` |
| DOL Filing | `outreach.dol` | `outreach_id` |
| People Slot | `people.company_slot` | `outreach_id` |
| Person Details | `people.people_master` | `barton_id` |
| BIT Score | `outreach.bit_scores` | `outreach_id` |

## Execution Handoff

Once a message is authorized and generated, it is handed off to the Execution Hub:

1. **Message Record Created** in `execution.send_queue` (not yet implemented)
2. **Proof Line Attached** to message for audit
3. **Slot Person Linked** via `barton_id`
4. **Send Attempted** via configured channel (email)
5. **Result Logged** for engagement tracking

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Slot Fill | 62.4% complete | 177,757 / 285,012 filled |
| BIT Scoring | 13.9% coverage | 13,226 / 95,004 scored |
| Proof Generation | NOT YET | Requires BIT v2 Phase 2 |
| Message Templates | NOT YET | Post-proof implementation |
| Execution Hub | SCHEMA ONLY | `execution.*` tables need population |

## Next Steps

1. **Complete BIT v2 Phase 2** - Movement event ingestion
2. **Implement proof line generation** - Based on detected pressure
3. **Build message template system** - Per audience, per pressure class
4. **Connect to execution** - Email sending infrastructure

---

**Universal Join Key**: `outreach_id`
**Source of Truth**: `outreach.outreach` (95,004 records)

# Technical Architecture Specification: State Machines

**Repository**: barton-outreach-core
**Version**: 1.0.0
**Generated**: 2026-01-28
**Purpose**: Valid states and transitions for all entities — NO invalid transitions

---

## 1. Company Identity States (CL)

### identity_status

```
                    ┌──────────────┐
                    │   PENDING    │ ◄── Initial state
                    └──────┬───────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ RESOLVED │    │  FAILED  │    │ DUPLICATE│
    └──────────┘    └──────────┘    └──────────┘
           │               │
           │               └──────► Can retry → PENDING
           │
           └──────► Can be marked duplicate → DUPLICATE
```

| From State | To State | Trigger | Reversible |
|------------|----------|---------|------------|
| PENDING | RESOLVED | Identity verification pass | NO |
| PENDING | FAILED | Identity verification fail | YES (retry) |
| PENDING | DUPLICATE | Duplicate detected | NO |
| FAILED | PENDING | Manual retry trigger | YES |
| RESOLVED | DUPLICATE | Late duplicate detection | NO |

### eligibility_status

```
    ┌──────────────┐
    │     NULL     │ ◄── Not yet evaluated
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │   PENDING    │ ◄── Evaluation in progress
    └──────┬───────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌──────────┐ ┌──────────┐
│ ELIGIBLE │ │ EXCLUDED │
└────┬─────┘ └────┬─────┘
     │            │
     │            └──────► Can appeal → ELIGIBLE
     │
     └──────► Can be excluded → EXCLUDED
```

| From State | To State | Trigger | exclusion_reason |
|------------|----------|---------|------------------|
| NULL | PENDING | Eligibility check starts | - |
| PENDING | ELIGIBLE | All checks pass | NULL |
| PENDING | EXCLUDED | Any check fails | Set to failure reason |
| ELIGIBLE | EXCLUDED | Manual exclusion or rule change | MANUAL_EXCLUSION |
| EXCLUDED | ELIGIBLE | Appeal approved | NULL (cleared) |

---

## 2. Outreach Status States

### outreach_status (in outreach.company_target)

```
    ┌──────────────┐
    │    QUEUED    │ ◄── Initial state (waiting for processing)
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │    ACTIVE    │ ◄── Currently in outreach campaign
    └──────┬───────┘
           │
    ┌──────┼──────┬──────────┐
    │      │      │          │
    ▼      ▼      ▼          ▼
┌──────┐┌──────┐┌──────┐┌──────────┐
│PAUSED││FAILED││COMPLT││ EXCLUDED │
└──┬───┘└──────┘└──────┘└──────────┘
   │
   └──────► Can resume → ACTIVE
```

| From State | To State | Trigger | Notes |
|------------|----------|---------|-------|
| QUEUED | ACTIVE | Campaign starts | First sequence initiated |
| ACTIVE | PAUSED | Manual pause or kill switch | Can resume |
| ACTIVE | FAILED | Unrecoverable error | Check error tables |
| ACTIVE | COMPLETED | All sequences done | Final state |
| ACTIVE | EXCLUDED | Kill switch activated | Check manual_overrides |
| PAUSED | ACTIVE | Resume command | Continues from pause point |
| PAUSED | EXCLUDED | Kill switch while paused | Final state |

### execution_status (in outreach.company_target)

```
    ┌──────────────┐
    │   PENDING    │ ◄── Waiting for sub-hub execution
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │   RUNNING    │ ◄── Sub-hub currently executing
    └──────┬───────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌──────────┐ ┌──────────┐
│   DONE   │ │  FAILED  │
└──────────┘ └──────────┘
                  │
                  └──────► Can retry → PENDING
```

| From State | To State | Trigger |
|------------|----------|---------|
| PENDING | RUNNING | Sub-hub execution starts |
| RUNNING | DONE | Sub-hub completes successfully |
| RUNNING | FAILED | Sub-hub encounters error |
| FAILED | PENDING | Retry initiated |

---

## 3. Slot States

### is_filled (in people.company_slot)

```
    ┌──────────────┐
    │    FALSE     │ ◄── Slot exists but empty
    └──────┬───────┘
           │
           ▼ (person assigned)
    ┌──────────────┐
    │    TRUE      │ ◄── Slot has person assigned
    └──────┬───────┘
           │
           ▼ (person removed/left)
    ┌──────────────┐
    │    FALSE     │ ◄── Slot vacant again
    └──────────────┘
```

| Transition | Trigger | Logs To |
|------------|---------|---------|
| FALSE → TRUE | Person assigned to slot | slot_assignment_history |
| TRUE → FALSE | Person removed from company | slot_assignment_history |
| TRUE → TRUE | Person replaced | slot_assignment_history (2 entries) |

---

## 4. BIT Tier States

### bit_tier (in outreach.bit_scores)

```
    ┌──────────────┐
    │     NONE     │ ◄── Score < 20
    └──────┬───────┘
           │ score increases
           ▼
    ┌──────────────┐
    │    BRONZE    │ ◄── Score 20-39
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │    SILVER    │ ◄── Score 40-59
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │     GOLD     │ ◄── Score 60-79
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │   PLATINUM   │ ◄── Score 80-100
    └──────────────┘

NOTE: Tiers can move UP or DOWN based on score changes
```

| Tier | Score Range | Priority |
|------|-------------|----------|
| PLATINUM | 80-100 | Highest |
| GOLD | 60-79 | High |
| SILVER | 40-59 | Medium |
| BRONZE | 20-39 | Low |
| NONE | 0-19 | Lowest |

**Override**: `manual_overrides.override_type = 'TIER_FORCE'` bypasses score calculation

---

## 5. Campaign States

### campaign_status (in outreach.campaigns)

```
    ┌──────────────┐
    │    DRAFT     │ ◄── Campaign created but not started
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │   SCHEDULED  │ ◄── Scheduled for future start
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │    ACTIVE    │ ◄── Currently running
    └──────┬───────┘
           │
    ┌──────┼──────┐
    │      │      │
    ▼      ▼      ▼
┌──────┐┌──────┐┌──────────┐
│PAUSED││COMPLT││ CANCELLED│
└──┬───┘└──────┘└──────────┘
   │
   └──────► ACTIVE (resume)
```

| From State | To State | Trigger |
|------------|----------|---------|
| DRAFT | SCHEDULED | Start date set |
| DRAFT | ACTIVE | Immediate start |
| SCHEDULED | ACTIVE | Start date reached |
| ACTIVE | PAUSED | Manual pause |
| ACTIVE | COMPLETED | All sequences finished |
| ACTIVE | CANCELLED | Manual cancellation |
| PAUSED | ACTIVE | Resume |
| PAUSED | CANCELLED | Cancel while paused |

---

## 6. Sequence States

### sequence_status (in outreach.sequences)

```
    ┌──────────────┐
    │  SCHEDULED   │ ◄── Waiting for send time
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │   SENDING    │ ◄── Currently being sent
    └──────┬───────┘
           │
    ┌──────┼──────┐
    │      │      │
    ▼      ▼      ▼
┌──────┐┌──────┐┌──────────┐
│ SENT ││FAILED││ SKIPPED  │
└──────┘└──────┘└──────────┘
```

| From State | To State | Trigger |
|------------|----------|---------|
| SCHEDULED | SENDING | Send time reached |
| SENDING | SENT | Send confirmed |
| SENDING | FAILED | Send error |
| SCHEDULED | SKIPPED | Campaign cancelled or person excluded |
| FAILED | SCHEDULED | Retry scheduled |

---

## 7. Send Log States

### send_status (in outreach.send_log)

```
    ┌──────────────┐
    │  SCHEDULED   │ ◄── Queued for sending
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │    SENT      │ ◄── Sent to provider
    └──────┬───────┘
           │
    ┌──────┼──────┐
    │      │      │
    ▼      ▼      ▼
┌──────┐┌──────┐┌──────────┐
│DELIVD││BOUNCE││ DROPPED  │
└──┬───┘└──────┘└──────────┘
   │
   ▼
┌──────────────┐
│    OPENED    │ ◄── Recipient opened
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   CLICKED    │ ◄── Link clicked
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   REPLIED    │ ◄── Reply received
└──────────────┘
```

| State | Meaning | Next States |
|-------|---------|-------------|
| SCHEDULED | In send queue | SENT, DROPPED |
| SENT | Handed to provider | DELIVERED, BOUNCED |
| DELIVERED | In recipient inbox | OPENED |
| BOUNCED | Email bounced | - (terminal) |
| DROPPED | Not sent (excluded) | - (terminal) |
| OPENED | Email opened | CLICKED |
| CLICKED | Link clicked | REPLIED |
| REPLIED | Reply received | - (terminal success) |

---

## 8. Override States

### is_active (in outreach.manual_overrides)

```
    ┌──────────────┐
    │    TRUE      │ ◄── Override currently active
    └──────┬───────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌──────────┐ ┌──────────┐
│  FALSE   │ │  FALSE   │
│(expired) │ │(removed) │
└──────────┘ └──────────┘
```

| Transition | Trigger | Logged To |
|------------|---------|-----------|
| TRUE → FALSE | expires_at reached | override_audit_log |
| TRUE → FALSE | Manual deactivation | override_audit_log |

---

## State Transition SQL Examples

### Check Valid Transition

```sql
-- Before updating outreach_status, verify transition is valid
SELECT
    CASE
        WHEN current_status = 'queued' AND new_status IN ('active') THEN true
        WHEN current_status = 'active' AND new_status IN ('paused', 'failed', 'completed', 'excluded') THEN true
        WHEN current_status = 'paused' AND new_status IN ('active', 'excluded') THEN true
        ELSE false
    END as is_valid_transition
FROM (
    SELECT outreach_status as current_status, $new_status as new_status
    FROM outreach.company_target
    WHERE outreach_id = $oid
) t;
```

### Log State Change

```sql
-- Log slot assignment change
INSERT INTO people.slot_assignment_history
(history_id, slot_id, previous_person_id, new_person_id, change_reason, changed_at)
SELECT
    gen_random_uuid(),
    slot_id,
    person_unique_id,
    $new_person_id,
    $reason,
    NOW()
FROM people.company_slot
WHERE slot_id = $slot_id;

-- Then update
UPDATE people.company_slot
SET person_unique_id = $new_person_id, is_filled = true, filled_at = NOW()
WHERE slot_id = $slot_id;
```

---

## Quick Reference: Valid Transitions

| Entity | Column | Valid From → To |
|--------|--------|-----------------|
| CL | identity_status | PENDING→RESOLVED, PENDING→FAILED, FAILED→PENDING |
| CL | eligibility_status | NULL→PENDING, PENDING→ELIGIBLE, PENDING→EXCLUDED |
| Outreach | outreach_status | queued→active, active→paused/failed/completed |
| Outreach | execution_status | pending→running, running→done/failed |
| Slot | is_filled | false→true, true→false |
| BIT | bit_tier | Any tier can change based on score |
| Campaign | campaign_status | draft→scheduled/active, active→paused/completed |
| Sequence | sequence_status | scheduled→sending→sent/failed |
| Send | send_status | scheduled→sent→delivered→opened→clicked→replied |

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-28 |
| Version | 1.0.0 |
| Author | Claude Code (AI Employee) |

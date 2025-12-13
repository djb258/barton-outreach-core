# Funnel Movement Rules

## Version: 1.0.0
## Last Updated: 2025-12-05

---

## Overview

This document defines the concrete rules and thresholds that govern contact movement between funnels and lifecycle states. These rules are the operational implementation of the state machine defined in `funnel_state_machine.md`.

---

## Engagement Thresholds

### Email Open Threshold

```yaml
rule_id: RULE_OPENS_X3
trigger_event: EVENT_OPENS_X3
threshold: 3
measurement_window: 30 days
deduplication: unique opens only (1 per email per day max)
applies_to:
  - SUSPECT → WARM
conditions:
  - opens >= 3 within window
  - opens from unique email sends (not same email opened multiple times)
  - not bounced or unsubscribed
```

**Implementation Notes**:
- Count unique opens per email campaign
- Same email opened multiple times in one day = 1 open
- Opens must be from different email sends to count toward threshold
- Window resets if contact goes to REENGAGEMENT state

### Email Click Threshold

```yaml
rule_id: RULE_CLICKS_X2
trigger_event: EVENT_CLICKS_X2
threshold: 2
measurement_window: 30 days
deduplication: unique clicks only (1 per link per day max)
applies_to:
  - SUSPECT → WARM
conditions:
  - clicks >= 2 within window
  - clicks on distinct links preferred
  - not bounced or unsubscribed
```

**Implementation Notes**:
- Click on same link multiple times in one day = 1 click
- Clicks on tracking pixels do not count
- Unsubscribe link clicks do not count
- Calendar/meeting links have special handling (may trigger APPOINTMENT directly)

### Email Reply Detection

```yaml
rule_id: RULE_REPLY
trigger_event: EVENT_REPLY
threshold: 1
sentiment_filter: positive or neutral (not negative/unsubscribe)
applies_to:
  - SUSPECT → WARM (immediate)
  - REENGAGEMENT → WARM (immediate)
  - TALENTFLOW_WARM → TALENTFLOW_WARM (maintain)
conditions:
  - reply detected in inbox
  - reply sentiment != negative
  - reply is not auto-responder
  - reply is not OOO (out of office)
```

**Sentiment Classification**:

| Sentiment | Action | Example |
|-----------|--------|---------|
| Positive | Promote to WARM | "I'd love to learn more" |
| Neutral | Promote to WARM | "Can you send more info?" |
| Negative | Do not promote | "Not interested" |
| Unsubscribe | Exit system | "Remove me from your list" |
| OOO | Ignore (retry later) | "I'm out until Monday" |
| Auto-reply | Ignore | "This inbox is not monitored" |

---

## BIT Score Rules

### BIT Score Thresholds

```yaml
rule_id: RULE_BIT_THRESHOLD
trigger_event: EVENT_BIT_THRESHOLD
thresholds:
  WARM_THRESHOLD: 25
  HOT_THRESHOLD: 50
  PRIORITY_THRESHOLD: 75
applies_to:
  - SUSPECT → WARM (when score >= WARM_THRESHOLD)
```

### BIT Score Components

| Signal Type | Weight | Max Points | Description |
|-------------|--------|------------|-------------|
| Email Opens | 2 | 10 | 2 points per unique open, max 5 opens |
| Email Clicks | 5 | 15 | 5 points per click, max 3 clicks |
| Email Reply | 15 | 15 | One-time bonus for reply |
| Website Visit | 3 | 12 | 3 points per visit, max 4 visits |
| Content Download | 8 | 16 | 8 points per download, max 2 |
| Webinar Attendance | 10 | 10 | One-time bonus |
| TalentFlow Signal | 20 | 20 | One-time bonus for movement |
| Recency Decay | -1/day | -30 | Lose 1 point per day of inactivity |

### BIT Score Calculation

```
BIT_SCORE = SUM(signal_points) - recency_decay
WHERE recency_decay = days_since_last_engagement * 1 (max 30)
```

**Example**:
- 3 opens (6 pts) + 2 clicks (10 pts) + 1 reply (15 pts) = 31 points
- If last engagement was 5 days ago: 31 - 5 = 26 points
- 26 >= WARM_THRESHOLD (25): Contact promotes to WARM

---

## TalentFlow Rules

### TalentFlow Movement Detection

```yaml
rule_id: RULE_TALENTFLOW_MOVE
trigger_event: EVENT_TALENTFLOW_MOVE
movement_types:
  - job_change: New employer detected
  - promotion: Title change at same employer
  - lateral: Role change at same employer
  - startup: Joined early-stage company
freshness_window: 90 days
applies_to:
  - SUSPECT → TALENTFLOW_WARM
  - WARM → TALENTFLOW_WARM
  - REENGAGEMENT → TALENTFLOW_WARM
```

### TalentFlow Priority Scoring

| Movement Type | Priority | Sequence Speed | Description |
|---------------|----------|----------------|-------------|
| job_change | Highest | Accelerated (24h) | New employer = fresh start |
| startup | High | Accelerated (24h) | Early-stage = budget authority |
| promotion | Medium | Standard (48h) | New budget/authority |
| lateral | Low | Standard (72h) | Same org, different focus |

### TalentFlow Decay Rules

```yaml
rule_id: RULE_TALENTFLOW_DECAY
trigger: movement_age > 90 days
action:
  if engaged: Maintain TALENTFLOW_WARM
  if not_engaged: Demote to REENGAGEMENT or SUSPECT
```

---

## Re-Engagement Rules

### Inactivity Timer

```yaml
rule_id: RULE_INACTIVITY_30D
trigger_event: EVENT_INACTIVITY_30D
threshold: 30 days
measurement: days since last engagement event
applies_to:
  - WARM → REENGAGEMENT
  - TALENTFLOW_WARM → REENGAGEMENT
  - APPOINTMENT → REENGAGEMENT
engagement_events:
  - email_open
  - email_click
  - email_reply
  - website_visit
  - meeting_attended
```

### Re-Engagement Cycle Timer

```yaml
rule_id: RULE_REENGAGEMENT_TIMER
trigger_event: EVENT_REENGAGEMENT_TRIGGER
cycle_interval: 60-90 days (configurable)
max_cycles: 3
applies_to:
  - Re-engagement sequence initiation
```

**Cycle Behavior**:

| Cycle | Wait Period | Sequence Type | Content Strategy |
|-------|-------------|---------------|------------------|
| 1 | 60 days | Soft re-engage | "Checking back in" |
| 2 | 75 days | Value re-engage | New case study/content |
| 3 | 90 days | Final attempt | Direct value prop |

### Re-Engagement Exhaustion

```yaml
rule_id: RULE_REENGAGEMENT_EXHAUSTED
trigger_event: EVENT_REENGAGEMENT_EXHAUSTED
condition: cycle_count >= 3 AND no_response
action: Recycle to SUSPECT (Funnel 1)
cooldown_before_cold_outreach: 180 days
```

---

## Appointment Rules

### Meeting Scheduled

```yaml
rule_id: RULE_APPOINTMENT_BOOKED
trigger_event: EVENT_APPOINTMENT
detection_methods:
  - Calendar integration (Calendly, HubSpot, etc.)
  - Manual CRM entry
  - Reply containing meeting confirmation
applies_to:
  - WARM → APPOINTMENT
  - TALENTFLOW_WARM → APPOINTMENT
  - REENGAGEMENT → APPOINTMENT
```

### Meeting Follow-Up

```yaml
rule_id: RULE_MEETING_FOLLOWUP
conditions:
  meeting_completed:
    if contract_sent: Stay in APPOINTMENT
    if proposal_requested: Stay in APPOINTMENT
    if no_interest: Demote to REENGAGEMENT
  meeting_no_show:
    first_no_show: Reschedule attempt (stay APPOINTMENT)
    second_no_show: Demote to REENGAGEMENT
  meeting_cancelled:
    with_reschedule: Stay in APPOINTMENT
    without_reschedule: Demote to REENGAGEMENT after 7 days
```

### Client Conversion

```yaml
rule_id: RULE_CLIENT_SIGNED
trigger_event: EVENT_CLIENT_SIGNED
detection_methods:
  - CRM opportunity closed-won
  - Contract signature detected
  - Manual confirmation
applies_to:
  - APPOINTMENT → CLIENT (final state)
post_conversion:
  - Remove from outreach sequences
  - Add to customer success track
  - Update all related records
```

---

## Priority Resolution Rules

### Simultaneous Event Handling

When multiple events occur in the same processing window:

```yaml
rule_id: RULE_PRIORITY_RESOLUTION
priority_order:
  1: EVENT_CLIENT_SIGNED (highest)
  2: EVENT_APPOINTMENT
  3: EVENT_TALENTFLOW_MOVE
  4: EVENT_REPLY
  5: EVENT_BIT_THRESHOLD
  6: EVENT_CLICKS_X2
  7: EVENT_OPENS_X3
  8: EVENT_REENGAGEMENT_TRIGGER (lowest)
behavior:
  - Process highest priority event only
  - Log all events for audit trail
  - Lower priority events may trigger in next cycle
```

### State Lock Rules

```yaml
rule_id: RULE_STATE_LOCK
lock_conditions:
  - Manual review pending
  - Data quality issue flagged
  - Duplicate resolution in progress
  - Compliance hold
lock_behavior:
  - No state transitions allowed
  - Events are queued, not lost
  - Lock must be explicitly released
```

---

## Anti-Thrashing Rules

### Cooldown Period

```yaml
rule_id: RULE_COOLDOWN
minimum_time_between_transitions: 24 hours
exceptions:
  - APPOINTMENT transitions (no cooldown)
  - CLIENT transitions (no cooldown)
  - Manual override by admin
purpose: Prevent rapid state flickering from event bursts
```

### Direction Lock

```yaml
rule_id: RULE_DIRECTION_LOCK
behavior:
  after_promotion: Cannot demote within 7 days (except APPOINTMENT/CLIENT)
  after_demotion: Cannot promote within 3 days
  exception: High-priority events (TALENTFLOW, APPOINTMENT, CLIENT)
```

### Event Accumulation Window

```yaml
rule_id: RULE_EVENT_ACCUMULATION
window: 4 hours
behavior:
  - Collect all events within window
  - Process as batch at window close
  - Apply priority resolution
  - Execute single highest-priority transition
purpose: Allow engagement bursts to accumulate before state evaluation
```

---

## Validation Rules

### Pre-Transition Validation

Before any state transition executes:

```yaml
validation_checks:
  1. contact_exists: Contact record must exist
  2. current_state_valid: Contact is in expected current state
  3. event_valid_for_state: Event is allowed for current state
  4. threshold_met: Numeric thresholds are satisfied
  5. cooldown_expired: Minimum time since last transition
  6. not_locked: Contact is not in locked state
  7. not_terminal: Current state allows outbound transitions
```

### Post-Transition Actions

After successful state transition:

```yaml
post_transition_actions:
  1. update_lifecycle_state: Set new state in database
  2. update_funnel_membership: Assign to correct funnel
  3. update_sequence_assignment: Assign appropriate outreach sequence
  4. record_timestamp: Log transition time
  5. emit_event: Send webhook/notification
  6. log_audit_trail: Record in audit log
  7. update_bit_score: Recalculate if applicable
```

---

## Rule Exceptions

### Manual Override

```yaml
rule_id: RULE_MANUAL_OVERRIDE
authorized_roles:
  - admin
  - sales_manager
  - customer_success
allowed_overrides:
  - Force state transition
  - Skip cooldown period
  - Reset engagement counters
  - Bypass threshold requirements
audit_requirements:
  - Reason must be documented
  - Override logged with user ID
  - Cannot override CLIENT → any transition
```

### System Maintenance

```yaml
rule_id: RULE_SYSTEM_MAINTENANCE
during_maintenance:
  - Events are queued, not processed
  - No state transitions execute
  - Timers are paused
  - Re-engagement cycles suspended
post_maintenance:
  - Process queued events in order
  - Resume normal operation
  - Log maintenance window in audit
```

---

## Rule Configuration

### Configurable Parameters

| Parameter | Default | Min | Max | Description |
|-----------|---------|-----|-----|-------------|
| `OPENS_THRESHOLD` | 3 | 2 | 10 | Opens required for promotion |
| `CLICKS_THRESHOLD` | 2 | 1 | 5 | Clicks required for promotion |
| `WARM_BIT_THRESHOLD` | 25 | 10 | 50 | BIT score for WARM promotion |
| `INACTIVITY_DAYS` | 30 | 14 | 90 | Days before inactivity trigger |
| `REENGAGEMENT_INTERVAL` | 60 | 30 | 120 | Days between re-engagement cycles |
| `MAX_REENGAGEMENT_CYCLES` | 3 | 1 | 5 | Maximum re-engagement attempts |
| `TALENTFLOW_FRESHNESS` | 90 | 30 | 180 | Days TalentFlow signal is valid |
| `COOLDOWN_HOURS` | 24 | 1 | 72 | Hours between state changes |
| `EVENT_WINDOW_HOURS` | 4 | 1 | 24 | Hours to accumulate events |

### Environment-Specific Overrides

```yaml
development:
  COOLDOWN_HOURS: 0  # No cooldown for testing
  EVENT_WINDOW_HOURS: 0  # Immediate processing

staging:
  COOLDOWN_HOURS: 1
  EVENT_WINDOW_HOURS: 1

production:
  COOLDOWN_HOURS: 24
  EVENT_WINDOW_HOURS: 4
```

---

## Cross-References

- **Funnel Definitions**: See `4_funnel_doctrine.md`
- **State Machine**: See `funnel_state_machine.md`
- **BIT Scoring**: See `bit_scoring_doctrine.md` (future)
- **TalentFlow Detection**: See `talentflow_doctrine.md` (future)

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-05 | System | Initial rules creation |

# Movement Engine

## Overview

The Movement Engine is the core logic layer for the 4-Funnel GTM System. It handles:
- Event detection and classification
- State transition validation
- Threshold evaluation (opens, clicks, BIT scores)
- Reply sentiment analysis
- TalentFlow signal validation
- Re-engagement cycle management

## Architecture

```
movement_engine/
├── __init__.py           # Public API exports
├── state_machine.py      # FSM implementation
├── movement_rules.py     # Business rules and thresholds
├── movement_engine.py    # Main orchestrator
└── README.md            # This file
```

## Components

### StateMachine

Implements the finite state machine for lifecycle states.

```python
from movement_engine import StateMachine, LifecycleState, EventType

sm = StateMachine()

# Check if transition is valid
is_valid = sm.is_valid_transition(
    from_state=LifecycleState.SUSPECT,
    to_state=LifecycleState.WARM,
    event_type=EventType.EVENT_REPLY
)

# Get next state
next_state = sm.get_next_state(
    current_state=LifecycleState.SUSPECT,
    event_type=EventType.EVENT_REPLY
)  # Returns LifecycleState.WARM
```

**Lifecycle States:**
- `SUSPECT` - Cold contact (Funnel 1)
- `WARM` - Engaged contact (Funnel 3)
- `TALENTFLOW_WARM` - TalentFlow signal (Funnel 2)
- `REENGAGEMENT` - Re-engagement cycle (Funnel 4)
- `APPOINTMENT` - Meeting scheduled
- `CLIENT` - Contract signed (terminal)
- `DISQUALIFIED` - Hard bounce (terminal)
- `UNSUBSCRIBED` - Opted out (terminal)

**Event Types:**
- `EVENT_REPLY` - Email reply received
- `EVENT_OPENS_X3` - 3+ email opens
- `EVENT_CLICKS_X2` - 2+ link clicks
- `EVENT_BIT_THRESHOLD` - BIT score crossed threshold
- `EVENT_TALENTFLOW_MOVE` - Job movement detected
- `EVENT_APPOINTMENT` - Meeting booked
- `EVENT_CLIENT_SIGNED` - Contract signed
- `EVENT_INACTIVITY_30D` - 30+ days inactive
- `EVENT_REENGAGEMENT_EXHAUSTED` - Max cycles reached
- `EVENT_UNSUBSCRIBE` - Opted out
- `EVENT_HARD_BOUNCE` - Email bounced
- `EVENT_MANUAL_OVERRIDE` - Admin override

### MovementRules

Contains business rules for classifying engagement signals.

```python
from movement_engine import MovementRules, MovementRulesConfig

# Custom configuration
config = MovementRulesConfig(
    opens_threshold=3,
    clicks_threshold=2,
    bit_warm_threshold=25,
    inactivity_threshold_days=30,
    max_reengagement_cycles=3
)

rules = MovementRules(config)

# Classify a reply
result = rules.classify_reply("I'd love to learn more!")
print(result.sentiment)      # ReplySentiment.POSITIVE
print(result.should_promote) # True

# Check thresholds
opens_result = rules.check_open_threshold(3)
print(opens_result.threshold_met)  # True

# Calculate BIT score
bit_result = rules.calculate_bit_score(
    opens=3,
    clicks=2,
    replies=1,
    has_talentflow_signal=True
)
print(bit_result.total_score)           # 51
print(bit_result.crossed_warm_threshold) # True
```

**Reply Sentiment Classification:**
- `POSITIVE` - Interest signals ("interested", "let's talk")
- `NEUTRAL` - No clear sentiment (still promotes)
- `NEGATIVE` - Rejection signals ("not interested")
- `UNSUBSCRIBE` - Opt-out request
- `OUT_OF_OFFICE` - OOO auto-reply
- `AUTO_REPLY` - System auto-reply

**Configurable Thresholds:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `opens_threshold` | 3 | Opens for promotion |
| `clicks_threshold` | 2 | Clicks for promotion |
| `bit_warm_threshold` | 25 | BIT score for WARM |
| `bit_hot_threshold` | 50 | BIT score for HOT |
| `bit_priority_threshold` | 75 | BIT score for PRIORITY |
| `inactivity_threshold_days` | 30 | Days before inactivity trigger |
| `max_reengagement_cycles` | 3 | Max re-engagement attempts |
| `reengagement_interval_days` | 60 | Days between cycles |
| `cooldown_hours` | 24 | Hours between transitions |
| `talentflow_freshness_days` | 90 | TalentFlow signal validity |

### MovementEngine

Main orchestrator that combines StateMachine and MovementRules.

```python
from movement_engine import MovementEngine, ContactState, LifecycleState, FunnelMembership

engine = MovementEngine()

# Detect an event
event = engine.detect_event(
    company_id="uuid-123",
    person_id="uuid-456",
    event_type="email_reply",
    metadata={"reply_text": "I'm interested!"}
)

# Create contact state (placeholder - would come from DB)
contact = ContactState(
    company_id="uuid-123",
    person_id="uuid-456",
    email="test@example.com",
    current_state=LifecycleState.SUSPECT,
    funnel_membership=FunnelMembership.COLD_UNIVERSE
)

# Evaluate transition
decision = engine.evaluate_transition(contact, event)
print(decision.should_transition)  # True
print(decision.to_state)           # LifecycleState.WARM

# Record transition (placeholder)
if decision.should_transition:
    record = engine.record_transition(decision)
```

## Event Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     EVENT PROCESSING FLOW                        │
└─────────────────────────────────────────────────────────────────┘

1. Event Detection
   ├── Raw event received (email_reply, email_open, etc.)
   ├── Map to EventType enum
   ├── Generate dedup hash
   └── Add to pending queue

2. Transition Evaluation
   ├── Check contact lock status
   ├── Check cooldown period
   ├── Validate event thresholds
   │   ├── Opens: count >= 3?
   │   ├── Clicks: count >= 2?
   │   ├── BIT: score >= 25?
   │   ├── Reply: sentiment positive/neutral?
   │   └── TalentFlow: signal fresh (<90 days)?
   └── Evaluate state machine transition

3. Priority Resolution (batch processing)
   ├── Collect all pending events for contact
   ├── Evaluate each event
   ├── Sort by priority
   └── Execute highest priority transition only

4. Transition Recording (placeholder)
   ├── Create TransitionRecord
   ├── Store in memory (DB write in future)
   └── Clear processed events
```

## Event Priority Order

When multiple events occur simultaneously:

| Priority | Event | Description |
|----------|-------|-------------|
| 100 | `EVENT_CLIENT_SIGNED` | Contract signed |
| 100 | `EVENT_MANUAL_OVERRIDE` | Admin override |
| 95 | `EVENT_UNSUBSCRIBE` | Compliance |
| 95 | `EVENT_HARD_BOUNCE` | Deliverability |
| 90 | `EVENT_APPOINTMENT` | Meeting booked |
| 80 | `EVENT_TALENTFLOW_MOVE` | Job movement |
| 70 | `EVENT_REPLY` | Email reply |
| 60 | `EVENT_BIT_THRESHOLD` | BIT score |
| 50 | `EVENT_CLICKS_X2` | Link clicks |
| 40 | `EVENT_OPENS_X3` | Email opens |

## Transition Table

| From State | Event | To State |
|------------|-------|----------|
| SUSPECT | EVENT_REPLY | WARM |
| SUSPECT | EVENT_OPENS_X3 | WARM |
| SUSPECT | EVENT_CLICKS_X2 | WARM |
| SUSPECT | EVENT_BIT_THRESHOLD | WARM |
| SUSPECT | EVENT_TALENTFLOW_MOVE | TALENTFLOW_WARM |
| WARM | EVENT_APPOINTMENT | APPOINTMENT |
| WARM | EVENT_TALENTFLOW_MOVE | TALENTFLOW_WARM |
| WARM | EVENT_INACTIVITY_30D | REENGAGEMENT |
| TALENTFLOW_WARM | EVENT_APPOINTMENT | APPOINTMENT |
| TALENTFLOW_WARM | EVENT_INACTIVITY_30D | REENGAGEMENT |
| REENGAGEMENT | EVENT_REPLY | WARM |
| REENGAGEMENT | EVENT_TALENTFLOW_MOVE | TALENTFLOW_WARM |
| REENGAGEMENT | EVENT_APPOINTMENT | APPOINTMENT |
| REENGAGEMENT | EVENT_REENGAGEMENT_EXHAUSTED | SUSPECT |
| APPOINTMENT | EVENT_CLIENT_SIGNED | CLIENT |
| APPOINTMENT | EVENT_INACTIVITY_30D | REENGAGEMENT |

## Cooldown Rules

- **Default:** 24 hours between state transitions
- **Bypass allowed for:**
  - `EVENT_APPOINTMENT`
  - `EVENT_CLIENT_SIGNED`
  - `EVENT_UNSUBSCRIBE`
  - `EVENT_HARD_BOUNCE`

## Integration Notes

**Current Status:** Pipeline-integrated (Prompt 4)

**No database integration yet:**
- Contact state is passed in (not loaded from DB)
- Transitions are stored in memory (not persisted)
- Events are queued in memory (not deduplicated against DB)

**Pipeline Integration (Prompt 4):**
- MovementEngine initialized in `pipeline_engine/main.py`
- Hook methods available on `CompanyIdentityPipeline`:
  - `hook_movement_reply(company_id, person_id, reply_text, metadata)`
  - `hook_movement_warm_engagement(company_id, person_id, opens, clicks, bit_score, metadata)`
  - `hook_movement_talentflow(company_id, person_id, signal_type, new_company, metadata)`
  - `hook_movement_appointment(company_id, person_id, appointment_type, metadata)`
- TalentFlowCompanyGate accepts optional `movement_hook` callback
- Movement event types added to `utils/logging.py`

**Future integration (Prompt 5+):**
- Load contact state from `funnel.suspect_universe`
- Write events to `funnel.engagement_events`
- Write transitions to `funnel.prospect_movement`

## Pipeline Hook Usage

```python
from pipeline_engine.main import CompanyIdentityPipeline

# Initialize pipeline (includes MovementEngine)
pipeline = CompanyIdentityPipeline(config={})

# Call hooks from external systems
# When email reply is received:
pipeline.hook_movement_reply(
    company_id="uuid-123",
    person_id="uuid-456",
    reply_text="I'm interested in learning more",
    metadata={"email_id": "msg-789"}
)

# When engagement thresholds crossed:
pipeline.hook_movement_warm_engagement(
    company_id="uuid-123",
    person_id="uuid-456",
    opens=3,
    clicks=2,
    bit_score=35
)

# When TalentFlow detects movement:
pipeline.hook_movement_talentflow(
    company_id="uuid-123",
    person_id="uuid-456",
    signal_type="job_change",
    new_company="Acme Corp"
)

# When appointment is booked:
pipeline.hook_movement_appointment(
    company_id="uuid-123",
    person_id="uuid-456",
    appointment_type="discovery_call"
)
```

## TalentFlow Integration

```python
from pipeline_engine.phases.talentflow_phase0_company_gate import TalentFlowCompanyGate

# Create gate with movement hook
def my_movement_hook(company_id, person_id, signal_type, new_company, metadata):
    print(f"Movement detected: {signal_type} for {person_id}")

gate = TalentFlowCompanyGate(
    config={},
    movement_hook=my_movement_hook
)

# Process movement event
result = gate.run(
    new_company_name="Acme Corp",
    company_df=company_master_df,
    person_id="uuid-456",
    signal_type="job_change",
    metadata={"source": "linkedin"}
)
```

## Related Documentation

- **Doctrine:** `ctb/sys/doctrine/4_funnel_doctrine.md`
- **State Machine:** `ctb/sys/doctrine/funnel_state_machine.md`
- **Rules:** `ctb/sys/doctrine/funnel_rules.md`
- **Schema:** `neon/migrations/README.md`

## Version

- **Version:** 1.0.0
- **Created:** 2025-12-05

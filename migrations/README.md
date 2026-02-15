# 4-Funnel GTM System - Neon Migrations

## Overview

These SQL migrations create the database schema for the 4-Funnel GTM (Go-To-Market) System.

## Migration Files

Run migrations in numerical order:

| Migration | Description |
|-----------|-------------|
| `0001_create_funnel_schema.sql` | Create `funnel` schema and ENUM types |
| `0002_create_suspect_universe.sql` | Primary contact lifecycle table (Funnel 1: Cold) |
| `0003_create_engagement_events.sql` | Engagement event log (opens, clicks, replies) |
| `0004_create_warm_universe.sql` | Warm contact tracking (Funnel 3: Engaged) |
| `0005_create_talentflow_signal_log.sql` | TalentFlow movement signals (Funnel 2) |
| `0006_create_bit_signal_log.sql` | BIT score tracking and thresholds |
| `0007_create_prospect_movement.sql` | State transition audit log |
| `0008_create_appointment_history.sql` | Sales pipeline meeting tracking |
| `0009_create_client_conversion.sql` | Client conversion records (Final state) |
| `0010_create_funnel_functions.sql` | Helper functions and utilities |

## Running Migrations

### Manual Execution

```bash
# Connect to Neon
psql postgresql://Marketing_DB_owner:<password>@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing_DB?sslmode=require

# Run each migration in order
\i neon/migrations/0001_create_funnel_schema.sql
\i neon/migrations/0002_create_suspect_universe.sql
# ... continue through 0010
```

### All-in-One Script

```bash
# Run all migrations
for f in neon/migrations/00*.sql; do
    echo "Running $f..."
    psql $NEON_CONNECTION_STRING -f "$f"
done
```

## Schema Overview

```
funnel.
├── suspect_universe         # Primary contact table
├── engagement_events        # Event log (immutable)
├── warm_universe           # Warm contacts
├── talentflow_signal_log   # TalentFlow signals
├── bit_signal_log          # BIT scores
├── prospect_movement       # State transitions (audit)
├── appointment_history     # Meetings
└── client_conversion       # Won deals
```

## ENUM Types

### lifecycle_state
- `SUSPECT` - New contact, no engagement
- `WARM` - Engaged via email signals
- `TALENTFLOW_WARM` - TalentFlow signal + engagement
- `REENGAGEMENT` - Past engagement, needs re-activation
- `APPOINTMENT` - Meeting scheduled
- `CLIENT` - Contract signed
- `DISQUALIFIED` - Permanently removed
- `UNSUBSCRIBED` - Opted out

### event_type
- `EVENT_REPLY` - Email reply received
- `EVENT_CLICKS_X2` - 2+ link clicks
- `EVENT_OPENS_X3` - 3+ email opens
- `EVENT_TALENTFLOW_MOVE` - Job movement detected
- `EVENT_BIT_THRESHOLD` - BIT score crossed threshold
- `EVENT_REENGAGEMENT_TRIGGER` - Re-engagement timer fires
- `EVENT_APPOINTMENT` - Meeting booked
- `EVENT_CLIENT_SIGNED` - Contract signed
- `EVENT_INACTIVITY_30D` - 30+ days no engagement
- `EVENT_REENGAGEMENT_EXHAUSTED` - Max attempts reached
- `EVENT_UNSUBSCRIBE` - Opted out
- `EVENT_HARD_BOUNCE` - Email bounced
- `EVENT_MANUAL_OVERRIDE` - Admin override

### funnel_membership
- `COLD_UNIVERSE` - Funnel 1
- `TALENTFLOW_UNIVERSE` - Funnel 2
- `WARM_UNIVERSE` - Funnel 3
- `REENGAGEMENT_UNIVERSE` - Funnel 4

## Index Summary

All tables are aggressively indexed for:
- `company_id` - Company lookups
- `person_id` - Person lookups
- `event_type` - Event filtering
- `funnel_state` - State queries
- Time-based fields - Range queries
- JSONB metadata - Flexible queries

## Helper Functions

| Function | Description |
|----------|-------------|
| `funnel.get_funnel_membership(person_id)` | Get current funnel for a person |
| `funnel.is_valid_transition(from, to, event)` | Validate state transition |
| `funnel.state_to_funnel(state)` | Map state to funnel membership |
| `funnel.is_in_cooldown(person_id)` | Check cooldown status |
| `funnel.count_events_in_window(person_id, type, days)` | Count events in window |
| `funnel.get_current_bit_score(person_id)` | Get latest BIT score |
| `funnel.has_fresh_talentflow_signal(person_id)` | Check for 90-day fresh signal |
| `funnel.get_journey_summary(person_id)` | Complete journey overview |
| `funnel.generate_event_hash(...)` | Deduplication hash |

## Views

| View | Description |
|------|-------------|
| `funnel.v_current_bit_scores` | Latest BIT score per person |
| `funnel.v_recent_movements` | Last 7 days of transitions |
| `funnel.v_movement_summary` | Transition counts by type |
| `funnel.v_upcoming_appointments` | Scheduled meetings |
| `funnel.v_appointment_outcomes` | Meeting conversion rates |
| `funnel.v_active_clients` | Current active clients |
| `funnel.v_revenue_by_funnel` | Revenue by source funnel |
| `funnel.v_monthly_conversions` | Monthly conversion trends |
| `funnel.v_upcoming_renewals` | Contracts expiring in 90 days |

## Related Documentation

- **Doctrine**: `ctb/sys/doctrine/4_funnel_doctrine.md`
- **State Machine**: `ctb/sys/doctrine/funnel_state_machine.md`
- **Rules**: `ctb/sys/doctrine/funnel_rules.md`

## Version

- **Schema Version**: 1.0.0
- **Created**: 2025-12-05

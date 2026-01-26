# BIT Pressure Signals

> **Authority**: ADR-017
> **Status**: DEPLOYED
> **Migration**: Phase 1 + Phase 1.5

## Signal Table Contract

All hub signal tables implement this structure:

| Column | Type | Description |
|--------|------|-------------|
| `signal_id` | UUID PK | Unique identifier |
| `company_unique_id` | TEXT | Company reference |
| `signal_type` | VARCHAR(50) | Signal classification |
| `pressure_domain` | ENUM | Domain constraint |
| `pressure_class` | ENUM | Pressure classification |
| `signal_value` | JSONB | Domain-specific payload |
| `magnitude` | INTEGER | Impact score (0-100) |
| `detected_at` | TIMESTAMPTZ | Detection time |
| `expires_at` | TIMESTAMPTZ | Validity window end |
| `correlation_id` | UUID | PID binding |
| `source_record_id` | TEXT | Traceability |

## Signal Tables by Hub

### DOL: `dol.pressure_signals`

**Domain**: STRUCTURAL_PRESSURE (Highest Trust)

| Signal Type | Source | Magnitude Range |
|-------------|--------|-----------------|
| `renewal_proximity` | renewal_calendar | 25-70 |
| `cost_increase` | form_5500 | 30-60 |
| `broker_change` | schedule_a | 40-70 |

**Bridge**: `dol.bridge_renewal_calendar()` trigger on `dol.renewal_calendar`

**Backfill**: `dol.backfill_renewal_signals()` function

### People: `people.pressure_signals`

**Domain**: DECISION_SURFACE (Medium Trust)

| Signal Type | Source | Magnitude Range |
|-------------|--------|-----------------|
| `executive_movement` | talent_flow.movements | 10-40 |
| `slot_vacancy` | company_slot | 20-35 |
| `authority_gap` | slot_assignment_history | 25-45 |

**Bridge**: `people.bridge_talent_flow_movement()` trigger on `talent_flow.movements`

### Blog: `blog.pressure_signals`

**Domain**: NARRATIVE_VOLATILITY (Lowest Trust)

| Signal Type | Source | Magnitude Range |
|-------------|--------|-----------------|
| `funding_announcement` | news | 20-40 |
| `news_mention` | press | 10-25 |
| `growth_indicator` | content | 15-30 |

**Trust Cap**: Blog alone = max Band 1

## Union View

`company_target.vw_all_pressure_signals` unions all three tables:
- Filters expired signals (`expires_at > NOW()`)
- Adds `source_hub` column ('dol', 'people', 'blog')

## Pressure Classes

| Class | Description | Primary Source |
|-------|-------------|----------------|
| `COST_PRESSURE` | Cost visibility gap | DOL |
| `VENDOR_DISSATISFACTION` | Broker churn | DOL + People |
| `DEADLINE_PROXIMITY` | Compressed decisions | DOL |
| `ORGANIZATIONAL_RECONFIGURATION` | Knowledge loss | People |
| `OPERATIONAL_CHAOS` | Compliance gaps | DOL |

## Related Documents

- [[BIT Authorization System Overview]]
- [[BIT Authorization Bands]]

## Tags

#bit #signals #schema #phase1

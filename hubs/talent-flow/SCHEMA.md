# Talent Flow Hub - Schema Documentation

> **AUTHORITY**: Neon PostgreSQL (Production)
> **VERIFIED**: 2026-01-25 via READ-ONLY connection
> **HUB ID**: 04.04.06
> **STATUS**: NEON VERIFIED

---

## Schema Overview

The Talent Flow hub tracks executive transitions, departures, and job market signals that indicate buying intent. It operates in SENSOR-ONLY mode - detecting movements but never triggering enrichment. All signals reference valid company_unique_id from upstream.

## Primary Tables

| Schema | Table | Purpose |
|--------|-------|---------|
| `talent_flow` | `movement_history` | Core movement tracking |
| `talent_flow` | `movements` | **BIT v2.0** Executive movements for pressure signals |
| `people` | `person_movement_history` | Person-level movement records |
| `outreach` | `bit_signals` | Movement signals for BIT scoring |

---

## Entity Relationship Diagram

```mermaid
erDiagram
    PEOPLE_PEOPLE_MASTER ||--o{ PEOPLE_PERSON_MOVEMENT_HISTORY : "unique_id"
    OUTREACH_OUTREACH ||--o{ TALENT_FLOW_MOVEMENT_HISTORY : "from/to outreach_id"
    OUTREACH_OUTREACH ||--o{ OUTREACH_BIT_SIGNALS : "outreach_id"
    TALENT_FLOW_MOVEMENT_HISTORY ||--o{ OUTREACH_BIT_SIGNALS : "triggers"
    TALENT_FLOW_MOVEMENTS ||--o{ PEOPLE_PRESSURE_SIGNALS : "bridge_trigger"

    TALENT_FLOW_MOVEMENTS {
        uuid movement_id PK
        uuid contact_id FK
        varchar movement_type
        text old_company_id
        text new_company_id
        text old_title
        text new_title
        int confidence_score
        timestamptz detected_at
        varchar detected_source
    }

    PEOPLE_PRESSURE_SIGNALS {
        uuid signal_id PK
        text company_unique_id FK
        varchar signal_type
        enum pressure_domain
        int magnitude
    }

    PEOPLE_PEOPLE_MASTER {
        text unique_id PK
        text company_unique_id
        text company_slot_unique_id
        text first_name
        text last_name
        text title
        text email
        text linkedin_url
    }

    TALENT_FLOW_MOVEMENT_HISTORY {
        uuid history_id PK
        text person_identifier
        uuid from_outreach_id FK
        uuid to_outreach_id FK
        varchar movement_type
        timestamptz detected_at
        varchar detection_source
        timestamptz processed_at
        varchar signal_emitted
        boolean bit_event_created
        uuid correlation_id
        uuid process_id
        timestamptz created_at
    }

    PEOPLE_PERSON_MOVEMENT_HISTORY {
        int id PK
        text person_unique_id FK
        text linkedin_url
        text company_from_id
        text company_to_id
        text title_from
        text title_to
        text movement_type
        timestamp detected_at
        jsonb raw_payload
        timestamp created_at
    }

    OUTREACH_OUTREACH {
        uuid outreach_id PK
        uuid sovereign_id FK
        varchar domain
        timestamp created_at
    }

    OUTREACH_BIT_SIGNALS {
        uuid signal_id PK
        uuid outreach_id FK
        varchar signal_type
        numeric signal_impact
        varchar source_spoke
        uuid correlation_id
        int decay_period_days
        numeric decayed_impact
        timestamp signal_timestamp
    }
```

---

## Table Details

### talent_flow.movement_history

Core movement tracking table for talent flow signals.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `history_id` | uuid | NOT NULL | - | Primary key |
| `person_identifier` | text | NOT NULL | - | Person reference (LinkedIn URL or ID) |
| `from_outreach_id` | uuid | NULL | - | Source company outreach ID |
| `to_outreach_id` | uuid | NULL | - | Destination company outreach ID |
| `movement_type` | varchar | NULL | - | Type (joined, left, title_change) |
| `detected_at` | timestamptz | NULL | - | When movement was detected |
| `detection_source` | varchar | NULL | - | How it was detected |
| `processed_at` | timestamptz | NULL | - | When signal was processed |
| `signal_emitted` | varchar | NULL | - | Signal type emitted |
| `bit_event_created` | boolean | NULL | - | BIT event was created |
| `correlation_id` | uuid | NULL | - | Correlation ID for tracing |
| `process_id` | uuid | NULL | - | Process ID |
| `created_at` | timestamptz | NULL | - | Record creation time |

### people.person_movement_history

Person-level movement history with detailed tracking.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | integer | NOT NULL | sequence | Primary key |
| `person_unique_id` | text | NOT NULL | - | FK to people_master |
| `linkedin_url` | text | NULL | - | LinkedIn profile URL |
| `company_from_id` | text | NOT NULL | - | Previous company ID |
| `company_to_id` | text | NULL | - | New company ID (null if departed) |
| `title_from` | text | NOT NULL | - | Previous title |
| `title_to` | text | NULL | - | New title |
| `movement_type` | text | NOT NULL | - | Type (promotion, departure, lateral) |
| `detected_at` | timestamp | NOT NULL | now() | Detection timestamp |
| `raw_payload` | jsonb | NULL | - | Raw detection data |
| `created_at` | timestamp | NULL | now() | Record creation time |

---

## Foreign Key Relationships

| Source Table | Source Column | Target Table | Target Column |
|--------------|---------------|--------------|---------------|
| people.person_movement_history | person_unique_id | people.people_master | unique_id |

---

## Movement Types

| Type | Description | Signal Value |
|------|-------------|--------------|
| `joined` | Executive joined from another company | +10 BIT |
| `left` | Executive departed (may signal instability) | +5 BIT |
| `title_change` | Title changed (promotion/demotion) | +3 BIT |
| `promotion` | Title advancement within company | +5 BIT |
| `lateral` | Same-level move to different company | +8 BIT |
| `departure` | Left company (no destination known) | +5 BIT |

---

## PASS Criteria

The hub computes PASS status based on:

1. **Freshness Window**: Movement signals within 60 days
2. **Minimum Movements**: At least 1 valid movement signal
3. **Confidence Threshold**: Signal confidence >= 0.70
4. **Upstream Dependency**: People Intelligence hub must not be BLOCKED

## Status Transitions

| From | To | Condition |
|------|-----|-----------|
| IN_PROGRESS | PASS | Valid movement detected within freshness window |
| PASS | IN_PROGRESS | All signals expire (freshness decay) |
| * | BLOCKED | Upstream People Intelligence is BLOCKED |

---

## Signal Integration

### BIT Engine Integration

Movement signals feed into BIT (Buyer Intent Tracker) scoring:

```
movement_event → talent_flow.movement_history → outreach.bit_signals
```

### Signal Schema

```json
{
  "signal_type": "TALENT_MOVEMENT",
  "signal_impact": 10,
  "source_spoke": "talent-flow",
  "decay_period_days": 90,
  "signal_metadata": {
    "movement_type": "joined",
    "person_identifier": "linkedin.com/in/xyz",
    "from_company": "Company A",
    "to_company": "Company B"
  }
}
```

---

## Detection Sources

| Source | Description |
|--------|-------------|
| `linkedin_monitor` | LinkedIn profile change detection |
| `manual_import` | Manual CSV import of movements |
| `news_crawler` | News/press release monitoring |
| `data_provider` | Third-party data provider feed |

---

## BIT v2.0 Movements Table (Phase 1.5)

### talent_flow.movements

**AI-Ready Data Metadata (per Canonical Architecture Doctrine §12):**

| Field | Value |
|-------|-------|
| `table_unique_id` | `TBL-TF-MOVEMENTS-001` |
| `owning_hub_unique_id` | `HUB-TF-001` |
| `owning_subhub_unique_id` | `SUBHUB-TF-001` |
| `description` | Executive movement tracking for BIT pressure signal generation. Captures hires, departures, promotions, and lateral moves. |
| `source_of_truth` | Talent Flow detection processes |
| `row_identity_strategy` | UUID primary key (movement_id) |

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `movement_id` | uuid | NOT NULL | gen_random_uuid() | Primary key |
| `contact_id` | uuid | NOT NULL | - | Person who moved |
| `movement_type` | varchar(20) | NOT NULL | - | hire, departure, promotion, lateral |
| `old_company_id` | text | NULL | - | Company they left (nullable for hires) |
| `new_company_id` | text | NULL | - | Company they joined (nullable for departures) |
| `old_title` | text | NULL | - | Previous title |
| `new_title` | text | NULL | - | New title |
| `confidence_score` | integer | NOT NULL | 0 | 0-100 detection confidence |
| `detected_at` | timestamptz | NOT NULL | now() | When movement was detected |
| `detected_source` | varchar(50) | NOT NULL | 'manual' | Source of detection |
| `created_at` | timestamptz | NOT NULL | now() | Record creation |
| `updated_at` | timestamptz | NOT NULL | now() | Last update |

**Column Metadata (per §12.3):**

| Column | column_unique_id | semantic_role | format |
|--------|------------------|---------------|--------|
| `movement_id` | COL-TF-MV-001 | identifier | UUID |
| `contact_id` | COL-TF-MV-002 | foreign_key | UUID |
| `movement_type` | COL-TF-MV-003 | attribute | ENUM |
| `old_company_id` | COL-TF-MV-004 | foreign_key | TEXT |
| `new_company_id` | COL-TF-MV-005 | foreign_key | TEXT |
| `old_title` | COL-TF-MV-006 | attribute | TEXT |
| `new_title` | COL-TF-MV-007 | attribute | TEXT |
| `confidence_score` | COL-TF-MV-008 | metric | INTEGER |
| `detected_at` | COL-TF-MV-009 | attribute | ISO-8601 |
| `detected_source` | COL-TF-MV-010 | attribute | ENUM |
| `created_at` | COL-TF-MV-011 | attribute | ISO-8601 |
| `updated_at` | COL-TF-MV-012 | attribute | ISO-8601 |

**Constraints:**
- At least one of `old_company_id` or `new_company_id` must be non-null
- `confidence_score` must be 0-100
- `movement_type` must be one of: hire, departure, promotion, lateral

**Bridge Trigger:** `trg_bridge_to_pressure_signals` fires on INSERT, calling `people.bridge_talent_flow_movement()` to emit DECISION_SURFACE signals to `people.pressure_signals`.

**Authority:** ADR-017
**Migration:** `neon/migrations/2026-01-26-bit-v2-phase1.5-backfill-and-movements.sql`

---

*Generated from Neon PostgreSQL via READ-ONLY connection*
*Last verified: 2026-01-26*

---

## Dropped Tables (2026-02-20 -- Table Consolidation)

The following tables were **dropped** during database consolidation. All had 0 rows at time of drop.
Recreatable from migration files if needed.

| Table | Reason | Migration Source |
|-------|--------|-----------------|
| `talent_flow.movement_history` | 0 rows, core movement tracking never populated | `migrations/2025-11-10-talent-flow.sql` |
| `talent_flow.movements` | 0 rows, BIT v2.0 executive movement table never populated | `migrations/2026-01-26-bit-v2-phase1.5-backfill-and-movements.sql` |
| `people.person_movement_history` | 0 rows, person-level movement records never populated | `migrations/2025-11-10-talent-flow.sql` |

**Note:** All three core Talent Flow tables were dropped. The entire `talent_flow` schema is now empty. Movement detection was designed but never activated in production.

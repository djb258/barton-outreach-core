# Tier Telemetry ERD

## Document Info

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Date** | 2026-01-20 |
| **Author** | IMO-Creator |
| **Status** | FROZEN (v1.0 Baseline) |

---

## Entity Relationship Diagram

```mermaid
erDiagram
    %% Core Tables
    company_target {
        uuid company_unique_id PK
        text domain
        text verified_pattern
        timestamp created_at
        timestamp updated_at
    }

    company_hub_status {
        uuid id PK
        uuid company_unique_id FK
        text hub_id FK
        enum status "PASS|IN_PROGRESS|FAIL|BLOCKED"
        timestamp status_updated_at
        text status_reason
        jsonb metadata
    }

    hub_registry {
        text hub_id PK
        text hub_name
        text classification
        boolean gates_completion
        int waterfall_order
    }

    manual_overrides {
        uuid override_id PK
        uuid company_unique_id FK
        enum override_type
        text reason
        jsonb metadata
        boolean is_active
        timestamp expires_at
        timestamp created_at
    }

    %% Telemetry Tables
    tier_snapshot_history {
        uuid snapshot_id PK
        date snapshot_date UK
        int total_companies
        int ineligible_count
        int tier_0_count
        int tier_1_count
        int tier_2_count
        int tier_3_count
        int blocked_total
        int complete_total
        int in_progress_total
        jsonb hub_pass_rates
        jsonb hub_block_rates
        jsonb freshness_stats
        timestamp captured_at
    }

    %% Audit Tables
    send_attempt_audit {
        uuid audit_id PK
        uuid company_unique_id FK
        text campaign_id
        text correlation_id
        int computed_tier
        int effective_tier
        boolean was_blocked
        text block_reason
        jsonb eligibility_snapshot
        timestamp attempt_timestamp
    }

    override_audit_log {
        uuid audit_id PK
        uuid override_id FK
        uuid company_unique_id FK
        text action
        jsonb old_values
        jsonb new_values
        text performed_by
        timestamp performed_at
    }

    %% Relationships
    company_target ||--o{ company_hub_status : "has"
    hub_registry ||--o{ company_hub_status : "defines"
    company_target ||--o{ manual_overrides : "may have"
    company_target ||--o{ send_attempt_audit : "logged in"
    manual_overrides ||--o{ override_audit_log : "audited by"

    %% Views (conceptual)
    vw_sovereign_completion }o--|| company_hub_status : "aggregates"
    vw_marketing_eligibility }o--|| vw_sovereign_completion : "computes from"
    vw_marketing_eligibility_with_overrides }o--|| vw_marketing_eligibility : "extends"
    vw_marketing_eligibility_with_overrides }o--|| manual_overrides : "applies"

    vw_tier_distribution }o--|| vw_marketing_eligibility : "summarizes"
    vw_hub_block_analysis }o--|| company_hub_status : "analyzes"
    vw_freshness_analysis }o--|| company_hub_status : "analyzes"
    vw_tier_drift_analysis }o--|| tier_snapshot_history : "compares"
```

---

## Tables

### tier_snapshot_history

Daily snapshots of tier distribution.

| Column | Type | Description |
|--------|------|-------------|
| snapshot_id | UUID | Primary key |
| snapshot_date | DATE | Date of snapshot (unique) |
| total_companies | INT | Total company count |
| ineligible_count | INT | Tier -1 count |
| tier_0_count | INT | Tier 0 count |
| tier_1_count | INT | Tier 1 count |
| tier_2_count | INT | Tier 2 count |
| tier_3_count | INT | Tier 3 count |
| blocked_total | INT | Total blocked |
| complete_total | INT | Total complete |
| in_progress_total | INT | Total in progress |
| hub_pass_rates | JSONB | Pass rate by hub |
| hub_block_rates | JSONB | Block rate by hub |
| freshness_stats | JSONB | Stale % by hub |
| captured_at | TIMESTAMPTZ | Capture timestamp |

### send_attempt_audit

Append-only audit of send attempts.

| Column | Type | Description |
|--------|------|-------------|
| audit_id | UUID | Primary key |
| company_unique_id | UUID | Target company |
| campaign_id | TEXT | Campaign identifier |
| correlation_id | TEXT | Request correlation |
| computed_tier | INT | Tier before overrides |
| effective_tier | INT | Tier after overrides |
| was_blocked | BOOLEAN | Whether blocked |
| block_reason | TEXT | Why blocked |
| eligibility_snapshot | JSONB | Full state at time |
| attempt_timestamp | TIMESTAMPTZ | When attempted |

---

## Views

### Telemetry Views (READ-ONLY)

| View | Purpose | Source |
|------|---------|--------|
| vw_tier_distribution | Tier counts and percentages | vw_marketing_eligibility |
| vw_hub_block_analysis | Block rate by hub | company_hub_status |
| vw_freshness_analysis | Stale % by hub | company_hub_status |
| vw_signal_gap_analysis | Signal coverage gaps | company_hub_status |
| vw_tier_telemetry_summary | Dashboard summary | Multiple |
| vw_tier_drift_analysis | Day-over-day changes | tier_snapshot_history |

### Authoritative Views (FROZEN)

| View | Purpose | Authority |
|------|---------|-----------|
| vw_sovereign_completion | Hub status aggregation | ADR-006 |
| vw_marketing_eligibility | Tier computation | ADR-006 |
| vw_marketing_eligibility_with_overrides | **THE** source of truth | ADR-007 |

---

## Functions

### fn_capture_tier_snapshot()

Captures a daily snapshot to tier_snapshot_history.

```sql
SELECT outreach.fn_capture_tier_snapshot();
```

Returns: UUID of created snapshot

---

## Relationships

```
company_target
    │
    ├──► company_hub_status (1:N per hub)
    │         │
    │         └──► hub_registry (N:1 lookup)
    │
    ├──► manual_overrides (1:N overrides)
    │         │
    │         └──► override_audit_log (1:N audit)
    │
    └──► send_attempt_audit (1:N attempts)

Views:
    company_hub_status ──► vw_sovereign_completion
                               │
                               ▼
                        vw_marketing_eligibility
                               │
                               ▼
                    vw_marketing_eligibility_with_overrides ◄── manual_overrides
                               │
                               ▼
                        vw_tier_distribution
                               │
                               ▼
                    tier_snapshot_history ──► vw_tier_drift_analysis
```

---

## References

- `infra/migrations/2026-01-20-tier-telemetry-views.sql`
- `infra/migrations/2026-01-19-kill-switches.sql`
- ADR-009: Tier Telemetry Analytics
- ADR-006: Sovereign Completion Infrastructure

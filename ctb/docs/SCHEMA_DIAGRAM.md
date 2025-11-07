<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs
Barton ID: 06.01.00
Unique ID: CTB-10793FD3
Blueprint Hash:
Last Updated: 2025-11-07
Enforcement: ORBT
─────────────────────────────────────────────
-->

# Database Schema Diagram

**Database**: Marketing DB (Neon PostgreSQL)
**Last Exported**: 2025-11-07
**Total Schemas**: 11
**Total Tables**: 64

---

## Primary Production Schema (marketing)

```mermaid
erDiagram
    company_master ||--o{ company_slots : has
    company_master ||--o{ pipeline_events : generates
    company_slots }o--|| people_master : "filled by"
    people_master ||--o{ people_resolution_queue : "may have duplicates"
    people_master ||--o{ contact_enrichment : "enriched via"
    people_master ||--o{ email_verification : "verified via"

    company_master {
        text company_unique_id PK "Barton ID"
        text company_name
        text industry
        integer employee_count
        decimal revenue
        text website
        text linkedin_url
        text phone
        text address
        text city
        text state
        text postal_code
        timestamp created_at
        timestamp updated_at
    }

    company_slots {
        text slot_unique_id PK "Barton ID"
        text company_unique_id FK
        text person_unique_id FK
        text slot_type "CEO/CFO/HR"
        boolean is_filled
        timestamp filled_at
        timestamp last_refreshed_at
    }

    people_master {
        text unique_id PK "Barton ID"
        text full_name
        text email
        text linkedin_url
        text title
        text phone
        text company_unique_id FK
        text source
        timestamp created_at
        timestamp updated_at
    }

    people_resolution_queue {
        text resolution_id PK
        text person_unique_id_primary FK
        text person_unique_id_duplicate FK
        text resolution_status
        text conflict_type
        timestamp created_at
    }

    contact_enrichment {
        text enrichment_id PK
        text person_unique_id FK
        text agent_name "Apify/Abacus/Firecrawl"
        text enrichment_type
        text status
        timestamp started_at
        timestamp completed_at
    }

    email_verification {
        text verification_id PK
        text person_unique_id FK
        text email_status "valid/invalid/risky"
        text provider "MillionVerifier"
        timestamp verified_at
    }

    pipeline_events {
        text event_id PK
        text company_unique_id FK
        text event_type
        jsonb payload
        timestamp created_at
    }

    pipeline_errors {
        text error_id PK
        text error_code
        text error_message
        text severity
        text component
        timestamp created_at
    }
```

---

## Buyer Intent Tracking Schema (bit)

```mermaid
erDiagram
    bit_signal ||--o{ bit_company_score : aggregates
    bit_signal ||--o{ bit_contact_score : aggregates

    bit_signal {
        text signal_id PK
        text company_unique_id FK
        text signal_type "website/linkedin/hiring"
        text signal_data jsonb
        integer signal_strength
        timestamp detected_at
    }

    bit_company_score {
        text score_id PK
        text company_unique_id FK
        integer total_score
        jsonb signal_breakdown
        timestamp calculated_at
    }

    bit_contact_score {
        text score_id PK
        text person_unique_id FK
        integer engagement_score
        jsonb activity_breakdown
        timestamp calculated_at
    }
```

---

## Product-Led Enrichment Schema (ple)

```mermaid
erDiagram
    ple_cycle ||--o{ ple_step : contains
    ple_step ||--o{ ple_log : logs

    ple_cycle {
        text cycle_id PK
        text cycle_name
        text status "pending/running/completed"
        timestamp started_at
        timestamp completed_at
    }

    ple_step {
        text step_id PK
        text cycle_id FK
        text step_name
        text step_type
        text status
        timestamp executed_at
    }

    ple_log {
        text log_id PK
        text step_id FK
        text log_level
        text message
        timestamp logged_at
    }
```

---

## Data Ingestion Schema (intake)

```mermaid
erDiagram
    company_raw_intake

    company_raw_intake {
        text intake_id PK
        text company_name
        text industry
        text website
        text validation_status
        text promoted_to_unique_id
        timestamp uploaded_at
        timestamp validated_at
    }
```

---

## Key Relationships & Data Flows

### 1. Company Ingestion Flow
```
intake.company_raw_intake (453 rows)
    ↓ [validation & promotion]
marketing.company_master (453 rows)
    ↓ [slot generation: 3 per company]
marketing.company_slots (1,359 rows)
```

### 2. Executive Position Tracking
```
marketing.company_slots (1,359 slots)
    ↓ [filled with executives]
marketing.people_master (170 people)
    ↓ [~12.5% fill rate]
Unfilled slots: ~1,189 (87.5%)
```

### 3. Enrichment Pipeline
```
marketing.people_master (170 contacts)
    ↓ [enrichment needed]
marketing.contact_enrichment (job tracking)
    ↓ [external APIs: Apify, Abacus, Firecrawl]
marketing.people_master (updated with enriched data)
```

### 4. Duplicate Resolution
```
marketing.people_master (170 contacts)
    ↓ [duplicate detection]
marketing.people_resolution_queue (1,206 duplicates)
    ↓ [manual/auto resolution]
marketing.people_master (de-duplicated)
```

### 5. Intent Signal Tracking
```
bit.bit_signal (detected signals)
    ↓ [aggregation by company]
bit.bit_company_score (company-level scores)
    ↓ [aggregation by contact]
bit.bit_contact_score (contact-level scores)
```

---

## Current Data Volumes

| Schema | Table | Rows | Status |
|--------|-------|------|--------|
| **marketing** | company_master | 453 | ✅ Active |
| **marketing** | company_slots | 1,359 | ✅ Active |
| **marketing** | people_master | 170 | ✅ Active |
| **marketing** | people_resolution_queue | 1,206 | ⚠️ Needs resolution |
| **marketing** | pipeline_events | 1,890 | ✅ Active logging |
| **marketing** | pipeline_errors | 0 | ✅ No errors |
| **marketing** | contact_enrichment | 0 | 🔄 Ready |
| **marketing** | email_verification | 0 | 🔄 Ready |
| **intake** | company_raw_intake | 453 | ✅ Active staging |
| **bit** | bit_signal | 0 | 🔄 Ready |
| **bit** | bit_company_score | 0 | 🔄 Ready |
| **bit** | bit_contact_score | 0 | 🔄 Ready |
| **ple** | ple_cycle | 0 | 🔄 Ready |
| **ple** | ple_step | 0 | 🔄 Ready |
| **ple** | ple_log | 0 | 🔄 Ready |

---

## Schema Design Notes

### Barton ID Format
All primary keys use Barton Doctrine format: `NN.NN.NN.NN.NNNNN.NNN`

**Examples**:
- Company Master: `04.04.02.04.30000.###`
- Company Slots: `04.04.02.04.10000.###`
- People Master: `04.04.02.04.20000.###`
- Error Log: `04.04.02.04.40000.###`

### Indexes
- **Total indexes across database**: 200+
- **Most indexed table**: people_master (10 indexes)
- All foreign keys have supporting indexes
- Timestamps indexed for time-based queries

### Foreign Keys
- Proper referential integrity enforced
- Cascade deletes where appropriate
- On-update cascade for ID changes

---

## Visualization Tools

### Generate Fresh Diagram
```bash
# Export latest schema
npm run schema:export

# View schema map
npm run schema:view
```

### View Complete Schema Details
```bash
# Read human-friendly reference
cat ctb/data/SCHEMA_REFERENCE.md

# View JSON schema map
cat ctb/docs/schema_map.json | jq .
```

---

## Related Documentation

- **Complete Schema Reference**: `ctb/data/SCHEMA_REFERENCE.md`
- **Schema Map JSON**: `ctb/docs/schema_map.json`
- **SQL Schema Files**: `ctb/data/infra/*.sql`
- **Migrations**: `ctb/data/infra/migrations/*.sql`
- **Export Script**: `ctb/ops/scripts/export-neon-schema.py`

---

**Last Schema Export**: 2025-11-07
**Database**: Marketing DB (Neon PostgreSQL)
**Schemas**: 11 | **Tables**: 64 | **Rows**: ~53,000+

*This diagram is auto-generated from live database. Run `npm run schema:export` to refresh.*

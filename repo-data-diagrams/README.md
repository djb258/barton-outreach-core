# Barton Outreach Core - Data Diagrams

Central repository for all data schema documentation, ERDs, and reference materials.

## Contents

| File | Description |
|------|-------------|
| [PLE_SCHEMA_ERD.md](./PLE_SCHEMA_ERD.md) | Mermaid Entity Relationship Diagram |
| [PLE_SCHEMA_REFERENCE.md](./PLE_SCHEMA_REFERENCE.md) | Complete column-level reference |
| [ple_schema.json](./ple_schema.json) | Machine-readable schema definition |

## Quick Links

- **Full System ERD**: [docs/COMPLETE_SYSTEM_ERD.md](../docs/COMPLETE_SYSTEM_ERD.md)
- **Schema Map (JSON)**: [docs/schema_map.json](../docs/schema_map.json)
- **Architecture Docs**: [docs/architecture/](../docs/architecture/)

## Hub-and-Spoke Architecture

```
                    COMPANY INTELLIGENCE HUB (AXLE)
                           04.04.01
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ People  │          │   DOL   │          │Outreach │
   │  Hub    │          │   Hub   │          │   Hub   │
   │04.04.02 │          │04.04.03 │          │04.04.04 │
   └─────────┘          └─────────┘          └─────────┘
```

## Database Schemas

| Schema | Purpose | Key Tables |
|--------|---------|------------|
| `marketing` | Company Hub data | company_master, company_slot, pipeline_events |
| `people` | People Hub data | people_master, person_scores, movement_history |
| `dol` | DOL Hub data | form_5500, form_5500_sf, schedule_a |
| `intake` | Raw data staging | company_raw_intake, people_raw_intake, quarantine |
| `public` | System tables | shq_error_log |

## Golden Rule

```
IF company_id IS NULL OR domain IS NULL OR email_pattern IS NULL:
    STOP. DO NOT PROCEED.
    → Route to Company Identity Pipeline first.
```

---

*Last Updated: 2025-12-26*
*Architecture: Hub & Spoke v1.0*

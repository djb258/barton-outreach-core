# PLE Architecture Documentation

This directory contains technical architecture documentation for the Perpetual Lead Engine (PLE) data system.

---

## Quick Links

| Document | Purpose |
|----------|---------|
| [PLE_DATA_ARCHITECTURE.md](./PLE_DATA_ARCHITECTURE.md) | **Start here** - Overview, core doctrine, hub-and-spoke pattern |
| [SPOKE_DETAILS.md](./SPOKE_DETAILS.md) | Technical implementation details per spoke |

---

## What is PLE?

**PLE (Perpetual Lead Engine)** is a data architecture where:

1. **Company is the product** - All enrichment serves the company record
2. **Hub-and-spoke pattern** - Company master is the hub, data sources are spokes
3. **EIN is the federal passport** - One EIN connects to all government data (DOL, IRS, OSHA, etc.)

---

## Current Implementation

### ✅ Completed (Schema v2.0.0)

**DOL Federal Data Spoke:**
- `marketing.form_5500` (230K records) - Large retirement plans
- `marketing.form_5500_sf` (759K records) - Small plans
- `marketing.schedule_a` (336K records) - Insurance + renewal dates

**People Spoke:**
- `marketing.company_slot` - Executive positions (CEO, CFO, HR)
- `marketing.people_master` - Contact records
- `marketing.person_movement_history` - Job change tracking

**BIT Scoring Spoke:**
- `marketing.person_scores` - Buyer intent scores
- `marketing.company_events` - Company signals

---

## File Organization

```
docs/architecture/
├── README.md                      # This file
├── PLE_DATA_ARCHITECTURE.md       # Start here (overview)
└── SPOKE_DETAILS.md              # Technical details

repo-data-diagrams/
├── DOL_SPOKE_ERD.md              # Visual Mermaid diagram
├── ple_schema.json               # Machine-readable schema
└── PLE_SCHEMA_REFERENCE.md       # Column reference

ctb/sys/enrichment/
├── FORM_5500_COMPLETE_GUIDE.md   # DOL import workflow
├── create_schedule_a_table.js    # Table creation scripts
└── import_schedule_a.py          # CSV import scripts
```

---

## Key Concepts

### Hub-and-Spoke

```
COMPANY MASTER (hub)
├── DOL Spoke (federal data)
├── People Spoke (sensors)
└── BIT Scoring Spoke (intent signals)
```

### Quarantine Pattern

Unmatched data stays in spoke with `company_unique_id = NULL` until matched. Prevents data loss.

### EIN (Federal Join Key)

```
company_master.ein = form_5500.ein
    ↓
Access all DOL data
    ↓
Renewal dates, plan details, violations
```

---

## Getting Started

1. **Read:** [PLE_DATA_ARCHITECTURE.md](./PLE_DATA_ARCHITECTURE.md)
2. **Visualize:** [repo-data-diagrams/DOL_SPOKE_ERD.md](../../repo-data-diagrams/DOL_SPOKE_ERD.md)
3. **Query:** See example SQL in architecture docs
4. **Import:** Follow [FORM_5500_COMPLETE_GUIDE.md](../../ctb/sys/enrichment/FORM_5500_COMPLETE_GUIDE.md)

---

## Database Connection

**Host:** ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech
**Database:** Marketing DB
**Schema:** `marketing` (core), `intake` (staging)

**Connection String:**
```bash
export NEON_CONNECTION_STRING="postgresql://Marketing_DB_owner:[password]@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing_DB?sslmode=require"
```

---

## Example Queries

### Find Companies with Renewals in Next 90 Days

```sql
SELECT
    cm.company_name,
    cm.ein,
    sa.policy_year_end_date,
    sa.insurance_company_name,
    (sa.policy_year_end_date - CURRENT_DATE) as days_to_renewal
FROM marketing.company_master cm
JOIN marketing.form_5500 f5 ON f5.ein = cm.ein
JOIN marketing.schedule_a sa ON sa.ack_id = f5.ack_id
WHERE sa.policy_year_end_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '90 days'
ORDER BY sa.policy_year_end_date;
```

### Find Unmatched High-Value DOL Companies

```sql
SELECT
    ein,
    sponsor_name,
    state,
    participant_count,
    total_assets
FROM marketing.form_5500
WHERE company_unique_id IS NULL
AND state IN ('PA', 'VA', 'MD', 'OH', 'WV', 'KY')
AND participant_count >= 50
ORDER BY total_assets DESC;
```

---

**Last Updated:** 2026-02-06
**Schema Version:** 4.4.0
**CTB Registry:** 246 tables registered, Phase 3 LOCKED
**Status:** Production Ready

---

## CTB Registry

As of 2026-02-06, all 246 tables are registered in the CTB (Christmas Tree Backbone) registry with governance metadata:

```sql
-- Query the registry
SELECT table_schema, table_name, leaf_type, is_frozen
FROM ctb.table_registry
ORDER BY leaf_type, table_schema;
```

| Leaf Type | Count | Description |
|-----------|-------|-------------|
| CANONICAL | 50 | Core data tables |
| ARCHIVE | 112 | History tables |
| DEPRECATED | 21 | Legacy (read-only) |
| FROZEN | 9 | Immutable core tables |

See `docs/audit/CTB_PHASE3_ENFORCEMENT_SUMMARY.md` for full details.

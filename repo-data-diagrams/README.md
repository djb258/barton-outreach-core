# Repo Data Diagrams

> Central reference for all PLE (Perpetual Lead Engine) schema documentation.
> Auto-generated from Neon PostgreSQL database.

## Quick Links

| File | Format | Purpose |
|------|--------|---------|
| [PLE_SCHEMA_ERD.md](PLE_SCHEMA_ERD.md) | Mermaid | Visual ERD diagram |
| [PLE_SCHEMA_REFERENCE.md](PLE_SCHEMA_REFERENCE.md) | Markdown | Complete column reference |
| [ple_schema.json](ple_schema.json) | JSON | Machine-readable schema |

## Schema Files

### Visual Documentation

- **PLE_SCHEMA_ERD.md** - Mermaid ERD that renders in:
  - Obsidian
  - GitHub/GitLab
  - VS Code (with extension)

### Reference Documentation

- **PLE_SCHEMA_REFERENCE.md** - Human-readable tables with:
  - Column types and constraints
  - Foreign key relationships
  - Example INSERT statements
  - JOIN query examples

### Machine-Readable

- **ple_schema.json** - For scripts and automation:
  - Complete column metadata
  - Validation rules
  - Barton ID patterns
  - Enum definitions

## Audit Reports

| File | Purpose |
|------|---------|
| [PLE_SCHEMA_VERIFICATION_REPORT.md](PLE_SCHEMA_VERIFICATION_REPORT.md) | Schema gap analysis vs PLE spec |
| [PLE_CONSTRAINT_AUDIT_REPORT.md](PLE_CONSTRAINT_AUDIT_REPORT.md) | NOT NULL, CHECK, UNIQUE audit |
| [PLE_CONSTRAINT_AUDIT_SUMMARY.md](PLE_CONSTRAINT_AUDIT_SUMMARY.md) | Executive summary |

## Field Mappings

| File | Purpose |
|------|---------|
| [ple_field_mapping.json](ple_field_mapping.json) | PLE spec name → actual DB column |
| [ple_schema_map.json](ple_schema_map.json) | Current vs target comparison |
| [ple_schema_summary.json](ple_schema_summary.json) | Compact status summary |

## Database Quick Reference

### Tables (6 core PLE tables)

```
marketing.company_master     → Companies (50+ employees, PA/VA/MD/OH/WV/KY)
marketing.company_slot       → Executive slots (CEO, CFO, HR per company)
marketing.people_master      → Executives with LinkedIn/email
marketing.person_movement_history → Job change tracking
marketing.person_scores      → BIT scores
marketing.company_events     → Company news/signals
```

### Barton ID Formats

```
Companies: 04.04.01.XX.XXXXX.XXX
People:    04.04.02.XX.XXXXX.XXX
Slots:     04.04.05.XX.XXXXX.XXX
```

### Valid Enums

| Field | Values |
|-------|--------|
| slot_type | CEO, CFO, HR |
| address_state | PA, VA, MD, OH, WV, KY |
| movement_type | company_change, title_change, contact_lost |
| event_type | funding, acquisition, ipo, layoff, leadership_change, product_launch, office_opening, other |

## Usage

### Import schema in scripts

```javascript
const schema = require('./repo-data-diagrams/ple_schema.json');
const fieldMap = require('./repo-data-diagrams/ple_field_mapping.json');

// Get all required fields for company insert
const required = Object.entries(schema.tables.company_master.columns)
  .filter(([k, v]) => v.required)
  .map(([k]) => k);
```

### View ERD in Obsidian

1. Open `repo-data-diagrams/PLE_SCHEMA_ERD.md`
2. Switch to Reading View
3. Mermaid diagram renders automatically

---

**Last Updated:** 2025-11-26
**Database:** Neon PostgreSQL (Marketing DB)
**Status:** Production Ready

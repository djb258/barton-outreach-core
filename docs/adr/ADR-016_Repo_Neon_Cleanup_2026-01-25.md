# ADR-016: Repository and Neon Schema Cleanup

## Status
**EXECUTED**

## Date
2026-01-25

## Context

Following the establishment of IMO_CANONICAL_v1.0, a cleanup audit identified:
- 22 untracked temporary files/folders in the repository
- 67 empty tables across multiple Neon schemas
- Several deprecated schemas replaced by canonical implementations

This cleanup aligns the physical state with the documented doctrine.

## Decision

Execute aggressive repo cleanup and conservative Neon cleanup with full audit trail.

---

## REPO CLEANUP

### Files Deleted

#### Root-Level Temp Scripts (One-Off Operations)
| File | Lines | Original Purpose |
|------|-------|------------------|
| `analyze_state_data.py` | 281 | State data analysis |
| `audit_neon_fk_rls.py` | 368 | RLS audit |
| `audit_pipeline.py` | 388 | Pipeline audit |
| `incremental_footprint_pass.py` | 669 | Footprint migration |
| `pipeline_authority_reset.py` | 779 | Authority reset |
| `rls_verification.py` | 179 | RLS verification |
| `search_state_tables.py` | 337 | State search |
| `search_state_tables_v2.py` | 385 | State search v2 |
| `verify_neon_migration.py` | 166 | Migration verification |
| `nul` | - | Windows artifact |

#### JSON Data Files
| File | Size | Original Purpose |
|------|------|------------------|
| `neon_audit_results.json` | 20K | Audit results snapshot |
| `neon_table_inventory_v2.json` | 4K | Table inventory |
| `state_data_analysis.json` | 4K | State analysis |

#### Folders Deleted
| Folder | Size | Contents |
|--------|------|----------|
| `data/` | 961MB | DOL 2023 raw files (already imported to Neon) |
| `pipeline_output/` | 60K | CSV test outputs |
| `workers/` | 40K | One-off worker scripts |

### Files Retained
| Path | Reason |
|------|--------|
| `scripts/import_wv_executives.py` | Operational script |
| `scripts/load_clay_people_intake.py` | Operational script |
| `scripts/promote_intake_to_slots.py` | Operational script |
| `infra/migrations/*.py` | May need for future migrations |
| `hubs/dol-filings/imo/middle/importers/import_dol_2023.py` | Active importer |

---

## NEON CLEANUP

### Schemas Dropped

| Schema | Tables | Rows | Reason |
|--------|--------|------|--------|
| `bit` | 3 | 0 | Replaced by `outreach.bit_*` |
| `clay` | 2 | 0 | Staging tables, never used |
| `neon_auth` | 1 | 0 | Neon internal, unused |
| `ple` | 3 | 0 | Pipeline Log Engine, never implemented |
| `"BIT"` | 0 | 0 | Legacy uppercase duplicate |
| `"DOL"` | 0 | 0 | Legacy uppercase duplicate |
| `"PLE"` | 0 | 0 | Legacy uppercase duplicate |
| `"Sales"` | 0 | 0 | Legacy uppercase duplicate |

### Tables NOT Dropped (Future Use)
| Schema.Table | Reason |
|--------------|--------|
| `talent_flow.movement_history` | Part of doctrine, just scaffolded |
| `outreach.campaigns` | Future campaign execution |
| `outreach.sequences` | Future sequence execution |
| `outreach.send_log` | Future send tracking |

### Archive Schema
The `archive.*` tables with numeric suffixes are retained pending future review.
These appear to be point-in-time snapshots created during migrations.

---

## Data Import Confirmation

| Dataset | Source | Neon Table | Import Date | Rows |
|---------|--------|------------|-------------|------|
| DOL 2023 Form 5500 | `data/dol_2023/` | `dol.form_5500` | 2026-01-15 | 230,482 |
| DOL 2023 Form 5500-SF | `data/dol_2023/` | `dol.form_5500_sf` | 2026-01-15 | 760,652 |
| DOL 2023 Schedule A | `data/dol_2023/` | `dol.schedule_a` | 2026-01-15 | 337,476 |

Local `data/` folder deleted after confirming successful import.

---

## Consequences

### Positive
- Repo size reduced by ~1GB
- No orphan scripts at root level
- Neon schema count reduced
- Clear separation of canonical vs deprecated

### Negative
- Raw DOL files no longer local (available from DOL.gov if needed)

### Neutral
- Archive tables retained for future review

---

## Rollback

### Repo
Files can be recovered from git history prior to this commit.

### Neon
Empty schemas contained no data. If schemas need to be recreated:
```sql
CREATE SCHEMA IF NOT EXISTS bit;
CREATE SCHEMA IF NOT EXISTS clay;
CREATE SCHEMA IF NOT EXISTS neon_auth;
CREATE SCHEMA IF NOT EXISTS ple;
-- Legacy uppercase duplicates (not recommended to restore)
CREATE SCHEMA IF NOT EXISTS "BIT";
CREATE SCHEMA IF NOT EXISTS "DOL";
CREATE SCHEMA IF NOT EXISTS "PLE";
CREATE SCHEMA IF NOT EXISTS "Sales";
```

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-25 |
| Author | Claude Code |
| Status | EXECUTED |
| Approved By | User (verbal) |

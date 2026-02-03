# Schema Drift - Quick Reference Card

**Date**: 2026-02-02 | **Status**: 🔴 CRITICAL | **Coverage**: 38.8%

---

## By The Numbers

```
103 tables in Neon
 50 tables documented
 40 tables matching
 63 tables UNDOCUMENTED
 10 tables STALE (in docs but not in DB)
 40 tables with COLUMN MISMATCHES
```

---

## Run Drift Check

```bash
# From repo root
doppler run -- python ops/schema-drift/schema_drift_checker.py
python ops/schema-drift/analyze_schema_drift.py
```

**Output**: `ERD_NEON_DRIFT_REPORT.md`

---

## Critical Issues (Fix First)

### 1. CL Authority Registry
- **File**: `hubs/company-target/SCHEMA.md`
- **Table**: `cl.company_identity`
- **Issue**: Shows 4 columns, has 30+ in Neon
- **Missing**: `sovereign_company_id`, `outreach_id`, `sales_process_id`, `client_id`
- **Impact**: v1.0 certification violation

### 2. Kill Switch Undocumented
- **File**: `hubs/outreach-execution/SCHEMA.md`
- **Tables**: `outreach.manual_overrides`, `outreach.override_audit_log`
- **Issue**: Not documented at all
- **Impact**: Critical safety mechanism has no ERD

### 3. 63 Tables Undocumented
- 7 archive tables
- 8 error tracking tables
- 5 exclusion tables
- Hub registry, control, and operational tables

---

## Top 5 Priorities

| # | Task | File | Deadline |
|---|------|------|----------|
| 1 | Update `cl.company_identity` (add 26 cols) | `hubs/company-target/SCHEMA.md` | 48hr |
| 2 | Document kill switch tables | `hubs/outreach-execution/SCHEMA.md` | 48hr |
| 3 | Remove 10 stale table references | All SCHEMA.md | 1wk |
| 4 | Complete DOL tables (add 100+ cols) | `hubs/dol-filings/SCHEMA.md` | 2wk |
| 5 | Add archive tables (7 tables) | All SCHEMA.md | 2wk |

---

## Schema Grades

```
outreach:  37.5%  🔴 F
cl:        13.3%  🔴 F
people:    69.2%  🟡 D
dol:       85.7%  🟢 B
company:   58.3%  🟡 D
bit:       75.0%  🟡 C
```

---

## Common Mismatches

### Timestamp Types
**ERD**: `timestamp`
**Neon**: `timestamp with time zone` (timestamptz)
**Fix**: Update ALL timestamps to `timestamptz`

### Enum Types
**ERD**: `enum`
**Neon**: `USER-DEFINED`
**Fix**: Document enum values

### Missing Columns
**Pattern**: Operational columns like `created_at`, `updated_at` missing
**Fix**: Add to all tables

---

## Undocumented Table Categories

```
Archive (7):
  - *_archive tables across all schemas

Errors (8):
  - *_errors tables across all schemas

Exclusion (5):
  - cl.*_excluded tables
  - outreach.outreach_excluded

Control (3):
  - outreach.hub_registry
  - outreach.column_registry
  - outreach.entity_resolution_queue

Override (2):
  - outreach.manual_overrides
  - outreach.override_audit_log
```

---

## Stale References (Remove These)

```
❌ bit.bit_company_score
❌ bit.bit_contact_score
❌ bit.bit_signal
❌ blog.pressure_signals
❌ company.target_vw_all_pressure_signals
❌ marketing.company_master
❌ marketing.people_master
❌ outreach.ctx_context
❌ outreach.ctx_spend_log
❌ talent.flow_movement_history
```

---

## Documentation Files

```
📊 ERD_NEON_DRIFT_REPORT.md (full report)
📋 ERD_DRIFT_ACTION_CHECKLIST.md (17 priorities)
📈 ERD_DRIFT_ANALYSIS_SUMMARY.md (analysis)
📄 SCHEMA_DRIFT_EXEC_SUMMARY.md (executive summary)
🔧 ops/schema-drift/ (tools)
```

---

## Weekly Ops Checklist

```bash
□ Run: doppler run -- python ops/schema-drift/schema_drift_checker.py
□ Run: python ops/schema-drift/analyze_schema_drift.py
□ Review: git diff ERD_NEON_DRIFT_REPORT.md
□ Action: Address new drift items
□ Report: Standup update on progress
```

---

## Escalation Criteria

**Escalate to Architecture Team if:**
- Drift exceeds 10 tables
- Drift exceeds 50 columns
- Critical system undocumented (CL, kill switch, hub registry)
- v1.0 frozen components affected

---

## Quick Commands

```bash
# Extract schema
doppler run -- python ops/schema-drift/schema_drift_checker.py

# Analyze drift
python ops/schema-drift/analyze_schema_drift.py

# View summary
cat ERD_DRIFT_ANALYSIS_SUMMARY.md | less

# View checklist
cat ERD_DRIFT_ACTION_CHECKLIST.md | less

# Check specific table
cat neon_schema_snapshot.json | jq '.schema_details."outreach.company_target"'
```

---

## Need Help?

- **Tool Docs**: `ops/schema-drift/README.md`
- **Action Items**: `ERD_DRIFT_ACTION_CHECKLIST.md`
- **Full Report**: `ERD_NEON_DRIFT_REPORT.md`
- **Contact**: Database Engineering Team

---

**Last Updated**: 2026-02-02
**Next Check**: 2026-02-09 (weekly)
**Owner**: Database Engineering

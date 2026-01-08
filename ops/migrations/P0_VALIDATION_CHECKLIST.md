# P0 Spine Remediation — Post-Migration Validation Checklist

**Migration Date:** 2026-01-08
**Author:** Claude Code (Schema Remediation Engineer)
**Mode:** SAFE MODE
**Scope:** DOL, Talent Flow, Outreach Execution

---

## Pre-Flight Checks

Before running migrations, verify:

- [ ] Database backup completed
- [ ] No active writes to affected tables
- [ ] Migration window communicated to stakeholders
- [ ] Rollback scripts reviewed and ready

---

## Migration Execution Order

Run migrations in this exact order:

```bash
# Step 1: DOL Spine Alignment
psql -f ops/migrations/P0_001_dol_spine_alignment.sql

# Step 2: Talent Flow Spine Alignment
psql -f ops/migrations/P0_002_talent_flow_spine_alignment.sql

# Step 3: Outreach Execution Spine Alignment
psql -f ops/migrations/P0_003_outreach_execution_spine_alignment.sql
```

---

## Post-Migration Validation

### 1. DOL Spine Alignment (P0_001)

| Check | Query | Expected |
|-------|-------|----------|
| Column added | `SELECT column_name FROM information_schema.columns WHERE table_schema = 'dol' AND table_name = 'ein_linkage' AND column_name = 'outreach_id';` | 1 row |
| Index created | `SELECT indexname FROM pg_indexes WHERE schemaname = 'dol' AND indexname = 'idx_ein_linkage_outreach_id';` | 1 row |
| View created | `SELECT viewname FROM pg_views WHERE schemaname = 'dol' AND viewname = 'v_ein_linkage_pending_spine';` | 1 row |
| Backfill coverage | `SELECT resolution_status, COUNT(*) FROM dol.v_ein_linkage_pending_spine GROUP BY 1;` | Review coverage |

**Pass Criteria:**
- [ ] `outreach_id` column exists
- [ ] Index exists
- [ ] View exists
- [ ] Backfill coverage > 80% (or documented exceptions)

---

### 2. Talent Flow Spine Alignment (P0_002)

| Check | Query | Expected |
|-------|-------|----------|
| Columns added (movements) | `SELECT column_name FROM information_schema.columns WHERE table_schema = 'talent_flow' AND table_name = 'movements' AND column_name IN ('from_outreach_id', 'to_outreach_id', 'correlation_id', 'movement_hash');` | 4 rows |
| Columns added (svg_marketing) | `SELECT column_name FROM information_schema.columns WHERE table_schema = 'svg_marketing' AND table_name = 'talent_flow_movements' AND column_name IN ('outreach_id', 'correlation_id');` | 2 rows |
| Error table created | `SELECT tablename FROM pg_tables WHERE schemaname = 'talent_flow' AND tablename = 'talent_flow_errors';` | 1 row |
| View created | `SELECT viewname FROM pg_views WHERE schemaname = 'talent_flow' AND viewname = 'v_movements_pending_spine';` | 1 row |
| Backfill coverage | `SELECT from_resolution_status, to_resolution_status, COUNT(*) FROM talent_flow.v_movements_pending_spine GROUP BY 1, 2;` | Review coverage |

**Pass Criteria:**
- [ ] All 4 columns exist on `talent_flow.movements`
- [ ] All 2 columns exist on `svg_marketing.talent_flow_movements`
- [ ] `talent_flow_errors` table exists
- [ ] View exists
- [ ] Backfill coverage > 80% (or documented exceptions)

---

### 3. Outreach Execution Spine Alignment (P0_003)

| Check | Query | Expected |
|-------|-------|----------|
| Tables created | `SELECT tablename FROM pg_tables WHERE schemaname = 'outreach' AND tablename IN ('campaigns', 'send_log', 'execution_errors');` | 3 rows |
| FK constraints | `SELECT conname FROM pg_constraint WHERE conrelid = 'outreach.campaigns'::regclass AND contype = 'f';` | 1+ rows |
| Views created | `SELECT viewname FROM pg_views WHERE schemaname = 'outreach' AND viewname IN ('v_campaign_summary', 'v_send_activity');` | 2 rows |
| Indexes created | `SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'outreach' AND tablename IN ('campaigns', 'send_log', 'execution_errors');` | 14+ |

**Pass Criteria:**
- [ ] All 3 tables exist
- [ ] FK constraints exist and reference `outreach.outreach`
- [ ] Both views exist
- [ ] Indexes created

---

## Rollback Procedure

If any validation fails:

```bash
# Rollback in REVERSE order
psql -f ops/migrations/P0_003_outreach_execution_spine_alignment_ROLLBACK.sql
psql -f ops/migrations/P0_002_talent_flow_spine_alignment_ROLLBACK.sql
psql -f ops/migrations/P0_001_dol_spine_alignment_ROLLBACK.sql
```

---

## Known Issues / Exceptions

Document any records that could not be backfilled:

| Table | Issue | Count | Resolution Plan |
|-------|-------|-------|-----------------|
| dol.ein_linkage | NO_SPINE_RECORD | TBD | Needs spine record creation |
| talent_flow.movements | NO_SPINE_RECORD (from) | TBD | Needs spine record creation |
| talent_flow.movements | NO_SPINE_RECORD (to) | TBD | Needs spine record creation |

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| DBA | | | |
| Engineering Lead | | | |
| Architect | | | |

---

## Phase 2 Prerequisites

Before proceeding to Phase 2 (FK enforcement + trigger rewrite):

- [ ] All `NO_SPINE_RECORD` entries resolved
- [ ] Backfill coverage at 100% for all tables
- [ ] Application code updated to use `outreach_id`
- [ ] Testing completed in staging environment

---

**Last Updated:** 2026-01-08
**Migration Status:** P0 COMPLETE (Pending Validation)

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

# Step 4: History Sidecar Tables (Prevent Duplicate Work)
psql -f ops/migrations/P0_004_history_sidecar_tables.sql

# Step 5: Blog Production Enablement
psql -f ops/migrations/P0_005_blog_production_enablement.sql

# Step 6: Blog Canary Infrastructure
psql -f ops/migrations/P0_006_blog_canary_infrastructure.sql
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

### 4. History Sidecar Tables (P0_004)

| Check | Query | Expected |
|-------|-------|----------|
| Tables created | `SELECT tablename FROM pg_tables WHERE tablename IN ('blog_source_history', 'people_resolution_history', 'movement_history', 'bit_input_history');` | 4 rows |
| Triggers created | `SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_name LIKE '%history%';` | 8 triggers |
| Functions created | `SELECT routine_name FROM information_schema.routines WHERE routine_name IN ('blog_url_exists', 'person_already_resolved', 'movement_already_recorded', 'bit_signal_already_processed');` | 4 rows |

**Pass Criteria:**
- [ ] All 4 history tables exist
- [ ] All 8 append-only triggers exist
- [ ] All 4 helper functions exist
- [ ] Append-only enforcement works (test with UPDATE attempt)

**Append-Only Test:**
```sql
-- Insert test record
INSERT INTO outreach.blog_source_history (outreach_id, source_type, source_url)
VALUES ('00000000-0000-0000-0000-000000000001', 'test', 'https://test.com');

-- Attempt forbidden update (should FAIL)
UPDATE outreach.blog_source_history SET source_url = 'https://other.com'
WHERE source_url = 'https://test.com';
-- Expected: ERROR - APPEND-ONLY violation

-- Clean up
DELETE FROM outreach.blog_source_history WHERE source_type = 'test';
-- Expected: ERROR - APPEND-ONLY violation (deletes blocked too)
```

---

### 5. Blog Production Enablement (P0_005)

| Check | Query | Expected |
|-------|-------|----------|
| Control table exists | `SELECT enabled, notes FROM outreach.blog_ingress_control;` | enabled = FALSE |
| Enum created | `SELECT enumlabel FROM pg_enum WHERE enumtypid = 'outreach.blog_source_type'::regtype;` | 7 values |
| Views created | `SELECT viewname FROM pg_views WHERE schemaname = 'outreach' AND viewname LIKE '%blog%';` | 2+ rows |
| Helper functions | `SELECT outreach.blog_ingress_enabled();` | FALSE |

**Pass Criteria:**
- [ ] `blog_ingress_control` table exists with `enabled = FALSE`
- [ ] `blog_source_type` enum has all 7 values
- [ ] `v_blog_ready` and `v_blog_ingestion_queue` views exist
- [ ] `blog_ingress_enabled()` returns FALSE (default safe state)
- [ ] Social guard works (test insert with source_type='social' should fail)

**Social Guard Test:**
```sql
-- Should FAIL with DOCTRINE VIOLATION
INSERT INTO outreach.blog (outreach_id, source_type, source_url)
VALUES ('00000000-0000-0000-0000-000000000001', 'social', 'https://twitter.com/test');
-- Expected: ERROR - DOCTRINE VIOLATION: Blog sub-hub DISALLOWS social metrics
```

**Flip the Switch (When Ready):**
```sql
UPDATE outreach.blog_ingress_control
SET enabled = TRUE,
    enabled_at = NOW(),
    enabled_by = 'operator',
    notes = 'Initial production enablement';
```

---

### 6. Blog Canary Infrastructure (P0_006)

| Check | Query | Expected |
|-------|-------|----------|
| Canary table created | `SELECT COUNT(*), status FROM outreach.blog_canary_allowlist GROUP BY status;` | ~25 pending |
| Canary columns added | `SELECT canary_enabled FROM outreach.blog_ingress_control;` | FALSE |
| Should process function | `SELECT * FROM outreach.blog_should_process('00000000-0000-0000-0000-000000000001');` | DISABLED |
| Queue is empty | `SELECT COUNT(*) FROM outreach.v_blog_ingestion_queue;` | 0 (canary not enabled) |

**Pass Criteria:**
- [ ] `blog_canary_allowlist` table exists with ~25 seed records
- [ ] `canary_enabled` column exists and is FALSE
- [ ] `blog_should_process()` function returns DISABLED mode
- [ ] `v_blog_ingestion_queue` returns 0 rows (nothing enabled)

**Idempotency Verification Functions:**
| Function | Purpose | Expected Output |
|----------|---------|-----------------|
| `outreach.check_canary_idempotency()` | Verify second run = 0 fetches | All rows: `second_run_fetches = 0` |
| `outreach.get_canary_health()` | Monitor blog health metrics | `duplicate_urls = 0` (CRITICAL) |
| `outreach.promote_canary_to_global(TEXT)` | Safe promotion guard | Blocks if idempotency fails |

**Observability Checks (Pre-Canary):**
```sql
-- Confirm history table ready for writes
SELECT COUNT(*) FROM outreach.blog_source_history; -- Should be 0

-- Confirm canary allowlist populated
SELECT COUNT(*) FROM outreach.blog_canary_allowlist WHERE status = 'pending'; -- ~25

-- Confirm all kill switches OFF
SELECT switch_name, is_enabled FROM people.slot_ingress_control;
SELECT enabled, canary_enabled FROM outreach.blog_ingress_control;
```

**Canary Rollout:**
```sql
-- Step 1: Enable canary mode
UPDATE outreach.blog_ingress_control
SET canary_enabled = TRUE, canary_started_at = NOW();

-- Step 2: Run worker twice, check idempotency
SELECT * FROM outreach.check_canary_idempotency();

-- Step 3: Monitor 24 hours
SELECT * FROM outreach.get_canary_health();

-- Step 4: Promote to global (if clean)
SELECT outreach.promote_canary_to_global('your_name');
```

---

## Rollback Procedure

If any validation fails:

```bash
# Rollback in REVERSE order
psql -f ops/migrations/P0_006_blog_canary_infrastructure_ROLLBACK.sql
psql -f ops/migrations/P0_005_blog_production_enablement_ROLLBACK.sql
psql -f ops/migrations/P0_004_history_sidecar_tables_ROLLBACK.sql
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

# Deployment Checklist: Database Hardening

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | CL Parent-Child Doctrine v1.0 |
| **CC Layer** | CC-04 |

---

## Hub Identity (CC-02)

| Field | Value |
|-------|-------|
| **Sovereign ID** | CL (Company Lifecycle) |
| **Hub Name** | Barton Outreach Core |
| **Hub ID** | 04.04.02.04 |

---

## Pre-Deployment Checklist

### Documentation Verification
- [ ] ADR approved and merged (ADR-002_Database_Hardening_RLS.md)
- [ ] Migration order documented (infra/MIGRATION_ORDER.md)
- [ ] PRDs updated with schema changes
- [ ] CLAUDE.md updated with hardening status

### Migration Preparation
- [ ] All migration files present in infra/migrations/
- [ ] Migration order verified against MIGRATION_ORDER.md
- [ ] Backup strategy confirmed
- [ ] Rollback plan documented

### Environment Verification
- [ ] Doppler secrets configured
- [ ] Database connection verified
- [ ] Sufficient permissions for schema creation
- [ ] Sufficient permissions for role creation

---

## Migration Execution Order

Execute migrations in this exact order (from infra/MIGRATION_ORDER.md):

### Phase 1: Core Infrastructure
```bash
doppler run -- psql -f infra/migrations/002_create_master_error_log.sql
doppler run -- psql -f infra/migrations/003_enforce_master_error_immutability.sql
```

### Phase 2: Intake & Tracking
```bash
doppler run -- psql -f infra/migrations/002_create_clay_intake_tables.sql
doppler run -- psql -f infra/migrations/003_create_people_raw_intake.sql
doppler run -- psql -f infra/migrations/004_add_enrichment_tracking_to_intake.sql
```

### Phase 3: BIT & Slot Infrastructure
```bash
doppler run -- psql -f infra/migrations/2025-11-06-bit-enrichment.sql
doppler run -- psql -f infra/migrations/2025-11-10-slot-tracker.sql
doppler run -- psql -f infra/migrations/2025-11-10-slot-filled-trigger.sql
doppler run -- psql -f infra/migrations/2025-11-10-talent-flow.sql
```

### Phase 4: Outreach Schema
```bash
doppler run -- psql -f infra/migrations/2025-12-26-outreach-schema-creation.sql
doppler run -- psql -f infra/migrations/2026-01-13-outreach-execution-complete.sql
```

### Phase 5: DOL Schema
```bash
doppler run -- psql -f infra/migrations/2026-01-13-dol-schema-creation.sql
```

### Phase 6: History & Audit
```bash
doppler run -- psql -f infra/migrations/2026-01-11-slot-assignment-history.sql
```

### Phase 7: Security Hardening
```bash
doppler run -- psql -f infra/migrations/2026-01-13-enable-rls-production-tables.sql
```

---

## Post-Deployment Verification

### Schema Verification
```sql
-- Check schemas exist
SELECT schema_name FROM information_schema.schemata
WHERE schema_name IN ('outreach', 'dol', 'funnel', 'bit');

-- Expected: outreach, dol (+ funnel, bit if applicable)
```

### Table Count Verification
```sql
SELECT table_schema, COUNT(*) as table_count
FROM information_schema.tables
WHERE table_schema IN ('outreach', 'dol')
GROUP BY table_schema;

-- Expected:
-- outreach | 7 (company_target, people, engagement_events, campaigns, sequences, send_log, column_registry)
-- dol      | 4 (form_5500, form_5500_sf, schedule_a, renewal_calendar)
```

### RLS Verification
```sql
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname IN ('outreach', 'dol')
ORDER BY schemaname, tablename;

-- Expected: All tables show rowsecurity = true
```

### Role Verification
```sql
SELECT rolname FROM pg_roles
WHERE rolname IN ('outreach_hub_writer', 'dol_hub_writer', 'hub_reader', 'error_log_writer');

-- Expected: All 4 roles exist
```

### Policy Count Verification
```sql
SELECT schemaname, COUNT(*) as policy_count
FROM pg_policies
WHERE schemaname IN ('outreach', 'dol')
GROUP BY schemaname;

-- Expected: 29+ policies total
```

### Immutability Trigger Verification
```sql
SELECT tgname, tgrelid::regclass, tgenabled
FROM pg_trigger
WHERE tgname = 'trg_engagement_events_immutability_delete';

-- Expected: Trigger exists and is enabled
```

---

## Verification Checklist

- [ ] All schemas created (outreach, dol)
- [ ] Table counts match expected (outreach: 7, dol: 4)
- [ ] RLS enabled on all production tables
- [ ] All roles created (4 roles)
- [ ] Policy count matches expected (29+)
- [ ] Immutability trigger active on engagement_events
- [ ] No orphan FK references

---

## Lifecycle Audit

Run the following audit to verify system integrity:

```sql
-- Check for orphaned people records
SELECT COUNT(*) as orphan_count
FROM outreach.people p
LEFT JOIN outreach.company_target ct ON p.target_id = ct.target_id
WHERE ct.target_id IS NULL;

-- Expected: 0 orphans
```

```sql
-- Check send_log FK integrity
SELECT
    (SELECT COUNT(*) FROM outreach.send_log WHERE campaign_id IS NOT NULL) as with_campaign,
    (SELECT COUNT(*) FROM outreach.send_log WHERE person_id IS NOT NULL) as with_person;

-- Expected: All records have valid FKs
```

---

## Rollback Procedure

If deployment fails, execute in reverse order:

```sql
-- 1. Disable RLS
ALTER TABLE outreach.company_target DISABLE ROW LEVEL SECURITY;
ALTER TABLE outreach.people DISABLE ROW LEVEL SECURITY;
ALTER TABLE outreach.engagement_events DISABLE ROW LEVEL SECURITY;
-- ... repeat for all tables

-- 2. Drop policies
DROP POLICY IF EXISTS outreach_company_target_select ON outreach.company_target;
DROP POLICY IF EXISTS outreach_company_target_insert ON outreach.company_target;
-- ... repeat for all policies

-- 3. Drop roles
DROP ROLE IF EXISTS outreach_hub_writer;
DROP ROLE IF EXISTS dol_hub_writer;
DROP ROLE IF EXISTS hub_reader;

-- 4. Drop triggers
DROP TRIGGER IF EXISTS trg_engagement_events_immutability_delete ON outreach.engagement_events;

-- 5. Drop schemas (CAUTION: Data loss)
-- DROP SCHEMA dol CASCADE;
-- Only if tables were newly created in this deployment
```

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Deployer | | | |
| Verifier | | | |
| Hub Owner | | | |

---

## Traceability

| Artifact | Reference |
|----------|-----------|
| Canonical Doctrine | CANONICAL_ARCHITECTURE_DOCTRINE.md |
| ADR | docs/adr/ADR-002_Database_Hardening_RLS.md |
| Migration Order | infra/MIGRATION_ORDER.md |
| Hub Compliance | templates/checklists/HUB_COMPLIANCE.md |

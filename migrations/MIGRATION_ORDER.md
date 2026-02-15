# Database Migration Order

> **HARDENING DOCUMENT** - Created 2026-01-13
> Linear execution order. No diagrams. No prose.

## Execution Order

Run migrations in this exact order:

### Phase 1: Core Infrastructure

```
1. infra/migrations/002_create_master_error_log.sql
2. infra/migrations/003_enforce_master_error_immutability.sql
```

### Phase 2: Intake & Tracking

```
3. infra/migrations/002_create_clay_intake_tables.sql
4. infra/migrations/003_create_people_raw_intake.sql
5. infra/migrations/004_add_enrichment_tracking_to_intake.sql
```

### Phase 3: BIT & Slot Infrastructure

```
6. infra/migrations/2025-11-06-bit-enrichment.sql
7. infra/migrations/2025-11-10-slot-tracker.sql
8. infra/migrations/2025-11-10-slot-filled-trigger.sql
9. infra/migrations/2025-11-10-talent-flow.sql
```

### Phase 4: Outreach Schema

```
10. infra/migrations/2025-12-26-outreach-schema-creation.sql
11. infra/migrations/2026-01-13-outreach-execution-complete.sql
```

### Phase 5: DOL Schema

```
12. infra/migrations/2026-01-13-dol-schema-creation.sql
```

### Phase 6: History & Audit

```
13. infra/migrations/2026-01-11-slot-assignment-history.sql
```

### Phase 7: Security Hardening

```
14. infra/migrations/2026-01-13-enable-rls-production-tables.sql
```

## Neon Funnel Migrations (Separate Execution)

```
neon/migrations/0001_create_funnel_schema.sql
neon/migrations/0002_create_suspect_universe.sql
neon/migrations/0003_create_engagement_events.sql
neon/migrations/0004_create_warm_universe.sql
neon/migrations/0005_create_talentflow_signal_log.sql
neon/migrations/0006_create_bit_signal_log.sql
neon/migrations/0007_create_prospect_movement.sql
neon/migrations/0008_create_appointment_history.sql
neon/migrations/0009_create_client_conversion.sql
neon/migrations/0010_create_funnel_functions.sql
```

## Dependencies

| Migration | Depends On |
|-----------|------------|
| 003_enforce_master_error_immutability | 002_create_master_error_log |
| 2025-12-26-outreach-schema-creation | None (creates schema) |
| 2026-01-13-outreach-execution-complete | 2025-12-26-outreach-schema-creation |
| 2026-01-13-dol-schema-creation | None (creates schema) |
| 2026-01-13-enable-rls-production-tables | All table creation migrations |

## Verification

After all migrations, run:

```sql
-- Check schemas exist
SELECT schema_name FROM information_schema.schemata
WHERE schema_name IN ('outreach', 'dol', 'funnel', 'bit');

-- Check table counts
SELECT table_schema, COUNT(*) as table_count
FROM information_schema.tables
WHERE table_schema IN ('outreach', 'dol')
GROUP BY table_schema;

-- Check RLS enabled
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname IN ('outreach', 'dol')
ORDER BY schemaname, tablename;

-- Check roles created
SELECT rolname FROM pg_roles
WHERE rolname IN ('outreach_hub_writer', 'dol_hub_writer', 'hub_reader', 'error_log_writer');
```

## Expected State Post-Migration

| Schema | Tables | RLS Enabled |
|--------|--------|-------------|
| outreach | 7 | Yes |
| dol | 4 | Yes |
| public | 2+ (error tables) | Yes (error_log) |

---

**Last Updated**: 2026-01-13

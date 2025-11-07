# Database Migrations

## Purpose

Database schema migrations for Barton Outreach Core, per IMO Creator global config.

## Configuration

From `global-config.yaml`:
- **Directory**: `ctb/data/migrations/`
- **Auto-run**: No (manual execution required)
- **Naming Convention**: `NNN_description.sql`
- **Schema Validation**: Enabled

## Naming Convention

Format: `NNN_description.sql`

Examples:
- `001_create_shq_error_log.sql`
- `002_add_enrichment_indexes.sql`
- `003_create_bit_events_table.sql`

## Schemas

Managed schemas:
- `marketing` - Core marketing intelligence data
- `intake` - Data ingestion and staging
- `public` - System-wide tables
- `bit` - Buyer Intent Tool data

## Creating a Migration

1. **Create file**: `ctb/data/migrations/NNN_description.sql`
2. **Include**:
   - Migration ID comment
   - Barton Doctrine compliance notes
   - Up migration (CREATE/ALTER)
   - Down migration (DROP/REVERT) in comments
3. **Test** on development database first
4. **Document** in this README

## Migration Template

```sql
-- Migration: NNN_description
-- Created: YYYY-MM-DD
-- Barton Doctrine: Compliant
-- Schemas: marketing, public, etc.
-- Purpose: Brief description

-- UP MIGRATION
BEGIN;

-- Your DDL statements here
CREATE TABLE IF NOT EXISTS marketing.example_table (
  id SERIAL PRIMARY KEY,
  barton_id VARCHAR(50) UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_example_barton_id ON marketing.example_table(barton_id);

-- Triggers
CREATE TRIGGER update_example_updated_at
  BEFORE UPDATE ON marketing.example_table
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

COMMIT;

-- DOWN MIGRATION (for rollback reference)
-- DROP TRIGGER IF EXISTS update_example_updated_at ON marketing.example_table;
-- DROP INDEX IF EXISTS marketing.idx_example_barton_id;
-- DROP TABLE IF EXISTS marketing.example_table;
```

## Existing Migrations

### 001_create_shq_error_log.sql
- **Location**: `infra/migrations/001_create_shq_error_log.sql`
- **Status**: ✅ Applied (shq_error_log table exists with 8 indexes)
- **Purpose**: System-wide error logging
- **Schema**: `public`

## Running Migrations

### Manual Execution

```bash
# Connect to Neon database
psql postgresql://Marketing_DB_owner:...@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing_DB?sslmode=require

# Run migration
\i ctb/data/migrations/NNN_description.sql

# Verify
\dt marketing.*
\d marketing.table_name
```

### Automated Execution (Future)

Per global config, `auto_run: false` - migrations must be run manually for safety.

A migration runner script can be created if needed:
- `ctb/data/run-migrations.js`
- Track applied migrations in `migration_history` table
- Prevent re-running completed migrations

## Schema Validation

After running migrations, validate schema:

```bash
# Refresh schema map
node infra/scripts/schema-refresh.js

# Check docs/schema_map.json for changes
cat docs/schema_map.json
```

## Best Practices

1. ✅ Always test on development first
2. ✅ Include rollback instructions in comments
3. ✅ Follow Barton Doctrine ID format for any new tables
4. ✅ Add indexes for foreign keys
5. ✅ Use `IF EXISTS` / `IF NOT EXISTS` for idempotency
6. ✅ Document breaking changes clearly
7. ✅ Update schema map after applying migrations

## Migration Tracking

Suggested table (not yet implemented):

```sql
CREATE TABLE IF NOT EXISTS public.migration_history (
  migration_id SERIAL PRIMARY KEY,
  migration_file VARCHAR(255) UNIQUE NOT NULL,
  applied_at TIMESTAMPTZ DEFAULT NOW(),
  applied_by VARCHAR(100),
  status VARCHAR(20) DEFAULT 'success',
  error_message TEXT
);
```

## Integration with Global Config

This migration system is part of the CTB (Collaborative Template Base) structure:
- Pulled from IMO Creator global config
- Follows Barton Doctrine standards
- Integrated with schema validation
- Supports multi-schema databases (marketing, intake, public, bit)

## Status

- **Migrations Directory**: Created ✅
- **Naming Convention**: Defined ✅
- **Auto-run**: Disabled (manual execution) ✅
- **Schema Validation**: Enabled ✅
- **Migration Runner**: Not yet implemented
- **Migration Tracking**: Not yet implemented

## Next Steps

1. Move existing migration from `infra/migrations/` to `ctb/data/migrations/`
2. Create migration tracking table
3. Build automated migration runner (optional)
4. Document all historical migrations

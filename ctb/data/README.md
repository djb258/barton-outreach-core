# Database & Data (data/)

**Barton ID Range**: 05.01.*
**Enforcement**: ORBT (Operation, Repair, Build, Training)

## Purpose
Database schemas, migrations, and data infrastructure for Neon PostgreSQL.

## Key Directories

### `infra/` - Base Schemas
- **Entry Point**: `neon.sql` - Master schema definition
- **Schemas**:
  - `company` - Company master data
  - `people` - People master data
  - `marketing` - Marketing campaigns & outreach
  - `bit` - Business Intelligence Tables
  - `ple` - People Lead Enrichment
- **Files**:
  - `neon.sql` - Complete schema with all tables
  - `neon-company-schema.sql` - Company schema only
  - `cold-outreach-schema.sql` - Outreach-specific tables

### `migrations/` - Schema Changes
- **Format**: `YYYY-MM-DD_description.sql`
- **Subdirectories**:
  - `outreach-process-manager/` - OPM-specific migrations
  - `outreach-process-manager/fixes/` - Hot fixes
- **Key Migrations**:
  - `create_company_master.sql` - Company master table
  - `create_people_master.sql` - People master table
  - `create_attribution_tables.sql` - Attribution tracking
  - `create_scoring_tables.sql` - Lead scoring

### `schemas/` - Schema Definitions
- JSON schema definitions
- Data contracts
- Validation rules

## Database Architecture

### Schema Structure
```
company.* - Company data (domain, name, industry, etc.)
people.* - Person data (name, email, title, LinkedIn, etc.)
marketing.* - Campaign, outreach, attribution
bit.* - Analytics & intelligence
ple.* - Lead enrichment workflows
```

### Master Tables
- `company.master` - Golden record for companies
- `people.master` - Golden record for people
- Both have `slot` tables for staging/validation

### Key Tables

#### Company Schema
- `company.master` - Company master data
- `company.slot` - Staging area for new companies
- `company.history` - Change tracking

#### People Schema
- `people.master` - People master data
- `people.slot` - Staging area for new people
- `people.intelligence` - LinkedIn enrichment data
- `people.history` - Change tracking

#### Marketing Schema
- `marketing.campaigns` - Campaign definitions
- `marketing.outreach_history` - Contact history
- `marketing.attribution` - Conversion tracking
- `marketing.feedback_reports` - Campaign feedback

## Common Tasks

### Apply Migration
```bash
# Using psql
psql $DATABASE_URL -f ctb/data/migrations/2025-10-23_my_migration.sql

# Using Node.js script
node ctb/ai/scripts/run_migrations.js
```

### Verify Schema
```bash
node ctb/ai/scripts/verify-schema.mjs
```

### Generate Schema Diagram
```bash
node ctb/ai/scripts/generate-schema-diagram.mjs > schema.mermaid
```

### Check Schema Compliance
```bash
node ctb/ai/scripts/validate-complete-schema.mjs
```

## Migration Guidelines

### File Naming
```
YYYY-MM-DD_verb_noun.sql
2025-10-23_create_company_master.sql
2025-10-23_add_linkedin_url_to_people.sql
2025-10-23_fix_company_slot_fk.sql
```

### Migration Template
```sql
-- ─────────────────────────────────────────────
-- 📁 CTB Classification Metadata
-- ─────────────────────────────────────────────
-- CTB Branch: data/migrations
-- Barton ID: 05.01.02
-- Unique ID: CTB-XXXXXXXX
-- Last Updated: YYYY-MM-DD
-- Enforcement: ORBT
-- ─────────────────────────────────────────────

-- Description: What this migration does

BEGIN;

-- Your migration SQL here

COMMIT;
```

### Best Practices
1. Always use transactions (BEGIN/COMMIT)
2. Include rollback instructions in comments
3. Test in development first
4. Never drop columns (add deprecated flag instead)
5. Use `IF NOT EXISTS` for idempotency

## Environment Variables
```bash
DATABASE_URL="postgresql://user:pass@host:5432/dbname?sslmode=require"
```

## Dependencies
- **Upstream**: None (data layer is foundation)
- **Downstream**:
  - `ctb/sys/api/` reads from these schemas
  - `ctb/ai/agents/` writes to these schemas
  - `ctb/ui/` displays this data

## Owners
- Schema Design: Data Engineering team
- Migrations: Backend team
- Data Quality: Data team

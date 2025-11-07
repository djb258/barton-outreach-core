# 🚀 MCP Task Execution Runbook

**Project**: Barton Outreach Core - Schema Finalization
**Date**: 2025-11-07
**Executor**: Composio MCP
**Task Registry**: composio_task_registry.json

---

## 📋 Overview

This runbook orchestrates the complete schema finalization process for Barton Outreach Core via Composio MCP. All tasks are dependency-aware and must be executed in the specified order.

**Total Tasks**: 8
**Estimated Duration**: 15-20 minutes
**Prerequisites**: DATABASE_URL environment variable, Composio API key

---

## 🎯 Task Sequence

### Task 1: Verify Neon Dependencies ✅

**ID**: `verify_neon_dependencies`
**Type**: SQL Query
**Priority**: 1
**Dependencies**: None

**Description**: Verify that Neon contains required base tables before shq views can be applied.

**Execution**:
```bash
composio run barton-outreach-core:verify_neon_dependencies
```

**Expected Output**:
```json
{
  "status": "success",
  "tables_found": [
    "intake.audit_log",
    "intake.raw_loads",
    "vault.contacts"
  ],
  "schemas_found": ["intake", "vault", "shq"]
}
```

**Validation**: All required schemas and tables must exist.

**On Failure**:
- Check DATABASE_URL connection
- Verify Neon database is properly initialized
- Run base migrations first

---

### Task 2: Apply SHQ Views ✅

**ID**: `apply_shq_views`
**Type**: Migration
**Priority**: 2
**Dependencies**: `verify_neon_dependencies`

**Description**: Create shq.audit_log and shq.validation_queue views if dependencies are satisfied.

**File**: `ctb/data/migrations/outreach-process-manager/fixes/2025-10-23_create_shq_views.sql`

**Execution**:
```bash
composio run barton-outreach-core:apply_shq_views
```

**What it does**:
- Creates `shq.audit_log` view (aggregates intake.audit_log)
- Creates `shq.validation_queue` view (filters pending validations)
- Adds view documentation

**Validation**:
```sql
SELECT COUNT(*) FROM pg_views WHERE schemaname = 'shq';
-- Expected: 2 (audit_log, validation_queue)
```

**On Failure**:
- Check if Task 1 passed
- Review SQL syntax errors
- Check for conflicting view names

---

### Task 3: Alias People Master Column ✅

**ID**: `alias_people_master`
**Type**: Migration
**Priority**: 3
**Dependencies**: None (independent)

**Description**: Create safe alias for people_master.unique_id → people_unique_id to avoid reserved word conflicts.

**File**: `ctb/data/migrations/outreach-process-manager/fixes/2025-10-23_fix_people_master_column_alias.sql`

**Execution**:
```bash
composio run barton-outreach-core:alias_people_master
```

**What it does**:
- Adds `people_unique_id` column as alias to `unique_id`
- Updates existing queries to use safe column name
- Preserves backward compatibility

**Validation**:
```sql
SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'people'
  AND table_name = 'master'
  AND column_name = 'people_unique_id';
-- Expected: 1 row
```

**On Failure**:
- Check if `people.master` table exists
- Review column naming conflicts
- Check for dependent views/functions

---

### Task 4: Introspect Schema to Manifest ⚠️

**ID**: `introspect_schema`
**Type**: Script
**Priority**: 4
**Dependencies**: `apply_shq_views`, `alias_people_master`

**Description**: Extract live Neon schema and generate doctrine-compliant YAML manifest.

**File**: `ctb/ai/scripts/introspect_neon_to_manifest.cjs` (⚠️ NEEDS CREATION)

**Output**: `ctb/data/infra/NEON_SCHEMA_MANIFEST.yaml`

**Execution**:
```bash
composio run barton-outreach-core:introspect_schema
```

**Script Requirements**:
```javascript
// Must query information_schema and pg_catalog
// Must extract:
// - All schemas
// - All tables with columns (types, constraints, defaults)
// - All views with definitions
// - All functions with signatures
// - All indexes
// - All foreign keys

// Output format (YAML):
schemas:
  - name: intake
    tables:
      - name: raw_loads
        columns: [...]
        indexes: [...]
  - name: vault
    tables: [...]
  - name: shq
    views: [...]
```

**Validation**:
- Output file exists
- Valid YAML syntax
- Contains all expected schemas (intake, vault, company, people, marketing, shq)
- All tables documented with columns

**On Failure**:
- Create script if missing (see template below)
- Check DATABASE_URL permissions (must allow schema introspection)
- Verify output directory exists

---

### Task 5: Verify Schema Alignment ⚠️

**ID**: `verify_schema_alignment`
**Type**: Script
**Priority**: 5
**Dependencies**: `introspect_schema`

**Description**: Compare live Neon schema vs manifest and report drift.

**File**: `ctb/ai/scripts/verify_schema_alignment.cjs` (⚠️ NEEDS CREATION)

**Output**: `ctb/data/infra/SCHEMA_DRIFT_REPORT.md`

**Execution**:
```bash
composio run barton-outreach-core:verify_schema_alignment
```

**Script Requirements**:
```javascript
// Must:
// 1. Load NEON_SCHEMA_MANIFEST.yaml
// 2. Query live database
// 3. Compare:
//    - Missing tables/views
//    - Extra tables/views
//    - Column mismatches (type, nullable, default)
//    - Index mismatches
// 4. Generate markdown report with:
//    - Drift summary
//    - Detailed differences
//    - Recommended actions
```

**Expected Output**:
```markdown
# Schema Drift Report

**Date**: 2025-11-07
**Status**: ✅ No Drift Detected

## Summary
- Tables: 25/25 match
- Views: 8/8 match
- Columns: 347/347 match
- Indexes: 52/52 match

## Details
All schemas are aligned with manifest.
```

**Validation**:
- Drift threshold = 0 (no differences allowed)
- Report must show 100% alignment

**On Failure**:
- Review drift report for specific mismatches
- Run remediation migrations
- Re-run introspection
- Verify manifest is up to date

---

### Task 6: Generate Firestore Schema ⚠️

**ID**: `generate_firestore_schema`
**Type**: Script
**Priority**: 6
**Dependencies**: `introspect_schema`

**Description**: Generate Firestore schema mirror from Neon manifest for Firebase integration.

**File**: `ctb/ai/scripts/generate_firestore_schema.js` (⚠️ NEEDS CREATION)

**Output**: `ctb/data/infra/FIRESTORE_SCHEMA.json`

**Execution**:
```bash
composio run barton-outreach-core:generate_firestore_schema
```

**Script Requirements**:
```javascript
// Must:
// 1. Load NEON_SCHEMA_MANIFEST.yaml
// 2. Transform PostgreSQL types to Firestore types:
//    - text → string
//    - integer → number
//    - boolean → boolean
//    - timestamptz → timestamp
//    - jsonb → map
//    - text[] → array
// 3. Generate Firestore collection structure
// 4. Document indexes and security rules
```

**Expected Output**:
```json
{
  "version": "1.0",
  "collections": {
    "contacts": {
      "fields": {
        "email": { "type": "string", "required": true },
        "name": { "type": "string" },
        "score": { "type": "number" }
      },
      "indexes": [...]
    },
    "campaigns": {...}
  }
}
```

**Validation**:
- Valid JSON format
- All Neon tables mapped to Firestore collections
- Type mappings correct

---

### Task 7: Generate Amplify Schema ⚠️

**ID**: `generate_amplify_schema`
**Type**: Script
**Priority**: 7
**Dependencies**: `introspect_schema`

**Description**: Generate Amplify GraphQL types from Neon manifest for AWS integration.

**File**: `ctb/ai/scripts/neon_to_amplify_schema.js` (⚠️ NEEDS CREATION)

**Output**: `ctb/data/infra/AMPLIFY_TYPES.graphql`

**Execution**:
```bash
composio run barton-outreach-core:generate_amplify_schema
```

**Script Requirements**:
```javascript
// Must:
// 1. Load NEON_SCHEMA_MANIFEST.yaml
// 2. Transform PostgreSQL types to GraphQL types:
//    - text → String
//    - integer → Int
//    - boolean → Boolean
//    - timestamptz → AWSDateTime
//    - jsonb → AWSJSON
//    - uuid → ID
// 3. Generate GraphQL schema with:
//    - Types
//    - Queries
//    - Mutations
//    - Subscriptions
// 4. Add @model, @key, @connection directives
```

**Expected Output**:
```graphql
type Contact @model {
  id: ID!
  email: String! @index(name: "byEmail", queryField: "contactByEmail")
  name: String
  score: Float
  status: String
  createdAt: AWSDateTime
  updatedAt: AWSDateTime
}

type Campaign @model {
  id: ID!
  name: String!
  status: String
  contacts: [Contact] @connection(keyName: "byCampaign", fields: ["id"])
}
```

**Validation**:
- Valid GraphQL syntax
- All Neon tables mapped to GraphQL types
- Proper directives for Amplify

---

### Task 8: Verify Post-Fix ⚠️

**ID**: `verify_postfix`
**Type**: Script
**Priority**: 8
**Dependencies**: All previous tasks

**Description**: Run end-to-end manifest and drift check after all fixes applied. Final verification step.

**File**: `ctb/ai/scripts/run_post_fix_verification.cjs` (⚠️ NEEDS CREATION)

**Execution**:
```bash
composio run barton-outreach-core:verify_postfix
```

**Script Requirements**:
```javascript
// Must verify:
// 1. All migration tasks completed successfully
// 2. NEON_SCHEMA_MANIFEST.yaml exists and is valid
// 3. SCHEMA_DRIFT_REPORT.md shows zero drift
// 4. FIRESTORE_SCHEMA.json generated correctly
// 5. AMPLIFY_TYPES.graphql generated correctly
// 6. All views queryable
// 7. All tables accessible
// 8. No orphaned dependencies

// Generate final report:
// - Task completion status
// - Schema health check
// - Output file validation
// - Next steps
```

**Expected Output**:
```
✅ All 8 tasks completed successfully
✅ Schema manifest generated
✅ Zero drift detected
✅ Firestore schema generated
✅ Amplify types generated
✅ All views operational
✅ Database health: EXCELLENT

🎉 Schema finalization complete!
```

**Validation**:
- All previous tasks show "success" status
- All output files exist and are valid
- No errors in execution logs

**On Failure**:
- Review execution logs for each task
- Re-run failed tasks individually
- Check for partial completions
- Verify all dependencies satisfied

---

## 🔄 Execution Workflow

### Full Chain Execution

```bash
# Run all tasks in sequence with dependency resolution
composio run-chain barton-outreach-core \
  --tasks verify_neon_dependencies,apply_shq_views,alias_people_master,introspect_schema,verify_schema_alignment,generate_firestore_schema,generate_amplify_schema,verify_postfix \
  --stop-on-error
```

### Individual Task Execution (for debugging)

```bash
# Test individual task
composio run barton-outreach-core:verify_neon_dependencies --verbose

# Check task status
composio status barton-outreach-core:verify_neon_dependencies

# View task logs
composio logs barton-outreach-core:verify_neon_dependencies
```

---

## 📊 Progress Tracking

```bash
# Check overall progress
composio progress barton-outreach-core

# Expected output:
# ✅ verify_neon_dependencies (completed)
# ✅ apply_shq_views (completed)
# ✅ alias_people_master (completed)
# ⏳ introspect_schema (running)
# ⏸️ verify_schema_alignment (pending)
# ⏸️ generate_firestore_schema (pending)
# ⏸️ generate_amplify_schema (pending)
# ⏸️ verify_postfix (pending)
```

---

## ⚠️ Missing Files Report

### ✅ Files That Exist

1. **2025-10-23_create_shq_views.sql** (Task 2)
   - Location: `ctb/data/migrations/outreach-process-manager/fixes/`
   - Status: Ready for execution

2. **2025-10-23_fix_people_master_column_alias.sql** (Task 3)
   - Location: `ctb/data/migrations/outreach-process-manager/fixes/`
   - Status: Ready for execution

### ❌ Files That Need Creation

1. **introspect_neon_to_manifest.cjs** (Task 4)
   - Location: `ctb/ai/scripts/`
   - Purpose: Extract live schema to YAML manifest
   - Template: See below

2. **verify_schema_alignment.cjs** (Task 5)
   - Location: `ctb/ai/scripts/`
   - Purpose: Compare manifest vs live and report drift
   - Template: See below

3. **generate_firestore_schema.js** (Task 6)
   - Location: `ctb/ai/scripts/`
   - Purpose: Generate Firestore schema from manifest
   - Template: See below

4. **neon_to_amplify_schema.js** (Task 7)
   - Location: `ctb/ai/scripts/`
   - Purpose: Generate Amplify GraphQL types from manifest
   - Template: See below

5. **run_post_fix_verification.cjs** (Task 8)
   - Location: `ctb/ai/scripts/`
   - Purpose: Final end-to-end verification
   - Template: See below

---

## 🛠️ Script Templates

### Template: introspect_neon_to_manifest.cjs

```javascript
#!/usr/bin/env node
/**
 * CTB Metadata
 * Barton ID: 03.01.XX.20251023.xxxx.001
 * Branch: ai
 * Altitude: 30k (HEIR)
 * Purpose: Introspect Neon PostgreSQL schema and generate YAML manifest
 */

const { Client } = require('pg');
const yaml = require('yaml');
const fs = require('fs');

const DATABASE_URL = process.env.DATABASE_URL;
if (!DATABASE_URL) {
  console.error('❌ DATABASE_URL environment variable required');
  process.exit(1);
}

async function introspectSchema() {
  const client = new Client({ connectionString: DATABASE_URL });
  await client.connect();

  console.log('🔍 Introspecting Neon schema...');

  // Query all schemas
  const schemas = await client.query(`
    SELECT schema_name
    FROM information_schema.schemata
    WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
    ORDER BY schema_name
  `);

  const manifest = {
    version: '1.0',
    generated: new Date().toISOString(),
    schemas: []
  };

  for (const schemaRow of schemas.rows) {
    const schemaName = schemaRow.schema_name;
    console.log(`  Introspecting schema: ${schemaName}`);

    // Get tables
    const tables = await client.query(`
      SELECT table_name
      FROM information_schema.tables
      WHERE table_schema = $1 AND table_type = 'BASE TABLE'
      ORDER BY table_name
    `, [schemaName]);

    // Get views
    const views = await client.query(`
      SELECT table_name
      FROM information_schema.views
      WHERE table_schema = $1
      ORDER BY table_name
    `, [schemaName]);

    const schemaObj = {
      name: schemaName,
      tables: [],
      views: []
    };

    // Process each table
    for (const tableRow of tables.rows) {
      const tableName = tableRow.table_name;

      // Get columns
      const columns = await client.query(`
        SELECT
          column_name,
          data_type,
          is_nullable,
          column_default
        FROM information_schema.columns
        WHERE table_schema = $1 AND table_name = $2
        ORDER BY ordinal_position
      `, [schemaName, tableName]);

      schemaObj.tables.push({
        name: tableName,
        columns: columns.rows
      });
    }

    // Process each view
    for (const viewRow of views.rows) {
      schemaObj.views.push({ name: viewRow.table_name });
    }

    manifest.schemas.push(schemaObj);
  }

  await client.end();

  // Write manifest
  const outputPath = 'ctb/data/infra/NEON_SCHEMA_MANIFEST.yaml';
  fs.writeFileSync(outputPath, yaml.stringify(manifest));
  console.log(`✅ Schema manifest written to ${outputPath}`);
  console.log(`   Schemas: ${manifest.schemas.length}`);
}

introspectSchema().catch(err => {
  console.error('❌ Error:', err.message);
  process.exit(1);
});
```

---

## 📝 Pre-Execution Checklist

Before running the task chain:

- [ ] DATABASE_URL environment variable set
- [ ] Composio API key configured
- [ ] All migration files exist (Tasks 2-3)
- [ ] Create missing scripts (Tasks 4-8) or skip if not needed
- [ ] Output directories exist:
  - [ ] `ctb/data/infra/`
  - [ ] `ctb/ai/mcp-tasks/execution_logs/`
- [ ] Database connection verified
- [ ] Adequate disk space for logs and outputs

---

## 🎯 Success Criteria

All tasks complete when:

1. ✅ All 8 tasks show "completed" status
2. ✅ Zero drift in schema alignment report
3. ✅ All output files generated and valid
4. ✅ No errors in execution logs
5. ✅ Final verification passes all checks

---

## 📞 Support & Troubleshooting

### Common Issues

**Issue**: Task fails with "file not found"
**Solution**: Check `file_status` in composio_task_registry.json, create missing files

**Issue**: Database connection timeout
**Solution**: Verify DATABASE_URL, check Neon service status, increase timeout

**Issue**: Permission denied on output directory
**Solution**: Create directories with `mkdir -p ctb/data/infra`

**Issue**: Drift detected in alignment check
**Solution**: Run remediation migrations, re-run introspection

### Logs Location

```
ctb/ai/mcp-tasks/execution_logs/
  ├── verify_neon_dependencies.log
  ├── apply_shq_views.log
  ├── alias_people_master.log
  ├── introspect_schema.log
  ├── verify_schema_alignment.log
  ├── generate_firestore_schema.log
  ├── generate_amplify_schema.log
  └── verify_postfix.log
```

---

**Last Updated**: 2025-11-07
**Maintained By**: AI Automation Team
**Related**: composio_task_registry.json, CTB_ENFORCEMENT.md

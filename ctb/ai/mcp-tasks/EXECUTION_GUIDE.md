# 🚀 Schema Finalization Execution Guide

**Status**: ✅ All scripts created and ready for execution
**Date**: 2025-11-07
**Task Chain**: 8 tasks (Migrations → Introspection → Verification → Schema Generation)

---

## Prerequisites

### 1. Environment Setup

```bash
# Set your Neon database URL
export DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require"

# Verify it's set
echo $DATABASE_URL
```

### 2. Install Dependencies

```bash
# Navigate to scripts directory
cd ctb/ai/scripts

# Install required npm packages
npm install pg@^8.11.0 yaml@^2.3.0
```

---

## Execution Order

### Option A: Manual Execution (Recommended for first run)

Execute scripts in this exact order:

#### **Step 1: Run Migrations** (Tasks 2-3)

```bash
# Option 1a: Using psql directly
psql $DATABASE_URL -f ctb/data/migrations/outreach-process-manager/fixes/2025-10-23_create_shq_views.sql
psql $DATABASE_URL -f ctb/data/migrations/outreach-process-manager/fixes/2025-10-23_fix_people_master_column_alias.sql

# Option 1b: Using Composio (if configured)
composio run barton-outreach-core:verify_neon_dependencies
composio run barton-outreach-core:apply_shq_views
composio run barton-outreach-core:alias_people_master
```

**Expected Output**:
- ✅ `shq.audit_log` and `shq.validation_queue` views created
- ✅ `people.master.people_unique_id` column alias created

---

#### **Step 2: Introspect Database Schema** (Task 4)

```bash
cd ctb/ai/scripts
node introspect_neon_to_manifest.cjs
```

**Expected Output**:
- ✅ File created: `ctb/data/infra/NEON_SCHEMA_MANIFEST.yaml`
- ✅ Contains all schemas, tables, views, functions, columns, indexes, foreign keys

**Verify**:
```bash
ls -lh ../../data/infra/NEON_SCHEMA_MANIFEST.yaml
head -20 ../../data/infra/NEON_SCHEMA_MANIFEST.yaml
```

---

#### **Step 3: Verify Schema Alignment** (Task 5)

```bash
node verify_schema_alignment.cjs
```

**Expected Output**:
- ✅ File created: `ctb/data/infra/SCHEMA_DRIFT_REPORT.md`
- ✅ Exit code 0 (no drift) or 1 (drift detected)

**Verify**:
```bash
cat ../../data/infra/SCHEMA_DRIFT_REPORT.md | grep "Total Drifts"
```

**Expected**: `**Total Drifts:** 0` (ideal) or review drift details if > 0

---

#### **Step 4: Generate Firestore Schema** (Task 6)

```bash
node generate_firestore_schema.js
```

**Expected Output**:
- ✅ File created: `ctb/data/infra/FIRESTORE_SCHEMA.json`
- ✅ All PostgreSQL types transformed to Firestore types

**Verify**:
```bash
cat ../../data/infra/FIRESTORE_SCHEMA.json | jq '.collections | length'
```

---

#### **Step 5: Generate Amplify GraphQL Schema** (Task 7)

```bash
node neon_to_amplify_schema.js
```

**Expected Output**:
- ✅ File created: `ctb/data/infra/AMPLIFY_TYPES.graphql`
- ✅ All tables converted to GraphQL types with `@model`, `@key`, `@connection` directives

**Verify**:
```bash
grep -c "type " ../../data/infra/AMPLIFY_TYPES.graphql
grep -c "@model" ../../data/infra/AMPLIFY_TYPES.graphql
```

---

#### **Step 6: Run Post-Fix Verification** (Task 8)

```bash
node run_post_fix_verification.cjs
```

**Expected Output**:
- ✅ All environment checks pass
- ✅ All files exist
- ✅ Database connectivity verified
- ✅ All schemas and views exist
- ✅ Output formats validated
- ✅ Zero drift (or warnings if drift detected)

**Exit Codes**:
- `0` = All checks passed
- `1` = Critical failures detected

---

### Option B: Automated Execution (via Composio)

**Prerequisites**: Composio CLI installed and configured

```bash
# Install Composio CLI
npm install -g composio-cli

# Authenticate
composio login

# Add Neon integration
composio add neon
composio auth neon --env DATABASE_URL

# Register task chain
composio register --file ctb/ai/mcp-tasks/composio_task_registry.json

# Execute full chain (stops on first error)
composio run-chain barton-outreach-core --stop-on-error
```

**Task Chain Order**:
1. `verify_neon_dependencies` (SQL query)
2. `apply_shq_views` (migration)
3. `alias_people_master` (migration)
4. `introspect_schema` (script)
5. `verify_schema_alignment` (script)
6. `generate_firestore_schema` (script)
7. `generate_amplify_schema` (script)
8. `verify_postfix` (script)

---

## Expected Final Outputs

After successful execution, you should have these files:

```
ctb/data/infra/
├── NEON_SCHEMA_MANIFEST.yaml       ✅ Complete database schema snapshot
├── SCHEMA_DRIFT_REPORT.md          ✅ Drift analysis (0 drifts = perfect)
├── FIRESTORE_SCHEMA.json           ✅ Firestore collection definitions
└── AMPLIFY_TYPES.graphql           ✅ AWS Amplify GraphQL schema
```

---

## Validation Checklist

After execution, verify:

- [ ] All 4 output files exist in `ctb/data/infra/`
- [ ] `NEON_SCHEMA_MANIFEST.yaml` contains all expected schemas
- [ ] `SCHEMA_DRIFT_REPORT.md` shows **0 drifts** (or acceptable drift)
- [ ] `FIRESTORE_SCHEMA.json` is valid JSON with collections array
- [ ] `AMPLIFY_TYPES.graphql` contains `type` definitions with `@model`
- [ ] Post-fix verification script exits with code 0
- [ ] Database has `shq.audit_log` and `shq.validation_queue` views
- [ ] Database has `people.master.people_unique_id` column

---

## Troubleshooting

### Error: "DATABASE_URL environment variable is required"

**Fix**:
```bash
export DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require"
```

---

### Error: "Cannot find module 'pg'"

**Fix**:
```bash
cd ctb/ai/scripts
npm install pg yaml
```

---

### Error: "Manifest not found"

**Cause**: Scripts must run in order. Task 5-7 depend on Task 4.

**Fix**: Run `introspect_neon_to_manifest.cjs` first.

---

### Drift Detected (Exit code 1 from verify_schema_alignment.cjs)

**Review**: Check `SCHEMA_DRIFT_REPORT.md` for details.

**Common Drifts**:
- Missing schemas: Create schema in database
- Extra schemas: Expected (e.g., `pg_catalog`, `information_schema`)
- Column type mismatch: Update manifest or database
- Missing views: Re-run migrations

**Remediation**:
1. Review drift report
2. Fix database schema or update manifest
3. Re-run introspection and verification

---

### Permission Denied Errors

**Cause**: Database user lacks schema introspection permissions.

**Fix**: Verify user has `SELECT` on `information_schema` and `pg_catalog`:
```sql
GRANT SELECT ON ALL TABLES IN SCHEMA information_schema TO your_user;
GRANT SELECT ON ALL TABLES IN SCHEMA pg_catalog TO your_user;
```

---

## Next Steps After Successful Execution

1. **Commit Generated Files**:
   ```bash
   git add ctb/data/infra/*.yaml ctb/data/infra/*.json ctb/data/infra/*.graphql ctb/data/infra/*.md
   git commit -m "Add schema finalization outputs (manifest, drift report, Firestore, Amplify)"
   git push
   ```

2. **Review Drift Report**: If any drifts detected, plan remediation.

3. **Use Schema Outputs**:
   - **Firestore**: Import `FIRESTORE_SCHEMA.json` for NoSQL migration
   - **Amplify**: Use `AMPLIFY_TYPES.graphql` in AWS Amplify projects
   - **Manifest**: Reference `NEON_SCHEMA_MANIFEST.yaml` for documentation

4. **Schedule Regular Introspection**: Add weekly cron job to detect schema drift:
   ```bash
   # Add to crontab
   0 0 * * 0 cd /path/to/ctb/ai/scripts && node introspect_neon_to_manifest.cjs && node verify_schema_alignment.cjs
   ```

---

## Script Reference

| Script | Purpose | Dependencies | Output |
|--------|---------|--------------|--------|
| `introspect_neon_to_manifest.cjs` | Extract live schema | DATABASE_URL, pg, yaml | `NEON_SCHEMA_MANIFEST.yaml` |
| `verify_schema_alignment.cjs` | Detect schema drift | DATABASE_URL, manifest | `SCHEMA_DRIFT_REPORT.md` |
| `generate_firestore_schema.js` | Transform to Firestore | manifest, yaml | `FIRESTORE_SCHEMA.json` |
| `neon_to_amplify_schema.js` | Transform to GraphQL | manifest, yaml | `AMPLIFY_TYPES.graphql` |
| `run_post_fix_verification.cjs` | End-to-end validation | All outputs, DATABASE_URL | Console report + exit code |

---

## Performance Notes

**Execution Time** (estimated):
- Migrations: 5-10 seconds
- Introspection: 30-60 seconds (depends on schema size)
- Verification: 30-60 seconds
- Firestore generation: 5-10 seconds
- Amplify generation: 5-10 seconds
- Post-fix verification: 15-30 seconds

**Total**: ~2-3 minutes for full execution

---

## Support

**Documentation**:
- Detailed runbook: `ctb/ai/mcp-tasks/MCP_RUNBOOK.md`
- Task registry: `ctb/ai/mcp-tasks/composio_task_registry.json`
- Status report: `ctb/ai/mcp-tasks/TASK_STATUS_REPORT.md`

**Related Files**:
- Migrations: `ctb/data/migrations/outreach-process-manager/fixes/2025-10-23_*.sql`
- Scripts: `ctb/ai/scripts/*.cjs`, `ctb/ai/scripts/*.js`

---

**Last Updated**: 2025-11-07
**Version**: 1.0
**Status**: ✅ Ready for execution

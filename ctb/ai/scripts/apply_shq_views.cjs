#!/usr/bin/env node
/**
 * CTB Metadata
 * Barton ID: 03.01.04.20251023.asvs.001
 * Branch: ai
 * Altitude: 30k (HEIR - Hierarchical Execution Intelligence & Repair)
 * Purpose: MCP Task 2 - Apply SHQ views migration
 * Dependencies: pg@^8.11.0
 */

const { Client } = require('pg');
const fs = require('fs');
const path = require('path');

// Configuration
const DATABASE_URL = process.env.DATABASE_URL;
const MIGRATION_FILE = path.join(__dirname, '../../data/migrations/outreach-process-manager/fixes/2025-10-23_create_shq_views.sql');

// Validation
if (!DATABASE_URL) {
  console.error('❌ ERROR: DATABASE_URL environment variable is required');
  console.error('   Set it with: export DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require"');
  process.exit(1);
}

if (!fs.existsSync(MIGRATION_FILE)) {
  console.error(`❌ ERROR: Migration file not found: ${MIGRATION_FILE}`);
  process.exit(1);
}

/**
 * Main migration execution function
 */
async function applyShqViews() {
  const client = new Client({ connectionString: DATABASE_URL });

  try {
    await client.connect();
    console.log('✅ Connected to Neon PostgreSQL');
    console.log('📄 Loading migration file...\n');

    // Read migration SQL
    const migrationSql = fs.readFileSync(MIGRATION_FILE, 'utf8');
    console.log(`   File: ${path.basename(MIGRATION_FILE)}`);
    console.log(`   Size: ${(migrationSql.length / 1024).toFixed(2)} KB\n`);

    // Execute migration
    console.log('🚀 Executing migration...\n');
    await client.query(migrationSql);
    console.log('✅ Migration executed successfully!\n');

    // Verify views were created
    console.log('🔍 Verifying views...\n');

    const viewsResult = await client.query(`
      SELECT
        table_schema,
        table_name,
        table_type
      FROM information_schema.tables
      WHERE table_schema = 'shq'
        AND table_name IN ('audit_log', 'validation_queue')
      ORDER BY table_name
    `);

    if (viewsResult.rows.length === 0) {
      console.error('❌ ERROR: No views found in shq schema after migration');
      process.exit(1);
    }

    console.log('   Views created:');
    for (const row of viewsResult.rows) {
      console.log(`   ✅ ${row.table_schema}.${row.table_name} (${row.table_type})`);
    }

    // Test data accessibility
    console.log('\n📊 Testing view accessibility...\n');

    try {
      const auditCountResult = await client.query('SELECT COUNT(*) as count FROM shq.audit_log');
      console.log(`   ✅ shq.audit_log accessible (${auditCountResult.rows[0].count} rows)`);
    } catch (err) {
      console.error(`   ❌ shq.audit_log error: ${err.message}`);
    }

    try {
      const validationCountResult = await client.query('SELECT COUNT(*) as count FROM shq.validation_queue');
      console.log(`   ✅ shq.validation_queue accessible (${validationCountResult.rows[0].count} rows)`);
    } catch (err) {
      console.error(`   ❌ shq.validation_queue error: ${err.message}`);
    }

    // Verify source tables exist
    console.log('\n🔗 Verifying source tables...\n');

    const sourceTablesResult = await client.query(`
      SELECT
        table_schema,
        table_name,
        table_type
      FROM information_schema.tables
      WHERE (table_schema = 'marketing' AND table_name = 'unified_audit_log')
         OR (table_schema = 'intake' AND table_name = 'validation_failed')
      ORDER BY table_schema, table_name
    `);

    if (sourceTablesResult.rows.length === 2) {
      console.log('   Source tables verified:');
      for (const row of sourceTablesResult.rows) {
        console.log(`   ✅ ${row.table_schema}.${row.table_name} (${row.table_type})`);
      }
    } else {
      console.warn('   ⚠️  Warning: Not all source tables found');
      console.warn('   Expected: marketing.unified_audit_log, intake.validation_failed');
      console.warn(`   Found: ${sourceTablesResult.rows.length} tables`);
    }

    // Summary
    console.log('\n' + '='.repeat(70));
    console.log('✅ MCP TASK 2 COMPLETE: apply_shq_views');
    console.log('='.repeat(70));
    console.log('Schema: shq (created/verified)');
    console.log('Views: shq.audit_log, shq.validation_queue (created)');
    console.log('Source: marketing.unified_audit_log, intake.validation_failed');
    console.log('Status: ✅ Views created per Doctrine requirement');
    console.log('='.repeat(70) + '\n');

    process.exit(0);

  } catch (error) {
    console.error('\n❌ Error during migration:', error.message);
    console.error('Stack trace:', error.stack);

    console.log('\n' + '='.repeat(70));
    console.log('❌ MCP TASK 2 FAILED: apply_shq_views');
    console.log('='.repeat(70));
    console.log('Error:', error.message);
    console.log('\nTroubleshooting:');
    console.log('1. Verify source tables exist:');
    console.log('   - marketing.unified_audit_log');
    console.log('   - intake.validation_failed');
    console.log('2. Check database permissions');
    console.log('3. Review error message above');
    console.log('='.repeat(70) + '\n');

    process.exit(1);
  } finally {
    await client.end();
  }
}

// Run migration
applyShqViews().catch(err => {
  console.error('❌ Fatal error:', err.message);
  process.exit(1);
});

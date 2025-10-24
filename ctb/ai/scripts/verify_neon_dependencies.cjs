#!/usr/bin/env node
/**
 * CTB Metadata
 * Barton ID: 03.01.04.20251023.vndc.001
 * Branch: ai
 * Altitude: 30k (HEIR - Hierarchical Execution Intelligence & Repair)
 * Purpose: MCP Task 1 - Verify Neon dependencies before applying SHQ views
 * Dependencies: pg@^8.11.0
 */

const { Client } = require('pg');

// Configuration
const DATABASE_URL = process.env.DATABASE_URL;

// Validation
if (!DATABASE_URL) {
  console.error('❌ ERROR: DATABASE_URL environment variable is required');
  console.error('   Set it with: export DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require"');
  process.exit(1);
}

/**
 * Main verification function
 */
async function verifyNeonDependencies() {
  const client = new Client({ connectionString: DATABASE_URL });

  try {
    await client.connect();
    console.log('✅ Connected to Neon PostgreSQL');
    console.log('🔍 Starting dependency verification...\n');

    const results = {
      passed: 0,
      failed: 0,
      tables: {},
      schemas: {}
    };

    // Check required schemas
    console.log('📁 Checking required schemas...');
    const requiredSchemas = ['intake', 'vault', 'shq', 'marketing'];

    for (const schema of requiredSchemas) {
      const schemaResult = await client.query(`
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name = $1
      `, [schema]);

      if (schemaResult.rows.length > 0) {
        console.log(`   ✅ Schema '${schema}' exists`);
        results.schemas[schema] = true;
        results.passed++;
      } else {
        console.error(`   ❌ Schema '${schema}' NOT FOUND`);
        results.schemas[schema] = false;
        results.failed++;
      }
    }

    console.log('\n📊 Checking required tables...');

    // Check marketing.unified_audit_log
    const marketingAuditResult = await client.query(`
      SELECT table_name
      FROM information_schema.tables
      WHERE table_schema = 'marketing' AND table_name = 'unified_audit_log'
    `);

    if (marketingAuditResult.rows.length > 0) {
      console.log('   ✅ marketing.unified_audit_log exists');
      results.tables['marketing.unified_audit_log'] = true;
      results.passed++;
    } else {
      console.error('   ❌ marketing.unified_audit_log NOT FOUND');
      results.tables['marketing.unified_audit_log'] = false;
      results.failed++;
    }

    // Check intake.validation_failed
    const intakeValidationResult = await client.query(`
      SELECT table_name
      FROM information_schema.tables
      WHERE table_schema = 'intake' AND table_name = 'validation_failed'
    `);

    if (intakeValidationResult.rows.length > 0) {
      console.log('   ✅ intake.validation_failed exists');
      results.tables['intake.validation_failed'] = true;
      results.passed++;
    } else {
      console.error('   ❌ intake.validation_failed NOT FOUND');
      results.tables['intake.validation_failed'] = false;
      results.failed++;
    }

    // Check additional required tables from registry
    const additionalTables = [
      { schema: 'intake', table: 'audit_log' },
      { schema: 'intake', table: 'raw_loads' },
      { schema: 'vault', table: 'contacts' }
    ];

    for (const { schema, table } of additionalTables) {
      const tableResult = await client.query(`
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = $1 AND table_name = $2
      `, [schema, table]);

      const fullName = `${schema}.${table}`;
      if (tableResult.rows.length > 0) {
        console.log(`   ✅ ${fullName} exists`);
        results.tables[fullName] = true;
        results.passed++;
      } else {
        console.error(`   ❌ ${fullName} NOT FOUND`);
        results.tables[fullName] = false;
        results.failed++;
      }
    }

    // Summary
    console.log('\n' + '='.repeat(60));
    console.log('📊 VERIFICATION SUMMARY');
    console.log('='.repeat(60));
    console.log(`✅ Passed: ${results.passed}`);
    console.log(`❌ Failed: ${results.failed}`);
    console.log(`📈 Total: ${results.passed + results.failed}`);
    console.log('='.repeat(60));

    if (results.failed === 0) {
      console.log('\n✅ All dependencies verified - Ready to apply SHQ views!\n');
      process.exit(0);
    } else {
      console.log('\n❌ Missing dependencies - Cannot apply SHQ views yet\n');
      console.log('Required Actions:');
      console.log('1. Create missing schemas and tables');
      console.log('2. Run migrations if available');
      console.log('3. Re-run this verification\n');
      process.exit(1);
    }

  } catch (error) {
    console.error('\n❌ Error during verification:', error.message);
    console.error('Stack trace:', error.stack);
    process.exit(1);
  } finally {
    await client.end();
  }
}

// Run verification
verifyNeonDependencies().catch(err => {
  console.error('❌ Fatal error:', err.message);
  process.exit(1);
});

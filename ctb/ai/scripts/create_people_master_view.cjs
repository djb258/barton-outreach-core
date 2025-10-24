#!/usr/bin/env node
/**
 * CTB Metadata
 * Barton ID: 03.01.04.20251023.cpmv.001
 * Branch: ai
 * Altitude: 30k (HEIR - Hierarchical Execution Intelligence & Repair)
 * Purpose: MCP Task 3 (Option A) - Create non-breaking people_master view with alias
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
 * Main view creation function
 */
async function createPeopleMasterView() {
  const client = new Client({ connectionString: DATABASE_URL });

  try {
    await client.connect();
    console.log('✅ Connected to Neon PostgreSQL');
    console.log('🔧 Creating people_master view with alias...\n');

    // Create view with alias (non-breaking)
    const viewSql = `
      CREATE OR REPLACE VIEW marketing.people_master_v AS
      SELECT
        *,
        unique_id AS people_unique_id
      FROM marketing.people_master;
    `;

    await client.query(viewSql);
    console.log('✅ View created: marketing.people_master_v\n');

    // Add comment
    await client.query(`
      COMMENT ON VIEW marketing.people_master_v IS
        'Non-breaking view created 2025-10-23 for Doctrine compliance.
        Aliases unique_id as people_unique_id without modifying base table.
        Use this view for new code; old code continues to work with people_master.unique_id';
    `);

    // Verify view
    console.log('🔍 Verifying view...\n');

    const verifyResult = await client.query(`
      SELECT
        table_schema,
        table_name,
        table_type
      FROM information_schema.tables
      WHERE table_schema = 'marketing'
        AND table_name = 'people_master_v'
    `);

    if (verifyResult.rows.length > 0) {
      console.log('   ✅ marketing.people_master_v (VIEW) exists');
    } else {
      console.error('   ❌ View not found after creation');
      process.exit(1);
    }

    // Test data access
    console.log('\n📊 Testing view accessibility...\n');

    const testResult = await client.query('SELECT * FROM marketing.people_master_v LIMIT 5');
    console.log(`   ✅ View accessible (${testResult.rows.length} rows returned)`);

    // Check for people_unique_id column
    const columnsResult = await client.query(`
      SELECT column_name
      FROM information_schema.columns
      WHERE table_schema = 'marketing'
        AND table_name = 'people_master_v'
        AND column_name = 'people_unique_id'
    `);

    if (columnsResult.rows.length > 0) {
      console.log('   ✅ people_unique_id column exists in view');
    } else {
      console.error('   ❌ people_unique_id column not found');
    }

    // Summary
    console.log('\n' + '='.repeat(70));
    console.log('✅ MCP TASK 3 COMPLETE: alias_people_master (Option A)');
    console.log('='.repeat(70));
    console.log('Approach: Non-breaking view');
    console.log('View: marketing.people_master_v');
    console.log('Alias: unique_id → people_unique_id');
    console.log('Breaking Changes: None');
    console.log('Old Code Impact: No changes required');
    console.log('New Code: Use marketing.people_master_v.people_unique_id');
    console.log('='.repeat(70) + '\n');

    process.exit(0);

  } catch (error) {
    console.error('\n❌ Error creating view:', error.message);
    console.error('Stack trace:', error.stack);

    console.log('\n' + '='.repeat(70));
    console.log('❌ MCP TASK 3 FAILED: alias_people_master');
    console.log('='.repeat(70));
    console.log('Error:', error.message);
    console.log('\nTroubleshooting:');
    console.log('1. Verify marketing.people_master table exists');
    console.log('2. Verify unique_id column exists in people_master');
    console.log('3. Check database permissions');
    console.log('='.repeat(70) + '\n');

    process.exit(1);
  } finally {
    await client.end();
  }
}

// Run view creation
createPeopleMasterView().catch(err => {
  console.error('❌ Fatal error:', err.message);
  process.exit(1);
});

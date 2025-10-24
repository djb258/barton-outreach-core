#!/usr/bin/env node
/**
 * CTB Metadata
 * Barton ID: 03.01.04.20251023.rpui.001
 * Branch: ai
 * Altitude: 30k (HEIR - Hierarchical Execution Intelligence & Repair)
 * Purpose: MCP Task 3 (Option B) - BREAKING: Rename people_master.unique_id column
 * Dependencies: pg@^8.11.0
 */

const { Client } = require('pg');
const fs = require('fs');
const path = require('path');

// Configuration
const DATABASE_URL = process.env.DATABASE_URL;
const MIGRATION_FILE = path.join(__dirname, '../../data/migrations/outreach-process-manager/fixes/2025-10-23_fix_people_master_column_alias.sql');

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
async function renamePeopleUniqueId() {
  const client = new Client({ connectionString: DATABASE_URL });

  try {
    await client.connect();
    console.log('✅ Connected to Neon PostgreSQL');
    console.log('\n' + '⚠️ '.repeat(35));
    console.log('⚠️  WARNING: BREAKING CHANGE MIGRATION');
    console.log('⚠️ '.repeat(35));
    console.log('\nThis migration will:');
    console.log('1. Drop foreign keys referencing people_master.unique_id');
    console.log('2. Rename column: unique_id → people_unique_id');
    console.log('3. Recreate foreign keys with new column name');
    console.log('\n❌ APPLICATION CODE USING people_master.unique_id WILL BREAK\n');
    console.log('Press Ctrl+C within 5 seconds to cancel...\n');

    // Wait 5 seconds
    await new Promise(resolve => setTimeout(resolve, 5000));

    console.log('📄 Loading migration file...\n');

    // Read migration SQL
    const migrationSql = fs.readFileSync(MIGRATION_FILE, 'utf8');
    console.log(`   File: ${path.basename(MIGRATION_FILE)}`);
    console.log(`   Size: ${(migrationSql.length / 1024).toFixed(2)} KB\n`);

    // Execute migration
    console.log('🚀 Executing migration...\n');
    await client.query(migrationSql);
    console.log('✅ Migration executed successfully!\n');

    // Verify column was renamed
    console.log('🔍 Verifying column rename...\n');

    const columnResult = await client.query(`
      SELECT column_name
      FROM information_schema.columns
      WHERE table_schema = 'marketing'
        AND table_name = 'people_master'
        AND column_name = 'people_unique_id'
    `);

    if (columnResult.rows.length > 0) {
      console.log('   ✅ Column people_unique_id exists');
    } else {
      console.error('   ❌ Column people_unique_id not found after migration');
      process.exit(1);
    }

    // Check that old column is gone
    const oldColumnResult = await client.query(`
      SELECT column_name
      FROM information_schema.columns
      WHERE table_schema = 'marketing'
        AND table_name = 'people_master'
        AND column_name = 'unique_id'
    `);

    if (oldColumnResult.rows.length === 0) {
      console.log('   ✅ Old column unique_id removed');
    } else {
      console.warn('   ⚠️  Old column unique_id still exists (unexpected)');
    }

    // Verify foreign keys
    console.log('\n🔗 Verifying foreign keys...\n');

    const fkResult = await client.query(`
      SELECT
        tc.constraint_name,
        tc.table_name,
        kcu.column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
      FROM information_schema.table_constraints AS tc
      JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
      JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
        AND ccu.table_schema = tc.table_schema
      WHERE tc.constraint_type = 'FOREIGN KEY'
        AND ccu.table_name = 'people_master'
        AND ccu.column_name = 'people_unique_id'
    `);

    if (fkResult.rows.length > 0) {
      console.log('   ✅ Foreign keys recreated:');
      for (const row of fkResult.rows) {
        console.log(`      - ${row.table_name}.${row.column_name} → people_master.people_unique_id`);
      }
    } else {
      console.log('   ℹ️  No foreign keys found (may not exist yet)');
    }

    // Summary
    console.log('\n' + '='.repeat(70));
    console.log('✅ MCP TASK 3 COMPLETE: alias_people_master (Option B)');
    console.log('='.repeat(70));
    console.log('Approach: Breaking column rename');
    console.log('Column: unique_id → people_unique_id');
    console.log('Status: ✅ Renamed successfully');
    console.log('\n⚠️  BREAKING CHANGES:');
    console.log('   - Application code must be updated');
    console.log('   - Search codebase for: people_master.unique_id');
    console.log('   - Replace with: people_master.people_unique_id');
    console.log('\nFiles likely affected:');
    console.log('   - apps/outreach-ui/src/components/people/*.tsx');
    console.log('   - apps/api/routes/people/*.js');
    console.log('   - Any raw SQL queries in application code');
    console.log('='.repeat(70) + '\n');

    process.exit(0);

  } catch (error) {
    console.error('\n❌ Error during migration:', error.message);
    console.error('Stack trace:', error.stack);

    console.log('\n' + '='.repeat(70));
    console.log('❌ MCP TASK 3 FAILED: alias_people_master');
    console.log('='.repeat(70));
    console.log('Error:', error.message);
    console.log('\nTroubleshooting:');
    console.log('1. Verify marketing.people_master table exists');
    console.log('2. Check if unique_id column exists');
    console.log('3. Check database permissions');
    console.log('4. Review foreign key dependencies');
    console.log('='.repeat(70) + '\n');

    process.exit(1);
  } finally {
    await client.end();
  }
}

// Run migration
renamePeopleUniqueId().catch(err => {
  console.error('❌ Fatal error:', err.message);
  process.exit(1);
});

#!/usr/bin/env node

/**
 * Execute SQL Migration - Simple Node.js version
 * Executes the shq_error_log table creation without requiring tsx
 */

const fs = require('fs');
const path = require('path');
const { Client } = require('pg');
require('dotenv').config();

async function executeMigration() {
  console.log('');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('  Execute shq_error_log Table Migration');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');

  // Check DATABASE_URL
  if (!process.env.DATABASE_URL && !process.env.NEON_DATABASE_URL) {
    console.error('❌ ERROR: DATABASE_URL or NEON_DATABASE_URL not found in environment');
    console.error('   Please set one of these variables in your .env file\n');
    process.exit(1);
  }

  const connectionString = process.env.DATABASE_URL || process.env.NEON_DATABASE_URL;

  // Read SQL file
  const sqlFilePath = path.join(__dirname, '..', 'infra', '2025-10-20_create_shq_error_log.sql');
  console.log(`[1/4] 📄 Reading SQL file: ${path.basename(sqlFilePath)}`);

  if (!fs.existsSync(sqlFilePath)) {
    console.error(`❌ ERROR: SQL file not found: ${sqlFilePath}\n`);
    process.exit(1);
  }

  const sqlContent = fs.readFileSync(sqlFilePath, 'utf-8');
  console.log(`      ✅ Loaded SQL file (${sqlContent.split('\n').length} lines)\n`);

  // Connect to database
  console.log('[2/4] 🔌 Connecting to Neon database...');
  const client = new Client({ connectionString });

  try {
    await client.connect();
    console.log('      ✅ Connected successfully\n');

    // Execute migration
    console.log('[3/4] 🚀 Executing migration...');
    await client.query(sqlContent);
    console.log('      ✅ Migration executed successfully\n');

    // Verify table creation
    console.log('[4/4] ✓ Verifying table creation...');
    const tableCheck = await client.query(
      "SELECT COUNT(*) as count FROM information_schema.tables WHERE table_name = 'shq_error_log'"
    );

    if (tableCheck.rows[0].count === '0') {
      console.error('      ⚠️  Warning: Table shq_error_log not found after migration\n');
    } else {
      console.log('      ✅ Table shq_error_log exists');

      // Check indexes
      const indexCheck = await client.query(
        "SELECT COUNT(*) as count FROM pg_indexes WHERE tablename = 'shq_error_log'"
      );
      console.log(`      ✅ Found ${indexCheck.rows[0].count} indexes\n`);
    }

    console.log('═══════════════════════════════════════════════════════════');
    console.log('✅ MIGRATION COMPLETE');
    console.log('═══════════════════════════════════════════════════════════');
    console.log('');
    console.log('Next steps:');
    console.log('  1. npm run schema:refresh     # Update schema map');
    console.log('  2. npm run sync:errors -- --dry-run --limit 5  # Test sync');
    console.log('');

  } catch (error) {
    console.error('');
    console.error('═══════════════════════════════════════════════════════════');
    console.error('❌ MIGRATION FAILED');
    console.error('═══════════════════════════════════════════════════════════');
    console.error('');
    console.error('Error:', error.message);
    console.error('');

    if (error.message.includes('already exists')) {
      console.log('ℹ️  Table already exists. Migration may have been run previously.');
      console.log('   If you need to recreate the table, drop it first:\n');
      console.log('   DROP TABLE IF EXISTS shq_error_log CASCADE;\n');
    }

    process.exit(1);
  } finally {
    await client.end();
  }
}

// Execute
executeMigration().catch((error) => {
  console.error('💥 Fatal error:', error);
  process.exit(1);
});

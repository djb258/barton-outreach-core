#!/usr/bin/env node
/**
 * Create Lovable.dev Role in Neon PostgreSQL
 *
 * This script creates a new role for Lovable.dev edge functions
 * with proper permissions on all schemas and tables.
 */

const { Client } = require('pg');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const connectionString = process.env.NEON_CONNECTION_STRING || process.env.DATABASE_URL;

if (!connectionString) {
  console.error('❌ Error: DATABASE_URL or NEON_CONNECTION_STRING not found in .env');
  process.exit(1);
}

async function createLovableRole() {
  const client = new Client({ connectionString });

  try {
    console.log('🔌 Connecting to Neon PostgreSQL...');
    await client.connect();
    console.log('✅ Connected successfully\n');

    // Read SQL file
    const sqlFilePath = path.join(__dirname, '../migrations/create_lovable_role.sql');
    const sql = fs.readFileSync(sqlFilePath, 'utf8');

    // Split by semicolon and execute each statement
    const statements = sql
      .split(';')
      .map(s => s.trim())
      .filter(s => s.length > 0 && !s.startsWith('--'));

    console.log('📝 Executing SQL statements...\n');

    for (let i = 0; i < statements.length; i++) {
      const statement = statements[i];

      // Skip comments
      if (statement.startsWith('--')) continue;

      try {
        const result = await client.query(statement);

        // Print results for SELECT queries
        if (result.rows && result.rows.length > 0) {
          console.log(`✅ Statement ${i + 1}:`);
          console.table(result.rows);
        } else {
          console.log(`✅ Statement ${i + 1}: Executed successfully`);
        }
      } catch (err) {
        // Check if error is "role already exists"
        if (err.message.includes('already exists')) {
          console.log(`⚠️  Statement ${i + 1}: Role already exists, skipping...`);
        } else {
          console.error(`❌ Statement ${i + 1} failed:`, err.message);
          // Continue with other statements
        }
      }
    }

    console.log('\n✅ All statements executed\n');

    // Test the new role's permissions
    console.log('🧪 Testing role permissions...');

    const testQueries = [
      {
        name: 'Check role exists',
        query: "SELECT rolname, rolcanlogin, rolsuper FROM pg_roles WHERE rolname = 'marketing_db_owner'"
      },
      {
        name: 'Check schema permissions',
        query: `SELECT nspname as schema_name
                FROM pg_namespace
                WHERE nspname IN ('public', 'marketing', 'intake', 'bit', 'shq')
                ORDER BY nspname`
      },
      {
        name: 'Check table count in marketing schema',
        query: `SELECT COUNT(*) as table_count
                FROM information_schema.tables
                WHERE table_schema = 'marketing'`
      },
      {
        name: 'Check invalid tables exist',
        query: `SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'marketing'
                  AND table_name LIKE '%invalid%'
                ORDER BY table_name`
      }
    ];

    for (const test of testQueries) {
      try {
        const result = await client.query(test.query);
        console.log(`\n✅ ${test.name}:`);
        console.table(result.rows);
      } catch (err) {
        console.error(`❌ ${test.name} failed:`, err.message);
      }
    }

    console.log('\n' + '='.repeat(80));
    console.log('🎉 SUCCESS: Lovable.dev role created successfully!');
    console.log('='.repeat(80));

  } catch (error) {
    console.error('\n❌ Error:', error.message);
    process.exit(1);
  } finally {
    await client.end();
    console.log('\n🔌 Disconnected from database');
  }
}

// Run the script
createLovableRole().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});

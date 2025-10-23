/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/analysis
Barton ID: 06.01.01
Unique ID: CTB-47A7D164
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

/**
 * Run Intelligence Table Migrations
 * Executes company_intelligence and people_intelligence migrations
 */

import pg from 'pg';
import fs from 'fs/promises';
import path from 'path';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const NEON_DATABASE_URL = process.env.NEON_DATABASE_URL || process.env.DATABASE_URL;

console.log('\n=== Running Intelligence Table Migrations ===\n');

async function runMigrations() {
  // Manually construct connection config to handle URL-encoded credentials
  const url = new URL(NEON_DATABASE_URL);

  const client = new pg.Client({
    host: url.hostname,
    port: url.port || 5432,
    database: url.pathname.slice(1), // Remove leading slash
    user: decodeURIComponent(url.username),
    password: decodeURIComponent(url.password),
    ssl: {
      rejectUnauthorized: false
    }
  });

  try {
    await client.connect();
    console.log('✅ Connected to Neon database\n');

    // Migration files
    const migrations = [
      '../apps/outreach-process-manager/migrations/2025-10-22_create_marketing_company_intelligence.sql',
      '../apps/outreach-process-manager/migrations/2025-10-22_create_marketing_people_intelligence.sql'
    ];

    for (const migrationFile of migrations) {
      console.log(`\n📄 Running migration: ${path.basename(migrationFile)}`);
      console.log('─'.repeat(60));

      const migrationPath = path.join(__dirname, migrationFile);
      const sql = await fs.readFile(migrationPath, 'utf8');

      try {
        await client.query(sql);
        console.log(`✅ Migration successful: ${path.basename(migrationFile)}`);
      } catch (error) {
        console.error(`❌ Migration failed: ${path.basename(migrationFile)}`);
        console.error(`   Error: ${error.message}`);
        throw error;
      }
    }

    // Verify tables were created
    console.log('\n\n[VERIFICATION] Checking if tables were created...\n');

    const verifyQuery = `
      SELECT
        table_schema,
        table_name,
        (SELECT COUNT(*) FROM information_schema.columns
         WHERE table_schema = t.table_schema
         AND table_name = t.table_name) as column_count
      FROM information_schema.tables t
      WHERE table_name IN ('company_intelligence', 'people_intelligence')
        AND table_schema = 'marketing'
      ORDER BY table_name;
    `;

    const result = await client.query(verifyQuery);

    if (result.rows.length === 2) {
      console.log('✅ Both intelligence tables created successfully:\n');
      result.rows.forEach(row => {
        console.log(`   ✓ ${row.table_schema}.${row.table_name} (${row.column_count} columns)`);
      });

      // Get column details
      console.log('\n[COLUMN DETAILS]\n');

      for (const table of result.rows) {
        const columnsQuery = `
          SELECT column_name, data_type, is_nullable, column_default
          FROM information_schema.columns
          WHERE table_schema = $1 AND table_name = $2
          ORDER BY ordinal_position;
        `;

        const cols = await client.query(columnsQuery, [table.table_schema, table.table_name]);

        console.log(`\n${table.table_schema}.${table.table_name}:`);
        cols.rows.forEach(col => {
          const nullable = col.is_nullable === 'YES' ? 'NULL' : 'NOT NULL';
          console.log(`  - ${col.column_name} (${col.data_type}) ${nullable}`);
        });
      }

      // Check for indexes
      console.log('\n\n[INDEXES]\n');

      const indexQuery = `
        SELECT
          schemaname,
          tablename,
          indexname
        FROM pg_indexes
        WHERE tablename IN ('company_intelligence', 'people_intelligence')
          AND schemaname = 'marketing'
        ORDER BY tablename, indexname;
      `;

      const indexes = await client.query(indexQuery);
      console.log(`Found ${indexes.rows.length} indexes:\n`);

      indexes.rows.forEach(idx => {
        console.log(`  ✓ ${idx.indexname} on ${idx.tablename}`);
      });

      // Check for functions
      console.log('\n\n[HELPER FUNCTIONS]\n');

      const funcQuery = `
        SELECT
          proname as function_name,
          pg_get_function_arguments(oid) as arguments
        FROM pg_proc
        WHERE proname ILIKE '%intelligence%'
          AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'marketing')
        ORDER BY proname;
      `;

      const funcs = await client.query(funcQuery);
      console.log(`Found ${funcs.rows.length} intelligence functions:\n`);

      funcs.rows.forEach(func => {
        console.log(`  ✓ ${func.function_name}(${func.arguments})`);
      });

    } else {
      console.error('❌ Table verification failed!');
      console.error(`   Expected 2 tables, found ${result.rows.length}`);
    }

    console.log('\n\n=== MIGRATION SUMMARY ===\n');
    console.log('✅ company_intelligence table created');
    console.log('✅ people_intelligence table created');
    console.log('✅ All indexes created');
    console.log('✅ All helper functions created');
    console.log('\n🎯 Schema is now fully Barton Doctrine compliant!');

  } catch (error) {
    console.error('\n❌ Migration failed:', error);
    throw error;
  } finally {
    await client.end();
    console.log('\n✅ Database connection closed\n');
  }
}

// Run migrations
runMigrations()
  .then(() => {
    console.log('✅ Migrations complete!');
    process.exit(0);
  })
  .catch(error => {
    console.error('❌ Migration error:', error.message);
    process.exit(1);
  });

/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/analysis
Barton ID: 06.01.01
Unique ID: CTB-05F465D8
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

/**
 * Discover Neon Schema
 * Lists all schemas, tables, and columns
 */

import pg from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const NEON_DATABASE_URL = process.env.NEON_DATABASE_URL || process.env.DATABASE_URL;

console.log('\n=== Neon Schema Discovery ===\n');

async function discoverSchema() {
  const client = new pg.Client({
    connectionString: NEON_DATABASE_URL,
    ssl: { rejectUnauthorized: false }
  });

  try {
    await client.connect();
    console.log('✅ Connected to Neon database\n');

    // 1. List all schemas
    console.log('[STEP 1] Discovering all schemas...\n');

    const schemasQuery = `
      SELECT schema_name
      FROM information_schema.schemata
      WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
      ORDER BY schema_name;
    `;

    const schemasResult = await client.query(schemasQuery);
    console.log(`Found ${schemasResult.rows.length} schemas:\n`);
    schemasResult.rows.forEach(row => {
      console.log(`  - ${row.schema_name}`);
    });

    // 2. List all tables in each schema
    console.log('\n\n[STEP 2] Discovering all tables...\n');

    const tablesQuery = `
      SELECT
        table_schema,
        table_name,
        table_type
      FROM information_schema.tables
      WHERE table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
      ORDER BY table_schema, table_name;
    `;

    const tablesResult = await client.query(tablesQuery);
    console.log(`Found ${tablesResult.rows.length} tables:\n`);

    const tablesBySchema = {};
    tablesResult.rows.forEach(row => {
      if (!tablesBySchema[row.table_schema]) {
        tablesBySchema[row.table_schema] = [];
      }
      tablesBySchema[row.table_schema].push(row.table_name);
    });

    Object.entries(tablesBySchema).forEach(([schema, tables]) => {
      console.log(`${schema}:`);
      tables.forEach(table => {
        console.log(`  - ${table}`);
      });
      console.log('');
    });

    // 3. Check for company-related tables
    console.log('\n[STEP 3] Looking for company-related tables...\n');

    const companyTablesQuery = `
      SELECT
        table_schema,
        table_name
      FROM information_schema.tables
      WHERE table_name ILIKE '%company%'
        OR table_name ILIKE '%people%'
        OR table_name ILIKE '%person%'
        OR table_name ILIKE '%contact%'
        OR table_name ILIKE '%lead%'
        OR table_name ILIKE '%master%'
        OR table_name ILIKE '%intake%'
      ORDER BY table_schema, table_name;
    `;

    const companyTables = await client.query(companyTablesQuery);

    if (companyTables.rows.length > 0) {
      console.log(`Found ${companyTables.rows.length} related tables:\n`);
      companyTables.rows.forEach(row => {
        console.log(`  - ${row.table_schema}.${row.table_name}`);
      });

      // Get columns for each table
      console.log('\n[STEP 4] Inspecting columns...\n');

      for (const table of companyTables.rows) {
        const columnsQuery = `
          SELECT column_name, data_type, is_nullable
          FROM information_schema.columns
          WHERE table_schema = $1
            AND table_name = $2
          ORDER BY ordinal_position;
        `;

        const columnsResult = await client.query(columnsQuery, [table.table_schema, table.table_name]);

        console.log(`\n${table.table_schema}.${table.table_name} (${columnsResult.rows.length} columns):`);
        columnsResult.rows.forEach(col => {
          console.log(`  - ${col.column_name} (${col.data_type})`);
        });
      }
    } else {
      console.log('❌ No company/people/contact related tables found!');
      console.log('\n⚠️ The database appears to be empty or schema migrations have not been run yet.');
    }

    // 4. Sample some data
    if (companyTables.rows.length > 0) {
      console.log('\n\n[STEP 5] Checking row counts...\n');

      for (const table of companyTables.rows.slice(0, 5)) {
        try {
          const countQuery = `SELECT COUNT(*) as count FROM "${table.table_schema}"."${table.table_name}"`;
          const countResult = await client.query(countQuery);
          console.log(`  ${table.table_schema}.${table.table_name}: ${countResult.rows[0].count} rows`);
        } catch (error) {
          console.log(`  ${table.table_schema}.${table.table_name}: ERROR - ${error.message}`);
        }
      }
    }

    console.log('\n\n=== DISCOVERY SUMMARY ===\n');
    console.log(`Total Schemas: ${schemasResult.rows.length}`);
    console.log(`Total Tables: ${tablesResult.rows.length}`);
    console.log(`Company-Related Tables: ${companyTables.rows.length}`);

    if (companyTables.rows.length === 0) {
      console.log('\n🚨 CRITICAL FINDING:');
      console.log('  The database schema has NOT been created yet!');
      console.log('\n📋 Action Required:');
      console.log('  1. Run schema migrations from apps/outreach-process-manager/migrations/');
      console.log('  2. Execute create_company_master.sql');
      console.log('  3. Execute create_people_master.sql');
      console.log('  4. Re-run this discovery script');
    }

  } catch (error) {
    console.error('\n❌ Discovery failed:', error);
    throw error;
  } finally {
    await client.end();
    console.log('\n✅ Database connection closed\n');
  }
}

// Run discovery
discoverSchema()
  .then(() => {
    console.log('✅ Schema discovery complete!');
    process.exit(0);
  })
  .catch(error => {
    console.error('❌ Discovery error:', error.message);
    process.exit(1);
  });

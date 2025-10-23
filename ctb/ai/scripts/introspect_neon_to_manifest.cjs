#!/usr/bin/env node
/**
 * CTB Metadata
 * Barton ID: 03.01.04.20251023.isch.001
 * Branch: ai
 * Altitude: 30k (HEIR - Hierarchical Execution Intelligence & Repair)
 * Purpose: Introspect Neon PostgreSQL schema and generate doctrine-compliant YAML manifest
 * Dependencies: pg@^8.11.0, yaml@^2.3.0
 * Output: ctb/data/infra/NEON_SCHEMA_MANIFEST.yaml
 */

const { Client } = require('pg');
const yaml = require('yaml');
const fs = require('fs');
const path = require('path');

// Configuration
const DATABASE_URL = process.env.DATABASE_URL;
const OUTPUT_PATH = path.join(__dirname, '../../data/infra/NEON_SCHEMA_MANIFEST.yaml');

// Validation
if (!DATABASE_URL) {
  console.error('❌ ERROR: DATABASE_URL environment variable is required');
  console.error('   Set it with: export DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require"');
  process.exit(1);
}

/**
 * Main introspection function
 */
async function introspectSchema() {
  const client = new Client({ connectionString: DATABASE_URL });

  try {
    await client.connect();
    console.log('✅ Connected to Neon PostgreSQL');
    console.log('🔍 Starting schema introspection...\n');

    // Initialize manifest
    const manifest = {
      version: '1.0',
      generated: new Date().toISOString(),
      database: await getDatabaseInfo(client),
      schemas: []
    };

    // Get all non-system schemas
    const schemasResult = await client.query(`
      SELECT schema_name
      FROM information_schema.schemata
      WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast', 'pg_temp_1', 'pg_toast_temp_1')
      ORDER BY schema_name
    `);

    console.log(`📊 Found ${schemasResult.rows.length} schemas to introspect\n`);

    // Process each schema
    for (const schemaRow of schemasResult.rows) {
      const schemaName = schemaRow.schema_name;
      console.log(`\n📁 Processing schema: ${schemaName}`);

      const schemaObj = {
        name: schemaName,
        tables: [],
        views: [],
        functions: []
      };

      // Get tables
      const tables = await getTables(client, schemaName);
      console.log(`   ├─ Tables: ${tables.length}`);

      for (const tableName of tables) {
        const tableDetails = await getTableDetails(client, schemaName, tableName);
        schemaObj.tables.push(tableDetails);
      }

      // Get views
      const views = await getViews(client, schemaName);
      console.log(`   ├─ Views: ${views.length}`);

      for (const viewName of views) {
        const viewDetails = await getViewDetails(client, schemaName, viewName);
        schemaObj.views.push(viewDetails);
      }

      // Get functions
      const functions = await getFunctions(client, schemaName);
      console.log(`   └─ Functions: ${functions.length}`);

      for (const funcName of functions) {
        const funcDetails = await getFunctionDetails(client, schemaName, funcName);
        schemaObj.functions.push(funcDetails);
      }

      manifest.schemas.push(schemaObj);
    }

    // Write manifest to file
    const outputDir = path.dirname(OUTPUT_PATH);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    fs.writeFileSync(OUTPUT_PATH, yaml.stringify(manifest, { indent: 2 }));

    // Summary
    console.log('\n' + '='.repeat(60));
    console.log('✅ Schema introspection complete!');
    console.log('='.repeat(60));
    console.log(`📄 Output: ${OUTPUT_PATH}`);
    console.log(`📊 Statistics:`);
    console.log(`   - Schemas: ${manifest.schemas.length}`);
    console.log(`   - Tables: ${manifest.schemas.reduce((sum, s) => sum + s.tables.length, 0)}`);
    console.log(`   - Views: ${manifest.schemas.reduce((sum, s) => sum + s.views.length, 0)}`);
    console.log(`   - Functions: ${manifest.schemas.reduce((sum, s) => sum + s.functions.length, 0)}`);
    console.log('='.repeat(60) + '\n');

  } catch (error) {
    console.error('\n❌ Error during introspection:', error.message);
    console.error('Stack trace:', error.stack);
    process.exit(1);
  } finally {
    await client.end();
  }
}

/**
 * Get database connection info
 */
async function getDatabaseInfo(client) {
  const result = await client.query('SELECT version(), current_database(), current_user');
  return {
    version: result.rows[0].version,
    name: result.rows[0].current_database,
    user: result.rows[0].current_user
  };
}

/**
 * Get all tables in a schema
 */
async function getTables(client, schemaName) {
  const result = await client.query(`
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = $1 AND table_type = 'BASE TABLE'
    ORDER BY table_name
  `, [schemaName]);

  return result.rows.map(row => row.table_name);
}

/**
 * Get detailed table information
 */
async function getTableDetails(client, schemaName, tableName) {
  // Get columns
  const columnsResult = await client.query(`
    SELECT
      column_name,
      data_type,
      is_nullable,
      column_default,
      character_maximum_length,
      numeric_precision,
      numeric_scale,
      udt_name
    FROM information_schema.columns
    WHERE table_schema = $1 AND table_name = $2
    ORDER BY ordinal_position
  `, [schemaName, tableName]);

  // Get primary key
  const pkResult = await client.query(`
    SELECT a.attname
    FROM pg_index i
    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
    WHERE i.indrelid = ($1 || '.' || $2)::regclass AND i.indisprimary
  `, [schemaName, tableName]);

  // Get indexes
  const indexesResult = await client.query(`
    SELECT
      i.relname AS index_name,
      a.attname AS column_name,
      ix.indisunique AS is_unique
    FROM pg_class t
    JOIN pg_index ix ON t.oid = ix.indrelid
    JOIN pg_class i ON i.oid = ix.indexrelid
    JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
    WHERE t.relkind = 'r'
      AND t.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = $1)
      AND t.relname = $2
    ORDER BY i.relname, a.attnum
  `, [schemaName, tableName]);

  // Get foreign keys
  const fkResult = await client.query(`
    SELECT
      tc.constraint_name,
      kcu.column_name,
      ccu.table_schema AS foreign_schema,
      ccu.table_name AS foreign_table,
      ccu.column_name AS foreign_column
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_schema = $1
      AND tc.table_name = $2
  `, [schemaName, tableName]);

  return {
    name: tableName,
    columns: columnsResult.rows.map(col => ({
      name: col.column_name,
      type: col.data_type,
      udt_name: col.udt_name,
      nullable: col.is_nullable === 'YES',
      default: col.column_default,
      max_length: col.character_maximum_length,
      precision: col.numeric_precision,
      scale: col.numeric_scale
    })),
    primary_key: pkResult.rows.map(row => row.attname),
    indexes: groupIndexes(indexesResult.rows),
    foreign_keys: fkResult.rows.map(fk => ({
      name: fk.constraint_name,
      column: fk.column_name,
      references: {
        schema: fk.foreign_schema,
        table: fk.foreign_table,
        column: fk.foreign_column
      }
    }))
  };
}

/**
 * Group index rows by index name
 */
function groupIndexes(indexRows) {
  const grouped = {};
  for (const row of indexRows) {
    if (!grouped[row.index_name]) {
      grouped[row.index_name] = {
        name: row.index_name,
        columns: [],
        unique: row.is_unique
      };
    }
    grouped[row.index_name].columns.push(row.column_name);
  }
  return Object.values(grouped);
}

/**
 * Get all views in a schema
 */
async function getViews(client, schemaName) {
  const result = await client.query(`
    SELECT table_name
    FROM information_schema.views
    WHERE table_schema = $1
    ORDER BY table_name
  `, [schemaName]);

  return result.rows.map(row => row.table_name);
}

/**
 * Get detailed view information
 */
async function getViewDetails(client, schemaName, viewName) {
  // Get columns
  const columnsResult = await client.query(`
    SELECT
      column_name,
      data_type,
      is_nullable,
      udt_name
    FROM information_schema.columns
    WHERE table_schema = $1 AND table_name = $2
    ORDER BY ordinal_position
  `, [schemaName, viewName]);

  // Get view definition
  const defResult = await client.query(`
    SELECT definition
    FROM pg_views
    WHERE schemaname = $1 AND viewname = $2
  `, [schemaName, viewName]);

  return {
    name: viewName,
    columns: columnsResult.rows.map(col => ({
      name: col.column_name,
      type: col.data_type,
      udt_name: col.udt_name,
      nullable: col.is_nullable === 'YES'
    })),
    definition: defResult.rows[0]?.definition || null
  };
}

/**
 * Get all functions in a schema
 */
async function getFunctions(client, schemaName) {
  const result = await client.query(`
    SELECT DISTINCT routine_name
    FROM information_schema.routines
    WHERE routine_schema = $1
      AND routine_type = 'FUNCTION'
    ORDER BY routine_name
  `, [schemaName]);

  return result.rows.map(row => row.routine_name);
}

/**
 * Get detailed function information
 */
async function getFunctionDetails(client, schemaName, functionName) {
  const result = await client.query(`
    SELECT
      routine_name,
      data_type AS return_type,
      routine_definition
    FROM information_schema.routines
    WHERE routine_schema = $1
      AND routine_name = $2
      AND routine_type = 'FUNCTION'
    LIMIT 1
  `, [schemaName, functionName]);

  // Get parameters
  const paramsResult = await client.query(`
    SELECT
      parameter_name,
      data_type,
      parameter_mode
    FROM information_schema.parameters
    WHERE specific_schema = $1
      AND specific_name LIKE $2 || '%'
    ORDER BY ordinal_position
  `, [schemaName, functionName]);

  return {
    name: functionName,
    return_type: result.rows[0]?.return_type || 'unknown',
    parameters: paramsResult.rows.map(param => ({
      name: param.parameter_name,
      type: param.data_type,
      mode: param.parameter_mode
    })),
    definition: result.rows[0]?.routine_definition || null
  };
}

// Run introspection
introspectSchema().catch(err => {
  console.error('❌ Fatal error:', err.message);
  process.exit(1);
});

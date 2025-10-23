/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ai/scripts
Barton ID: 03.01.04
Unique ID: CTB-49CAEE73
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: HEIR
─────────────────────────────────────────────
*/

import pkg from 'pg';

const { Client } = pkg;

async function inspectExistingSchema() {
  const connectionString = 'postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/Marketing%20DB?sslmode=require';

  const client = new Client({
    connectionString: connectionString
  });

  try {
    await client.connect();
    console.log('🔗 Connected to Neon Marketing DB\n');

    // Check existing people schema
    console.log('📋 Checking existing people schema...\n');

    // Get all tables in people schema
    const tablesResult = await client.query(`
      SELECT table_name, table_type
      FROM information_schema.tables
      WHERE table_schema = 'people'
      ORDER BY table_name;
    `);

    console.log('🏗️ Tables in people schema:');
    if (tablesResult.rows.length === 0) {
      console.log('   No tables found in people schema');
    } else {
      tablesResult.rows.forEach(table => {
        console.log(`   ${table.table_name} (${table.table_type})`);
      });
    }

    // Get detailed column information for people.contact
    if (tablesResult.rows.some(t => t.table_name === 'contact')) {
      console.log('\n📊 Detailed schema for people.contact:');
      const columnsResult = await client.query(`
        SELECT
          column_name,
          data_type,
          is_nullable,
          column_default,
          character_maximum_length,
          ordinal_position
        FROM information_schema.columns
        WHERE table_schema = 'people' AND table_name = 'contact'
        ORDER BY ordinal_position;
      `);

      columnsResult.rows.forEach((col, i) => {
        const nullable = col.is_nullable === 'YES' ? 'NULL' : 'NOT NULL';
        const defaultVal = col.column_default ? ` DEFAULT ${col.column_default}` : '';
        const maxLen = col.character_maximum_length ? `(${col.character_maximum_length})` : '';
        console.log(`   ${i + 1}. ${col.column_name} - ${col.data_type}${maxLen} ${nullable}${defaultVal}`);
      });
    }

    // Check for indexes on people.contact
    console.log('\n🔍 Indexes on people.contact:');
    const indexesResult = await client.query(`
      SELECT
        indexname,
        indexdef
      FROM pg_indexes
      WHERE schemaname = 'people' AND tablename = 'contact'
      ORDER BY indexname;
    `);

    if (indexesResult.rows.length === 0) {
      console.log('   No custom indexes found');
    } else {
      indexesResult.rows.forEach(index => {
        console.log(`   ${index.indexname}`);
        console.log(`     ${index.indexdef}`);
      });
    }

    // Check for triggers
    console.log('\n⚡ Triggers on people.contact:');
    const triggersResult = await client.query(`
      SELECT
        trigger_name,
        event_manipulation,
        action_timing,
        action_statement
      FROM information_schema.triggers
      WHERE event_object_schema = 'people' AND event_object_table = 'contact'
      ORDER BY trigger_name;
    `);

    if (triggersResult.rows.length === 0) {
      console.log('   No triggers found');
    } else {
      triggersResult.rows.forEach(trigger => {
        console.log(`   ${trigger.trigger_name} (${trigger.action_timing} ${trigger.event_manipulation})`);
      });
    }

    // Sample data
    console.log('\n📄 Sample data from people.contact (first 3 rows):');
    const sampleResult = await client.query(`
      SELECT * FROM people.contact LIMIT 3;
    `);

    if (sampleResult.rows.length === 0) {
      console.log('   No data found');
    } else {
      console.log(`   Found ${sampleResult.rows.length} sample rows:`);
      sampleResult.rows.forEach((row, i) => {
        console.log(`   Row ${i + 1}:`, JSON.stringify(row, null, 2));
      });
    }

  } catch (err) {
    console.error('❌ Database error:', err.message);
  } finally {
    await client.end();
    console.log('\n🔚 Connection closed');
  }
}

console.log('🔍 Inspecting Existing People Schema...\n');
inspectExistingSchema();
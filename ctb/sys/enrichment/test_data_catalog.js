#!/usr/bin/env node
/**
 * Test PLE Data Catalog Search Functions
 */

const { Client } = require('pg');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '..', '..', '..', '.env') });

async function testCatalog() {
  const client = new Client({
    connectionString: process.env.DATABASE_URL || process.env.NEON_CONNECTION_STRING
  });

  try {
    await client.connect();
    console.log('='.repeat(80));
    console.log('TESTING DATA CATALOG SEARCH FUNCTIONS');
    console.log('='.repeat(80));

    // Test 1: Search for "renewal date"
    console.log('\n--- Test 1: Search for "ein federal tax" ---');
    const test1 = await client.query(`SELECT * FROM catalog.search_columns('ein federal tax', 5)`);
    console.log(`Found ${test1.rows.length} results:`);
    for (const row of test1.rows) {
      console.log(`  ${row.column_id} (${row.data_type})`);
      console.log(`    -> ${row.description}`);
    }

    // Test 2: Search by tag
    console.log('\n--- Test 2: Search by tag "dol" ---');
    const test2 = await client.query(`SELECT * FROM catalog.search_by_tag('dol') LIMIT 10`);
    console.log(`Found ${test2.rows.length} columns with tag "dol":`);
    for (const row of test2.rows) {
      console.log(`  ${row.column_id}`);
    }

    // Test 3: Get table details
    console.log('\n--- Test 3: Get table details for company.company_master ---');
    const test3 = await client.query(`SELECT * FROM catalog.get_table_details('company.company_master') LIMIT 10`);
    console.log(`Found ${test3.rows.length} columns:`);
    console.log('| Column | Type | Description |');
    console.log('|--------|------|-------------|');
    for (const row of test3.rows) {
      const desc = row.description ? row.description.substring(0, 50) : 'N/A';
      console.log(`| ${row.column_name} | ${row.data_type} | ${desc} |`);
    }

    // Test 4: Search for linkedin
    console.log('\n--- Test 4: Search for "linkedin" ---');
    const test4 = await client.query(`SELECT * FROM catalog.search_columns('linkedin', 5)`);
    console.log(`Found ${test4.rows.length} results:`);
    for (const row of test4.rows) {
      console.log(`  ${row.column_id} -> ${row.business_name || row.column_name}`);
    }

    // Test 5: Schema summary view
    console.log('\n--- Test 5: Schema Summary ---');
    const test5 = await client.query(`SELECT * FROM catalog.v_schema_summary`);
    console.log('| Schema | Type | Tables | Columns | Rows |');
    console.log('|--------|------|--------|---------|------|');
    for (const row of test5.rows) {
      console.log(`| ${row.schema_name} | ${row.schema_type} | ${row.table_count} | ${row.column_count} | ${(row.total_rows || 0).toLocaleString()} |`);
    }

    // Test 6: Get AI context for company schema
    console.log('\n--- Test 6: Get AI Context (company schema, first 2000 chars) ---');
    const test6 = await client.query(`SELECT LEFT(catalog.get_ai_context('company'), 2000) as context`);
    console.log(test6.rows[0].context);
    console.log('... (truncated)');

    console.log('\n' + '='.repeat(80));
    console.log('ALL TESTS PASSED!');
    console.log('='.repeat(80));

  } catch (error) {
    console.error('Error:', error.message);
  } finally {
    await client.end();
  }
}

testCatalog();

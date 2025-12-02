#!/usr/bin/env node
/**
 * Fix Data Catalog Search Functions
 */

const { Client } = require('pg');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '..', '..', '..', '.env') });

async function fixFunctions() {
  const client = new Client({
    connectionString: process.env.DATABASE_URL || process.env.NEON_CONNECTION_STRING
  });

  try {
    await client.connect();
    console.log('Fixing catalog search functions...\n');

    // Drop and recreate search_columns with proper types
    await client.query(`DROP FUNCTION IF EXISTS catalog.search_columns(TEXT, INT)`);

    await client.query(`
      CREATE OR REPLACE FUNCTION catalog.search_columns(
        p_query TEXT,
        p_limit INT DEFAULT 20
      ) RETURNS TABLE (
        column_id TEXT,
        table_id TEXT,
        column_name TEXT,
        description TEXT,
        business_name TEXT,
        data_type TEXT,
        relevance REAL
      ) AS $$
      BEGIN
        RETURN QUERY
        SELECT
          c.column_id::TEXT,
          c.table_id::TEXT,
          c.column_name::TEXT,
          c.description::TEXT,
          c.business_name::TEXT,
          c.data_type::TEXT,
          ts_rank(
            to_tsvector('english',
              c.column_name || ' ' ||
              COALESCE(c.description, '') || ' ' ||
              COALESCE(c.business_name, '') || ' ' ||
              COALESCE(c.business_definition, '') || ' ' ||
              COALESCE(array_to_string(c.synonyms, ' '), '') || ' ' ||
              COALESCE(array_to_string(c.tags, ' '), '')
            ),
            plainto_tsquery('english', p_query)
          )::REAL as relevance
        FROM catalog.columns c
        WHERE to_tsvector('english',
              c.column_name || ' ' ||
              COALESCE(c.description, '') || ' ' ||
              COALESCE(c.business_name, '') || ' ' ||
              COALESCE(c.business_definition, '') || ' ' ||
              COALESCE(array_to_string(c.synonyms, ' '), '') || ' ' ||
              COALESCE(array_to_string(c.tags, ' '), '')
          ) @@ plainto_tsquery('english', p_query)
        ORDER BY relevance DESC
        LIMIT p_limit;
      END;
      $$ LANGUAGE plpgsql;
    `);
    console.log('  Fixed: catalog.search_columns()');

    // Drop and recreate search_by_tag
    await client.query(`DROP FUNCTION IF EXISTS catalog.search_by_tag(TEXT)`);

    await client.query(`
      CREATE OR REPLACE FUNCTION catalog.search_by_tag(
        p_tag TEXT
      ) RETURNS TABLE (
        column_id TEXT,
        table_id TEXT,
        column_name TEXT,
        description TEXT,
        tags TEXT[]
      ) AS $$
      BEGIN
        RETURN QUERY
        SELECT
          c.column_id::TEXT,
          c.table_id::TEXT,
          c.column_name::TEXT,
          c.description::TEXT,
          c.tags
        FROM catalog.columns c
        WHERE p_tag = ANY(c.tags)
        ORDER BY c.table_id, c.ordinal_position;
      END;
      $$ LANGUAGE plpgsql;
    `);
    console.log('  Fixed: catalog.search_by_tag()');

    // Drop and recreate get_table_details
    await client.query(`DROP FUNCTION IF EXISTS catalog.get_table_details(VARCHAR)`);

    await client.query(`
      CREATE OR REPLACE FUNCTION catalog.get_table_details(p_table_id TEXT)
      RETURNS TABLE (
        column_id TEXT,
        column_name TEXT,
        business_name TEXT,
        data_type TEXT,
        description TEXT,
        format_example TEXT,
        is_nullable BOOLEAN,
        is_primary_key BOOLEAN,
        is_foreign_key BOOLEAN
      ) AS $$
      BEGIN
        RETURN QUERY
        SELECT
          c.column_id::TEXT,
          c.column_name::TEXT,
          c.business_name::TEXT,
          c.data_type::TEXT,
          c.description::TEXT,
          c.format_example::TEXT,
          c.is_nullable,
          c.is_primary_key,
          c.is_foreign_key
        FROM catalog.columns c
        WHERE c.table_id = p_table_id
        ORDER BY c.ordinal_position;
      END;
      $$ LANGUAGE plpgsql;
    `);
    console.log('  Fixed: catalog.get_table_details()');

    // Test the functions
    console.log('\nTesting fixed functions...');

    const test1 = await client.query(`SELECT * FROM catalog.search_columns('ein', 5)`);
    console.log(`\nSearch for "ein": Found ${test1.rows.length} results`);
    for (const row of test1.rows) {
      console.log(`  - ${row.column_id}`);
    }

    const test2 = await client.query(`SELECT * FROM catalog.search_by_tag('dol') LIMIT 5`);
    console.log(`\nSearch by tag "dol": Found ${test2.rows.length}+ columns`);

    const test3 = await client.query(`SELECT * FROM catalog.get_table_details('company.company_master') LIMIT 5`);
    console.log(`\nTable details for company.company_master: Found ${test3.rows.length}+ columns`);

    console.log('\nAll functions fixed and tested successfully!');

  } catch (error) {
    console.error('Error:', error.message);
    throw error;
  } finally {
    await client.end();
  }
}

fixFunctions().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});

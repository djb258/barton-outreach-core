/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/scripts
Barton ID: 06.01.04
Unique ID: CTB-8F4818E2
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

#!/usr/bin/env node
/**
 * List all tables in the marketing schema of Neon PostgreSQL database
 */

import pg from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const { Client } = pg;

async function listMarketingTables() {
  const client = new Client({
    connectionString: process.env.NEON_DATABASE_URL || process.env.DATABASE_URL,
    ssl: {
      rejectUnauthorized: false
    }
  });

  try {
    console.log('🔌 Connecting to Marketing DB...');
    await client.connect();
    console.log('✅ Connected successfully\n');

    // Query to get all tables in the marketing schema
    const tablesQuery = `
      SELECT 
        table_name,
        table_type,
        (SELECT obj_description(c.oid) 
         FROM pg_class c 
         WHERE c.relname = t.table_name 
         AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'marketing')
        ) as table_comment
      FROM information_schema.tables t
      WHERE table_schema = 'marketing'
      ORDER BY table_type, table_name;
    `;

    console.log('📊 Fetching all tables in marketing schema...\n');
    const tablesResult = await client.query(tablesQuery);

    if (tablesResult.rows.length === 0) {
      console.log('❌ No tables found in marketing schema');
      console.log('💡 Make sure the marketing schema exists and has tables');
      return;
    }

    console.log('=' * 60);
    console.log('📋 MARKETING SCHEMA - TABLES LIST');
    console.log('=' * 60);
    
    // Separate tables and views
    const tables = tablesResult.rows.filter(row => row.table_type === 'BASE TABLE');
    const views = tablesResult.rows.filter(row => row.table_type === 'VIEW');

    // List regular tables
    if (tables.length > 0) {
      console.log('\n📁 TABLES (' + tables.length + '):');
      console.log('-'.repeat(40));
      tables.forEach((table, index) => {
        console.log(`${index + 1}. marketing.${table.table_name}`);
        if (table.table_comment) {
          console.log(`   Description: ${table.table_comment}`);
        }
      });
    }

    // List views
    if (views.length > 0) {
      console.log('\n👁️ VIEWS (' + views.length + '):');
      console.log('-'.repeat(40));
      views.forEach((view, index) => {
        console.log(`${index + 1}. marketing.${view.table_name}`);
        if (view.table_comment) {
          console.log(`   Description: ${view.table_comment}`);
        }
      });
    }

    // Get column details for each table
    console.log('\n' + '=' * 60);
    console.log('📊 TABLE DETAILS WITH COLUMNS:');
    console.log('=' * 60);

    for (const table of tables) {
      const columnsQuery = `
        SELECT 
          column_name,
          data_type,
          character_maximum_length,
          is_nullable,
          column_default,
          (SELECT col_description(pgc.oid, cols.ordinal_position::int)
           FROM pg_class pgc
           WHERE pgc.relname = cols.table_name
           AND pgc.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'marketing')
          ) as column_comment
        FROM information_schema.columns cols
        WHERE table_schema = 'marketing' 
        AND table_name = $1
        ORDER BY ordinal_position;
      `;

      const columnsResult = await client.query(columnsQuery, [table.table_name]);
      
      console.log(`\n📋 Table: marketing.${table.table_name}`);
      console.log('   Columns:');
      
      columnsResult.rows.forEach(col => {
        let typeInfo = col.data_type;
        if (col.character_maximum_length) {
          typeInfo += `(${col.character_maximum_length})`;
        }
        const nullable = col.is_nullable === 'YES' ? 'NULL' : 'NOT NULL';
        const defaultVal = col.column_default ? ` DEFAULT ${col.column_default}` : '';
        
        console.log(`   • ${col.column_name}: ${typeInfo} ${nullable}${defaultVal}`);
        if (col.column_comment) {
          console.log(`     Comment: ${col.column_comment}`);
        }
      });
    }

    // Get row counts for each table
    console.log('\n' + '=' * 60);
    console.log('📈 TABLE ROW COUNTS:');
    console.log('=' * 60);

    for (const table of tables) {
      try {
        const countQuery = `SELECT COUNT(*) as count FROM marketing.${table.table_name}`;
        const countResult = await client.query(countQuery);
        const count = countResult.rows[0].count;
        console.log(`   • marketing.${table.table_name}: ${count} rows`);
      } catch (err) {
        console.log(`   • marketing.${table.table_name}: Error counting rows`);
      }
    }

    // Summary
    console.log('\n' + '=' * 60);
    console.log('📊 SUMMARY:');
    console.log(`   • Total Tables: ${tables.length}`);
    console.log(`   • Total Views: ${views.length}`);
    console.log(`   • Total Objects: ${tablesResult.rows.length}`);
    console.log('=' * 60);

  } catch (error) {
    console.error('❌ Error:', error.message);
    if (error.code === 'ECONNREFUSED') {
      console.log('\n💡 Connection refused. Check your database configuration.');
    } else if (error.code === '42P01') {
      console.log('\n💡 Table or schema does not exist.');
    }
  } finally {
    await client.end();
    console.log('\n🔌 Database connection closed');
  }
}

// Run the script
listMarketingTables().catch(console.error);
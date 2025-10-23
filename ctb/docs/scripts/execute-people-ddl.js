/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/scripts
Barton ID: 06.01.04
Unique ID: CTB-3E25687D
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

import pkg from 'pg';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const { Client } = pkg;
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function executePeopleDDL() {
  const connectionString = 'postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/Marketing%20DB?sslmode=require';
  
  const client = new Client({
    connectionString: connectionString
  });

  try {
    await client.connect();
    console.log('🔗 Connected to Neon Marketing DB\n');

    // Read the DDL file
    const ddlPath = join(__dirname, 'create-people-schema.sql');
    const ddlContent = readFileSync(ddlPath, 'utf8');
    
    console.log('📄 Executing People Schema DDL...\n');
    
    // Execute the DDL
    await client.query(ddlContent);
    
    console.log('✅ People schema DDL executed successfully!\n');

    // Verify the tables were created
    const tablesResult = await client.query(`
      SELECT 
        table_name,
        table_type
      FROM information_schema.tables 
      WHERE table_schema = 'people'
      ORDER BY table_name;
    `);
    
    console.log('📊 Created tables in "people" schema:');
    if (tablesResult.rows.length === 0) {
      console.log('❌ No tables found - DDL may have failed');
    } else {
      tablesResult.rows.forEach(table => {
        console.log(`✅ ${table.table_name} (${table.table_type})`);
      });
    }

    // Show column count for each table
    console.log('\n📋 Table details:');
    for (const table of tablesResult.rows) {
      const columnsResult = await client.query(`
        SELECT COUNT(*) as column_count
        FROM information_schema.columns 
        WHERE table_schema = 'people' 
          AND table_name = $1;
      `, [table.table_name]);
      
      const columnCount = columnsResult.rows[0].column_count;
      console.log(`   ${table.table_name}: ${columnCount} columns`);
    }

    // Check indexes
    const indexesResult = await client.query(`
      SELECT 
        indexname,
        tablename
      FROM pg_indexes 
      WHERE schemaname = 'people'
      ORDER BY tablename, indexname;
    `);
    
    console.log('\n🔍 Created indexes:');
    if (indexesResult.rows.length === 0) {
      console.log('   No custom indexes found');
    } else {
      indexesResult.rows.forEach(index => {
        console.log(`   ${index.tablename}.${index.indexname}`);
      });
    }

  } catch (err) {
    console.error('❌ Database error:', err.message);
    console.error('Stack:', err.stack);
  } finally {
    await client.end();
    console.log('\n🔚 Connection closed');
  }
}

console.log('🚀 Starting People Schema DDL Execution...\n');
executePeopleDDL();
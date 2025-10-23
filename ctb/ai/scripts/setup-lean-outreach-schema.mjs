/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ai/scripts
Barton ID: 03.01.04
Unique ID: CTB-74559F4A
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

#!/usr/bin/env node
/**
 * Setup Lean Outreach Database Schema with Marketing Cleanup
 */

import pg from 'pg';
import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

dotenv.config();

const { Client } = pg;
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function setupLeanOutreachSchema() {
  const client = new Client({
    connectionString: process.env.NEON_DATABASE_URL || process.env.DATABASE_URL,
    ssl: {
      rejectUnauthorized: false
    }
  });

  try {
    console.log('🔌 Connecting to Neon Database...');
    await client.connect();
    console.log('✅ Connected successfully\n');

    // Read the SQL file
    const sqlPath = path.join(__dirname, '..', 'infra', 'lean-outreach-schema.sql');
    console.log(`📄 Reading SQL from: ${sqlPath}`);
    const sql = fs.readFileSync(sqlPath, 'utf8');

    console.log('🚀 Executing Lean Outreach Schema with Cleanup...');
    console.log('=' .repeat(60));
    
    // Execute the entire SQL file
    await client.query(sql);
    
    console.log('✅ Lean schema creation and cleanup completed successfully!\n');

    // Verify what was created/updated
    console.log('📊 Verifying schema objects...\n');

    // Check tables in each schema
    const tablesQuery = `
      SELECT 
        table_schema,
        table_name,
        (SELECT COUNT(*) FROM information_schema.columns 
         WHERE table_schema = t.table_schema 
         AND table_name = t.table_name) as column_count
      FROM information_schema.tables t
      WHERE table_schema IN ('company', 'people', 'marketing')
        AND table_type = 'BASE TABLE'
      ORDER BY table_schema, table_name;
    `;
    const tablesResult = await client.query(tablesQuery);
    
    console.log('📋 Tables in place:');
    let currentSchema = '';
    tablesResult.rows.forEach(row => {
      if (currentSchema !== row.table_schema) {
        currentSchema = row.table_schema;
        console.log(`\n  ${currentSchema} schema:`);
      }
      console.log(`    ✅ ${row.table_name} (${row.column_count} columns)`);
    });

    // Check views
    const viewsQuery = `
      SELECT 
        table_schema,
        table_name
      FROM information_schema.views
      WHERE table_schema IN ('company', 'people', 'marketing')
      ORDER BY table_schema, table_name;
    `;
    const viewsResult = await client.query(viewsQuery);
    
    console.log('\n👁️ Views created:');
    currentSchema = '';
    viewsResult.rows.forEach(row => {
      if (currentSchema !== row.table_schema) {
        currentSchema = row.table_schema;
        console.log(`\n  ${currentSchema} schema:`);
      }
      console.log(`    ✅ ${row.table_name}`);
    });

    // Summary statistics
    console.log('\n' + '='.repeat(60));
    console.log('📊 LEAN SCHEMA SUMMARY:');
    console.log(`   • Tables: ${tablesResult.rows.length}`);
    console.log(`   • Views: ${viewsResult.rows.length}`);
    
    // Count records in key tables
    const countQueries = [
      { schema: 'company', table: 'company' },
      { schema: 'company', table: 'company_slot' },
      { schema: 'people', table: 'contact' },
      { schema: 'marketing', table: 'campaign' }
    ];
    
    console.log('\n📈 Record Counts:');
    for (const q of countQueries) {
      try {
        const countResult = await client.query(
          `SELECT COUNT(*) as count FROM ${q.schema}.${q.table}`
        );
        console.log(`   • ${q.schema}.${q.table}: ${countResult.rows[0].count} records`);
      } catch (err) {
        console.log(`   • ${q.schema}.${q.table}: Error counting`);
      }
    }

    console.log('\n✅ Lean Outreach Database Schema Ready!');
    console.log('🎯 Key Features:');
    console.log('   • Slot-based contact management (CEO, CFO, HR)');
    console.log('   • Zero-wandering scraper queues');
    console.log('   • Automatic renewal campaign tracking');
    console.log('   • Email verification status tracking');
    console.log('   • Compatibility views for legacy code');

  } catch (error) {
    console.error('❌ Error setting up schema:', error.message);
    
    if (error.code === '42P07') {
      console.log('\n💡 Some objects already exist. This is expected.');
    } else {
      console.log('\n💡 Debug information:');
      console.log('   Error Code:', error.code);
      console.log('   Detail:', error.detail);
      console.log('   Hint:', error.hint);
    }
    
    throw error;
  } finally {
    await client.end();
    console.log('\n🔌 Database connection closed');
  }
}

// Run the setup
setupLeanOutreachSchema().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
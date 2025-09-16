#!/usr/bin/env node
/**
 * Setup Cold Outreach Database Schema
 * Creates all required schemas, tables, types, and views for the cold outreach system
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

async function setupColdOutreachSchema() {
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
    const sqlPath = path.join(__dirname, '..', 'infra', 'cold-outreach-schema.sql');
    console.log(`📄 Reading SQL from: ${sqlPath}`);
    const sql = fs.readFileSync(sqlPath, 'utf8');

    console.log('🚀 Executing Cold Outreach Schema...');
    console.log('=' * 60);
    
    // Execute the entire SQL file
    await client.query(sql);
    
    console.log('✅ Schema creation completed successfully!\n');

    // Verify what was created
    console.log('📊 Verifying created objects...\n');

    // Check schemas
    const schemasQuery = `
      SELECT nspname as schema_name 
      FROM pg_namespace 
      WHERE nspname IN ('company', 'people', 'marketing', 'bit', 'ple')
      ORDER BY nspname;
    `;
    const schemasResult = await client.query(schemasQuery);
    console.log('📁 Schemas created:');
    schemasResult.rows.forEach(row => {
      console.log(`   ✅ ${row.schema_name}`);
    });

    // Check types
    const typesQuery = `
      SELECT 
        n.nspname as schema_name,
        t.typname as type_name
      FROM pg_type t
      JOIN pg_namespace n ON n.oid = t.typnamespace
      WHERE n.nspname IN ('company', 'people')
        AND t.typname IN ('role_code_t', 'email_status_t')
      ORDER BY n.nspname, t.typname;
    `;
    const typesResult = await client.query(typesQuery);
    console.log('\n🏷️ Types created:');
    typesResult.rows.forEach(row => {
      console.log(`   ✅ ${row.schema_name}.${row.type_name}`);
    });

    // Check tables
    const tablesQuery = `
      SELECT 
        table_schema,
        table_name,
        (SELECT COUNT(*) FROM information_schema.columns 
         WHERE table_schema = t.table_schema 
         AND table_name = t.table_name) as column_count
      FROM information_schema.tables t
      WHERE table_schema IN ('company', 'people', 'marketing', 'bit')
        AND table_type = 'BASE TABLE'
      ORDER BY table_schema, table_name;
    `;
    const tablesResult = await client.query(tablesQuery);
    console.log('\n📋 Tables created:');
    tablesResult.rows.forEach(row => {
      console.log(`   ✅ ${row.table_schema}.${row.table_name} (${row.column_count} columns)`);
    });

    // Check views
    const viewsQuery = `
      SELECT 
        table_schema,
        table_name
      FROM information_schema.views
      WHERE table_schema IN ('company', 'people')
      ORDER BY table_schema, table_name;
    `;
    const viewsResult = await client.query(viewsQuery);
    console.log('\n👁️ Views created:');
    viewsResult.rows.forEach(row => {
      console.log(`   ✅ ${row.table_schema}.${row.table_name}`);
    });

    // Check indexes
    const indexesQuery = `
      SELECT 
        schemaname,
        tablename,
        indexname
      FROM pg_indexes
      WHERE schemaname IN ('company', 'people', 'marketing', 'bit')
        AND indexname NOT LIKE '%_pkey'
        AND indexname NOT LIKE '%_key'
      ORDER BY schemaname, tablename, indexname;
    `;
    const indexesResult = await client.query(indexesQuery);
    console.log('\n🔍 Indexes created:');
    const indexByTable = {};
    indexesResult.rows.forEach(row => {
      const key = `${row.schemaname}.${row.tablename}`;
      if (!indexByTable[key]) {
        indexByTable[key] = [];
      }
      indexByTable[key].push(row.indexname);
    });
    Object.entries(indexByTable).forEach(([table, indexes]) => {
      console.log(`   ${table}:`);
      indexes.forEach(idx => console.log(`      ✅ ${idx}`));
    });

    // Summary statistics
    console.log('\n' + '=' * 60);
    console.log('📊 SUMMARY:');
    console.log(`   • Schemas: ${schemasResult.rows.length}`);
    console.log(`   • Types: ${typesResult.rows.length}`);
    console.log(`   • Tables: ${tablesResult.rows.length}`);
    console.log(`   • Views: ${viewsResult.rows.length}`);
    console.log(`   • Custom Indexes: ${indexesResult.rows.length}`);
    console.log('=' * 60);

    // Show queue views for scraping
    console.log('\n🤖 Zero-Wandering Scraper Queues:');
    console.log('   • company.next_company_urls_30d - Companies due for URL scraping');
    console.log('   • people.next_profile_urls_30d - Profiles due for scraping');
    console.log('   • people.due_email_recheck_30d - Emails due for re-verification');
    console.log('   • company.vw_due_renewals_ready - Companies in renewal window with green contacts');

    console.log('\n✅ Cold Outreach Database Schema Setup Complete!');
    console.log('🎉 Your database is ready for the complete pipeline:');
    console.log('   Ingestor → Neon → Apify → PLE → Bit');

  } catch (error) {
    console.error('❌ Error setting up schema:', error.message);
    
    if (error.code === '42P07') {
      console.log('\n💡 Some objects already exist. This is normal if running multiple times.');
    } else if (error.code === '42883') {
      console.log('\n💡 Function or type issue. Check PostgreSQL version compatibility.');
    } else {
      console.log('\n💡 Debug information:');
      console.log('   Error Code:', error.code);
      console.log('   Detail:', error.detail);
      console.log('   Hint:', error.hint);
      console.log('   Position:', error.position);
    }
    
    throw error;
  } finally {
    await client.end();
    console.log('\n🔌 Database connection closed');
  }
}

// Run the setup
setupColdOutreachSchema().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
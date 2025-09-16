#!/usr/bin/env node
/**
 * Check existing views that might conflict with our schema
 */

import pg from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const { Client } = pg;

async function checkExistingViews() {
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

    // Check existing views in all relevant schemas
    const viewsQuery = `
      SELECT 
        schemaname,
        viewname,
        viewowner
      FROM pg_views
      WHERE schemaname IN ('company', 'people', 'marketing', 'bit', 'ple', 'public')
      ORDER BY schemaname, viewname;
    `;
    
    console.log('📊 Checking existing views...\n');
    const viewsResult = await client.query(viewsQuery);
    
    if (viewsResult.rows.length > 0) {
      console.log('👁️ Existing views found:');
      viewsResult.rows.forEach(row => {
        console.log(`   • ${row.schemaname}.${row.viewname} (owner: ${row.viewowner})`);
      });
      
      // Generate DROP statements for conflicting views
      console.log('\n💡 To drop these views (if needed), run:');
      viewsResult.rows.forEach(row => {
        console.log(`   DROP VIEW IF EXISTS ${row.schemaname}.${row.viewname} CASCADE;`);
      });
    } else {
      console.log('✅ No existing views found in target schemas');
    }

    // Check for existing types
    const typesQuery = `
      SELECT 
        n.nspname as schema_name,
        t.typname as type_name
      FROM pg_type t
      JOIN pg_namespace n ON n.oid = t.typnamespace
      WHERE n.nspname IN ('company', 'people')
        AND t.typtype = 'e'
      ORDER BY n.nspname, t.typname;
    `;
    
    console.log('\n🏷️ Checking existing types...');
    const typesResult = await client.query(typesQuery);
    
    if (typesResult.rows.length > 0) {
      console.log('Existing enum types found:');
      typesResult.rows.forEach(row => {
        console.log(`   • ${row.schema_name}.${row.type_name}`);
      });
    } else {
      console.log('✅ No existing enum types found');
    }

    // Check for tables that might have dependencies
    const tablesQuery = `
      SELECT 
        schemaname,
        tablename
      FROM pg_tables
      WHERE schemaname IN ('company', 'people', 'marketing', 'bit', 'ple')
      ORDER BY schemaname, tablename;
    `;
    
    console.log('\n📋 Checking existing tables...');
    const tablesResult = await client.query(tablesQuery);
    
    if (tablesResult.rows.length > 0) {
      console.log('Existing tables found:');
      tablesResult.rows.forEach(row => {
        console.log(`   • ${row.schemaname}.${row.tablename}`);
      });
    } else {
      console.log('✅ No existing tables found in target schemas');
    }

  } catch (error) {
    console.error('❌ Error:', error.message);
  } finally {
    await client.end();
    console.log('\n🔌 Database connection closed');
  }
}

// Run the check
checkExistingViews().catch(console.error);
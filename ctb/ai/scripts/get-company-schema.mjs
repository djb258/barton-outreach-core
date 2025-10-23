/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ai/scripts
Barton ID: 03.01.04
Unique ID: CTB-A099FDBC
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

#!/usr/bin/env node

/**
 * Retrieve Complete Company & People Schema Information from Neon
 * Comprehensive schema inspection for the integrated company/people database
 */

import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function getCompleteSchema() {
  console.log('🔍 Retrieving Complete Neon Schema (Company & People)...\n');
  
  try {
    // Get connection string - check multiple possible env vars
    const connectionString = 
      process.env.NEON_DATABASE_URL ||
      process.env.DATABASE_URL ||
      process.env.NEON_MARKETING_DB_URL ||
      process.env.MARKETING_DATABASE_URL;
    
    if (!connectionString) {
      console.error('❌ No database connection string found.');
      console.log('Please set one of these environment variables:');
      console.log('  - NEON_DATABASE_URL');
      console.log('  - DATABASE_URL');
      console.log('  - NEON_MARKETING_DB_URL');
      console.log('  - MARKETING_DATABASE_URL');
      return;
    }
    
    const sql = neon(connectionString);
    
    console.log('📊 Checking complete schema structure...\n');
    
    // Get all schemas
    const schemasQuery = `
      SELECT schema_name 
      FROM information_schema.schemata 
      WHERE schema_name IN ('company', 'people', 'intake', 'vault', 'marketing')
      ORDER BY schema_name;
    `;
    
    const schemas = await sql(schemasQuery);
    
    if (schemas.length === 0) {
      console.log('⚠️  No target schemas found. Available schemas:');
      
      const allSchemasQuery = `
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        ORDER BY schema_name;
      `;
      
      const allSchemas = await sql(allSchemasQuery);
      allSchemas.forEach(schema => {
        console.log(`  • ${schema.schema_name}`);
      });
      return;
    }
    
    console.log('✅ Found schemas:');
    schemas.forEach(schema => {
      console.log(`  • ${schema.schema_name}`);
    });
    console.log('');
    
    // Get tables for each schema
    for (const schema of schemas) {
      console.log(`📋 Tables in ${schema.schema_name} schema:`);
      console.log('=' .repeat(50));
      
      const tablesQuery = `
        SELECT table_name, table_type
        FROM information_schema.tables 
        WHERE table_schema = $1
        ORDER BY table_name;
      `;
      
      const tables = await sql(tablesQuery, [schema.schema_name]);
      
      for (const table of tables) {
        console.log(`\n🔧 ${schema.schema_name}.${table.table_name} (${table.table_type})`);
        
        // Get column information for each table
        const columnQuery = `
          SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length,
            numeric_precision,
            numeric_scale,
            ordinal_position
          FROM information_schema.columns 
          WHERE table_schema = $1 
            AND table_name = $2
          ORDER BY ordinal_position;
        `;
        
        const columns = await sql(columnQuery, [schema.schema_name, table.table_name]);
        
        columns.forEach((column, index) => {
          const typeInfo = column.character_maximum_length 
            ? `${column.data_type}(${column.character_maximum_length})`
            : column.data_type;
          
          console.log(`  ${index + 1}. ${column.column_name}: ${typeInfo}${column.is_nullable === 'NO' ? ' NOT NULL' : ''}`);
          
          if (column.column_default) {
            console.log(`     DEFAULT: ${column.column_default}`);
          }
        });
      }
      console.log('');
    }
    
    // Check for foreign key relationships
    console.log('🔗 Foreign Key Relationships:');
    console.log('=' .repeat(50));
    
    const fkQuery = `
      SELECT 
        tc.table_schema,
        tc.table_name,
        kcu.column_name,
        ccu.table_schema AS foreign_table_schema,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name,
        tc.constraint_name
      FROM information_schema.table_constraints AS tc 
      JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
      JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
      WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND tc.table_schema IN ('company', 'people', 'intake', 'vault', 'marketing')
      ORDER BY tc.table_schema, tc.table_name;
    `;
    
    const foreignKeys = await sql(fkQuery);
    
    foreignKeys.forEach(fk => {
      console.log(`${fk.table_schema}.${fk.table_name}.${fk.column_name} → ${fk.foreign_table_schema}.${fk.foreign_table_name}.${fk.foreign_column_name}`);
    });
    console.log('');
    
    // Check for secure functions
    console.log('🔒 Secure Functions (SECURITY DEFINER):');
    console.log('=' .repeat(50));
    
    const functionsQuery = `
      SELECT 
        n.nspname as schema_name,
        p.proname as function_name,
        pg_get_function_result(p.oid) as return_type,
        p.prosecdef as is_security_definer
      FROM pg_proc p
      JOIN pg_namespace n ON p.pronamespace = n.oid
      WHERE n.nspname IN ('intake', 'vault')
        AND p.prosecdef = true
      ORDER BY n.nspname, p.proname;
    `;
    
    const functions = await sql(functionsQuery);
    
    if (functions.length > 0) {
      functions.forEach(fn => {
        console.log(`✅ ${fn.schema_name}.${fn.function_name}() → ${fn.return_type}`);
      });
    } else {
      console.log('⚠️  No SECURITY DEFINER functions found. Run neon-company-schema.sql to create them.');
    }
    console.log('');
    
    // Sample data counts
    console.log('📊 Data Summary:');
    console.log('=' .repeat(50));
    
    const tableCounts = [
      ['company.company', 'Companies'],
      ['company.company_slot', 'Company Slots'],
      ['people.contact', 'Contacts'],
      ['intake.raw_loads', 'Raw Loads'],
      ['vault.contact_promotions', 'Promotions']
    ];
    
    for (const [tableName, label] of tableCounts) {
      try {
        const countResult = await sql(`SELECT COUNT(*) as count FROM ${tableName}`);
        console.log(`${label}: ${countResult[0].count} records`);
      } catch (error) {
        console.log(`${label}: Table not found or no access`);
      }
    }
    
    console.log('\n✅ Complete schema analysis finished!\n');
    
  } catch (error) {
    console.error('❌ Error retrieving schema:', error.message);
    
    if (error.message.includes('permission denied')) {
      console.log('\n💡 Permission denied. Make sure your user has SELECT permissions on:');
      console.log('  • information_schema.*');
      console.log('  • All target schemas (company, people, intake, vault)');
    }
    
    if (error.message.includes('does not exist')) {
      console.log('\n💡 Schema/table may not exist. Run neon-company-schema.sql first:');
      console.log('  • Execute the schema creation script in Neon');
      console.log('  • Verify database name in connection string');
    }
  }
}

// Run the schema analysis
getCompleteSchema().catch(console.error);
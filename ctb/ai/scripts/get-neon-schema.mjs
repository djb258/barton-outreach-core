/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ai/scripts
Barton ID: 03.01.04
Unique ID: CTB-3C4D1938
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

#!/usr/bin/env node

/**
 * Retrieve Neon Marketing DB Schema Information
 * Gets column details from company.marketing_company table
 */

import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function getNeonSchema() {
  console.log('🔍 Retrieving Neon Marketing DB Schema...\n');
  
  try {
    // Get connection string - check multiple possible env vars
    const connectionString = 
      process.env.NEON_MARKETING_DB_URL ||
      process.env.MARKETING_DATABASE_URL ||
      process.env.DATABASE_URL ||
      process.env.NEON_DATABASE_URL ||
      // Direct connection string for Neon Marketing DB
      "postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/Marketing%20DB?sslmode=require&channel_binding=require";
    
    if (!connectionString) {
      console.error('❌ No database connection string found.');
      console.log('Please set one of these environment variables:');
      console.log('  - NEON_MARKETING_DB_URL');
      console.log('  - MARKETING_DATABASE_URL');
      console.log('  - DATABASE_URL');
      console.log('  - NEON_DATABASE_URL');
      return;
    }
    
    const sql = neon(connectionString);
    
    console.log('📊 Checking company.marketing_company table structure...\n');
    
    // Query to get column information
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
      WHERE table_schema = 'company' 
        AND table_name = 'marketing_company'
      ORDER BY ordinal_position;
    `;
    
    const columns = await sql(columnQuery);
    
    if (columns.length === 0) {
      console.log('⚠️  Table company.marketing_company not found.');
      console.log('Let me check what tables exist in the company schema...\n');
      
      const tablesQuery = `
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'company'
        ORDER BY table_name;
      `;
      
      const tables = await sql(tablesQuery);
      
      if (tables.length === 0) {
        console.log('⚠️  Schema "company" not found. Checking available schemas...\n');
        
        const schemasQuery = `
          SELECT schema_name 
          FROM information_schema.schemata 
          WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
          ORDER BY schema_name;
        `;
        
        const schemas = await sql(schemasQuery);
        
        console.log('📋 Available schemas:');
        schemas.forEach(schema => {
          console.log(`  • ${schema.schema_name}`);
        });
      } else {
        console.log('📋 Tables in company schema:');
        tables.forEach(table => {
          console.log(`  • ${table.table_name}`);
        });
      }
      
      return;
    }
    
    // Display column information
    console.log('✅ Found company.marketing_company table!\n');
    console.log('📋 Column Information:');
    console.log('=' . repeat(80));
    
    columns.forEach((column, index) => {
      console.log(`${index + 1}. ${column.column_name}`);
      console.log(`   Type: ${column.data_type}${column.character_maximum_length ? `(${column.character_maximum_length})` : ''}`);
      console.log(`   Nullable: ${column.is_nullable}`);
      if (column.column_default) {
        console.log(`   Default: ${column.column_default}`);
      }
      console.log('');
    });
    
    // Generate TypeScript interface
    console.log('🔧 Generated TypeScript Interface:');
    console.log('=' . repeat(50));
    console.log('interface MarketingCompany {');
    
    columns.forEach(column => {
      const tsType = mapPostgresToTypeScript(column.data_type);
      const optional = column.is_nullable === 'YES' || column.column_default ? '?' : '';
      console.log(`  ${column.column_name}${optional}: ${tsType};`);
    });
    
    console.log('}\n');
    
    // Generate SQL for our ingestion function
    console.log('📝 SQL Integration for Ingestion:');
    console.log('=' . repeat(50));
    console.log('-- Example INSERT for company.marketing_company');
    console.log('INSERT INTO company.marketing_company (');
    
    const insertableColumns = columns.filter(col => 
      !col.column_default?.includes('nextval') && // Skip auto-increment
      col.column_name !== 'created_at' && 
      col.column_name !== 'updated_at'
    );
    
    console.log('  ' + insertableColumns.map(col => col.column_name).join(',\n  '));
    console.log(') VALUES (');
    console.log('  ' + insertableColumns.map(() => '$?').join(',\n  '));
    console.log(');\n');
    
    // Show sample data if available
    try {
      const sampleQuery = `SELECT * FROM company.marketing_company LIMIT 3`;
      const sampleData = await sql(sampleQuery);
      
      if (sampleData.length > 0) {
        console.log('📊 Sample Data (first 3 rows):');
        console.log('=' . repeat(50));
        console.table(sampleData);
      }
    } catch (error) {
      console.log('ℹ️  Unable to retrieve sample data (permissions may be required)');
    }
    
    console.log('✅ Schema retrieval complete!\n');
    
  } catch (error) {
    console.error('❌ Error retrieving schema:', error.message);
    
    if (error.message.includes('permission denied')) {
      console.log('\n💡 Permission denied. Make sure your user has SELECT permissions on:');
      console.log('  • information_schema.columns');
      console.log('  • information_schema.tables');
      console.log('  • company.marketing_company');
    }
    
    if (error.message.includes('does not exist')) {
      console.log('\n💡 Database/schema/table may not exist. Please verify:');
      console.log('  • Database name in connection string');
      console.log('  • Schema name: "company"');
      console.log('  • Table name: "marketing_company"');
    }
  }
}

// Helper function to map PostgreSQL types to TypeScript
function mapPostgresToTypeScript(pgType) {
  const typeMap = {
    'integer': 'number',
    'bigint': 'number',
    'smallint': 'number',
    'decimal': 'number',
    'numeric': 'number',
    'real': 'number',
    'double precision': 'number',
    'serial': 'number',
    'bigserial': 'number',
    'character varying': 'string',
    'varchar': 'string',
    'character': 'string',
    'char': 'string',
    'text': 'string',
    'boolean': 'boolean',
    'date': 'string', // ISO date string
    'timestamp': 'string', // ISO datetime string
    'timestamp with time zone': 'string',
    'timestamptz': 'string',
    'time': 'string',
    'jsonb': 'Record<string, any>',
    'json': 'Record<string, any>',
    'uuid': 'string',
    'inet': 'string',
    'cidr': 'string'
  };
  
  return typeMap[pgType.toLowerCase()] || 'any';
}

// Helper for string repeat
String.prototype.repeat = String.prototype.repeat || function(count) {
  return new Array(count + 1).join(this);
};

// Run the schema retrieval
getNeonSchema().catch(console.error);
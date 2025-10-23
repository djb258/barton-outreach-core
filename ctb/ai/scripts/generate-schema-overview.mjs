/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ai/scripts
Barton ID: 03.01.04
Unique ID: CTB-3CA5AAE7
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

#!/usr/bin/env node

/**
 * Generate Complete Schema Overview
 * Comprehensive documentation of all schemas, tables, columns, and relationships
 */

import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function generateSchemaOverview() {
  console.log('📋 Generating Complete Schema Overview...\n');
  
  try {
    const sql = neon(process.env.NEON_DATABASE_URL || process.env.DATABASE_URL);
    
    console.log('📡 Connected to Neon database');
    console.log('');

    // Get all schemas
    const schemas = await sql`
      SELECT schema_name 
      FROM information_schema.schemata 
      WHERE schema_name IN ('company', 'people', 'marketing', 'bit', 'intake', 'vault', 'admin')
      ORDER BY schema_name
    `;

    console.log('🏗️ COMPLETE SCHEMA OVERVIEW');
    console.log('=' .repeat(80));
    console.log('');

    // Process each schema
    for (const schema of schemas) {
      console.log(`📂 SCHEMA: ${schema.schema_name.toUpperCase()}`);
      console.log('-' .repeat(50));
      
      // Get all tables and views in this schema
      const tables = await sql`
        SELECT table_name, table_type
        FROM information_schema.tables 
        WHERE table_schema = ${schema.schema_name}
        ORDER BY 
          CASE WHEN table_type = 'BASE TABLE' THEN 1 ELSE 2 END,
          table_name
      `;

      for (const table of tables) {
        const isView = table.table_type === 'VIEW';
        console.log(`\n${isView ? '👁️' : '📄'} ${schema.schema_name}.${table.table_name} (${table.table_type})`);
        
        // Get columns
        const columns = await sql`
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
          WHERE table_schema = ${schema.schema_name} 
            AND table_name = ${table.table_name}
          ORDER BY ordinal_position
        `;

        columns.forEach((column, index) => {
          let typeInfo = column.data_type;
          if (column.character_maximum_length) {
            typeInfo += `(${column.character_maximum_length})`;
          } else if (column.numeric_precision) {
            typeInfo += `(${column.numeric_precision}${column.numeric_scale ? ',' + column.numeric_scale : ''})`;
          }

          const nullable = column.is_nullable === 'YES' ? '' : ' NOT NULL';
          const defaultVal = column.column_default ? ` DEFAULT ${column.column_default}` : '';
          
          console.log(`   ${index + 1}. ${column.column_name}: ${typeInfo}${nullable}${defaultVal}`);
        });
      }
      console.log('');
    }

    // Get all foreign key relationships
    console.log('🔗 FOREIGN KEY RELATIONSHIPS');
    console.log('-' .repeat(50));
    
    const foreignKeys = await sql`
      SELECT 
        tc.table_schema,
        tc.table_name,
        kcu.column_name,
        ccu.table_schema AS foreign_table_schema,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name,
        tc.constraint_name,
        rc.delete_rule,
        rc.update_rule
      FROM information_schema.table_constraints AS tc 
      JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
      JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
      JOIN information_schema.referential_constraints AS rc
        ON tc.constraint_name = rc.constraint_name
      WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND tc.table_schema IN ('company', 'people', 'marketing', 'bit', 'intake', 'vault', 'admin')
      ORDER BY tc.table_schema, tc.table_name, kcu.column_name
    `;

    foreignKeys.forEach(fk => {
      const deleteAction = fk.delete_rule !== 'NO ACTION' ? ` ON DELETE ${fk.delete_rule}` : '';
      const updateAction = fk.update_rule !== 'NO ACTION' ? ` ON UPDATE ${fk.update_rule}` : '';
      console.log(`${fk.table_schema}.${fk.table_name}.${fk.column_name}`);
      console.log(`  → ${fk.foreign_table_schema}.${fk.foreign_table_name}.${fk.foreign_column_name}${deleteAction}${updateAction}`);
    });
    console.log('');

    // Get all stored functions
    console.log('⚙️ STORED FUNCTIONS');
    console.log('-' .repeat(50));
    
    const functions = await sql`
      SELECT 
        n.nspname as schema_name,
        p.proname as function_name,
        pg_get_function_result(p.oid) as return_type,
        pg_get_function_arguments(p.oid) as arguments
      FROM pg_proc p
      JOIN pg_namespace n ON p.pronamespace = n.oid
      WHERE n.nspname IN ('company', 'people', 'marketing', 'bit', 'intake', 'vault', 'admin')
      ORDER BY n.nspname, p.proname
    `;

    functions.forEach(fn => {
      console.log(`${fn.schema_name}.${fn.function_name}(${fn.arguments || ''})`);
      console.log(`  Returns: ${fn.return_type}`);
    });
    console.log('');

    // Get all indexes
    console.log('📊 INDEXES');
    console.log('-' .repeat(50));
    
    const indexes = await sql`
      SELECT 
        schemaname,
        tablename,
        indexname,
        indexdef
      FROM pg_indexes
      WHERE schemaname IN ('company', 'people', 'marketing', 'bit', 'intake', 'vault', 'admin')
        AND indexname NOT LIKE '%_pkey'
      ORDER BY schemaname, tablename, indexname
    `;

    let currentTable = '';
    indexes.forEach(idx => {
      const tableKey = `${idx.schemaname}.${idx.tablename}`;
      if (tableKey !== currentTable) {
        console.log(`\n📄 ${tableKey}:`);
        currentTable = tableKey;
      }
      console.log(`  • ${idx.indexname}`);
    });
    console.log('');

    // Generate summary statistics
    console.log('📈 SCHEMA STATISTICS');
    console.log('-' .repeat(50));
    
    const stats = await sql`
      SELECT 
        table_schema,
        COUNT(CASE WHEN table_type = 'BASE TABLE' THEN 1 END) as tables,
        COUNT(CASE WHEN table_type = 'VIEW' THEN 1 END) as views,
        COUNT(*) as total_objects
      FROM information_schema.tables 
      WHERE table_schema IN ('company', 'people', 'marketing', 'bit', 'intake', 'vault', 'admin')
      GROUP BY table_schema
      ORDER BY table_schema
    `;

    stats.forEach(stat => {
      console.log(`${stat.table_schema}: ${stat.tables} tables, ${stat.views} views (${stat.total_objects} total)`);
    });

    const totalFunctions = functions.length;
    const totalIndexes = indexes.length;
    const totalForeignKeys = foreignKeys.length;

    console.log(`Functions: ${totalFunctions}`);
    console.log(`Indexes: ${totalIndexes}`);
    console.log(`Foreign Keys: ${totalForeignKeys}`);
    console.log('');

    // Generate ChatGPT-friendly summary
    console.log('🤖 CHATGPT REVIEW FORMAT');
    console.log('=' .repeat(80));
    console.log('');
    console.log('**COMPLETE SCHEMA STRUCTURE FOR REVIEW**');
    console.log('');
    
    // Regenerate in a more structured format for ChatGPT
    for (const schema of schemas) {
      console.log(`**${schema.schema_name.toUpperCase()} SCHEMA:**`);
      
      const tables = await sql`
        SELECT table_name, table_type
        FROM information_schema.tables 
        WHERE table_schema = ${schema.schema_name}
        ORDER BY 
          CASE WHEN table_type = 'BASE TABLE' THEN 1 ELSE 2 END,
          table_name
      `;

      for (const table of tables) {
        const columns = await sql`
          SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
          FROM information_schema.columns 
          WHERE table_schema = ${schema.schema_name} 
            AND table_name = ${table.table_name}
          ORDER BY ordinal_position
        `;

        console.log(`\n${table.table_name} (${table.table_type}):`);
        columns.forEach(col => {
          const nullable = col.is_nullable === 'YES' ? ' NULL' : ' NOT NULL';
          const defaultVal = col.column_default ? ` DEFAULT ${col.column_default}` : '';
          console.log(`- ${col.column_name}: ${col.data_type}${nullable}${defaultVal}`);
        });
      }
      console.log('');
    }

    console.log('**RELATIONSHIPS:**');
    foreignKeys.forEach(fk => {
      console.log(`- ${fk.table_schema}.${fk.table_name}.${fk.column_name} → ${fk.foreign_table_schema}.${fk.foreign_table_name}.${fk.foreign_column_name} (${fk.delete_rule})`);
    });
    console.log('');

    console.log('**KEY FUNCTIONS:**');
    functions.forEach(fn => {
      console.log(`- ${fn.schema_name}.${fn.function_name}() → ${fn.return_type}`);
    });
    console.log('');

    console.log('**SYSTEM PURPOSE:**');
    console.log('This is a complete outreach management system with:');
    console.log('- Company and contact management');
    console.log('- Email verification and status tracking');
    console.log('- Marketing campaign and handoff workflows');
    console.log('- Business intelligence trigger system (BIT)');
    console.log('- Data refresh orchestration with source tracking');
    console.log('- Renewal management and opportunity tracking');
    console.log('');

    console.log('🎉 Schema Overview Generation Complete!');
    console.log('\n💡 Copy the "CHATGPT REVIEW FORMAT" section above to ChatGPT for validation');

  } catch (error) {
    console.error('❌ Schema overview generation failed:', error.message);
  }
}

generateSchemaOverview().catch(console.error);
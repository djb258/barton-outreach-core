#!/usr/bin/env node
/**
 * Generate Database Schema Diagram
 * Creates a visual representation of table relationships
 */

import pg from 'pg';
import dotenv from 'dotenv';
import fs from 'fs';

dotenv.config();

const { Client } = pg;

async function generateSchemaDiagram() {
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

    // Get all tables and their relationships
    const relationshipsQuery = `
      SELECT 
        tc.table_schema,
        tc.table_name,
        tc.constraint_name,
        tc.constraint_type,
        kcu.column_name,
        ccu.table_schema AS foreign_table_schema,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
      FROM information_schema.table_constraints tc
      LEFT JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
      LEFT JOIN information_schema.constraint_column_usage ccu
        ON tc.constraint_name = ccu.constraint_name
        AND tc.table_schema = ccu.table_schema
      WHERE tc.table_schema IN ('company', 'people', 'marketing', 'bit')
        AND tc.constraint_type IN ('FOREIGN KEY', 'PRIMARY KEY')
      ORDER BY tc.table_schema, tc.table_name, tc.constraint_type;
    `;

    const relationshipsResult = await client.query(relationshipsQuery);

    // Get table columns
    const columnsQuery = `
      SELECT 
        table_schema,
        table_name,
        column_name,
        data_type,
        is_nullable,
        column_default
      FROM information_schema.columns
      WHERE table_schema IN ('company', 'people', 'marketing', 'bit')
        AND table_name NOT LIKE 'marketing_%'
      ORDER BY table_schema, table_name, ordinal_position;
    `;

    const columnsResult = await client.query(columnsQuery);

    // Generate Mermaid ER diagram
    let mermaidDiagram = `erDiagram\n\n`;

    // Group tables by schema
    const tablesBySchema = {};
    const relationships = [];
    
    columnsResult.rows.forEach(row => {
      const schemaTable = `${row.table_schema}_${row.table_name}`;
      if (!tablesBySchema[schemaTable]) {
        tablesBySchema[schemaTable] = {
          schema: row.table_schema,
          table: row.table_name,
          columns: []
        };
      }
      
      let columnDef = `${row.data_type}`;
      if (row.is_nullable === 'NO') columnDef += ' NOT_NULL';
      if (row.column_default && row.column_default.includes('nextval')) columnDef += ' PK';
      
      tablesBySchema[schemaTable].columns.push({
        name: row.column_name,
        type: columnDef
      });
    });

    // Add table definitions
    Object.values(tablesBySchema).forEach(table => {
      mermaidDiagram += `    ${table.schema}_${table.table} {\n`;
      table.columns.forEach(col => {
        mermaidDiagram += `        ${col.type} ${col.name}\n`;
      });
      mermaidDiagram += `    }\n\n`;
    });

    // Add relationships
    relationshipsResult.rows.forEach(row => {
      if (row.constraint_type === 'FOREIGN KEY' && row.foreign_table_name) {
        const sourceTable = `${row.table_schema}_${row.table_name}`;
        const targetTable = `${row.foreign_table_schema}_${row.foreign_table_name}`;
        mermaidDiagram += `    ${sourceTable} }|--|| ${targetTable} : "belongs to"\n`;
      }
    });

    // Save the diagram
    fs.writeFileSync('./SCHEMA_DIAGRAM.md', `# Database Schema Diagram

\`\`\`mermaid
${mermaidDiagram}
\`\`\`

## Schema Relationships Summary

### Core Tables
- **company.company**: Central company repository
- **company.company_slot**: Role-based contact slots (CEO, CFO, HR)
- **people.contact**: Contact information
- **people.contact_verification**: Email verification status

### Marketing Tables
- **marketing.campaign**: Campaign definitions
- **marketing.campaign_contact**: Campaign participants
- **marketing.message_log**: Communication tracking
- **marketing.booking_event**: Meeting bookings
- **marketing.ac_handoff**: Account handoffs

### Intent Tracking
- **bit.signal**: Buyer intent signals

### Key Relationships
1. Each company has exactly 3 slots (CEO, CFO, HR)
2. Each slot can have one contact assigned
3. Each contact has one verification record
4. Contacts can participate in multiple campaigns
5. All communications are logged in message_log

### Queue Views (Auto-Generated)
- \`company.next_company_urls_30d\` - URLs due for scraping
- \`people.next_profile_urls_30d\` - Profiles due for scraping  
- \`people.due_email_recheck_30d\` - Emails due for verification
- \`company.vw_due_renewals_ready\` - Companies ready for renewal campaigns
`);

    console.log('📊 Schema Analysis:');
    console.log(`   • Total Tables: ${Object.keys(tablesBySchema).length}`);
    console.log(`   • Foreign Key Relationships: ${relationshipsResult.rows.filter(r => r.constraint_type === 'FOREIGN KEY').length}`);
    
    console.log('\n📄 Generated Files:');
    console.log('   ✅ SCHEMA_DIAGRAM.md - Mermaid ER diagram');
    console.log('   ✅ DATABASE_SCHEMA.md - Comprehensive documentation');

    // Generate table summary
    console.log('\n📋 Table Summary by Schema:');
    const schemaGroups = {};
    Object.values(tablesBySchema).forEach(table => {
      if (!schemaGroups[table.schema]) {
        schemaGroups[table.schema] = [];
      }
      schemaGroups[table.schema].push(table.table);
    });

    Object.entries(schemaGroups).forEach(([schema, tables]) => {
      console.log(`\n   ${schema.toUpperCase()} Schema (${tables.length} tables):`);
      tables.forEach(table => {
        console.log(`     • ${table}`);
      });
    });

    console.log('\n✅ Schema documentation generation complete!');

  } catch (error) {
    console.error('❌ Error generating schema diagram:', error.message);
  } finally {
    await client.end();
    console.log('\n🔌 Database connection closed');
  }
}

// Run the generation
generateSchemaDiagram().catch(console.error);
#!/usr/bin/env node

/**
 * PLE Schema Compliance Audit Script
 *
 * Purpose: Identify violations, check constraints, audit columns, and generate field mapping
 *
 * Barton ID: 04.04.02.04.50000.001
 */

const { Client } = require('pg');
const fs = require('fs');
const path = require('path');

// Database connection from environment
const connectionString = process.env.DATABASE_URL || process.env.NEON_CONNECTION_STRING;

if (!connectionString) {
  console.error('ERROR: No database connection string found in environment');
  process.exit(1);
}

const client = new Client({ connectionString });

// ANSI color codes for output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
};

async function main() {
  try {
    await client.connect();
    console.log(`${colors.green}✓ Connected to Neon PostgreSQL${colors.reset}\n`);

    // PHASE 1: IDENTIFY VIOLATIONS
    console.log(`${colors.bright}${colors.cyan}═══════════════════════════════════════════════════════════${colors.reset}`);
    console.log(`${colors.bright}${colors.cyan}PHASE 1: IDENTIFY VIOLATIONS${colors.reset}`);
    console.log(`${colors.bright}${colors.cyan}═══════════════════════════════════════════════════════════${colors.reset}\n`);

    const violationsQuery = `
      SELECT
          company_unique_id,
          company_name,
          employee_count,
          address_state,
          CASE
              WHEN employee_count < 50 THEN 'BELOW MINIMUM'
              WHEN employee_count > 2000 THEN 'ABOVE 2000 (should be valid)'
              ELSE 'UNKNOWN'
          END as violation_type
      FROM marketing.company_master
      WHERE employee_count < 50 OR employee_count > 2000
      ORDER BY employee_count;
    `;

    const violationsResult = await client.query(violationsQuery);

    console.log(`${colors.yellow}Found ${violationsResult.rows.length} violation(s):${colors.reset}\n`);

    if (violationsResult.rows.length > 0) {
      console.table(violationsResult.rows);
    } else {
      console.log(`${colors.green}✓ No violations found!${colors.reset}\n`);
    }

    // PHASE 2: CHECK CURRENT CONSTRAINT
    console.log(`\n${colors.bright}${colors.cyan}═══════════════════════════════════════════════════════════${colors.reset}`);
    console.log(`${colors.bright}${colors.cyan}PHASE 2: CHECK CURRENT CONSTRAINT${colors.reset}`);
    console.log(`${colors.bright}${colors.cyan}═══════════════════════════════════════════════════════════${colors.reset}\n`);

    const constraintQuery = `
      SELECT constraint_name, check_clause
      FROM information_schema.check_constraints
      WHERE constraint_schema = 'marketing'
      AND constraint_name LIKE '%employee%';
    `;

    const constraintResult = await client.query(constraintQuery);

    if (constraintResult.rows.length > 0) {
      console.log(`${colors.yellow}Found ${constraintResult.rows.length} employee-related constraint(s):${colors.reset}\n`);
      console.table(constraintResult.rows);
    } else {
      console.log(`${colors.yellow}⚠ No employee-related constraints found${colors.reset}\n`);
    }

    // PHASE 3: AUDIT ALL COLUMN NAMES
    console.log(`\n${colors.bright}${colors.cyan}═══════════════════════════════════════════════════════════${colors.reset}`);
    console.log(`${colors.bright}${colors.cyan}PHASE 3: AUDIT ALL COLUMN NAMES${colors.reset}`);
    console.log(`${colors.bright}${colors.cyan}═══════════════════════════════════════════════════════════${colors.reset}\n`);

    const columnsQuery = `
      SELECT
          table_name,
          column_name,
          data_type,
          is_nullable,
          column_default
      FROM information_schema.columns
      WHERE table_schema = 'marketing'
      AND table_name IN ('company_master', 'company_slot', 'people_master', 'person_movement_history', 'person_scores', 'company_events')
      ORDER BY table_name, ordinal_position;
    `;

    const columnsResult = await client.query(columnsQuery);

    console.log(`${colors.yellow}Found ${columnsResult.rows.length} columns across PLE tables:${colors.reset}\n`);

    // Group by table
    const tableGroups = {};
    columnsResult.rows.forEach(row => {
      if (!tableGroups[row.table_name]) {
        tableGroups[row.table_name] = [];
      }
      tableGroups[row.table_name].push(row);
    });

    Object.keys(tableGroups).forEach(tableName => {
      console.log(`${colors.bright}${colors.blue}Table: ${tableName}${colors.reset}`);
      console.table(tableGroups[tableName]);
      console.log('');
    });

    // PHASE 4: CREATE FIELD MAPPING JSON
    console.log(`${colors.bright}${colors.cyan}═══════════════════════════════════════════════════════════${colors.reset}`);
    console.log(`${colors.bright}${colors.cyan}PHASE 4: CREATE FIELD MAPPING JSON${colors.reset}`);
    console.log(`${colors.bright}${colors.cyan}═══════════════════════════════════════════════════════════${colors.reset}\n`);

    const fieldMapping = {
      schema_version: "1.0",
      generated_at: new Date().toISOString(),
      database_info: {
        schema: "marketing",
        connection_verified: true,
        total_tables: Object.keys(tableGroups).length,
        total_columns: columnsResult.rows.length
      },
      tables: {}
    };

    // Build field mapping structure
    const tableSpecNames = {
      'company_master': 'companies',
      'company_slot': 'company_slots',
      'people_master': 'people',
      'person_movement_history': 'person_movements',
      'person_scores': 'person_scores',
      'company_events': 'company_events'
    };

    Object.keys(tableGroups).forEach(tableName => {
      const fields = {};
      tableGroups[tableName].forEach(col => {
        fields[col.column_name] = {
          actual_name: col.column_name,
          data_type: col.data_type,
          is_nullable: col.is_nullable,
          has_default: col.column_default !== null
        };
      });

      fieldMapping.tables[tableName] = {
        spec_name: tableSpecNames[tableName] || tableName,
        actual_name: tableName,
        column_count: tableGroups[tableName].length,
        fields: fields
      };
    });

    // Save to file
    const outputPath = path.join(__dirname, 'ple_field_mapping.json');
    fs.writeFileSync(outputPath, JSON.stringify(fieldMapping, null, 2), 'utf8');

    console.log(`${colors.green}✓ Field mapping saved to: ${outputPath}${colors.reset}\n`);

    // SUMMARY REPORT
    console.log(`\n${colors.bright}${colors.magenta}═══════════════════════════════════════════════════════════${colors.reset}`);
    console.log(`${colors.bright}${colors.magenta}SUMMARY REPORT${colors.reset}`);
    console.log(`${colors.bright}${colors.magenta}═══════════════════════════════════════════════════════════${colors.reset}\n`);

    console.log(`${colors.bright}Violations Found:${colors.reset} ${violationsResult.rows.length}`);

    if (violationsResult.rows.length > 0) {
      const belowMin = violationsResult.rows.filter(r => r.violation_type === 'BELOW MINIMUM').length;
      const aboveMax = violationsResult.rows.filter(r => r.violation_type === 'ABOVE 2000 (should be valid)').length;

      console.log(`  - ${colors.red}Below minimum (< 50):${colors.reset} ${belowMin}`);
      console.log(`  - ${colors.yellow}Above 2000 (valid but flagged):${colors.reset} ${aboveMax}`);
    }

    console.log(`\n${colors.bright}Constraint Analysis:${colors.reset}`);
    if (constraintResult.rows.length > 0) {
      constraintResult.rows.forEach(constraint => {
        console.log(`  - ${constraint.constraint_name}: ${constraint.check_clause}`);

        // Check if constraint has 2000 ceiling
        if (constraint.check_clause && constraint.check_clause.includes('2000')) {
          console.log(`    ${colors.yellow}⚠ RECOMMENDATION: Remove 2000 ceiling (companies >2000 should be valid)${colors.reset}`);
        }
      });
    } else {
      console.log(`  ${colors.yellow}⚠ No employee-related constraints found${colors.reset}`);
    }

    console.log(`\n${colors.bright}Field Mapping:${colors.reset}`);
    console.log(`  - Tables mapped: ${Object.keys(fieldMapping.tables).length}`);
    console.log(`  - Total columns: ${columnsResult.rows.length}`);
    console.log(`  - Output file: ${outputPath}`);

    console.log(`\n${colors.bright}Next Steps:${colors.reset}`);
    if (violationsResult.rows.filter(r => r.violation_type === 'BELOW MINIMUM').length > 0) {
      console.log(`  ${colors.red}1. DELETE or UPDATE records with employee_count < 50${colors.reset}`);
    }
    if (constraintResult.rows.some(c => c.check_clause && c.check_clause.includes('2000'))) {
      console.log(`  ${colors.yellow}2. MODIFY constraint to remove 2000 ceiling${colors.reset}`);
    }
    console.log(`  ${colors.green}3. Review ple_field_mapping.json for schema compliance${colors.reset}`);

    console.log(`\n${colors.green}✓ Audit complete!${colors.reset}\n`);

  } catch (error) {
    console.error(`${colors.red}ERROR:${colors.reset}`, error.message);
    console.error(error.stack);
    process.exit(1);
  } finally {
    await client.end();
  }
}

main();

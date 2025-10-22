#!/usr/bin/env node

/**
 * PRE-FLIGHT VALIDATION SCRIPT
 * Barton Outreach Core - Production Readiness Check
 *
 * Purpose:
 * Validates schema integrity, data quality, and compliance before production deployment.
 *
 * Validation Checks:
 * 1. Table/View Existence (10 required objects)
 * 2. Row Count Thresholds (data sufficiency)
 * 3. Barton ID Pattern Compliance (04.04.0x.xx.xxxxx.xxx)
 * 4. Foreign Key Integrity (referential constraints)
 * 5. Status Report Generation (markdown output)
 *
 * Integration:
 * - Uses Composio MCP neon_execute_sql for all database queries
 * - Follows HEIR/ORBT payload format
 * - Outputs results to PRE_FLIGHT_VALIDATION_REPORT.md
 *
 * Usage:
 *   node pre_flight_validation.js [--output <file>]
 *
 * @module pre_flight_validation
 * @doctrine 04.04 - Outreach Core Validation
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ============================================================================
// CONFIGURATION
// ============================================================================

const CONFIG = {
  // Required tables/views for production deployment
  requiredObjects: [
    { name: 'marketing.company_master', type: 'table', doctrine: '04.04.01' },
    { name: 'marketing.company_slot', type: 'table', doctrine: '04.04.05' },
    { name: 'marketing.company_intelligence', type: 'table', doctrine: '04.04.03' },
    { name: 'marketing.people_master', type: 'table', doctrine: '04.04.02' },
    { name: 'marketing.people_intelligence', type: 'table', doctrine: '04.04.04' },
    { name: 'marketing.actor_usage_log', type: 'table', doctrine: '04.04.07' },
    { name: 'marketing.linkedin_refresh_jobs', type: 'table', doctrine: '04.04.06' },
    { name: 'marketing.company_audit_log', type: 'table', doctrine: '04.04.01' },
    { name: 'marketing.people_audit_log', type: 'table', doctrine: '04.04.02' },
    { name: 'marketing.validation_log', type: 'table', doctrine: '04.04' }
  ],

  // Row count thresholds
  rowCountThresholds: {
    'marketing.company_master': { min: 400, operator: '>=', label: '≥ 400' },
    'marketing.company_slot': { formula: 'company_master * 3', operator: '=', label: '= 3× company_master' },
    'marketing.people_master': { min: 0, operator: '>=', label: '≥ 0' },
    'marketing.company_audit_log': { min: 1, operator: '>', label: '> 0 (not empty)' },
    'marketing.people_audit_log': { min: 1, operator: '>', label: '> 0 (not empty)' },
    'marketing.validation_log': { min: 1, operator: '>', label: '> 0 (not empty)' }
  },

  // Barton ID patterns by doctrine segment
  bartonIdPatterns: {
    'marketing.company_master': {
      column: 'company_barton_id',
      pattern: '^04\\.04\\.01\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$',
      example: '04.04.01.01.00001.001',
      doctrine: '04.04.01'
    },
    'marketing.people_master': {
      column: 'people_barton_id',
      pattern: '^04\\.04\\.02\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$',
      example: '04.04.02.01.00001.001',
      doctrine: '04.04.02'
    },
    'marketing.company_intelligence': {
      column: 'intel_barton_id',
      pattern: '^04\\.04\\.03\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$',
      example: '04.04.03.01.00001.001',
      doctrine: '04.04.03'
    },
    'marketing.people_intelligence': {
      column: 'intel_barton_id',
      pattern: '^04\\.04\\.04\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$',
      example: '04.04.04.01.00001.001',
      doctrine: '04.04.04'
    },
    'marketing.company_slot': {
      column: 'slot_barton_id',
      pattern: '^04\\.04\\.05\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$',
      example: '04.04.05.01.00001.001',
      doctrine: '04.04.05'
    }
  },

  // Foreign key relationships
  foreignKeyRelationships: [
    {
      parent: 'marketing.company_master',
      parentColumn: 'company_barton_id',
      child: 'marketing.company_slot',
      childColumn: 'company_barton_id',
      label: 'company_master → company_slot'
    },
    {
      parent: 'marketing.company_master',
      parentColumn: 'company_barton_id',
      child: 'marketing.company_intelligence',
      childColumn: 'company_barton_id',
      label: 'company_master → company_intelligence'
    },
    {
      parent: 'marketing.people_master',
      parentColumn: 'people_barton_id',
      child: 'marketing.people_intelligence',
      childColumn: 'people_barton_id',
      label: 'people_master → people_intelligence'
    },
    {
      parent: 'marketing.company_master',
      parentColumn: 'company_barton_id',
      child: 'marketing.people_intelligence',
      childColumn: 'company_barton_id',
      label: 'company_master → people_intelligence (via company_barton_id)'
    }
  ]
};

// ============================================================================
// VALIDATION RESULTS STORAGE
// ============================================================================

const validationResults = {
  timestamp: new Date().toISOString(),
  checks: {
    tableExistence: [],
    rowCounts: [],
    bartonIdPatterns: [],
    foreignKeyIntegrity: []
  },
  summary: {
    total: 0,
    passed: 0,
    warnings: 0,
    failed: 0
  }
};

// ============================================================================
// VALIDATION CHECK 1: TABLE/VIEW EXISTENCE
// ============================================================================

/**
 * Validates that all required tables and views exist in the database
 */
async function validateTableExistence() {
  console.log('\n🔍 Check 1/5: Validating table/view existence...\n');

  const query = `
    SELECT
      table_schema || '.' || table_name as full_name,
      table_type
    FROM information_schema.tables
    WHERE table_schema = 'marketing'
      AND table_name IN (
        'company_master', 'company_slot', 'company_intelligence',
        'people_master', 'people_intelligence', 'actor_usage_log',
        'linkedin_refresh_jobs', 'company_audit_log', 'people_audit_log',
        'validation_log'
      );
  `;

  console.log('📋 SQL Query:');
  console.log(query);
  console.log('\n⚠️  MANUAL EXECUTION REQUIRED:');
  console.log('   Run this query via Composio MCP neon_execute_sql tool');
  console.log('   Store results for report generation\n');

  // Check each required object
  for (const obj of CONFIG.requiredObjects) {
    validationResults.checks.tableExistence.push({
      object: obj.name,
      type: obj.type,
      doctrine: obj.doctrine,
      status: 'PENDING',
      message: 'Requires manual MCP query execution'
    });
  }
}

// ============================================================================
// VALIDATION CHECK 2: ROW COUNT THRESHOLDS
// ============================================================================

/**
 * Validates row counts meet minimum thresholds
 */
async function validateRowCounts() {
  console.log('\n🔢 Check 2/5: Validating row count thresholds...\n');

  const queries = [];

  // Generate count queries for each table
  for (const [table, threshold] of Object.entries(CONFIG.rowCountThresholds)) {
    const query = `SELECT '${table}' as table_name, COUNT(*) as row_count FROM ${table};`;
    queries.push(query);
  }

  // Special query for company_slot validation (must equal 3× company_master)
  queries.push(`
    SELECT
      (SELECT COUNT(*) FROM marketing.company_master) as company_master_count,
      (SELECT COUNT(*) FROM marketing.company_slot) as company_slot_count,
      (SELECT COUNT(*) FROM marketing.company_slot) =
        (SELECT COUNT(*) FROM marketing.company_master) * 3 as slot_ratio_valid;
  `);

  console.log('📋 SQL Queries:');
  queries.forEach((q, i) => {
    console.log(`\n-- Query ${i + 1}`);
    console.log(q);
  });

  console.log('\n⚠️  MANUAL EXECUTION REQUIRED:');
  console.log('   Run these queries via Composio MCP neon_execute_sql tool');
  console.log('   Compare results against thresholds\n');

  // Record pending validations
  for (const [table, threshold] of Object.entries(CONFIG.rowCountThresholds)) {
    validationResults.checks.rowCounts.push({
      table: table,
      threshold: threshold.label,
      status: 'PENDING',
      message: 'Requires manual MCP query execution'
    });
  }
}

// ============================================================================
// VALIDATION CHECK 3: BARTON ID PATTERN COMPLIANCE
// ============================================================================

/**
 * Validates Barton ID format compliance (04.04.0x.xx.xxxxx.xxx)
 */
async function validateBartonIdPatterns() {
  console.log('\n🔖 Check 3/5: Validating Barton ID patterns...\n');

  const queries = [];

  for (const [table, config] of Object.entries(CONFIG.bartonIdPatterns)) {
    const query = `
      SELECT
        '${table}' as table_name,
        '${config.column}' as id_column,
        COUNT(*) as total_rows,
        COUNT(*) FILTER (
          WHERE ${config.column} ~ '${config.pattern}'
        ) as valid_ids,
        COUNT(*) FILTER (
          WHERE ${config.column} !~ '${config.pattern}'
        ) as invalid_ids,
        ARRAY_AGG(
          ${config.column}
        ) FILTER (
          WHERE ${config.column} !~ '${config.pattern}'
        ) as invalid_examples
      FROM ${table}
      GROUP BY table_name, id_column;
    `;
    queries.push(query);
  }

  console.log('📋 SQL Queries:');
  queries.forEach((q, i) => {
    console.log(`\n-- Query ${i + 1}`);
    console.log(q);
  });

  console.log('\n⚠️  MANUAL EXECUTION REQUIRED:');
  console.log('   Run these queries via Composio MCP neon_execute_sql tool');
  console.log('   Check for invalid_ids > 0\n');

  // Record pending validations
  for (const [table, config] of Object.entries(CONFIG.bartonIdPatterns)) {
    validationResults.checks.bartonIdPatterns.push({
      table: table,
      column: config.column,
      pattern: config.pattern,
      example: config.example,
      doctrine: config.doctrine,
      status: 'PENDING',
      message: 'Requires manual MCP query execution'
    });
  }
}

// ============================================================================
// VALIDATION CHECK 4: FOREIGN KEY INTEGRITY
// ============================================================================

/**
 * Validates foreign key relationships and referential integrity
 */
async function validateForeignKeyIntegrity() {
  console.log('\n🔗 Check 4/5: Validating foreign key integrity...\n');

  const queries = [];

  for (const fk of CONFIG.foreignKeyRelationships) {
    // Check for orphaned records in child table
    const query = `
      SELECT
        '${fk.label}' as relationship,
        '${fk.child}' as child_table,
        COUNT(*) as orphaned_records
      FROM ${fk.child} child
      WHERE NOT EXISTS (
        SELECT 1 FROM ${fk.parent} parent
        WHERE parent.${fk.parentColumn} = child.${fk.childColumn}
      );
    `;
    queries.push(query);
  }

  // Check for foreign key constraints in information_schema
  queries.push(`
    SELECT
      tc.table_schema || '.' || tc.table_name as child_table,
      kcu.column_name as child_column,
      ccu.table_schema || '.' || ccu.table_name as parent_table,
      ccu.column_name as parent_column,
      tc.constraint_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_schema = 'marketing';
  `);

  console.log('📋 SQL Queries:');
  queries.forEach((q, i) => {
    console.log(`\n-- Query ${i + 1}`);
    console.log(q);
  });

  console.log('\n⚠️  MANUAL EXECUTION REQUIRED:');
  console.log('   Run these queries via Composio MCP neon_execute_sql tool');
  console.log('   Check for orphaned_records = 0\n');

  // Record pending validations
  for (const fk of CONFIG.foreignKeyRelationships) {
    validationResults.checks.foreignKeyIntegrity.push({
      relationship: fk.label,
      parent: fk.parent,
      child: fk.child,
      status: 'PENDING',
      message: 'Requires manual MCP query execution'
    });
  }
}

// ============================================================================
// VALIDATION CHECK 5: GENERATE MARKDOWN REPORT
// ============================================================================

/**
 * Generates markdown validation report with status indicators
 */
function generateMarkdownReport() {
  console.log('\n📄 Check 5/5: Generating markdown report...\n');

  const report = [];

  // Header
  report.push('# 🚀 PRE-FLIGHT VALIDATION REPORT');
  report.push('**Barton Outreach Core - Production Readiness Check**\n');
  report.push(`**Generated**: ${new Date().toLocaleString()}`);
  report.push(`**Status**: Manual validation required\n`);
  report.push('---\n');

  // Check 1: Table Existence
  report.push('## ✅ Check 1: Table/View Existence\n');
  report.push('| Object | Type | Doctrine | Status | Notes |');
  report.push('|--------|------|----------|--------|-------|');
  for (const check of validationResults.checks.tableExistence) {
    const status = check.status === 'PENDING' ? '⏳ PENDING' :
                   check.status === 'OK' ? '✅ OK' :
                   check.status === 'WARN' ? '⚠️  WARN' : '❌ FAIL';
    report.push(`| ${check.object} | ${check.type} | ${check.doctrine} | ${status} | ${check.message} |`);
  }
  report.push('');

  // Check 2: Row Counts
  report.push('## 🔢 Check 2: Row Count Thresholds\n');
  report.push('| Table | Threshold | Actual | Status | Notes |');
  report.push('|-------|-----------|--------|--------|-------|');
  for (const check of validationResults.checks.rowCounts) {
    const status = check.status === 'PENDING' ? '⏳ PENDING' :
                   check.status === 'OK' ? '✅ OK' :
                   check.status === 'WARN' ? '⚠️  WARN' : '❌ FAIL';
    report.push(`| ${check.table} | ${check.threshold} | TBD | ${status} | ${check.message} |`);
  }
  report.push('');

  // Check 3: Barton ID Patterns
  report.push('## 🔖 Check 3: Barton ID Pattern Compliance\n');
  report.push('| Table | Column | Pattern | Valid | Invalid | Status | Notes |');
  report.push('|-------|--------|---------|-------|---------|--------|-------|');
  for (const check of validationResults.checks.bartonIdPatterns) {
    const status = check.status === 'PENDING' ? '⏳ PENDING' :
                   check.status === 'OK' ? '✅ OK' :
                   check.status === 'WARN' ? '⚠️  WARN' : '❌ FAIL';
    report.push(`| ${check.table} | ${check.column} | \`${check.pattern}\` | TBD | TBD | ${status} | ${check.message} |`);
  }
  report.push('');

  // Check 4: Foreign Key Integrity
  report.push('## 🔗 Check 4: Foreign Key Integrity\n');
  report.push('| Relationship | Parent Table | Child Table | Orphaned | Status | Notes |');
  report.push('|--------------|--------------|-------------|----------|--------|-------|');
  for (const check of validationResults.checks.foreignKeyIntegrity) {
    const status = check.status === 'PENDING' ? '⏳ PENDING' :
                   check.status === 'OK' ? '✅ OK' :
                   check.status === 'WARN' ? '⚠️  WARN' : '❌ FAIL';
    report.push(`| ${check.relationship} | ${check.parent} | ${check.child} | TBD | ${status} | ${check.message} |`);
  }
  report.push('');

  // Summary
  report.push('---\n');
  report.push('## 📊 Validation Summary\n');
  report.push('| Metric | Count |');
  report.push('|--------|-------|');
  report.push(`| Total Checks | ${validationResults.summary.total} |`);
  report.push(`| ✅ Passed | ${validationResults.summary.passed} |`);
  report.push(`| ⚠️  Warnings | ${validationResults.summary.warnings} |`);
  report.push(`| ❌ Failed | ${validationResults.summary.failed} |`);
  report.push(`| ⏳ Pending | ${validationResults.summary.total - validationResults.summary.passed - validationResults.summary.warnings - validationResults.summary.failed} |`);
  report.push('');

  // Next Steps
  report.push('---\n');
  report.push('## 🎯 Next Steps\n');
  report.push('1. Execute all SQL queries via Composio MCP `neon_execute_sql` tool');
  report.push('2. Update this report with actual results from database');
  report.push('3. Resolve any ❌ FAIL or ⚠️  WARN statuses before production deployment');
  report.push('4. Re-run validation after fixes to confirm ✅ OK status');
  report.push('5. Archive this report for audit trail\n');

  // SQL Execution Instructions
  report.push('---\n');
  report.push('## 🛠️  SQL Execution Instructions\n');
  report.push('All queries must be executed via Composio MCP using the following pattern:\n');
  report.push('```bash');
  report.push('curl -X POST http://localhost:3001/tool \\');
  report.push('  -H "Content-Type: application/json" \\');
  report.push('  -d \'{');
  report.push('    "tool": "neon_execute_sql",');
  report.push('    "data": {');
  report.push('      "sql_query": "<YOUR_SQL_QUERY_HERE>"');
  report.push('    },');
  report.push('    "unique_id": "HEIR-2025-10-PREFLIGHT-01",');
  report.push('    "process_id": "PRC-VALIDATION-001",');
  report.push('    "orbt_layer": 2,');
  report.push('    "blueprint_version": "1.0"');
  report.push('  }\'');
  report.push('```\n');

  // Footer
  report.push('---\n');
  report.push('**Doctrine Reference**: 04.04 - Outreach Core Data Integrity');
  report.push('**Validation Script**: `analysis/pre_flight_validation.js`');
  report.push('**Report File**: `analysis/PRE_FLIGHT_VALIDATION_REPORT.md`\n');

  return report.join('\n');
}

// ============================================================================
// MAIN EXECUTION
// ============================================================================

async function main() {
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║  BARTON OUTREACH CORE - PRE-FLIGHT VALIDATION SCRIPT      ║');
  console.log('║  Production Readiness Check                                ║');
  console.log('╚════════════════════════════════════════════════════════════╝');

  try {
    // Run all validation checks
    await validateTableExistence();
    await validateRowCounts();
    await validateBartonIdPatterns();
    await validateForeignKeyIntegrity();

    // Calculate totals
    validationResults.summary.total =
      validationResults.checks.tableExistence.length +
      validationResults.checks.rowCounts.length +
      validationResults.checks.bartonIdPatterns.length +
      validationResults.checks.foreignKeyIntegrity.length;

    // Generate markdown report
    const reportContent = generateMarkdownReport();

    // Write report to file
    const outputPath = path.join(__dirname, 'PRE_FLIGHT_VALIDATION_REPORT.md');
    fs.writeFileSync(outputPath, reportContent, 'utf8');

    console.log('✅ Validation report generated successfully!');
    console.log(`📄 Report saved to: ${outputPath}\n`);

    // Display next steps
    console.log('╔════════════════════════════════════════════════════════════╗');
    console.log('║  NEXT STEPS                                                ║');
    console.log('╚════════════════════════════════════════════════════════════╝');
    console.log('');
    console.log('1. Review PRE_FLIGHT_VALIDATION_REPORT.md for SQL queries');
    console.log('2. Execute queries via Composio MCP neon_execute_sql tool');
    console.log('3. Update report with actual results');
    console.log('4. Resolve any failures or warnings');
    console.log('5. Re-run validation to confirm readiness\n');

  } catch (error) {
    console.error('❌ Validation script error:', error.message);
    process.exit(1);
  }
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { validateTableExistence, validateRowCounts, validateBartonIdPatterns, validateForeignKeyIntegrity, generateMarkdownReport };

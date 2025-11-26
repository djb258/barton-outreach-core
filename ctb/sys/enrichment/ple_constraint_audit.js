/**
 * PLE Constraint Audit Script
 * Audits NOT NULL, CHECK, and UNIQUE constraints on marketing schema tables
 *
 * Barton ID: 04.04.02.04.50000.001
 * Purpose: Comprehensive constraint compliance audit for PLE schema
 */

const { Client } = require('pg');
const fs = require('fs');
const path = require('path');

// Database connection string from .env
const CONNECTION_STRING = process.env.DATABASE_URL ||
  'postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing%20DB?sslmode=require';

const client = new Client({
  connectionString: CONNECTION_STRING
});

// Required constraints definition
const REQUIRED_CONSTRAINTS = {
  not_null: {
    company_master: ['company_unique_id', 'company_name', 'source_system', 'created_at'],
    company_slot: ['company_slot_unique_id', 'company_unique_id', 'slot_type'],
    people_master: ['unique_id', 'company_unique_id', 'first_name', 'last_name', 'created_at']
  },
  check: [
    {
      table: 'company_master',
      name: 'chk_employee_range',
      column: 'employee_count',
      condition: '(employee_count >= 50 AND employee_count <= 2000)',
      description: 'Employee count must be between 50 and 2000'
    },
    {
      table: 'company_master',
      name: 'chk_state_valid',
      column: 'address_state',
      condition: "(address_state IN ('PA','VA','MD','OH','WV','KY','Pennsylvania','Virginia','Maryland','Ohio','West Virginia','Kentucky'))",
      description: 'State must be valid mid-Atlantic abbreviation or full name'
    },
    {
      table: 'company_slot',
      name: 'chk_slot_type',
      column: 'slot_type',
      condition: "(LOWER(slot_type) IN ('ceo','cfo','hr'))",
      description: 'Slot type must be CEO, CFO, or HR (case-insensitive)'
    },
    {
      table: 'people_master',
      name: 'chk_contact_required',
      column: null,
      condition: "(linkedin_url IS NOT NULL OR email IS NOT NULL)",
      description: 'At least one of LinkedIn URL or email must be provided'
    }
  ],
  unique: [
    {
      table: 'company_master',
      name: 'company_master_pkey',
      columns: ['company_unique_id'],
      description: 'Primary key on company_unique_id'
    },
    {
      table: 'company_slot',
      name: 'uq_company_slot_type',
      columns: ['company_unique_id', 'slot_type'],
      description: 'Unique constraint on company + slot type combination'
    },
    {
      table: 'people_master',
      name: 'people_master_pkey',
      columns: ['unique_id'],
      description: 'Primary key on unique_id'
    }
  ]
};

// Audit queries
const QUERIES = {
  // 1. Check NOT NULL constraints
  notNullColumns: `
    SELECT
      table_schema,
      table_name,
      column_name,
      is_nullable,
      data_type,
      column_default
    FROM information_schema.columns
    WHERE table_schema = 'marketing'
    AND table_name IN ('company_master', 'company_slot', 'people_master')
    ORDER BY table_name, ordinal_position;
  `,

  // 2. Check CHECK constraints
  checkConstraints: `
    SELECT
      tc.table_schema,
      tc.table_name,
      tc.constraint_name,
      cc.check_clause
    FROM information_schema.table_constraints tc
    JOIN information_schema.check_constraints cc
      ON tc.constraint_name = cc.constraint_name
    WHERE tc.table_schema = 'marketing'
    AND tc.constraint_type = 'CHECK'
    ORDER BY tc.table_name, tc.constraint_name;
  `,

  // 3. Check UNIQUE constraints
  uniqueConstraints: `
    SELECT
      tc.table_schema,
      tc.table_name,
      tc.constraint_name,
      tc.constraint_type,
      string_agg(kcu.column_name, ', ' ORDER BY kcu.ordinal_position) as columns
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    WHERE tc.table_schema = 'marketing'
    AND tc.constraint_type IN ('UNIQUE', 'PRIMARY KEY')
    AND tc.table_name IN ('company_master', 'company_slot', 'people_master')
    GROUP BY tc.table_schema, tc.table_name, tc.constraint_name, tc.constraint_type
    ORDER BY tc.table_name, tc.constraint_type, tc.constraint_name;
  `,

  // 4. Data violation checks
  violations: {
    employeeRange: `
      SELECT COUNT(*) as violations
      FROM marketing.company_master
      WHERE employee_count IS NOT NULL
      AND (employee_count < 50 OR employee_count > 2000);
    `,
    stateValid: `
      SELECT COUNT(*) as violations
      FROM marketing.company_master
      WHERE address_state IS NOT NULL
      AND address_state NOT IN ('PA','VA','MD','OH','WV','KY','Pennsylvania','Virginia','Maryland','Ohio','West Virginia','Kentucky');
    `,
    slotType: `
      SELECT COUNT(*) as violations
      FROM marketing.company_slot
      WHERE slot_type IS NOT NULL
      AND LOWER(slot_type) NOT IN ('ceo','cfo','hr');
    `,
    contactInfo: `
      SELECT COUNT(*) as violations
      FROM marketing.people_master
      WHERE linkedin_url IS NULL AND email IS NULL;
    `,
    nullValues: `
      SELECT 'company_master' as table_name, 'company_name' as column_name, COUNT(*) as null_count
      FROM marketing.company_master WHERE company_name IS NULL
      UNION ALL
      SELECT 'company_master', 'source_system', COUNT(*) FROM marketing.company_master WHERE source_system IS NULL
      UNION ALL
      SELECT 'company_slot', 'company_unique_id', COUNT(*) FROM marketing.company_slot WHERE company_unique_id IS NULL
      UNION ALL
      SELECT 'company_slot', 'slot_type', COUNT(*) FROM marketing.company_slot WHERE slot_type IS NULL
      UNION ALL
      SELECT 'people_master', 'first_name', COUNT(*) FROM marketing.people_master WHERE first_name IS NULL
      UNION ALL
      SELECT 'people_master', 'last_name', COUNT(*) FROM marketing.people_master WHERE last_name IS NULL
      UNION ALL
      SELECT 'people_master', 'company_unique_id', COUNT(*) FROM marketing.people_master WHERE company_unique_id IS NULL
      ORDER BY table_name, column_name;
    `,
    duplicateSlots: `
      SELECT company_unique_id, slot_type, COUNT(*) as duplicate_count
      FROM marketing.company_slot
      GROUP BY company_unique_id, slot_type
      HAVING COUNT(*) > 1
      ORDER BY duplicate_count DESC;
    `
  }
};

async function runAudit() {
  const results = {
    notNullColumns: [],
    checkConstraints: [],
    uniqueConstraints: [],
    violations: {},
    timestamp: new Date().toISOString()
  };

  try {
    console.log('Connecting to Neon PostgreSQL...');
    await client.connect();
    console.log('✅ Connected successfully\n');

    // 1. Audit NOT NULL columns
    console.log('📋 Auditing NOT NULL constraints...');
    const notNullRes = await client.query(QUERIES.notNullColumns);
    results.notNullColumns = notNullRes.rows;
    console.log(`   Found ${notNullRes.rows.length} columns\n`);

    // 2. Audit CHECK constraints
    console.log('📋 Auditing CHECK constraints...');
    const checkRes = await client.query(QUERIES.checkConstraints);
    results.checkConstraints = checkRes.rows;
    console.log(`   Found ${checkRes.rows.length} CHECK constraints\n`);

    // 3. Audit UNIQUE constraints
    console.log('📋 Auditing UNIQUE/PRIMARY KEY constraints...');
    const uniqueRes = await client.query(QUERIES.uniqueConstraints);
    results.uniqueConstraints = uniqueRes.rows;
    console.log(`   Found ${uniqueRes.rows.length} UNIQUE/PK constraints\n`);

    // 4. Check for data violations
    console.log('📋 Checking for data violations...');
    for (const [key, query] of Object.entries(QUERIES.violations)) {
      const res = await client.query(query);
      results.violations[key] = res.rows;
      console.log(`   ${key}: ${res.rows.length} results`);
    }
    console.log('');

    return results;

  } catch (error) {
    console.error('❌ Error during audit:', error.message);
    throw error;
  } finally {
    await client.end();
    console.log('✅ Database connection closed');
  }
}

function generateReport(results) {
  const lines = [];

  lines.push('# PLE CONSTRAINT AUDIT REPORT');
  lines.push('');
  lines.push(`**Generated:** ${new Date(results.timestamp).toLocaleString()}`);
  lines.push(`**Barton ID:** 04.04.02.04.50000.001`);
  lines.push(`**Purpose:** Constraint compliance audit for PLE schema tables`);
  lines.push('');
  lines.push('---');
  lines.push('');

  // === NOT NULL AUDIT ===
  lines.push('## 1. NOT NULL CONSTRAINT AUDIT');
  lines.push('');

  for (const [tableName, requiredCols] of Object.entries(REQUIRED_CONSTRAINTS.not_null)) {
    lines.push(`### ${tableName}`);
    lines.push('');
    lines.push('| Column Name | Data Type | Required | Current Status | Action Needed |');
    lines.push('|-------------|-----------|----------|----------------|---------------|');

    const tableColumns = results.notNullColumns.filter(c => c.table_name === tableName);

    for (const col of tableColumns) {
      const isRequired = requiredCols.includes(col.column_name);
      const currentStatus = col.is_nullable === 'NO' ? 'NOT NULL ✅' : 'Nullable';
      const action = isRequired && col.is_nullable === 'YES' ? '⚠️ ADD NOT NULL' :
                     isRequired ? '✅ Compliant' : 'No action';

      const marker = isRequired ? '**' : '';
      lines.push(`| ${marker}${col.column_name}${marker} | ${col.data_type} | ${isRequired ? 'Yes' : 'No'} | ${currentStatus} | ${action} |`);
    }
    lines.push('');
  }

  // === CHECK CONSTRAINT AUDIT ===
  lines.push('## 2. CHECK CONSTRAINT AUDIT');
  lines.push('');
  lines.push('| Table | Constraint Name | Required | Current Status | Action Needed |');
  lines.push('|-------|-----------------|----------|----------------|---------------|');

  for (const req of REQUIRED_CONSTRAINTS.check) {
    const exists = results.checkConstraints.find(c =>
      c.table_name === req.table &&
      c.constraint_name === req.name
    );

    const status = exists ? `✅ EXISTS: ${exists.check_clause}` : '❌ MISSING';
    const action = exists ? '✅ Compliant' : '⚠️ CREATE CONSTRAINT';

    lines.push(`| ${req.table} | ${req.name} | Yes | ${status} | ${action} |`);
  }
  lines.push('');
  lines.push('### Required CHECK Constraint Details:');
  lines.push('');
  for (const req of REQUIRED_CONSTRAINTS.check) {
    lines.push(`**${req.name}** (${req.table})`);
    lines.push(`- Description: ${req.description}`);
    lines.push(`- Condition: \`${req.condition}\``);
    lines.push('');
  }

  // === UNIQUE CONSTRAINT AUDIT ===
  lines.push('## 3. UNIQUE CONSTRAINT AUDIT');
  lines.push('');
  lines.push('| Table | Constraint Name | Type | Columns | Required | Current Status | Action Needed |');
  lines.push('|-------|-----------------|------|---------|----------|----------------|---------------|');

  for (const req of REQUIRED_CONSTRAINTS.unique) {
    const exists = results.uniqueConstraints.find(c =>
      c.table_name === req.table &&
      (c.constraint_name === req.name ||
       c.columns === req.columns.join(', '))
    );

    const status = exists ? `✅ ${exists.constraint_type}` : '❌ MISSING';
    const action = exists ? '✅ Compliant' : '⚠️ CREATE CONSTRAINT';
    const type = req.name.includes('pkey') ? 'PRIMARY KEY' : 'UNIQUE';

    lines.push(`| ${req.table} | ${req.name} | ${type} | ${req.columns.join(', ')} | Yes | ${status} | ${action} |`);
  }
  lines.push('');

  // === DATA VIOLATION REPORT ===
  lines.push('## 4. DATA VIOLATION REPORT');
  lines.push('');
  lines.push('### Violations That Would Prevent Constraint Creation');
  lines.push('');

  let totalViolations = 0;

  // Employee count range
  const empViolations = results.violations.employeeRange[0]?.violations || 0;
  totalViolations += parseInt(empViolations);
  lines.push(`#### Employee Count Range (50-2000)`);
  lines.push(`- **Violations:** ${empViolations}`);
  lines.push(`- **Impact:** ${empViolations > 0 ? '⚠️ Cannot add chk_employee_range until fixed' : '✅ No violations'}`);
  lines.push('');

  // State validation
  const stateViolations = results.violations.stateValid[0]?.violations || 0;
  totalViolations += parseInt(stateViolations);
  lines.push(`#### State Validation`);
  lines.push(`- **Violations:** ${stateViolations}`);
  lines.push(`- **Impact:** ${stateViolations > 0 ? '⚠️ Cannot add chk_state_valid until fixed' : '✅ No violations'}`);
  lines.push('');

  // Slot type validation
  const slotViolations = results.violations.slotType[0]?.violations || 0;
  totalViolations += parseInt(slotViolations);
  lines.push(`#### Slot Type Validation`);
  lines.push(`- **Violations:** ${slotViolations}`);
  lines.push(`- **Impact:** ${slotViolations > 0 ? '⚠️ Cannot add chk_slot_type until fixed' : '✅ No violations'}`);
  lines.push('');

  // Contact info validation
  const contactViolations = results.violations.contactInfo[0]?.violations || 0;
  totalViolations += parseInt(contactViolations);
  lines.push(`#### Contact Info Required`);
  lines.push(`- **Violations:** ${contactViolations}`);
  lines.push(`- **Impact:** ${contactViolations > 0 ? '⚠️ Cannot add chk_contact_required until fixed' : '✅ No violations'}`);
  lines.push('');

  // NULL values in required columns
  lines.push(`#### NULL Values in Required Columns`);
  lines.push('');
  lines.push('| Table | Column | NULL Count | Impact |');
  lines.push('|-------|--------|------------|--------|');

  for (const row of results.violations.nullValues || []) {
    const nullCount = parseInt(row.null_count);
    totalViolations += nullCount;
    const impact = nullCount > 0 ? '⚠️ Cannot add NOT NULL' : '✅ OK';
    lines.push(`| ${row.table_name} | ${row.column_name} | ${nullCount} | ${impact} |`);
  }
  lines.push('');

  // Duplicate slots
  const duplicateSlots = results.violations.duplicateSlots || [];
  if (duplicateSlots.length > 0) {
    lines.push(`#### Duplicate Slots (Violates Unique Constraint)`);
    lines.push('');
    lines.push('| Company Unique ID | Slot Type | Duplicate Count |');
    lines.push('|-------------------|-----------|-----------------|');

    for (const dup of duplicateSlots) {
      totalViolations += parseInt(dup.duplicate_count) - 1; // Subtract 1 because first is valid
      lines.push(`| ${dup.company_unique_id} | ${dup.slot_type} | ${dup.duplicate_count} |`);
    }
    lines.push('');
    lines.push(`⚠️ **${duplicateSlots.length} companies** have duplicate slot types that must be resolved before adding unique constraint`);
    lines.push('');
  }

  // Summary
  lines.push('### Summary');
  lines.push('');
  lines.push(`- **Total Violations:** ${totalViolations}`);
  lines.push(`- **Status:** ${totalViolations === 0 ? '✅ READY to add all constraints' : '⚠️ Data cleanup required before adding constraints'}`);
  lines.push('');

  // === RECOMMENDATIONS ===
  lines.push('## 5. RECOMMENDATIONS');
  lines.push('');

  if (totalViolations > 0) {
    lines.push('### Data Cleanup Required (Priority Order)');
    lines.push('');
    lines.push('1. **Fix NULL values in required columns** - Highest priority');
    lines.push('2. **Resolve duplicate company_slot records** - Prevents unique constraint');
    lines.push('3. **Fix employee_count range violations** - Out of 50-2000 range');
    lines.push('4. **Fix state abbreviation violations** - Invalid state codes');
    lines.push('5. **Fix slot_type violations** - Must be CEO/CFO/HR');
    lines.push('6. **Fix missing contact info** - Need LinkedIn OR email');
    lines.push('');
    lines.push('### After Data Cleanup');
    lines.push('');
    lines.push('1. Run data cleanup queries (see migration SQL)');
    lines.push('2. Re-run this audit to verify 0 violations');
    lines.push('3. Execute constraint migration SQL in transaction');
    lines.push('4. Verify all constraints are active');
    lines.push('');
  } else {
    lines.push('✅ **No data violations detected!**');
    lines.push('');
    lines.push('You can safely proceed with adding constraints:');
    lines.push('');
    lines.push('1. Review the migration SQL script');
    lines.push('2. Execute in a transaction (can rollback if issues)');
    lines.push('3. Verify constraints are active');
    lines.push('4. Update application code to handle constraint violations');
    lines.push('');
  }

  // === EXISTING CONSTRAINTS FOUND ===
  lines.push('## 6. EXISTING CONSTRAINTS INVENTORY');
  lines.push('');

  lines.push('### CHECK Constraints Currently Defined');
  lines.push('');
  if (results.checkConstraints.length > 0) {
    lines.push('| Table | Constraint Name | Check Clause |');
    lines.push('|-------|-----------------|--------------|');
    for (const constraint of results.checkConstraints) {
      lines.push(`| ${constraint.table_name} | ${constraint.constraint_name} | ${constraint.check_clause} |`);
    }
  } else {
    lines.push('❌ No CHECK constraints currently defined');
  }
  lines.push('');

  lines.push('### UNIQUE/PRIMARY KEY Constraints Currently Defined');
  lines.push('');
  if (results.uniqueConstraints.length > 0) {
    lines.push('| Table | Constraint Name | Type | Columns |');
    lines.push('|-------|-----------------|------|---------|');
    for (const constraint of results.uniqueConstraints) {
      lines.push(`| ${constraint.table_name} | ${constraint.constraint_name} | ${constraint.constraint_type} | ${constraint.columns} |`);
    }
  } else {
    lines.push('❌ No UNIQUE/PRIMARY KEY constraints currently defined');
  }
  lines.push('');

  lines.push('---');
  lines.push('');
  lines.push('**Next Steps:**');
  lines.push('1. Review this audit report');
  lines.push('2. Execute data cleanup if violations found');
  lines.push('3. Review and execute `ple_constraint_migration.sql`');
  lines.push('4. Verify constraints with follow-up audit');
  lines.push('');
  lines.push('**Generated by:** PLE Constraint Audit Script (Barton ID: 04.04.02.04.50000.001)');

  return lines.join('\n');
}

function generateMigrationSQL(results) {
  const lines = [];

  lines.push('-- ============================================================================');
  lines.push('-- PLE CONSTRAINT MIGRATION SCRIPT');
  lines.push('-- ============================================================================');
  lines.push('-- Barton ID: 04.04.02.04.50000.002');
  lines.push('-- Purpose: Add missing NOT NULL, CHECK, and UNIQUE constraints');
  lines.push('--');
  lines.push(`-- Generated: ${new Date().toISOString()}`);
  lines.push('--');
  lines.push('-- IMPORTANT: Review audit report before executing!');
  lines.push('-- This script will FAIL if data violations exist.');
  lines.push('-- ============================================================================');
  lines.push('');
  lines.push('BEGIN;');
  lines.push('');
  lines.push('-- ============================================================================');
  lines.push('-- PHASE 1: DATA CLEANUP (Run if violations detected)');
  lines.push('-- ============================================================================');
  lines.push('');

  // Data cleanup queries
  lines.push('-- 1. Set default values for NULL required fields (REVIEW CAREFULLY!)');
  lines.push('-- UPDATE marketing.company_master SET source_system = \'unknown\' WHERE source_system IS NULL;');
  lines.push('-- UPDATE marketing.people_master SET first_name = \'Unknown\' WHERE first_name IS NULL;');
  lines.push('-- UPDATE marketing.people_master SET last_name = \'Unknown\' WHERE last_name IS NULL;');
  lines.push('');

  lines.push('-- 2. Fix employee_count range violations');
  lines.push('-- UPDATE marketing.company_master SET employee_count = NULL WHERE employee_count < 50 OR employee_count > 2000;');
  lines.push('');

  lines.push('-- 3. Fix state violations (set to NULL or correct value)');
  lines.push('-- UPDATE marketing.company_master SET address_state = NULL');
  lines.push('-- WHERE address_state IS NOT NULL');
  lines.push('-- AND address_state NOT IN (\'PA\',\'VA\',\'MD\',\'OH\',\'WV\',\'KY\',\'Pennsylvania\',\'Virginia\',\'Maryland\',\'Ohio\',\'West Virginia\',\'Kentucky\');');
  lines.push('');

  lines.push('-- 4. Fix slot_type violations (set to NULL or correct value)');
  lines.push('-- UPDATE marketing.company_slot SET slot_type = UPPER(slot_type)');
  lines.push('-- WHERE LOWER(slot_type) IN (\'ceo\',\'cfo\',\'hr\') AND slot_type != UPPER(slot_type);');
  lines.push('');

  lines.push('-- 5. Delete people_master records with no contact info (or add dummy email)');
  lines.push('-- DELETE FROM marketing.people_master WHERE linkedin_url IS NULL AND email IS NULL;');
  lines.push('-- OR');
  lines.push('-- UPDATE marketing.people_master SET email = \'noemail@example.com\' WHERE linkedin_url IS NULL AND email IS NULL;');
  lines.push('');

  lines.push('-- 6. Resolve duplicate company_slot records (keep most recent)');
  lines.push('-- DELETE FROM marketing.company_slot');
  lines.push('-- WHERE company_slot_unique_id IN (');
  lines.push('--   SELECT company_slot_unique_id FROM (');
  lines.push('--     SELECT company_slot_unique_id,');
  lines.push('--            ROW_NUMBER() OVER (PARTITION BY company_unique_id, slot_type ORDER BY created_at DESC NULLS LAST) as rn');
  lines.push('--     FROM marketing.company_slot');
  lines.push('--   ) sub WHERE rn > 1');
  lines.push('-- );');
  lines.push('');

  lines.push('-- ============================================================================');
  lines.push('-- PHASE 2: ADD NOT NULL CONSTRAINTS');
  lines.push('-- ============================================================================');
  lines.push('');

  for (const [tableName, requiredCols] of Object.entries(REQUIRED_CONSTRAINTS.not_null)) {
    lines.push(`-- Table: ${tableName}`);

    const tableColumns = results.notNullColumns.filter(c => c.table_name === tableName);

    for (const colName of requiredCols) {
      const col = tableColumns.find(c => c.column_name === colName);
      if (col && col.is_nullable === 'YES') {
        lines.push(`ALTER TABLE marketing.${tableName}`);
        lines.push(`  ALTER COLUMN ${colName} SET NOT NULL;`);
        lines.push('');
      }
    }
  }

  lines.push('-- ============================================================================');
  lines.push('-- PHASE 3: ADD CHECK CONSTRAINTS');
  lines.push('-- ============================================================================');
  lines.push('');

  for (const req of REQUIRED_CONSTRAINTS.check) {
    const exists = results.checkConstraints.find(c =>
      c.table_name === req.table &&
      c.constraint_name === req.name
    );

    if (!exists) {
      lines.push(`-- ${req.description}`);
      lines.push(`ALTER TABLE marketing.${req.table}`);
      lines.push(`  ADD CONSTRAINT ${req.name}`);
      lines.push(`  CHECK ${req.condition};`);
      lines.push('');
    }
  }

  lines.push('-- ============================================================================');
  lines.push('-- PHASE 4: ADD UNIQUE CONSTRAINTS');
  lines.push('-- ============================================================================');
  lines.push('');

  for (const req of REQUIRED_CONSTRAINTS.unique) {
    const exists = results.uniqueConstraints.find(c =>
      c.table_name === req.table &&
      (c.constraint_name === req.name || c.columns === req.columns.join(', '))
    );

    if (!exists) {
      lines.push(`-- ${req.description}`);
      if (req.name.includes('pkey')) {
        lines.push(`-- Note: Primary key should already exist. If not:`);
        lines.push(`-- ALTER TABLE marketing.${req.table}`);
        lines.push(`--   ADD CONSTRAINT ${req.name} PRIMARY KEY (${req.columns.join(', ')});`);
      } else {
        lines.push(`ALTER TABLE marketing.${req.table}`);
        lines.push(`  ADD CONSTRAINT ${req.name} UNIQUE (${req.columns.join(', ')});`);
      }
      lines.push('');
    }
  }

  lines.push('-- ============================================================================');
  lines.push('-- PHASE 5: VERIFICATION');
  lines.push('-- ============================================================================');
  lines.push('');
  lines.push('-- Verify NOT NULL constraints');
  lines.push('SELECT table_name, column_name, is_nullable');
  lines.push('FROM information_schema.columns');
  lines.push('WHERE table_schema = \'marketing\'');
  lines.push('AND table_name IN (\'company_master\', \'company_slot\', \'people_master\')');
  lines.push('AND is_nullable = \'NO\'');
  lines.push('ORDER BY table_name, column_name;');
  lines.push('');

  lines.push('-- Verify CHECK constraints');
  lines.push('SELECT tc.table_name, tc.constraint_name, cc.check_clause');
  lines.push('FROM information_schema.table_constraints tc');
  lines.push('JOIN information_schema.check_constraints cc ON tc.constraint_name = cc.constraint_name');
  lines.push('WHERE tc.table_schema = \'marketing\'');
  lines.push('AND tc.constraint_type = \'CHECK\'');
  lines.push('ORDER BY tc.table_name, tc.constraint_name;');
  lines.push('');

  lines.push('-- Verify UNIQUE constraints');
  lines.push('SELECT tc.table_name, tc.constraint_name, tc.constraint_type,');
  lines.push('       string_agg(kcu.column_name, \', \' ORDER BY kcu.ordinal_position) as columns');
  lines.push('FROM information_schema.table_constraints tc');
  lines.push('JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name');
  lines.push('WHERE tc.table_schema = \'marketing\'');
  lines.push('AND tc.constraint_type IN (\'UNIQUE\', \'PRIMARY KEY\')');
  lines.push('GROUP BY tc.table_name, tc.constraint_name, tc.constraint_type');
  lines.push('ORDER BY tc.table_name, tc.constraint_type;');
  lines.push('');

  lines.push('-- If all looks good, commit. Otherwise, rollback.');
  lines.push('-- COMMIT;');
  lines.push('ROLLBACK; -- Change to COMMIT after review');
  lines.push('');
  lines.push('-- ============================================================================');
  lines.push('-- END OF MIGRATION SCRIPT');
  lines.push('-- ============================================================================');

  return lines.join('\n');
}

// Main execution
(async () => {
  try {
    console.log('═══════════════════════════════════════════════════════════');
    console.log('   PLE CONSTRAINT AUDIT');
    console.log('   Barton ID: 04.04.02.04.50000.001');
    console.log('═══════════════════════════════════════════════════════════');
    console.log('');

    const results = await runAudit();

    console.log('\n📝 Generating audit report...');
    const report = generateReport(results);
    const reportPath = path.join(__dirname, '..', '..', '..', 'PLE_CONSTRAINT_AUDIT_REPORT.md');
    fs.writeFileSync(reportPath, report);
    console.log(`✅ Report saved: ${reportPath}`);

    console.log('\n📝 Generating migration SQL...');
    const migrationSQL = generateMigrationSQL(results);
    const sqlPath = path.join(__dirname, 'ple_constraint_migration.sql');
    fs.writeFileSync(sqlPath, migrationSQL);
    console.log(`✅ SQL saved: ${sqlPath}`);

    console.log('\n═══════════════════════════════════════════════════════════');
    console.log('   AUDIT COMPLETE');
    console.log('═══════════════════════════════════════════════════════════');
    console.log('');
    console.log('Next steps:');
    console.log('1. Review: PLE_CONSTRAINT_AUDIT_REPORT.md');
    console.log('2. Clean data if violations exist');
    console.log('3. Execute: ple_constraint_migration.sql');
    console.log('');

  } catch (error) {
    console.error('\n❌ AUDIT FAILED');
    console.error('Error:', error.message);
    console.error('Stack:', error.stack);
    process.exit(1);
  }
})();

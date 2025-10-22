/**
 * Execute Intelligence Table Migrations via Composio MCP
 *
 * Barton Doctrine Spec:
 * - Barton ID: 04.04.99.07.migration.XXX
 * - Altitude: 10000 (Execution Layer)
 * - MCP: Composio (http://localhost:3001/tool)
 * - Tool: neon_execute_sql
 *
 * Creates:
 * - marketing.company_intelligence (04.04.03.XX.XXXXX.XXX)
 * - marketing.people_intelligence (04.04.04.XX.XXXXX.XXX)
 */

import fetch from 'node-fetch';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const COMPOSIO_MCP_URL = process.env.COMPOSIO_MCP_URL || 'http://localhost:3001/tool';
const COMPOSIO_USER_ID = process.env.COMPOSIO_USER_ID || 'usr_default';

console.log('\n=== Executing Intelligence Migrations via Composio MCP ===\n');
console.log(`MCP URL: ${COMPOSIO_MCP_URL}`);
console.log(`User ID: ${COMPOSIO_USER_ID}\n`);

/**
 * Execute Neon SQL via Composio MCP
 */
async function executeNeonSQL(sql, description) {
  const payload = {
    tool: 'neon_execute_sql',
    data: {
      sql: sql,
      database_url: process.env.NEON_DATABASE_URL || process.env.DATABASE_URL
    },
    unique_id: `HEIR-2025-10-MIGRATION-${Date.now()}`,
    process_id: `PRC-INTEL-MIGRATION-${Date.now()}`,
    orbt_layer: 2,
    blueprint_version: '1.0'
  };

  console.log(`\n[EXEC] ${description}`);
  console.log(`[SQL]  ${sql.substring(0, 100)}...`);

  try {
    const response = await fetch(`${COMPOSIO_MCP_URL}?user_id=${COMPOSIO_USER_ID}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    const text = await response.text();

    if (!response.ok) {
      console.error(`❌ HTTP ${response.status}`);
      console.error(`   Response: ${text.substring(0, 300)}`);
      return {
        success: false,
        error: `HTTP ${response.status}: ${text.substring(0, 200)}`
      };
    }

    try {
      const data = JSON.parse(text);
      console.log(`✅ Success`);
      return {
        success: true,
        data: data
      };
    } catch (parseError) {
      console.log(`✅ Success (non-JSON response)`);
      return {
        success: true,
        data: text
      };
    }

  } catch (error) {
    console.error(`❌ Failed: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
}

async function runIntelligenceMigrations() {
  const results = {
    company_intelligence_created: false,
    people_intelligence_created: false,
    verification_passed: false,
    errors: []
  };

  try {
    // Load migration SQL files
    const companyIntelMigrationPath = path.join(
      __dirname,
      '../migrations/2025-10-22_create_marketing_company_intelligence.sql'
    );
    const peopleIntelMigrationPath = path.join(
      __dirname,
      '../migrations/2025-10-22_create_marketing_people_intelligence.sql'
    );

    console.log('[LOADING] Reading migration files...\n');

    const companyIntelSQL = await fs.readFile(companyIntelMigrationPath, 'utf8');
    const peopleIntelSQL = await fs.readFile(peopleIntelMigrationPath, 'utf8');

    console.log(`✓ company_intelligence.sql (${companyIntelSQL.length} chars)`);
    console.log(`✓ people_intelligence.sql (${peopleIntelSQL.length} chars)`);

    // =================================================================
    // STEP 1: Create marketing.company_intelligence via Composio MCP
    // =================================================================
    console.log('\n' + '='.repeat(60));
    console.log('[STEP 1] Creating marketing.company_intelligence');
    console.log('='.repeat(60));

    const companyIntelResult = await executeNeonSQL(
      companyIntelSQL,
      'Execute company_intelligence migration'
    );

    if (companyIntelResult.success) {
      console.log('\n✅ marketing.company_intelligence table created');
      results.company_intelligence_created = true;
    } else {
      console.error('\n❌ Failed to create company_intelligence');
      console.error(`   Error: ${companyIntelResult.error}`);
      results.errors.push(`company_intelligence: ${companyIntelResult.error}`);
    }

    // =================================================================
    // STEP 2: Create marketing.people_intelligence via Composio MCP
    // =================================================================
    console.log('\n' + '='.repeat(60));
    console.log('[STEP 2] Creating marketing.people_intelligence');
    console.log('='.repeat(60));

    const peopleIntelResult = await executeNeonSQL(
      peopleIntelSQL,
      'Execute people_intelligence migration'
    );

    if (peopleIntelResult.success) {
      console.log('\n✅ marketing.people_intelligence table created');
      results.people_intelligence_created = true;
    } else {
      console.error('\n❌ Failed to create people_intelligence');
      console.error(`   Error: ${peopleIntelResult.error}`);
      results.errors.push(`people_intelligence: ${peopleIntelResult.error}`);
    }

    // =================================================================
    // STEP 3: Verify Tables Were Created
    // =================================================================
    console.log('\n' + '='.repeat(60));
    console.log('[STEP 3] Verifying tables via Composio MCP');
    console.log('='.repeat(60));

    const verifySQL = `
      SELECT
        table_schema,
        table_name,
        (SELECT COUNT(*) FROM information_schema.columns
         WHERE table_schema = t.table_schema
         AND table_name = t.table_name) as column_count
      FROM information_schema.tables t
      WHERE table_name IN ('company_intelligence', 'people_intelligence')
        AND table_schema = 'marketing'
      ORDER BY table_name;
    `;

    const verifyResult = await executeNeonSQL(
      verifySQL,
      'Verify intelligence tables exist'
    );

    if (verifyResult.success) {
      // Parse rows from Composio response
      const rows = verifyResult.data?.rows || verifyResult.data || [];

      if (Array.isArray(rows) && rows.length === 2) {
        console.log('\n✅ Both intelligence tables verified:\n');
        rows.forEach(table => {
          console.log(`   ✓ ${table.table_schema}.${table.table_name} (${table.column_count} columns)`);
        });
        results.verification_passed = true;
      } else {
        console.error(`\n❌ Verification failed: Expected 2 tables, found ${rows.length}`);
        results.errors.push(`Verification failed: found ${rows.length} tables`);
      }
    } else {
      console.error('\n❌ Table verification failed');
      console.error(`   Error: ${verifyResult.error}`);
      results.errors.push(`Verification query failed: ${verifyResult.error}`);
    }

    // =================================================================
    // STEP 4: Test Barton ID Generation
    // =================================================================
    console.log('\n' + '='.repeat(60));
    console.log('[STEP 4] Testing Barton ID generation');
    console.log('='.repeat(60));

    const testCompanyIdSQL = `SELECT marketing.generate_company_intelligence_barton_id() as id;`;
    const testPeopleIdSQL = `SELECT marketing.generate_people_intelligence_barton_id() as id;`;

    const companyIdTest = await executeNeonSQL(testCompanyIdSQL, 'Generate company intelligence ID');
    const peopleIdTest = await executeNeonSQL(testPeopleIdSQL, 'Generate people intelligence ID');

    if (companyIdTest.success && peopleIdTest.success) {
      const companyIdRow = (companyIdTest.data?.rows || companyIdTest.data || [])[0];
      const peopleIdRow = (peopleIdTest.data?.rows || peopleIdTest.data || [])[0];

      const companyId = companyIdRow?.id || companyIdRow?.generate_company_intelligence_barton_id;
      const peopleId = peopleIdRow?.id || peopleIdRow?.generate_people_intelligence_barton_id;

      console.log('\n✅ Barton ID generation successful:\n');
      console.log(`   Company Intelligence: ${companyId}`);
      console.log(`   People Intelligence:  ${peopleId}\n`);

      // Verify format
      const companyIdMatch = companyId?.match(/^04\.04\.03\.\d{2}\.\d{5}\.\d{3}$/);
      const peopleIdMatch = peopleId?.match(/^04\.04\.04\.\d{2}\.\d{5}\.\d{3}$/);

      if (companyIdMatch && peopleIdMatch) {
        console.log('✅ Barton ID format validation passed');
      } else {
        console.log('⚠️  Barton ID format validation warnings:');
        if (!companyIdMatch) console.log(`   ✗ Company ID: ${companyId}`);
        if (!peopleIdMatch) console.log(`   ✗ People ID: ${peopleId}`);
      }
    } else {
      console.log('\n⚠️  Could not test Barton ID generation');
    }

    // =================================================================
    // MIGRATION SUMMARY
    // =================================================================
    console.log('\n\n' + '='.repeat(60));
    console.log('=== MIGRATION SUMMARY ===');
    console.log('='.repeat(60) + '\n');

    console.log('Table Creation (via Composio MCP):');
    console.log(`  marketing.company_intelligence: ${results.company_intelligence_created ? '✅ SUCCESS' : '❌ FAILED'}`);
    console.log(`  marketing.people_intelligence:  ${results.people_intelligence_created ? '✅ SUCCESS' : '❌ FAILED'}`);

    console.log('\nVerification:');
    console.log(`  Schema verification: ${results.verification_passed ? '✅ PASSED' : '❌ FAILED'}`);

    if (results.errors.length > 0) {
      console.log('\n⚠️  Errors encountered:');
      results.errors.forEach(error => {
        console.log(`  - ${error}`);
      });
    }

    if (results.company_intelligence_created &&
        results.people_intelligence_created &&
        results.verification_passed) {
      console.log('\n🎯 MIGRATION STATUS: ✅ COMPLETE');
      console.log('   All intelligence tables created via Composio MCP');
      console.log('   Schema is now Barton Doctrine compliant!');
      console.log('   MCP Tool: neon_execute_sql');
      console.log(`   MCP Server: ${COMPOSIO_MCP_URL}\n`);
    } else {
      console.log('\n⚠️  MIGRATION STATUS: INCOMPLETE');
      console.log('   Review errors above and retry if needed\n');
    }

    return results;

  } catch (error) {
    console.error('\n❌ Migration failed:', error);
    console.error('   Stack:', error.stack);
    results.errors.push(`Fatal error: ${error.message}`);
    throw error;
  }
}

// Execute migrations
runIntelligenceMigrations()
  .then((results) => {
    if (results.company_intelligence_created &&
        results.people_intelligence_created &&
        results.verification_passed) {
      console.log('✅ All migrations completed via Composio MCP!');
      process.exit(0);
    } else {
      console.error('⚠️  Migrations completed with errors');
      process.exit(1);
    }
  })
  .catch(error => {
    console.error('❌ Fatal migration error:', error.message);
    process.exit(1);
  });

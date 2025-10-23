/**
 * Run Intelligence Table Migrations via Composio MCP
 *
 * Barton Doctrine Spec:
 * - Barton ID: 04.04.99.07.migration.XXX
 * - Altitude: 10000 (Execution Layer)
 * - MCP: Composio (Neon bridge)
 *
 * Creates:
 * - marketing.company_intelligence (04.04.03.XX.XXXXX.XXX)
 * - marketing.people_intelligence (04.04.04.XX.XXXXX.XXX)
 */

import ComposioNeonBridge from '../api/lib/composio-neon-bridge.js';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('\n=== Running Intelligence Table Migrations via Composio MCP ===\n');

async function runIntelligenceMigrations() {
  const bridge = new ComposioNeonBridge();

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

    console.log('[MIGRATION] Loading SQL files...\n');

    const companyIntelSQL = await fs.readFile(companyIntelMigrationPath, 'utf8');
    const peopleIntelSQL = await fs.readFile(peopleIntelMigrationPath, 'utf8');

    console.log(`✓ Loaded company_intelligence migration (${companyIntelSQL.length} chars)`);
    console.log(`✓ Loaded people_intelligence migration (${peopleIntelSQL.length} chars)`);

    // =================================================================
    // STEP 1: Create marketing.company_intelligence
    // =================================================================
    console.log('\n[STEP 1] Creating marketing.company_intelligence via Composio MCP...\n');
    console.log('─'.repeat(60));

    const companyIntelResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: companyIntelSQL,
      mode: 'write',
      return_type: 'affected_rows'
    });

    if (companyIntelResult.success) {
      console.log('✅ marketing.company_intelligence created successfully');
      console.log(`   Source: ${companyIntelResult.source}`);
      results.company_intelligence_created = true;
    } else {
      console.error('❌ Failed to create marketing.company_intelligence');
      console.error(`   Error: ${companyIntelResult.error}`);
      results.errors.push(`company_intelligence: ${companyIntelResult.error}`);
    }

    // =================================================================
    // STEP 2: Create marketing.people_intelligence
    // =================================================================
    console.log('\n[STEP 2] Creating marketing.people_intelligence via Composio MCP...\n');
    console.log('─'.repeat(60));

    const peopleIntelResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: peopleIntelSQL,
      mode: 'write',
      return_type: 'affected_rows'
    });

    if (peopleIntelResult.success) {
      console.log('✅ marketing.people_intelligence created successfully');
      console.log(`   Source: ${peopleIntelResult.source}`);
      results.people_intelligence_created = true;
    } else {
      console.error('❌ Failed to create marketing.people_intelligence');
      console.error(`   Error: ${peopleIntelResult.error}`);
      results.errors.push(`people_intelligence: ${peopleIntelResult.error}`);
    }

    // =================================================================
    // STEP 3: Verify Tables Were Created
    // =================================================================
    console.log('\n[STEP 3] Verifying tables via Composio MCP...\n');
    console.log('─'.repeat(60));

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

    const verifyResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: verifySQL,
      mode: 'read',
      return_type: 'rows'
    });

    if (verifyResult.success) {
      const tables = verifyResult.data.rows || verifyResult.data;

      if (tables.length === 2) {
        console.log('✅ Both intelligence tables verified in Neon:\n');
        tables.forEach(table => {
          console.log(`   ✓ ${table.table_schema}.${table.table_name} (${table.column_count} columns)`);
        });
        results.verification_passed = true;
      } else {
        console.error(`❌ Verification failed: Expected 2 tables, found ${tables.length}`);
        results.errors.push(`Verification failed: found ${tables.length} tables instead of 2`);
      }
    } else {
      console.error('❌ Table verification failed');
      console.error(`   Error: ${verifyResult.error}`);
      results.errors.push(`Verification query failed: ${verifyResult.error}`);
    }

    // =================================================================
    // STEP 4: Verify Helper Functions
    // =================================================================
    console.log('\n[STEP 4] Verifying helper functions via Composio MCP...\n');
    console.log('─'.repeat(60));

    const functionsSQL = `
      SELECT
        proname as function_name,
        pg_get_function_arguments(oid) as arguments
      FROM pg_proc
      WHERE proname ILIKE '%intelligence%'
        AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'marketing')
      ORDER BY proname;
    `;

    const functionsResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: functionsSQL,
      mode: 'read',
      return_type: 'rows'
    });

    if (functionsResult.success) {
      const functions = functionsResult.data.rows || functionsResult.data;
      console.log(`✅ Found ${functions.length} intelligence functions:\n`);

      functions.forEach(func => {
        console.log(`   ✓ ${func.function_name}(${func.arguments || ''})`);
      });
    } else {
      console.log('⚠️  Could not verify functions');
      console.log(`   Error: ${functionsResult.error}`);
    }

    // =================================================================
    // STEP 5: Test Barton ID Generation
    // =================================================================
    console.log('\n[STEP 5] Testing Barton ID generation via Composio MCP...\n');
    console.log('─'.repeat(60));

    const testCompanyIdSQL = `SELECT marketing.generate_company_intelligence_barton_id();`;
    const testPeopleIdSQL = `SELECT marketing.generate_people_intelligence_barton_id();`;

    const companyIdTest = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: testCompanyIdSQL,
      mode: 'read',
      return_type: 'rows'
    });

    const peopleIdTest = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: testPeopleIdSQL,
      mode: 'read',
      return_type: 'rows'
    });

    if (companyIdTest.success && peopleIdTest.success) {
      const companyId = Object.values(companyIdTest.data.rows[0] || companyIdTest.data[0])[0];
      const peopleId = Object.values(peopleIdTest.data.rows[0] || peopleIdTest.data[0])[0];

      console.log('✅ Barton ID generation tested:\n');
      console.log(`   Company Intelligence: ${companyId}`);
      console.log(`   People Intelligence:  ${peopleId}\n`);

      // Verify format
      const companyIdMatch = companyId?.match(/^04\.04\.03\.\d{2}\.\d{5}\.\d{3}$/);
      const peopleIdMatch = peopleId?.match(/^04\.04\.04\.\d{2}\.\d{5}\.\d{3}$/);

      if (companyIdMatch && peopleIdMatch) {
        console.log('✅ Barton ID format validation passed');
      } else {
        console.log('⚠️  Barton ID format validation failed');
        if (!companyIdMatch) {
          console.log(`   ✗ Company ID format incorrect: ${companyId}`);
        }
        if (!peopleIdMatch) {
          console.log(`   ✗ People ID format incorrect: ${peopleId}`);
        }
      }
    } else {
      console.log('⚠️  Could not test Barton ID generation');
    }

    // =================================================================
    // MIGRATION SUMMARY
    // =================================================================
    console.log('\n\n' + '='.repeat(60));
    console.log('=== MIGRATION SUMMARY ===');
    console.log('='.repeat(60) + '\n');

    console.log('Table Creation:');
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
      console.log('   All intelligence tables created successfully via Composio MCP');
      console.log('   Schema is now Barton Doctrine compliant!\n');
    } else {
      console.log('\n⚠️  MIGRATION STATUS: INCOMPLETE');
      console.log('   Some tables may not have been created successfully');
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
      console.log('✅ All migrations completed successfully via Composio MCP!');
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

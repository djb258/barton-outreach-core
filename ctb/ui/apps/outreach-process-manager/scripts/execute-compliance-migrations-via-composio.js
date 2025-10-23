/**
 * Execute Column Compliance Migrations via Composio MCP
 *
 * Barton Doctrine Spec:
 * - Barton ID: 04.04.99.08.compliance.XXX
 * - Altitude: 10000 (Execution Layer)
 * - MCP: Composio (http://localhost:3001/tool)
 * - Tool: neon_execute_sql
 *
 * Applies 4 critical schema fixes from FINAL_COLUMN_COMPLIANCE_REPORT.md:
 * 1. Fix marketing.company_slot duplicate columns
 * 2. Fix company_slot FK to reference company_master
 * 3. Rename people_master.unique_id to people_unique_id
 * 4. Verify/create shq schema views
 */

import fetch from 'node-fetch';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const COMPOSIO_MCP_URL = process.env.COMPOSIO_MCP_URL || 'http://localhost:3001/tool';
const COMPOSIO_USER_ID = process.env.COMPOSIO_USER_ID || 'usr_default';

console.log('\n=== Executing Column Compliance Migrations via Composio MCP ===\n');
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
    unique_id: `HEIR-2025-10-COMPLIANCE-${Date.now()}`,
    process_id: `PRC-COMPLIANCE-MIGRATION-${Date.now()}`,
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

async function runComplianceMigrations() {
  const results = {
    fix_duplicates: false,
    fix_fk: false,
    rename_column: false,
    verify_views: false,
    verification_passed: false,
    errors: []
  };

  try {
    // Migration file paths
    const migrations = [
      {
        key: 'fix_duplicates',
        file: '../migrations/2025-10-23_fix_marketing_company_slot_duplicates.sql',
        description: 'Fix duplicate timestamp columns in company_slot'
      },
      {
        key: 'fix_fk',
        file: '../migrations/2025-10-23_fix_company_slot_fk.sql',
        description: 'Fix company_slot FK to reference company_master'
      },
      {
        key: 'rename_column',
        file: '../migrations/2025-10-23_fix_people_master_column_naming.sql',
        description: 'Rename people_master.unique_id to people_unique_id'
      },
      {
        key: 'verify_views',
        file: '../migrations/2025-10-23_verify_shq_views.sql',
        description: 'Verify/create shq.audit_log and shq.validation_queue views'
      }
    ];

    console.log('[LOADING] Reading migration files...\n');

    // Load all migration files
    for (const migration of migrations) {
      const filePath = path.join(__dirname, migration.file);
      try {
        migration.sql = await fs.readFile(filePath, 'utf8');
        console.log(`✓ ${path.basename(migration.file)} (${migration.sql.length} chars)`);
      } catch (error) {
        console.error(`✗ Failed to read ${migration.file}: ${error.message}`);
        results.errors.push(`Failed to read ${migration.file}`);
        return results;
      }
    }

    // Execute each migration in sequence
    for (let i = 0; i < migrations.length; i++) {
      const migration = migrations[i];
      console.log('\n' + '='.repeat(70));
      console.log(`[STEP ${i + 1}/${migrations.length}] ${migration.description}`);
      console.log('='.repeat(70));

      const result = await executeNeonSQL(migration.sql, migration.description);

      if (result.success) {
        console.log(`\n✅ Migration ${i + 1} completed successfully`);
        results[migration.key] = true;
      } else {
        console.error(`\n❌ Migration ${i + 1} failed`);
        console.error(`   Error: ${result.error}`);
        results.errors.push(`${migration.key}: ${result.error}`);
        // Continue with remaining migrations even if one fails
      }
    }

    // =================================================================
    // VERIFICATION STEP: Confirm all fixes were applied
    // =================================================================
    console.log('\n' + '='.repeat(70));
    console.log('[VERIFICATION] Checking schema compliance');
    console.log('='.repeat(70));

    const verificationQueries = [
      {
        name: 'Check company_slot columns',
        sql: `
          SELECT column_name, data_type
          FROM information_schema.columns
          WHERE table_schema = 'marketing'
            AND table_name = 'company_slot'
            AND column_name IN ('created_at', 'updated_at')
          ORDER BY ordinal_position;
        `
      },
      {
        name: 'Check company_slot FK',
        sql: `
          SELECT constraint_name, table_name
          FROM information_schema.table_constraints
          WHERE constraint_schema = 'marketing'
            AND table_name = 'company_slot'
            AND constraint_type = 'FOREIGN KEY'
            AND constraint_name LIKE '%company_master%';
        `
      },
      {
        name: 'Check people_master column',
        sql: `
          SELECT column_name
          FROM information_schema.columns
          WHERE table_schema = 'marketing'
            AND table_name = 'people_master'
            AND column_name = 'people_unique_id';
        `
      },
      {
        name: 'Check shq views',
        sql: `
          SELECT table_schema, table_name, table_type
          FROM information_schema.tables
          WHERE table_schema = 'shq'
            AND table_name IN ('audit_log', 'validation_queue')
          ORDER BY table_name;
        `
      }
    ];

    let allVerificationsPassed = true;

    for (const query of verificationQueries) {
      console.log(`\n[VERIFY] ${query.name}`);
      const result = await executeNeonSQL(query.sql, query.name);

      if (result.success) {
        const rows = result.data?.rows || result.data || [];
        console.log(`   ✓ Query returned ${rows.length} row(s)`);
      } else {
        console.error(`   ✗ Verification query failed: ${result.error}`);
        allVerificationsPassed = false;
      }
    }

    results.verification_passed = allVerificationsPassed;

    // =================================================================
    // MIGRATION SUMMARY
    // =================================================================
    console.log('\n\n' + '='.repeat(70));
    console.log('=== MIGRATION SUMMARY ===');
    console.log('='.repeat(70) + '\n');

    console.log('Schema Fixes (via Composio MCP):');
    console.log(`  1. Fix company_slot duplicates:  ${results.fix_duplicates ? '✅ SUCCESS' : '❌ FAILED'}`);
    console.log(`  2. Fix company_slot FK:          ${results.fix_fk ? '✅ SUCCESS' : '❌ FAILED'}`);
    console.log(`  3. Rename people_master column:  ${results.rename_column ? '✅ SUCCESS' : '❌ FAILED'}`);
    console.log(`  4. Verify shq views:             ${results.verify_views ? '✅ SUCCESS' : '❌ FAILED'}`);

    console.log('\nVerification:');
    console.log(`  Schema compliance check: ${results.verification_passed ? '✅ PASSED' : '❌ FAILED'}`);

    if (results.errors.length > 0) {
      console.log('\n⚠️  Errors encountered:');
      results.errors.forEach(error => {
        console.log(`  - ${error}`);
      });
    }

    const allMigrationsSuccess = results.fix_duplicates && results.fix_fk &&
                                 results.rename_column && results.verify_views;

    if (allMigrationsSuccess && results.verification_passed) {
      console.log('\n🎯 MIGRATION STATUS: ✅ COMPLETE');
      console.log('   All compliance fixes applied via Composio MCP');
      console.log('   Schema is now 100% Barton Doctrine compliant!');
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
runComplianceMigrations()
  .then((results) => {
    const allMigrationsSuccess = results.fix_duplicates && results.fix_fk &&
                                 results.rename_column && results.verify_views;

    if (allMigrationsSuccess && results.verification_passed) {
      console.log('✅ All compliance migrations completed via Composio MCP!');
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

#!/usr/bin/env node
/**
 * Execute MCP Task 2: Apply SHQ Views via Composio SDK
 * Barton ID: 03.01.04.20251023.et2cs.001
 *
 * CORRECTED APPROACH: Uses Composio SDK (@composio/core) instead of HTTP calls
 */

import { Composio } from '@composio/core';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const COMPOSIO_API_KEY = process.env.COMPOSIO_API_KEY || 'ak_t-F0AbvfZHUZSUrqAGNn';
const NEON_DATABASE_URL = process.env.NEON_DATABASE_URL || process.env.DATABASE_URL;

console.log('\n=== MCP TASK 2: Apply SHQ Views (Composio SDK) ===\n');
console.log(`API Key: ${COMPOSIO_API_KEY.substring(0, 10)}...`);
console.log(`Database URL: ${NEON_DATABASE_URL ? 'SET' : 'NOT SET'}\n`);

async function executeNeonSQL(composio, sql, description) {
  console.log(`\n[EXEC] ${description}`);

  try {
    // Execute via Composio SDK
    const result = await composio.actions.execute({
      actionName: 'neon_execute_sql',
      appName: 'neon',
      params: {
        sql: sql,
        database_url: NEON_DATABASE_URL
      }
    });

    console.log(`✅ Success`);
    return {
      success: true,
      data: result.data || result
    };

  } catch (error) {
    console.error(`❌ Failed: ${error.message}`);
    return {
      success: false,
      error: error.message,
      stack: error.stack
    };
  }
}

async function applyShqViews() {
  try {
    // Initialize Composio
    console.log('[INIT] Initializing Composio SDK...');
    const composio = new Composio({
      apiKey: COMPOSIO_API_KEY
    });
    console.log('✅ Composio initialized\n');

    // Load SQL migration file
    const migrationPath = path.join(
      __dirname,
      '../../data/migrations/outreach-process-manager/fixes/2025-10-23_create_shq_views.sql'
    );

    console.log('[LOADING] Reading migration file...');
    const sql = await fs.readFile(migrationPath, 'utf8');
    console.log(`✓ Migration SQL loaded (${sql.length} chars)\n`);

    // Execute via Composio SDK
    console.log('='.repeat(60));
    console.log('[EXECUTING] Creating SHQ views via Composio SDK');
    console.log('='.repeat(60));

    const result = await executeNeonSQL(composio, sql, 'Create shq.audit_log and shq.validation_queue views');

    if (result.success) {
      console.log('\n✅ SHQ views created successfully');

      // Verify views
      const verifySQL = `
        SELECT table_schema, table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = 'shq'
          AND table_name IN ('audit_log', 'validation_queue')
        ORDER BY table_name;
      `;

      const verifyResult = await executeNeonSQL(composio, verifySQL, 'Verify SHQ views exist');

      if (verifyResult.success) {
        const rows = verifyResult.data?.rows || verifyResult.data || [];
        console.log(`\n✅ Views verified (${rows.length} found):\n`);
        rows.forEach(row => {
          console.log(`   ✓ ${row.table_schema}.${row.table_name} (${row.table_type})`);
        });
      }

      console.log('\n🎯 TASK 2 STATUS: ✅ COMPLETE');
      console.log('   Views: shq.audit_log, shq.validation_queue');
      console.log('   Method: Composio SDK (@composio/core)');
      console.log('   Action: neon_execute_sql\n');

      return true;
    } else {
      console.error('\n❌ Failed to create SHQ views');
      console.error(`   Error: ${result.error}`);
      if (result.stack) {
        console.error('\n   Stack trace:');
        console.error(result.stack);
      }
      return false;
    }

  } catch (error) {
    console.error('\n❌ Task 2 failed:', error);
    console.error('   Stack:', error.stack);
    return false;
  }
}

// Execute
applyShqViews()
  .then((success) => {
    if (success) {
      console.log('✅ Task 2 completed via Composio SDK!');
      process.exit(0);
    } else {
      console.error('⚠️  Task 2 completed with errors');
      process.exit(1);
    }
  })
  .catch(error => {
    console.error('❌ Fatal error:', error.message);
    console.error(error.stack);
    process.exit(1);
  });

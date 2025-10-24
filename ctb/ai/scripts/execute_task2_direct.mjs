#!/usr/bin/env node
/**
 * Execute MCP Task 2: Apply SHQ Views via Direct DB Connection
 * Barton ID: 03.01.04.20251023.et2direct.001
 *
 * NOTE: Direct connection used because neon_execute_sql tool not found in:
 * - Composio cloud API (backend.composio.dev/api/v3)
 * - Local MCP server (localhost:3001/tool returns "Not found")
 */

import pg from 'pg';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DATABASE_URL = process.env.NEON_DATABASE_URL || process.env.DATABASE_URL;

console.log('\n=== MCP TASK 2: Apply SHQ Views (Direct Connection) ===\n');
console.log('Database URL: ' + (DATABASE_URL ? 'SET' : 'NOT SET'));
console.log('Connection Method: Direct PostgreSQL Client\n');

if (!DATABASE_URL) {
  console.error('❌ DATABASE_URL or NEON_DATABASE_URL environment variable not set');
  console.error('   Please set one of these variables with your Neon connection string');
  process.exit(1);
}

async function executeSQL(sql, description) {
  console.log(`[EXEC] ${description}`);

  const client = new pg.Client({ connectionString: DATABASE_URL });

  try {
    await client.connect();
    const result = await client.query(sql);
    console.log('✅ Success');
    return {
      success: true,
      result: result
    };
  } catch (error) {
    console.error(`❌ Failed: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  } finally {
    await client.end();
  }
}

async function applyShqViews() {
  try {
    // Load SQL migration file
    const migrationPath = path.join(
      __dirname,
      '../../data/migrations/outreach-process-manager/fixes/2025-10-23_create_shq_views.sql'
    );

    console.log('[LOADING] Reading migration file...');
    const sql = await fs.readFile(migrationPath, 'utf8');
    console.log(`✓ Migration SQL loaded (${sql.length} chars)\n`);

    // Execute migration
    console.log('='.repeat(60));
    console.log('[EXECUTING] Creating SHQ views');
    console.log('='.repeat(60));

    const result = await executeSQL(
      sql,
      'Create shq.audit_log and shq.validation_queue views'
    );

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

      const verifyResult = await executeSQL(
        verifySQL,
        'Verify SHQ views exist'
      );

      if (verifyResult.success && verifyResult.result.rows) {
        console.log(`\n✅ Views verified (${verifyResult.result.rows.length} found):\n`);
        verifyResult.result.rows.forEach(row => {
          console.log(`   ✓ ${row.table_schema}.${row.table_name} (${row.table_type})`);
        });
      }

      console.log('\n🎯 TASK 2 STATUS: ✅ COMPLETE');
      console.log('   Views: shq.audit_log, shq.validation_queue');
      console.log('   Method: Direct PostgreSQL Connection');
      console.log('   Client: node-postgres (pg)\n');

      return true;
    } else {
      console.error('\n❌ Failed to create SHQ views');
      console.error(`   Error: ${result.error}`);
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
      console.log('✅ Task 2 completed!');
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

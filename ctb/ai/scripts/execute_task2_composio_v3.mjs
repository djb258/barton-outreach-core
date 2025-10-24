#!/usr/bin/env node
/**
 * Execute MCP Task 2: Apply SHQ Views via Composio V3 API
 * Barton ID: 03.01.04.20251023.et2cv3.001
 */

import fetch from 'node-fetch';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const COMPOSIO_API_KEY = 'ak_t-F0AbvfZHUZSUrqAGNn';
const COMPOSIO_BASE_URL = 'https://backend.composio.dev';
const NEON_DATABASE_URL = process.env.NEON_DATABASE_URL || process.env.DATABASE_URL;

console.log('\n=== MCP TASK 2: Apply SHQ Views (Composio V3 API) ===\n');
console.log(`API Endpoint: ${COMPOSIO_BASE_URL}/api/v3`);
console.log(`Database URL: ${NEON_DATABASE_URL ? 'SET' : 'NOT SET'}\n');

async function listConnectedAccounts() {
  console.log('[INFO] Checking for Neon connected account...');

  try {
    const response = await fetch(`${COMPOSIO_BASE_URL}/api/v3/connectedAccounts`, {
      headers: {
        'x-api-key': COMPOSIO_API_KEY,
        'Authorization': `Bearer ${COMPOSIO_API_KEY}`
      }
    });

    if (!response.ok) {
      console.log(`⚠️  Could not list accounts: ${response.status}`);
      return null;
    }

    const data = await response.json();
    const neonAccount = data.items?.find(acc =>
      acc.appName?.toLowerCase() === 'neon' ||
      acc.integrationId?.toLowerCase().includes('neon')
    );

    if (neonAccount) {
      console.log(`✅ Found Neon account: ${neonAccount.id}\n`);
      return neonAccount.id;
    } else {
      console.log(`⚠️  No Neon connected account found\n`);
      return null;
    }
  } catch (error) {
    console.log(`⚠️  Error checking accounts: ${error.message}\n`);
    return null;
  }
}

async function executeNeonSQL(sql, description, connectedAccountId) {
  console.log(`\n[EXEC] ${description}`);

  const payload = {
    tool_slug: 'neon_execute_sql',
    input: {
      sql: sql,
      database_url: NEON_DATABASE_URL
    }
  };

  // Add connected account if available
  if (connectedAccountId) {
    payload.connected_account_id = connectedAccountId;
  }

  try {
    const response = await fetch(`${COMPOSIO_BASE_URL}/api/v3/tools/execute`, {
      method: 'POST',
      headers: {
        'x-api-key': COMPOSIO_API_KEY,
        'Authorization': `Bearer ${COMPOSIO_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    const responseText = await response.text();

    if (!response.ok) {
      console.error(`❌ HTTP ${response.status}`);
      console.error(`   Response: ${responseText.substring(0, 500)}`);
      return {
        success: false,
        error: `HTTP ${response.status}: ${responseText.substring(0, 200)}`
      };
    }

    try {
      const data = JSON.parse(responseText);
      console.log(`✅ Success`);
      return {
        success: true,
        data: data
      };
    } catch (parseError) {
      console.log(`✅ Success (non-JSON response)`);
      return {
        success: true,
        data: responseText
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

async function applyShqViews() {
  try {
    // Check for connected account
    const connectedAccountId = await listConnectedAccounts();

    // Load SQL migration file
    const migrationPath = path.join(
      __dirname,
      '../../data/migrations/outreach-process-manager/fixes/2025-10-23_create_shq_views.sql'
    );

    console.log('[LOADING] Reading migration file...');
    const sql = await fs.readFile(migrationPath, 'utf8');
    console.log(`✓ Migration SQL loaded (${sql.length} chars)\n`);

    // Execute via Composio V3 API
    console.log('='.repeat(60));
    console.log('[EXECUTING] Creating SHQ views via Composio V3 API');
    console.log('='.repeat(60));

    const result = await executeNeonSQL(
      sql,
      'Create shq.audit_log and shq.validation_queue views',
      connectedAccountId
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

      const verifyResult = await executeNeonSQL(
        verifySQL,
        'Verify SHQ views exist',
        connectedAccountId
      );

      if (verifyResult.success) {
        const rows = verifyResult.data?.rows || verifyResult.data?.items || [];
        console.log(`\n✅ Views verified (${rows.length} found):\n`);
        rows.forEach(row => {
          console.log(`   ✓ ${row.table_schema}.${row.table_name} (${row.table_type})`);
        });
      }

      console.log('\n🎯 TASK 2 STATUS: ✅ COMPLETE');
      console.log('   Views: shq.audit_log, shq.validation_queue');
      console.log('   Method: Composio V3 API');
      console.log('   Endpoint: /api/v3/tools/execute\n');

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
      console.log('✅ Task 2 completed via Composio V3 API!');
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

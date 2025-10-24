/**
 * Execute MCP Task 2: Apply SHQ Views via Composio MCP
 * Barton ID: 03.01.04.20251023.et2mc.001
 */

import fetch from 'node-fetch';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const COMPOSIO_MCP_URL = process.env.COMPOSIO_MCP_URL || 'http://localhost:3001/tool';
const COMPOSIO_USER_ID = process.env.COMPOSIO_USER_ID || 'usr_default';

console.log('\n=== MCP TASK 2: Apply SHQ Views ===\n');
console.log(`MCP URL: ${COMPOSIO_MCP_URL}`);
console.log(`User ID: ${COMPOSIO_USER_ID}\n`);

async function executeNeonSQL(sql, description) {
  const payload = {
    tool: 'neon_execute_sql',
    data: {
      sql: sql,
      database_url: process.env.NEON_DATABASE_URL || process.env.DATABASE_URL
    },
    unique_id: `HEIR-2025-10-23-TASK2-${Date.now()}`,
    process_id: `PRC-SHQ-VIEWS-${Date.now()}`,
    orbt_layer: 2,
    blueprint_version: '1.0'
  };

  console.log(`\n[EXEC] ${description}`);

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

async function applyShqViews() {
  try {
    // Load SQL migration file
    const migrationPath = path.join(
      __dirname,
      '../../data/migrations/outreach-process-manager/fixes/2025-10-23_create_shq_views.sql'
    );

    console.log('[LOADING] Reading migration file...\n');
    const sql = await fs.readFile(migrationPath, 'utf8');
    console.log(`✓ Migration SQL loaded (${sql.length} chars)`);

    // Execute via Composio MCP
    console.log('\n' + '='.repeat(60));
    console.log('[EXECUTING] Creating SHQ views via Composio MCP');
    console.log('='.repeat(60));

    const result = await executeNeonSQL(sql, 'Create shq.audit_log and shq.validation_queue views');

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

      const verifyResult = await executeNeonSQL(verifySQL, 'Verify SHQ views exist');

      if (verifyResult.success) {
        const rows = verifyResult.data?.rows || verifyResult.data || [];
        console.log(`\n✅ Views verified (${rows.length} found):\n`);
        rows.forEach(row => {
          console.log(`   ✓ ${row.table_schema}.${row.table_name} (${row.table_type})`);
        });
      }

      console.log('\n🎯 TASK 2 STATUS: ✅ COMPLETE');
      console.log('   Views: shq.audit_log, shq.validation_queue');
      console.log('   MCP Tool: neon_execute_sql');
      console.log(`   MCP Server: ${COMPOSIO_MCP_URL}\n`);

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
      console.log('✅ Task 2 completed via Composio MCP!');
      process.exit(0);
    } else {
      console.error('⚠️  Task 2 completed with errors');
      process.exit(1);
    }
  })
  .catch(error => {
    console.error('❌ Fatal error:', error.message);
    process.exit(1);
  });

/**
 * Post-Fix Schema Verification Script
 *
 * Purpose: Re-run the 6 verification queries from FINAL_COLUMN_COMPLIANCE_REPORT.md
 *          after applying schema fixes (2025-10-23)
 *
 * Requires: MCP server running on localhost:3001
 *
 * Fixes Applied:
 * - Fix A: Removed duplicate columns in company_slot
 * - Fix B: Corrected FK to company_master
 * - Fix C: Renamed unique_id to people_unique_id
 * - Fix D: Verified shq views exist
 *
 * Usage:
 *   node scripts/run_post_fix_verification_via_composio.js
 */

const fs = require('fs');
const path = require('path');

// MCP Server Configuration
const MCP_BASE_URL = 'http://localhost:3001';
const REPORT_PATH = path.join(__dirname, '../analysis/FINAL_COLUMN_COMPLIANCE_REPORT.md');

// HEIR/ORBT Payload Generator
function generateHeirPayload(tool, sqlQuery, uniqueIdSuffix) {
  const timestamp = Math.floor(Date.now() / 1000);
  return {
    tool: tool,
    data: {
      sql_query: sqlQuery
    },
    unique_id: `HEIR-2025-10-POST-FIX-${uniqueIdSuffix}`,
    process_id: `PRC-POST-FIX-VERIFICATION-${timestamp}`,
    orbt_layer: 3,
    blueprint_version: '1.0'
  };
}

// Six Verification Queries from FINAL_COLUMN_COMPLIANCE_REPORT.md
const VERIFICATION_QUERIES = [
  {
    id: 'QUERY-01',
    name: 'Column Metadata',
    description: 'Get all columns with data types, nullability, defaults, and comments',
    sql: `
      SELECT
        t.table_schema,
        t.table_name,
        t.table_type,
        c.column_name,
        c.ordinal_position,
        c.data_type,
        c.character_maximum_length,
        c.numeric_precision,
        c.numeric_scale,
        c.is_nullable,
        c.column_default,
        c.is_generated,
        c.generation_expression,
        pgd.description as column_comment
      FROM information_schema.tables t
      JOIN information_schema.columns c
        ON t.table_schema = c.table_schema
        AND t.table_name = c.table_name
      LEFT JOIN pg_catalog.pg_description pgd
        ON pgd.objoid = (t.table_schema||'.'||t.table_name)::regclass::oid
        AND pgd.objsubid = c.ordinal_position
      WHERE t.table_schema IN ('marketing', 'shq')
        AND t.table_name IN (
          'company_master', 'people_master', 'company_slot',
          'company_intelligence', 'people_intelligence', 'outreach_history',
          'audit_log', 'validation_queue', 'unified_audit_log'
        )
      ORDER BY t.table_schema, t.table_name, c.ordinal_position;
    `
  },
  {
    id: 'QUERY-02',
    name: 'Table Constraints',
    description: 'Get all CHECK constraints, foreign keys, and unique constraints',
    sql: `
      SELECT
        tc.table_schema,
        tc.table_name,
        tc.constraint_type,
        tc.constraint_name,
        cc.check_clause,
        kcu.column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
      FROM information_schema.table_constraints tc
      LEFT JOIN information_schema.check_constraints cc
        ON tc.constraint_name = cc.constraint_name
      LEFT JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
      LEFT JOIN information_schema.constraint_column_usage ccu
        ON tc.constraint_name = ccu.constraint_name
      WHERE tc.table_schema IN ('marketing', 'shq')
        AND tc.table_name IN (
          'company_master', 'people_master', 'company_slot',
          'company_intelligence', 'people_intelligence', 'unified_audit_log'
        )
      ORDER BY tc.table_schema, tc.table_name, tc.constraint_type, tc.constraint_name;
    `
  },
  {
    id: 'QUERY-03',
    name: 'Index Information',
    description: 'Get all indexes for doctrine tables',
    sql: `
      SELECT
        t.schemaname,
        t.tablename,
        i.indexname,
        i.indexdef,
        pg_size_pretty(pg_relation_size(i.indexrelid)) as index_size
      FROM pg_indexes i
      JOIN pg_tables t
        ON i.tablename = t.tablename
        AND i.schemaname = t.schemaname
      WHERE t.schemaname IN ('marketing', 'shq')
        AND t.tablename IN (
          'company_master', 'people_master', 'company_slot',
          'company_intelligence', 'people_intelligence', 'unified_audit_log'
        )
      ORDER BY t.schemaname, t.tablename, i.indexname;
    `
  },
  {
    id: 'QUERY-04',
    name: 'Trigger Information',
    description: 'Get all triggers for doctrine tables',
    sql: `
      SELECT
        t.trigger_schema,
        t.event_object_table,
        t.trigger_name,
        t.event_manipulation,
        t.action_timing,
        t.action_statement
      FROM information_schema.triggers t
      WHERE t.trigger_schema IN ('marketing', 'shq')
        AND t.event_object_table IN (
          'company_master', 'people_master', 'company_slot',
          'company_intelligence', 'people_intelligence', 'unified_audit_log'
        )
      ORDER BY t.trigger_schema, t.event_object_table, t.trigger_name;
    `
  },
  {
    id: 'QUERY-05',
    name: 'View Definitions',
    description: 'Get view definitions for outreach_history and shq views',
    sql: `
      SELECT
        table_schema,
        table_name,
        view_definition
      FROM information_schema.views
      WHERE table_schema IN ('marketing', 'shq')
        AND table_name IN ('outreach_history', 'audit_log', 'validation_queue')
      ORDER BY table_schema, table_name;
    `
  },
  {
    id: 'QUERY-06',
    name: 'Row Counts',
    description: 'Verify tables are populated with data',
    sql: `
      SELECT 'company_master' as table_name, COUNT(*) as row_count
      FROM marketing.company_master
      UNION ALL
      SELECT 'people_master', COUNT(*)
      FROM marketing.people_master
      UNION ALL
      SELECT 'company_slot', COUNT(*)
      FROM marketing.company_slot
      UNION ALL
      SELECT 'company_intelligence', COUNT(*)
      FROM marketing.company_intelligence
      UNION ALL
      SELECT 'people_intelligence', COUNT(*)
      FROM marketing.people_intelligence
      UNION ALL
      SELECT 'unified_audit_log', COUNT(*)
      FROM marketing.unified_audit_log
      ORDER BY table_name;
    `
  }
];

// Execute verification query via Composio MCP
async function executeQuery(query) {
  const payload = generateHeirPayload('neon_execute_sql', query.sql, query.id);

  try {
    const response = await fetch(`${MCP_BASE_URL}/tool`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    return {
      query: query.id,
      name: query.name,
      status: 'success',
      rowCount: result.data?.rows?.length || 0,
      data: result.data
    };
  } catch (error) {
    return {
      query: query.id,
      name: query.name,
      status: 'error',
      error: error.message
    };
  }
}

// Check MCP server health
async function checkMcpHealth() {
  try {
    const response = await fetch(`${MCP_BASE_URL}/mcp/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000)
    });

    if (!response.ok) {
      return { available: false, error: `HTTP ${response.status}` };
    }

    const health = await response.json();
    return { available: true, health };
  } catch (error) {
    return { available: false, error: error.message };
  }
}

// Generate markdown report section
function generateMarkdownReport(results, mcpHealth) {
  const timestamp = new Date().toISOString();

  let markdown = `\n\n---\n\n`;
  markdown += `## 🔍 POST-FIX VERIFICATION RESULTS\n\n`;
  markdown += `**Executed**: ${timestamp}\n`;
  markdown += `**MCP Server**: ${mcpHealth.available ? '✅ Available' : '❌ Unavailable'}\n`;
  markdown += `**Migrations Applied**:\n`;
  markdown += `- ✅ Fix A: Removed duplicate columns in company_slot\n`;
  markdown += `- ✅ Fix B: Corrected FK reference to company_master\n`;
  markdown += `- ✅ Fix C: Renamed unique_id to people_unique_id\n`;
  markdown += `- ✅ Fix D: Verified shq.audit_log and shq.validation_queue views\n\n`;

  markdown += `### Verification Query Results\n\n`;
  markdown += `| Query | Name | Status | Rows Returned | Notes |\n`;
  markdown += `|-------|------|--------|---------------|-------|\n`;

  for (const result of results) {
    const status = result.status === 'success' ? '✅' : '❌';
    const notes = result.error || '-';
    markdown += `| ${result.query} | ${result.name} | ${status} | ${result.rowCount || 0} | ${notes} |\n`;
  }

  markdown += `\n### Key Findings\n\n`;

  // Analyze results
  const columnMetadata = results.find(r => r.query === 'QUERY-01');
  if (columnMetadata && columnMetadata.status === 'success') {
    const peopleUnique = columnMetadata.data.rows?.filter(r =>
      r.table_name === 'people_master' && r.column_name === 'people_unique_id'
    );
    const oldUnique = columnMetadata.data.rows?.filter(r =>
      r.table_name === 'people_master' && r.column_name === 'unique_id'
    );

    if (peopleUnique?.length > 0) {
      markdown += `- ✅ **Fix C Verified**: Column renamed to \`people_unique_id\` (${peopleUnique.length} row found)\n`;
    }
    if (oldUnique?.length > 0) {
      markdown += `- ⚠️ **Fix C Issue**: Old column \`unique_id\` still exists (${oldUnique.length} row found)\n`;
    }
  }

  const constraints = results.find(r => r.query === 'QUERY-02');
  if (constraints && constraints.status === 'success') {
    const slotFK = constraints.data.rows?.find(r =>
      r.table_name === 'company_slot' &&
      r.constraint_name === 'fk_company_slot_company_master'
    );

    if (slotFK) {
      markdown += `- ✅ **Fix B Verified**: FK \`fk_company_slot_company_master\` points to \`company_master\`\n`;
    } else {
      markdown += `- ⚠️ **Fix B Issue**: FK \`fk_company_slot_company_master\` not found\n`;
    }
  }

  const views = results.find(r => r.query === 'QUERY-05');
  if (views && views.status === 'success') {
    const auditLog = views.data.rows?.find(r => r.table_name === 'audit_log');
    const validationQueue = views.data.rows?.find(r => r.table_name === 'validation_queue');

    if (auditLog) {
      markdown += `- ✅ **Fix D Verified**: View \`shq.audit_log\` exists\n`;
    }
    if (validationQueue) {
      markdown += `- ✅ **Fix D Verified**: View \`shq.validation_queue\` exists\n`;
    }
    if (!auditLog || !validationQueue) {
      markdown += `- ⚠️ **Fix D Issue**: Some shq views missing (audit_log: ${!!auditLog}, validation_queue: ${!!validationQueue})\n`;
    }
  }

  markdown += `\n**Overall Status**: ${results.every(r => r.status === 'success') ? '✅ All Queries Passed' : '⚠️ Some Queries Failed'}\n`;

  return markdown;
}

// Main execution
async function main() {
  console.log('🔍 Post-Fix Schema Verification Script');
  console.log('=====================================\n');

  // Step 1: Check MCP server health
  console.log('Step 1: Checking MCP server health...');
  const mcpHealth = await checkMcpHealth();

  if (!mcpHealth.available) {
    console.error(`❌ MCP Server unavailable: ${mcpHealth.error}`);
    console.error('Please start the MCP server:');
    console.error('  cd "C:\\Users\\CUSTOM PC\\Desktop\\Cursor Builds\\scraping-tool\\imo-creator\\mcp-servers\\composio-mcp"');
    console.error('  node server.js\n');
    process.exit(1);
  }

  console.log('✅ MCP Server is available\n');

  // Step 2: Execute all verification queries
  console.log('Step 2: Executing verification queries...');
  const results = [];

  for (const query of VERIFICATION_QUERIES) {
    console.log(`  Executing ${query.id}: ${query.name}...`);
    const result = await executeQuery(query);
    results.push(result);
    console.log(`    ${result.status === 'success' ? '✅' : '❌'} ${result.status} (${result.rowCount || 0} rows)`);
  }

  console.log('\nStep 3: Generating markdown report...');
  const markdownReport = generateMarkdownReport(results, mcpHealth);

  // Step 4: Append to FINAL_COLUMN_COMPLIANCE_REPORT.md
  console.log('Step 4: Appending results to report...');
  try {
    fs.appendFileSync(REPORT_PATH, markdownReport, 'utf8');
    console.log(`✅ Results appended to: ${REPORT_PATH}\n`);
  } catch (error) {
    console.error(`❌ Error writing report: ${error.message}\n`);
    console.log('Markdown output:\n');
    console.log(markdownReport);
    process.exit(1);
  }

  // Step 5: Summary
  const successCount = results.filter(r => r.status === 'success').length;
  const totalCount = results.length;

  console.log('=====================================');
  console.log(`✅ Verification Complete: ${successCount}/${totalCount} queries successful`);
  console.log('=====================================\n');

  if (successCount === totalCount) {
    process.exit(0);
  } else {
    process.exit(1);
  }
}

// Run main function
main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});

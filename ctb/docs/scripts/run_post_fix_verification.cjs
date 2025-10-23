/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/scripts
Barton ID: 06.01.04
Unique ID: CTB-3D40B5F1
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

/**
 * Post-Fix Verification Script
 * Re-runs the 6 verification queries from FINAL_COLUMN_COMPLIANCE_REPORT
 * and appends results to the report
 *
 * Uses direct Neon database connection (working pattern)
 */

const { Client } = require('pg');
const fs = require('fs');
const path = require('path');

const DATABASE_URL = process.env.DATABASE_URL || process.env.NEON_DATABASE_URL;

if (!DATABASE_URL) {
  console.error('❌ DATABASE_URL or NEON_DATABASE_URL environment variable required');
  process.exit(1);
}

const VERIFICATION_QUERIES = [
  {
    id: 'QUERY-01',
    name: 'Column Metadata Verification',
    sql: `
      SELECT
        t.table_schema,
        t.table_name,
        c.column_name,
        c.data_type,
        c.ordinal_position
      FROM information_schema.tables t
      JOIN information_schema.columns c
        ON t.table_schema = c.table_schema
        AND t.table_name = c.table_name
      WHERE t.table_schema IN ('marketing', 'intake', 'shq')
        AND (
          c.column_name LIKE '%unique_id%'
          OR c.column_name IN ('created_at', 'updated_at')
        )
      ORDER BY t.table_schema, t.table_name, c.ordinal_position;
    `
  },
  {
    id: 'QUERY-02',
    name: 'Duplicate Column Check',
    sql: `
      SELECT
        table_schema,
        table_name,
        column_name,
        COUNT(*) as occurrence_count
      FROM information_schema.columns
      WHERE table_schema IN ('marketing', 'intake')
      GROUP BY table_schema, table_name, column_name
      HAVING COUNT(*) > 1;
    `
  },
  {
    id: 'QUERY-03',
    name: 'Foreign Key Constraints',
    sql: `
      SELECT
        tc.constraint_schema,
        tc.table_name,
        tc.constraint_name,
        kcu.column_name,
        ccu.table_schema AS foreign_table_schema,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
      FROM information_schema.table_constraints tc
      JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.constraint_schema = kcu.constraint_schema
      JOIN information_schema.constraint_column_usage ccu
        ON ccu.constraint_name = tc.constraint_name
        AND ccu.constraint_schema = tc.constraint_schema
      WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.constraint_schema IN ('marketing', 'intake')
      ORDER BY tc.table_name, tc.constraint_name;
    `
  },
  {
    id: 'QUERY-04',
    name: 'company_slot Specific Verification',
    sql: `
      SELECT
        column_name,
        data_type,
        is_nullable,
        column_default
      FROM information_schema.columns
      WHERE table_schema = 'marketing'
        AND table_name = 'company_slot'
      ORDER BY ordinal_position;
    `
  },
  {
    id: 'QUERY-05',
    name: 'people_master Column Check',
    sql: `
      SELECT
        column_name,
        data_type
      FROM information_schema.columns
      WHERE table_schema = 'marketing'
        AND table_name = 'people_master'
        AND column_name LIKE '%unique_id%';
    `
  },
  {
    id: 'QUERY-06',
    name: 'shq Views Verification',
    sql: `
      SELECT
        table_schema,
        table_name,
        table_type
      FROM information_schema.tables
      WHERE table_schema = 'shq'
        AND table_name IN ('audit_log', 'validation_queue')
      ORDER BY table_name;
    `
  }
];

async function runVerification() {
  const client = new Client({ connectionString: DATABASE_URL });
  const results = [];

  try {
    await client.connect();
    console.log('✅ Connected to Neon database\n');

    for (const query of VERIFICATION_QUERIES) {
      console.log(`\n[${query.id}] Running: ${query.name}...`);

      try {
        const result = await client.query(query.sql);
        console.log(`   ✅ Success - ${result.rows.length} rows returned`);

        results.push({
          query_id: query.id,
          query_name: query.name,
          success: true,
          row_count: result.rows.length,
          rows: result.rows,
          timestamp: new Date().toISOString()
        });
      } catch (error) {
        console.error(`   ❌ Error: ${error.message}`);

        results.push({
          query_id: query.id,
          query_name: query.name,
          success: false,
          error: error.message,
          timestamp: new Date().toISOString()
        });
      }
    }

  } catch (error) {
    console.error('\n❌ Connection error:', error.message);
    process.exit(1);
  } finally {
    await client.end();
  }

  return results;
}

async function appendToReport(results) {
  const reportPath = path.join(__dirname, '../analysis/FINAL_COLUMN_COMPLIANCE_REPORT.md');

  const appendContent = `

---

## 🔄 Post-Fix Verification Results

**Date**: ${new Date().toISOString()}
**Verification Script**: \`scripts/run_post_fix_verification.cjs\`

### Summary

${results.map(r => `- **${r.query_id}**: ${r.success ? `✅ ${r.row_count} rows` : `❌ ${r.error}`}`).join('\n')}

### Detailed Results

${results.map(r => `
#### ${r.query_id}: ${r.query_name}

${r.success ? `
**Status**: ✅ Success
**Rows Returned**: ${r.row_count}

\`\`\`json
${JSON.stringify(r.rows.slice(0, 10), null, 2)}
${r.rows.length > 10 ? `\n... (${r.rows.length - 10} more rows)` : ''}
\`\`\`
` : `
**Status**: ❌ Failed
**Error**: \`${r.error}\`
`}
`).join('\n')}

### Compliance Status

${(() => {
  const duplicates = results.find(r => r.query_id === 'QUERY-02');
  const companySlot = results.find(r => r.query_id === 'QUERY-04');
  const peopleMaster = results.find(r => r.query_id === 'QUERY-05');
  const shqViews = results.find(r => r.query_id === 'QUERY-06');

  return `
- **Duplicate Columns**: ${duplicates?.success && duplicates?.row_count === 0 ? '✅ None found' : '❌ Issues remain'}
- **company_slot Structure**: ${companySlot?.success ? '✅ Verified' : '❌ Not verified'}
- **people_master Naming**: ${peopleMaster?.success && peopleMaster?.rows?.some(r => r.column_name === 'people_unique_id') ? '✅ Compliant' : '⚠️ Check required'}
- **shq Views**: ${shqViews?.success && shqViews?.row_count === 2 ? '✅ Both exist' : '⚠️ Missing or incomplete'}
  `;
})()}

---
`;

  try {
    fs.appendFileSync(reportPath, appendContent, 'utf8');
    console.log(`\n✅ Results appended to ${reportPath}`);
  } catch (error) {
    console.error(`\n❌ Failed to append to report: ${error.message}`);
  }
}

// Run verification
runVerification()
  .then(async (results) => {
    console.log('\n\n=== VERIFICATION COMPLETE ===\n');

    const successCount = results.filter(r => r.success).length;
    console.log(`✅ ${successCount}/${results.length} queries succeeded`);

    await appendToReport(results);

    process.exit(successCount === results.length ? 0 : 1);
  })
  .catch(error => {
    console.error('❌ Fatal error:', error.message);
    process.exit(1);
  });

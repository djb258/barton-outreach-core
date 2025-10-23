#!/usr/bin/env node
/**
 * CTB Metadata
 * Barton ID: 03.01.05.20251023.vsal.001
 * Branch: ai
 * Altitude: 30k (HEIR - Hierarchical Execution Intelligence & Repair)
 * Purpose: Compare live Neon schema vs manifest and report drift
 * Dependencies: pg@^8.11.0, yaml@^2.3.0
 * Input: ctb/data/infra/NEON_SCHEMA_MANIFEST.yaml
 * Output: ctb/data/infra/SCHEMA_DRIFT_REPORT.md
 */

const { Client } = require('pg');
const yaml = require('yaml');
const fs = require('fs');
const path = require('path');

// Configuration
const DATABASE_URL = process.env.DATABASE_URL;
const MANIFEST_PATH = path.join(__dirname, '../../data/infra/NEON_SCHEMA_MANIFEST.yaml');
const OUTPUT_PATH = path.join(__dirname, '../../data/infra/SCHEMA_DRIFT_REPORT.md');

// Validation
if (!DATABASE_URL) {
  console.error('❌ ERROR: DATABASE_URL environment variable is required');
  process.exit(1);
}

if (!fs.existsSync(MANIFEST_PATH)) {
  console.error(`❌ ERROR: Manifest not found at ${MANIFEST_PATH}`);
  console.error('   Run introspect_neon_to_manifest.cjs first');
  process.exit(1);
}

/**
 * Main drift detection function
 */
async function detectDrift() {
  console.log('🔍 Starting schema drift detection...\n');

  // Load manifest
  const manifestContent = fs.readFileSync(MANIFEST_PATH, 'utf8');
  const manifest = yaml.parse(manifestContent);
  console.log(`✅ Loaded manifest from ${MANIFEST_PATH}`);
  console.log(`   Generated: ${manifest.generated}`);
  console.log(`   Schemas in manifest: ${manifest.schemas.length}\n`);

  // Connect to database
  const client = new Client({ connectionString: DATABASE_URL });
  await client.connect();
  console.log('✅ Connected to Neon PostgreSQL\n');

  try {
    // Initialize drift report
    const drift = {
      summary: {
        total_drifts: 0,
        schemas_with_drift: 0,
        missing_schemas: [],
        extra_schemas: [],
        table_drifts: [],
        view_drifts: [],
        function_drifts: []
      },
      details: []
    };

    // Get live schemas
    const liveSchemas = await getLiveSchemas(client);
    console.log(`📊 Live schemas: ${liveSchemas.length}\n`);

    // Compare schemas
    for (const manifestSchema of manifest.schemas) {
      const schemaName = manifestSchema.name;

      if (!liveSchemas.includes(schemaName)) {
        drift.summary.missing_schemas.push(schemaName);
        drift.summary.total_drifts++;
        drift.summary.schemas_with_drift++;
        console.log(`⚠️  Schema missing in live: ${schemaName}`);
        continue;
      }

      console.log(`🔍 Checking schema: ${schemaName}`);
      const schemaDrift = await compareSchema(client, schemaName, manifestSchema);

      if (schemaDrift.has_drift) {
        drift.summary.schemas_with_drift++;
        drift.summary.total_drifts += schemaDrift.drift_count;
        drift.details.push(schemaDrift);
      }
    }

    // Check for extra schemas in live
    for (const liveSchema of liveSchemas) {
      const inManifest = manifest.schemas.some(s => s.name === liveSchema);
      if (!inManifest) {
        drift.summary.extra_schemas.push(liveSchema);
        drift.summary.total_drifts++;
        console.log(`⚠️  Extra schema in live (not in manifest): ${liveSchema}`);
      }
    }

    await client.end();

    // Generate report
    const report = generateMarkdownReport(drift, manifest);
    fs.writeFileSync(OUTPUT_PATH, report);

    // Summary
    console.log('\n' + '='.repeat(60));
    if (drift.summary.total_drifts === 0) {
      console.log('✅ SCHEMA ALIGNMENT: PERFECT');
      console.log('   No drift detected between manifest and live database');
    } else {
      console.log('⚠️  SCHEMA DRIFT DETECTED');
      console.log(`   Total drifts: ${drift.summary.total_drifts}`);
      console.log(`   Schemas with drift: ${drift.summary.schemas_with_drift}`);
      console.log(`   Missing schemas: ${drift.summary.missing_schemas.length}`);
      console.log(`   Extra schemas: ${drift.summary.extra_schemas.length}`);
    }
    console.log('='.repeat(60));
    console.log(`📄 Report: ${OUTPUT_PATH}`);
    console.log('='.repeat(60) + '\n');

    process.exit(drift.summary.total_drifts === 0 ? 0 : 1);

  } catch (error) {
    console.error('\n❌ Error during drift detection:', error.message);
    console.error('Stack trace:', error.stack);
    await client.end();
    process.exit(1);
  }
}

/**
 * Get all live schemas
 */
async function getLiveSchemas(client) {
  const result = await client.query(`
    SELECT schema_name
    FROM information_schema.schemata
    WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast', 'pg_temp_1', 'pg_toast_temp_1')
    ORDER BY schema_name
  `);
  return result.rows.map(row => row.schema_name);
}

/**
 * Compare a single schema
 */
async function compareSchema(client, schemaName, manifestSchema) {
  const drift = {
    schema: schemaName,
    has_drift: false,
    drift_count: 0,
    tables: {
      missing: [],
      extra: [],
      mismatched: []
    },
    views: {
      missing: [],
      extra: []
    },
    functions: {
      missing: [],
      extra: []
    }
  };

  // Get live tables
  const liveTables = await getLiveTables(client, schemaName);
  const manifestTables = manifestSchema.tables.map(t => t.name);

  // Compare tables
  for (const manifestTable of manifestTables) {
    if (!liveTables.includes(manifestTable)) {
      drift.tables.missing.push(manifestTable);
      drift.drift_count++;
      drift.has_drift = true;
      console.log(`   ⚠️  Table missing: ${schemaName}.${manifestTable}`);
    }
  }

  for (const liveTable of liveTables) {
    if (!manifestTables.includes(liveTable)) {
      drift.tables.extra.push(liveTable);
      drift.drift_count++;
      drift.has_drift = true;
      console.log(`   ⚠️  Extra table: ${schemaName}.${liveTable}`);
    } else {
      // Compare columns for matching tables
      const manifestTableObj = manifestSchema.tables.find(t => t.name === liveTable);
      const columnDrift = await compareTableColumns(client, schemaName, liveTable, manifestTableObj);
      if (columnDrift.has_drift) {
        drift.tables.mismatched.push(columnDrift);
        drift.drift_count += columnDrift.drift_count;
        drift.has_drift = true;
      }
    }
  }

  // Get live views
  const liveViews = await getLiveViews(client, schemaName);
  const manifestViews = manifestSchema.views.map(v => v.name);

  // Compare views
  for (const manifestView of manifestViews) {
    if (!liveViews.includes(manifestView)) {
      drift.views.missing.push(manifestView);
      drift.drift_count++;
      drift.has_drift = true;
      console.log(`   ⚠️  View missing: ${schemaName}.${manifestView}`);
    }
  }

  for (const liveView of liveViews) {
    if (!manifestViews.includes(liveView)) {
      drift.views.extra.push(liveView);
      drift.drift_count++;
      drift.has_drift = true;
      console.log(`   ⚠️  Extra view: ${schemaName}.${liveView}`);
    }
  }

  // Get live functions
  const liveFunctions = await getLiveFunctions(client, schemaName);
  const manifestFunctions = manifestSchema.functions.map(f => f.name);

  // Compare functions
  for (const manifestFunc of manifestFunctions) {
    if (!liveFunctions.includes(manifestFunc)) {
      drift.functions.missing.push(manifestFunc);
      drift.drift_count++;
      drift.has_drift = true;
      console.log(`   ⚠️  Function missing: ${schemaName}.${manifestFunc}`);
    }
  }

  for (const liveFunc of liveFunctions) {
    if (!manifestFunctions.includes(liveFunc)) {
      drift.functions.extra.push(liveFunc);
      drift.drift_count++;
      drift.has_drift = true;
      console.log(`   ⚠️  Extra function: ${schemaName}.${liveFunc}`);
    }
  }

  if (!drift.has_drift) {
    console.log(`   ✅ Schema aligned: ${schemaName}`);
  }

  return drift;
}

/**
 * Get live tables in schema
 */
async function getLiveTables(client, schemaName) {
  const result = await client.query(`
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = $1 AND table_type = 'BASE TABLE'
  `, [schemaName]);
  return result.rows.map(row => row.table_name);
}

/**
 * Get live views in schema
 */
async function getLiveViews(client, schemaName) {
  const result = await client.query(`
    SELECT table_name
    FROM information_schema.views
    WHERE table_schema = $1
  `, [schemaName]);
  return result.rows.map(row => row.table_name);
}

/**
 * Get live functions in schema
 */
async function getLiveFunctions(client, schemaName) {
  const result = await client.query(`
    SELECT DISTINCT routine_name
    FROM information_schema.routines
    WHERE routine_schema = $1 AND routine_type = 'FUNCTION'
  `, [schemaName]);
  return result.rows.map(row => row.routine_name);
}

/**
 * Compare table columns
 */
async function compareTableColumns(client, schemaName, tableName, manifestTable) {
  const drift = {
    table: tableName,
    has_drift: false,
    drift_count: 0,
    columns: {
      missing: [],
      extra: [],
      type_mismatch: []
    }
  };

  const liveColumnsResult = await client.query(`
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_schema = $1 AND table_name = $2
  `, [schemaName, tableName]);

  const liveColumns = liveColumnsResult.rows;
  const liveColumnNames = liveColumns.map(c => c.column_name);
  const manifestColumnNames = manifestTable.columns.map(c => c.name);

  // Check for missing columns
  for (const manifestCol of manifestTable.columns) {
    if (!liveColumnNames.includes(manifestCol.name)) {
      drift.columns.missing.push(manifestCol.name);
      drift.drift_count++;
      drift.has_drift = true;
      console.log(`      ⚠️  Column missing: ${tableName}.${manifestCol.name}`);
    }
  }

  // Check for extra columns
  for (const liveCol of liveColumns) {
    if (!manifestColumnNames.includes(liveCol.column_name)) {
      drift.columns.extra.push(liveCol.column_name);
      drift.drift_count++;
      drift.has_drift = true;
      console.log(`      ⚠️  Extra column: ${tableName}.${liveCol.column_name}`);
    } else {
      // Check for type mismatches
      const manifestCol = manifestTable.columns.find(c => c.name === liveCol.column_name);
      if (manifestCol && manifestCol.type !== liveCol.data_type) {
        drift.columns.type_mismatch.push({
          column: liveCol.column_name,
          manifest_type: manifestCol.type,
          live_type: liveCol.data_type
        });
        drift.drift_count++;
        drift.has_drift = true;
        console.log(`      ⚠️  Type mismatch: ${tableName}.${liveCol.column_name} (manifest: ${manifestCol.type}, live: ${liveCol.data_type})`);
      }
    }
  }

  return drift;
}

/**
 * Generate markdown report
 */
function generateMarkdownReport(drift, manifest) {
  const timestamp = new Date().toISOString();
  const status = drift.summary.total_drifts === 0 ? '✅ No Drift Detected' : '⚠️ Drift Detected';

  let report = `# Schema Drift Report

**Generated**: ${timestamp}
**Manifest Date**: ${manifest.generated}
**Database**: ${manifest.database.name}
**Status**: ${status}

---

## Summary

| Metric | Count |
|--------|-------|
| **Total Drifts** | ${drift.summary.total_drifts} |
| **Schemas with Drift** | ${drift.summary.schemas_with_drift} |
| **Missing Schemas** | ${drift.summary.missing_schemas.length} |
| **Extra Schemas** | ${drift.summary.extra_schemas.length} |

`;

  if (drift.summary.total_drifts === 0) {
    report += `\n## ✅ Perfect Alignment\n\nAll schemas, tables, views, and functions are aligned with the manifest.\nNo action required.\n\n`;
  } else {
    report += `\n## ⚠️ Detected Drift\n\n`;

    if (drift.summary.missing_schemas.length > 0) {
      report += `### Missing Schemas\n\nThese schemas exist in the manifest but not in the live database:\n\n`;
      drift.summary.missing_schemas.forEach(schema => {
        report += `- \`${schema}\`\n`;
      });
      report += '\n';
    }

    if (drift.summary.extra_schemas.length > 0) {
      report += `### Extra Schemas\n\nThese schemas exist in the live database but not in the manifest:\n\n`;
      drift.summary.extra_schemas.forEach(schema => {
        report += `- \`${schema}\`\n`;
      });
      report += '\n';
    }

    for (const schemaDrift of drift.details) {
      report += `### Schema: \`${schemaDrift.schema}\`\n\n`;

      if (schemaDrift.tables.missing.length > 0) {
        report += `#### Missing Tables\n\n`;
        schemaDrift.tables.missing.forEach(table => {
          report += `- \`${table}\`\n`;
        });
        report += '\n';
      }

      if (schemaDrift.tables.extra.length > 0) {
        report += `#### Extra Tables\n\n`;
        schemaDrift.tables.extra.forEach(table => {
          report += `- \`${table}\`\n`;
        });
        report += '\n';
      }

      if (schemaDrift.tables.mismatched.length > 0) {
        report += `#### Mismatched Tables\n\n`;
        schemaDrift.tables.mismatched.forEach(mismatch => {
          report += `**Table**: \`${mismatch.table}\`\n\n`;
          if (mismatch.columns.missing.length > 0) {
            report += `- Missing columns: ${mismatch.columns.missing.map(c => `\`${c}\``).join(', ')}\n`;
          }
          if (mismatch.columns.extra.length > 0) {
            report += `- Extra columns: ${mismatch.columns.extra.map(c => `\`${c}\``).join(', ')}\n`;
          }
          if (mismatch.columns.type_mismatch.length > 0) {
            report += `- Type mismatches:\n`;
            mismatch.columns.type_mismatch.forEach(tm => {
              report += `  - \`${tm.column}\`: manifest=\`${tm.manifest_type}\`, live=\`${tm.live_type}\`\n`;
            });
          }
          report += '\n';
        });
      }

      if (schemaDrift.views.missing.length > 0) {
        report += `#### Missing Views\n\n`;
        schemaDrift.views.missing.forEach(view => {
          report += `- \`${view}\`\n`;
        });
        report += '\n';
      }

      if (schemaDrift.views.extra.length > 0) {
        report += `#### Extra Views\n\n`;
        schemaDrift.views.extra.forEach(view => {
          report += `- \`${view}\`\n`;
        });
        report += '\n';
      }

      if (schemaDrift.functions.missing.length > 0) {
        report += `#### Missing Functions\n\n`;
        schemaDrift.functions.missing.forEach(func => {
          report += `- \`${func}\`\n`;
        });
        report += '\n';
      }

      if (schemaDrift.functions.extra.length > 0) {
        report += `#### Extra Functions\n\n`;
        schemaDrift.functions.extra.forEach(func => {
          report += `- \`${func}\`\n`;
        });
        report += '\n';
      }
    }

    report += `\n## Recommended Actions\n\n`;
    report += `1. Review the drift items above\n`;
    report += `2. Determine if drift is expected or needs remediation\n`;
    report += `3. If remediation needed:\n`;
    report += `   - For missing items: Run migrations to create them\n`;
    report += `   - For extra items: Update manifest or remove from database\n`;
    report += `   - For mismatches: Run migrations to align types\n`;
    report += `4. Re-run introspection after remediation\n`;
    report += `5. Re-run this verification to confirm alignment\n\n`;
  }

  report += `---\n\n**Report Generated By**: verify_schema_alignment.cjs (CTB 03.01.05)\n`;
  report += `**Next Step**: ${drift.summary.total_drifts === 0 ? 'Proceed with schema mirror generation' : 'Remediate drift before proceeding'}\n`;

  return report;
}

// Run drift detection
detectDrift().catch(err => {
  console.error('❌ Fatal error:', err.message);
  process.exit(1);
});

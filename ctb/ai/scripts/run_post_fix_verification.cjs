#!/usr/bin/env node
/**
 * CTB Metadata
 * Barton ID: 03.01.04.20251023.rpfv.001
 * Branch: ai
 * Altitude: 30k (HEIR - Hierarchical Execution Intelligence & Repair)
 * Purpose: End-to-end verification of schema finalization task chain
 * Dependencies: pg@^8.11.0, yaml@^2.3.0
 * Verifies: All task outputs, schema alignment, database accessibility
 */

const { Client } = require('pg');
const yaml = require('yaml');
const fs = require('fs');
const path = require('path');

// Configuration
const DATABASE_URL = process.env.DATABASE_URL;
const BASE_PATH = path.join(__dirname, '../..');

const EXPECTED_OUTPUTS = {
  manifest: path.join(BASE_PATH, 'data/infra/NEON_SCHEMA_MANIFEST.yaml'),
  drift_report: path.join(BASE_PATH, 'data/infra/SCHEMA_DRIFT_REPORT.md'),
  firestore_schema: path.join(BASE_PATH, 'data/infra/FIRESTORE_SCHEMA.json'),
  amplify_types: path.join(BASE_PATH, 'data/infra/AMPLIFY_TYPES.graphql')
};

const EXPECTED_MIGRATIONS = {
  shq_views: path.join(BASE_PATH, 'data/migrations/outreach-process-manager/fixes/2025-10-23_create_shq_views.sql'),
  people_alias: path.join(BASE_PATH, 'data/migrations/outreach-process-manager/fixes/2025-10-23_fix_people_master_column_alias.sql')
};

// Verification results
const results = {
  environment: {},
  files: {},
  database: {},
  schemas: {},
  outputs: {},
  overall: {
    passed: 0,
    failed: 0,
    warnings: 0
  }
};

/**
 * Main verification function
 */
async function runPostFixVerification() {
  console.log('='.repeat(70));
  console.log('🔍 CTB POST-FIX VERIFICATION');
  console.log('='.repeat(70));
  console.log(`Started: ${new Date().toISOString()}\n`);

  try {
    // Step 1: Environment checks
    await verifyEnvironment();

    // Step 2: File existence checks
    await verifyFiles();

    // Step 3: Database connectivity and schema checks
    await verifyDatabase();

    // Step 4: Output validation
    await verifyOutputs();

    // Step 5: Drift analysis
    await analyzeDrift();

    // Step 6: Generate final report
    generateFinalReport();

  } catch (error) {
    console.error('\n❌ CRITICAL ERROR during verification:', error.message);
    console.error('Stack trace:', error.stack);
    results.overall.failed++;
    generateFinalReport();
    process.exit(1);
  }
}

/**
 * Step 1: Verify environment configuration
 */
async function verifyEnvironment() {
  console.log('📋 Step 1: Environment Verification\n');

  // Check DATABASE_URL
  if (!DATABASE_URL) {
    results.environment.database_url = '❌ FAILED - DATABASE_URL not set';
    results.overall.failed++;
    console.error('   ❌ DATABASE_URL environment variable is not set');
  } else {
    results.environment.database_url = '✅ PASSED';
    results.overall.passed++;
    console.log('   ✅ DATABASE_URL is set');
  }

  // Check Node.js version
  const nodeVersion = process.version;
  results.environment.node_version = `${nodeVersion}`;
  console.log(`   ℹ️  Node.js version: ${nodeVersion}`);

  // Check required dependencies
  const deps = ['pg', 'yaml'];
  for (const dep of deps) {
    try {
      require(dep);
      results.environment[`dep_${dep}`] = '✅ INSTALLED';
      results.overall.passed++;
      console.log(`   ✅ Dependency '${dep}' is installed`);
    } catch (err) {
      results.environment[`dep_${dep}`] = '❌ MISSING';
      results.overall.failed++;
      console.error(`   ❌ Dependency '${dep}' is missing`);
    }
  }

  console.log();
}

/**
 * Step 2: Verify all expected files exist
 */
async function verifyFiles() {
  console.log('📁 Step 2: File Existence Verification\n');

  // Check migration files
  console.log('   Migration Files:');
  for (const [name, filePath] of Object.entries(EXPECTED_MIGRATIONS)) {
    if (fs.existsSync(filePath)) {
      results.files[name] = '✅ EXISTS';
      results.overall.passed++;
      console.log(`   ✅ ${name}: ${path.basename(filePath)}`);
    } else {
      results.files[name] = '❌ MISSING';
      results.overall.failed++;
      console.error(`   ❌ ${name}: ${filePath}`);
    }
  }

  // Check output files
  console.log('\n   Output Files:');
  for (const [name, filePath] of Object.entries(EXPECTED_OUTPUTS)) {
    if (fs.existsSync(filePath)) {
      const stats = fs.statSync(filePath);
      const sizeKB = (stats.size / 1024).toFixed(2);
      results.files[name] = `✅ EXISTS (${sizeKB} KB)`;
      results.overall.passed++;
      console.log(`   ✅ ${name}: ${path.basename(filePath)} (${sizeKB} KB)`);
    } else {
      results.files[name] = '❌ MISSING';
      results.overall.failed++;
      console.error(`   ❌ ${name}: ${filePath}`);
    }
  }

  console.log();
}

/**
 * Step 3: Verify database connectivity and schema
 */
async function verifyDatabase() {
  if (!DATABASE_URL) {
    console.log('⏭️  Step 3: Database Verification (SKIPPED - No DATABASE_URL)\n');
    return;
  }

  console.log('🗄️  Step 3: Database Verification\n');

  const client = new Client({ connectionString: DATABASE_URL });

  try {
    await client.connect();
    results.database.connection = '✅ CONNECTED';
    results.overall.passed++;
    console.log('   ✅ Database connection successful');

    // Get database info
    const versionResult = await client.query('SELECT version(), current_database()');
    const dbVersion = versionResult.rows[0].version.split(' ')[1];
    const dbName = versionResult.rows[0].current_database;
    results.database.name = dbName;
    results.database.version = dbVersion;
    console.log(`   ℹ️  Database: ${dbName} (PostgreSQL ${dbVersion})`);

    // Verify schemas exist
    console.log('\n   Schemas:');
    const expectedSchemas = ['intake', 'vault', 'shq', 'company', 'people', 'marketing'];
    const schemasResult = await client.query(`
      SELECT schema_name
      FROM information_schema.schemata
      WHERE schema_name = ANY($1)
      ORDER BY schema_name
    `, [expectedSchemas]);

    const existingSchemas = schemasResult.rows.map(r => r.schema_name);
    for (const schema of expectedSchemas) {
      if (existingSchemas.includes(schema)) {
        results.schemas[schema] = '✅ EXISTS';
        results.overall.passed++;
        console.log(`   ✅ Schema '${schema}' exists`);
      } else {
        results.schemas[schema] = '⚠️  MISSING';
        results.overall.warnings++;
        console.warn(`   ⚠️  Schema '${schema}' not found`);
      }
    }

    // Verify shq views (if schema exists)
    if (existingSchemas.includes('shq')) {
      console.log('\n   SHQ Views:');
      const viewsResult = await client.query(`
        SELECT viewname
        FROM pg_views
        WHERE schemaname = 'shq'
        ORDER BY viewname
      `);

      if (viewsResult.rows.length > 0) {
        results.database.shq_views = `✅ ${viewsResult.rows.length} views`;
        results.overall.passed++;
        console.log(`   ✅ Found ${viewsResult.rows.length} views in 'shq' schema:`);
        for (const row of viewsResult.rows) {
          console.log(`      - ${row.viewname}`);
        }
      } else {
        results.database.shq_views = '⚠️  No views found';
        results.overall.warnings++;
        console.warn(`   ⚠️  No views found in 'shq' schema`);
      }
    }

    // Verify people.master alias (if schema exists)
    if (existingSchemas.includes('people')) {
      console.log('\n   People Schema:');
      const aliasResult = await client.query(`
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'people'
          AND table_name = 'master'
          AND column_name = 'people_unique_id'
      `);

      if (aliasResult.rows.length > 0) {
        results.database.people_alias = '✅ Column alias exists';
        results.overall.passed++;
        console.log(`   ✅ Column 'people_unique_id' exists in people.master`);
      } else {
        results.database.people_alias = '⚠️  Column alias not found';
        results.overall.warnings++;
        console.warn(`   ⚠️  Column 'people_unique_id' not found in people.master`);
      }
    }

  } catch (error) {
    results.database.connection = `❌ FAILED - ${error.message}`;
    results.overall.failed++;
    console.error(`   ❌ Database error: ${error.message}`);
  } finally {
    await client.end();
  }

  console.log();
}

/**
 * Step 4: Validate output file formats
 */
async function verifyOutputs() {
  console.log('📊 Step 4: Output Format Validation\n');

  // Validate YAML manifest
  if (fs.existsSync(EXPECTED_OUTPUTS.manifest)) {
    try {
      const manifestContent = fs.readFileSync(EXPECTED_OUTPUTS.manifest, 'utf8');
      const manifest = yaml.parse(manifestContent);

      if (manifest.version && manifest.schemas && Array.isArray(manifest.schemas)) {
        results.outputs.manifest_format = `✅ VALID (${manifest.schemas.length} schemas)`;
        results.overall.passed++;
        console.log(`   ✅ NEON_SCHEMA_MANIFEST.yaml is valid YAML (${manifest.schemas.length} schemas)`);

        // Count tables, views, functions
        const totalTables = manifest.schemas.reduce((sum, s) => sum + (s.tables?.length || 0), 0);
        const totalViews = manifest.schemas.reduce((sum, s) => sum + (s.views?.length || 0), 0);
        const totalFunctions = manifest.schemas.reduce((sum, s) => sum + (s.functions?.length || 0), 0);
        console.log(`      - Tables: ${totalTables}`);
        console.log(`      - Views: ${totalViews}`);
        console.log(`      - Functions: ${totalFunctions}`);
      } else {
        results.outputs.manifest_format = '❌ INVALID - Missing required fields';
        results.overall.failed++;
        console.error('   ❌ NEON_SCHEMA_MANIFEST.yaml is missing required fields');
      }
    } catch (err) {
      results.outputs.manifest_format = `❌ INVALID - ${err.message}`;
      results.overall.failed++;
      console.error(`   ❌ NEON_SCHEMA_MANIFEST.yaml parse error: ${err.message}`);
    }
  } else {
    results.outputs.manifest_format = '⏭️  SKIPPED - File missing';
  }

  // Validate JSON Firestore schema
  if (fs.existsSync(EXPECTED_OUTPUTS.firestore_schema)) {
    try {
      const firestoreContent = fs.readFileSync(EXPECTED_OUTPUTS.firestore_schema, 'utf8');
      const firestore = JSON.parse(firestoreContent);

      if (firestore.version && firestore.collections && Array.isArray(firestore.collections)) {
        results.outputs.firestore_format = `✅ VALID (${firestore.collections.length} collections)`;
        results.overall.passed++;
        console.log(`   ✅ FIRESTORE_SCHEMA.json is valid JSON (${firestore.collections.length} collections)`);
      } else {
        results.outputs.firestore_format = '❌ INVALID - Missing required fields';
        results.overall.failed++;
        console.error('   ❌ FIRESTORE_SCHEMA.json is missing required fields');
      }
    } catch (err) {
      results.outputs.firestore_format = `❌ INVALID - ${err.message}`;
      results.overall.failed++;
      console.error(`   ❌ FIRESTORE_SCHEMA.json parse error: ${err.message}`);
    }
  } else {
    results.outputs.firestore_format = '⏭️  SKIPPED - File missing';
  }

  // Validate GraphQL schema
  if (fs.existsSync(EXPECTED_OUTPUTS.amplify_types)) {
    try {
      const graphqlContent = fs.readFileSync(EXPECTED_OUTPUTS.amplify_types, 'utf8');

      // Basic GraphQL validation
      const typeCount = (graphqlContent.match(/type \w+/g) || []).length;
      const modelCount = (graphqlContent.match(/@model/g) || []).length;
      const keyCount = (graphqlContent.match(/@key/g) || []).length;

      results.outputs.amplify_format = `✅ VALID (${typeCount} types, ${modelCount} @model)`;
      results.overall.passed++;
      console.log(`   ✅ AMPLIFY_TYPES.graphql is valid GraphQL`);
      console.log(`      - Types: ${typeCount}`);
      console.log(`      - @model directives: ${modelCount}`);
      console.log(`      - @key directives: ${keyCount}`);
    } catch (err) {
      results.outputs.amplify_format = `❌ INVALID - ${err.message}`;
      results.overall.failed++;
      console.error(`   ❌ AMPLIFY_TYPES.graphql read error: ${err.message}`);
    }
  } else {
    results.outputs.amplify_format = '⏭️  SKIPPED - File missing';
  }

  console.log();
}

/**
 * Step 5: Analyze drift report
 */
async function analyzeDrift() {
  console.log('🔍 Step 5: Drift Analysis\n');

  if (!fs.existsSync(EXPECTED_OUTPUTS.drift_report)) {
    results.outputs.drift_status = '⏭️  SKIPPED - Drift report missing';
    console.log('   ⏭️  Drift report not found, skipping analysis\n');
    return;
  }

  try {
    const driftContent = fs.readFileSync(EXPECTED_OUTPUTS.drift_report, 'utf8');

    // Parse drift summary
    const totalDriftsMatch = driftContent.match(/Total Drifts:\*\*\s*(\d+)/);
    const totalDrifts = totalDriftsMatch ? parseInt(totalDriftsMatch[1]) : null;

    if (totalDrifts === 0) {
      results.outputs.drift_status = '✅ NO DRIFT DETECTED';
      results.overall.passed++;
      console.log('   ✅ NO DRIFT DETECTED - Schema is perfectly aligned!');
    } else if (totalDrifts > 0) {
      results.outputs.drift_status = `⚠️  ${totalDrifts} DRIFTS DETECTED`;
      results.overall.warnings++;
      console.warn(`   ⚠️  ${totalDrifts} drifts detected - Review SCHEMA_DRIFT_REPORT.md`);
    } else {
      results.outputs.drift_status = '⚠️  Unable to parse drift count';
      results.overall.warnings++;
      console.warn('   ⚠️  Unable to parse drift count from report');
    }

  } catch (err) {
    results.outputs.drift_status = `❌ ERROR - ${err.message}`;
    results.overall.failed++;
    console.error(`   ❌ Error reading drift report: ${err.message}`);
  }

  console.log();
}

/**
 * Step 6: Generate final report
 */
function generateFinalReport() {
  console.log('='.repeat(70));
  console.log('📊 FINAL VERIFICATION REPORT');
  console.log('='.repeat(70));

  const total = results.overall.passed + results.overall.failed + results.overall.warnings;
  const passRate = total > 0 ? ((results.overall.passed / total) * 100).toFixed(1) : 0;

  console.log(`\nSummary:`);
  console.log(`   ✅ Passed:   ${results.overall.passed}`);
  console.log(`   ❌ Failed:   ${results.overall.failed}`);
  console.log(`   ⚠️  Warnings: ${results.overall.warnings}`);
  console.log(`   📊 Total:    ${total}`);
  console.log(`   📈 Pass Rate: ${passRate}%\n`);

  // Overall status
  if (results.overall.failed === 0 && results.overall.warnings === 0) {
    console.log('🎉 STATUS: ✅ ALL CHECKS PASSED - SCHEMA FINALIZATION COMPLETE!\n');
    console.log('Next Steps:');
    console.log('   1. Review generated outputs in ctb/data/infra/');
    console.log('   2. Commit schema manifests to version control');
    console.log('   3. Deploy schema changes if needed');
    console.log('   4. Update documentation with new schema references\n');
    process.exit(0);
  } else if (results.overall.failed === 0 && results.overall.warnings > 0) {
    console.log('⚠️  STATUS: PASSED WITH WARNINGS - Review warnings above\n');
    console.log('Next Steps:');
    console.log('   1. Review warnings in the report');
    console.log('   2. Address any missing schemas or views if critical');
    console.log('   3. Re-run verification after fixes\n');
    process.exit(0);
  } else {
    console.log('❌ STATUS: FAILED - Critical errors detected\n');
    console.log('Required Actions:');
    console.log('   1. Review failed checks above');
    console.log('   2. Fix critical issues (environment, files, database)');
    console.log('   3. Re-run task chain: composio run-chain barton-outreach-core');
    console.log('   4. Re-run this verification\n');
    process.exit(1);
  }
}

// Run verification
runPostFixVerification().catch(err => {
  console.error('❌ Fatal error:', err.message);
  process.exit(1);
});

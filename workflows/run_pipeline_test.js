#!/usr/bin/env node
/**
 * Outreach Step 1 Pipeline Test
 * Tests the full pipeline with West Virginia batch (20251024-WV-B1)
 */

const { Client } = require('pg');
const { makeApiRequest } = require('./bootstrap_n8n.js');
const fs = require('fs');
const path = require('path');

// Load environment variables
try {
  const envPath = path.join(__dirname, '.env');
  if (fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, 'utf8');
    envContent.split('\n').forEach(line => {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith('#')) {
        const [key, ...valueParts] = trimmed.split('=');
        if (key && valueParts.length > 0) {
          const value = valueParts.join('=').trim();
          if (!process.env[key]) {
            process.env[key] = value;
          }
        }
      }
    });
  }
} catch (error) {
  // Ignore
}

const BATCH_ID = '20251024-WV-B1';

const WORKFLOWS = {
  validation: { id: 'qvKf2iqxEZrCYPoI', name: 'Validation Gatekeeper', shouldActivate: true },
  promotion: { id: 'KFLye1yXNjvXgAn1', name: 'Promotion Runner', shouldActivate: true },
  slots: { id: 'BQU4q99xBcdE0LaH', name: 'Slot Creator', shouldActivate: true },
  apify: { id: 'euSD6SOXPrqnsFxc', name: 'Apify Enrichment', shouldActivate: false },
  millionverify: { id: 'RAeFH4CStkDcDAnm', name: 'MillionVerify Checker', shouldActivate: false }
};

const DB_CONFIG = {
  host: 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
  port: 5432,
  database: 'Marketing DB',
  user: 'n8n_user',
  password: process.env.NEON_PASSWORD || 'n8n_secure_ivq5lxz3ej',
  ssl: { rejectUnauthorized: false }
};

async function checkWorkflowStatus() {
  console.log('\n📊 Step 1: Checking Workflow Status\n');

  const workflows = await makeApiRequest('/api/v1/workflows');

  console.log('| Workflow                  | ID               | Active | Target |');
  console.log('|---------------------------|------------------|--------|--------|');

  for (const [key, config] of Object.entries(WORKFLOWS)) {
    const workflow = workflows.data.find(w => w.id === config.id);
    const active = workflow?.active ? '✅ Yes' : '❌ No';
    const target = config.shouldActivate ? '✅ ON' : '❌ OFF';
    console.log(`| ${config.name.padEnd(25)} | ${config.id} | ${active.padEnd(6)} | ${target.padEnd(6)} |`);
  }
  console.log('');
}

async function setWorkflowActivation(workflowId, shouldActivate, workflowName) {
  try {
    const workflow = await makeApiRequest(`/api/v1/workflows/${workflowId}`);
    const currentlyActive = workflow.active || false;

    if (currentlyActive === shouldActivate) {
      console.log(`  ℹ️  ${workflowName}: Already ${shouldActivate ? 'active' : 'inactive'}`);
      return true;
    }

    workflow.active = shouldActivate;

    // Remove read-only fields
    delete workflow.id;
    delete workflow.versionId;
    delete workflow.meta;
    delete workflow.tags;
    delete workflow.createdAt;
    delete workflow.updatedAt;

    await makeApiRequest(`/api/v1/workflows/${workflowId}`, 'PUT', workflow);
    console.log(`  ${shouldActivate ? '✅ Activated' : '❌ Deactivated'}: ${workflowName}`);
    return true;
  } catch (error) {
    console.log(`  ⚠️  Could not ${shouldActivate ? 'activate' : 'deactivate'} ${workflowName}: ${error.message}`);
    return false;
  }
}

async function configureWorkflows() {
  console.log('🔧 Step 2: Configuring Workflows\n');

  for (const [key, config] of Object.entries(WORKFLOWS)) {
    await setWorkflowActivation(config.id, config.shouldActivate, config.name);
  }
  console.log('');
}

async function checkBatchData(client) {
  console.log('📥 Step 3: Checking Batch Data\n');

  const result = await client.query(`
    SELECT
      import_batch_id,
      COUNT(*) as total,
      COUNT(*) FILTER (WHERE validated = TRUE) as validated,
      COUNT(*) FILTER (WHERE validated = FALSE) as failed,
      COUNT(*) FILTER (WHERE validated IS NULL) as pending
    FROM intake.company_raw_intake
    WHERE import_batch_id = $1
    GROUP BY import_batch_id
  `, [BATCH_ID]);

  if (result.rows.length === 0) {
    console.log(`  ⚠️  No records found for batch '${BATCH_ID}'`);
    return { total: 0, validated: 0, failed: 0, pending: 0 };
  }

  const stats = result.rows[0];
  console.log(`  Batch ID: ${stats.import_batch_id}`);
  console.log(`  Total Records: ${stats.total}`);
  console.log(`  ✅ Validated: ${stats.validated}`);
  console.log(`  ❌ Failed: ${stats.failed}`);
  console.log(`  ⏳ Pending: ${stats.pending}\n`);

  return stats;
}

async function runValidation() {
  console.log('🔍 Step 4: Running Validation Gatekeeper\n');

  try {
    console.log('  → Triggering workflow via API...');
    const result = await makeApiRequest(`/api/v1/workflows/${WORKFLOWS.validation.id}/execute`, 'POST', {});
    console.log(`  ✅ Validation workflow triggered (Execution ID: ${result.id || 'N/A'})`);
    console.log('  ⏳ Waiting 10 seconds for validation to complete...\n');

    await new Promise(resolve => setTimeout(resolve, 10000));
    return true;
  } catch (error) {
    console.log(`  ❌ Failed to trigger validation: ${error.message}\n`);
    return false;
  }
}

async function checkPromotionResults(client) {
  console.log('🎯 Step 5: Checking Promotion Results\n');

  const result = await client.query(`
    SELECT
      COUNT(*) AS promoted,
      MIN(created_at) AS first_promo,
      MAX(created_at) AS last_promo
    FROM marketing.company_master
    WHERE import_batch_id = $1
  `, [BATCH_ID]);

  const stats = result.rows[0];
  console.log(`  Promoted Companies: ${stats.promoted}`);
  console.log(`  First Promotion: ${stats.first_promo || 'N/A'}`);
  console.log(`  Last Promotion: ${stats.last_promo || 'N/A'}\n`);

  if (stats.promoted > 0) {
    // Check for Barton IDs
    const idCheck = await client.query(`
      SELECT company_unique_id
      FROM marketing.company_master
      WHERE import_batch_id = $1
      LIMIT 5
    `, [BATCH_ID]);

    console.log('  Sample Barton IDs:');
    idCheck.rows.forEach((row, idx) => {
      console.log(`    ${idx + 1}. ${row.company_unique_id}`);
    });
    console.log('');
  }

  return stats;
}

async function checkSlotCreation(client) {
  console.log('🎰 Step 6: Checking Slot Creation\n');

  const result = await client.query(`
    SELECT COUNT(*) as slot_count
    FROM marketing.company_slots
    WHERE company_unique_id IN (
      SELECT company_unique_id
      FROM marketing.company_master
      WHERE import_batch_id = $1
    )
  `, [BATCH_ID]);

  const slotCount = result.rows[0].slot_count;
  console.log(`  Total Slots Created: ${slotCount}\n`);

  if (slotCount > 0) {
    const sampleSlots = await client.query(`
      SELECT cs.company_slot_unique_id, cs.slot_position, cm.company_name
      FROM marketing.company_slots cs
      JOIN marketing.company_master cm ON cs.company_unique_id = cm.company_unique_id
      WHERE cm.import_batch_id = $1
      LIMIT 9
    `, [BATCH_ID]);

    console.log('  Sample Slots:');
    sampleSlots.rows.forEach((row, idx) => {
      console.log(`    ${idx + 1}. ${row.company_slot_unique_id} - ${row.company_name} (Position ${row.slot_position})`);
    });
    console.log('');
  }

  return slotCount;
}

async function logToValidationLog(client, stats) {
  console.log('📝 Step 7: Logging to shq_validation_log\n');

  try {
    await client.query(`
      INSERT INTO shq_validation_log (
        workflow_id,
        workflow_name,
        execution_time,
        record_count,
        status,
        notes
      ) VALUES (
        'pipeline-test',
        'WV Batch Pipeline Test',
        NOW(),
        $1,
        'completed',
        'Batch 20251024-WV-B1: ' || $1 || ' companies validated, promoted, and slotted. Executor: n8n_test'
      )
    `, [stats.promoted || 0]);

    console.log('  ✅ Logged to shq_validation_log\n');
  } catch (error) {
    console.log(`  ⚠️  Logging failed: ${error.message}\n`);
  }
}

async function generateFinalReport(intakeStats, promotionStats, slotCount) {
  console.log('\n════════════════════════════════════════════════════════════════════════════════');
  console.log('📊 FINAL PIPELINE TEST REPORT');
  console.log('════════════════════════════════════════════════════════════════════════════════\n');

  console.log(`Batch ID: ${BATCH_ID}`);
  console.log(`Test Date: ${new Date().toISOString()}\n`);

  console.log('| Stage | Metric | Value |');
  console.log('|-------|--------|-------|');
  console.log(`| Intake | Total Companies | ${intakeStats.total} |`);
  console.log(`| Intake | Validated | ${intakeStats.validated} |`);
  console.log(`| Intake | Failed | ${intakeStats.failed} |`);
  console.log(`| Intake | Pending | ${intakeStats.pending} |`);
  console.log(`| Promotion | Companies Promoted | ${promotionStats.promoted} |`);
  console.log(`| Slots | Total Slots Created | ${slotCount} |`);
  console.log(`| Slots | Avg Slots per Company | ${(slotCount / (promotionStats.promoted || 1)).toFixed(1)} |`);

  console.log('\n════════════════════════════════════════════════════════════════════════════════');

  const pipelineStatus =
    intakeStats.validated > 0 &&
    promotionStats.promoted > 0 &&
    slotCount > 0 ? '✅ SUCCESS' : '⚠️ INCOMPLETE';

  console.log(`\nPipeline Status: ${pipelineStatus}`);
  console.log('Pipeline Flow: Validation → Promotion → Slot Creation\n');

  if (pipelineStatus === '✅ SUCCESS') {
    console.log('✅ Ready for Enrichment + Email Verification');
    console.log('\nNext Steps:');
    console.log('  1. Enable Apify Enrichment workflow');
    console.log('  2. Set APIFY_TOKEN in n8n environment');
    console.log('  3. Enable MillionVerify Checker workflow');
    console.log('  4. Monitor execution logs\n');
  } else {
    console.log('⚠️  Pipeline incomplete - review workflow executions\n');
  }
}

async function main() {
  console.log('\n════════════════════════════════════════════════════════════════════════════════');
  console.log('🚀 OUTREACH STEP 1 PIPELINE TEST');
  console.log('════════════════════════════════════════════════════════════════════════════════');

  const client = new Client(DB_CONFIG);

  try {
    await client.connect();

    // Step 1: Check workflow status
    await checkWorkflowStatus();

    // Step 2: Configure workflows
    await configureWorkflows();

    // Step 3: Check batch data
    const intakeStats = await checkBatchData(client);

    if (intakeStats.total === 0) {
      console.log('❌ No data found in batch. Pipeline test aborted.\n');
      process.exit(1);
    }

    // Step 4: Run validation
    await runValidation();

    // Re-check intake stats after validation
    const updatedIntakeStats = await checkBatchData(client);

    // Step 5: Check promotion results
    const promotionStats = await checkPromotionResults(client);

    // Step 6: Check slot creation
    const slotCount = await checkSlotCreation(client);

    // Step 7: Log to validation log
    await logToValidationLog(client, promotionStats);

    // Final report
    await generateFinalReport(updatedIntakeStats, promotionStats, slotCount);

  } catch (error) {
    console.error('\n❌ Pipeline test failed:', error.message);
    console.error('\nStack trace:', error.stack);
    process.exit(1);
  } finally {
    await client.end();
  }
}

if (require.main === module) {
  main();
}

module.exports = { main };

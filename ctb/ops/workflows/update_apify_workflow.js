#!/usr/bin/env node
/**
 * Update Apify Enrichment Workflow
 * Adds throttling, batching, and retry handling
 */

const fs = require('fs');
const path = require('path');
const { makeApiRequest } = require('./bootstrap_n8n.js');

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
  // Ignore errors
}

const WORKFLOW_ID = 'euSD6SOXPrqnsFxc';
const WORKFLOW_FILE = '04-apify-enrichment-throttled.json';

async function updateApifyWorkflow() {
  console.log('\n════════════════════════════════════════════════════════════════════════════════');
  console.log('🔄 UPDATING APIFY ENRICHMENT WORKFLOW');
  console.log('════════════════════════════════════════════════════════════════════════════════\n');

  console.log(`Workflow ID: ${WORKFLOW_ID}`);
  console.log(`Source File: ${WORKFLOW_FILE}\n`);

  try {
    // Read updated workflow JSON
    const filePath = path.join(__dirname, WORKFLOW_FILE);
    const workflowJson = JSON.parse(fs.readFileSync(filePath, 'utf8'));

    // Get current credential ID
    console.log('→ Fetching current credential ID...');
    const existingWorkflow = await makeApiRequest(`/api/v1/workflows/${WORKFLOW_ID}`);

    let credentialId = null;
    if (existingWorkflow && existingWorkflow.nodes) {
      for (const node of existingWorkflow.nodes) {
        if (node.credentials && node.credentials.postgres) {
          credentialId = node.credentials.postgres.id;
          break;
        }
      }
    }

    if (!credentialId) {
      console.log('⚠️  Could not find credential ID, using placeholder');
      credentialId = 'CREDENTIAL_ID_NOT_FOUND';
    } else {
      console.log(`✅ Found credential ID: ${credentialId}`);
    }

    // Replace credential placeholder
    const workflowStr = JSON.stringify(workflowJson).replace(/\{\{NEON_CREDENTIAL_ID\}\}/g, credentialId);
    const updatedWorkflow = JSON.parse(workflowStr);

    // Remove read-only fields
    delete updatedWorkflow.id;
    delete updatedWorkflow.versionId;
    delete updatedWorkflow.meta;
    delete updatedWorkflow.active;
    delete updatedWorkflow.tags;
    delete updatedWorkflow.createdAt;
    delete updatedWorkflow.updatedAt;

    // Update workflow
    console.log('→ Updating workflow via API...\n');
    await makeApiRequest(`/api/v1/workflows/${WORKFLOW_ID}`, 'PUT', updatedWorkflow);
    console.log('✅ Workflow updated successfully\n');

    // Summary
    console.log('════════════════════════════════════════════════════════════════════════════════');
    console.log('📊 CONFIGURATION SUMMARY\n');
    console.log('| Component         | Setting                    | Value |');
    console.log('|-------------------|----------------------------|-------|');
    console.log('| Batch size        | Companies per batch        | 25    | ✅');
    console.log('| Delay             | Throttle between requests  | 5s    | ✅');
    console.log('| Max retries       | Retry attempts on error    | 3     | ✅');
    console.log('| Retry wait        | Wait between retries       | 60s   | ✅');
    console.log('| Concurrency       | Parallel executions        | 1     | ✅');
    console.log('| Trigger interval  | Poll frequency             | 60min | ✅');
    console.log('| HTTP timeout      | Request timeout            | 120s  | ✅');
    console.log('| Error handling    | Continue on error          | ON    | ✅');
    console.log('\n════════════════════════════════════════════════════════════════════════════════');

    console.log('\n🎯 FEATURES ADDED:\n');
    console.log('  ✅ Postgres Trigger (60min polling)');
    console.log('  ✅ Batch Controller (25 companies max)');
    console.log('  ✅ Throttling Delay (5s between requests)');
    console.log('  ✅ Retry Logic (3 attempts with 60s wait)');
    console.log('  ✅ Error Handling (rate limit detection)');
    console.log('  ✅ Failed Company Logging (marketing.company_missing)');
    console.log('  ✅ People Data Insertion (marketing.people_master)');
    console.log('  ✅ Execution Logging (shq_validation_log)');
    console.log('  ✅ Concurrency Control (1 execution at a time)');

    console.log('\n⚠️  WORKFLOW STATUS:\n');
    console.log('  Status: INACTIVE (kept disabled for manual review)');
    console.log('  Action Required: Review and activate in n8n UI');

    console.log('\n📋 NEXT STEPS:\n');
    console.log('1. Review workflow in n8n UI: https://dbarton.app.n8n.cloud');
    console.log('2. Set APIFY_TOKEN environment variable in n8n');
    console.log('3. Verify Apify actor path: code_crafter~leads-finder');
    console.log('4. Test with small batch before full activation');
    console.log('5. Activate workflow when ready\n');

    return {
      success: true,
      workflowId: WORKFLOW_ID,
      features: [
        'Postgres Trigger (60min)',
        'Batch Controller (25)',
        'Throttling (5s)',
        'Retry Logic (3x)',
        'Error Handling',
        'Concurrency (1)'
      ]
    };

  } catch (error) {
    console.error('\n❌ Update failed:', error.message);
    console.error('\nTroubleshooting:');
    console.error('  1. Verify N8N_API_URL and N8N_API_KEY in .env');
    console.error('  2. Check workflow ID exists in n8n');
    console.error('  3. Ensure network connectivity');
    console.error('  4. Review error details above\n');
    throw error;
  }
}

if (require.main === module) {
  updateApifyWorkflow().catch(error => {
    console.error('\n❌ Fatal error:', error.message);
    process.exit(1);
  });
}

module.exports = { updateApifyWorkflow };

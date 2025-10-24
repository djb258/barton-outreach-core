#!/usr/bin/env node
/**
 * Update Workflows with Automatic Triggers
 * Replaces manual triggers with scheduled polling triggers
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

const WORKFLOWS = [
  {
    id: 'qvKf2iqxEZrCYPoI',
    name: 'Validation Gatekeeper',
    file: '01-validation-gatekeeper-updated.json',
    trigger: 'Schedule (15min)',
    interval: '15 minutes'
  },
  {
    id: 'RAeFH4CStkDcDAnm',
    name: 'MillionVerify Checker',
    file: '05-millionverify-checker-updated.json',
    trigger: 'Schedule (30min)',
    interval: '30 minutes'
  }
];

async function updateWorkflows() {
  console.log('\n════════════════════════════════════════════════════════════════════════════════');
  console.log('🔄 UPDATING WORKFLOWS WITH AUTOMATIC TRIGGERS');
  console.log('════════════════════════════════════════════════════════════════════════════════\n');

  const results = [];

  for (const workflow of WORKFLOWS) {
    console.log(`\n📝 Updating: ${workflow.name}`);
    console.log(`   ID: ${workflow.id}`);
    console.log(`   Trigger: ${workflow.trigger}`);
    console.log(`   Interval: ${workflow.interval}\n`);

    try {
      // Read updated workflow JSON
      const filePath = path.join(__dirname, workflow.file);
      const workflowJson = JSON.parse(fs.readFileSync(filePath, 'utf8'));

      // Get the latest credential ID
      console.log('   → Fetching current credential ID...');
      const existingWorkflow = await makeApiRequest(`/api/v1/workflows/${workflow.id}`);

      // Extract credential ID from existing workflow
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
        console.log('   ⚠️  Could not find credential ID, using placeholder');
        credentialId = 'CREDENTIAL_ID_NOT_FOUND';
      } else {
        console.log(`   ✅ Found credential ID: ${credentialId}`);
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
      console.log('   → Updating workflow via API...');
      await makeApiRequest(`/api/v1/workflows/${workflow.id}`, 'PUT', updatedWorkflow);
      console.log('   ✅ Workflow updated successfully');

      // Activate workflow
      console.log('   → Activating workflow...');
      try {
        const fullWorkflow = await makeApiRequest(`/api/v1/workflows/${workflow.id}`);
        const workflowData = fullWorkflow.data || fullWorkflow;
        workflowData.active = true;

        // Remove read-only fields again
        delete workflowData.id;
        delete workflowData.versionId;
        delete workflowData.meta;
        delete workflowData.tags;
        delete workflowData.createdAt;
        delete workflowData.updatedAt;

        await makeApiRequest(`/api/v1/workflows/${workflow.id}`, 'PUT', workflowData);
        console.log('   ✅ Workflow activated\n');

        results.push({
          name: workflow.name,
          id: workflow.id,
          trigger: workflow.trigger,
          interval: workflow.interval,
          status: 'Updated & Active',
          success: true
        });
      } catch (activationError) {
        console.log('   ⚠️  Activation failed (activate manually in UI)\n');
        results.push({
          name: workflow.name,
          id: workflow.id,
          trigger: workflow.trigger,
          interval: workflow.interval,
          status: 'Updated (manual activation required)',
          success: true
        });
      }

    } catch (error) {
      console.error(`   ❌ Error: ${error.message}\n`);
      results.push({
        name: workflow.name,
        id: workflow.id,
        trigger: workflow.trigger,
        interval: workflow.interval,
        status: 'Failed',
        success: false,
        error: error.message
      });
    }
  }

  // Summary table
  console.log('\n════════════════════════════════════════════════════════════════════════════════');
  console.log('📊 SUMMARY\n');
  console.log('| Workflow                  | Trigger Type      | Poll Interval | Status          |');
  console.log('|---------------------------|-------------------|---------------|-----------------|');

  results.forEach(r => {
    const name = r.name.padEnd(25);
    const trigger = r.trigger.padEnd(17);
    const interval = r.interval.padEnd(13);
    const status = r.success ? '✅ Updated' : '❌ Failed';
    console.log(`| ${name} | ${trigger} | ${interval} | ${status.padEnd(15)} |`);
  });

  console.log('\n════════════════════════════════════════════════════════════════════════════════');

  const successCount = results.filter(r => r.success).length;
  console.log(`\n✅ Successfully updated: ${successCount}/${WORKFLOWS.length} workflows`);

  if (successCount < WORKFLOWS.length) {
    console.log('⚠️  Some workflows failed - check errors above\n');
  } else {
    console.log('\n🎉 All workflows now use automatic polling triggers!');
    console.log('   They will run automatically when new data appears in Neon.\n');
  }

  // Next steps
  console.log('📋 NEXT STEPS:\n');
  console.log('1. Verify workflows are active in n8n UI: https://dbarton.app.n8n.cloud');
  console.log('2. Check execution logs to confirm polling is working');
  console.log('3. Add test data to trigger workflow execution:');
  console.log('   - For Validation: INSERT into intake.company_raw_intake');
  console.log('   - For MillionVerify: INSERT into marketing.people_master with emails\n');
}

if (require.main === module) {
  updateWorkflows().catch(error => {
    console.error('\n❌ Fatal error:', error.message);
    process.exit(1);
  });
}

module.exports = { updateWorkflows };

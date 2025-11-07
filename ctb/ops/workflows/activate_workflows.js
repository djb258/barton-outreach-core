#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

// Load environment
try {
  const envContent = fs.readFileSync(path.join(__dirname, '.env'), 'utf8');
  envContent.split('\n').forEach(line => {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('#')) {
      const [key, ...valueParts] = trimmed.split('=');
      if (key && valueParts.length > 0) {
        process.env[key] = valueParts.join('=').trim();
      }
    }
  });
} catch (e) {}

const N8N_API_URL = process.env.N8N_API_URL;
const N8N_API_KEY = process.env.N8N_API_KEY;

async function makeApiRequest(endpoint, method = 'GET', body = null) {
  const url = `${N8N_API_URL}${endpoint}`;
  const options = {
    method,
    headers: {
      'X-N8N-API-KEY': N8N_API_KEY,
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(url, options);
  const text = await response.text();

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${text}`);
  }

  return text ? JSON.parse(text) : null;
}

async function activateWorkflows() {
  console.log('\n🚀 Activating n8n Workflows\n');

  try {
    // Get all workflows
    const workflows = await makeApiRequest('/api/v1/workflows');
    console.log(`  Found ${workflows.data.length} workflows\n`);

    // Workflows to activate (first 3)
    const targetWorkflows = [
      'Validation Gatekeeper',
      'Promotion Engine',
      'Company Slot Creator'
    ];

    for (const workflowName of targetWorkflows) {
      const workflow = workflows.data.find(w => w.name === workflowName);

      if (!workflow) {
        console.log(`  ⚠️  Workflow not found: ${workflowName}`);
        continue;
      }

      console.log(`  📋 ${workflowName} (ID: ${workflow.id})`);

      if (workflow.active) {
        console.log(`     ✅ Already active\n`);
        continue;
      }

      // Activate workflow
      try {
        await makeApiRequest(`/api/v1/workflows/${workflow.id}/activate`, 'POST');
        console.log(`     ✅ Activated successfully\n`);
      } catch (error) {
        console.log(`     ❌ Failed to activate: ${error.message}\n`);
      }
    }

    // Show status of all workflows
    console.log('\n════════════════════════════════════════════════════════════════════════════════');
    console.log('📊 WORKFLOW STATUS');
    console.log('════════════════════════════════════════════════════════════════════════════════\n');

    const updatedWorkflows = await makeApiRequest('/api/v1/workflows');

    console.log('| Workflow | Status | Schedule |');
    console.log('|----------|--------|----------|');

    updatedWorkflows.data.forEach(w => {
      const status = w.active ? '✅ Active' : '⭕ Inactive';
      const hasSchedule = w.nodes?.some(n => n.type === 'n8n-nodes-base.scheduleTrigger');
      const schedule = hasSchedule ? '15min/30min' : 'Manual';
      console.log(`| ${w.name.padEnd(30)} | ${status.padEnd(12)} | ${schedule} |`);
    });

    console.log('\n════════════════════════════════════════════════════════════════════════════════\n');

  } catch (error) {
    console.error('❌ Error:', error.message);
    throw error;
  }
}

activateWorkflows();

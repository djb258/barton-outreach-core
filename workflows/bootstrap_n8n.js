#!/usr/bin/env node
/**
 * N8N Bootstrap Script
 * Automates the setup of n8n workflows and credentials
 *
 * Required Environment Variables:
 * - N8N_API_URL: Base URL of your n8n instance (e.g., http://localhost:5678)
 * - N8N_API_KEY: API key for authentication
 * - NEON_PASSWORD: Password for n8n_user (from N8N_CREDENTIALS.txt)
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

// Load environment variables from .env file
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
  // Ignore errors, env vars might be set elsewhere
}

// Configuration
const CONFIG = {
  n8nApiUrl: process.env.N8N_API_URL || 'http://localhost:5678',
  n8nApiKey: process.env.N8N_API_KEY,
  neonPassword: process.env.NEON_PASSWORD || 'n8n_secure_ivq5lxz3ej',  // Default from setup
  neonHost: 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
  neonDatabase: 'Marketing DB',
  neonUser: 'n8n_user'
};

// Workflow files
const WORKFLOWS = [
  { file: '01-validation-gatekeeper.json', name: 'Validation Gatekeeper' },
  { file: '02-promotion-runner.json', name: 'Promotion Runner' },
  { file: '03-slot-creator.json', name: 'Slot Creator' },
  { file: '04-apify-enrichment.json', name: 'Apify Enrichment' },
  { file: '05-millionverify-checker.json', name: 'MillionVerify Checker' }
];

// Helper: Make API request
async function makeApiRequest(endpoint, method = 'GET', body = null) {
  const url = new URL(endpoint, CONFIG.n8nApiUrl);
  const isHttps = url.protocol === 'https:';
  const httpModule = isHttps ? https : http;

  return new Promise((resolve, reject) => {
    const options = {
      hostname: url.hostname,
      port: url.port || (isHttps ? 443 : 80),
      path: url.pathname + url.search,
      method: method,
      headers: {
        'X-N8N-API-KEY': CONFIG.n8nApiKey,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    };

    const req = httpModule.request(options, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            resolve(JSON.parse(data || '{}'));
          } catch (e) {
            resolve({ statusCode: res.statusCode, data: data });
          }
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${data}`));
        }
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    if (body) {
      req.write(JSON.stringify(body));
    }

    req.end();
  });
}

// Step 1: Check API connection
async function checkApiConnection() {
  console.log('\n📡 Step 1: Checking n8n API connection...\n');

  if (!CONFIG.n8nApiKey) {
    throw new Error('N8N_API_KEY environment variable is required');
  }

  try {
    const response = await makeApiRequest('/api/v1/workflows');
    console.log(`  ✅ Connected to n8n at ${CONFIG.n8nApiUrl}`);
    console.log(`  ℹ️  Found ${response.data?.length || 0} existing workflows`);
    return true;
  } catch (error) {
    console.error(`  ❌ Connection failed: ${error.message}`);
    throw error;
  }
}

// Step 2: Create Neon database credential
async function createNeonCredential() {
  console.log('\n🔐 Step 2: Creating Neon database credential...\n');

  const credential = {
    name: 'Neon Marketing DB',
    type: 'postgres',
    data: {
      host: CONFIG.neonHost,
      port: 5432,
      database: CONFIG.neonDatabase,
      user: CONFIG.neonUser,
      password: CONFIG.neonPassword,
      ssl: 'allow',  // Neon requires SSL
      // SSH tunnel properties (disabled but required by n8n schema)
      sshAuthenticateWith: 'password',
      sshHost: '',
      sshPort: 22,
      sshUser: '',
      sshPassword: '',
      privateKey: '',
      passphrase: ''
    }
  };

  try {
    // Try to create new credential (may fail if exists)
    try {
      const response = await makeApiRequest('/api/v1/credentials', 'POST', credential);
      console.log(`  ✅ Created credential "${credential.name}" (ID: ${response.id})`);
      return response.id;
    } catch (createError) {
      // If creation fails, try to get existing credentials
      if (createError.message.includes('already exists') || createError.message.includes('duplicate')) {
        console.log(`  ℹ️  Credential "${credential.name}" already exists, attempting to retrieve...`);
        // For now, return a placeholder ID - workflows will prompt for credential selection
        console.log(`  ⚠️  Please manually select credential in n8n UI`);
        return 'MANUAL_SELECT';
      }
      throw createError;
    }
  } catch (error) {
    console.error(`  ❌ Failed to create credential: ${error.message}`);
    throw error;
  }
}

// Step 3: Import workflows
async function importWorkflows(credentialId) {
  console.log('\n📥 Step 3: Importing workflows...\n');

  const results = [];

  for (const workflow of WORKFLOWS) {
    const filePath = path.join(__dirname, workflow.file);

    try {
      // Read workflow JSON
      const workflowJson = JSON.parse(fs.readFileSync(filePath, 'utf8'));

      // Replace credential placeholder with actual ID
      const workflowStr = JSON.stringify(workflowJson).replace(/\{\{NEON_CREDENTIAL_ID\}\}/g, credentialId);
      const updatedWorkflow = JSON.parse(workflowStr);

      // Remove properties that n8n auto-generates or doesn't accept in POST/PUT
      delete updatedWorkflow.id;
      delete updatedWorkflow.versionId;
      delete updatedWorkflow.meta;
      delete updatedWorkflow.active;  // Set via PATCH after creation
      delete updatedWorkflow.tags;    // Managed separately via tags API

      // Check if workflow already exists
      const existing = await makeApiRequest('/api/v1/workflows');
      const existingWorkflow = existing.data?.find(w => w.name === workflow.name);

      let response;
      if (existingWorkflow) {
        console.log(`  ↳ Updating existing workflow "${workflow.name}"...`);
        response = await makeApiRequest(`/api/v1/workflows/${existingWorkflow.id}`, 'PUT', updatedWorkflow);
      } else {
        console.log(`  ↳ Creating workflow "${workflow.name}"...`);
        response = await makeApiRequest('/api/v1/workflows', 'POST', updatedWorkflow);
      }

      results.push({
        name: workflow.name,
        id: response.id,
        status: 'imported',
        active: response.active
      });

      console.log(`  ✅ ${workflow.name} (ID: ${response.id})`);
    } catch (error) {
      results.push({
        name: workflow.name,
        status: 'error',
        error: error.message
      });
      console.error(`  ❌ ${workflow.name}: ${error.message}`);
    }
  }

  return results;
}

// Step 4: Enable workflows
async function enableWorkflows(workflowResults) {
  console.log('\n⚡ Step 4: Enabling workflows...\n');

  for (const workflow of workflowResults) {
    if (workflow.status === 'imported' && !workflow.active) {
      try {
        // Get the full workflow
        const fullWorkflow = await makeApiRequest(`/api/v1/workflows/${workflow.id}`);

        // Update with active: true (response might be in .data or directly)
        const workflowData = fullWorkflow.data || fullWorkflow;
        workflowData.active = true;

        // Remove read-only fields
        delete workflowData.id;
        delete workflowData.versionId;
        delete workflowData.meta;
        delete workflowData.tags;
        delete workflowData.createdAt;
        delete workflowData.updatedAt;

        await makeApiRequest(`/api/v1/workflows/${workflow.id}`, 'PUT', workflowData);

        workflow.active = true;
        console.log(`  ✅ Enabled: ${workflow.name}`);
      } catch (error) {
        console.error(`  ⚠️  Could not enable ${workflow.name}: ${error.message}`);
      }
    } else if (workflow.active) {
      console.log(`  ℹ️  Already active: ${workflow.name}`);
    }
  }
}

// Main execution
async function main() {
  console.log('═'.repeat(80));
  console.log('🚀 N8N BOOTSTRAP - Outreach Automation Setup');
  console.log('═'.repeat(80));

  try {
    // Step 1: Check connection
    await checkApiConnection();

    // Step 2: Create credential
    const credentialId = await createNeonCredential();

    // Step 3: Import workflows
    const workflowResults = await importWorkflows(credentialId);

    // Step 4: Enable workflows
    await enableWorkflows(workflowResults);

    // Summary
    console.log('\n' + '═'.repeat(80));
    console.log('📊 SUMMARY\n');

    console.log('| Workflow                  | ID | Status    | Active |');
    console.log('|---------------------------|-----|-----------|--------|');

    workflowResults.forEach(w => {
      const name = w.name.padEnd(25);
      const id = (w.id || 'N/A').toString().padEnd(3);
      const status = (w.status === 'imported' ? '✅ imported' : '❌ error').padEnd(9);
      const active = w.active ? '✅' : '❌';
      console.log(`| ${name} | ${id} | ${status} | ${active}   |`);
    });

    console.log('\n═'.repeat(80));

    const successCount = workflowResults.filter(w => w.status === 'imported').length;
    const activeCount = workflowResults.filter(w => w.active).length;

    console.log(`✅ Bootstrap complete: ${successCount}/${WORKFLOWS.length} workflows imported`);
    console.log(`⚡ Active workflows: ${activeCount}/${WORKFLOWS.length}`);
    console.log(`🔗 n8n URL: ${CONFIG.n8nApiUrl}`);
    console.log('');

  } catch (error) {
    console.error('\n❌ Bootstrap failed:', error.message);
    console.error('\nTroubleshooting:');
    console.error('  1. Verify N8N_API_URL is correct');
    console.error('  2. Verify N8N_API_KEY is valid');
    console.error('  3. Ensure n8n is running');
    console.error('  4. Check network connectivity');
    console.error('');
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { main, makeApiRequest };

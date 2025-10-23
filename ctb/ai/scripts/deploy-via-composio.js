/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ai/scripts
Barton ID: 03.01.04
Unique ID: CTB-9AC5DEAE
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

/**
 * Deploy to Vercel via Composio MCP Integration
 * Using the connected Vercel account: ca_vkXglNynIxjm
 */

const composioApiKey = 'ak_t-F0AbvfZHUZSUrqAGNn';
const composioBaseUrl = 'https://backend.composio.dev';
const vercelConnectedAccountId = 'ca_vkXglNynIxjm';

async function deployToVercelViaComposio() {
  console.log('🚀 DEPLOYING TO VERCEL VIA COMPOSIO');
  console.log('═'.repeat(50));

  // Step 1: Test if we can list Vercel projects
  console.log('\n📋 Step 1: Testing Vercel connection...');

  try {
    // Try different Vercel endpoints through Composio
    const testEndpoints = [
      '/api/v3/tools/execute',
      '/api/v3/actions/execute',
      '/api/v3/tools/vercel_list_projects/execute',
      '/api/v3/apps/vercel/actions/execute'
    ];

    for (const endpoint of testEndpoints) {
      console.log(`\n🔧 Testing endpoint: ${endpoint}`);

      const testPayloads = [
        {
          tool_slug: 'vercel_list_projects',
          connected_account_id: vercelConnectedAccountId,
          input: {}
        },
        {
          app_name: 'vercel',
          action_name: 'list_projects',
          connected_account_id: vercelConnectedAccountId,
          input: {}
        },
        {
          connected_account_id: vercelConnectedAccountId,
          input: {}
        }
      ];

      for (const payload of testPayloads) {
        try {
          const response = await fetch(`${composioBaseUrl}${endpoint}`, {
            method: 'POST',
            headers: {
              'x-api-key': composioApiKey,
              'Authorization': `Bearer ${composioApiKey}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
          });

          console.log(`📤 Status: ${response.status}`);

          if (response.ok) {
            const result = await response.json();
            console.log(`✅ SUCCESS! Vercel connection works`);
            console.log(`📊 Response:`, JSON.stringify(result, null, 2));

            // If we can list projects, try creating/deploying
            return await createVercelProject(endpoint, payload);
          } else if (response.status !== 404) {
            const responseText = await response.text();
            console.log(`📥 Response: ${responseText.substring(0, 200)}...`);
          }
        } catch (error) {
          console.log(`❌ Error: ${error.message}`);
        }
      }
    }

    console.log('\n⚠️ Direct Vercel integration not working through Composio action execution');
    console.log('Falling back to manual deployment instructions...');

  } catch (error) {
    console.error('❌ Deployment error:', error);
  }
}

async function createVercelProject(workingEndpoint, workingPayload) {
  console.log('\n🏗️ Step 2: Creating Vercel project...');

  // Try to create a new project
  const createPayload = {
    ...workingPayload,
    tool_slug: 'vercel_create_project',
    input: {
      name: 'outreach-process-manager',
      gitRepository: {
        repo: 'djb258/barton-outreach-core',
        branch: 'ui'
      },
      framework: 'vite',
      buildCommand: 'cd apps/outreach-ui && npm install && npm run build',
      outputDirectory: 'apps/outreach-ui/dist',
      installCommand: 'cd apps/outreach-ui && npm install'
    }
  };

  try {
    const response = await fetch(`${composioBaseUrl}${workingEndpoint}`, {
      method: 'POST',
      headers: {
        'x-api-key': composioApiKey,
        'Authorization': `Bearer ${composioApiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(createPayload)
    });

    console.log(`📤 Create project status: ${response.status}`);

    if (response.ok) {
      const result = await response.json();
      console.log(`✅ PROJECT CREATED!`);
      console.log(`📊 Project details:`, JSON.stringify(result, null, 2));

      // Set environment variables
      return await setEnvironmentVariables(workingEndpoint, result.project_id || result.id);
    } else {
      const responseText = await response.text();
      console.log(`📥 Create response: ${responseText}`);
    }
  } catch (error) {
    console.log(`❌ Create project error: ${error.message}`);
  }

  return null;
}

async function setEnvironmentVariables(workingEndpoint, projectId) {
  console.log('\n🔐 Step 3: Setting environment variables...');

  const envVars = {
    COMPOSIO_API_KEY: 'ak_t-F0AbvfZHUZSUrqAGNn',
    COMPOSIO_BASE_URL: 'https://backend.composio.dev',
    NEON_DATABASE_URL: 'postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/Marketing%20DB?sslmode=require&channel_binding=require',
    DOCTRINE_HASH: 'STAMPED_v2.1.0',
    NODE_ENV: 'production',
    VITE_API_URL: 'https://outreach-process-manager.vercel.app'
  };

  const envPayload = {
    tool_slug: 'vercel_set_env_vars',
    connected_account_id: vercelConnectedAccountId,
    input: {
      project_id: projectId,
      environment_variables: envVars
    }
  };

  try {
    const response = await fetch(`${composioBaseUrl}${workingEndpoint}`, {
      method: 'POST',
      headers: {
        'x-api-key': composioApiKey,
        'Authorization': `Bearer ${composioApiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(envPayload)
    });

    console.log(`📤 Set env vars status: ${response.status}`);

    if (response.ok) {
      const result = await response.json();
      console.log(`✅ ENVIRONMENT VARIABLES SET!`);
      console.log(`🎉 DEPLOYMENT COMPLETE!`);

      return {
        success: true,
        project_url: `https://outreach-process-manager.vercel.app`,
        project_id: projectId
      };
    } else {
      const responseText = await response.text();
      console.log(`📥 Env vars response: ${responseText}`);
    }
  } catch (error) {
    console.log(`❌ Env vars error: ${error.message}`);
  }

  return null;
}

// Fallback: Provide manual deployment instructions
function provideManualInstructions() {
  console.log('\n📋 MANUAL DEPLOYMENT INSTRUCTIONS');
  console.log('═'.repeat(40));
  console.log('Since Composio action execution needs configuration, here\'s the manual process:');
  console.log('');
  console.log('1. 👉 Visit: https://vercel.com/new/git/external?repository-url=https://github.com/djb258/barton-outreach-core&branch=ui&project-name=outreach-process-manager');
  console.log('');
  console.log('2. ⚙️ Build Settings:');
  console.log('   Framework: Vite');
  console.log('   Build Command: cd apps/outreach-ui && npm install && npm run build');
  console.log('   Output Directory: apps/outreach-ui/dist');
  console.log('   Install Command: cd apps/outreach-ui && npm install');
  console.log('');
  console.log('3. 🔐 Environment Variables:');
  console.log('   COMPOSIO_API_KEY=ak_t-F0AbvfZHUZSUrqAGNn');
  console.log('   COMPOSIO_BASE_URL=https://backend.composio.dev');
  console.log('   NEON_DATABASE_URL=postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/Marketing%20DB?sslmode=require&channel_binding=require');
  console.log('   DOCTRINE_HASH=STAMPED_v2.1.0');
  console.log('   NODE_ENV=production');
  console.log('   VITE_API_URL=https://outreach-process-manager.vercel.app');
  console.log('');
  console.log('4. 🚀 Deploy and the app will be live at: https://outreach-process-manager.vercel.app');
}

// Run deployment
deployToVercelViaComposio().then(() => {
  provideManualInstructions();
}).catch(error => {
  console.error('Deployment failed:', error);
  provideManualInstructions();
});
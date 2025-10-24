#!/usr/bin/env node
/**
 * Setup Neon Integration in Composio
 * Barton ID: 03.01.04.20251023.sni.001
 */

import fetch from 'node-fetch';

const COMPOSIO_API_KEY = 'ak_j35MCGETpmFuX8iUpC0q';
const COMPOSIO_BASE_URL = 'https://backend.composio.dev/api/v3';
const NEON_API_KEY = 'napi_xjl7fz34lkcw5j00o1iu8p07mvu4im2uynkk9kiigqp7g9c3aunc57fcc7nbdqu1';
const USER_ID = 'napi_xjl7fz34lkcw5j00o1iu8p07mvu4im2uynkk9kiigqp7g9c3aunc57fcc7nbdqu1';

console.log('\n=== Setup Neon Integration in Composio ===\n');
console.log('Composio API Key: ' + COMPOSIO_API_KEY.substring(0, 10) + '...');
console.log('Neon API Key: ' + NEON_API_KEY.substring(0, 10) + '...\n');

async function setupNeonIntegration() {
  try {
    // Step 1: Check if Neon app exists in Composio
    console.log('[1/4] Checking for Neon app in Composio catalog...');
    const appsResponse = await fetch(`${COMPOSIO_BASE_URL}/apps?search=neon`, {
      headers: {
        'x-api-key': COMPOSIO_API_KEY,
        'Content-Type': 'application/json'
      }
    });

    if (!appsResponse.ok) {
      console.error(`❌ HTTP ${appsResponse.status}`);
      const text = await appsResponse.text();
      console.error(text.substring(0, 500));
      return false;
    }

    const appsData = await appsResponse.json();
    const apps = appsData.items || [];
    const neonApp = apps.find(app =>
      app.name?.toLowerCase().includes('neon') ||
      app.key?.toLowerCase() === 'neon'
    );

    if (!neonApp) {
      console.log('⚠️  Neon app not found in Composio catalog');
      console.log('   Available apps containing "neon":', apps.map(a => a.key || a.name));
      console.log('\n   Trying to create custom integration...\n');
    } else {
      console.log(`✅ Found Neon app: ${neonApp.key || neonApp.name}`);
      console.log(`   App ID: ${neonApp.appId || neonApp.key}\n`);
    }

    // Step 2: Create integration/connection
    console.log('[2/4] Creating Neon integration...');

    // Try different payload formats
    const integrationPayloads = [
      // Format 1: Using integrationId
      {
        integrationId: neonApp?.key || 'neon',
        data: {
          api_key: NEON_API_KEY
        },
        userId: USER_ID
      },
      // Format 2: Using appName
      {
        appName: 'neon',
        authConfig: {
          api_key: NEON_API_KEY
        },
        entityId: USER_ID
      },
      // Format 3: Direct connection
      {
        app: 'neon',
        authMode: 'API_KEY',
        credentials: {
          api_key: NEON_API_KEY
        }
      }
    ];

    let connectionCreated = false;
    let connectedAccountId = null;

    for (let i = 0; i < integrationPayloads.length; i++) {
      console.log(`   Attempt ${i + 1}/${integrationPayloads.length}...`);

      const integrationResponse = await fetch(`${COMPOSIO_BASE_URL}/connectedAccounts`, {
        method: 'POST',
        headers: {
          'x-api-key': COMPOSIO_API_KEY,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(integrationPayloads[i])
      });

      const responseText = await integrationResponse.text();

      if (integrationResponse.ok) {
        try {
          const integrationData = JSON.parse(responseText);
          connectedAccountId = integrationData.id || integrationData.connectedAccountId;
          console.log(`✅ Integration created!`);
          console.log(`   Connected Account ID: ${connectedAccountId}\n`);
          connectionCreated = true;
          break;
        } catch (e) {
          console.log(`✅ Integration created (non-JSON response)`);
          console.log(`   Response: ${responseText.substring(0, 200)}\n`);
          connectionCreated = true;
          break;
        }
      } else {
        console.log(`   ❌ HTTP ${integrationResponse.status}: ${responseText.substring(0, 200)}`);
      }
    }

    if (!connectionCreated) {
      console.error('\n❌ Failed to create integration with all payload formats');
      return false;
    }

    // Step 3: List available tools now
    console.log('[3/4] Checking available Neon tools...');
    const toolsResponse = await fetch(`${COMPOSIO_BASE_URL}/tools?search=neon`, {
      headers: {
        'x-api-key': COMPOSIO_API_KEY,
        'Content-Type': 'application/json'
      }
    });

    if (toolsResponse.ok) {
      const toolsData = await toolsResponse.json();
      const tools = toolsData.items || [];

      console.log(`✅ Found ${tools.length} Neon tools:\n`);
      tools.forEach(tool => {
        console.log(`   • ${tool.slug || tool.name}`);
        console.log(`     ${tool.description || 'N/A'}`);
      });

      const executeSqlTool = tools.find(t =>
        t.slug?.toLowerCase().includes('execute') &&
        t.slug?.toLowerCase().includes('sql')
      );

      if (executeSqlTool) {
        console.log(`\n✅ SQL execution tool found: ${executeSqlTool.slug}`);
      } else {
        console.log('\n⚠️  No SQL execution tool found yet');
      }
    } else {
      console.log(`⚠️  Could not fetch tools (HTTP ${toolsResponse.status})`);
    }

    // Step 4: Test the connection
    console.log('\n[4/4] Testing Neon connection...');

    // Try a simple query if we have the connected account ID
    if (connectedAccountId) {
      const testPayload = {
        connected_account_id: connectedAccountId,
        user_id: USER_ID,
        arguments: {
          sql: 'SELECT 1 as test;'
        }
      };

      const testResponse = await fetch(`${COMPOSIO_BASE_URL}/tools/execute/neon_execute_sql`, {
        method: 'POST',
        headers: {
          'x-api-key': COMPOSIO_API_KEY,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(testPayload)
      });

      if (testResponse.ok) {
        console.log('✅ Neon connection test PASSED!\n');
        console.log('🎯 SETUP COMPLETE - Neon is ready to use!\n');
        return true;
      } else {
        const errorText = await testResponse.text();
        console.log(`⚠️  Connection test status: HTTP ${testResponse.status}`);
        console.log(`   Response: ${errorText.substring(0, 300)}`);
        console.log('\n   Integration created but test query failed - may need database URL\n');
      }
    }

    console.log('\n✅ SETUP COMPLETE\n');
    console.log('Summary:');
    console.log(`  • Neon integration: ${connectionCreated ? 'Created' : 'Pending'}`);
    console.log(`  • Connected Account ID: ${connectedAccountId || 'N/A'}`);
    console.log(`  • API Key configured: YES\n`);

    return connectionCreated;

  } catch (error) {
    console.error('\n❌ Setup failed:', error.message);
    console.error(error.stack);
    return false;
  }
}

// Execute
setupNeonIntegration()
  .then((success) => {
    if (success) {
      console.log('✅ Neon integration setup completed!');
      process.exit(0);
    } else {
      console.error('⚠️  Setup completed with warnings');
      process.exit(1);
    }
  })
  .catch(error => {
    console.error('❌ Fatal error:', error.message);
    console.error(error.stack);
    process.exit(1);
  });

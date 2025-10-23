/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ai/testing
Barton ID: 03.01.03
Unique ID: CTB-8C3C83B0
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: HEIR
─────────────────────────────────────────────
*/

/**
 * Test Composio API v3 endpoints and connected accounts
 * Based on documentation showing /api/v3/ pattern
 */

const composioApiKey = 'ak_t-F0AbvfZHUZSUrqAGNn';
const composioBaseUrl = 'https://backend.composio.dev';

async function testV3Endpoints() {
  console.log('🔍 TESTING COMPOSIO API V3 ENDPOINTS');
  console.log('═'.repeat(50));

  // Test v3 connected accounts endpoint from docs
  console.log('\n📋 Testing Connected Accounts (v3)...');
  try {
    const response = await fetch(`${composioBaseUrl}/api/v3/connected_accounts`, {
      headers: {
        'x-api-key': composioApiKey,
        'Authorization': `Bearer ${composioApiKey}`
      }
    });

    console.log(`📤 Connected Accounts: ${response.status}`);

    if (response.ok) {
      const data = await response.json();
      console.log(`✅ SUCCESS: ${JSON.stringify(data, null, 2)}`);
    } else {
      const errorText = await response.text();
      console.log(`❌ Error: ${errorText.substring(0, 200)}...`);
    }
  } catch (error) {
    console.log(`❌ Network Error: ${error.message}`);
  }

  // Test v3 actions endpoint patterns
  console.log('\n⚡ Testing V3 Actions Endpoints...');

  const v3ActionEndpoints = [
    '/api/v3/actions/execute',
    '/api/v3/tools/execute',
    '/api/v3/actions',
    '/api/v3/tools'
  ];

  for (const endpoint of v3ActionEndpoints) {
    try {
      // First try GET to see if endpoint exists
      const getResponse = await fetch(`${composioBaseUrl}${endpoint}`, {
        headers: {
          'x-api-key': composioApiKey,
          'Authorization': `Bearer ${composioApiKey}`
        }
      });

      console.log(`📤 GET ${endpoint}: ${getResponse.status}`);

      if (getResponse.status !== 404) {
        console.log(`✅ ENDPOINT EXISTS: ${endpoint}`);

        if (getResponse.ok) {
          const data = await getResponse.json();
          if (Array.isArray(data)) {
            console.log(`📊 Found ${data.length} items`);
          } else {
            console.log(`📄 Data keys: ${Object.keys(data).join(', ')}`);
          }
        }
      }

      // Also try POST for execute endpoints
      if (endpoint.includes('execute')) {
        const postResponse = await fetch(`${composioBaseUrl}${endpoint}`, {
          method: 'POST',
          headers: {
            'x-api-key': composioApiKey,
            'Authorization': `Bearer ${composioApiKey}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            tool_slug: 'neon',
            action: 'LIST_DATABASES',
            input: {}
          })
        });

        console.log(`📤 POST ${endpoint}: ${postResponse.status}`);

        if (postResponse.status !== 404) {
          const responseText = await postResponse.text();
          console.log(`📥 POST Response: ${responseText.substring(0, 150)}...`);
        }
      }
    } catch (error) {
      console.log(`❌ Error testing ${endpoint}: ${error.message}`);
    }
  }

  // Test specific app actions endpoints
  console.log('\n🎯 Testing App-Specific V3 Endpoints...');

  const appEndpoints = [
    '/api/v3/apps/neon/actions',
    '/api/v3/apps/neon/execute',
    '/api/v3/integrations/neon/execute'
  ];

  for (const endpoint of appEndpoints) {
    try {
      const response = await fetch(`${composioBaseUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'x-api-key': composioApiKey,
          'Authorization': `Bearer ${composioApiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          action: 'LIST_DATABASES',
          input: {},
          connected_account_id: 'default'
        })
      });

      console.log(`📤 ${endpoint}: ${response.status}`);

      if (response.status !== 404) {
        const responseText = await response.text();
        console.log(`📥 Response: ${responseText.substring(0, 150)}...`);

        if (response.status === 200 || response.status === 400 || response.status === 401) {
          console.log(`✅ WORKING ENDPOINT: ${endpoint}`);
        }
      }
    } catch (error) {
      console.log(`❌ Error: ${error.message}`);
    }
  }
}

// Test if we need to create connected accounts first
async function testCreateConnectedAccount() {
  console.log('\n🔗 TESTING CONNECTED ACCOUNT CREATION');
  console.log('═'.repeat(40));

  try {
    const response = await fetch(`${composioBaseUrl}/api/v3/connected_accounts`, {
      method: 'POST',
      headers: {
        'x-api-key': composioApiKey,
        'Authorization': `Bearer ${composioApiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        toolkit_slug: 'neon',
        entity_id: 'test-user',
        auth_config: {
          api_key: 'test'
        }
      })
    });

    console.log(`📤 Create Connected Account: ${response.status}`);
    const responseText = await response.text();
    console.log(`📥 Response: ${responseText}`);

    if (response.ok) {
      console.log(`✅ Connected account created successfully!`);
    } else {
      console.log(`⚠️ Could not create connected account: ${responseText}`);
    }
  } catch (error) {
    console.log(`❌ Error creating connected account: ${error.message}`);
  }
}

// Main execution
async function main() {
  try {
    await testV3Endpoints();
    await testCreateConnectedAccount();

    console.log('\n🎯 V3 API TESTING COMPLETE');
    return { success: true };
  } catch (error) {
    console.error('❌ Test error:', error);
    return { success: false, error: error.message };
  }
}

main().catch(console.error);
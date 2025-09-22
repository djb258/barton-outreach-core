/**
 * Test correct Composio API endpoints
 * Find the working API structure for MCP integration
 */

async function testComposioEndpoints() {
  const composioApiKey = 'ak_t-F0AbvfZHUZSUrqAGNn';
  const composioBaseUrl = 'https://backend.composio.dev';

  console.log('🔍 TESTING COMPOSIO API ENDPOINTS');
  console.log('═'.repeat(50));

  // Test different endpoint structures
  const endpoints = [
    '/api/v1/apps',
    '/v1/apps',
    '/apps',
    '/api/apps',
    '/api/v1/integrations',
    '/v1/integrations',
    '/api/v1/actions',
    '/v1/actions',
    '/api/v1/actions/execute',
    '/v1/execute',
    '/execute',
    '/api/execute'
  ];

  const results = {};

  for (const endpoint of endpoints) {
    console.log(`\n📡 Testing: ${composioBaseUrl}${endpoint}`);

    try {
      const response = await fetch(`${composioBaseUrl}${endpoint}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${composioApiKey}`,
          'X-API-Key': composioApiKey,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log(`✅ SUCCESS: ${response.status} - ${typeof data} returned`);

        if (Array.isArray(data)) {
          console.log(`📊 Array with ${data.length} items`);
          if (data.length > 0) {
            console.log(`📋 First item: ${JSON.stringify(data[0]).substring(0, 100)}...`);
          }
        } else if (typeof data === 'object') {
          console.log(`📄 Object keys: ${Object.keys(data).join(', ')}`);
        }

        results[endpoint] = {
          status: response.status,
          success: true,
          data_type: Array.isArray(data) ? 'array' : typeof data,
          data_preview: Array.isArray(data) ? `${data.length} items` : Object.keys(data).join(', ')
        };
      } else {
        const errorText = await response.text();
        console.log(`❌ FAILED: ${response.status} - ${errorText.substring(0, 100)}...`);

        results[endpoint] = {
          status: response.status,
          success: false,
          error: errorText.substring(0, 200)
        };
      }
    } catch (error) {
      console.log(`❌ ERROR: ${error.message}`);
      results[endpoint] = {
        success: false,
        error: error.message
      };
    }
  }

  // Summary
  console.log('\n' + '═'.repeat(50));
  console.log('📊 ENDPOINT TEST SUMMARY');
  console.log('═'.repeat(50));

  const workingEndpoints = Object.entries(results).filter(([_, result]) => result.success);
  const failedEndpoints = Object.entries(results).filter(([_, result]) => !result.success);

  console.log(`✅ Working endpoints: ${workingEndpoints.length}`);
  console.log(`❌ Failed endpoints: ${failedEndpoints.length}`);

  workingEndpoints.forEach(([endpoint, result]) => {
    console.log(`  ✅ ${endpoint} (${result.status}) - ${result.data_preview}`);
  });

  if (workingEndpoints.length > 0) {
    console.log('\n🎯 RECOMMENDED FOR MCP INTEGRATION:');

    // Look for apps endpoint
    const appsEndpoint = workingEndpoints.find(([endpoint, _]) =>
      endpoint.includes('apps') || endpoint.includes('integrations')
    );

    if (appsEndpoint) {
      console.log(`📱 Apps/Integrations: ${appsEndpoint[0]}`);
    }

    // Look for actions endpoint
    const actionsEndpoint = workingEndpoints.find(([endpoint, _]) =>
      endpoint.includes('actions') || endpoint.includes('execute')
    );

    if (actionsEndpoint) {
      console.log(`⚡ Actions/Execute: ${actionsEndpoint[0]}`);
    }
  } else {
    console.log('\n❌ NO WORKING ENDPOINTS FOUND');
    console.log('Possible issues:');
    console.log('  - API key invalid or expired');
    console.log('  - Composio service unavailable');
    console.log('  - Different API base URL required');
  }

  return {
    total_tested: endpoints.length,
    working: workingEndpoints.length,
    failed: failedEndpoints.length,
    working_endpoints: workingEndpoints.map(([endpoint, result]) => ({
      endpoint,
      status: result.status,
      data_type: result.data_type
    })),
    recommendations: {
      apps_endpoint: workingEndpoints.find(([endpoint, _]) =>
        endpoint.includes('apps'))?.[0] || null,
      actions_endpoint: workingEndpoints.find(([endpoint, _]) =>
        endpoint.includes('actions'))?.[0] || null
    }
  };
}

// Test specific Composio action execution endpoints
async function testActionExecution() {
  const composioApiKey = 'ak_t-F0AbvfZHUZSUrqAGNn';
  const composioBaseUrl = 'https://backend.composio.dev';

  console.log('\n🔍 TESTING ACTION EXECUTION ENDPOINTS');
  console.log('═'.repeat(50));

  const actionEndpoints = [
    '/api/v1/actions/execute',
    '/v1/actions/execute',
    '/api/v1/execute',
    '/v1/execute',
    '/execute',
    '/api/actions/neon/execute',
    '/api/v1/apps/neon/actions/execute',
    '/v1/apps/neon/execute'
  ];

  const testPayload = {
    app: 'neon',
    action: 'QUERY',
    params: {
      sql: 'SELECT 1',
      database_id: 'test'
    }
  };

  for (const endpoint of actionEndpoints) {
    console.log(`\n⚡ Testing action: ${composioBaseUrl}${endpoint}`);

    try {
      const response = await fetch(`${composioBaseUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${composioApiKey}`,
          'X-API-Key': composioApiKey,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(testPayload)
      });

      const responseText = await response.text();
      console.log(`📤 Status: ${response.status}`);
      console.log(`📥 Response: ${responseText.substring(0, 200)}...`);

      if (response.status !== 404) {
        console.log(`✅ Endpoint exists (non-404 response)`);
      }

    } catch (error) {
      console.log(`❌ Error: ${error.message}`);
    }
  }
}

// Main execution
async function main() {
  try {
    const endpointResults = await testComposioEndpoints();
    await testActionExecution();

    console.log('\n[FINAL RESULTS]');
    console.log(JSON.stringify(endpointResults, null, 2));

    return endpointResults;
  } catch (error) {
    console.error('Test suite error:', error);
    return { error: error.message };
  }
}

// Run tests
main().then(results => {
  if (results.working > 0) {
    console.log('\n🎉 SUCCESS: Found working Composio endpoints!');
    process.exit(0);
  } else {
    console.log('\n❌ FAILED: No working endpoints found');
    process.exit(1);
  }
}).catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});

export default main;
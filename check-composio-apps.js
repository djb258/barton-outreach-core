/**
 * Check Composio Apps Structure and Find Action Execution Pattern
 */

const composioApiKey = 'ak_t-F0AbvfZHUZSUrqAGNn';
const composioBaseUrl = 'https://backend.composio.dev';

async function checkAppsStructure() {
  console.log('🔍 ANALYZING COMPOSIO APPS STRUCTURE');
  console.log('═'.repeat(50));

  try {
    // Get apps list
    const appsResponse = await fetch(`${composioBaseUrl}/api/v1/apps`, {
      headers: {
        'Authorization': `Bearer ${composioApiKey}`,
        'X-API-Key': composioApiKey
      }
    });

    const appsData = await appsResponse.json();
    console.log(`📱 Found ${appsData.items.length} total apps`);

    // Look for key apps we need
    const targetApps = ['neon', 'apify', 'github', 'vercel'];
    const foundApps = {};

    targetApps.forEach(target => {
      const app = appsData.items.find(item =>
        item.key.toLowerCase().includes(target) ||
        item.name.toLowerCase().includes(target)
      );
      if (app) {
        foundApps[target] = app;
        console.log(`✅ Found ${target}: ${app.key} (${app.name})`);
      } else {
        console.log(`❌ Missing ${target}`);
      }
    });

    // Check integrations endpoint for action structure
    console.log('\n🔍 CHECKING INTEGRATIONS FOR ACTION PATTERNS');
    const integrationsResponse = await fetch(`${composioBaseUrl}/api/v1/integrations`, {
      headers: {
        'Authorization': `Bearer ${composioApiKey}`,
        'X-API-Key': composioApiKey
      }
    });

    const integrationsData = await integrationsResponse.json();
    console.log(`🔗 Found ${integrationsData.items.length} integrations`);

    // Look for active integrations
    const activeIntegrations = integrationsData.items.filter(integration =>
      integration.status === 'active' || integration.status === 'ACTIVE'
    );
    console.log(`⚡ Active integrations: ${activeIntegrations.length}`);

    if (activeIntegrations.length > 0) {
      console.log('\n📋 Active Integrations:');
      activeIntegrations.slice(0, 5).forEach(integration => {
        console.log(`  - ${integration.appKey || integration.app_key}: ${integration.status}`);
      });
    }

    // Try different action execution patterns based on found apps
    console.log('\n🎯 TESTING ACTION EXECUTION PATTERNS');

    const actionPatterns = [
      '/api/v1/actions/{app}/execute',
      '/api/v1/integrations/{id}/execute',
      '/api/v1/connectedAccounts/{id}/execute',
      '/api/v1/apps/{app}/execute',
      '/api/v1/execute/{app}',
      '/api/v1/actions/execute'
    ];

    for (const pattern of actionPatterns) {
      console.log(`\n⚡ Testing pattern: ${pattern}`);

      // Try with neon if we found it
      if (foundApps.neon) {
        const testUrl = pattern.replace('{app}', foundApps.neon.key).replace('{id}', 'test');
        const testEndpoint = `${composioBaseUrl}${testUrl}`;

        try {
          const testResponse = await fetch(testEndpoint, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${composioApiKey}`,
              'X-API-Key': composioApiKey,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              action: 'LIST_TABLES',
              params: { database_id: 'test' }
            })
          });

          console.log(`📤 ${testEndpoint}: ${testResponse.status}`);
          if (testResponse.status !== 404) {
            const responseText = await testResponse.text();
            console.log(`📥 Response: ${responseText.substring(0, 200)}...`);

            if (testResponse.status === 200 || testResponse.status === 400 || testResponse.status === 401) {
              console.log(`✅ FOUND WORKING PATTERN: ${pattern}`);
            }
          }
        } catch (error) {
          console.log(`❌ Error testing ${pattern}: ${error.message}`);
        }
      }
    }

    return {
      total_apps: appsData.items.length,
      found_apps: foundApps,
      total_integrations: integrationsData.items.length,
      active_integrations: activeIntegrations.length,
      sample_apps: appsData.items.slice(0, 10).map(app => ({ key: app.key, name: app.name }))
    };

  } catch (error) {
    console.error('❌ Error checking Composio structure:', error);
    return { error: error.message };
  }
}

// Run the check
checkAppsStructure().then(result => {
  console.log('\n[COMPOSIO STRUCTURE ANALYSIS]');
  console.log(JSON.stringify(result, null, 2));
}).catch(console.error);
/**
 * Test working Composio action execution using v3/tools and connected accounts
 * Found: /api/v3/tools works, connected accounts exist
 */

const composioApiKey = 'ak_t-F0AbvfZHUZSUrqAGNn';
const composioBaseUrl = 'https://backend.composio.dev';

// Connected account IDs from previous test
const connectedAccounts = {
  vercel: 'ca_vkXglNynIxjm',
  apify: 'ca_yGfXDKPv3hz6',
  // Note: No Neon account found, we'll need to create one
};

async function listAvailableTools() {
  console.log('📋 LISTING AVAILABLE TOOLS FROM V3 ENDPOINT');
  console.log('═'.repeat(50));

  try {
    const response = await fetch(`${composioBaseUrl}/api/v3/tools`, {
      headers: {
        'x-api-key': composioApiKey,
        'Authorization': `Bearer ${composioApiKey}`
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${await response.text()}`);
    }

    const data = await response.json();
    console.log(`📊 Found ${data.total_items} tools total, showing page ${data.current_page} of ${data.total_pages}`);

    // Look for tools we need: neon, apify, vercel, etc.
    const targetApps = ['neon', 'apify', 'vercel', 'github'];
    const foundTools = {};

    data.items.forEach(tool => {
      targetApps.forEach(target => {
        if (tool.name.toLowerCase().includes(target) ||
            (tool.app_name && tool.app_name.toLowerCase().includes(target))) {
          if (!foundTools[target]) foundTools[target] = [];
          foundTools[target].push(tool);
        }
      });
    });

    console.log('\n🎯 Found relevant tools:');
    Object.entries(foundTools).forEach(([app, tools]) => {
      console.log(`\n${app.toUpperCase()}:`);
      tools.slice(0, 3).forEach(tool => {
        console.log(`  - ${tool.name} (${tool.slug})`);
      });
    });

    return { success: true, tools: foundTools, sample: data.items.slice(0, 5) };
  } catch (error) {
    console.log(`❌ Error listing tools: ${error.message}`);
    return { success: false, error: error.message };
  }
}

async function testToolExecution() {
  console.log('\n⚡ TESTING TOOL EXECUTION WITH CONNECTED ACCOUNTS');
  console.log('═'.repeat(50));

  // First, test with Vercel since we have a connected account
  const vercelTests = [
    {
      endpoint: '/api/v3/tools/execute',
      payload: {
        tool_slug: 'vercel_list_projects',
        connected_account_id: connectedAccounts.vercel,
        input: {}
      }
    },
    {
      endpoint: '/api/v3/tools/vercel_list_projects/execute',
      payload: {
        connected_account_id: connectedAccounts.vercel,
        input: {}
      }
    }
  ];

  for (const test of vercelTests) {
    console.log(`\n🔧 Testing: ${test.endpoint}`);

    try {
      const response = await fetch(`${composioBaseUrl}${test.endpoint}`, {
        method: 'POST',
        headers: {
          'x-api-key': composioApiKey,
          'Authorization': `Bearer ${composioApiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(test.payload)
      });

      console.log(`📤 Status: ${response.status}`);

      const responseText = await response.text();
      console.log(`📥 Response: ${responseText.substring(0, 300)}...`);

      if (response.ok) {
        console.log(`✅ SUCCESS: Vercel tool execution works!`);
        try {
          const jsonResponse = JSON.parse(responseText);
          console.log(`📊 Data: ${JSON.stringify(jsonResponse, null, 2)}`);
        } catch (e) {
          // Not JSON
        }
      } else if (response.status === 400) {
        console.log(`⚠️ BAD REQUEST: Tool exists but invalid payload`);
      } else if (response.status === 401) {
        console.log(`🔑 AUTH ISSUE: Tool exists but authorization problem`);
      } else if (response.status === 405) {
        console.log(`🚫 METHOD NOT ALLOWED: Wrong HTTP method or endpoint`);
      }

    } catch (error) {
      console.log(`❌ Error: ${error.message}`);
    }
  }

  // Test with Apify
  console.log('\n🕷️ Testing Apify tools...');
  const apifyTest = {
    endpoint: '/api/v3/tools/execute',
    payload: {
      tool_slug: 'apify_list_actors',
      connected_account_id: connectedAccounts.apify,
      input: {}
    }
  };

  try {
    const response = await fetch(`${composioBaseUrl}${apifyTest.endpoint}`, {
      method: 'POST',
      headers: {
        'x-api-key': composioApiKey,
        'Authorization': `Bearer ${composioApiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(apifyTest.payload)
    });

    console.log(`📤 Apify test: ${response.status}`);
    const responseText = await response.text();
    console.log(`📥 Apify response: ${responseText.substring(0, 200)}...`);

  } catch (error) {
    console.log(`❌ Apify error: ${error.message}`);
  }
}

async function createNeonConnection() {
  console.log('\n🐘 CREATING NEON CONNECTION');
  console.log('═'.repeat(30));

  // Try to create a Neon connected account
  const payload = {
    toolkit_slug: 'neon',
    entity_id: 'outreach-user',
    auth_config: {
      // Need to find the correct auth config ID for Neon
    }
  };

  console.log('⚠️ Neon connection creation requires proper auth config setup');
  console.log('This would typically be done through Composio dashboard first');
}

// Test different execution endpoint patterns
async function testExecutionPatterns() {
  console.log('\n🎯 TESTING EXECUTION ENDPOINT PATTERNS');
  console.log('═'.repeat(45));

  const patterns = [
    // Pattern 1: Direct tool slug execution
    { url: '/api/v3/tools/vercel_list_projects/execute', method: 'POST' },
    // Pattern 2: Generic execution with tool_slug in body
    { url: '/api/v3/tools/execute', method: 'POST' },
    // Pattern 3: Actions endpoint
    { url: '/api/v3/actions/execute', method: 'POST' },
  ];

  for (const pattern of patterns) {
    console.log(`\n⚡ Testing pattern: ${pattern.method} ${pattern.url}`);

    const payload = pattern.url.includes('vercel_list_projects') ?
      { connected_account_id: connectedAccounts.vercel, input: {} } :
      { tool_slug: 'vercel_list_projects', connected_account_id: connectedAccounts.vercel, input: {} };

    try {
      const response = await fetch(`${composioBaseUrl}${pattern.url}`, {
        method: pattern.method,
        headers: {
          'x-api-key': composioApiKey,
          'Authorization': `Bearer ${composioApiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      console.log(`📤 ${pattern.url}: ${response.status}`);

      if (response.status !== 404) {
        const responseText = await response.text();
        console.log(`📥 Response: ${responseText.substring(0, 150)}...`);

        if (response.ok) {
          console.log(`✅ FOUND WORKING PATTERN: ${pattern.method} ${pattern.url}`);
        }
      }

    } catch (error) {
      console.log(`❌ Error: ${error.message}`);
    }
  }
}

// Main execution
async function main() {
  try {
    console.log('🚀 COMPOSIO WORKING EXECUTION TEST');
    console.log('═'.repeat(40));

    const toolsResult = await listAvailableTools();
    await testExecutionPatterns();
    await testToolExecution();
    await createNeonConnection();

    console.log('\n🎯 TESTING COMPLETE!');
    return { success: true };
  } catch (error) {
    console.error('❌ Test error:', error);
    return { success: false, error: error.message };
  }
}

main().catch(console.error);
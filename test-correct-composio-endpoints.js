/**
 * Test correct Composio tools execution endpoint
 * Based on documentation finding: /tools/execute/{tool-slug}
 */

const composioApiKey = 'ak_t-F0AbvfZHUZSUrqAGNn';
const composioBaseUrl = 'https://backend.composio.dev';

async function testCorrectToolsEndpoint() {
  console.log('🎯 TESTING CORRECT COMPOSIO TOOLS ENDPOINT');
  console.log('═'.repeat(50));

  // Test different tools endpoint patterns based on documentation
  const toolsEndpoints = [
    '/api/v1/tools/execute',
    '/api/tools/execute',
    '/tools/execute',
    '/api/v1/tools/neon/execute',
    '/api/tools/neon/execute',
    '/tools/neon/execute'
  ];

  const testPayload = {
    tool_slug: 'neon_list_databases',
    input: {}
  };

  console.log('📝 Test payload:', JSON.stringify(testPayload, null, 2));

  for (const endpoint of toolsEndpoints) {
    console.log(`\n⚡ Testing tools endpoint: ${composioBaseUrl}${endpoint}`);

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

      console.log(`📤 Status: ${response.status}`);

      const responseText = await response.text();
      console.log(`📥 Response: ${responseText.substring(0, 200)}...`);

      if (response.status !== 404) {
        console.log(`✅ ENDPOINT EXISTS (non-404 response)`);

        // If we get a meaningful response, log more details
        if (response.status === 200 || response.status === 400 || response.status === 401) {
          try {
            const jsonResponse = JSON.parse(responseText);
            console.log(`📊 JSON Response:`, JSON.stringify(jsonResponse, null, 2));
          } catch (e) {
            // Not JSON, that's ok
          }
        }
      }

    } catch (error) {
      console.log(`❌ Network Error: ${error.message}`);
    }
  }

  // Also test some specific tool patterns
  console.log('\n🔧 TESTING SPECIFIC NEON TOOL PATTERNS');

  const neonToolPatterns = [
    { endpoint: '/api/v1/tools/execute', tool: 'neon_list_databases' },
    { endpoint: '/api/v1/tools/execute', tool: 'neon_run_query' },
    { endpoint: '/api/v1/tools/execute', tool: 'neon_query' },
    { endpoint: '/api/v1/tools/execute', tool: 'NEON_LIST_DATABASES' },
    { endpoint: '/api/v1/tools/execute', tool: 'NEON_QUERY' }
  ];

  for (const pattern of neonToolPatterns) {
    const payload = {
      tool_slug: pattern.tool,
      input: pattern.tool.includes('query') ? { query: 'SELECT 1' } : {}
    };

    console.log(`\n🎯 Testing ${pattern.tool}:`);

    try {
      const response = await fetch(`${composioBaseUrl}${pattern.endpoint}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${composioApiKey}`,
          'X-API-Key': composioApiKey,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      console.log(`📤 ${pattern.tool}: ${response.status}`);
      const responseText = await response.text();

      if (response.status !== 404) {
        console.log(`📥 Response: ${responseText.substring(0, 150)}...`);

        if (response.status === 200) {
          console.log(`✅ SUCCESS: Tool ${pattern.tool} works!`);
        } else if (response.status === 401) {
          console.log(`🔑 AUTH NEEDED: Tool exists but needs authentication`);
        } else if (response.status === 400) {
          console.log(`⚠️ BAD REQUEST: Tool exists but invalid payload`);
        }
      }

    } catch (error) {
      console.log(`❌ Error testing ${pattern.tool}: ${error.message}`);
    }
  }
}

// Check what tools are actually available
async function listAvailableTools() {
  console.log('\n📋 LISTING AVAILABLE TOOLS');
  console.log('═'.repeat(30));

  const toolsListEndpoints = [
    '/api/v1/tools',
    '/api/tools',
    '/tools',
    '/api/v1/apps/neon/tools',
    '/api/v1/apps/neon/actions'
  ];

  for (const endpoint of toolsListEndpoints) {
    console.log(`\n📡 Checking: ${composioBaseUrl}${endpoint}`);

    try {
      const response = await fetch(`${composioBaseUrl}${endpoint}`, {
        headers: {
          'Authorization': `Bearer ${composioApiKey}`,
          'X-API-Key': composioApiKey
        }
      });

      console.log(`📤 Status: ${response.status}`);

      if (response.ok) {
        const data = await response.json();
        console.log(`✅ SUCCESS - Found tools list`);

        if (Array.isArray(data)) {
          console.log(`📊 ${data.length} tools available`);

          // Look for Neon-related tools
          const neonTools = data.filter(tool =>
            (tool.name && tool.name.toLowerCase().includes('neon')) ||
            (tool.slug && tool.slug.toLowerCase().includes('neon')) ||
            (tool.app && tool.app.toLowerCase().includes('neon'))
          );

          if (neonTools.length > 0) {
            console.log(`🎯 Found ${neonTools.length} Neon tools:`);
            neonTools.forEach(tool => {
              console.log(`  - ${tool.slug || tool.name}: ${tool.description || 'No description'}`);
            });
          }
        } else if (data.items) {
          console.log(`📊 ${data.items.length} tools available`);
          const sample = data.items.slice(0, 5);
          sample.forEach(tool => {
            console.log(`  - ${tool.slug || tool.name || tool.key}`);
          });
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
    await listAvailableTools();
    await testCorrectToolsEndpoint();

    console.log('\n🎉 Testing complete!');
    return { success: true };
  } catch (error) {
    console.error('❌ Test suite error:', error);
    return { success: false, error: error.message };
  }
}

main().catch(console.error);
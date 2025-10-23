/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ai/testing
Barton ID: 03.01.03
Unique ID: CTB-864CB4F4
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: HEIR
─────────────────────────────────────────────
*/

/**
 * Final test of Composio execution based on documentation patterns
 * Try different URL patterns and payload structures
 */

const composioApiKey = 'ak_t-F0AbvfZHUZSUrqAGNn';
const composioBaseUrl = 'https://backend.composio.dev';

const connectedAccounts = {
  vercel: 'ca_vkXglNynIxjm',
  apify: 'ca_yGfXDKPv3hz6',
};

async function testFinalExecutionPatterns() {
  console.log('🔥 FINAL COMPOSIO EXECUTION TEST');
  console.log('═'.repeat(40));

  // Based on docs: post-tools-execute-by-tool-slug pattern
  const testCases = [
    // Case 1: Direct tool slug in URL path
    {
      name: 'Tool slug in path',
      url: '/api/v3/tools/vercel_list_projects',
      method: 'POST',
      payload: {
        connected_account_id: connectedAccounts.vercel,
        input: {}
      }
    },
    // Case 2: Execute suffix in URL
    {
      name: 'Execute suffix',
      url: '/api/v3/tools/vercel_list_projects/execute',
      method: 'POST',
      payload: {
        connected_account_id: connectedAccounts.vercel,
        input: {}
      }
    },
    // Case 3: POST to tool ID directly
    {
      name: 'POST to tool directly',
      url: '/api/v3/tools/vercel_list_projects',
      method: 'POST',
      payload: {
        connected_account_id: connectedAccounts.vercel
      }
    },
    // Case 4: Generic actions endpoint
    {
      name: 'Generic actions execute',
      url: '/api/v3/actions/execute',
      method: 'POST',
      payload: {
        app_name: 'vercel',
        action_name: 'list_projects',
        connected_account_id: connectedAccounts.vercel,
        input: {}
      }
    },
    // Case 5: Different payload structure
    {
      name: 'Different payload format',
      url: '/api/v3/actions/execute',
      method: 'POST',
      payload: {
        toolkit_slug: 'vercel',
        tool_name: 'vercel_list_projects',
        connected_account_id: connectedAccounts.vercel,
        parameters: {}
      }
    }
  ];

  for (const testCase of testCases) {
    console.log(`\n🎯 Testing: ${testCase.name}`);
    console.log(`   URL: ${testCase.method} ${testCase.url}`);
    console.log(`   Payload: ${JSON.stringify(testCase.payload, null, 2)}`);

    try {
      const response = await fetch(`${composioBaseUrl}${testCase.url}`, {
        method: testCase.method,
        headers: {
          'x-api-key': composioApiKey,
          'Authorization': `Bearer ${composioApiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(testCase.payload)
      });

      console.log(`📤 Status: ${response.status}`);

      const responseText = await response.text();

      if (response.ok) {
        console.log(`✅ SUCCESS!`);
        console.log(`📊 Response: ${responseText}`);
        return { success: true, working_pattern: testCase, response: responseText };
      } else if (response.status === 400) {
        console.log(`⚠️ BAD REQUEST: ${responseText.substring(0, 200)}...`);

        // Try to parse JSON error for more details
        try {
          const errorJson = JSON.parse(responseText);
          if (errorJson.error && errorJson.error.errors) {
            console.log(`🔍 Validation errors: ${errorJson.error.errors.join(', ')}`);
          }
        } catch (e) {
          // Not JSON
        }
      } else if (response.status === 401) {
        console.log(`🔑 AUTH ISSUE: ${responseText.substring(0, 150)}...`);
      } else if (response.status === 405) {
        console.log(`🚫 METHOD NOT ALLOWED`);
      } else if (response.status === 404) {
        console.log(`❌ NOT FOUND`);
      } else {
        console.log(`📥 Response: ${responseText.substring(0, 200)}...`);
      }

    } catch (error) {
      console.log(`❌ Network Error: ${error.message}`);
    }
  }

  return { success: false, message: 'No working patterns found' };
}

// Let's also try to find what tools are actually available
async function findWorkingToolSlugs() {
  console.log('\n📋 FINDING ACTUAL WORKING TOOL SLUGS');
  console.log('═'.repeat(40));

  try {
    // Get a sample of tools to see their actual slugs
    const response = await fetch(`${composioBaseUrl}/api/v3/tools?limit=20`, {
      headers: {
        'x-api-key': composioApiKey,
        'Authorization': `Bearer ${composioApiKey}`
      }
    });

    if (response.ok) {
      const data = await response.json();
      console.log(`📊 Sample tools (first 10):`);

      data.items.slice(0, 10).forEach((tool, index) => {
        console.log(`${index + 1}. ${tool.name} (slug: ${tool.slug})`);
        if (tool.app_name) console.log(`   App: ${tool.app_name}`);
      });

      // Look specifically for Vercel tools
      const vercelTools = data.items.filter(tool =>
        tool.app_name === 'vercel' ||
        tool.name.toLowerCase().includes('vercel') ||
        tool.slug.toLowerCase().includes('vercel')
      );

      if (vercelTools.length > 0) {
        console.log(`\n🎯 Found ${vercelTools.length} Vercel tools:`);
        vercelTools.forEach(tool => {
          console.log(`  - ${tool.name} (${tool.slug})`);
        });

        // Test with actual Vercel tool slug
        console.log(`\n⚡ Testing with actual Vercel tool slug: ${vercelTools[0].slug}`);

        const testResponse = await fetch(`${composioBaseUrl}/api/v3/tools/${vercelTools[0].slug}`, {
          method: 'POST',
          headers: {
            'x-api-key': composioApiKey,
            'Authorization': `Bearer ${composioApiKey}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            connected_account_id: connectedAccounts.vercel,
            input: {}
          })
        });

        console.log(`📤 Test with real slug: ${testResponse.status}`);
        const testText = await testResponse.text();
        console.log(`📥 Response: ${testText.substring(0, 200)}...`);
      }

      return { success: true, sample_tools: data.items.slice(0, 5) };
    }
  } catch (error) {
    console.log(`❌ Error finding tool slugs: ${error.message}`);
  }

  return { success: false };
}

// Main execution
async function main() {
  try {
    await findWorkingToolSlugs();
    const result = await testFinalExecutionPatterns();

    console.log('\n🎯 FINAL TEST COMPLETE');
    return result;
  } catch (error) {
    console.error('❌ Test error:', error);
    return { success: false, error: error.message };
  }
}

main().then(result => {
  if (result.success) {
    console.log('\n🎉 FOUND WORKING COMPOSIO EXECUTION PATTERN!');
    process.exit(0);
  } else {
    console.log('\n❌ No working execution pattern found yet');
    console.log('Next steps: Check Composio dashboard for proper tool setup');
    process.exit(1);
  }
}).catch(console.error);
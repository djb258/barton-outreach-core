/**
 * List Apify Actors via Composio MCP
 * Queries your actual Apify account through Composio integration
 */

import fetch from 'node-fetch';
import fs from 'fs/promises';

const COMPOSIO_MCP_URL = process.env.COMPOSIO_MCP_URL || 'http://localhost:3001';
const COMPOSIO_API_KEY = process.env.COMPOSIO_API_KEY || 'ak_t-F0AbvfZHUZSUrqAGNn';
const APIFY_API_KEY = process.env.APIFY_API_KEY;

console.log('\n=== Apify Actor Discovery via Composio MCP ===\n');
console.log(`Composio MCP URL: ${COMPOSIO_MCP_URL}`);
console.log(`Composio API Key: ${COMPOSIO_API_KEY.substring(0, 10)}...`);
console.log(`Apify API Key: ${APIFY_API_KEY ? APIFY_API_KEY.substring(0, 10) + '...' : 'NOT SET'}\n`);

/**
 * Call Composio MCP tool
 */
async function callComposioTool(toolName, params = {}) {
  const payload = {
    tool: toolName,
    data: params,
    unique_id: '04.01.99.11.05000.002',
    process_id: 'List Apify Actors via Composio',
    orbt_layer: 5,
    blueprint_version: '1.0'
  };

  console.log(`\n[COMPOSIO] Calling tool: ${toolName}`);
  console.log(`[COMPOSIO] Params:`, JSON.stringify(params, null, 2));

  try {
    const response = await fetch(`${COMPOSIO_MCP_URL}/tool`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Composio-Api-Key': COMPOSIO_API_KEY,
        ...(APIFY_API_KEY ? { 'X-Apify-Api-Key': APIFY_API_KEY } : {})
      },
      body: JSON.stringify(payload)
    });

    const responseText = await response.text();
    console.log(`[COMPOSIO] Response Status: ${response.status}`);

    if (!response.ok) {
      console.error(`[COMPOSIO] Error Response:`, responseText);
      return { success: false, error: responseText, status: response.status };
    }

    try {
      const data = JSON.parse(responseText);
      console.log(`[COMPOSIO] Response received`);
      return { success: true, data, status: response.status };
    } catch (parseError) {
      console.log(`[COMPOSIO] Raw response:`, responseText);
      return { success: true, data: responseText, status: response.status };
    }
  } catch (error) {
    console.error(`[COMPOSIO] Request failed:`, error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Test Composio MCP health
 */
async function testComposioHealth() {
  console.log('\n[STEP 1] Testing Composio MCP connection...\n');

  try {
    const response = await fetch(`${COMPOSIO_MCP_URL}/health`, {
      method: 'GET',
      headers: {
        'X-Composio-Api-Key': COMPOSIO_API_KEY
      }
    });

    const health = await response.text();
    console.log(`[HEALTH] Status: ${response.status}`);
    console.log(`[HEALTH] Response:`, health);

    return response.ok;
  } catch (error) {
    console.error(`[HEALTH] Failed:`, error.message);
    return false;
  }
}

/**
 * List available Composio tools
 */
async function listComposioTools() {
  console.log('\n[STEP 2] Listing available Composio tools...\n');

  try {
    const response = await fetch(`${COMPOSIO_MCP_URL}/tools`, {
      method: 'GET',
      headers: {
        'X-Composio-Api-Key': COMPOSIO_API_KEY
      }
    });

    const tools = await response.json();
    console.log(`[TOOLS] Found ${tools.length || 0} tools`);

    // Filter for Apify tools
    const apifyTools = tools.filter(tool =>
      tool.name?.toLowerCase().includes('apify') ||
      tool.id?.toLowerCase().includes('apify')
    );

    console.log(`\n[TOOLS] Apify-related tools (${apifyTools.length}):`);
    apifyTools.forEach(tool => {
      console.log(`  - ${tool.name || tool.id}: ${tool.description || 'No description'}`);
    });

    return apifyTools;
  } catch (error) {
    console.error(`[TOOLS] Failed:`, error.message);
    return [];
  }
}

/**
 * Try different methods to list Apify actors
 */
async function listApifyActors() {
  console.log('\n[STEP 3] Attempting to list Apify actors...\n');

  const methods = [
    // Method 1: Composio Apify list actors
    { name: 'apify.list_actors', params: { my: true, limit: 100 } },
    { name: 'apify_list_actors', params: { my: true, limit: 100 } },

    // Method 2: Get user's actors
    { name: 'apify.get_user_actors', params: {} },
    { name: 'apify_get_user_actors', params: {} },

    // Method 3: List my actors
    { name: 'apify.my_actors', params: {} },
    { name: 'apify_my_actors', params: {} },

    // Method 4: Get account info (might include actors)
    { name: 'apify.get_account', params: {} },
    { name: 'apify_get_account', params: {} },

    // Method 5: Generic tool call
    { name: 'APIFY_LIST_ACTORS', params: {} },
  ];

  for (const method of methods) {
    console.log(`\n--- Trying: ${method.name} ---`);
    const result = await callComposioTool(method.name, method.params);

    if (result.success && result.data) {
      console.log(`[SUCCESS] Method worked: ${method.name}`);

      // Try to extract actor list
      if (result.data.data?.items) {
        console.log(`[ACTORS] Found ${result.data.data.items.length} actors!`);
        return result.data.data.items;
      } else if (result.data.items) {
        console.log(`[ACTORS] Found ${result.data.items.length} actors!`);
        return result.data.items;
      } else if (Array.isArray(result.data)) {
        console.log(`[ACTORS] Found ${result.data.length} actors!`);
        return result.data;
      } else {
        console.log(`[DATA] Response structure:`, Object.keys(result.data));
      }
    }

    // Wait a bit between attempts
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  console.log('\n[WARNING] No method successfully returned actors list');
  return null;
}

/**
 * Try direct Apify API call (as fallback)
 */
async function listActorsDirectly() {
  if (!APIFY_API_KEY) {
    console.log('\n[SKIP] No APIFY_API_KEY set, skipping direct API call');
    return null;
  }

  console.log('\n[STEP 4] Trying direct Apify API as fallback...\n');

  const endpoints = [
    'https://api.apify.com/v2/acts',
    'https://api.apify.com/v2/acts?my=true',
    'https://api.apify.com/v2/actor-tasks',
    'https://api.apify.com/v2/store',
  ];

  for (const endpoint of endpoints) {
    console.log(`\n[DIRECT] Trying: ${endpoint}`);

    try {
      const response = await fetch(`${endpoint}?token=${APIFY_API_KEY}`, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      console.log(`[DIRECT] Status: ${response.status}`);

      if (response.ok) {
        const data = await response.json();

        if (data.data?.items) {
          console.log(`[DIRECT] Found ${data.data.items.length} items!`);
          return data.data.items;
        } else if (data.data?.count !== undefined) {
          console.log(`[DIRECT] Total count: ${data.data.count}`);
          console.log(`[DIRECT] Response keys:`, Object.keys(data.data));
        }
      }
    } catch (error) {
      console.error(`[DIRECT] Error:`, error.message);
    }
  }

  return null;
}

/**
 * Main execution
 */
async function main() {
  const results = {
    timestamp: new Date().toISOString(),
    composio_healthy: false,
    available_tools: [],
    actors_found: [],
    method_used: null,
    errors: []
  };

  try {
    // Step 1: Test Composio health
    results.composio_healthy = await testComposioHealth();

    if (!results.composio_healthy) {
      console.log('\n[ERROR] Composio MCP is not responding!');
      console.log('[INFO] Make sure the Composio MCP server is running on port 3001');
      console.log('[INFO] You can start it with: cd mcp-servers/composio-mcp && node server.js');
    }

    // Step 2: List available tools
    results.available_tools = await listComposioTools();

    // Step 3: Try to list actors via Composio
    const actorsViaComposio = await listApifyActors();

    if (actorsViaComposio && actorsViaComposio.length > 0) {
      results.actors_found = actorsViaComposio;
      results.method_used = 'composio';
    } else {
      // Step 4: Fallback to direct API
      const actorsDirectly = await listActorsDirectly();

      if (actorsDirectly && actorsDirectly.length > 0) {
        results.actors_found = actorsDirectly;
        results.method_used = 'direct_api';
      }
    }

    // Save results
    const outputPath = './analysis/apify_actors_via_composio.json';
    await fs.writeFile(outputPath, JSON.stringify(results, null, 2));

    // Print summary
    console.log('\n\n=== DISCOVERY SUMMARY ===\n');
    console.log(`Composio MCP Healthy: ${results.composio_healthy ? 'YES' : 'NO'}`);
    console.log(`Available Composio Tools: ${results.available_tools.length}`);
    console.log(`Actors Found: ${results.actors_found.length}`);
    console.log(`Method Used: ${results.method_used || 'NONE'}`);

    if (results.actors_found.length > 0) {
      console.log('\n=== YOUR APIFY ACTORS ===\n');
      results.actors_found.forEach((actor, i) => {
        console.log(`${i + 1}. ${actor.id || actor.name || 'Unknown'}`);
        if (actor.title) console.log(`   Title: ${actor.title}`);
        if (actor.username) console.log(`   Owner: ${actor.username}`);
        if (actor.stats?.runs) console.log(`   Total Runs: ${actor.stats.runs}`);
        console.log('');
      });
    } else {
      console.log('\n[WARNING] No actors found in your account');
      console.log('[INFO] This could mean:');
      console.log('  1. You need to subscribe to actors in Apify Store');
      console.log('  2. Your API key needs permissions');
      console.log('  3. Composio-Apify integration needs configuration');
    }

    console.log(`\nResults saved to: ${outputPath}`);

  } catch (error) {
    console.error('\n[FATAL ERROR]:', error);
    results.errors.push(error.message);
  }

  return results;
}

// Run
main()
  .then(results => {
    if (results.actors_found.length > 0) {
      console.log('\n✅ SUCCESS: Found actors in your account!');
      process.exit(0);
    } else {
      console.log('\n⚠️  WARNING: No actors found');
      process.exit(1);
    }
  })
  .catch(error => {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  });

/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/analysis
Barton ID: 06.01.01
Unique ID: CTB-D67EE977
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

/**
 * Query Apify via Composio Backend API
 * Uses Composio's REST API to access Apify integration
 */

import fetch from 'node-fetch';
import fs from 'fs/promises';

const COMPOSIO_API_KEY = process.env.COMPOSIO_API_KEY || 'ak_t-F0AbvfZHUZSUrqAGNn';
const COMPOSIO_BASE_URL = 'https://backend.composio.dev/api/v2';

console.log('\n=== Querying Apify via Composio Backend API ===\n');
console.log(`Composio API Key: ${COMPOSIO_API_KEY.substring(0, 15)}...`);
console.log(`Composio Base URL: ${COMPOSIO_BASE_URL}\n`);

/**
 * Call Composio API
 */
async function callComposioAPI(endpoint, method = 'GET', body = null) {
  const url = `${COMPOSIO_BASE_URL}${endpoint}`;
  console.log(`\n[API] ${method} ${endpoint}`);

  const options = {
    method,
    headers: {
      'X-API-Key': COMPOSIO_API_KEY,
      'Content-Type': 'application/json'
    }
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(url, options);
    const text = await response.text();

    console.log(`[API] Status: ${response.status}`);

    if (!response.ok) {
      console.error(`[API] Error:`, text.substring(0, 200));
      return { success: false, status: response.status, error: text };
    }

    try {
      const data = JSON.parse(text);
      return { success: true, status: response.status, data };
    } catch (e) {
      return { success: true, status: response.status, data: text };
    }
  } catch (error) {
    console.error(`[API] Request failed:`, error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Step 1: Check connected accounts
 */
async function getConnectedAccounts() {
  console.log('\n[STEP 1] Checking connected accounts...\n');

  const result = await callComposioAPI('/connectedAccounts');

  if (result.success && result.data) {
    const accounts = result.data.items || result.data.connectedAccounts || result.data;
    console.log(`[ACCOUNTS] Found ${Array.isArray(accounts) ? accounts.length : 'unknown'} connected accounts`);

    if (Array.isArray(accounts)) {
      accounts.forEach(account => {
        console.log(`  - ${account.appName || account.app_name || 'Unknown'} (${account.id})`);
      });

      // Find Apify account
      const apifyAccount = accounts.find(acc =>
        (acc.appName || acc.app_name || '').toLowerCase().includes('apify')
      );

      if (apifyAccount) {
        console.log(`\n[FOUND] Apify account connected!`);
        console.log(`  ID: ${apifyAccount.id}`);
        console.log(`  Status: ${apifyAccount.status || 'Active'}`);
        return apifyAccount;
      } else {
        console.log(`\n[WARNING] No Apify account found in connected accounts`);
      }
    }
  }

  return null;
}

/**
 * Step 2: Get available Apify actions
 */
async function getApifyActions() {
  console.log('\n[STEP 2] Getting available Apify actions...\n');

  // Try v2 API endpoint
  const result = await callComposioAPI('/actions?apps=apify');

  if (result.success && result.data) {
    const actions = result.data.items || result.data.actions || result.data;
    console.log(`[ACTIONS] Found ${Array.isArray(actions) ? actions.length : 'unknown'} Apify actions`);

    if (Array.isArray(actions)) {
      // Filter for list/get actor actions
      const actorActions = actions.filter(action =>
        action.name?.toLowerCase().includes('actor') ||
        action.name?.toLowerCase().includes('list') ||
        action.description?.toLowerCase().includes('actor')
      );

      console.log(`\n[ACTOR ACTIONS] ${actorActions.length} actor-related actions:`);
      actorActions.forEach(action => {
        console.log(`  - ${action.name}: ${action.description || 'No description'}`);
      });

      return actorActions;
    }
  }

  return [];
}

/**
 * Step 3: Execute action to list actors
 */
async function listActors(connectedAccountId) {
  console.log('\n[STEP 3] Listing Apify actors...\n');

  // Try different action names
  const actionNames = [
    'APIFY_LIST_ACTORS',
    'APIFY_GET_ACTORS',
    'APIFY_LIST_USER_ACTORS',
    'apify_list_actors',
    'apify_get_actors'
  ];

  for (const actionName of actionNames) {
    console.log(`\n[TRY] Executing action: ${actionName}`);

    const payload = {
      connectedAccountId: connectedAccountId,
      input: {
        my: true,
        limit: 100
      },
      appName: 'apify'
    };

    // Try v2 execute endpoint
    const result = await callComposioAPI(`/actions/${actionName}/execute`, 'POST', payload);

    if (result.success && result.data) {
      console.log(`[SUCCESS] Action worked!`);

      // Try to find actors in response
      if (result.data.data?.items) {
        return result.data.data.items;
      } else if (result.data.items) {
        return result.data.items;
      } else if (result.data.result) {
        return result.data.result;
      } else if (result.data.executionDetails?.data?.items) {
        return result.data.executionDetails.data.items;
      } else {
        console.log(`[RESPONSE] Keys:`, Object.keys(result.data));
        console.log(`[RESPONSE] Sample:`, JSON.stringify(result.data).substring(0, 300));
      }
    }
  }

  return null;
}

/**
 * Step 4: Try direct Apify integration query
 */
async function getApifyIntegration() {
  console.log('\n[STEP 4] Checking Apify app integration...\n');

  const result = await callComposioAPI('/apps/apify');

  if (result.success && result.data) {
    console.log(`[APP] Apify integration details:`);
    console.log(JSON.stringify(result.data, null, 2).substring(0, 500));
    return result.data;
  }

  return null;
}

/**
 * Step 5: Get entity info (might include actors)
 */
async function getEntityInfo() {
  console.log('\n[STEP 5] Getting entity information...\n');

  const result = await callComposioAPI('/client/auth/user_info');

  if (result.success && result.data) {
    console.log(`[ENTITY] User info retrieved`);
    return result.data;
  }

  return null;
}

/**
 * Main execution
 */
async function main() {
  const results = {
    timestamp: new Date().toISOString(),
    composio_api_key: COMPOSIO_API_KEY.substring(0, 15) + '...',
    connected_accounts: [],
    apify_account: null,
    apify_actions: [],
    actors: [],
    errors: []
  };

  try {
    // Step 1: Get connected accounts
    const apifyAccount = await getConnectedAccounts();
    results.apify_account = apifyAccount;

    // Step 2: Get Apify actions
    const actions = await getApifyActions();
    results.apify_actions = actions.map(a => ({
      name: a.name,
      description: a.description
    }));

    // Step 3: If we have an Apify account, try to list actors
    if (apifyAccount && apifyAccount.id) {
      const actors = await listActors(apifyAccount.id);
      if (actors) {
        results.actors = actors;
      }
    } else {
      console.log('\n[INFO] No connected Apify account found');
      console.log('[INFO] You need to connect Apify to Composio at: https://app.composio.dev');
    }

    // Step 4: Get Apify app integration details
    const appDetails = await getApifyIntegration();
    results.app_details = appDetails;

    // Step 5: Get entity info
    const entityInfo = await getEntityInfo();
    results.entity_info = entityInfo;

    // Save results
    const outputPath = './analysis/apify_via_composio_results.json';
    await fs.writeFile(outputPath, JSON.stringify(results, null, 2));

    // Print summary
    console.log('\n\n=== SUMMARY ===\n');
    console.log(`Connected Accounts: ${results.connected_accounts.length}`);
    console.log(`Apify Account Connected: ${results.apify_account ? 'YES' : 'NO'}`);
    console.log(`Available Apify Actions: ${results.apify_actions.length}`);
    console.log(`Actors Found: ${results.actors.length}`);

    if (results.actors.length > 0) {
      console.log('\n=== YOUR APIFY ACTORS ===\n');
      results.actors.forEach((actor, i) => {
        console.log(`${i + 1}. ${actor.id || actor.name}`);
        if (actor.title) console.log(`   Title: ${actor.title}`);
        if (actor.username) console.log(`   Owner: ${actor.username}`);
        console.log('');
      });
    } else if (!results.apify_account) {
      console.log('\n[ACTION REQUIRED] Connect Apify to Composio:');
      console.log('1. Go to: https://app.composio.dev');
      console.log('2. Navigate to "Connected Accounts"');
      console.log('3. Click "Add Account" and select "Apify"');
      console.log('4. Enter your Apify API token');
      console.log('5. Re-run this script');
    }

    console.log(`\nResults saved to: ${outputPath}`);
    return results;

  } catch (error) {
    console.error('\n[ERROR]:', error);
    results.errors.push(error.message);
    return results;
  }
}

// Run
main()
  .then(results => {
    if (results.actors.length > 0) {
      console.log('\n✅ SUCCESS: Found actors via Composio!');
      process.exit(0);
    } else {
      console.log('\n⚠️  No actors found - may need to connect Apify to Composio');
      process.exit(0);
    }
  })
  .catch(error => {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  });

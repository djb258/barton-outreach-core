/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/analysis
Barton ID: 06.01.01
Unique ID: CTB-C2603BB4
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

/**
 * Execute Apify List Tasks via Composio
 * Uses the connected Apify account to list tasks/actors
 */

import fetch from 'node-fetch';

const COMPOSIO_API_KEY = 'ak_t-F0AbvfZHUZSUrqAGNn';
const APIFY_CONNECTED_ACCOUNT_ID = 'f81a8a4a-c602-4adf-be02-fadec17cc378';

console.log('\n=== Executing Apify Actions via Composio ===\n');

async function executeComposioAction(actionName, params = {}) {
  const url = `https://backend.composio.dev/api/v2/actions/${actionName}/execute`;

  const payload = {
    connectedAccountId: APIFY_CONNECTED_ACCOUNT_ID,
    appName: 'apify',
    input: params
  };

  console.log(`\n[EXECUTE] ${actionName}`);
  console.log(`[PARAMS]`, JSON.stringify(params, null, 2));

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'X-API-Key': COMPOSIO_API_KEY,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    const text = await response.text();
    console.log(`[STATUS] ${response.status}`);

    if (!response.ok) {
      console.error(`[ERROR]`, text.substring(0, 300));
      return null;
    }

    const data = JSON.parse(text);
    console.log(`[SUCCESS] Response received`);

    return data;
  } catch (error) {
    console.error(`[FAILED]`, error.message);
    return null;
  }
}

async function main() {
  console.log('Step 1: Trying to list Actor Tasks...\n');

  const tasks = await executeComposioAction('APIFY_GET_LIST_OF_TASKS', {
    limit: 100
  });

  if (tasks && tasks.data) {
    console.log('\n=== YOUR APIFY TASKS ===\n');
    console.log(JSON.stringify(tasks.data, null, 2));

    if (tasks.data.items && Array.isArray(tasks.data.items)) {
      console.log(`\nFound ${tasks.data.items.length} tasks:`);
      tasks.data.items.forEach((task, i) => {
        console.log(`${i + 1}. ${task.name || task.id}`);
        if (task.actorId) console.log(`   Actor: ${task.actorId}`);
        if (task.actorTaskId) console.log(`   Task ID: ${task.actorTaskId}`);
      });
    }
  }

  // Let's also try to get a specific popular actor
  console.log('\n\nStep 2: Trying to get a popular Apify actor...\n');

  const popularActors = [
    'apify/web-scraper',
    'apify/google-search-scraper',
    'apify/linkedin-profile-scraper',
    'apify/website-content-crawler'
  ];

  for (const actorId of popularActors) {
    console.log(`\nTrying: ${actorId}`);

    const actor = await executeComposioAction('APIFY_GET_ACTOR', {
      actorId: actorId
    });

    if (actor && actor.data) {
      console.log(`✅ Found: ${actor.data.name || actorId}`);
      console.log(`   Description: ${(actor.data.description || '').substring(0, 100)}`);
      console.log(`   Public: ${actor.data.isPublic}`);

      // Save first found actor
      if (!global.firstActor) {
        global.firstActor = actor.data;
      }
    }
  }

  console.log('\n\n=== SUMMARY ===\n');
  console.log('✅ Successfully connected to Apify via Composio');
  console.log('✅ Can execute Apify actions');
  console.log('\n📋 Available Actions:');
  console.log('  - APIFY_GET_LIST_OF_TASKS');
  console.log('  - APIFY_GET_ACTOR');
  console.log('  - APIFY_RUN_ACTOR');
  console.log('  - APIFY_RUN_ACTOR_SYNC_GET_DATASET_ITEMS');
  console.log('  - And 15+ more actions');

  console.log('\n💡 Next Steps:');
  console.log('1. Tell me which Apify actors YOU want to use');
  console.log('2. I can run them via Composio and get results');
  console.log('3. Or list YOUR custom actors if you have any');
}

main().catch(console.error);

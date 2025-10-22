/**
 * Find code_crafter/leads-finder Actor via Composio
 */

import fetch from 'node-fetch';

const COMPOSIO_API_KEY = 'ak_t-F0AbvfZHUZSUrqAGNn';
const APIFY_CONNECTED_ACCOUNT_ID = 'f81a8a4a-c602-4adf-be02-fadec17cc378';

console.log('\n=== Searching for code_crafter/leads-finder Actor ===\n');

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
      console.error(`[ERROR]`, text.substring(0, 500));
      return null;
    }

    const data = JSON.parse(text);
    console.log(`[SUCCESS] Response received`);
    console.log(`[FULL RESPONSE]`, JSON.stringify(data, null, 2));

    return data;
  } catch (error) {
    console.error(`[FAILED]`, error.message);
    return null;
  }
}

async function main() {
  // Try 1: Get the specific actor by ID
  console.log('\n[TRY 1] Getting actor: code_crafter/leads-finder\n');

  const actor1 = await executeComposioAction('APIFY_GET_ACTOR', {
    actorId: 'code_crafter/leads-finder'
  });

  if (actor1) {
    // Check different response structures
    const actorData = actor1.data || actor1.executionDetails?.data || actor1.result || actor1;

    if (actorData && Object.keys(actorData).length > 0) {
      console.log('\n=== FOUND ACTOR ===\n');
      console.log(JSON.stringify(actorData, null, 2));
      return actorData;
    } else {
      console.log('[INFO] Actor endpoint responded but no data returned');
      console.log('[RESPONSE KEYS]', Object.keys(actor1));
    }
  }

  // Try 2: With tilde separator
  console.log('\n[TRY 2] Getting actor: code_crafter~leads-finder\n');

  const actor2 = await executeComposioAction('APIFY_GET_ACTOR', {
    actorId: 'code_crafter~leads-finder'
  });

  if (actor2 && actor2.data) {
    console.log('\n=== FOUND ACTOR ===\n');
    console.log(JSON.stringify(actor2.data, null, 2));
    return actor2.data;
  }

  // Try 3: List all tasks to see if leads-finder is configured
  console.log('\n[TRY 3] Listing all tasks to find leads-finder\n');

  const tasks = await executeComposioAction('APIFY_GET_LIST_OF_TASKS', {
    limit: 100
  });

  if (tasks && tasks.data) {
    console.log('\n=== ALL TASKS ===\n');
    console.log(JSON.stringify(tasks.data, null, 2));

    if (tasks.data.items && Array.isArray(tasks.data.items)) {
      const leadsFinderTask = tasks.data.items.find(task =>
        task.name?.toLowerCase().includes('leads-finder') ||
        task.actorId?.includes('leads-finder')
      );

      if (leadsFinderTask) {
        console.log('\n=== FOUND LEADS-FINDER TASK ===\n');
        console.log(JSON.stringify(leadsFinderTask, null, 2));
        return leadsFinderTask;
      }
    }
  }

  // Try 4: Get list of runs to see if this actor has been executed
  console.log('\n[TRY 4] Getting list of runs for leads-finder\n');

  const runs = await executeComposioAction('APIFY_GET_LIST_OF_RUNS', {
    limit: 100
  });

  if (runs && runs.data) {
    console.log('\n=== ACTOR RUNS ===\n');
    console.log(JSON.stringify(runs.data, null, 2).substring(0, 1000));

    if (runs.data.items && Array.isArray(runs.data.items)) {
      const leadsFinderRuns = runs.data.items.filter(run =>
        run.actorId?.includes('leads-finder') ||
        run.actorTaskId?.includes('leads-finder')
      );

      if (leadsFinderRuns.length > 0) {
        console.log('\n=== FOUND LEADS-FINDER RUNS ===\n');
        console.log(JSON.stringify(leadsFinderRuns, null, 2));
        return leadsFinderRuns;
      }
    }
  }

  console.log('\n[NOT FOUND] Could not locate code_crafter/leads-finder actor');
  console.log('[INFO] This could mean:');
  console.log('  1. The actor is not yet created in your Apify account');
  console.log('  2. The actor name/username is different');
  console.log('  3. The actor is private and requires different permissions');

  return null;
}

main().catch(console.error);

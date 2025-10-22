/**
 * Get Input Schema for code_crafter/leads-finder
 */

import fetch from 'node-fetch';
import fs from 'fs/promises';

const COMPOSIO_API_KEY = 'ak_t-F0AbvfZHUZSUrqAGNn';
const APIFY_CONNECTED_ACCOUNT_ID = 'f81a8a4a-c602-4adf-be02-fadec17cc378';

console.log('\n=== Getting Leads Finder Input Schema ===\n');

async function executeComposioAction(actionName, params = {}) {
  const url = `https://backend.composio.dev/api/v2/actions/${actionName}/execute`;

  const payload = {
    connectedAccountId: APIFY_CONNECTED_ACCOUNT_ID,
    appName: 'apify',
    input: params
  };

  console.log(`\n[EXECUTE] ${actionName}`);

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

    return JSON.parse(text);
  } catch (error) {
    console.error(`[FAILED]`, error.message);
    return null;
  }
}

async function main() {
  const results = {
    actor_id: 'code_crafter~leads-finder',
    actor_details: null,
    input_schema: null,
    builds: null,
    recent_runs: null,
    timestamp: new Date().toISOString()
  };

  // 1. Get full actor details
  console.log('\n[STEP 1] Getting full actor details...\n');
  const actorDetails = await executeComposioAction('APIFY_GET_ACTOR', {
    actorId: 'code_crafter~leads-finder'
  });

  if (actorDetails && actorDetails.data) {
    results.actor_details = actorDetails.data;
    console.log('[SUCCESS] Actor details retrieved');
  }

  // 2. Get the latest build (which contains input schema)
  console.log('\n[STEP 2] Getting latest build for input schema...\n');
  const buildDetails = await executeComposioAction('APIFY_GET_DEFAULT_BUILD', {
    actorId: 'code_crafter~leads-finder',
    waitForFinish: 0
  });

  if (buildDetails && buildDetails.data) {
    results.input_schema = buildDetails.data.inputSchema || buildDetails.data;
    console.log('[SUCCESS] Build details retrieved');
  }

  // 3. Get list of recent builds
  console.log('\n[STEP 3] Getting build history...\n');
  const builds = await executeComposioAction('APIFY_GET_LIST_OF_BUILDS', {
    actorId: 'code_crafter~leads-finder',
    limit: 5
  });

  if (builds && builds.data) {
    results.builds = builds.data;
    console.log('[SUCCESS] Build history retrieved');
  }

  // 4. Get recent runs to see example inputs
  console.log('\n[STEP 4] Getting recent runs for example inputs...\n');
  const runs = await executeComposioAction('APIFY_GET_LIST_OF_RUNS', {
    limit: 10
  });

  if (runs && runs.data && runs.data.items) {
    // Filter for leads-finder runs
    const leadsFinderRuns = runs.data.items.filter(run =>
      run.actorId === 'IoSHqwTR9YGhzccez' ||
      run.actorId?.includes('leads-finder')
    );
    results.recent_runs = leadsFinderRuns.slice(0, 5);
    console.log(`[SUCCESS] Found ${leadsFinderRuns.length} recent runs`);
  }

  // 5. Try to get OpenAPI definition
  console.log('\n[STEP 5] Getting OpenAPI definition...\n');
  const openApi = await executeComposioAction('APIFY_GET_OPEN_API_DEFINITION', {
    actorId: 'code_crafter~leads-finder'
  });

  if (openApi && openApi.data) {
    results.openapi_schema = openApi.data;
    console.log('[SUCCESS] OpenAPI definition retrieved');
  }

  // Save results
  const outputPath = './analysis/leads_finder_schema.json';
  await fs.writeFile(outputPath, JSON.stringify(results, null, 2));

  // Print summary
  console.log('\n\n=== LEADS FINDER SCHEMA SUMMARY ===\n');
  console.log(`Actor ID: ${results.actor_details?.id || 'N/A'}`);
  console.log(`Actor Name: ${results.actor_details?.name || 'N/A'}`);
  console.log(`Username: ${results.actor_details?.username || 'N/A'}`);
  console.log(`Title: ${results.actor_details?.title || 'N/A'}`);
  console.log(`Description: ${results.actor_details?.description || 'N/A'}`);
  console.log(`\nCategories: ${results.actor_details?.categories?.join(', ') || 'N/A'}`);
  console.log(`Public: ${results.actor_details?.isPublic || false}`);
  console.log(`Permission Level: ${results.actor_details?.actorPermissionLevel || 'N/A'}`);

  console.log('\n--- PERFORMANCE STATS ---');
  if (results.actor_details?.stats) {
    console.log(`Total Runs: ${results.actor_details.stats.totalRuns || 0}`);
    console.log(`Total Users: ${results.actor_details.stats.totalUsers || 0}`);
    console.log(`Last Run: ${results.actor_details.stats.lastRunStartedAt || 'N/A'}`);

    if (results.actor_details.stats.publicActorRunStats30Days) {
      const stats30 = results.actor_details.stats.publicActorRunStats30Days;
      console.log('\n30-Day Run Stats:');
      console.log(`  Succeeded: ${stats30.SUCCEEDED || 0}`);
      console.log(`  Failed: ${stats30.FAILED || 0}`);
      console.log(`  Timed-out: ${stats30['TIMED-OUT'] || 0}`);
      console.log(`  Aborted: ${stats30.ABORTED || 0}`);
      console.log(`  Total: ${stats30.TOTAL || 0}`);
      const successRate = ((stats30.SUCCEEDED / stats30.TOTAL) * 100).toFixed(2);
      console.log(`  Success Rate: ${successRate}%`);
    }
  }

  console.log('\n--- PRICING ---');
  if (results.actor_details?.pricingInfos && results.actor_details.pricingInfos[0]) {
    const pricing = results.actor_details.pricingInfos[0];
    console.log(`Model: ${pricing.pricingModel || 'N/A'}`);
    console.log(`Minimum Charge: $${pricing.minimalMaxTotalChargeUsd || 0}`);

    if (pricing.pricingPerEvent?.actorChargeEvents) {
      console.log('\nEvent Pricing:');
      const events = pricing.pricingPerEvent.actorChargeEvents;

      if (events['apify-actor-start']) {
        console.log(`  Actor Start: $${events['apify-actor-start'].eventPriceUsd}`);
      }

      if (events['lead-fetched']?.eventTieredPricingUsd) {
        console.log('  Lead Fetched (per lead):');
        Object.entries(events['lead-fetched'].eventTieredPricingUsd).forEach(([tier, info]) => {
          console.log(`    ${tier}: $${info.tieredEventPriceUsd}`);
        });
      }
    }
  }

  console.log('\n--- DEFAULT RUN OPTIONS ---');
  if (results.actor_details?.defaultRunOptions) {
    const opts = results.actor_details.defaultRunOptions;
    console.log(`Build: ${opts.build || 'N/A'}`);
    console.log(`Memory: ${opts.memoryMbytes || 0} MB`);
    console.log(`Timeout: ${opts.timeoutSecs || 0} seconds (${Math.floor((opts.timeoutSecs || 0) / 60)} minutes)`);
    console.log(`Max Items: ${opts.maxItems || 'Unlimited'}`);
  }

  console.log('\n--- INPUT SCHEMA ---');
  if (results.input_schema) {
    console.log('Input schema found! Check leads_finder_schema.json for full details.');
  } else {
    console.log('No input schema found in build details.');
  }

  console.log('\n--- RECENT RUNS ---');
  if (results.recent_runs && results.recent_runs.length > 0) {
    console.log(`Found ${results.recent_runs.length} recent runs:`);
    results.recent_runs.forEach((run, i) => {
      console.log(`\n${i + 1}. Run ${run.id}`);
      console.log(`   Status: ${run.status}`);
      console.log(`   Started: ${run.startedAt}`);
      console.log(`   Finished: ${run.finishedAt || 'N/A'}`);
      if (run.stats?.inputBodyLen) {
        console.log(`   Input Size: ${run.stats.inputBodyLen} bytes`);
      }
    });
  } else {
    console.log('No recent runs found for this actor.');
  }

  console.log(`\n\nFull details saved to: ${outputPath}`);

  return results;
}

main().catch(console.error);

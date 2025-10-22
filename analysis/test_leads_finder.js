/**
 * Test Leads Finder Actor - Executive Enrichment
 * This script demonstrates how to run code_crafter~leads-finder via Composio
 */

import fetch from 'node-fetch';
import fs from 'fs/promises';

const COMPOSIO_API_KEY = 'ak_t-F0AbvfZHUZSUrqAGNn';
const APIFY_CONNECTED_ACCOUNT_ID = 'f81a8a4a-c602-4adf-be02-fadec17cc378';
const ACTOR_ID = 'code_crafter~leads-finder';

console.log('\n=== Testing Leads Finder Actor for Executive Enrichment ===\n');

/**
 * Run the Leads Finder actor via Composio
 */
async function runLeadsFinder(inputParams) {
  const url = 'https://backend.composio.dev/api/v2/actions/APIFY_RUN_ACTOR/execute';

  const payload = {
    connectedAccountId: APIFY_CONNECTED_ACCOUNT_ID,
    appName: 'apify',
    input: {
      actorId: ACTOR_ID,
      ...inputParams
    }
  };

  console.log('[RUN] Starting Leads Finder actor...');
  console.log('[INPUT]', JSON.stringify(inputParams, null, 2));

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
      console.error('[ERROR]', text.substring(0, 500));
      return null;
    }

    const data = JSON.parse(text);
    return data;
  } catch (error) {
    console.error('[FAILED]', error.message);
    return null;
  }
}

/**
 * Run actor synchronously and get dataset items
 */
async function runLeadsFinderSync(inputParams) {
  const url = 'https://backend.composio.dev/api/v2/actions/APIFY_RUN_ACTOR_SYNC_GET_DATASET_ITEMS/execute';

  const payload = {
    connectedAccountId: APIFY_CONNECTED_ACCOUNT_ID,
    appName: 'apify',
    input: {
      actorId: ACTOR_ID,
      runInput: inputParams,
      timeout: 300 // 5 minutes
    }
  };

  console.log('[RUN SYNC] Starting Leads Finder actor (synchronous)...');
  console.log('[INPUT]', JSON.stringify(inputParams, null, 2));
  console.log('[WAIT] This may take a few minutes...\n');

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
      console.error('[ERROR]', text.substring(0, 1000));
      return null;
    }

    const data = JSON.parse(text);
    return data;
  } catch (error) {
    console.error('[FAILED]', error.message);
    return null;
  }
}

/**
 * Main test scenarios
 */
async function main() {
  const results = {
    timestamp: new Date().toISOString(),
    tests: []
  };

  // Test 1: Small test - C-suite executives in tech
  console.log('\n\n=== TEST 1: C-Suite Executives in Tech ===\n');

  const test1Input = {
    company_industry: [
      'information technology & services',
      'computer software'
    ],
    contact_job_title: [
      'CEO',
      'CFO',
      'CTO'
    ],
    contact_seniority: [
      'c-suite'
    ],
    contact_location: [
      'united states'
    ],
    contact_state: [
      'california, us'
    ],
    max_leads: 10 // Small test
  };

  const test1Result = await runLeadsFinderSync(test1Input);

  if (test1Result) {
    console.log('\n[SUCCESS] Test 1 completed');

    // Check for data in different response structures
    const leads = test1Result.data?.items ||
                  test1Result.data ||
                  test1Result.executionDetails?.data?.items ||
                  [];

    console.log(`[RESULTS] Found ${Array.isArray(leads) ? leads.length : 'unknown'} leads`);

    if (Array.isArray(leads) && leads.length > 0) {
      console.log('\n[SAMPLE LEAD]');
      console.log(JSON.stringify(leads[0], null, 2));
    }

    results.tests.push({
      name: 'C-Suite Tech Executives',
      input: test1Input,
      success: true,
      leadCount: Array.isArray(leads) ? leads.length : 0,
      sampleLead: Array.isArray(leads) && leads.length > 0 ? leads[0] : null
    });
  } else {
    console.log('\n[FAILED] Test 1 did not complete');
    results.tests.push({
      name: 'C-Suite Tech Executives',
      input: test1Input,
      success: false
    });
  }

  // Test 2: HR Leaders in Healthcare (async)
  console.log('\n\n=== TEST 2: HR Leaders in Healthcare (Async) ===\n');

  const test2Input = {
    company_industry: [
      'hospital & health care',
      'health, wellness & fitness'
    ],
    contact_job_title: [
      'CHRO',
      'HR Director',
      'VP of Human Resources'
    ],
    contact_seniority: [
      'c-suite',
      'vp',
      'director'
    ],
    contact_location: [
      'united states'
    ],
    max_leads: 5
  };

  const test2Result = await runLeadsFinder(test2Input);

  if (test2Result && test2Result.data) {
    console.log('\n[SUCCESS] Test 2 initiated (async)');
    console.log('[RUN ID]', test2Result.data.id || 'N/A');
    console.log('[STATUS]', test2Result.data.status || 'N/A');
    console.log('[NOTE] Run started asynchronously. Check Apify dashboard for results.');

    results.tests.push({
      name: 'HR Leaders in Healthcare',
      input: test2Input,
      success: true,
      runId: test2Result.data.id,
      status: test2Result.data.status
    });
  } else {
    console.log('\n[FAILED] Test 2 did not start');
    results.tests.push({
      name: 'HR Leaders in Healthcare',
      input: test2Input,
      success: false
    });
  }

  // Save results
  const outputPath = './analysis/leads_finder_test_results.json';
  await fs.writeFile(outputPath, JSON.stringify(results, null, 2));

  // Summary
  console.log('\n\n=== TEST SUMMARY ===\n');
  console.log(`Total Tests: ${results.tests.length}`);
  console.log(`Successful: ${results.tests.filter(t => t.success).length}`);
  console.log(`Failed: ${results.tests.filter(t => !t.success).length}`);

  results.tests.forEach((test, i) => {
    console.log(`\n${i + 1}. ${test.name}`);
    console.log(`   Status: ${test.success ? 'SUCCESS' : 'FAILED'}`);
    if (test.leadCount !== undefined) {
      console.log(`   Leads Found: ${test.leadCount}`);
    }
    if (test.runId) {
      console.log(`   Run ID: ${test.runId}`);
    }
  });

  console.log(`\n\nResults saved to: ${outputPath}`);
  console.log('\n=== NEXT STEPS ===');
  console.log('1. Review the results in leads_finder_test_results.json');
  console.log('2. Check lead quality and data completeness');
  console.log('3. Adjust filters based on results');
  console.log('4. Scale up max_leads once validated');
  console.log('5. Integrate into your outreach pipeline');

  return results;
}

// Run tests
main().catch(console.error);

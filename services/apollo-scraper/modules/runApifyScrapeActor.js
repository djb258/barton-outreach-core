// modules/runApifyScrapeActor.js
// Alternative version that uses Actor directly instead of Task
const { ApifyClient } = require('apify-client');

async function runApifyScrape(company) {
  console.log(`[O] [STEP] runApifyScrape: Triggering Apify for ${company.company_id || company.id} | ${company.company_name}...`);
  try {
    // Get environment variables
    const APIFY_API_KEY = process.env.APIFY_API_KEY;
    const APIFY_ACTOR_ID = process.env.APIFY_ACTOR_ID || process.env.APIFY_TASK_ID;
    
    if (!APIFY_API_KEY) throw new Error('[B] [ERROR] APIFY_API_KEY environment variable is required');
    if (!APIFY_ACTOR_ID) throw new Error('[B] [ERROR] APIFY_ACTOR_ID environment variable is required');
    
    console.log(`[R] [INFO] Launching Apify Apollo scraper for company: ${company.company_name}`);
    
    // Initialize Apify client
    const client = new ApifyClient({ token: APIFY_API_KEY });
    
    // Prepare input for the Apollo scraper actor
    const input = {
      url: company.apollo_url,
      cleanOutput: false,  // Matches your working configuration
      // Additional parameters that might be needed by the apollo-io-scraper actor
      maxResults: 1000,
      fileName: `${company.company_name.replace(/\s+/g, '_').toLowerCase()}_contacts`
    };
    
    console.log('[R] [INFO] Starting actor with input:', {
      url: input.url.substring(0, 80) + '...',
      cleanOutput: input.cleanOutput,
      maxResults: input.maxResults
    });
    
    // Run the actor
    const run = await client.actor(APIFY_ACTOR_ID).call(input);
    
    console.log(`[R] [SUCCESS] Apify run started for ${company.company_name}`);
    console.log(`[R] [INFO] Run ID: ${run.id}`);
    console.log(`[R] [INFO] Dataset ID: ${run.defaultDatasetId}`);
    
    // Wait for the run to finish
    console.log('[R] [INFO] Waiting for run to complete...');
    const finishedRun = await client.run(run.id).waitForFinish();
    
    if (finishedRun.status === 'SUCCEEDED') {
      console.log(`[R] [SUCCESS] Run completed successfully`);
      return { 
        runId: finishedRun.id, 
        datasetId: finishedRun.defaultDatasetId 
      };
    } else if (finishedRun.status === 'FAILED') {
      throw new Error(`Apify run failed: ${finishedRun.statusMessage}`);
    } else {
      throw new Error(`Unexpected run status: ${finishedRun.status}`);
    }
    
  } catch (error) {
    console.error(`[R] [ERROR] Failed to launch Apify run for ${company.company_name}:`, error.message);
    if (error.response?.data) {
      console.error('[R] [ERROR] API Response:', error.response.data);
    }
    throw new Error(`Apify launch failed: ${error.message}`);
  }
}

module.exports = { runApifyScrape };
// modules/runApifyScrape.js
const axios = require('axios');

async function runApifyScrape(company) {
  console.log(`[O] [STEP] runApifyScrape: Triggering Apify for ${company.company_id} | ${company.company_name}...`);
  try {
    // Get environment variables
    const APIFY_API_KEY = process.env.APIFY_API_KEY;
    const APIFY_TASK_ID = process.env.APIFY_TASK_ID;
    if (!APIFY_API_KEY) throw new Error('[B] [ERROR] APIFY_API_KEY environment variable is required');
    if (!APIFY_TASK_ID) throw new Error('[B] [ERROR] APIFY_TASK_ID environment variable is required');
    console.log(`[R] [INFO] Launching Apify Apollo scraper for company: ${company.company_name}`);
    const response = await axios.post(
      `https://api.apify.com/v2/actor-tasks/${APIFY_TASK_ID}/run-sync`,
      {
        url: company.apollo_url,
        fileName: `${company.company_name.replace(/\s+/g, '_').toLowerCase()}_contacts`,
        totalRecords: 1000,        // Or bump to 50000 if needed
        cleanOutput: false         // Matches working configuration
      },
      {
        headers: {
          Authorization: `Bearer ${APIFY_API_KEY}`,
          Accept: 'application/json'
        }
      }
    );
    const { id: runId, data } = response.data;
    const datasetId = data?.defaultDatasetId;
    console.log(`[R] [SUCCESS] Apify run started for ${company.company_name} | Run ID: ${runId} | Dataset ID: ${datasetId}`);
    return { runId, datasetId };
  } catch (error) {
    console.error(`[R] [ERROR] Failed to launch Apify run for ${company.company_name}:`, error?.response?.data || error.message);
    throw new Error(`Apify launch failed: ${error.message}`);
  }
}

module.exports = { runApifyScrape }; 
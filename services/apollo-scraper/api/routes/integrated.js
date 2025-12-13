const express = require('express');
const router = express.Router();
const { ApifyClient } = require('apify-client');
const { renderClient } = require('../clients/renderClient');

// Initialize Apify client
const apifyClient = new ApifyClient({
  token: process.env.APIFY_API_KEY
});

/**
 * POST /api/v1/integrated/scrape-and-store
 * Start a scraping job and store results in Render marketing DB
 */
router.post('/scrape-and-store', async (req, res) => {
  try {
    const {
      companyName,
      apolloUrl,
      maxResults = 1000,
      filterByTitle = true,
      industry,
      location
    } = req.body;

    // Validate required fields
    if (!companyName || !apolloUrl) {
      return res.status(400).json({
        error: 'Company name and Apollo URL are required'
      });
    }

    console.log(`[Integrated] Starting scrape for ${companyName}...`);

    // Step 1: Create company in Render DB
    let company;
    try {
      company = await renderClient.createCompany({
        company_name: companyName,
        apollo_url: apolloUrl,
        industry: industry || 'Technology',
        location: location || 'Germany',
        scrape_status: 'PENDING',
        created_at: new Date().toISOString()
      });
      console.log(`[Integrated] Company created in Render DB:`, company);
    } catch (dbError) {
      console.error('[Integrated] Failed to create company in DB:', dbError);
      // Continue anyway - scraping is more important
    }

    // Step 2: Start Apify scrape
    const input = {
      url: apolloUrl,
      maxResults,
      cleanOutput: false,
      fileName: `${companyName.replace(/\s+/g, '_').toLowerCase()}_contacts`
    };

    const actorId = process.env.APIFY_ACTOR_ID || 'jljBwyyQakqrL1wae';
    const run = await apifyClient.actor(actorId).call(input);

    console.log(`[Integrated] Apify run started: ${run.id}`);

    // Step 3: Wait for completion (async - don't block)
    processScrapingJob(run.id, companyName, filterByTitle);

    res.status(201).json({
      success: true,
      message: `Scraping job started for ${companyName}`,
      job: {
        id: run.id,
        companyName,
        status: 'running',
        datasetId: run.defaultDatasetId
      }
    });

  } catch (error) {
    console.error('[Integrated] Error:', error);
    res.status(500).json({
      error: error.message || 'Failed to start integrated scraping'
    });
  }
});

/**
 * GET /api/v1/integrated/company-status/:companyName
 * Get company and scraping status from Render DB
 */
router.get('/company-status/:companyName', async (req, res) => {
  try {
    const { companyName } = req.params;

    // Get company from Render DB
    const companies = await renderClient.getCompanies();
    const company = companies.companies?.find(
      c => c.company_name.toLowerCase() === companyName.toLowerCase()
    );

    if (!company) {
      return res.status(404).json({
        error: 'Company not found'
      });
    }

    // Get Apollo data if available
    const apolloData = await renderClient.getApolloData({
      company_id: company.id
    });

    res.json({
      success: true,
      company,
      apolloData: apolloData.apollo_data || [],
      totalContacts: apolloData.apollo_data?.length || 0
    });

  } catch (error) {
    console.error('[Integrated] Error:', error);
    res.status(500).json({
      error: error.message || 'Failed to get company status'
    });
  }
});

/**
 * POST /api/v1/integrated/batch-scrape
 * Scrape multiple companies and store in Render DB
 */
router.post('/batch-scrape', async (req, res) => {
  try {
    const { companies } = req.body;

    if (!companies || !Array.isArray(companies)) {
      return res.status(400).json({
        error: 'Companies array is required'
      });
    }

    const jobs = [];
    const errors = [];

    for (const company of companies) {
      try {
        // Create company in Render DB
        await renderClient.createCompany({
          company_name: company.name,
          apollo_url: company.url,
          industry: company.industry || 'Technology',
          location: company.location || 'Germany',
          scrape_status: 'PENDING'
        });

        // Start Apify scrape
        const input = {
          url: company.url,
          maxResults: company.maxResults || 1000,
          cleanOutput: false
        };

        const actorId = process.env.APIFY_ACTOR_ID || 'jljBwyyQakqrL1wae';
        const run = await apifyClient.actor(actorId).call(input);

        jobs.push({
          id: run.id,
          companyName: company.name,
          status: 'running'
        });

        // Process async
        processScrapingJob(run.id, company.name, true);

      } catch (error) {
        errors.push({
          company: company.name,
          error: error.message
        });
      }
    }

    res.status(201).json({
      success: true,
      message: `Started ${jobs.length} scraping jobs`,
      jobs,
      errors: errors.length > 0 ? errors : undefined
    });

  } catch (error) {
    console.error('[Integrated] Batch error:', error);
    res.status(500).json({
      error: error.message || 'Failed to start batch scraping'
    });
  }
});

/**
 * GET /api/v1/integrated/test-connection
 * Test connection to Render marketing DB
 */
router.get('/test-connection', async (req, res) => {
  try {
    const result = await renderClient.testConnection();
    res.json(result);
  } catch (error) {
    res.status(500).json({
      error: error.message || 'Connection test failed'
    });
  }
});

// Helper function to process scraping job asynchronously
async function processScrapingJob(runId, companyName, filterByTitle = true) {
  try {
    console.log(`[Integrated] Processing job ${runId} for ${companyName}...`);

    // Wait for Apify run to complete
    const finishedRun = await apifyClient.run(runId).waitForFinish();

    if (finishedRun.status !== 'SUCCEEDED') {
      console.error(`[Integrated] Run failed for ${companyName}:`, finishedRun.status);
      return;
    }

    console.log(`[Integrated] Run completed for ${companyName}`);

    // Fetch results from dataset
    const dataset = apifyClient.dataset(finishedRun.defaultDatasetId);
    const { items } = await dataset.listItems({ limit: 10000 });

    console.log(`[Integrated] Fetched ${items.length} contacts for ${companyName}`);

    // Filter contacts if needed
    let contacts = items;
    if (filterByTitle) {
      const targetTitles = [
        'CEO', 'CTO', 'CFO', 'COO', 'CMO',
        'Chief', 'President', 'Vice President', 'VP',
        'Director', 'Head of', 'Manager'
      ];
      
      contacts = items.filter(contact => 
        targetTitles.some(title => 
          contact.title && contact.title.toLowerCase().includes(title.toLowerCase())
        )
      );
      
      console.log(`[Integrated] Filtered to ${contacts.length} qualified contacts`);
    }

    // Submit to Render DB
    const result = await renderClient.submitApolloContacts(
      companyName, // Using company name as ID for now
      contacts,
      {
        apify_run_id: runId,
        filtered: filterByTitle,
        original_count: items.length,
        filtered_count: contacts.length
      }
    );

    console.log(`[Integrated] ✅ Successfully stored ${contacts.length} contacts for ${companyName}`);

  } catch (error) {
    console.error(`[Integrated] Error processing job ${runId}:`, error);
  }
}

module.exports = router;
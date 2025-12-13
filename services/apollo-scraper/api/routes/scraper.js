const express = require('express');
const router = express.Router();
const { ApifyClient } = require('apify-client');
const { neon } = require('@neondatabase/serverless');

// Initialize Apify client
const apifyClient = new ApifyClient({
  token: process.env.APIFY_API_KEY
});

// Store active scrape jobs (in production, use Redis or database)
const scrapeJobs = new Map();

/**
 * POST /api/v1/scraper/start
 * Start a new scraping job
 */
router.post('/start', async (req, res) => {
  try {
    const {
      url,
      companyId,
      companyName,
      maxResults = 1000,
      cleanOutput = false
    } = req.body;

    // Validate required fields
    if (!url) {
      return res.status(400).json({
        error: 'URL is required'
      });
    }

    if (!companyId || !companyName) {
      return res.status(400).json({
        error: 'Company ID and name are required'
      });
    }

    // Prepare input for Apollo scraper
    const input = {
      url,
      maxResults,
      cleanOutput,
      fileName: `${companyName.replace(/\s+/g, '_').toLowerCase()}_contacts`
    };

    console.log(`Starting scrape for ${companyName}...`);

    // Start the Apify actor
    const actorId = process.env.APIFY_ACTOR_ID || 'jljBwyyQakqrL1wae';
    const run = await apifyClient.actor(actorId).call(input);

    // Create job record
    const job = {
      id: run.id,
      companyId,
      companyName,
      url,
      status: 'running',
      startedAt: new Date().toISOString(),
      apifyRunId: run.id,
      datasetId: run.defaultDatasetId
    };

    // Store job (in memory for now, use database in production)
    scrapeJobs.set(run.id, job);

    // Update database if connected
    if (process.env.NEON_DATABASE_URL) {
      try {
        const sql = neon(process.env.NEON_DATABASE_URL);
        await sql`
          UPDATE marketing_company_intake 
          SET scrape_status = 'IN_PROGRESS',
              apify_run_id = ${run.id},
              last_scraped_at = NOW()
          WHERE id = ${companyId}
        `;
      } catch (dbError) {
        console.error('Database update failed:', dbError);
      }
    }

    res.status(201).json({
      success: true,
      job: {
        id: job.id,
        status: job.status,
        companyName: job.companyName,
        startedAt: job.startedAt
      },
      message: `Scraping job started for ${companyName}`
    });

  } catch (error) {
    console.error('Error starting scrape:', error);
    res.status(500).json({
      error: error.message || 'Failed to start scraping job'
    });
  }
});

/**
 * GET /api/v1/scraper/status/:jobId
 * Check the status of a scraping job
 */
router.get('/status/:jobId', async (req, res) => {
  try {
    const { jobId } = req.params;

    // Get job from storage
    let job = scrapeJobs.get(jobId);

    if (!job) {
      return res.status(404).json({
        error: 'Job not found'
      });
    }

    // Check current status from Apify
    const run = await apifyClient.run(jobId).get();
    
    // Update job status
    job.status = run.status.toLowerCase();
    job.finishedAt = run.finishedAt || null;
    job.stats = {
      computeUnits: run.stats?.computeUnits || 0,
      datasetItemCount: run.stats?.datasetItemCount || 0,
      duration: run.stats?.durationMillis || 0
    };

    // Update in storage
    scrapeJobs.set(jobId, job);

    // If completed, update database
    if (job.status === 'succeeded' && process.env.NEON_DATABASE_URL) {
      try {
        const sql = neon(process.env.NEON_DATABASE_URL);
        await sql`
          UPDATE marketing_company_intake 
          SET scrape_status = 'COMPLETE',
              total_contacts_found = ${job.stats.datasetItemCount}
          WHERE id = ${job.companyId}
        `;
      } catch (dbError) {
        console.error('Database update failed:', dbError);
      }
    }

    res.json({
      success: true,
      job: {
        id: job.id,
        status: job.status,
        companyName: job.companyName,
        startedAt: job.startedAt,
        finishedAt: job.finishedAt,
        stats: job.stats,
        datasetId: job.datasetId
      }
    });

  } catch (error) {
    console.error('Error checking status:', error);
    res.status(500).json({
      error: error.message || 'Failed to check job status'
    });
  }
});

/**
 * GET /api/v1/scraper/results/:jobId
 * Get the results of a completed scraping job
 */
router.get('/results/:jobId', async (req, res) => {
  try {
    const { jobId } = req.params;
    const { limit = 100, offset = 0, filterByTitle = true } = req.query;

    // Get job from storage
    const job = scrapeJobs.get(jobId);

    if (!job) {
      return res.status(404).json({
        error: 'Job not found'
      });
    }

    if (job.status !== 'succeeded') {
      return res.status(400).json({
        error: `Job is ${job.status}, not completed yet`
      });
    }

    // Fetch results from Apify dataset
    const dataset = apifyClient.dataset(job.datasetId);
    const { items } = await dataset.listItems({
      limit: parseInt(limit),
      offset: parseInt(offset)
    });

    // Filter by title if requested
    let results = items;
    if (filterByTitle === 'true' || filterByTitle === true) {
      const targetTitles = [
        'CEO', 'CTO', 'CFO', 'COO', 'CMO',
        'Chief', 'President', 'Vice President', 'VP',
        'Director', 'Head of', 'Manager'
      ];
      
      results = items.filter(contact => 
        targetTitles.some(title => 
          contact.title && contact.title.toLowerCase().includes(title.toLowerCase())
        )
      );
    }

    res.json({
      success: true,
      job: {
        id: job.id,
        companyName: job.companyName,
        status: job.status
      },
      pagination: {
        limit: parseInt(limit),
        offset: parseInt(offset),
        total: results.length
      },
      results
    });

  } catch (error) {
    console.error('Error fetching results:', error);
    res.status(500).json({
      error: error.message || 'Failed to fetch results'
    });
  }
});

/**
 * POST /api/v1/scraper/batch
 * Start multiple scraping jobs at once
 */
router.post('/batch', async (req, res) => {
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
        const input = {
          url: company.url,
          maxResults: company.maxResults || 1000,
          cleanOutput: company.cleanOutput || false,
          fileName: `${company.name.replace(/\s+/g, '_').toLowerCase()}_contacts`
        };

        const actorId = process.env.APIFY_ACTOR_ID || 'jljBwyyQakqrL1wae';
        const run = await apifyClient.actor(actorId).call(input);

        const job = {
          id: run.id,
          companyId: company.id,
          companyName: company.name,
          url: company.url,
          status: 'running',
          startedAt: new Date().toISOString(),
          apifyRunId: run.id,
          datasetId: run.defaultDatasetId
        };

        scrapeJobs.set(run.id, job);
        jobs.push(job);

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
      jobs: jobs.map(j => ({
        id: j.id,
        companyName: j.companyName,
        status: j.status
      })),
      errors: errors.length > 0 ? errors : undefined
    });

  } catch (error) {
    console.error('Error starting batch scrape:', error);
    res.status(500).json({
      error: error.message || 'Failed to start batch scraping'
    });
  }
});

/**
 * GET /api/v1/scraper/jobs
 * List all scraping jobs
 */
router.get('/jobs', async (req, res) => {
  try {
    const { status, limit = 50, offset = 0 } = req.query;

    let jobs = Array.from(scrapeJobs.values());

    // Filter by status if provided
    if (status) {
      jobs = jobs.filter(job => job.status === status);
    }

    // Sort by startedAt (newest first)
    jobs.sort((a, b) => new Date(b.startedAt) - new Date(a.startedAt));

    // Apply pagination
    const paginatedJobs = jobs.slice(
      parseInt(offset),
      parseInt(offset) + parseInt(limit)
    );

    res.json({
      success: true,
      pagination: {
        total: jobs.length,
        limit: parseInt(limit),
        offset: parseInt(offset)
      },
      jobs: paginatedJobs.map(job => ({
        id: job.id,
        companyName: job.companyName,
        status: job.status,
        startedAt: job.startedAt,
        finishedAt: job.finishedAt,
        stats: job.stats
      }))
    });

  } catch (error) {
    console.error('Error listing jobs:', error);
    res.status(500).json({
      error: error.message || 'Failed to list jobs'
    });
  }
});

module.exports = router;
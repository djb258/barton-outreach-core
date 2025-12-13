const express = require('express');
const axios = require('axios');
const router = express.Router();

// Apollo Scraper Service Integration (HEIR Hierarchical communication)
const APOLLO_SCRAPER_BASE_URL = process.env.APOLLO_SCRAPER_URL || 'http://localhost:3000';

/**
 * POST /api/v1/apollo-sync/trigger-scrape
 * Trigger Apollo scraper based on ingested company data (HEIR Integration)
 */
router.post('/trigger-scrape', async (req, res) => {
  try {
    const { companies, scrapeConfig = {} } = req.body;
    
    if (!companies || !Array.isArray(companies)) {
      return res.status(400).json({
        success: false,
        error: 'Companies array is required'
      });
    }

    console.log(`[Apollo-Sync] Triggering scrapes for ${companies.length} companies`);

    const results = [];
    const errors = [];

    // Process each company through Apollo scraper
    for (const company of companies) {
      try {
        // Validate company has required Apollo URL or can generate one
        const apolloUrl = company.apollo_url || await generateApolloUrl(company);
        
        if (!apolloUrl) {
          errors.push({
            company: company.company_name || company.name,
            error: 'No Apollo URL available or generatable'
          });
          continue;
        }

        // Build scraping request
        const scrapeRequest = {
          companyName: company.company_name || company.name,
          apolloUrl: apolloUrl,
          maxResults: scrapeConfig.maxResults || 1000,
          filterByTitle: scrapeConfig.filterByTitle !== false,
          industry: company.industry,
          location: company.location
        };

        // Call Apollo scraper service
        const response = await axios.post(
          `${APOLLO_SCRAPER_BASE_URL}/api/v1/integrated/scrape-and-store`,
          scrapeRequest,
          {
            headers: {
              'Content-Type': 'application/json',
              'X-Requested-With': 'csv-data-ingestor'
            },
            timeout: 10000 // 10 second timeout for initial request
          }
        );

        results.push({
          company: company.company_name || company.name,
          success: true,
          jobId: response.data.job?.id,
          status: response.data.job?.status,
          message: response.data.message
        });

        // HEIR Event: Publish scrape trigger
        publishEvent('apollo.scrape.triggered', {
          companyName: company.company_name || company.name,
          jobId: response.data.job?.id,
          triggeredBy: 'csv-ingestor'
        });

      } catch (error) {
        console.error(`[Apollo-Sync] Error for company ${company.company_name}:`, error.message);
        
        errors.push({
          company: company.company_name || company.name,
          error: error.message,
          status: error.response?.status
        });
      }
    }

    // HEIR Event: Publish sync completion
    publishEvent('apollo.sync.completed', {
      totalCompanies: companies.length,
      successful: results.length,
      failed: errors.length,
      successRate: results.length / companies.length
    });

    res.json({
      success: true,
      message: `Apollo sync initiated for ${companies.length} companies`,
      summary: {
        totalCompanies: companies.length,
        successful: results.length,
        failed: errors.length,
        successRate: Math.round((results.length / companies.length) * 100)
      },
      results,
      errors: errors.length > 0 ? errors : undefined
    });

  } catch (error) {
    console.error('[Apollo-Sync] Trigger error:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to trigger Apollo scrapes'
    });
  }
});

/**
 * GET /api/v1/apollo-sync/status
 * Get status of Apollo scraper jobs (HEIR Monitoring)
 */
router.get('/status', async (req, res) => {
  try {
    const { jobIds } = req.query;
    
    if (!jobIds) {
      // Get all jobs status
      const response = await axios.get(
        `${APOLLO_SCRAPER_BASE_URL}/api/v1/scraper/jobs`,
        { timeout: 5000 }
      );
      
      return res.json({
        success: true,
        jobs: response.data.jobs || [],
        summary: response.data.pagination || {}
      });
    }

    // Get specific job statuses
    const jobIdArray = Array.isArray(jobIds) ? jobIds : [jobIds];
    const statuses = [];

    for (const jobId of jobIdArray) {
      try {
        const response = await axios.get(
          `${APOLLO_SCRAPER_BASE_URL}/api/v1/scraper/status/${jobId}`,
          { timeout: 5000 }
        );
        
        statuses.push({
          jobId,
          success: true,
          ...response.data.job
        });
      } catch (error) {
        statuses.push({
          jobId,
          success: false,
          error: error.message,
          status: error.response?.status
        });
      }
    }

    res.json({
      success: true,
      statuses
    });

  } catch (error) {
    console.error('[Apollo-Sync] Status check error:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to check Apollo scraper status'
    });
  }
});

/**
 * POST /api/v1/apollo-sync/auto-sync
 * Automatically sync recent CSV ingestions with Apollo scraper
 */
router.post('/auto-sync', async (req, res) => {
  try {
    const { 
      timeRange = '1h', // 1 hour default
      dataType = 'companies',
      maxCompanies = 10
    } = req.body;

    console.log(`[Apollo-Sync] Auto-sync for last ${timeRange}, max ${maxCompanies} companies`);

    // Get recent ingestions (this would query your ingestion log/database)
    const recentCompanies = await getRecentIngestions(timeRange, dataType, maxCompanies);

    if (recentCompanies.length === 0) {
      return res.json({
        success: true,
        message: 'No recent company ingestions found',
        companiesFound: 0
      });
    }

    // Filter companies that need Apollo URLs
    const companiesNeedingScraping = recentCompanies.filter(company => {
      return company.company_name && (
        !company.apollo_url || 
        !company.contacts_scraped || 
        company.last_scraped < Date.now() - (24 * 60 * 60 * 1000) // 24h ago
      );
    });

    if (companiesNeedingScraping.length === 0) {
      return res.json({
        success: true,
        message: 'All recent companies already have up-to-date Apollo data',
        companiesChecked: recentCompanies.length
      });
    }

    // Trigger scraping for eligible companies
    const scrapeConfig = {
      maxResults: 500, // Smaller batches for auto-sync
      filterByTitle: true
    };

    const syncResult = await triggerApolloScrapes(companiesNeedingScraping, scrapeConfig);

    res.json({
      success: true,
      message: `Auto-sync completed for ${companiesNeedingScraping.length} companies`,
      summary: {
        companiesFound: recentCompanies.length,
        eligibleForScraping: companiesNeedingScraping.length,
        scrapingTriggered: syncResult.successful,
        failed: syncResult.failed
      },
      details: syncResult
    });

  } catch (error) {
    console.error('[Apollo-Sync] Auto-sync error:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Auto-sync failed'
    });
  }
});

/**
 * POST /api/v1/apollo-sync/generate-urls
 * Generate Apollo URLs for companies missing them (HEIR Intelligence)
 */
router.post('/generate-urls', async (req, res) => {
  try {
    const { companies } = req.body;
    
    if (!companies || !Array.isArray(companies)) {
      return res.status(400).json({
        success: false,
        error: 'Companies array is required'
      });
    }

    const results = [];

    for (const company of companies) {
      try {
        const apolloUrl = await generateApolloUrl(company);
        
        results.push({
          companyName: company.company_name || company.name,
          success: !!apolloUrl,
          apolloUrl: apolloUrl,
          confidence: calculateUrlConfidence(company, apolloUrl)
        });

      } catch (error) {
        results.push({
          companyName: company.company_name || company.name,
          success: false,
          error: error.message
        });
      }
    }

    res.json({
      success: true,
      message: `Generated Apollo URLs for ${results.filter(r => r.success).length} companies`,
      results
    });

  } catch (error) {
    console.error('[Apollo-Sync] URL generation error:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to generate Apollo URLs'
    });
  }
});

/**
 * GET /api/v1/apollo-sync/health
 * Check Apollo scraper service connectivity
 */
router.get('/health', async (req, res) => {
  try {
    const response = await axios.get(
      `${APOLLO_SCRAPER_BASE_URL}/api/v1/health`,
      { timeout: 5000 }
    );

    res.json({
      success: true,
      apolloScraperStatus: 'connected',
      apolloScraperUrl: APOLLO_SCRAPER_BASE_URL,
      apolloScraperHealth: response.data
    });

  } catch (error) {
    res.status(503).json({
      success: false,
      apolloScraperStatus: 'disconnected',
      apolloScraperUrl: APOLLO_SCRAPER_BASE_URL,
      error: error.message
    });
  }
});

// Helper functions

async function generateApolloUrl(company) {
  try {
    // Intelligent Apollo URL generation based on company data
    const baseUrl = 'https://app.apollo.io/#/people';
    const params = new URLSearchParams();

    // Add location filter if available
    if (company.location) {
      params.append('personLocations[]', company.location);
    }

    // Add company name filter if available
    if (company.company_name || company.name) {
      params.append('organizationNames[]', company.company_name || company.name);
    }

    // Add industry filter if available
    if (company.industry) {
      // This would need mapping to Apollo industry IDs
      // For now, we'll use a simple approach
    }

    // Add employee count range if available
    if (company.employee_count || company.employees) {
      const count = company.employee_count || company.employees;
      if (typeof count === 'number') {
        const ranges = getEmployeeRange(count);
        params.append('organizationNumEmployeesRanges[]', ranges);
      }
    }

    // Default sorting
    params.append('page', '1');
    params.append('sortByField', 'recommendations_score');

    const url = `${baseUrl}?${params.toString()}`;
    
    console.log(`[Apollo-Sync] Generated URL for ${company.company_name}: ${url}`);
    return url;

  } catch (error) {
    console.error('[Apollo-Sync] URL generation error:', error);
    return null;
  }
}

function getEmployeeRange(count) {
  // Convert employee count to Apollo range format
  if (count <= 10) return '1%2C10';
  if (count <= 50) return '11%2C50';
  if (count <= 200) return '51%2C200';
  if (count <= 1000) return '201%2C1000';
  if (count <= 5000) return '1001%2C5000';
  return '5001%2C10000';
}

function calculateUrlConfidence(company, apolloUrl) {
  let confidence = 0;
  
  if (apolloUrl) confidence += 20;
  if (company.company_name) confidence += 30;
  if (company.location) confidence += 25;
  if (company.industry) confidence += 15;
  if (company.employee_count) confidence += 10;
  
  return Math.min(confidence, 100);
}

async function getRecentIngestions(timeRange, dataType, maxCompanies) {
  // This would query your ingestion log/database
  // For now, return mock data
  console.log(`[Apollo-Sync] Getting recent ingestions: ${timeRange}, ${dataType}, ${maxCompanies}`);
  
  // In production, this would be a real database query
  return [];
}

async function triggerApolloScrapes(companies, config) {
  try {
    const response = await axios.post(
      `${APOLLO_SCRAPER_BASE_URL}/api/v1/integrated/batch-scrape`,
      {
        companies: companies.map(c => ({
          name: c.company_name || c.name,
          url: c.apollo_url,
          industry: c.industry,
          location: c.location,
          maxResults: config.maxResults
        }))
      },
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 15000
      }
    );

    return {
      successful: response.data.jobs?.length || 0,
      failed: response.data.errors?.length || 0,
      jobs: response.data.jobs || [],
      errors: response.data.errors || []
    };

  } catch (error) {
    throw new Error(`Failed to trigger Apollo scrapes: ${error.message}`);
  }
}

function publishEvent(eventType, payload) {
  // HEIR Event-driven pattern
  console.log(`[HEIR-Event] ${eventType}:`, JSON.stringify(payload, null, 2));
  
  // In production, connect to event bus
  // eventBus.publish(eventType, { service: 'csv-data-ingestor', ...payload });
}

module.exports = router;
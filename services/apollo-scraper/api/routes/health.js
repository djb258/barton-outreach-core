const express = require('express');
const router = express.Router();
const { renderClient } = require('../clients/renderClient');

/**
 * GET /api/v1/health
 * Health check endpoint
 */
router.get('/', async (req, res) => {
  try {
    // Check Render DB connection
    const renderHealth = await renderClient.checkHealth().catch(err => ({
      status: 'error',
      message: err.message
    }));

    // Check Apify API
    const apifyStatus = process.env.APIFY_API_KEY ? 'configured' : 'not configured';

    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      services: {
        api: 'running',
        renderDB: renderHealth.status || 'unknown',
        apify: apifyStatus
      },
      environment: {
        node: process.version,
        platform: process.platform,
        uptime: process.uptime()
      }
    });
  } catch (error) {
    res.status(500).json({
      status: 'unhealthy',
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/v1/health/render
 * Check Render DB health
 */
router.get('/render', async (req, res) => {
  try {
    const health = await renderClient.checkHealth();
    res.json(health);
  } catch (error) {
    res.status(503).json({
      status: 'error',
      message: 'Render DB is not accessible',
      error: error.message
    });
  }
});

/**
 * GET /api/v1/health/database
 * Check database status
 */
router.get('/database', async (req, res) => {
  try {
    const status = await renderClient.getDatabaseStatus();
    res.json(status);
  } catch (error) {
    res.status(503).json({
      status: 'error',
      message: 'Database is not accessible',
      error: error.message
    });
  }
});

module.exports = router;
const express = require('express');
const router = express.Router();
const { renderClient } = require('../clients/renderClient');

/**
 * GET /api/v1/results/apollo
 * Get Apollo scraping results from Render marketing DB
 */
router.get('/apollo', async (req, res) => {
  try {
    const apolloData = await renderClient.getApolloData(req.query);
    res.json(apolloData);
  } catch (error) {
    console.error('Error fetching Apollo data:', error);
    res.status(500).json({
      error: error.message || 'Failed to fetch Apollo data'
    });
  }
});

/**
 * POST /api/v1/results/apollo
 * Submit Apollo scraping results to Render marketing DB
 */
router.post('/apollo', async (req, res) => {
  try {
    const result = await renderClient.submitApolloData(req.body);
    res.status(201).json(result);
  } catch (error) {
    console.error('Error submitting Apollo data:', error);
    res.status(500).json({
      error: error.message || 'Failed to submit Apollo data'
    });
  }
});

module.exports = router;
const express = require('express');
const router = express.Router();
const InstantlyService = require('../services/instantly');

router.get('/', async (req, res) => {
  try {
    const connection = await InstantlyService.testConnection();
    const limits = await InstantlyService.getAccountLimits();
    
    res.json({
      service: 'instantly-integration',
      status: 'healthy',
      timestamp: new Date().toISOString(),
      connection,
      limits,
      architecture: 'HEIR',
      version: '1.0.0'
    });
  } catch (error) {
    res.status(500).json({
      service: 'instantly-integration',
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

module.exports = router;
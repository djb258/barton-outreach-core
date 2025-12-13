const express = require('express');
const router = express.Router();
const HeyReachService = require('../services/heyreach');

router.get('/', async (req, res) => {
  try {
    const connection = await HeyReachService.testConnection();
    const limits = await HeyReachService.getAccountLimits();
    
    res.json({
      service: 'heyreach-integration',
      status: 'healthy',
      timestamp: new Date().toISOString(),
      connection,
      limits,
      architecture: 'HEIR',
      version: '1.0.0'
    });
  } catch (error) {
    res.status(500).json({
      service: 'heyreach-integration',
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

module.exports = router;
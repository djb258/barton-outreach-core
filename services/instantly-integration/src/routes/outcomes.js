const express = require('express');
const router = express.Router();
const OutcomeTracker = require('../services/outcomeTracker');

router.get('/company/:companyId', async (req, res) => {
  try {
    const { companyId } = req.params;
    const outcomes = await OutcomeTracker.getOutcomesByCompany(companyId);
    
    res.json({
      success: true,
      outcomes
    });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to get company outcomes',
      details: error.message
    });
  }
});

router.get('/slot-performance', async (req, res) => {
  try {
    const performance = await OutcomeTracker.getSlotPerformance();
    
    res.json({
      success: true,
      performance
    });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to get slot performance',
      details: error.message
    });
  }
});

router.get('/export', async (req, res) => {
  try {
    const { format = 'json' } = req.query;
    const data = await OutcomeTracker.exportOutcomes(format);
    
    if (format === 'csv') {
      res.setHeader('Content-Type', 'text/csv');
      res.setHeader('Content-Disposition', 'attachment; filename=outcomes.csv');
    }
    
    res.send(data);
  } catch (error) {
    res.status(500).json({
      error: 'Failed to export outcomes',
      details: error.message
    });
  }
});

module.exports = router;
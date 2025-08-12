const express = require('express');
const router = express.Router();
const InstantlyService = require('../services/instantly');
const OutcomeTracker = require('../services/outcomeTracker');

router.get('/:email/status', async (req, res) => {
  try {
    const { email } = req.params;
    const status = await InstantlyService.getEmailStatus(email);
    
    res.json({
      success: true,
      status
    });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to get contact status',
      details: error.message
    });
  }
});

router.get('/:contactId/engagement', async (req, res) => {
  try {
    const { contactId } = req.params;
    const engagement = await OutcomeTracker.getEngagementScore(contactId);
    
    res.json({
      success: true,
      engagement
    });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to get engagement score',
      details: error.message
    });
  }
});

module.exports = router;
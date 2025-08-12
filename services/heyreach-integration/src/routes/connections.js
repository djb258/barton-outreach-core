const express = require('express');
const router = express.Router();
const HeyReachService = require('../services/heyreach');
const OutcomeTracker = require('../services/outcomeTracker');

router.get('/:leadId/status', async (req, res) => {
  try {
    const { leadId } = req.params;
    const status = await HeyReachService.getLeadStatus(leadId);
    
    res.json({
      success: true,
      status
    });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to get lead status',
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

router.get('/network-growth', async (req, res) => {
  try {
    const growth = await OutcomeTracker.getLinkedInNetworkGrowth();
    
    res.json({
      success: true,
      growth
    });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to get network growth',
      details: error.message
    });
  }
});

module.exports = router;
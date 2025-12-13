const express = require('express');
const router = express.Router();
const HeyReachService = require('../services/heyreach');
const OutcomeTracker = require('../services/outcomeTracker');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [new winston.transports.Console()]
});

router.post('/create', async (req, res) => {
  try {
    const {
      name,
      type,
      dailyLimit,
      timezone,
      days,
      startHour,
      endHour,
      connectionMessage,
      followUpMessages
    } = req.body;

    const result = await HeyReachService.createCampaign({
      name,
      type,
      dailyLimit,
      timezone,
      days,
      startHour,
      endHour,
      connectionMessage,
      followUpMessages
    });

    res.json({
      success: true,
      campaign: result
    });
  } catch (error) {
    logger.error('Failed to create campaign', error);
    res.status(500).json({
      error: 'Failed to create campaign',
      details: error.message
    });
  }
});

router.post('/:campaignId/leads', async (req, res) => {
  try {
    const { campaignId } = req.params;
    const { leads } = req.body;

    const result = await HeyReachService.addLeadsToCampaign(campaignId, leads);

    res.json({
      success: true,
      result
    });
  } catch (error) {
    logger.error('Failed to add leads to campaign', error);
    res.status(500).json({
      error: 'Failed to add leads',
      details: error.message
    });
  }
});

router.post('/:campaignId/start', async (req, res) => {
  try {
    const { campaignId } = req.params;
    
    const result = await HeyReachService.startCampaign(campaignId);

    res.json({
      success: true,
      result
    });
  } catch (error) {
    logger.error('Failed to start campaign', error);
    res.status(500).json({
      error: 'Failed to start campaign',
      details: error.message
    });
  }
});

router.post('/:campaignId/pause', async (req, res) => {
  try {
    const { campaignId } = req.params;
    
    const result = await HeyReachService.pauseCampaign(campaignId);

    res.json({
      success: true,
      result
    });
  } catch (error) {
    logger.error('Failed to pause campaign', error);
    res.status(500).json({
      error: 'Failed to pause campaign',
      details: error.message
    });
  }
});

router.get('/:campaignId/stats', async (req, res) => {
  try {
    const { campaignId } = req.params;
    
    const stats = await HeyReachService.getCampaignStats(campaignId);
    const performance = await OutcomeTracker.getCampaignPerformance(campaignId);

    res.json({
      success: true,
      stats,
      performance
    });
  } catch (error) {
    logger.error('Failed to get campaign stats', error);
    res.status(500).json({
      error: 'Failed to get stats',
      details: error.message
    });
  }
});

router.post('/webhook', async (req, res) => {
  try {
    const webhookData = req.body;
    
    const outcome = await HeyReachService.handleWebhook(webhookData);
    await OutcomeTracker.trackOutcome(outcome);

    res.json({
      success: true,
      message: 'Webhook processed'
    });
  } catch (error) {
    logger.error('Failed to process webhook', error);
    res.status(500).json({
      error: 'Webhook processing failed',
      details: error.message
    });
  }
});

module.exports = router;
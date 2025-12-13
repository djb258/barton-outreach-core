const express = require('express');
const router = express.Router();
const InstantlyService = require('../services/instantly');
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
      fromName,
      fromEmail,
      replyTo,
      subject,
      bodyHtml,
      bodyText,
      schedule
    } = req.body;

    const result = await InstantlyService.createCampaign({
      name,
      fromName,
      fromEmail,
      replyTo,
      subject,
      bodyHtml,
      bodyText,
      schedule
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

router.post('/:campaignId/contacts', async (req, res) => {
  try {
    const { campaignId } = req.params;
    const { contacts } = req.body;

    const result = await InstantlyService.addContactsToCampaign(campaignId, contacts);

    res.json({
      success: true,
      result
    });
  } catch (error) {
    logger.error('Failed to add contacts to campaign', error);
    res.status(500).json({
      error: 'Failed to add contacts',
      details: error.message
    });
  }
});

router.post('/:campaignId/launch', async (req, res) => {
  try {
    const { campaignId } = req.params;
    
    const result = await InstantlyService.launchCampaign(campaignId);

    res.json({
      success: true,
      result
    });
  } catch (error) {
    logger.error('Failed to launch campaign', error);
    res.status(500).json({
      error: 'Failed to launch campaign',
      details: error.message
    });
  }
});

router.post('/:campaignId/pause', async (req, res) => {
  try {
    const { campaignId } = req.params;
    
    const result = await InstantlyService.pauseCampaign(campaignId);

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
    
    const stats = await InstantlyService.getCampaignStats(campaignId);
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
    
    const outcome = await InstantlyService.handleWebhook(webhookData);
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
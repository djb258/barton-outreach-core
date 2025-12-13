const express = require('express');
const router = express.Router();
const HeyReachService = require('../services/heyreach');

router.post('/:leadId/send', async (req, res) => {
  try {
    const { leadId } = req.params;
    const { message } = req.body;
    
    const result = await HeyReachService.sendMessage(leadId, message);
    
    res.json({
      success: true,
      result
    });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to send message',
      details: error.message
    });
  }
});

router.post('/sequences/create', async (req, res) => {
  try {
    const sequenceData = req.body;
    
    const result = await HeyReachService.createMessageSequence(sequenceData);
    
    res.json({
      success: true,
      sequence: result
    });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to create sequence',
      details: error.message
    });
  }
});

module.exports = router;
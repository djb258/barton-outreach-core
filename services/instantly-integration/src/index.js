require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const winston = require('winston');
const InstantlyMCPManager = require('./services/mcpManager');
const OutcomeTracker = require('./services/outcomeTracker');
const campaignRoutes = require('./routes/campaigns');
const contactRoutes = require('./routes/contacts');
const outcomeRoutes = require('./routes/outcomes');
const healthRoutes = require('./routes/health');

const app = express();
const PORT = process.env.PORT || 3006;

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

app.use(helmet());
app.use(cors());
app.use(express.json({ limit: '10mb' }));

app.use((req, res, next) => {
  logger.info(`${req.method} ${req.path}`);
  next();
});

app.use('/api/campaigns', campaignRoutes);
app.use('/api/contacts', contactRoutes);
app.use('/api/outcomes', outcomeRoutes);
app.use('/health', healthRoutes);

app.use((err, req, res, next) => {
  logger.error('Error:', err);
  res.status(err.status || 500).json({
    error: err.message || 'Internal server error',
    details: process.env.NODE_ENV === 'development' ? err.stack : undefined
  });
});

app.listen(PORT, async () => {
  logger.info(`Instantly Integration Service running on port ${PORT}`);
  logger.info('HEIR Architecture: Enabled');
  logger.info('Email Outreach: Ready');
  logger.info('Outcome Tracking: Active');
  
  // Start MCP server
  try {
    await InstantlyMCPManager.start();
    logger.info('✅ Instantly MCP server started');
  } catch (error) {
    logger.error('❌ Failed to start Instantly MCP server:', error);
    logger.info('⚠️  Service will run without MCP integration');
  }
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  logger.info('Received SIGTERM, shutting down gracefully...');
  await InstantlyMCPManager.stop();
  process.exit(0);
});

process.on('SIGINT', async () => {
  logger.info('Received SIGINT, shutting down gracefully...');
  await InstantlyMCPManager.stop();
  process.exit(0);
});
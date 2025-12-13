require('dotenv').config();
const HeyReachService = require('./src/services/heyreach');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.simple(),
  transports: [new winston.transports.Console()]
});

async function setupHeyReach() {
  logger.info('🚀 Setting up HeyReach Integration Service...');
  
  // Check environment variables
  const requiredEnvVars = [
    'HEYREACH_API_KEY',
    'NEON_DATABASE_URL'
  ];
  
  const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);
  
  if (missingVars.length > 0) {
    logger.error('❌ Missing required environment variables:');
    missingVars.forEach(varName => {
      logger.error(`   - ${varName}`);
    });
    logger.info('\n📝 Please copy .env.example to .env and fill in the required values');
    process.exit(1);
  }
  
  logger.info('✅ Environment variables configured');
  
  // Test HeyReach API connection
  try {
    logger.info('🔌 Testing HeyReach API connection...');
    const connectionTest = await HeyReachService.testConnection();
    
    if (connectionTest.success && connectionTest.connected) {
      logger.info('✅ HeyReach API connection successful');
      logger.info(`   Account: ${connectionTest.accountEmail}`);
      logger.info(`   Plan: ${connectionTest.plan}`);
      logger.info(`   LinkedIn Accounts: ${connectionTest.linkedInAccounts.length}`);
      
      // Get account limits
      const limits = await HeyReachService.getAccountLimits();
      if (limits.success) {
        logger.info('📊 Account limits:');
        logger.info(`   Daily connection limit: ${limits.limits.dailyConnectionLimit}`);
        logger.info(`   Daily message limit: ${limits.limits.dailyMessageLimit}`);
        logger.info(`   Connections sent today: ${limits.limits.connectionsToday}`);
        logger.info(`   Messages sent today: ${limits.limits.messagesToday}`);
        logger.info(`   LinkedIn accounts connected: ${limits.limits.linkedInAccounts.length}`);
      }
    } else {
      logger.error('❌ HeyReach API connection failed');
      logger.error(`   Error: ${connectionTest.error}`);
      process.exit(1);
    }
  } catch (error) {
    logger.error('❌ Failed to connect to HeyReach API');
    logger.error(`   Error: ${error.message}`);
    logger.info('\n🔑 Please check your HEYREACH_API_KEY in the .env file');
    process.exit(1);
  }
  
  logger.info('\n🎉 HeyReach Integration Service setup complete!');
  logger.info('\n📋 Next steps:');
  logger.info('1. Run: npm run dev (to start development server)');
  logger.info('2. Test endpoint: http://localhost:3007/health');
  logger.info('3. View API docs: http://localhost:3007/api-docs (when implemented)');
  logger.info('\n🔗 Integration endpoints ready:');
  logger.info('   POST /api/campaigns/create - Create new LinkedIn campaign');
  logger.info('   POST /api/campaigns/:id/leads - Add leads to campaign');
  logger.info('   POST /api/campaigns/:id/start - Start campaign');
  logger.info('   GET  /api/campaigns/:id/stats - Get campaign statistics');
  logger.info('   POST /api/messages/:leadId/send - Send direct message');
  logger.info('   POST /api/campaigns/webhook - Webhook for outcome tracking');
}

if (require.main === module) {
  setupHeyReach().catch(error => {
    logger.error('Setup failed:', error);
    process.exit(1);
  });
}

module.exports = setupHeyReach;
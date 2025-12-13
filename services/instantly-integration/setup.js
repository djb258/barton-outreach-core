require('dotenv').config();
const InstantlyService = require('./src/services/instantly');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.simple(),
  transports: [new winston.transports.Console()]
});

async function setupInstantly() {
  logger.info('🚀 Setting up Instantly Integration Service...');
  
  // Check environment variables
  const requiredEnvVars = [
    'INSTANTLY_API_KEY',
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
  
  // Test Instantly API connection
  try {
    logger.info('🔌 Testing Instantly API connection...');
    const connectionTest = await InstantlyService.testConnection();
    
    if (connectionTest.success && connectionTest.connected) {
      logger.info('✅ Instantly API connection successful');
      logger.info(`   Account: ${connectionTest.accountEmail}`);
      logger.info(`   Plan: ${connectionTest.plan}`);
      
      // Get account limits
      const limits = await InstantlyService.getAccountLimits();
      if (limits.success) {
        logger.info('📊 Account limits:');
        logger.info(`   Daily email limit: ${limits.limits.emailsPerDay}`);
        logger.info(`   Emails sent today: ${limits.limits.emailsSentToday}`);
        logger.info(`   Active campaigns: ${limits.limits.activeCampaigns}`);
      }
    } else {
      logger.error('❌ Instantly API connection failed');
      logger.error(`   Error: ${connectionTest.error}`);
      process.exit(1);
    }
  } catch (error) {
    logger.error('❌ Failed to connect to Instantly API');
    logger.error(`   Error: ${error.message}`);
    logger.info('\n🔑 Please check your INSTANTLY_API_KEY in the .env file');
    process.exit(1);
  }
  
  logger.info('\n🎉 Instantly Integration Service setup complete!');
  logger.info('\n📋 Next steps:');
  logger.info('1. Run: npm run dev (to start development server)');
  logger.info('2. Test endpoint: http://localhost:3006/health');
  logger.info('3. View API docs: http://localhost:3006/api-docs (when implemented)');
  logger.info('\n🔗 Integration endpoints ready:');
  logger.info('   POST /api/campaigns/create - Create new campaign');
  logger.info('   POST /api/campaigns/:id/contacts - Add contacts to campaign');
  logger.info('   POST /api/campaigns/:id/launch - Launch campaign');
  logger.info('   GET  /api/campaigns/:id/stats - Get campaign statistics');
  logger.info('   POST /api/campaigns/webhook - Webhook for outcome tracking');
}

if (require.main === module) {
  setupInstantly().catch(error => {
    logger.error('Setup failed:', error);
    process.exit(1);
  });
}

module.exports = setupInstantly;
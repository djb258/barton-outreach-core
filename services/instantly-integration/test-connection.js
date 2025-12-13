require('dotenv').config();
const InstantlyService = require('./src/services/instantly');

async function testInstantlyConnection() {
  console.log('🔌 Testing Instantly API Connection...\n');
  
  try {
    // Test basic connection
    const connectionResult = await InstantlyService.testConnection();
    
    if (connectionResult.success) {
      console.log('✅ Connection successful!');
      console.log(`   Account Email: ${connectionResult.accountEmail}`);
      console.log(`   Plan: ${connectionResult.plan}`);
      console.log(`   Status: ${connectionResult.connected ? 'Active' : 'Inactive'}\n`);
      
      // Get account limits
      console.log('📊 Checking account limits...');
      const limitsResult = await InstantlyService.getAccountLimits();
      
      if (limitsResult.success) {
        console.log('✅ Account limits retrieved:');
        console.log(`   Daily email limit: ${limitsResult.limits.emailsPerDay}`);
        console.log(`   Emails sent today: ${limitsResult.limits.emailsSentToday}`);
        console.log(`   Remaining today: ${limitsResult.limits.emailsPerDay - limitsResult.limits.emailsSentToday}`);
        console.log(`   Campaigns limit: ${limitsResult.limits.campaignsLimit}`);
        console.log(`   Active campaigns: ${limitsResult.limits.activeCampaigns}`);
        console.log(`   Account status: ${limitsResult.limits.accountStatus}\n`);
        
        // Check if ready for campaigns
        const canSendEmails = limitsResult.limits.emailsPerDay > limitsResult.limits.emailsSentToday;
        const canCreateCampaigns = limitsResult.limits.campaignsLimit > limitsResult.limits.activeCampaigns;
        
        if (canSendEmails && canCreateCampaigns) {
          console.log('🚀 Ready to create and run campaigns!');
        } else {
          console.log('⚠️  Account limitations detected:');
          if (!canSendEmails) console.log('   - Daily email limit reached');
          if (!canCreateCampaigns) console.log('   - Campaign limit reached');
        }
        
      } else {
        console.log('❌ Failed to get account limits');
      }
      
    } else {
      console.log('❌ Connection failed');
      console.log(`   Error: ${connectionResult.error}`);
    }
    
  } catch (error) {
    console.log('❌ Connection test failed');
    console.log(`   Error: ${error.message}`);
    console.log('\n🔧 Troubleshooting:');
    console.log('1. Check your INSTANTLY_API_KEY in .env file');
    console.log('2. Ensure API key has proper permissions');
    console.log('3. Verify your Instantly account is active');
  }
}

// Test sample campaign creation (dry run)
async function testCampaignCreation() {
  console.log('\n🧪 Testing campaign creation (sample data)...');
  
  try {
    const sampleCampaign = {
      name: 'Test Campaign - ' + new Date().toISOString(),
      fromName: 'Test User',
      fromEmail: 'test@example.com',
      replyTo: 'replies@example.com',
      subject: 'Test Subject',
      bodyHtml: '<p>This is a test email</p>',
      bodyText: 'This is a test email',
      schedule: {
        timezone: 'America/New_York',
        days: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
        start_hour: 9,
        end_hour: 17,
        emails_per_day: 10
      }
    };
    
    // Note: This would actually create a campaign if uncommented
    console.log('📋 Sample campaign configuration:');
    console.log(`   Name: ${sampleCampaign.name}`);
    console.log(`   From: ${sampleCampaign.fromName} <${sampleCampaign.fromEmail}>`);
    console.log(`   Subject: ${sampleCampaign.subject}`);
    console.log(`   Daily limit: ${sampleCampaign.schedule.emails_per_day}`);
    console.log('\n⚠️  Campaign creation test skipped (to avoid creating actual campaigns)');
    console.log('   Uncomment the actual API call in test-connection.js to test campaign creation');
    
  } catch (error) {
    console.log('❌ Campaign creation test failed');
    console.log(`   Error: ${error.message}`);
  }
}

async function runTests() {
  await testInstantlyConnection();
  await testCampaignCreation();
  
  console.log('\n✅ Connection tests completed!');
  console.log('\n📚 Next steps:');
  console.log('1. Start the service: npm run dev');
  console.log('2. Test health endpoint: GET http://localhost:3006/health');
  console.log('3. Create your first campaign via API');
}

if (require.main === module) {
  runTests().catch(console.error);
}

module.exports = { testInstantlyConnection, testCampaignCreation };
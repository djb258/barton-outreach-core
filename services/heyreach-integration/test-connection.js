require('dotenv').config();
const HeyReachService = require('./src/services/heyreach');

async function testHeyReachConnection() {
  console.log('🔌 Testing HeyReach API Connection...\n');
  
  try {
    // Test basic connection
    const connectionResult = await HeyReachService.testConnection();
    
    if (connectionResult.success) {
      console.log('✅ Connection successful!');
      console.log(`   Account Email: ${connectionResult.accountEmail}`);
      console.log(`   Plan: ${connectionResult.plan}`);
      console.log(`   Status: ${connectionResult.connected ? 'Active' : 'Inactive'}`);
      console.log(`   LinkedIn Accounts: ${connectionResult.linkedInAccounts?.length || 0}\n`);
      
      // Get account limits
      console.log('📊 Checking account limits...');
      const limitsResult = await HeyReachService.getAccountLimits();
      
      if (limitsResult.success) {
        console.log('✅ Account limits retrieved:');
        console.log(`   Daily connection limit: ${limitsResult.limits.dailyConnectionLimit}`);
        console.log(`   Daily message limit: ${limitsResult.limits.dailyMessageLimit}`);
        console.log(`   Connections sent today: ${limitsResult.limits.connectionsToday}`);
        console.log(`   Messages sent today: ${limitsResult.limits.messagesToday}`);
        console.log(`   Remaining connections: ${limitsResult.limits.dailyConnectionLimit - limitsResult.limits.connectionsToday}`);
        console.log(`   Remaining messages: ${limitsResult.limits.dailyMessageLimit - limitsResult.limits.messagesToday}`);
        console.log(`   Account status: ${limitsResult.limits.accountStatus}\n`);
        
        // Check LinkedIn accounts
        if (limitsResult.limits.linkedInAccounts && limitsResult.limits.linkedInAccounts.length > 0) {
          console.log('💼 LinkedIn accounts connected:');
          limitsResult.limits.linkedInAccounts.forEach((account, index) => {
            console.log(`   ${index + 1}. ${account.name} (${account.status})`);
          });
        } else {
          console.log('⚠️  No LinkedIn accounts connected');
          console.log('   Please connect LinkedIn accounts in your HeyReach dashboard');
        }
        
        // Check if ready for campaigns
        const canSendConnections = limitsResult.limits.dailyConnectionLimit > limitsResult.limits.connectionsToday;
        const canSendMessages = limitsResult.limits.dailyMessageLimit > limitsResult.limits.messagesToday;
        const hasLinkedInAccounts = limitsResult.limits.linkedInAccounts && limitsResult.limits.linkedInAccounts.length > 0;
        
        console.log('\n🚀 Campaign readiness check:');
        if (canSendConnections && canSendMessages && hasLinkedInAccounts) {
          console.log('✅ Ready to create and run LinkedIn campaigns!');
        } else {
          console.log('⚠️  Campaign limitations detected:');
          if (!canSendConnections) console.log('   - Daily connection limit reached');
          if (!canSendMessages) console.log('   - Daily message limit reached');
          if (!hasLinkedInAccounts) console.log('   - No LinkedIn accounts connected');
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
    console.log('1. Check your HEYREACH_API_KEY in .env file');
    console.log('2. Ensure API key has proper permissions');
    console.log('3. Verify your HeyReach account is active');
    console.log('4. Make sure LinkedIn accounts are connected in HeyReach dashboard');
  }
}

// Test sample campaign creation (dry run)
async function testCampaignCreation() {
  console.log('\n🧪 Testing campaign creation (sample data)...');
  
  try {
    const sampleCampaign = {
      name: 'Test LinkedIn Campaign - ' + new Date().toISOString(),
      type: 'connection_request',
      dailyLimit: 10,
      timezone: 'America/New_York',
      days: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
      startHour: 9,
      endHour: 17,
      connectionMessage: 'Hi {firstName}, I came across your profile and would love to connect with you. Looking forward to networking!',
      followUpMessages: [
        {
          content: 'Thanks for connecting! I noticed we both work in {industry}. Would love to learn more about your experience.',
          delayDays: 3
        },
        {
          content: 'Hi {firstName}, I thought you might be interested in our latest insights on {industry}. Would you like to schedule a brief call?',
          delayDays: 7
        }
      ]
    };
    
    console.log('📋 Sample campaign configuration:');
    console.log(`   Name: ${sampleCampaign.name}`);
    console.log(`   Type: ${sampleCampaign.type}`);
    console.log(`   Daily limit: ${sampleCampaign.dailyLimit} connections`);
    console.log(`   Schedule: ${sampleCampaign.days.join(', ')} ${sampleCampaign.startHour}:00-${sampleCampaign.endHour}:00`);
    console.log(`   Follow-up messages: ${sampleCampaign.followUpMessages.length}`);
    console.log('\n⚠️  Campaign creation test skipped (to avoid creating actual campaigns)');
    console.log('   Uncomment the actual API call in test-connection.js to test campaign creation');
    
  } catch (error) {
    console.log('❌ Campaign creation test failed');
    console.log(`   Error: ${error.message}`);
  }
}

// Test LinkedIn profile extraction
async function testProfileExtraction() {
  console.log('\n🔍 Testing LinkedIn profile extraction...');
  
  const sampleLinkedInUrls = [
    'https://www.linkedin.com/in/sample-ceo',
    'https://www.linkedin.com/in/sample-cfo'
  ];
  
  console.log('📋 Sample URLs for extraction:');
  sampleLinkedInUrls.forEach((url, index) => {
    console.log(`   ${index + 1}. ${url}`);
  });
  
  console.log('\n⚠️  Profile extraction test skipped (to avoid API usage)');
  console.log('   Uncomment the actual API calls to test profile extraction');
}

async function runTests() {
  await testHeyReachConnection();
  await testCampaignCreation();
  await testProfileExtraction();
  
  console.log('\n✅ Connection tests completed!');
  console.log('\n📚 Next steps:');
  console.log('1. Connect LinkedIn accounts in your HeyReach dashboard');
  console.log('2. Start the service: npm run dev');
  console.log('3. Test health endpoint: GET http://localhost:3007/health');
  console.log('4. Create your first LinkedIn campaign via API');
}

if (require.main === module) {
  runTests().catch(console.error);
}

module.exports = { testHeyReachConnection, testCampaignCreation, testProfileExtraction };
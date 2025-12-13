require('dotenv').config();
const { ApifyClient } = require('apify-client');

// Test the new API key
const API_KEY = 'apify_api_63CEvQr4uy247iyULJibGB1JSOHYtd2RVDqH';

async function testApiKey() {
    console.log('======================================');
    console.log('  TESTING APIFY API KEY');
    console.log('======================================\n');
    
    console.log('API Key:', API_KEY.substring(0, 20) + '...');
    console.log('\nAttempting to authenticate...\n');
    
    try {
        const client = new ApifyClient({ token: API_KEY });
        
        // Test 1: Get user info
        console.log('1. Testing user authentication...');
        const user = await client.user().get();
        console.log('   ✅ SUCCESS! Authenticated as:', user.username);
        console.log('   • Email:', user.email || 'N/A');
        console.log('   • Plan:', user.plan?.name || 'N/A');
        
        // Test 2: List available actors
        console.log('\n2. Checking available actors...');
        const { items: actors } = await client.actors().list({ limit: 5 });
        console.log(`   ✅ Found ${actors.length} actors`);
        actors.forEach(actor => {
            console.log(`   • ${actor.name} (${actor.id})`);
        });
        
        // Test 3: List available tasks
        console.log('\n3. Checking available tasks...');
        const { items: tasks } = await client.tasks().list({ limit: 5 });
        console.log(`   ✅ Found ${tasks.length} tasks`);
        tasks.forEach(task => {
            console.log(`   • ${task.name} (${task.id})`);
            if (task.name.toLowerCase().includes('apollo') || 
                task.name.toLowerCase().includes('scrape')) {
                console.log(`     ⭐ Potential Apollo scraper task found!`);
            }
        });
        
        // Test 4: Check account limits
        console.log('\n4. Checking account limits...');
        const account = await client.user().get();
        if (account.limits) {
            console.log('   • Monthly actor compute units:', account.limits.monthlyActorComputeUnits || 'N/A');
            console.log('   • Monthly dataset reads:', account.limits.monthlyDatasetReads || 'N/A');
        }
        
        console.log('\n======================================');
        console.log('  ✅ API KEY IS VALID!');
        console.log('======================================');
        console.log('\nNext steps:');
        console.log('1. Note down any Apollo-related task IDs from above');
        console.log('2. Create .env file with this API key');
        console.log('3. Add the task ID to your .env file');
        console.log('4. Configure your Neon database connection');
        
        return true;
        
    } catch (error) {
        console.log('❌ AUTHENTICATION FAILED!');
        console.log('Error:', error.message);
        
        if (error.statusCode === 401) {
            console.log('\n⚠️  This API key is invalid or expired.');
            console.log('Please check if you copied it correctly.');
        } else if (error.statusCode === 403) {
            console.log('\n⚠️  This API key lacks necessary permissions.');
        } else {
            console.log('\n⚠️  Unexpected error occurred.');
            console.log('Status code:', error.statusCode);
        }
        
        return false;
    }
}

// Run the test
testApiKey().then(success => {
    if (success) {
        console.log('\n✅ You can now use this API key in your .env file');
    } else {
        console.log('\n❌ This API key cannot be used');
    }
}).catch(error => {
    console.error('Unexpected error:', error);
    process.exit(1);
});
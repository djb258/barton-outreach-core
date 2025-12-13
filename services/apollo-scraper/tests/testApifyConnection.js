require('dotenv').config();
const { ApifyClient } = require('apify-client');

async function testApifyConnection() {
    console.log('======================================');
    console.log('  APIFY CONNECTION TEST');
    console.log('======================================\n');
    
    const APIFY_API_KEY = process.env.APIFY_API_KEY;
    const APIFY_ACTOR_ID = process.env.APIFY_ACTOR_ID;
    
    console.log('Configuration:');
    console.log('• API Key:', APIFY_API_KEY ? APIFY_API_KEY.substring(0, 20) + '...' : 'NOT SET');
    console.log('• Actor ID:', APIFY_ACTOR_ID || 'NOT SET');
    
    if (!APIFY_API_KEY) {
        console.log('\n❌ APIFY_API_KEY not found in .env file');
        return;
    }
    
    try {
        const client = new ApifyClient({ token: APIFY_API_KEY });
        
        // Test authentication
        console.log('\n1. Testing authentication...');
        const user = await client.user().get();
        console.log('   ✅ Authenticated as:', user.username);
        
        // Test actor access
        if (APIFY_ACTOR_ID) {
            console.log('\n2. Testing Apollo scraper actor...');
            const actor = await client.actor(APIFY_ACTOR_ID).get();
            console.log('   ✅ Actor found:', actor.name);
            console.log('   • Description:', actor.description || 'No description');
            console.log('   • Version:', actor.versions[0]?.versionNumber || 'N/A');
            
            // Check actor input schema to understand required parameters
            if (actor.versions[0]?.sourceFiles?.find(f => f.name === 'INPUT_SCHEMA.json')) {
                console.log('   • Has input schema: Yes');
            }
            
            // Test with a small example
            console.log('\n3. Testing actor with sample Apollo URL...');
            const testInput = {
                url: 'https://app.apollo.io/#/people?personLocations[]=Germany&page=1',
                maxResults: 5,  // Very small number for testing
                cleanOutput: false
            };
            
            console.log('   Test input:', testInput);
            console.log('\n   ⚠️  Not running actual scrape to avoid consuming credits.');
            console.log('   To run a real test, uncomment the code below.');
            
            // UNCOMMENT TO RUN ACTUAL TEST (WILL CONSUME CREDITS):
            /*
            const run = await client.actor(APIFY_ACTOR_ID).call(testInput);
            console.log('   ✅ Actor started! Run ID:', run.id);
            console.log('   Waiting for completion...');
            const finishedRun = await client.run(run.id).waitForFinish();
            console.log('   ✅ Run completed with status:', finishedRun.status);
            
            if (finishedRun.status === 'SUCCEEDED') {
                const { items } = await client.dataset(finishedRun.defaultDatasetId).listItems({ limit: 5 });
                console.log(`   ✅ Retrieved ${items.length} results`);
                if (items.length > 0) {
                    console.log('   Sample result:', items[0]);
                }
            }
            */
        }
        
        console.log('\n======================================');
        console.log('  ✅ APIFY SETUP IS WORKING!');
        console.log('======================================');
        console.log('\nYour Apify configuration is valid and ready to use.');
        console.log('\nRemaining setup:');
        console.log('1. Configure NEON_DATABASE_URL in .env file');
        console.log('2. Set up database tables using the SQL scripts');
        console.log('3. Run: npm start');
        
    } catch (error) {
        console.log('\n❌ Test failed:', error.message);
        if (error.statusCode) {
            console.log('   Status code:', error.statusCode);
        }
    }
}

testApifyConnection();
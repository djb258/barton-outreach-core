require('dotenv').config();
const { ApifyClient } = require('apify-client');

// Your working Apollo scraper configuration
const TEST_CONFIG = {
    cleanOutput: false,
    url: "https://app.apollo.io/#/people?finderViewId=5b8050d050a3893c382e9360&personLocations[]=Germany&page=1&sortByField=recommendations_score&organizationNumEmployeesRanges[]=5000%2C5200&organizationIndustryTagIds[]=5567e0bf7369641d115f0200&organizationIndustryTagIds[]=5567e3f3736964395d7a0000"
};

// Parse the Apollo URL to understand the search parameters
function parseApolloUrl(url) {
    console.log('\n📋 APOLLO URL ANALYSIS:');
    console.log('------------------------');
    
    const hashIndex = url.indexOf('#');
    if (hashIndex === -1) {
        console.log('❌ Invalid Apollo URL format');
        return null;
    }
    
    const fragment = url.substring(hashIndex + 1);
    const [path, queryString] = fragment.split('?');
    
    console.log('Path:', path);
    
    if (queryString) {
        const params = new URLSearchParams(queryString);
        console.log('\nSearch Parameters:');
        for (const [key, value] of params) {
            if (key === 'personLocations[]') {
                console.log(`  • Location: ${value}`);
            } else if (key === 'page') {
                console.log(`  • Page: ${value}`);
            } else if (key === 'sortByField') {
                console.log(`  • Sort by: ${value}`);
            } else if (key === 'organizationNumEmployeesRanges[]') {
                const [min, max] = value.split('%2C');
                console.log(`  • Company size: ${min}-${max} employees`);
            } else if (key === 'organizationIndustryTagIds[]') {
                console.log(`  • Industry ID: ${value}`);
            } else if (key === 'finderViewId') {
                console.log(`  • Finder View ID: ${value}`);
            } else {
                console.log(`  • ${key}: ${value}`);
            }
        }
    }
    
    return { path, queryString };
}

// Test the Apify scraper with this configuration
async function testApifyScraper() {
    console.log('======================================');
    console.log('  APOLLO SCRAPER TEST');
    console.log('======================================\n');
    
    // Analyze the URL
    parseApolloUrl(TEST_CONFIG.url);
    
    console.log('\n🔧 SCRAPER CONFIGURATION:');
    console.log('------------------------');
    console.log('• Clean Output:', TEST_CONFIG.cleanOutput);
    console.log('• Total Records: 1000 (default)');
    console.log('• File Name: company_contacts (default)');
    
    // Check if we have Apify credentials
    const APIFY_API_KEY = process.env.APIFY_API_KEY;
    const APIFY_TASK_ID = process.env.APIFY_TASK_ID;
    
    console.log('\n🔑 CREDENTIALS CHECK:');
    console.log('------------------------');
    console.log('• APIFY_API_KEY:', APIFY_API_KEY ? `✓ Set (${APIFY_API_KEY.substring(0, 20)}...)` : '✗ Not set');
    console.log('• APIFY_TASK_ID:', APIFY_TASK_ID ? `✓ Set (${APIFY_TASK_ID})` : '✗ Not set');
    
    if (!APIFY_API_KEY || !APIFY_TASK_ID) {
        console.log('\n⚠️  Cannot proceed with actual API test without credentials.');
        console.log('\n📝 To test with real Apify:');
        console.log('1. Create a .env file in this directory');
        console.log('2. Add your Apify credentials:');
        console.log('   APIFY_API_KEY=your_api_key_here');
        console.log('   APIFY_TASK_ID=your_task_id_here');
        
        // Simulate what would happen
        console.log('\n🎭 SIMULATING SCRAPER BEHAVIOR:');
        console.log('------------------------');
        console.log('1. Would send request to Apify with:');
        console.log('   • URL:', TEST_CONFIG.url.substring(0, 80) + '...');
        console.log('   • Clean Output:', TEST_CONFIG.cleanOutput);
        console.log('2. Would poll for completion');
        console.log('3. Would fetch dataset results');
        console.log('4. Would filter contacts by title');
        console.log('5. Would save to database');
        
        return;
    }
    
    // Test with actual Apify API
    console.log('\n🚀 TESTING WITH APIFY API:');
    console.log('------------------------');
    
    try {
        const client = new ApifyClient({ token: APIFY_API_KEY });
        
        // Verify the task exists
        console.log('Checking task...');
        const task = await client.task(APIFY_TASK_ID).get();
        console.log(`✓ Task found: ${task.name}`);
        console.log(`  Actor: ${task.actId}`);
        
        // Prepare the input for the task
        const input = {
            url: TEST_CONFIG.url,
            cleanOutput: TEST_CONFIG.cleanOutput,
            totalRecords: 10, // Use small number for testing
            fileName: 'test_apollo_scrape'
        };
        
        console.log('\n📤 Would send this input to Apify:');
        console.log(JSON.stringify(input, null, 2));
        
        // Ask for confirmation before running
        console.log('\n⚠️  Ready to run actual Apify task.');
        console.log('This will consume Apify credits.');
        console.log('To proceed with actual run, use: node runActualScrape.js');
        
    } catch (error) {
        console.log('❌ API Test failed:', error.message);
        if (error.statusCode === 401) {
            console.log('   The API key appears to be invalid');
        } else if (error.statusCode === 404) {
            console.log('   The task ID was not found');
        }
    }
}

// Also test how the scraper would handle this in the pipeline
async function testScraperPipeline() {
    console.log('\n🔄 TESTING SCRAPER PIPELINE:');
    console.log('------------------------');
    
    // Mock a company record that would come from the database
    const mockCompany = {
        company_id: 'test-123',
        company_name: 'Test German Tech Company',
        apollo_url: TEST_CONFIG.url
    };
    
    console.log('Mock Company:', {
        id: mockCompany.company_id,
        name: mockCompany.company_name,
        url: mockCompany.apollo_url.substring(0, 80) + '...'
    });
    
    // Show what each module would do
    console.log('\n📊 Pipeline Steps:');
    console.log('1. getPendingCompanies() - Would fetch this from DB');
    console.log('2. runApifyScrape() - Would start Apify task');
    console.log('3. pollApifyRun() - Would wait for completion');
    console.log('4. fetchApifyDataset() - Would download results');
    console.log('5. filterContactsByTitle() - Would filter contacts');
    console.log('6. writeResults() - Would save to database');
    console.log('7. markCompanyStatus() - Would mark as COMPLETE');
}

// Run tests
async function main() {
    await testApifyScraper();
    await testScraperPipeline();
    
    console.log('\n======================================');
    console.log('  TEST COMPLETE');
    console.log('======================================');
}

main().catch(error => {
    console.error('Test failed:', error);
    process.exit(1);
});
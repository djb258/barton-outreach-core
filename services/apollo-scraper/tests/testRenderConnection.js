require('dotenv').config();
const { renderClient } = require('./api/clients/renderClient');

async function testRenderConnection() {
  console.log('======================================');
  console.log('  RENDER MARKETING DB CONNECTION TEST');
  console.log('======================================\n');

  try {
    console.log('1. Testing basic connection...');
    const connectionTest = await renderClient.testConnection();
    
    if (connectionTest.connected) {
      console.log('   ✅ Connection successful!');
      console.log('   • Health:', connectionTest.health);
      console.log('   • Database:', connectionTest.database);
    } else {
      console.log('   ❌ Connection failed:', connectionTest.error);
      return;
    }

    console.log('\n2. Testing company endpoints...');
    try {
      const companies = await renderClient.getCompanies();
      console.log('   ✅ Companies endpoint working');
      console.log('   • Found companies:', companies.companies?.length || 0);
    } catch (error) {
      console.log('   ⚠️  Companies endpoint error:', error.message);
    }

    console.log('\n3. Testing Apollo data endpoints...');
    try {
      const apolloData = await renderClient.getApolloData();
      console.log('   ✅ Apollo endpoint working');
      console.log('   • Found Apollo records:', apolloData.apollo_data?.length || 0);
    } catch (error) {
      console.log('   ⚠️  Apollo endpoint error:', error.message);
    }

    console.log('\n4. Testing ping endpoint...');
    try {
      const response = await renderClient.client.post('/pingpong', {
        prompt: 'Test from scraping tool'
      });
      console.log('   ✅ Ping endpoint working');
      console.log('   • Response:', response.data.response);
    } catch (error) {
      console.log('   ⚠️  Ping endpoint error:', error.message);
    }

    console.log('\n======================================');
    console.log('  🎉 RENDER CONNECTION READY!');
    console.log('======================================');
    console.log('\nYou can now:');
    console.log('1. Start the API server: npm run start:api');
    console.log('2. Use the integrated endpoints to scrape and store data');
    console.log('3. Check the API documentation at: http://localhost:3000/api/v1/docs');

  } catch (error) {
    console.log('\n❌ Connection test failed:', error.message);
    console.log('\nTroubleshooting:');
    console.log('1. Check if Render service is running at:', renderClient.baseURL);
    console.log('2. Verify CORS configuration allows your requests');
    console.log('3. Check network connectivity');
  }
}

testRenderConnection();
require('dotenv').config();
const { ApifyClient } = require('apify-client');

const API_KEY = process.env.APIFY_API_KEY || 'apify_api_63EvQr4y247iyULJibGB1JSOHYtd2VDqH';
const DATASET_ID = 'trG644GcFz8Alev';

async function testApiKey() {
  try {
    console.log('Testing API key with:', API_KEY.substring(0, 20) + '...');
    const client = new ApifyClient({ token: API_KEY });
    
    // Test getting dataset items
    const dataset = client.dataset(DATASET_ID);
    const { items } = await dataset.listItems({ limit: 10 });
    
    console.log('Success! Found', items.length, 'items');
    if (items.length > 0) {
      console.log('First item:', items[0]);
    }
  } catch (error) {
    console.error('Error:', error.message);
    if (error.statusCode) {
      console.error('Status Code:', error.statusCode);
    }
  }
}

testApiKey(); 
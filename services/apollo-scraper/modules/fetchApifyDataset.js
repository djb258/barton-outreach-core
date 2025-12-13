// modules/fetchApifyDataset.js
require('dotenv').config();
const axios = require('axios');

async function fetchApifyDataset(datasetId) {
  const APIFY_API_KEY = process.env.APIFY_API_KEY;
  if (!APIFY_API_KEY) throw new Error('[B] [ERROR] APIFY_API_KEY environment variable is required');
  const url = `https://api.apify.com/v2/datasets/${datasetId}/items`;
  try {
    const response = await axios.get(url, {
      headers: {
        Authorization: `Bearer ${APIFY_API_KEY}`,
        Accept: 'application/json'
      }
    });
    const contacts = response.data;
    console.log(`[O] [INFO] fetchApifyDataset: Retrieved ${contacts.length} records from dataset ${datasetId}`);
    return contacts;
  } catch (error) {
    console.error(`[R] [ERROR] fetchApifyDataset: Failed to fetch dataset ${datasetId}:`, error?.response?.data || error.message);
    throw new Error(`Failed to fetch Apify dataset: ${error.message}`);
  }
}

module.exports = { fetchApifyDataset }; 
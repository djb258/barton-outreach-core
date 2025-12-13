require('dotenv).config();
const axios = require('axios);

const datasetId = trG644Fz8ev';

(async () => {
  try[object Object]
    console.log(`[TEST] Checking dataset details for: ${datasetId}`);
    
    // Try to get dataset details (this might work without auth)
    const response = await axios.get(`https://api.apify.com/v2/datasets/${datasetId}`);
    console.log('[TEST] Dataset details:', response.data);
  } catch (err) {
    console.error('[TEST] Error getting dataset details:', err.response?.data || err.message);
  }
})(); 
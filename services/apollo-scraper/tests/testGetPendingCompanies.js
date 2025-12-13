require('dotenv').config();
const { getPendingCompanies } = require('./modules/getPendingCompanies');

(async () => {
  try {
    const companies = await getPendingCompanies();
    console.log('[TEST] Result:', companies);
  } catch (err) {
    console.error('[TEST] Error:', err);
  }
})(); 
require('dotenv').config();

console.log('NEON_DATABASE_URL:', process.env.NEON_DATABASE_URL ? 'SET' : 'NOT SET');
console.log('APIFY_API_KEY:', process.env.APIFY_API_KEY ? 'SET' : 'NOT SET');
console.log('APIFY_API_KEY length:', process.env.APIFY_API_KEY ? process.env.APIFY_API_KEY.length : 0);
console.log('APIFY_API_KEY first 10 chars:', process.env.APIFY_API_KEY ? process.env.APIFY_API_KEY.substring(0, 10) : 'N/A'); 
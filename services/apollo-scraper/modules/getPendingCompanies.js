// modules/getPendingCompanies.js
const { neon } = require('@neondatabase/serverless');

async function getPendingCompanies() {
  console.log('[O] [STEP] getPendingCompanies: Connecting to Neon database...');
  try {
    // Get database connection string from environment
    const databaseUrl = process.env.NEON_DATABASE_URL;
    if (!databaseUrl) {
      throw new Error('[B] [ERROR] NEON_DATABASE_URL environment variable is required');
    }
    console.log('[O] [INFO] Fetching pending companies from Neon (marketing_company_intake)...');
    // Create database connection
    const sql = neon(databaseUrl);
    // Query for pending companies with validated Apollo URLs
    const query = `
      SELECT 
        id as company_id,
        company_name,
        apollo_url
      FROM marketing_company_intake 
      WHERE scrape_status = 'PENDING' 
        AND apollo_url_validated = TRUE
      LIMIT 5;
    `;
    console.log('[R] [INFO] Executing SQL query for pending companies...');
    const companies = await sql(query);
    console.log(`[R] [SUCCESS] Pulled ${companies.length} companies with scrape_status='PENDING'`);
    // Log each company for observability
    companies.forEach(company => {
      console.log(`[O] [INFO] Company: ${company.company_id} | ${company.company_name} | ${company.apollo_url}`);
    });
    return companies;
  } catch (error) {
    console.error('[R] [ERROR] Failed to fetch pending companies:', error.message);
    throw error;
  }
}

module.exports = { getPendingCompanies }; 
/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/analysis
Barton ID: 06.01.01
Unique ID: CTB-364247A9
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

/**
 * List Companies from intake.company_raw_intake
 * These are the companies available for executive enrichment
 */

import pg from 'pg';
import dotenv from 'dotenv';
import fs from 'fs/promises';

dotenv.config();

const NEON_DATABASE_URL = process.env.NEON_DATABASE_URL || process.env.DATABASE_URL;

console.log('\n=== Companies Available for Enrichment ===\n');

async function listCompanies() {
  const client = new pg.Client({
    connectionString: NEON_DATABASE_URL,
    ssl: { rejectUnauthorized: false }
  });

  try {
    await client.connect();
    console.log('✅ Connected to Neon database\n');

    // 1. Get total count
    console.log('[STEP 1] Counting companies in intake.company_raw_intake...\n');

    const countQuery = 'SELECT COUNT(*) as total FROM intake.company_raw_intake';
    const countResult = await client.query(countQuery);
    const totalCompanies = countResult.rows[0].total;

    console.log(`Found ${totalCompanies} companies in intake.company_raw_intake\n`);

    // 2. Get all companies with key fields
    console.log('[STEP 2] Fetching company details...\n');

    const companiesQuery = `
      SELECT
        id,
        company,
        company_name_for_emails,
        website,
        company_linkedin_url,
        industry,
        num_employees,
        company_city,
        company_state,
        company_country,
        company_phone,
        founded_year,
        created_at
      FROM intake.company_raw_intake
      ORDER BY id ASC
    `;

    const companiesResult = await client.query(companiesQuery);
    const companies = companiesResult.rows;

    console.log(`Retrieved ${companies.length} companies:\n`);

    // 3. Display companies
    companies.forEach((company, index) => {
      console.log(`${index + 1}. [ID: ${company.id}] ${company.company || company.company_name_for_emails || 'Unnamed Company'}`);
      console.log(`   Website: ${company.website || 'N/A'}`);
      console.log(`   LinkedIn: ${company.company_linkedin_url || 'N/A'}`);
      console.log(`   Industry: ${company.industry || 'N/A'}`);
      console.log(`   Employees: ${company.num_employees || 'N/A'}`);
      console.log(`   Location: ${company.company_city || 'N/A'}, ${company.company_state || 'N/A'}, ${company.company_country || 'N/A'}`);
      console.log('');
    });

    // 4. Analyze data quality
    console.log('\n[STEP 3] Analyzing data quality for enrichment...\n');

    const withWebsite = companies.filter(c => c.website);
    const withLinkedIn = companies.filter(c => c.company_linkedin_url);
    const withIndustry = companies.filter(c => c.industry);
    const withLocation = companies.filter(c => c.company_state || c.company_city);
    const withEmployeeCount = companies.filter(c => c.num_employees);

    console.log('Data Quality Analysis:');
    console.log(`  Companies with Website: ${withWebsite.length} / ${companies.length} (${(withWebsite.length/companies.length*100).toFixed(1)}%)`);
    console.log(`  Companies with LinkedIn: ${withLinkedIn.length} / ${companies.length} (${(withLinkedIn.length/companies.length*100).toFixed(1)}%)`);
    console.log(`  Companies with Industry: ${withIndustry.length} / ${companies.length} (${(withIndustry.length/companies.length*100).toFixed(1)}%)`);
    console.log(`  Companies with Location: ${withLocation.length} / ${companies.length} (${(withLocation.length/companies.length*100).toFixed(1)}%)`);
    console.log(`  Companies with Employee Count: ${withEmployeeCount.length} / ${companies.length} (${(withEmployeeCount.length/companies.length*100).toFixed(1)}%)`);

    // 5. Identify companies ready for enrichment
    console.log('\n[STEP 4] Identifying companies ready for enrichment...\n');

    const readyForEnrichment = companies.filter(c =>
      (c.website || c.company_linkedin_url) && // Need at least website OR LinkedIn
      (c.industry || c.num_employees) // Need some company context
    );

    console.log(`${readyForEnrichment.length} companies are ready for executive enrichment:\n`);

    readyForEnrichment.forEach((company, index) => {
      console.log(`  ${index + 1}. [ID: ${company.id}] ${company.company || company.company_name_for_emails}`);
      console.log(`     Domain: ${company.website || 'Use LinkedIn instead'}`);
      console.log(`     Industry: ${company.industry || 'N/A'}`);
      console.log(`     Size: ${company.num_employees || 'Unknown'} employees`);
      console.log('');
    });

    // 6. Save to JSON for enrichment script
    const enrichmentInput = {
      timestamp: new Date().toISOString(),
      total_companies: companies.length,
      ready_for_enrichment: readyForEnrichment.length,
      companies: readyForEnrichment.map(c => ({
        id: c.id,
        company_name: c.company || c.company_name_for_emails,
        website: c.website,
        linkedin_url: c.company_linkedin_url,
        industry: c.industry,
        num_employees: c.num_employees,
        location: {
          city: c.company_city,
          state: c.company_state,
          country: c.company_country
        },
        phone: c.company_phone,
        founded_year: c.founded_year
      }))
    };

    const outputPath = './analysis/companies_for_enrichment.json';
    await fs.writeFile(outputPath, JSON.stringify(enrichmentInput, null, 2));

    console.log('\n[STEP 5] Summary and Next Steps\n');
    console.log(`✅ Found ${companies.length} total companies in intake.company_raw_intake`);
    console.log(`✅ ${readyForEnrichment.length} companies ready for executive enrichment`);
    console.log(`✅ Company list saved to: ${outputPath}`);

    console.log('\n📋 Recommended Trial Parameters:');
    if (readyForEnrichment.length > 0) {
      console.log(`  Start with: 1-3 companies (low cost trial)`);
      console.log(`  Estimated cost: $0.25 - $0.75 for 3 companies`);
      console.log(`  Expected executives: 3-15 (5 per company avg)`);
    }

    console.log('\n🎯 Best Candidates for Trial:\n');
    readyForEnrichment.slice(0, 5).forEach((company, index) => {
      const score = (
        (company.website ? 30 : 0) +
        (company.company_linkedin_url ? 30 : 0) +
        (company.industry ? 20 : 0) +
        (company.num_employees ? 20 : 0)
      );
      console.log(`  ${index + 1}. [ID: ${company.id}] ${company.company || company.company_name_for_emails} (Score: ${score}/100)`);
    });

    return companies;

  } catch (error) {
    console.error('\n❌ Query failed:', error);
    throw error;
  } finally {
    await client.end();
    console.log('\n✅ Database connection closed\n');
  }
}

// Run
listCompanies()
  .then(() => {
    console.log('✅ Company list generated successfully!');
    process.exit(0);
  })
  .catch(error => {
    console.error('❌ Failed:', error.message);
    process.exit(1);
  });

/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/analysis
Barton ID: 06.01.01
Unique ID: CTB-2BC526EE
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

/**
 * Setup Master Tables and Promote Companies
 * Creates marketing.company_master and marketing.people_master
 * Then promotes companies from intake.company_raw_intake
 */

import pg from 'pg';
import dotenv from 'dotenv';
import fs from 'fs/promises';
import path from 'path';

dotenv.config();

const NEON_DATABASE_URL = process.env.NEON_DATABASE_URL || process.env.DATABASE_URL;

console.log('\n=== Setting Up Master Tables ===\n');

async function setupMasterTables() {
  const client = new pg.Client({
    connectionString: NEON_DATABASE_URL,
    ssl: { rejectUnauthorized: false }
  });

  try {
    await client.connect();
    console.log('✅ Connected to Neon database\n');

    // 1. Create marketing.company_master
    console.log('[STEP 1] Creating marketing.company_master table...\n');

    const companyMasterSQL = await fs.readFile(
      path.join(process.cwd(), 'apps/outreach-process-manager/migrations/create_company_master.sql'),
      'utf-8'
    );

    await client.query(companyMasterSQL);
    console.log('✅ marketing.company_master table created\n');

    // 2. Create marketing.people_master
    console.log('[STEP 2] Creating marketing.people_master table...\n');

    const peopleMasterSQL = await fs.readFile(
      path.join(process.cwd(), 'apps/outreach-process-manager/migrations/create_people_master.sql'),
      'utf-8'
    );

    await client.query(peopleMasterSQL);
    console.log('✅ marketing.people_master table created\n');

    // 3. Check if tables exist
    console.log('[STEP 3] Verifying tables...\n');

    const verifyQuery = `
      SELECT table_name
      FROM information_schema.tables
      WHERE table_schema = 'marketing'
        AND table_name IN ('company_master', 'people_master')
      ORDER BY table_name;
    `;

    const verifyResult = await client.query(verifyQuery);
    console.log(`Found ${verifyResult.rows.length} tables:`);
    verifyResult.rows.forEach(row => {
      console.log(`  ✅ marketing.${row.table_name}`);
    });

    // 4. Count companies ready to promote
    console.log('\n[STEP 4] Counting companies ready for promotion...\n');

    const countQuery = 'SELECT COUNT(*) as total FROM intake.company_raw_intake';
    const countResult = await client.query(countQuery);
    const totalCompanies = countResult.rows[0].total;

    console.log(`Found ${totalCompanies} companies in intake.company_raw_intake ready to promote\n`);

    // 5. Promote companies to company_master
    console.log('[STEP 5] Promoting companies to marketing.company_master...\n');

    const promoteQuery = `
      INSERT INTO marketing.company_master (
        company_unique_id,
        company_name,
        website_url,
        industry,
        employee_count,
        company_phone,
        address_city,
        address_state,
        address_country,
        linkedin_url,
        facebook_url,
        twitter_url,
        sic_codes,
        founded_year,
        source_system,
        source_record_id,
        promoted_from_intake_at,
        created_at,
        updated_at
      )
      SELECT
        -- Generate Barton ID: 06.01.01
        '04' || '.' ||  -- Entity type: company
        '04' || '.' ||  -- Schema version
        '01' || '.' ||  -- Table: company_master
        LPAD((EXTRACT(EPOCH FROM NOW())::BIGINT % 100)::TEXT, 2, '0') || '.' ||
        LPAD((RANDOM() * 100000)::INT::TEXT, 5, '0') || '.' ||
        LPAD((id % 1000)::TEXT, 3, '0') as company_unique_id,

        COALESCE(company, company_name_for_emails, 'Unknown Company') as company_name,
        COALESCE(website, 'https://example.com') as website_url,
        industry,
        num_employees as employee_count,
        company_phone,
        company_city as address_city,
        company_state as address_state,
        company_country as address_country,
        company_linkedin_url as linkedin_url,
        facebook_url,
        twitter_url,
        sic_codes,
        founded_year,
        'intake_promotion' as source_system,
        id::text as source_record_id,
        NOW() as promoted_from_intake_at,
        NOW() as created_at,
        NOW() as updated_at
      FROM intake.company_raw_intake
      ON CONFLICT (company_unique_id) DO NOTHING;
    `;

    const promoteResult = await client.query(promoteQuery);
    console.log(`✅ Promoted ${promoteResult.rowCount} companies to marketing.company_master\n`);

    // 6. Verify promotion
    console.log('[STEP 6] Verifying promotion...\n');

    const verifyPromotionQuery = `
      SELECT
        COUNT(*) as total,
        COUNT(DISTINCT industry) as industries,
        MIN(employee_count) as min_employees,
        MAX(employee_count) as max_employees,
        AVG(employee_count)::int as avg_employees
      FROM marketing.company_master;
    `;

    const verifyPromotionResult = await client.query(verifyPromotionQuery);
    const stats = verifyPromotionResult.rows[0];

    console.log('Marketing Company Master Stats:');
    console.log(`  Total Companies: ${stats.total}`);
    console.log(`  Industries: ${stats.industries}`);
    console.log(`  Employee Range: ${stats.min_employees} - ${stats.max_employees}`);
    console.log(`  Average Employees: ${stats.avg_employees}`);

    // 7. Sample companies
    console.log('\n[STEP 7] Sample promoted companies...\n');

    const sampleQuery = `
      SELECT
        company_unique_id,
        company_name,
        website_url,
        industry,
        employee_count,
        address_state
      FROM marketing.company_master
      ORDER BY employee_count DESC
      LIMIT 5;
    `;

    const sampleResult = await client.query(sampleQuery);
    console.log('Top 5 Companies by Size:');
    sampleResult.rows.forEach((row, i) => {
      console.log(`\n  ${i + 1}. ${row.company_name}`);
      console.log(`     ID: ${row.company_unique_id}`);
      console.log(`     Website: ${row.website_url}`);
      console.log(`     Industry: ${row.industry}`);
      console.log(`     Employees: ${row.employee_count}`);
      console.log(`     State: ${row.address_state}`);
    });

    // 8. Save mapping
    console.log('\n\n[STEP 8] Creating intake → master mapping...\n');

    const mappingQuery = `
      SELECT
        cri.id as intake_id,
        cri.company as intake_company_name,
        cm.company_unique_id as master_unique_id,
        cm.company_name as master_company_name
      FROM intake.company_raw_intake cri
      JOIN marketing.company_master cm ON cm.source_record_id = cri.id::text
      ORDER BY cri.id
      LIMIT 10;
    `;

    const mappingResult = await client.query(mappingQuery);

    console.log('Sample ID Mapping (intake → master):');
    mappingResult.rows.forEach(row => {
      console.log(`  Intake ID ${row.intake_id} → Master ID ${row.master_unique_id}`);
      console.log(`  "${row.intake_company_name}" → "${row.master_company_name}"`);
      console.log('');
    });

    // 9. Generate summary
    const summary = {
      timestamp: new Date().toISOString(),
      tables_created: [
        'marketing.company_master',
        'marketing.people_master'
      ],
      companies_promoted: promoteResult.rowCount,
      total_companies_in_master: parseInt(stats.total),
      ready_for_enrichment: true,
      next_steps: [
        'Run executive enrichment trial',
        'Populate marketing.people_master with executives',
        'Link executives to companies via company_unique_id'
      ]
    };

    await fs.writeFile(
      './analysis/master_tables_setup_summary.json',
      JSON.stringify(summary, null, 2)
    );

    console.log('\n\n=== SETUP COMPLETE ===\n');
    console.log('✅ Tables Created:');
    console.log('   - marketing.company_master');
    console.log('   - marketing.people_master');
    console.log(`\n✅ Companies Promoted: ${promoteResult.rowCount}`);
    console.log(`✅ Total in Master: ${stats.total}`);
    console.log('\n✅ Summary saved to: analysis/master_tables_setup_summary.json');
    console.log('\n🚀 Ready for executive enrichment!');

  } catch (error) {
    console.error('\n❌ Setup failed:', error);
    console.error('Error details:', error.message);
    throw error;
  } finally {
    await client.end();
    console.log('\n✅ Database connection closed\n');
  }
}

// Run setup
setupMasterTables()
  .then(() => {
    console.log('✅ Master tables setup complete!');
    process.exit(0);
  })
  .catch(error => {
    console.error('❌ Setup error:', error.message);
    process.exit(1);
  });

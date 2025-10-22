/**
 * Validate Neon Schema for Executive Enrichment
 * Queries actual Neon database to verify table structure
 */

import pg from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const NEON_DATABASE_URL = process.env.NEON_DATABASE_URL || process.env.DATABASE_URL;

console.log('\n=== Neon Schema Validation ===\n');

async function validateSchema() {
  const client = new pg.Client({
    connectionString: NEON_DATABASE_URL,
    ssl: { rejectUnauthorized: false }
  });

  try {
    await client.connect();
    console.log('✅ Connected to Neon database\n');

    // 1. Check if company_master exists
    console.log('[STEP 1] Checking marketing.company_master table...\n');

    const companyTableQuery = `
      SELECT column_name, data_type, is_nullable
      FROM information_schema.columns
      WHERE table_schema = 'marketing'
        AND table_name = 'company_master'
      ORDER BY ordinal_position;
    `;

    const companyResult = await client.query(companyTableQuery);

    if (companyResult.rows.length === 0) {
      console.log('❌ Table marketing.company_master does not exist!\n');
    } else {
      console.log(`✅ Found marketing.company_master with ${companyResult.rows.length} columns:\n`);

      const executiveFields = [
        'ceo_name', 'ceo_email', 'ceo_linkedin', 'ceo_phone',
        'cfo_name', 'cfo_email', 'cfo_linkedin', 'cfo_phone',
        'chro_name', 'chro_email', 'chro_linkedin',
        'hr_name', 'hr_email', 'hr_linkedin',
        'enrichment_status', 'enrichment_source', 'last_enriched'
      ];

      const existingColumns = companyResult.rows.map(r => r.column_name);
      const missingExecutiveFields = executiveFields.filter(f => !existingColumns.includes(f));

      console.log('Current Columns:');
      companyResult.rows.forEach(row => {
        console.log(`  - ${row.column_name} (${row.data_type})`);
      });

      console.log(`\n❌ Missing Executive Enrichment Fields (${missingExecutiveFields.length}):`);
      missingExecutiveFields.forEach(field => {
        console.log(`  - ${field}`);
      });
    }

    // 2. Check if people_master exists
    console.log('\n\n[STEP 2] Checking marketing.people_master table...\n');

    const peopleTableQuery = `
      SELECT column_name, data_type, is_nullable
      FROM information_schema.columns
      WHERE table_schema = 'marketing'
        AND table_name = 'people_master'
      ORDER BY ordinal_position;
    `;

    const peopleResult = await client.query(peopleTableQuery);

    if (peopleResult.rows.length === 0) {
      console.log('❌ Table marketing.people_master does not exist!\n');
    } else {
      console.log(`✅ Found marketing.people_master with ${peopleResult.rows.length} columns:\n`);

      const requiredFields = [
        'unique_id', 'company_unique_id', 'first_name', 'last_name',
        'title', 'seniority', 'email', 'linkedin_url'
      ];

      console.log('Key Columns for Executive Storage:');
      peopleResult.rows
        .filter(r => requiredFields.includes(r.column_name))
        .forEach(row => {
          console.log(`  ✅ ${row.column_name} (${row.data_type}) - ${row.is_nullable === 'NO' ? 'NOT NULL' : 'NULLABLE'}`);
        });

      const missingRequired = requiredFields.filter(f =>
        !peopleResult.rows.find(r => r.column_name === f)
      );

      if (missingRequired.length > 0) {
        console.log(`\n❌ Missing Required Fields:`);
        missingRequired.forEach(field => {
          console.log(`  - ${field}`);
        });
      }
    }

    // 3. Check row counts
    console.log('\n\n[STEP 3] Checking data counts...\n');

    const companyCountQuery = 'SELECT COUNT(*) as count FROM marketing.company_master';
    const peopleCountQuery = 'SELECT COUNT(*) as count FROM marketing.people_master';

    const companyCount = await client.query(companyCountQuery);
    const peopleCount = await client.query(peopleCountQuery);

    console.log(`Companies in database: ${companyCount.rows[0].count}`);
    console.log(`People in database: ${peopleCount.rows[0].count}`);

    // 4. Sample query for executives
    console.log('\n\n[STEP 4] Testing executive query...\n');

    const executiveQuery = `
      SELECT
        pm.unique_id,
        pm.full_name,
        pm.title,
        pm.seniority,
        pm.email,
        pm.linkedin_url,
        cm.company_name
      FROM marketing.people_master pm
      JOIN marketing.company_master cm ON pm.company_unique_id = cm.company_unique_id
      WHERE pm.seniority = 'c-suite'
        OR pm.title ILIKE '%CEO%'
        OR pm.title ILIKE '%CFO%'
        OR pm.title ILIKE '%CHRO%'
      LIMIT 5;
    `;

    try {
      const execResult = await client.query(executiveQuery);
      console.log(`Found ${execResult.rows.length} existing executive records:`);

      if (execResult.rows.length > 0) {
        execResult.rows.forEach((row, i) => {
          console.log(`\n  ${i + 1}. ${row.full_name} - ${row.title}`);
          console.log(`     Company: ${row.company_name}`);
          console.log(`     Email: ${row.email || 'N/A'}`);
          console.log(`     LinkedIn: ${row.linkedin_url || 'N/A'}`);
        });
      } else {
        console.log('  (No executives currently in database)');
      }
    } catch (error) {
      console.log(`❌ Executive query failed: ${error.message}`);
    }

    // 5. Generate summary
    console.log('\n\n=== VALIDATION SUMMARY ===\n');

    console.log('Schema Status:');
    console.log(`  ✅ marketing.company_master: ${companyResult.rows.length > 0 ? 'EXISTS' : 'MISSING'}`);
    console.log(`  ✅ marketing.people_master: ${peopleResult.rows.length > 0 ? 'EXISTS' : 'MISSING'}`);

    console.log('\nRecommended Approach:');
    console.log('  ✅ Use normalized design (people_master)');
    console.log('  ✅ Link executives via company_unique_id');
    console.log('  ✅ Filter by title/seniority for executive queries');

    console.log('\nNext Steps:');
    console.log('  1. Review enrichment_process_audit.md');
    console.log('  2. Choose architecture (denormalized vs normalized)');
    console.log('  3. Create executive enrichment workflow');
    console.log('  4. Test with 1 company');

  } catch (error) {
    console.error('\n❌ Validation failed:', error);
    throw error;
  } finally {
    await client.end();
    console.log('\n✅ Database connection closed\n');
  }
}

// Run validation
validateSchema()
  .then(() => {
    console.log('✅ Schema validation complete!');
    process.exit(0);
  })
  .catch(error => {
    console.error('❌ Validation error:', error.message);
    process.exit(1);
  });

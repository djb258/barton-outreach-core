#!/usr/bin/env node
/**
 * Create Hub + Spoke Views
 */

const { Client } = require('pg');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '..', '..', '..', '.env') });

async function createViews() {
  const client = new Client({
    connectionString: process.env.DATABASE_URL || process.env.NEON_CONNECTION_STRING
  });

  try {
    await client.connect();
    console.log('Connected - creating views...\n');

    // Company views
    console.log('Creating company schema views...');

    await client.query(`
      CREATE OR REPLACE VIEW company.v_enrichment_status AS
      SELECT
        cm.company_unique_id,
        cm.company_name,
        cm.address_state,
        CASE WHEN cm.ein IS NOT NULL THEN 1 ELSE 0 END as has_ein,
        CASE WHEN cm.email_pattern IS NOT NULL THEN 1 ELSE 0 END as has_email_pattern,
        CASE WHEN cm.linkedin_url IS NOT NULL THEN 1 ELSE 0 END as has_linkedin,
        CASE WHEN cm.website_url IS NOT NULL THEN 1 ELSE 0 END as has_website,
        (SELECT COUNT(*) FROM people.company_slot cs
         WHERE cs.company_unique_id = cm.company_unique_id
         AND cs.person_unique_id IS NOT NULL) as slots_filled,
        company.calculate_bit_score(cm.company_unique_id) as bit_score
      FROM company.company_master cm
    `);
    console.log('  Created: company.v_enrichment_status');

    await client.query(`
      CREATE OR REPLACE VIEW company.v_needs_enrichment AS
      SELECT
        company_unique_id, company_name, address_state,
        CASE
          WHEN ein IS NULL THEN 'ein'
          WHEN email_pattern IS NULL THEN 'email_pattern'
          ELSE 'complete'
        END as next_needed
      FROM company.company_master
      WHERE ein IS NULL OR email_pattern IS NULL
      ORDER BY CASE WHEN ein IS NULL AND email_pattern IS NULL THEN 1
                    WHEN ein IS NULL THEN 2 ELSE 3 END
    `);
    console.log('  Created: company.v_needs_enrichment');

    // Clay views
    console.log('\nCreating clay schema views...');

    await client.query(`
      CREATE OR REPLACE VIEW clay.v_companies_for_enrichment AS
      SELECT
        cm.company_unique_id,
        cm.company_name,
        cm.address_city,
        cm.address_state,
        cm.linkedin_url,
        cm.website_url
      FROM company.company_master cm
      WHERE cm.ein IS NULL
         OR cm.email_pattern IS NULL
         OR cm.linkedin_url IS NULL
    `);
    console.log('  Created: clay.v_companies_for_enrichment');

    await client.query(`
      CREATE OR REPLACE VIEW clay.v_people_for_enrichment AS
      SELECT
        cs.company_unique_id,
        cs.slot_type,
        cm.company_name,
        pm.unique_id as person_unique_id,
        pm.first_name,
        pm.last_name,
        pm.linkedin_url
      FROM people.company_slot cs
      JOIN company.company_master cm ON cm.company_unique_id = cs.company_unique_id
      LEFT JOIN people.people_master pm ON pm.unique_id = cs.person_unique_id
      WHERE cs.person_unique_id IS NULL
         OR pm.linkedin_url IS NULL
    `);
    console.log('  Created: clay.v_people_for_enrichment');

    // DOL views
    console.log('\nCreating dol schema views...');

    await client.query(`
      CREATE OR REPLACE VIEW dol.v_5500_summary AS
      SELECT
        f.sponsor_dfe_name,
        f.sponsor_dfe_ein,
        f.spons_dfe_loc_us_state as state,
        COUNT(*) as filing_count,
        MAX(f.date_received) as latest_filing,
        SUM(COALESCE(f.tot_partcp_boy_cnt, 0)) as total_participants
      FROM dol.form_5500 f
      GROUP BY f.sponsor_dfe_name, f.sponsor_dfe_ein, f.spons_dfe_loc_us_state
    `);
    console.log('  Created: dol.v_5500_summary');

    await client.query(`
      CREATE OR REPLACE VIEW dol.v_schedule_a_carriers AS
      SELECT
        a.insurance_company_name,
        a.insurance_company_ein,
        COUNT(DISTINCT a.ack_id) as policy_count,
        SUM(COALESCE(a.covered_lives, 0)) as total_covered_lives
      FROM dol.schedule_a a
      WHERE a.insurance_company_name IS NOT NULL
      GROUP BY a.insurance_company_name, a.insurance_company_ein
      ORDER BY policy_count DESC
    `);
    console.log('  Created: dol.v_schedule_a_carriers');

    // People views
    console.log('\nCreating people schema views...');

    await client.query(`
      CREATE OR REPLACE VIEW people.v_slot_coverage AS
      SELECT
        cm.company_unique_id,
        cm.company_name,
        cs.slot_type,
        CASE WHEN cs.person_unique_id IS NOT NULL THEN 'FILLED' ELSE 'EMPTY' END as status,
        pm.first_name,
        pm.last_name,
        pm.title,
        pm.linkedin_url
      FROM company.company_master cm
      JOIN people.company_slot cs ON cs.company_unique_id = cm.company_unique_id
      LEFT JOIN people.people_master pm ON pm.unique_id = cs.person_unique_id
      ORDER BY cm.company_name, cs.slot_type
    `);
    console.log('  Created: people.v_slot_coverage');

    // Log completion
    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status)
      VALUES ('hub_spoke_reorg_phase3', 'CREATE_VIEWS', 'SUCCESS')
    `);

    // Final verification
    console.log('\nVerifying views created...');
    const views = await client.query(`
      SELECT table_schema, table_name
      FROM information_schema.views
      WHERE table_schema IN ('company', 'dol', 'people', 'clay')
      ORDER BY table_schema, table_name
    `);

    console.log('\nViews by schema:');
    let schema = '';
    for (const v of views.rows) {
      if (v.table_schema !== schema) {
        schema = v.table_schema;
        console.log('  ' + schema + ':');
      }
      console.log('    - ' + v.table_name);
    }

    // Test cross-schema query
    console.log('\nTesting cross-schema query...');
    const test = await client.query(`
      SELECT company_name, slots_filled, bit_score
      FROM company.v_enrichment_status
      LIMIT 5
    `);
    console.log('Test query returned ' + test.rows.length + ' rows - SUCCESS');

    console.log('\nVIEWS CREATED SUCCESSFULLY!');

  } catch (error) {
    console.error('Error:', error.message);
    throw error;
  } finally {
    await client.end();
  }
}

createViews().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});

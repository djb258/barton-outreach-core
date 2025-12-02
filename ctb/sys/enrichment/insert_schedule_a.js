#!/usr/bin/env node
/**
 * Insert Schedule A from Staging to Main Table
 */

const { Client } = require('pg');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '..', '..', '..', '.env') });

async function insertScheduleA() {
  const client = new Client({
    connectionString: process.env.DATABASE_URL || process.env.NEON_CONNECTION_STRING
  });

  try {
    await client.connect();
    console.log('Connected to Neon PostgreSQL');

    console.log('\nInserting schedule_a from staging (336K rows)...');

    const insertSQL = `
      INSERT INTO marketing.schedule_a (
        ack_id, sch_a_plan_year_begin_date, sch_a_plan_year_end_date,
        insurance_company_name, insurance_company_ein, contract_number,
        covered_lives, policy_year_begin_date, policy_year_end_date
      )
      SELECT
        ack_id,
        CASE WHEN sch_a_plan_year_begin_date ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN sch_a_plan_year_begin_date::date ELSE NULL END,
        CASE WHEN sch_a_plan_year_end_date ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN sch_a_plan_year_end_date::date ELSE NULL END,
        insurance_company_name,
        insurance_company_ein,
        contract_number,
        NULLIF(covered_lives, '')::integer,
        CASE WHEN policy_year_begin_date ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN policy_year_begin_date::date ELSE NULL END,
        CASE WHEN policy_year_end_date ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN policy_year_end_date::date ELSE NULL END
      FROM marketing.schedule_a_staging
    `;

    const scha_result = await client.query(insertSQL);
    console.log('Schedule A inserted: ' + (scha_result.rowCount || 0).toLocaleString() + ' rows');

    // Verify counts
    const countSQL = `
      SELECT
        (SELECT COUNT(*) FROM marketing.form_5500) as form_5500,
        (SELECT COUNT(*) FROM marketing.form_5500_sf) as form_5500_sf,
        (SELECT COUNT(*) FROM marketing.schedule_a) as schedule_a
    `;

    const counts = await client.query(countSQL);

    const f5500 = parseInt(counts.rows[0].form_5500);
    const f5500sf = parseInt(counts.rows[0].form_5500_sf);
    const scheda = parseInt(counts.rows[0].schedule_a);
    const total = f5500 + f5500sf + scheda;

    console.log('\n' + '='.repeat(80));
    console.log('FINAL MAIN TABLE COUNTS');
    console.log('='.repeat(80));
    console.log('  form_5500:    ' + f5500.toLocaleString() + ' rows (expected: 230,009)');
    console.log('  form_5500_sf: ' + f5500sf.toLocaleString() + ' rows (expected: 759,569)');
    console.log('  schedule_a:   ' + scheda.toLocaleString() + ' rows (expected: 336,817)');
    console.log('  TOTAL:        ' + total.toLocaleString() + ' rows (expected: 1,326,395)');

    // Test hub-and-spoke join
    console.log('\n' + '='.repeat(80));
    console.log('HUB-AND-SPOKE JOIN TEST');
    console.log('='.repeat(80));

    const joinSQL = `
      SELECT f.sponsor_dfe_name, COUNT(a.ack_id) as insurance_contracts
      FROM marketing.form_5500 f
      JOIN marketing.schedule_a a ON f.ack_id = a.ack_id
      GROUP BY f.sponsor_dfe_name
      ORDER BY insurance_contracts DESC
      LIMIT 10
    `;

    const joinTest = await client.query(joinSQL);

    console.log('\nTop 10 Companies by Insurance Contracts:');
    joinTest.rows.forEach((row, i) => {
      const name = row.sponsor_dfe_name ? row.sponsor_dfe_name.substring(0, 50) : 'Unknown';
      console.log('  ' + (i+1) + '. ' + name + ': ' + parseInt(row.insurance_contracts).toLocaleString() + ' contracts');
    });

    console.log('\n' + '='.repeat(80));
    console.log('DOL FORM 5500 IMPORT COMPLETE!');
    console.log('='.repeat(80));

  } catch (error) {
    console.error('Error:', error.message);
    throw error;
  } finally {
    await client.end();
  }
}

insertScheduleA().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});

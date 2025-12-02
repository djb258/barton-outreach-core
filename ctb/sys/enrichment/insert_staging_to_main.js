#!/usr/bin/env node
/**
 * Direct Insert from Staging to Main Tables
 *
 * Handles type conversions for:
 * - text -> date
 * - text -> integer
 * - text -> varchar
 */

const { Client } = require('pg');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '..', '..', '..', '.env') });

async function insertStagingToMain() {
  const client = new Client({
    connectionString: process.env.DATABASE_URL || process.env.NEON_CONNECTION_STRING
  });

  try {
    await client.connect();
    console.log('Connected to Neon PostgreSQL');

    console.log('\n' + '='.repeat(80));
    console.log('INSERTING FORM 5500-SF FROM STAGING TO MAIN TABLE');
    console.log('='.repeat(80));

    // Insert form_5500_sf with explicit column list and type casting
    console.log('\nInserting form_5500_sf from staging (759K rows)...');
    const sf_result = await client.query(`
      INSERT INTO marketing.form_5500_sf (
        ack_id, filing_status, date_received, valid_sig,
        sponsor_dfe_ein, sponsor_dfe_name,
        spons_dfe_mail_us_address1, spons_dfe_mail_us_address2,
        spons_dfe_mail_us_city, spons_dfe_mail_us_state, spons_dfe_mail_us_zip,
        spons_dfe_loc_us_address1, spons_dfe_loc_us_address2,
        spons_dfe_loc_us_city, spons_dfe_loc_us_state, spons_dfe_loc_us_zip,
        spons_dfe_phone_num, business_code, plan_name, plan_number,
        plan_type_pension_ind, plan_type_welfare_ind,
        funding_insurance_ind, funding_trust_ind, funding_gen_assets_ind,
        benefit_insurance_ind, benefit_trust_ind, benefit_gen_assets_ind,
        tot_active_partcp_boy_cnt, tot_partcp_boy_cnt,
        tot_active_partcp_eoy_cnt, tot_partcp_eoy_cnt,
        participant_cnt_rptd_ind, short_plan_year_ind, dfvc_program_ind,
        sch_a_attached_ind, num_sch_a_attached_cnt,
        sch_c_attached_ind, sch_d_attached_ind, sch_g_attached_ind,
        sch_h_attached_ind, sch_i_attached_ind, sch_mb_attached_ind,
        sch_sb_attached_ind, sch_r_attached_ind, mewa_m1_attached_ind,
        form_year
      )
      SELECT
        ack_id, filing_status,
        CASE WHEN date_received ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN date_received::date ELSE NULL END,
        valid_sig,
        sponsor_dfe_ein, sponsor_dfe_name,
        spons_dfe_mail_us_address1, spons_dfe_mail_us_address2,
        spons_dfe_mail_us_city, spons_dfe_mail_us_state, spons_dfe_mail_us_zip,
        spons_dfe_loc_us_address1, spons_dfe_loc_us_address2,
        spons_dfe_loc_us_city, spons_dfe_loc_us_state, spons_dfe_loc_us_zip,
        spons_dfe_phone_num, business_code, plan_name, plan_number,
        plan_type_pension_ind, plan_type_welfare_ind,
        funding_insurance_ind, funding_trust_ind, funding_gen_assets_ind,
        benefit_insurance_ind, benefit_trust_ind, benefit_gen_assets_ind,
        NULLIF(tot_active_partcp_boy_cnt, '')::integer,
        NULLIF(tot_partcp_boy_cnt, '')::integer,
        NULLIF(tot_active_partcp_eoy_cnt, '')::integer,
        NULLIF(tot_partcp_eoy_cnt, '')::integer,
        participant_cnt_rptd_ind, short_plan_year_ind, dfvc_program_ind,
        sch_a_attached_ind, NULLIF(num_sch_a_attached_cnt, '')::integer,
        sch_c_attached_ind, sch_d_attached_ind, sch_g_attached_ind,
        sch_h_attached_ind, sch_i_attached_ind, sch_mb_attached_ind,
        sch_sb_attached_ind, sch_r_attached_ind, mewa_m1_attached_ind,
        NULLIF(form_year, '')::integer
      FROM marketing.form_5500_sf_staging
      ON CONFLICT (ack_id) DO NOTHING
    `);
    console.log('Form 5500-SF inserted: ' + (sf_result.rowCount || 0).toLocaleString() + ' rows');

    // Verify count
    const sf_count = await client.query('SELECT COUNT(*) FROM marketing.form_5500_sf');
    console.log('form_5500_sf now has: ' + parseInt(sf_count.rows[0].count).toLocaleString() + ' rows');

    console.log('\n' + '='.repeat(80));
    console.log('INSERTING SCHEDULE A FROM STAGING TO MAIN TABLE');
    console.log('='.repeat(80));

    // Check schedule_a columns
    const schaCols = await client.query(`
      SELECT column_name, data_type FROM information_schema.columns
      WHERE table_schema = 'marketing' AND table_name = 'schedule_a'
      ORDER BY ordinal_position
    `);
    console.log('\nSchedule A columns: ' + schaCols.rows.map(r => r.column_name).join(', '));

    const schaStagingCols = await client.query(`
      SELECT column_name FROM information_schema.columns
      WHERE table_schema = 'marketing' AND table_name = 'schedule_a_staging'
      ORDER BY ordinal_position
    `);
    console.log('Schedule A staging columns: ' + schaStagingCols.rows.map(r => r.column_name).join(', '));

    // Insert schedule_a - only matching columns between staging and main
    console.log('\nInserting schedule_a from staging (336K rows)...');
    const scha_result = await client.query(`
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
      ON CONFLICT (ack_id, insurance_company_ein, contract_number) DO NOTHING
    `);
    console.log('Schedule A inserted: ' + (scha_result.rowCount || 0).toLocaleString() + ' rows');

    // Verify count
    const scha_count = await client.query('SELECT COUNT(*) FROM marketing.schedule_a');
    console.log('schedule_a now has: ' + parseInt(scha_count.rows[0].count).toLocaleString() + ' rows');

    // Final summary
    console.log('\n' + '='.repeat(80));
    console.log('FINAL MAIN TABLE COUNTS');
    console.log('='.repeat(80));

    const counts = await client.query(`
      SELECT
        (SELECT COUNT(*) FROM marketing.form_5500) as form_5500,
        (SELECT COUNT(*) FROM marketing.form_5500_sf) as form_5500_sf,
        (SELECT COUNT(*) FROM marketing.schedule_a) as schedule_a
    `);

    const f5500 = parseInt(counts.rows[0].form_5500);
    const f5500sf = parseInt(counts.rows[0].form_5500_sf);
    const scheda = parseInt(counts.rows[0].schedule_a);
    const total = f5500 + f5500sf + scheda;

    console.log('  form_5500:    ' + f5500.toLocaleString() + ' rows (expected: 230,009)');
    console.log('  form_5500_sf: ' + f5500sf.toLocaleString() + ' rows (expected: 759,569)');
    console.log('  schedule_a:   ' + scheda.toLocaleString() + ' rows (expected: 336,817)');
    console.log('  TOTAL:        ' + total.toLocaleString() + ' rows (expected: 1,326,395)');

    // Test hub-and-spoke join
    console.log('\n' + '='.repeat(80));
    console.log('HUB-AND-SPOKE JOIN TEST');
    console.log('='.repeat(80));

    const joinTest = await client.query(`
      SELECT f.sponsor_dfe_name, COUNT(a.ack_id) as insurance_contracts
      FROM marketing.form_5500 f
      JOIN marketing.schedule_a a ON f.ack_id = a.ack_id
      GROUP BY f.sponsor_dfe_name
      ORDER BY insurance_contracts DESC
      LIMIT 10
    `);

    console.log('\nTop 10 Companies by Insurance Contracts:');
    joinTest.rows.forEach((row, i) => {
      console.log(`  ${i+1}. ${row.sponsor_dfe_name.substring(0, 50)}: ${parseInt(row.insurance_contracts).toLocaleString()} contracts`);
    });

    console.log('\n' + '='.repeat(80));
    console.log('IMPORT COMPLETE!');
    console.log('='.repeat(80));

  } catch (error) {
    console.error('Error:', error.message);
    throw error;
  } finally {
    await client.end();
  }
}

insertStagingToMain().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});

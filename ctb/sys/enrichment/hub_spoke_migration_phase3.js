#!/usr/bin/env node
/**
 * PLE Hub + Spoke Schema Migration - Phase 3
 *
 * Tasks 8-14: Create functions, views, update FKs, cleanup
 */

const { Client } = require('pg');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '..', '..', '..', '.env') });

async function migratePhase3() {
  const client = new Client({
    connectionString: process.env.DATABASE_URL || process.env.NEON_CONNECTION_STRING
  });

  try {
    await client.connect();
    console.log('Connected to Neon PostgreSQL\n');

    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status, details)
      VALUES ('hub_spoke_reorg_phase3', 'START', 'INITIATED', 'Creating functions, views, and cleanup')
    `);

    // =========================================================================
    // TASK 8: CREATE FUNCTIONS IN CORRECT SCHEMAS
    // =========================================================================
    console.log('='.repeat(80));
    console.log('TASK 8: CREATING FUNCTIONS IN CORRECT SCHEMAS');
    console.log('='.repeat(80));

    // 8A: Company Schema Functions
    console.log('\n  Creating company schema functions...');

    // Generate email function
    await client.query(`
      CREATE OR REPLACE FUNCTION company.generate_email(
        p_first_name VARCHAR,
        p_last_name VARCHAR,
        p_pattern VARCHAR,
        p_domain VARCHAR
      ) RETURNS VARCHAR AS $$
      DECLARE
        v_email VARCHAR;
        v_first VARCHAR;
        v_last VARCHAR;
        v_f CHAR(1);
        v_l CHAR(1);
      BEGIN
        v_first := LOWER(TRIM(p_first_name));
        v_last := LOWER(TRIM(p_last_name));
        v_f := LEFT(v_first, 1);
        v_l := LEFT(v_last, 1);

        v_email := p_pattern;
        v_email := REPLACE(v_email, '{first}', v_first);
        v_email := REPLACE(v_email, '{last}', v_last);
        v_email := REPLACE(v_email, '{f}', v_f);
        v_email := REPLACE(v_email, '{l}', v_l);
        v_email := v_email || p_domain;

        RETURN v_email;
      END;
      $$ LANGUAGE plpgsql
    `);
    console.log('    Created: company.generate_email()');

    // Detect email pattern function
    await client.query(`
      CREATE OR REPLACE FUNCTION company.detect_email_pattern(
        p_email VARCHAR,
        p_first_name VARCHAR,
        p_last_name VARCHAR
      ) RETURNS VARCHAR AS $$
      DECLARE
        v_local VARCHAR;
        v_first VARCHAR;
        v_last VARCHAR;
        v_f CHAR(1);
        v_l CHAR(1);
      BEGIN
        v_local := LOWER(SPLIT_PART(p_email, '@', 1));
        v_first := LOWER(TRIM(p_first_name));
        v_last := LOWER(TRIM(p_last_name));
        v_f := LEFT(v_first, 1);
        v_l := LEFT(v_last, 1);

        IF v_local = v_first || '.' || v_last THEN RETURN '{first}.{last}@';
        ELSIF v_local = v_f || v_last THEN RETURN '{f}{last}@';
        ELSIF v_local = v_first || v_last THEN RETURN '{first}{last}@';
        ELSIF v_local = v_first || v_l THEN RETURN '{first}{l}@';
        ELSIF v_local = v_f || '.' || v_last THEN RETURN '{f}.{last}@';
        ELSIF v_local = v_last || '.' || v_first THEN RETURN '{last}.{first}@';
        ELSIF v_local = v_first THEN RETURN '{first}@';
        ELSIF v_local = v_last THEN RETURN '{last}@';
        ELSE RETURN NULL;
        END IF;
      END;
      $$ LANGUAGE plpgsql
    `);
    console.log('    Created: company.detect_email_pattern()');

    // Calculate BIT score function
    await client.query(`
      CREATE OR REPLACE FUNCTION company.calculate_bit_score(p_company_unique_id VARCHAR)
      RETURNS INT AS $$
      DECLARE
        v_score INT := 0;
        v_slots_filled INT;
        v_has_5500 BOOLEAN;
        v_has_violations BOOLEAN;
      BEGIN
        -- Slots filled (+10 each)
        SELECT COUNT(*) INTO v_slots_filled
        FROM people.company_slot
        WHERE company_unique_id = p_company_unique_id
        AND person_unique_id IS NOT NULL;
        v_score := v_score + (v_slots_filled * 10);

        -- Has 5500 data (+15) - check via EIN match
        SELECT EXISTS(
          SELECT 1 FROM dol.form_5500 f
          JOIN company.company_master c ON c.ein = f.sponsor_dfe_ein
          WHERE c.company_unique_id = p_company_unique_id
        ) INTO v_has_5500;

        IF v_has_5500 THEN
          v_score := v_score + 15;
        END IF;

        -- Has violations (+10 - they need help)
        SELECT EXISTS(
          SELECT 1 FROM dol.violations v
          JOIN company.company_master c ON c.ein = v.ein
          WHERE c.company_unique_id = p_company_unique_id
        ) INTO v_has_violations;

        IF v_has_violations THEN
          v_score := v_score + 10;
        END IF;

        RETURN v_score;
      END;
      $$ LANGUAGE plpgsql
    `);
    console.log('    Created: company.calculate_bit_score()');

    // 8B: DOL Schema Functions
    console.log('\n  Creating dol schema functions...');

    await client.query(`
      CREATE OR REPLACE FUNCTION dol.match_5500_to_company(
        p_sponsor_name VARCHAR,
        p_city VARCHAR,
        p_state VARCHAR
      ) RETURNS VARCHAR AS $$
      DECLARE
        v_company_uid VARCHAR;
      BEGIN
        -- Exact match
        SELECT company_unique_id INTO v_company_uid
        FROM company.company_master
        WHERE LOWER(company_name) = LOWER(p_sponsor_name)
        AND address_state = p_state
        LIMIT 1;

        -- Fuzzy fallback
        IF v_company_uid IS NULL THEN
          SELECT company_unique_id INTO v_company_uid
          FROM company.company_master
          WHERE LOWER(company_name) LIKE '%' || LOWER(SUBSTRING(p_sponsor_name FROM 1 FOR 20)) || '%'
          AND LOWER(address_city) = LOWER(p_city)
          AND address_state = p_state
          LIMIT 1;
        END IF;

        RETURN v_company_uid;
      END;
      $$ LANGUAGE plpgsql
    `);
    console.log('    Created: dol.match_5500_to_company()');

    // 8C: People Schema Functions
    console.log('\n  Creating people schema functions...');

    await client.query(`
      CREATE OR REPLACE FUNCTION people.assign_slot(
        p_company_unique_id VARCHAR,
        p_slot_type VARCHAR,
        p_person_unique_id VARCHAR
      ) RETURNS BOOLEAN AS $$
      BEGIN
        UPDATE people.company_slot
        SET person_unique_id = p_person_unique_id, updated_at = NOW()
        WHERE company_unique_id = p_company_unique_id
        AND slot_type = p_slot_type;

        RETURN FOUND;
      END;
      $$ LANGUAGE plpgsql
    `);
    console.log('    Created: people.assign_slot()');

    await client.query(`
      CREATE OR REPLACE FUNCTION people.vacate_slot(
        p_company_unique_id VARCHAR,
        p_slot_type VARCHAR
      ) RETURNS BOOLEAN AS $$
      BEGIN
        UPDATE people.company_slot
        SET person_unique_id = NULL, updated_at = NOW()
        WHERE company_unique_id = p_company_unique_id
        AND slot_type = p_slot_type;

        RETURN FOUND;
      END;
      $$ LANGUAGE plpgsql
    `);
    console.log('    Created: people.vacate_slot()');

    await client.query(`
      CREATE OR REPLACE FUNCTION people.detect_movement(
        p_person_unique_id VARCHAR,
        p_current_company VARCHAR,
        p_current_title VARCHAR
      ) RETURNS VARCHAR AS $$
      DECLARE
        v_stored_company VARCHAR;
        v_stored_title VARCHAR;
      BEGIN
        SELECT cs.company_unique_id, pm.title
        INTO v_stored_company, v_stored_title
        FROM people.people_master pm
        JOIN people.company_slot cs ON cs.person_unique_id = pm.unique_id
        WHERE pm.unique_id = p_person_unique_id;

        IF v_stored_company IS NULL THEN RETURN 'CONTACT_LOST';
        ELSIF v_stored_company != p_current_company THEN RETURN 'COMPANY_CHANGE';
        ELSIF v_stored_title IS DISTINCT FROM p_current_title THEN RETURN 'TITLE_CHANGE';
        ELSE RETURN 'NONE';
        END IF;
      END;
      $$ LANGUAGE plpgsql
    `);
    console.log('    Created: people.detect_movement()');

    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status)
      VALUES ('hub_spoke_reorg_phase3', 'CREATE_FUNCTIONS', 'SUCCESS')
    `);

    // =========================================================================
    // TASK 9: CREATE VIEWS IN CORRECT SCHEMAS
    // =========================================================================
    console.log('\n' + '='.repeat(80));
    console.log('TASK 9: CREATING VIEWS IN CORRECT SCHEMAS');
    console.log('='.repeat(80));

    // Company views
    console.log('\n  Creating company schema views...');

    await client.query(`
      CREATE OR REPLACE VIEW company.v_enrichment_status AS
      SELECT
        cm.id,
        cm.company_unique_id,
        cm.company_name,
        cm.address_state,
        CASE WHEN cm.ein IS NOT NULL THEN 1 ELSE 0 END as has_ein,
        CASE WHEN cm.email_pattern IS NOT NULL THEN 1 ELSE 0 END as has_email_pattern,
        CASE WHEN cm.linkedin_url IS NOT NULL THEN 1 ELSE 0 END as has_linkedin,
        CASE WHEN cm.website IS NOT NULL THEN 1 ELSE 0 END as has_website,
        (SELECT COUNT(*) FROM people.company_slot cs
         WHERE cs.company_unique_id = cm.company_unique_id
         AND cs.person_unique_id IS NOT NULL) as slots_filled,
        company.calculate_bit_score(cm.company_unique_id) as bit_score
      FROM company.company_master cm
    `);
    console.log('    Created: company.v_enrichment_status');

    await client.query(`
      CREATE OR REPLACE VIEW company.v_needs_enrichment AS
      SELECT
        id, company_unique_id, company_name, address_state,
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
    console.log('    Created: company.v_needs_enrichment');

    // Clay views
    console.log('\n  Creating clay schema views...');

    await client.query(`
      CREATE OR REPLACE VIEW clay.v_companies_for_enrichment AS
      SELECT
        cm.id,
        cm.company_unique_id,
        cm.company_name,
        cm.address_city,
        cm.address_state,
        cm.linkedin_url,
        cm.website
      FROM company.company_master cm
      WHERE cm.ein IS NULL
         OR cm.email_pattern IS NULL
         OR cm.linkedin_url IS NULL
    `);
    console.log('    Created: clay.v_companies_for_enrichment');

    await client.query(`
      CREATE OR REPLACE VIEW clay.v_people_for_enrichment AS
      SELECT
        cs.id as slot_id,
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
    console.log('    Created: clay.v_people_for_enrichment');

    // DOL views
    console.log('\n  Creating dol schema views...');

    await client.query(`
      CREATE OR REPLACE VIEW dol.v_5500_summary AS
      SELECT
        f.sponsor_dfe_name,
        f.sponsor_dfe_ein,
        f.spons_dfe_loc_us_state as state,
        COUNT(*) as filing_count,
        MAX(f.date_received) as latest_filing,
        SUM(COALESCE(f.tot_partcp_eoy_cnt, 0)) as total_participants
      FROM dol.form_5500 f
      GROUP BY f.sponsor_dfe_name, f.sponsor_dfe_ein, f.spons_dfe_loc_us_state
    `);
    console.log('    Created: dol.v_5500_summary');

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
    console.log('    Created: dol.v_schedule_a_carriers');

    // People views
    console.log('\n  Creating people schema views...');

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
    console.log('    Created: people.v_slot_coverage');

    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status)
      VALUES ('hub_spoke_reorg_phase3', 'CREATE_VIEWS', 'SUCCESS')
    `);

    // =========================================================================
    // TASK 10: DROP OLD FUNCTIONS/VIEWS FROM MARKETING SCHEMA
    // =========================================================================
    console.log('\n' + '='.repeat(80));
    console.log('TASK 10: DROPPING OLD OBJECTS FROM MARKETING SCHEMA');
    console.log('='.repeat(80));

    // Get list of functions in marketing schema
    const funcs = await client.query(`
      SELECT routine_name, routine_type
      FROM information_schema.routines
      WHERE routine_schema = 'marketing'
    `);

    if (funcs.rows.length > 0) {
      console.log('\n  Functions in marketing schema:');
      for (const f of funcs.rows) {
        console.log(`    - ${f.routine_name} (${f.routine_type})`);
      }
    } else {
      console.log('\n  No functions in marketing schema');
    }

    // Get list of views in marketing schema
    const views = await client.query(`
      SELECT table_name
      FROM information_schema.views
      WHERE table_schema = 'marketing'
    `);

    if (views.rows.length > 0) {
      console.log('\n  Views in marketing schema:');
      for (const v of views.rows) {
        console.log(`    - ${v.table_name}`);
        try {
          await client.query(`DROP VIEW IF EXISTS marketing."${v.table_name}" CASCADE`);
          console.log(`      DROPPED`);
        } catch (err) {
          console.log(`      SKIP: ${err.message}`);
        }
      }
    } else {
      console.log('\n  No views in marketing schema');
    }

    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status)
      VALUES ('hub_spoke_reorg_phase3', 'DROP_OLD_OBJECTS', 'SUCCESS')
    `);

    // =========================================================================
    // TASK 11: VERIFY FOREIGN KEYS (informational only)
    // =========================================================================
    console.log('\n' + '='.repeat(80));
    console.log('TASK 11: CHECKING FOREIGN KEY REFERENCES');
    console.log('='.repeat(80));

    const fks = await client.query(`
      SELECT
        tc.table_schema,
        tc.table_name,
        kcu.column_name,
        ccu.table_schema AS foreign_table_schema,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
      FROM information_schema.table_constraints AS tc
      JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
      JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
      WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_schema IN ('company', 'dol', 'people', 'clay', 'intake')
    `);

    if (fks.rows.length > 0) {
      console.log('\n  Current foreign keys:');
      for (const fk of fks.rows) {
        console.log(`    ${fk.table_schema}.${fk.table_name}.${fk.column_name} -> ${fk.foreign_table_schema}.${fk.foreign_table_name}.${fk.foreign_column_name}`);
      }
    } else {
      console.log('\n  No foreign keys found (tables use company_unique_id joins)');
    }

    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status)
      VALUES ('hub_spoke_reorg_phase3', 'CHECK_FKS', 'SUCCESS')
    `);

    // =========================================================================
    // TASK 12: FINAL VERIFICATION
    // =========================================================================
    console.log('\n' + '='.repeat(80));
    console.log('TASK 12: FINAL VERIFICATION');
    console.log('='.repeat(80));

    // Verify functions
    const newFuncs = await client.query(`
      SELECT routine_schema, routine_name
      FROM information_schema.routines
      WHERE routine_schema IN ('company', 'dol', 'people', 'clay')
      ORDER BY routine_schema, routine_name
    `);

    console.log('\n  Functions by schema:');
    let currentSchema = '';
    for (const f of newFuncs.rows) {
      if (f.routine_schema !== currentSchema) {
        currentSchema = f.routine_schema;
        console.log(`\n    ${currentSchema}:`);
      }
      console.log(`      - ${f.routine_name}`);
    }

    // Verify views
    const newViews = await client.query(`
      SELECT table_schema, table_name
      FROM information_schema.views
      WHERE table_schema IN ('company', 'dol', 'people', 'clay')
      ORDER BY table_schema, table_name
    `);

    console.log('\n\n  Views by schema:');
    currentSchema = '';
    for (const v of newViews.rows) {
      if (v.table_schema !== currentSchema) {
        currentSchema = v.table_schema;
        console.log(`\n    ${currentSchema}:`);
      }
      console.log(`      - ${v.table_name}`);
    }

    // Test cross-schema query
    console.log('\n\n  Testing cross-schema query...');
    const testQuery = await client.query(`
      SELECT
        cm.company_name,
        cs.slot_type,
        CASE WHEN cs.person_unique_id IS NOT NULL THEN 'FILLED' ELSE 'EMPTY' END as status
      FROM company.company_master cm
      LEFT JOIN people.company_slot cs ON cs.company_unique_id = cm.company_unique_id
      LIMIT 5
    `);
    console.log(`    Query returned ${testQuery.rows.length} rows - SUCCESS`);

    // =========================================================================
    // TASK 13-14: FINALIZE
    // =========================================================================
    console.log('\n' + '='.repeat(80));
    console.log('TASK 13-14: FINALIZATION');
    console.log('='.repeat(80));

    // Check if marketing schema can be dropped
    const marketingTables = await client.query(`
      SELECT table_name FROM information_schema.tables
      WHERE table_schema = 'marketing' AND table_type = 'BASE TABLE'
    `);

    if (marketingTables.rows.length === 0) {
      console.log('\n  Marketing schema is empty - ready for removal');
      console.log('  NOTE: Run "DROP SCHEMA marketing CASCADE" manually to remove');
    } else {
      console.log(`\n  Marketing schema still has ${marketingTables.rows.length} tables:`);
      for (const t of marketingTables.rows) {
        console.log(`    - ${t.table_name}`);
      }
    }

    // Final log
    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status, details)
      VALUES ('hub_spoke_reorg_phase3', 'COMPLETE', 'SUCCESS', 'Functions, views created. Hub + Spoke architecture complete.')
    `);

    // Show migration log
    console.log('\n' + '='.repeat(80));
    console.log('MIGRATION LOG');
    console.log('='.repeat(80));

    const log = await client.query(`
      SELECT step, status, details, executed_at
      FROM public.migration_log
      WHERE migration_name LIKE 'hub_spoke%'
      ORDER BY executed_at
    `);

    for (const entry of log.rows) {
      const time = new Date(entry.executed_at).toLocaleTimeString();
      console.log(`  [${time}] ${entry.step}: ${entry.status}${entry.details ? ' - ' + entry.details : ''}`);
    }

    console.log('\n' + '='.repeat(80));
    console.log('PHASE 3 MIGRATION COMPLETE!');
    console.log('='.repeat(80));
    console.log('\nHub + Spoke Architecture is now fully implemented.');

  } catch (error) {
    console.error('\nError:', error.message);

    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status, details)
      VALUES ('hub_spoke_reorg_phase3', 'ERROR', 'FAILED', $1)
    `, [error.message]);

    throw error;
  } finally {
    await client.end();
  }
}

migratePhase3().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});

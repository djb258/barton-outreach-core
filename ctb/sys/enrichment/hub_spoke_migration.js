#!/usr/bin/env node
/**
 * PLE Hub + Spoke Schema Migration
 *
 * Reorganizes from flat marketing.* schema to:
 *   company.* (hub)
 *   dol.* (spoke)
 *   people.* (spoke)
 *   clay.* (spoke)
 *   intake.* (quarantine only)
 */

const { Client } = require('pg');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '..', '..', '..', '.env') });

async function migrate() {
  const client = new Client({
    connectionString: process.env.DATABASE_URL || process.env.NEON_CONNECTION_STRING
  });

  try {
    await client.connect();
    console.log('Connected to Neon PostgreSQL\n');

    // =========================================================================
    // TASK 0: DOCUMENT CURRENT STATE
    // =========================================================================
    console.log('='.repeat(80));
    console.log('TASK 0: DOCUMENTING CURRENT STATE');
    console.log('='.repeat(80));

    // Get all tables
    const tables = await client.query(`
      SELECT table_schema, table_name
      FROM information_schema.tables
      WHERE table_schema IN ('marketing', 'intake', 'public')
      AND table_type = 'BASE TABLE'
      ORDER BY table_schema, table_name
    `);

    console.log('\nCurrent tables:');
    for (const row of tables.rows) {
      const countRes = await client.query(`SELECT COUNT(*) FROM "${row.table_schema}"."${row.table_name}"`);
      console.log(`  ${row.table_schema}.${row.table_name}: ${parseInt(countRes.rows[0].count).toLocaleString()} rows`);
    }

    // Create migration log table
    await client.query(`
      CREATE TABLE IF NOT EXISTS public.migration_log (
        id SERIAL PRIMARY KEY,
        migration_name VARCHAR(100),
        step VARCHAR(200),
        status VARCHAR(20),
        details TEXT,
        executed_at TIMESTAMP DEFAULT NOW()
      )
    `);

    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status, details)
      VALUES ('hub_spoke_reorg', 'START', 'INITIATED', 'Beginning schema reorganization')
    `);

    // =========================================================================
    // TASK 1: CREATE NEW SCHEMAS
    // =========================================================================
    console.log('\n' + '='.repeat(80));
    console.log('TASK 1: CREATING NEW SCHEMAS');
    console.log('='.repeat(80));

    await client.query(`CREATE SCHEMA IF NOT EXISTS company`);
    await client.query(`COMMENT ON SCHEMA company IS 'Hub: The company record - all enrichment lands here'`);
    console.log('  Created: company schema (hub)');

    await client.query(`CREATE SCHEMA IF NOT EXISTS dol`);
    await client.query(`COMMENT ON SCHEMA dol IS 'Spoke: DOL federal data - Form 5500, Schedule A, violations'`);
    console.log('  Created: dol schema (spoke)');

    await client.query(`CREATE SCHEMA IF NOT EXISTS people`);
    await client.query(`COMMENT ON SCHEMA people IS 'Spoke: People as sensors - slots, occupants, movement tracking'`);
    console.log('  Created: people schema (spoke)');

    await client.query(`CREATE SCHEMA IF NOT EXISTS clay`);
    await client.query(`COMMENT ON SCHEMA clay IS 'Spoke: Clay.com enrichment engine - raw data intake'`);
    console.log('  Created: clay schema (spoke)');

    await client.query(`COMMENT ON SCHEMA intake IS 'Quarantine: Invalid records pending review'`);
    console.log('  Updated: intake schema (quarantine)');

    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status)
      VALUES ('hub_spoke_reorg', 'CREATE_SCHEMAS', 'SUCCESS')
    `);

    // =========================================================================
    // TASK 2: MIGRATE HUB (company_master)
    // =========================================================================
    console.log('\n' + '='.repeat(80));
    console.log('TASK 2: MIGRATING HUB (company_master)');
    console.log('='.repeat(80));

    const hubTable = await client.query(`
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'marketing' AND table_name = 'company_master'
    `);

    if (hubTable.rows.length > 0) {
      await client.query(`ALTER TABLE marketing.company_master SET SCHEMA company`);
      console.log('  Moved: marketing.company_master -> company.company_master');

      await client.query(`
        INSERT INTO public.migration_log (migration_name, step, status, details)
        VALUES ('hub_spoke_reorg', 'MOVE_COMPANY_MASTER', 'SUCCESS', 'company_master -> company schema')
      `);
    } else {
      console.log('  SKIP: company_master not found in marketing schema');
    }

    // =========================================================================
    // TASK 3: MIGRATE DOL SPOKE
    // =========================================================================
    console.log('\n' + '='.repeat(80));
    console.log('TASK 3: MIGRATING DOL SPOKE');
    console.log('='.repeat(80));

    // Form 5500
    const f5500 = await client.query(`
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'marketing' AND table_name = 'form_5500'
    `);
    if (f5500.rows.length > 0) {
      await client.query(`ALTER TABLE marketing.form_5500 SET SCHEMA dol`);
      console.log('  Moved: marketing.form_5500 -> dol.form_5500');
    }

    // Form 5500-SF
    const f5500sf = await client.query(`
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'marketing' AND table_name = 'form_5500_sf'
    `);
    if (f5500sf.rows.length > 0) {
      await client.query(`ALTER TABLE marketing.form_5500_sf SET SCHEMA dol`);
      console.log('  Moved: marketing.form_5500_sf -> dol.form_5500_sf');
    }

    // Schedule A
    const schedA = await client.query(`
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'marketing' AND table_name = 'schedule_a'
    `);
    if (schedA.rows.length > 0) {
      await client.query(`ALTER TABLE marketing.schedule_a SET SCHEMA dol`);
      console.log('  Moved: marketing.schedule_a -> dol.schedule_a');
    }

    // Form 5500 staging
    const f5500stg = await client.query(`
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'marketing' AND table_name = 'form_5500_staging'
    `);
    if (f5500stg.rows.length > 0) {
      await client.query(`ALTER TABLE marketing.form_5500_staging SET SCHEMA dol`);
      console.log('  Moved: marketing.form_5500_staging -> dol.form_5500_staging');
    }

    // Form 5500-SF staging
    const f5500sfstg = await client.query(`
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'marketing' AND table_name = 'form_5500_sf_staging'
    `);
    if (f5500sfstg.rows.length > 0) {
      await client.query(`ALTER TABLE marketing.form_5500_sf_staging SET SCHEMA dol`);
      console.log('  Moved: marketing.form_5500_sf_staging -> dol.form_5500_sf_staging');
    }

    // Schedule A staging
    const schedAstg = await client.query(`
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'marketing' AND table_name = 'schedule_a_staging'
    `);
    if (schedAstg.rows.length > 0) {
      await client.query(`ALTER TABLE marketing.schedule_a_staging SET SCHEMA dol`);
      console.log('  Moved: marketing.schedule_a_staging -> dol.schedule_a_staging');
    }

    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status, details)
      VALUES ('hub_spoke_reorg', 'MOVE_DOL_TABLES', 'SUCCESS', 'DOL tables -> dol schema')
    `);

    // =========================================================================
    // TASK 4: MIGRATE PEOPLE SPOKE
    // =========================================================================
    console.log('\n' + '='.repeat(80));
    console.log('TASK 4: MIGRATING PEOPLE SPOKE');
    console.log('='.repeat(80));

    // Company slots
    const slots = await client.query(`
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'marketing' AND table_name = 'company_slot'
    `);
    if (slots.rows.length > 0) {
      await client.query(`ALTER TABLE marketing.company_slot SET SCHEMA people`);
      console.log('  Moved: marketing.company_slot -> people.company_slot');
    }

    // People master
    const ppl = await client.query(`
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'marketing' AND table_name = 'people_master'
    `);
    if (ppl.rows.length > 0) {
      await client.query(`ALTER TABLE marketing.people_master SET SCHEMA people`);
      console.log('  Moved: marketing.people_master -> people.people_master');
    }

    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status, details)
      VALUES ('hub_spoke_reorg', 'MOVE_PEOPLE_TABLES', 'SUCCESS', 'People tables -> people schema')
    `);

    // =========================================================================
    // TASK 5: MIGRATE CLAY SPOKE
    // =========================================================================
    console.log('\n' + '='.repeat(80));
    console.log('TASK 5: MIGRATING CLAY SPOKE');
    console.log('='.repeat(80));

    // Company raw from Clay (check intake schema)
    const clayComp = await client.query(`
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'intake' AND table_name = 'company_raw_from_clay'
    `);
    if (clayComp.rows.length > 0) {
      await client.query(`ALTER TABLE intake.company_raw_from_clay SET SCHEMA clay`);
      await client.query(`ALTER TABLE clay.company_raw_from_clay RENAME TO company_raw`);
      console.log('  Moved: intake.company_raw_from_clay -> clay.company_raw');
    }

    // People raw from Clay
    const clayPpl = await client.query(`
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'intake' AND table_name = 'people_raw_from_clay'
    `);
    if (clayPpl.rows.length > 0) {
      await client.query(`ALTER TABLE intake.people_raw_from_clay SET SCHEMA clay`);
      await client.query(`ALTER TABLE clay.people_raw_from_clay RENAME TO people_raw`);
      console.log('  Moved: intake.people_raw_from_clay -> clay.people_raw');
    }

    // Clay intake table
    const clayIntake = await client.query(`
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'intake' AND table_name = 'clay_intake'
    `);
    if (clayIntake.rows.length > 0) {
      await client.query(`ALTER TABLE intake.clay_intake SET SCHEMA clay`);
      console.log('  Moved: intake.clay_intake -> clay.clay_intake');
    }

    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status, details)
      VALUES ('hub_spoke_reorg', 'MOVE_CLAY_TABLES', 'SUCCESS', 'Clay tables -> clay schema')
    `);

    // =========================================================================
    // TASK 6: SETUP QUARANTINE
    // =========================================================================
    console.log('\n' + '='.repeat(80));
    console.log('TASK 6: SETTING UP QUARANTINE');
    console.log('='.repeat(80));

    // Check if company_invalid exists and move to intake as quarantine
    const invalid = await client.query(`
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'marketing' AND table_name = 'company_invalid'
    `);
    if (invalid.rows.length > 0) {
      await client.query(`ALTER TABLE marketing.company_invalid SET SCHEMA intake`);
      await client.query(`ALTER TABLE intake.company_invalid RENAME TO quarantine`);
      console.log('  Moved: marketing.company_invalid -> intake.quarantine');
    } else {
      // Create quarantine table if doesn't exist
      await client.query(`
        CREATE TABLE IF NOT EXISTS intake.quarantine (
          id SERIAL PRIMARY KEY,
          source_system VARCHAR(50) NOT NULL,
          source_table VARCHAR(50),
          record_data JSONB NOT NULL,
          rejection_reason VARCHAR(500),
          rejection_code VARCHAR(50),
          created_at TIMESTAMP DEFAULT NOW(),
          reviewed_at TIMESTAMP,
          reviewed_by VARCHAR(100),
          resolution VARCHAR(50)
        )
      `);
      console.log('  Created: intake.quarantine table');
    }

    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status, details)
      VALUES ('hub_spoke_reorg', 'SETUP_QUARANTINE', 'SUCCESS', 'Intake schema now quarantine-only')
    `);

    // =========================================================================
    // TASK 7: LIST REMAINING TABLES IN MARKETING
    // =========================================================================
    console.log('\n' + '='.repeat(80));
    console.log('TASK 7: REMAINING TABLES IN MARKETING SCHEMA');
    console.log('='.repeat(80));

    const remaining = await client.query(`
      SELECT table_name
      FROM information_schema.tables
      WHERE table_schema = 'marketing'
      AND table_type = 'BASE TABLE'
    `);

    if (remaining.rows.length > 0) {
      console.log('\n  Tables still in marketing schema:');
      for (const row of remaining.rows) {
        const countRes = await client.query(`SELECT COUNT(*) FROM marketing."${row.table_name}"`);
        console.log(`    - ${row.table_name}: ${parseInt(countRes.rows[0].count).toLocaleString()} rows`);
      }
    } else {
      console.log('  marketing schema is now empty!');
    }

    // =========================================================================
    // FINAL VERIFICATION
    // =========================================================================
    console.log('\n' + '='.repeat(80));
    console.log('FINAL VERIFICATION');
    console.log('='.repeat(80));

    const finalTables = await client.query(`
      SELECT table_schema, table_name
      FROM information_schema.tables
      WHERE table_schema IN ('company', 'dol', 'people', 'clay', 'intake')
      AND table_type = 'BASE TABLE'
      ORDER BY table_schema, table_name
    `);

    console.log('\nNew schema layout:');
    let currentSchema = '';
    for (const row of finalTables.rows) {
      if (row.table_schema !== currentSchema) {
        currentSchema = row.table_schema;
        console.log(`\n  ${row.table_schema}:`);
      }
      const countRes = await client.query(`SELECT COUNT(*) FROM "${row.table_schema}"."${row.table_name}"`);
      console.log(`    - ${row.table_name}: ${parseInt(countRes.rows[0].count).toLocaleString()} rows`);
    }

    // Log completion
    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status, details)
      VALUES ('hub_spoke_reorg', 'COMPLETE', 'SUCCESS', 'Hub + Spoke architecture implemented')
    `);

    console.log('\n' + '='.repeat(80));
    console.log('MIGRATION COMPLETE!');
    console.log('='.repeat(80));

  } catch (error) {
    console.error('\nError:', error.message);

    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status, details)
      VALUES ('hub_spoke_reorg', 'ERROR', 'FAILED', $1)
    `, [error.message]);

    throw error;
  } finally {
    await client.end();
  }
}

migrate().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});

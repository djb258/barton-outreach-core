#!/usr/bin/env node
/**
 * PLE Hub + Spoke Schema Migration - Phase 2
 *
 * Migrates remaining tables from marketing schema:
 *   - person_movement_history, person_scores, people_invalid, people_resolution_queue -> people
 *   - company_events, company_sidecar, pipeline_events, pipeline_errors, company_slots -> company
 *   - dol_violations -> dol (rename to violations)
 *   - company_raw_wv, people_raw_wv -> intake
 *   - message_key_reference, email_verification, contact_enrichment, validation_failures_log, people_sidecar -> company
 */

const { Client } = require('pg');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '..', '..', '..', '.env') });

async function migratePhase2() {
  const client = new Client({
    connectionString: process.env.DATABASE_URL || process.env.NEON_CONNECTION_STRING
  });

  try {
    await client.connect();
    console.log('Connected to Neon PostgreSQL\n');

    // Log start
    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status, details)
      VALUES ('hub_spoke_reorg_phase2', 'START', 'INITIATED', 'Migrating remaining tables from marketing schema')
    `);

    // =========================================================================
    // Get current tables in marketing schema
    // =========================================================================
    console.log('='.repeat(80));
    console.log('CURRENT STATE: MARKETING SCHEMA');
    console.log('='.repeat(80));

    const marketingTables = await client.query(`
      SELECT table_name
      FROM information_schema.tables
      WHERE table_schema = 'marketing'
      AND table_type = 'BASE TABLE'
      ORDER BY table_name
    `);

    console.log('\nTables in marketing schema:');
    for (const row of marketingTables.rows) {
      const countRes = await client.query(`SELECT COUNT(*) FROM marketing."${row.table_name}"`);
      console.log(`  - ${row.table_name}: ${parseInt(countRes.rows[0].count).toLocaleString()} rows`);
    }

    // =========================================================================
    // MIGRATE TO PEOPLE SCHEMA
    // =========================================================================
    console.log('\n' + '='.repeat(80));
    console.log('MIGRATING TO PEOPLE SCHEMA');
    console.log('='.repeat(80));

    const peopleTables = [
      'person_movement_history',
      'person_scores',
      'people_invalid',
      'people_resolution_queue',
      'people_sidecar'
    ];

    for (const tableName of peopleTables) {
      const exists = await client.query(`
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'marketing' AND table_name = $1
      `, [tableName]);

      if (exists.rows.length > 0) {
        await client.query(`ALTER TABLE marketing."${tableName}" SET SCHEMA people`);
        console.log(`  Moved: marketing.${tableName} -> people.${tableName}`);
      } else {
        console.log(`  SKIP: ${tableName} not found in marketing schema`);
      }
    }

    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status, details)
      VALUES ('hub_spoke_reorg_phase2', 'MOVE_PEOPLE_TABLES', 'SUCCESS', 'Moved people-related tables to people schema')
    `);

    // =========================================================================
    // MIGRATE TO COMPANY SCHEMA
    // =========================================================================
    console.log('\n' + '='.repeat(80));
    console.log('MIGRATING TO COMPANY SCHEMA');
    console.log('='.repeat(80));

    const companyTables = [
      'company_events',
      'company_sidecar',
      'pipeline_events',
      'pipeline_errors',
      'company_slots',
      'message_key_reference',
      'email_verification',
      'contact_enrichment',
      'validation_failures_log'
    ];

    for (const tableName of companyTables) {
      const exists = await client.query(`
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'marketing' AND table_name = $1
      `, [tableName]);

      if (exists.rows.length > 0) {
        await client.query(`ALTER TABLE marketing."${tableName}" SET SCHEMA company`);
        console.log(`  Moved: marketing.${tableName} -> company.${tableName}`);
      } else {
        console.log(`  SKIP: ${tableName} not found in marketing schema`);
      }
    }

    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status, details)
      VALUES ('hub_spoke_reorg_phase2', 'MOVE_COMPANY_TABLES', 'SUCCESS', 'Moved company-related tables to company schema')
    `);

    // =========================================================================
    // MIGRATE TO DOL SCHEMA
    // =========================================================================
    console.log('\n' + '='.repeat(80));
    console.log('MIGRATING TO DOL SCHEMA');
    console.log('='.repeat(80));

    const dolViolations = await client.query(`
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'marketing' AND table_name = 'dol_violations'
    `);

    if (dolViolations.rows.length > 0) {
      await client.query(`ALTER TABLE marketing.dol_violations SET SCHEMA dol`);
      await client.query(`ALTER TABLE dol.dol_violations RENAME TO violations`);
      console.log('  Moved: marketing.dol_violations -> dol.violations');
    } else {
      console.log('  SKIP: dol_violations not found in marketing schema');
    }

    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status, details)
      VALUES ('hub_spoke_reorg_phase2', 'MOVE_DOL_TABLES', 'SUCCESS', 'Moved DOL violations to dol schema')
    `);

    // =========================================================================
    // MIGRATE TO INTAKE SCHEMA
    // =========================================================================
    console.log('\n' + '='.repeat(80));
    console.log('MIGRATING TO INTAKE SCHEMA');
    console.log('='.repeat(80));

    const intakeTables = [
      'company_raw_wv',
      'people_raw_wv'
    ];

    for (const tableName of intakeTables) {
      const exists = await client.query(`
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'marketing' AND table_name = $1
      `, [tableName]);

      if (exists.rows.length > 0) {
        await client.query(`ALTER TABLE marketing."${tableName}" SET SCHEMA intake`);
        console.log(`  Moved: marketing.${tableName} -> intake.${tableName}`);
      } else {
        console.log(`  SKIP: ${tableName} not found in marketing schema`);
      }
    }

    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status, details)
      VALUES ('hub_spoke_reorg_phase2', 'MOVE_INTAKE_TABLES', 'SUCCESS', 'Moved raw/wv tables to intake schema')
    `);

    // =========================================================================
    // FINAL CHECK: REMAINING TABLES IN MARKETING
    // =========================================================================
    console.log('\n' + '='.repeat(80));
    console.log('REMAINING TABLES IN MARKETING SCHEMA');
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
      console.log('  marketing schema is now EMPTY!');
    }

    // =========================================================================
    // FINAL VERIFICATION
    // =========================================================================
    console.log('\n' + '='.repeat(80));
    console.log('FINAL SCHEMA LAYOUT');
    console.log('='.repeat(80));

    const schemas = ['company', 'dol', 'people', 'clay', 'intake'];

    for (const schema of schemas) {
      const tables = await client.query(`
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = $1
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
      `, [schema]);

      console.log(`\n  ${schema.toUpperCase()}:`);
      for (const row of tables.rows) {
        const countRes = await client.query(`SELECT COUNT(*) FROM "${schema}"."${row.table_name}"`);
        console.log(`    - ${row.table_name}: ${parseInt(countRes.rows[0].count).toLocaleString()} rows`);
      }
    }

    // Log completion
    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status, details)
      VALUES ('hub_spoke_reorg_phase2', 'COMPLETE', 'SUCCESS', 'Phase 2 migration complete')
    `);

    console.log('\n' + '='.repeat(80));
    console.log('PHASE 2 MIGRATION COMPLETE!');
    console.log('='.repeat(80));

  } catch (error) {
    console.error('\nError:', error.message);

    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status, details)
      VALUES ('hub_spoke_reorg_phase2', 'ERROR', 'FAILED', $1)
    `, [error.message]);

    throw error;
  } finally {
    await client.end();
  }
}

migratePhase2().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});

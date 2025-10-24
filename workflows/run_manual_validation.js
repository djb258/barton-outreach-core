#!/usr/bin/env node
/**
 * Manual Pipeline Execution
 * Simulates the validation workflow by running SQL directly
 */

const { Client } = require('pg');
const fs = require('fs');
const path = require('path');

// Load environment
try {
  const envContent = fs.readFileSync(path.join(__dirname, '.env'), 'utf8');
  envContent.split('\n').forEach(line => {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('#')) {
      const [key, ...valueParts] = trimmed.split('=');
      if (key && valueParts.length > 0) {
        process.env[key] = valueParts.join('=').trim();
      }
    }
  });
} catch (e) {}

const DB_CONFIG = {
  host: 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
  port: 5432,
  database: 'Marketing DB',
  user: 'n8n_user',
  password: process.env.NEON_PASSWORD || 'n8n_secure_ivq5lxz3ej',
  ssl: { rejectUnauthorized: false }
};

const BATCH_ID = '20251024-WV-B1';

async function runValidation(client) {
  console.log('\n🔍 Step 1: Running Validation\n');

  // Get unvalidated companies
  const companies = await client.query(`
    SELECT id, company, website
    FROM intake.company_raw_intake
    WHERE import_batch_id = $1
      AND validated IS NULL
    LIMIT 50
  `, [BATCH_ID]);

  console.log(`  Found ${companies.rows.length} companies to validate\n`);

  let validated = 0;
  let failed = 0;

  for (const row of companies.rows) {
    const hasCompany = row.company && row.company.trim().length > 0;
    const hasWebsite = row.website && row.website.trim().length > 0;

    if (hasCompany && hasWebsite) {
      await client.query(`
        UPDATE intake.company_raw_intake
        SET
          validated = TRUE,
          validated_at = NOW(),
          validated_by = 'manual-test',
          validation_notes = 'Passed automated validation'
        WHERE id = $1
      `, [row.id]);
      validated++;
    } else {
      await client.query(`
        UPDATE intake.company_raw_intake
        SET
          validated = FALSE,
          validated_at = NOW(),
          validated_by = 'manual-test',
          validation_notes = 'Failed: Missing required fields'
        WHERE id = $1
      `, [row.id]);
      failed++;
    }
  }

  console.log(`  ✅ Validated: ${validated}`);
  console.log(`  ❌ Failed: ${failed}\n`);

  return { validated, failed };
}

async function runPromotion(client) {
  console.log('🎯 Step 2: Running Promotion\n');

  // Call the promotion function
  const result = await client.query(`
    SELECT shq.promote_company_records($1, 'manual-test') as result
  `, [BATCH_ID]);

  console.log(`  ✅ Promotion function executed\n`);

  // Check promoted companies
  const promoted = await client.query(`
    SELECT COUNT(*) as count
    FROM marketing.company_master
    WHERE import_batch_id = $1
  `, [BATCH_ID]);

  console.log(`  Promoted companies: ${promoted.rows[0].count}\n`);

  return promoted.rows[0].count;
}

async function checkSlots(client) {
  console.log('🎰 Step 3: Checking Slots\n');

  const slots = await client.query(`
    SELECT COUNT(*) as count
    FROM marketing.company_slots
    WHERE company_unique_id IN (
      SELECT company_unique_id
      FROM marketing.company_master
      WHERE import_batch_id = $1
    )
  `, [BATCH_ID]);

  console.log(`  Total slots: ${slots.rows[0].count}\n`);

  return slots.rows[0].count;
}

async function generateReport(client) {
  console.log('\n════════════════════════════════════════════════════════════════════════════════');
  console.log('📊 PIPELINE EXECUTION REPORT');
  console.log('════════════════════════════════════════════════════════════════════════════════\n');

  // Intake stats
  const intake = await client.query(`
    SELECT
      COUNT(*) as total,
      COUNT(*) FILTER (WHERE validated = TRUE) as validated,
      COUNT(*) FILTER (WHERE validated = FALSE) as failed,
      COUNT(*) FILTER (WHERE validated IS NULL) as pending
    FROM intake.company_raw_intake
    WHERE import_batch_id = $1
  `, [BATCH_ID]);

  // Promotion stats
  const promotion = await client.query(`
    SELECT
      COUNT(*) as promoted,
      MIN(created_at) as first_promo,
      MAX(created_at) as last_promo
    FROM marketing.company_master
    WHERE import_batch_id = $1
  `, [BATCH_ID]);

  // Slot stats
  const slots = await client.query(`
    SELECT COUNT(*) as count
    FROM marketing.company_slots
    WHERE company_unique_id IN (
      SELECT company_unique_id
      FROM marketing.company_master
      WHERE import_batch_id = $1
    )
  `, [BATCH_ID]);

  const intakeStats = intake.rows[0];
  const promotionStats = promotion.rows[0];
  const slotCount = slots.rows[0].count;

  console.log(`Batch ID: ${BATCH_ID}`);
  console.log(`Date: ${new Date().toISOString()}\n`);

  console.log('| Stage | Metric | Value |');
  console.log('|-------|--------|-------|');
  console.log(`| Intake | Total Companies | ${intakeStats.total} |`);
  console.log(`| Intake | ✅ Validated | ${intakeStats.validated} |`);
  console.log(`| Intake | ❌ Failed | ${intakeStats.failed} |`);
  console.log(`| Intake | ⏳ Pending | ${intakeStats.pending} |`);
  console.log(`| Promotion | Promoted to Master | ${promotionStats.promoted} |`);
  console.log(`| Slots | Total Slots Created | ${slotCount} |`);
  console.log(`| Slots | Avg per Company | ${(slotCount / (promotionStats.promoted || 1)).toFixed(1)} |`);

  console.log('\n════════════════════════════════════════════════════════════════════════════════');

  const success = intakeStats.validated > 0 && promotionStats.promoted > 0 && slotCount > 0;

  console.log(`\n${success ? '✅' : '⚠️'} Pipeline Status: ${success ? 'SUCCESS' : 'INCOMPLETE'}`);
  console.log('Flow: Validation → Promotion → Slot Creation\n');

  // Sample Barton IDs
  if (promotionStats.promoted > 0) {
    const samples = await client.query(`
      SELECT company_unique_id, company_name
      FROM marketing.company_master
      WHERE import_batch_id = $1
      LIMIT 5
    `, [BATCH_ID]);

    console.log('Sample Barton IDs:');
    samples.rows.forEach((row, idx) => {
      console.log(`  ${idx + 1}. ${row.company_unique_id} - ${row.company_name}`);
    });
    console.log('');
  }

  if (success) {
    console.log('✅ Ready for enrichment + email verification\n');
  }
}

async function main() {
  const client = new Client(DB_CONFIG);

  try {
    await client.connect();
    console.log('\n✅ Connected to Neon database');

    // Run validation
    await runValidation(client);

    // Run promotion
    await runPromotion(client);

    // Check slots (automated workflow should create these)
    await checkSlots(client);

    // Generate report
    await generateReport(client);

  } catch (error) {
    console.error('\n❌ Error:', error.message);
    console.error('Stack:', error.stack);
  } finally {
    await client.end();
  }
}

main();

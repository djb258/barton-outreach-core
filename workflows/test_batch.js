#!/usr/bin/env node
/**
 * Test Batch Validation Script
 * Checks the status of batch '20251024-WV-B1' in the database
 */

const { Client } = require('pg');

// Load environment variables
require('fs').readFileSync(require('path').join(__dirname, '.env'), 'utf8')
  .split('\n').forEach(line => {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('#')) {
      const [key, ...valueParts] = trimmed.split('=');
      if (key && valueParts.length > 0) {
        const value = valueParts.join('=').trim();
        if (!process.env[key]) {
          process.env[key] = value;
        }
      }
    }
  });

const BATCH_ID = '20251024-WV-B1';

const CONFIG = {
  host: 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
  port: 5432,
  database: 'Marketing DB',
  user: 'n8n_user',
  password: process.env.NEON_PASSWORD || 'n8n_secure_ivq5lxz3ej',
  ssl: { rejectUnauthorized: false }
};

async function testBatch() {
  const client = new Client(CONFIG);

  console.log('\n════════════════════════════════════════════════════════════════════════════════');
  console.log(`🧪 TESTING BATCH: ${BATCH_ID}`);
  console.log('════════════════════════════════════════════════════════════════════════════════\n');

  try {
    await client.connect();
    console.log('✅ Connected to Neon database\n');

    // Check if batch exists in intake
    console.log('📥 INTAKE STATUS:\n');
    const intakeResult = await client.query(`
      SELECT
        import_batch_id,
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE validated = TRUE) as validated,
        COUNT(*) FILTER (WHERE validated = FALSE) as failed,
        COUNT(*) FILTER (WHERE validated IS NULL) as pending
      FROM intake.company_raw_intake
      WHERE import_batch_id = $1
      GROUP BY import_batch_id
    `, [BATCH_ID]);

    if (intakeResult.rows.length === 0) {
      console.log(`  ⚠️  No records found for batch '${BATCH_ID}' in intake.company_raw_intake`);
      console.log(`  ℹ️  You may need to import data first\n`);
    } else {
      const stats = intakeResult.rows[0];
      console.log(`  Batch ID: ${stats.import_batch_id}`);
      console.log(`  Total Records: ${stats.total}`);
      console.log(`  ✅ Validated: ${stats.validated}`);
      console.log(`  ❌ Failed: ${stats.failed}`);
      console.log(`  ⏳ Pending: ${stats.pending}\n`);
    }

    // Check promotion status
    console.log('🎯 PROMOTION STATUS:\n');
    const promotionResult = await client.query(`
      SELECT COUNT(*) as promoted_count
      FROM marketing.company_master
      WHERE import_batch_id = $1
    `, [BATCH_ID]);

    const promotedCount = promotionResult.rows[0].promoted_count;
    console.log(`  Promoted to company_master: ${promotedCount} companies\n`);

    // Check slot creation
    if (promotedCount > 0) {
      console.log('🎰 SLOT CREATION STATUS:\n');
      const slotResult = await client.query(`
        SELECT
          COUNT(DISTINCT cs.company_unique_id) as companies_with_slots,
          COUNT(cs.slot_id) as total_slots
        FROM marketing.company_master c
        LEFT JOIN marketing.company_slots cs ON c.company_unique_id = cs.company_unique_id
        WHERE c.import_batch_id = $1
      `, [BATCH_ID]);

      const slotStats = slotResult.rows[0];
      console.log(`  Companies with slots: ${slotStats.companies_with_slots}`);
      console.log(`  Total slots created: ${slotStats.total_slots}`);
      console.log(`  Average slots per company: ${(slotStats.total_slots / promotedCount).toFixed(1)}\n`);
    }

    // Sample records
    console.log('📋 SAMPLE RECORDS (First 5):\n');
    const sampleResult = await client.query(`
      SELECT company, website, validated, validation_notes
      FROM intake.company_raw_intake
      WHERE import_batch_id = $1
      LIMIT 5
    `, [BATCH_ID]);

    if (sampleResult.rows.length > 0) {
      sampleResult.rows.forEach((row, idx) => {
        const status = row.validated === true ? '✅' : row.validated === false ? '❌' : '⏳';
        console.log(`  ${idx + 1}. ${status} ${row.company || '(no name)'}`);
        console.log(`     Website: ${row.website || '(none)'}`);
        console.log(`     Notes: ${row.validation_notes || '(none)'}\n`);
      });
    }

    console.log('════════════════════════════════════════════════════════════════════════════════');
    console.log('✅ Test complete\n');

  } catch (error) {
    console.error('❌ Error:', error.message);
    console.error('\nTroubleshooting:');
    console.error('  1. Check NEON_PASSWORD in .env file');
    console.error('  2. Verify n8n_user has SELECT permissions');
    console.error('  3. Ensure batch data exists in intake.company_raw_intake\n');
    process.exit(1);
  } finally {
    await client.end();
  }
}

if (require.main === module) {
  testBatch();
}

module.exports = { testBatch };

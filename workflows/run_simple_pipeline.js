#!/usr/bin/env node
/**
 * Simplified Pipeline - Direct SQL Approach
 * Runs validation → promotion → slot check without complex functions
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

function generateBartonId(sequence) {
  const category = '04'; // Marketing/Sales
  const division = '04'; // Outreach
  const dept = '01'; // Company
  const subsection = '84'; // Subsection identifier (matching existing pattern)
  const seq = String(sequence).padStart(5, '0');
  const ver = '001';
  return `${category}.${division}.${dept}.${subsection}.${seq}.${ver}`;
}

async function validateCompanies(client, limit = 100) {
  console.log(`\n🔍 STEP 1: Validating up to ${limit} companies\n`);

  const companies = await client.query(`
    SELECT id, company, website
    FROM intake.company_raw_intake
    WHERE import_batch_id = $1
      AND validated IS NULL
    LIMIT $2
  `, [BATCH_ID, limit]);

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
          validated_by = 'pipeline-test',
          validation_notes = 'Passed validation'
        WHERE id = $1
      `, [row.id]);
      validated++;
    } else {
      await client.query(`
        UPDATE intake.company_raw_intake
        SET
          validated = FALSE,
          validated_at = NOW(),
          validated_by = 'pipeline-test',
          validation_notes = 'Missing required fields'
        WHERE id = $1
      `, [row.id]);
      failed++;
    }
  }

  console.log(`  ✅ Validated: ${validated}`);
  console.log(`  ❌ Failed: ${failed}\n`);

  return { validated, failed };
}

async function promoteCompanies(client) {
  console.log('🎯 STEP 2: Promoting validated companies\n');

  // Get validated companies that haven't been promoted yet
  const companies = await client.query(`
    SELECT
      i.id,
      i.company,
      i.website,
      i.import_batch_id
    FROM intake.company_raw_intake i
    WHERE i.import_batch_id = $1
      AND i.validated = TRUE
      AND NOT EXISTS (
        SELECT 1 FROM marketing.company_master m
        WHERE m.company_name = i.company
          AND m.import_batch_id = i.import_batch_id
      )
  `, [BATCH_ID]);

  console.log(`  Found ${companies.rows.length} companies to promote\n`);

  let promoted = 0;

  for (const [index, row] of companies.rows.entries()) {
    const bartonId = generateBartonId(index + 1);

    try {
      await client.query(`
        INSERT INTO marketing.company_master (
          company_unique_id,
          company_name,
          website_url,
          import_batch_id,
          source_system,
          promoted_from_intake_at,
          created_at
        ) VALUES ($1, $2, $3, $4, 'intake-promotion', NOW(), NOW())
        ON CONFLICT (company_unique_id) DO NOTHING
      `, [bartonId, row.company, row.website, row.import_batch_id]);

      promoted++;
    } catch (error) {
      console.log(`    ⚠️  Failed to promote ${row.company}: ${error.message}`);
    }
  }

  console.log(`  ✅ Promoted: ${promoted} companies\n`);

  return promoted;
}

async function createSlots(client) {
  console.log('🎰 STEP 3: Creating company slots\n');

  // Get companies without slots
  const companies = await client.query(`
    SELECT c.company_unique_id, c.company_name
    FROM marketing.company_master c
    WHERE c.import_batch_id = $1
      AND NOT EXISTS (
        SELECT 1 FROM marketing.company_slots s
        WHERE s.company_unique_id = c.company_unique_id
      )
    LIMIT 50
  `, [BATCH_ID]);

  console.log(`  Found ${companies.rows.length} companies needing slots\n`);

  const roles = [
    { position: 1, title: 'CEO' },
    { position: 2, title: 'CFO' },
    { position: 3, title: 'HR Director' }
  ];

  let totalSlots = 0;

  for (const company of companies.rows) {
    for (const role of roles) {
      const slotId = company.company_unique_id.replace('.01.', `.0${role.position}.`);

      try {
        await client.query(`
          INSERT INTO marketing.company_slots (
            company_slot_unique_id,
            company_unique_id,
            slot_type,
            slot_label,
            created_at
          ) VALUES ($1, $2, $3, $4, NOW())
          ON CONFLICT (company_slot_unique_id) DO NOTHING
        `, [slotId, company.company_unique_id, 'executive', role.title]);

        totalSlots++;
      } catch (error) {
        console.log(`    ⚠️  Failed to create slot for ${company.company_name}: ${error.message}`);
      }
    }
  }

  console.log(`  ✅ Created: ${totalSlots} slots\n`);

  return totalSlots;
}

async function generateReport(client) {
  console.log('\n════════════════════════════════════════════════════════════════════════════════');
  console.log('📊 OUTREACH STEP 1 PIPELINE - FINAL REPORT');
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
    SELECT COUNT(*) as promoted
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

  const stats = {
    intake: intake.rows[0],
    promoted: promotion.rows[0].promoted,
    slots: slots.rows[0].count
  };

  console.log(`Batch ID: ${BATCH_ID}`);
  console.log(`Date: ${new Date().toISOString().split('T')[0]}\n`);

  console.log('| Stage | Metric | Value |');
  console.log('|-------|--------|-------|');
  console.log(`| Intake | Total Companies | ${stats.intake.total} |`);
  console.log(`| Intake | ✅ Validated | ${stats.intake.validated} |`);
  console.log(`| Intake | ❌ Failed | ${stats.intake.failed} |`);
  console.log(`| Intake | ⏳ Pending | ${stats.intake.pending} |`);
  console.log(`| Promotion | Promoted to Master | ${stats.promoted} |`);
  console.log(`| Slots | Total Slots Created | ${stats.slots} |`);
  console.log(`| Slots | Avg per Company | ${(stats.slots / (stats.promoted || 1)).toFixed(1)} |`);

  console.log('\n════════════════════════════════════════════════════════════════════════════════');

  const success = stats.intake.validated > 0 && stats.promoted > 0 && stats.slots > 0;

  console.log(`\n${success ? '✅ SUCCESS' : '⚠️ INCOMPLETE'}: Pipeline Flow Complete`);
  console.log('Flow: Validation → Promotion → Slot Creation\n');

  // Sample IDs
  if (stats.promoted > 0) {
    const samples = await client.query(`
      SELECT company_unique_id, company_name
      FROM marketing.company_master
      WHERE import_batch_id = $1
      LIMIT 5
    `, [BATCH_ID]);

    console.log('Sample Barton IDs (04.04.01 format):');
    samples.rows.forEach((row, idx) => {
      console.log(`  ${idx + 1}. ${row.company_unique_id} - ${row.company_name}`);
    });
    console.log('');
  }

  if (success) {
    console.log('✅ Ready for Enrichment + Email Verification\n');
    console.log('Next Steps:');
    console.log('  1. Set APIFY_TOKEN in n8n (see SET_APIFY_TOKEN.md)');
    console.log('  2. Activate Apify Enrichment workflow');
    console.log('  3. Activate MillionVerify Checker workflow');
    console.log('  4. Monitor executions in n8n UI\n');
  }

  return stats;
}

async function main() {
  const client = new Client(DB_CONFIG);

  try {
    await client.connect();
    console.log('\n════════════════════════════════════════════════════════════════════════════════');
    console.log('🚀 OUTREACH STEP 1 PIPELINE - WEST VIRGINIA BATCH');
    console.log('════════════════════════════════════════════════════════════════════════════════');
    console.log(`\nTesting batch: ${BATCH_ID}`);

    // Step 1: Validate
    await validateCompanies(client, 100);

    // Step 2: Promote
    await promoteCompanies(client);

    // Step 3: Create slots
    await createSlots(client);

    // Final report
    await generateReport(client);

  } catch (error) {
    console.error('\n❌ Pipeline Error:', error.message);
    console.error('Stack:', error.stack);
  } finally {
    await client.end();
  }
}

main();

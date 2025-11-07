#!/usr/bin/env node
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

async function completeSlots(client) {
  console.log('\n🎰 Completing Company Slots\n');

  // Get ALL companies without full slots (no LIMIT)
  const companies = await client.query(`
    SELECT c.company_unique_id, c.company_name
    FROM marketing.company_master c
    WHERE c.import_batch_id = $1
      AND (
        SELECT COUNT(*)
        FROM marketing.company_slots s
        WHERE s.company_unique_id = c.company_unique_id
      ) < 3
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
      // Generate slot ID by replacing .01. with .0X. where X is the role position
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

  console.log(`  ✅ Created: ${totalSlots} additional slots\n`);

  return totalSlots;
}

async function verifySlots(client) {
  const result = await client.query(`
    SELECT
      COUNT(DISTINCT c.company_unique_id) as companies_with_slots,
      COUNT(s.company_slot_unique_id) as total_slots,
      ROUND(COUNT(s.company_slot_unique_id)::numeric / COUNT(DISTINCT c.company_unique_id), 1) as avg_per_company
    FROM marketing.company_master c
    LEFT JOIN marketing.company_slots s ON s.company_unique_id = c.company_unique_id
    WHERE c.import_batch_id = $1
  `, [BATCH_ID]);

  const stats = result.rows[0];

  console.log('📊 FINAL SLOT STATISTICS:\n');
  console.log(`  Companies with slots: ${stats.companies_with_slots}`);
  console.log(`  Total slots: ${stats.total_slots}`);
  console.log(`  Average per company: ${stats.avg_per_company}\n`);

  return stats;
}

async function main() {
  const client = new Client(DB_CONFIG);

  try {
    await client.connect();
    console.log('✅ Connected to Neon database');

    await completeSlots(client);
    await verifySlots(client);

    console.log('✅ All slots completed!\n');

  } catch (error) {
    console.error('\n❌ Error:', error.message);
    console.error('Stack:', error.stack);
  } finally {
    await client.end();
  }
}

main();

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

async function fixBatchIds() {
  const client = new Client(DB_CONFIG);

  try {
    await client.connect();
    console.log('\n✅ Connected to Neon database\n');

    console.log('🔧 Fixing NULL batch IDs in intake.company_raw_intake\n');

    // Update NULL batch IDs
    const result = await client.query(`
      UPDATE intake.company_raw_intake
      SET import_batch_id = $1
      WHERE import_batch_id IS NULL
    `, [BATCH_ID]);

    console.log(`  ✅ Updated ${result.rowCount} records with batch ID: ${BATCH_ID}\n`);

    // Verify
    const verify = await client.query(`
      SELECT import_batch_id, COUNT(*) as count
      FROM intake.company_raw_intake
      GROUP BY import_batch_id
      ORDER BY COUNT(*) DESC
    `);

    console.log('📊 UPDATED BATCH DISTRIBUTION:\n');
    console.log('| Batch ID | Count |');
    console.log('|----------|-------|');
    verify.rows.forEach(row => {
      console.log(`| ${(row.import_batch_id || 'NULL').padEnd(8)} | ${row.count} |`);
    });
    console.log('');

  } catch (error) {
    console.error('❌ Error:', error.message);
  } finally {
    await client.end();
  }
}

fixBatchIds();

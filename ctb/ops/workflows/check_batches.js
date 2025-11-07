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

async function checkBatches() {
  const client = new Client(DB_CONFIG);

  try {
    await client.connect();
    console.log('\n✅ Connected to Neon database\n');

    // Check all batches in intake
    console.log('📦 BATCHES IN intake.company_raw_intake:\n');
    const batches = await client.query(`
      SELECT
        import_batch_id,
        COUNT(*) as count,
        MIN(created_at) as first_import,
        MAX(created_at) as last_import
      FROM intake.company_raw_intake
      GROUP BY import_batch_id
      ORDER BY MIN(created_at) DESC
      LIMIT 10
    `);

    if (batches.rows.length === 0) {
      console.log('  ⚠️  No batches found in intake.company_raw_intake\n');
    } else {
      console.log('| Batch ID | Count | First Import | Last Import |');
      console.log('|----------|-------|--------------|-------------|');
      batches.rows.forEach(b => {
        console.log(`| ${(b.import_batch_id || 'NULL').padEnd(8)} | ${String(b.count).padEnd(5)} | ${b.first_import?.toISOString().slice(0, 10) || 'N/A'} | ${b.last_import?.toISOString().slice(0, 10) || 'N/A'} |`);
      });
      console.log('');
    }

    // Check total records
    const total = await client.query('SELECT COUNT(*) as count FROM intake.company_raw_intake');
    console.log(`Total records in intake: ${total.rows[0].count}\n`);

    // Check company_master
    console.log('📊 BATCHES IN marketing.company_master:\n');
    const masterBatches = await client.query(`
      SELECT
        import_batch_id,
        COUNT(*) as count,
        MIN(created_at) as first_import
      FROM marketing.company_master
      GROUP BY import_batch_id
      ORDER BY MIN(created_at) DESC
      LIMIT 10
    `);

    if (masterBatches.rows.length === 0) {
      console.log('  ⚠️  No batches found in marketing.company_master\n');
    } else {
      console.log('| Batch ID | Count | First Import |');
      console.log('|----------|-------|--------------|');
      masterBatches.rows.forEach(b => {
        console.log(`| ${(b.import_batch_id || 'NULL').padEnd(8)} | ${String(b.count).padEnd(5)} | ${b.first_import?.toISOString().slice(0, 10) || 'N/A'} |`);
      });
      console.log('');
    }

    // Sample data
    console.log('📋 SAMPLE RECORDS FROM intake.company_raw_intake:\n');
    const sample = await client.query('SELECT company, website, import_batch_id, validated FROM intake.company_raw_intake LIMIT 5');

    if (sample.rows.length > 0) {
      sample.rows.forEach((row, idx) => {
        console.log(`  ${idx + 1}. ${row.company || '(no name)'}`);
        console.log(`     Batch: ${row.import_batch_id || 'NULL'}`);
        console.log(`     Website: ${row.website || '(none)'}`);
        console.log(`     Validated: ${row.validated === null ? 'NULL' : row.validated}\n`);
      });
    } else {
      console.log('  ⚠️  No records found\n');
    }

  } catch (error) {
    console.error('❌ Error:', error.message);
  } finally {
    await client.end();
  }
}

checkBatches();

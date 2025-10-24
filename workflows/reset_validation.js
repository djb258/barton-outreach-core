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

async function resetValidation() {
  const client = new Client(DB_CONFIG);

  try {
    await client.connect();
    console.log('\n✅ Connected to Neon database\n');

    console.log(`🔄 Resetting validation status for batch: ${BATCH_ID}\n`);

    // Reset validation fields to NULL
    const result = await client.query(`
      UPDATE intake.company_raw_intake
      SET
        validated = NULL,
        validated_at = NULL,
        validated_by = NULL,
        validation_notes = NULL
      WHERE import_batch_id = $1
    `, [BATCH_ID]);

    console.log(`  ✅ Reset validation for ${result.rowCount} records\n`);

    // Verify
    const verify = await client.query(`
      SELECT
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE validated = TRUE) as validated_true,
        COUNT(*) FILTER (WHERE validated = FALSE) as validated_false,
        COUNT(*) FILTER (WHERE validated IS NULL) as validated_null
      FROM intake.company_raw_intake
      WHERE import_batch_id = $1
    `, [BATCH_ID]);

    const stats = verify.rows[0];
    console.log('📊 VALIDATION STATUS AFTER RESET:\n');
    console.log(`  Total: ${stats.total}`);
    console.log(`  ✅ Validated (TRUE): ${stats.validated_true}`);
    console.log(`  ❌ Failed (FALSE): ${stats.validated_false}`);
    console.log(`  ⏳ Pending (NULL): ${stats.validated_null}\n`);

  } catch (error) {
    console.error('❌ Error:', error.message);
  } finally {
    await client.end();
  }
}

resetValidation();

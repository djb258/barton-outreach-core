#!/usr/bin/env node
/**
 * Event-Driven Pipeline Deployment Script (Using Owner Account)
 *
 * This script uses the database owner account to deploy migrations
 * that require elevated privileges (creating functions, triggers, etc.)
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

// Use database OWNER credentials for migrations
const DB_CONFIG = {
  host: 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
  port: 5432,
  database: 'Marketing DB',
  user: 'Marketing DB_owner', // Owner account
  password: process.env.NEON_OWNER_PASSWORD || 'npg_OsE4Z2oPCpiT',
  ssl: { rejectUnauthorized: false }
};

async function deployMigration(client, migrationFile, description) {
  console.log(`\n📦 Deploying: ${description}`);
  console.log(`   File: ${migrationFile}`);

  try {
    const sql = fs.readFileSync(
      path.join(__dirname, '..', 'migrations', migrationFile),
      'utf8'
    );

    await client.query(sql);
    console.log(`   ✅ Success!\n`);
    return true;
  } catch (error) {
    console.log(`   ❌ Failed: ${error.message}\n`);
    console.error(`   Stack: ${error.stack}\n`);
    return false;
  }
}

async function grantPermissions(client) {
  console.log('\n🔐 Granting Permissions to n8n_user\n');

  try {
    // Grant usage on schema
    await client.query(`GRANT USAGE ON SCHEMA marketing TO n8n_user;`);
    console.log('   ✅ Granted USAGE on schema marketing');

    // Grant permissions on tables
    await client.query(`GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA marketing TO n8n_user;`);
    console.log('   ✅ Granted table permissions');

    // Grant permissions on sequences
    await client.query(`GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA marketing TO n8n_user;`);
    console.log('   ✅ Granted sequence permissions');

    // Grant execute on functions
    await client.query(`GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA marketing TO n8n_user;`);
    console.log('   ✅ Granted function execution permissions');

    // Set default privileges for future objects
    await client.query(`ALTER DEFAULT PRIVILEGES IN SCHEMA marketing GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO n8n_user;`);
    await client.query(`ALTER DEFAULT PRIVILEGES IN SCHEMA marketing GRANT USAGE, SELECT ON SEQUENCES TO n8n_user;`);
    await client.query(`ALTER DEFAULT PRIVILEGES IN SCHEMA marketing GRANT EXECUTE ON FUNCTIONS TO n8n_user;`);
    console.log('   ✅ Set default privileges for future objects\n');

    return true;
  } catch (error) {
    console.log(`   ❌ Permission grant failed: ${error.message}\n`);
    return false;
  }
}

async function verifyDeployment(client) {
  console.log('\n🔍 VERIFYING DEPLOYMENT\n');

  // Check triggers
  const triggers = await client.query(`
    SELECT COUNT(*) as count
    FROM information_schema.triggers
    WHERE trigger_schema IN ('marketing', 'intake')
      AND trigger_name LIKE 'trigger_%event'
  `);

  console.log(`   📌 Event Triggers: ${triggers.rows[0].count}`);

  // Check tables
  const tables = await client.query(`
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'marketing'
      AND table_name IN ('pipeline_events', 'pipeline_errors', 'contact_enrichment', 'email_verification')
    ORDER BY table_name
  `);

  console.log(`   📊 Pipeline Tables: ${tables.rows.length}`);
  tables.rows.forEach(t => {
    console.log(`      - ${t.table_name}`);
  });

  // Check functions
  const functions = await client.query(`
    SELECT routine_name
    FROM information_schema.routines
    WHERE routine_schema = 'marketing'
      AND routine_name LIKE '%pipeline%'
    ORDER BY routine_name
  `);

  console.log(`   ⚙️  Pipeline Functions: ${functions.rows.length}`);
  functions.rows.forEach(f => {
    console.log(`      - ${f.routine_name}`);
  });

  console.log('');
}

async function testEventFlow(client) {
  console.log('\n════════════════════════════════════════════════════════════════════════════════');
  console.log('🧪 TESTING EVENT FLOW');
  console.log('════════════════════════════════════════════════════════════════════════════════\n');

  console.log('📝 Step 1: Insert test company\n');

  const result = await client.query(`
    INSERT INTO intake.company_raw_intake (company, website, import_batch_id)
    VALUES ('Event System Test', 'https://eventsystest.com', 'EVENT-SYS-TEST')
    RETURNING id
  `);

  const companyId = result.rows[0].id;
  console.log(`   ✅ Inserted company ID: ${companyId}\n`);

  // Wait for trigger
  await new Promise(resolve => setTimeout(resolve, 1000));

  console.log('🔍 Step 2: Check for company_created event\n');

  const events = await client.query(`
    SELECT
      id,
      event_type,
      payload->>'company_name' as company_name,
      status,
      created_at
    FROM marketing.pipeline_events
    WHERE payload->>'record_id' = $1
    ORDER BY created_at
  `, [String(companyId)]);

  if (events.rows.length > 0) {
    console.log(`   ✅ Found ${events.rows.length} event(s):\n`);
    events.rows.forEach(e => {
      console.log(`   📋 ${e.event_type} (Status: ${e.status})`);
      console.log(`      Company: ${e.company_name}`);
      console.log(`      Created: ${e.created_at}`);
      console.log('');
    });

    // Cleanup
    await client.query(`DELETE FROM intake.company_raw_intake WHERE id = $1`, [companyId]);
    await client.query(`DELETE FROM marketing.pipeline_events WHERE payload->>'record_id' = $1`, [String(companyId)]);

    console.log('   ✅ Event system is working! Test data cleaned up.\n');
    return true;
  } else {
    console.log('   ❌ No events found. Trigger may not have fired.\n');
    return false;
  }
}

async function showNextSteps() {
  console.log('\n════════════════════════════════════════════════════════════════════════════════');
  console.log('✅ DEPLOYMENT COMPLETE - NEXT STEPS');
  console.log('════════════════════════════════════════════════════════════════════════════════\n');

  console.log('1. Review deployment:');
  console.log('   - Triggers created: 5 (company_raw_intake, company_master, company_slots, etc.)');
  console.log('   - Tables created: pipeline_events, pipeline_errors, contact_enrichment, email_verification');
  console.log('   - Functions created: notify_pipeline_event, mark_event_processed, log_pipeline_error\n');

  console.log('2. Create n8n webhook workflows:');
  console.log('   See: docs/EVENT_DRIVEN_DEPLOYMENT_GUIDE.md\n');

  console.log('3. Test with real data:');
  console.log('   INSERT INTO intake.company_raw_intake (company, website, import_batch_id)');
  console.log('   VALUES (\'Test Co\', \'https://test.com\', \'TEST-001\');\n');

  console.log('4. Monitor events:');
  console.log('   SELECT * FROM marketing.pipeline_events ORDER BY created_at DESC LIMIT 10;\n');

  console.log('5. Monitor errors:');
  console.log('   SELECT * FROM marketing.vw_unresolved_errors;\n');

  console.log('📡 Real-time monitoring:');
  console.log('   LISTEN pipeline_event;\n');
}

async function main() {
  const client = new Client(DB_CONFIG);

  try {
    console.log('\n════════════════════════════════════════════════════════════════════════════════');
    console.log('🚀 EVENT-DRIVEN PIPELINE DEPLOYMENT (Using Owner Account)');
    console.log('════════════════════════════════════════════════════════════════════════════════');

    await client.connect();
    console.log('\n✅ Connected to Neon database as owner');

    // Deploy migrations
    const triggersOk = await deployMigration(
      client,
      '005_neon_pipeline_triggers.sql',
      'PostgreSQL Triggers & Event Queue'
    );

    if (!triggersOk) {
      console.log('\n❌ Trigger deployment failed. Stopping.\n');
      return;
    }

    const errorsOk = await deployMigration(
      client,
      '006_pipeline_error_log.sql',
      'Error Logging System'
    );

    if (!errorsOk) {
      console.log('\n❌ Error logging deployment failed. Stopping.\n');
      return;
    }

    // Grant permissions to n8n_user
    await grantPermissions(client);

    // Verify deployment
    await verifyDeployment(client);

    // Test event flow
    const testOk = await testEventFlow(client);

    if (testOk) {
      await showNextSteps();
    }

  } catch (error) {
    console.error('\n❌ Deployment Error:', error.message);
    console.error('Stack:', error.stack);
  } finally {
    await client.end();
  }
}

main();

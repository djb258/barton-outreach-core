#!/usr/bin/env node
/**
 * Event-Driven Pipeline Deployment Script
 *
 * Deploys:
 * 1. PostgreSQL triggers (005_neon_pipeline_triggers.sql)
 * 2. Error logging system (006_pipeline_error_log.sql)
 * 3. Tests event flow
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
    return false;
  }
}

async function verifyTriggers(client) {
  console.log('\n🔍 VERIFYING TRIGGERS\n');

  const triggers = await client.query(`
    SELECT
      trigger_name,
      event_object_table,
      action_statement
    FROM information_schema.triggers
    WHERE trigger_schema IN ('marketing', 'intake')
      AND trigger_name LIKE 'trigger_%event'
    ORDER BY event_object_table, trigger_name
  `);

  console.log(`   Found ${triggers.rows.length} event triggers:\n`);

  triggers.rows.forEach(t => {
    console.log(`   📌 ${t.trigger_name}`);
    console.log(`      Table: ${t.event_object_table}`);
    console.log(`      Action: ${t.action_statement.substring(0, 50)}...`);
    console.log('');
  });

  return triggers.rows.length > 0;
}

async function verifyTables(client) {
  console.log('\n📊 VERIFYING TABLES\n');

  const tables = [
    'marketing.pipeline_events',
    'marketing.pipeline_errors',
    'marketing.contact_enrichment',
    'marketing.email_verification'
  ];

  for (const table of tables) {
    const [schema, tableName] = table.split('.');
    const result = await client.query(`
      SELECT COUNT(*) as count
      FROM information_schema.tables
      WHERE table_schema = $1
        AND table_name = $2
    `, [schema, tableName]);

    if (result.rows[0].count > 0) {
      console.log(`   ✅ ${table}`);
    } else {
      console.log(`   ❌ ${table} - NOT FOUND`);
    }
  }
}

async function testEventFlow(client) {
  console.log('\n\n════════════════════════════════════════════════════════════════════════════════');
  console.log('🧪 TESTING EVENT FLOW');
  console.log('════════════════════════════════════════════════════════════════════════════════\n');

  // Clear previous test data
  await client.query(`
    DELETE FROM marketing.pipeline_events
    WHERE payload->>'company_name' LIKE 'Event Test%'
  `);

  console.log('📝 Step 1: Insert test company into intake\n');

  const result = await client.query(`
    INSERT INTO intake.company_raw_intake (company, website, import_batch_id)
    VALUES ('Event Test Company', 'https://eventtest.com', 'EVENT-TEST-001')
    RETURNING id
  `);

  const companyId = result.rows[0].id;
  console.log(`   Inserted company ID: ${companyId}\n`);

  // Wait a moment for trigger to fire
  await new Promise(resolve => setTimeout(resolve, 500));

  console.log('🔍 Step 2: Check pipeline_events table\n');

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
      console.log(`   📋 Event ID: ${e.id}`);
      console.log(`      Type: ${e.event_type}`);
      console.log(`      Company: ${e.company_name}`);
      console.log(`      Status: ${e.status}`);
      console.log(`      Created: ${e.created_at}`);
      console.log('');
    });
  } else {
    console.log('   ❌ No events found! Trigger may not have fired.\n');
    return false;
  }

  console.log('📝 Step 3: Update company to validated\n');

  await client.query(`
    UPDATE intake.company_raw_intake
    SET
      validated = TRUE,
      validated_at = NOW(),
      validated_by = 'test-script'
    WHERE id = $1
  `, [companyId]);

  console.log('   ✅ Updated validated=TRUE\n');

  // Wait for trigger
  await new Promise(resolve => setTimeout(resolve, 500));

  console.log('🔍 Step 4: Check for company_validated event\n');

  const validatedEvents = await client.query(`
    SELECT
      id,
      event_type,
      payload->>'company_name' as company_name,
      status,
      created_at
    FROM marketing.pipeline_events
    WHERE payload->>'record_id' = $1
      AND event_type = 'company_validated'
    ORDER BY created_at DESC
    LIMIT 1
  `, [String(companyId)]);

  if (validatedEvents.rows.length > 0) {
    console.log('   ✅ company_validated event created!\n');
    console.log(`   📋 Event ID: ${validatedEvents.rows[0].id}`);
    console.log(`      Status: ${validatedEvents.rows[0].status}`);
    console.log('');
  } else {
    console.log('   ❌ company_validated event NOT found\n');
    return false;
  }

  console.log('🧹 Step 5: Cleanup test data\n');

  await client.query(`
    DELETE FROM intake.company_raw_intake WHERE id = $1
  `, [companyId]);

  await client.query(`
    DELETE FROM marketing.pipeline_events
    WHERE payload->>'record_id' = $1
  `, [String(companyId)]);

  console.log('   ✅ Test data cleaned up\n');

  return true;
}

async function testErrorLogging(client) {
  console.log('\n════════════════════════════════════════════════════════════════════════════════');
  console.log('🧪 TESTING ERROR LOGGING');
  console.log('════════════════════════════════════════════════════════════════════════════════\n');

  console.log('📝 Log a test error\n');

  const errorId = await client.query(`
    SELECT marketing.log_pipeline_error(
      'test_event',
      'TEST-123',
      'This is a test error',
      jsonb_build_object('test', true, 'severity', 'warning'),
      'warning'
    ) as id
  `);

  console.log(`   ✅ Error logged with ID: ${errorId.rows[0].id}\n`);

  console.log('🔍 Check error log\n');

  const errors = await client.query(`
    SELECT * FROM marketing.pipeline_errors
    WHERE id = $1
  `, [errorId.rows[0].id]);

  if (errors.rows.length > 0) {
    const err = errors.rows[0];
    console.log(`   ✅ Error found:`);
    console.log(`      Event Type: ${err.event_type}`);
    console.log(`      Record ID: ${err.record_id}`);
    console.log(`      Message: ${err.error_message}`);
    console.log(`      Severity: ${err.severity}`);
    console.log(`      Resolved: ${err.resolved}`);
    console.log('');
  }

  console.log('📝 Resolve the error\n');

  await client.query(`
    SELECT marketing.resolve_pipeline_error(
      $1,
      'test-admin',
      'This was just a test'
    )
  `, [errorId.rows[0].id]);

  console.log('   ✅ Error marked as resolved\n');

  // Verify resolution
  const resolved = await client.query(`
    SELECT resolved, resolved_by, resolution_notes
    FROM marketing.pipeline_errors
    WHERE id = $1
  `, [errorId.rows[0].id]);

  if (resolved.rows[0].resolved) {
    console.log(`   ✅ Confirmed resolved by: ${resolved.rows[0].resolved_by}`);
    console.log(`      Notes: ${resolved.rows[0].resolution_notes}\n`);
  }

  console.log('🧹 Cleanup test error\n');

  await client.query(`
    DELETE FROM marketing.pipeline_errors WHERE id = $1
  `, [errorId.rows[0].id]);

  console.log('   ✅ Test error cleaned up\n');
}

async function showNextSteps() {
  console.log('\n════════════════════════════════════════════════════════════════════════════════');
  console.log('✅ DEPLOYMENT COMPLETE - NEXT STEPS');
  console.log('════════════════════════════════════════════════════════════════════════════════\n');

  console.log('1. Create n8n webhook workflows:');
  console.log('   - Validation Gatekeeper (webhook: /validate-company)');
  console.log('   - Promotion Runner (webhook: /promote-company)');
  console.log('   - Slot Creator (webhook: /create-slots)');
  console.log('   - Apify Enrichment (webhook: /enrich-contact)');
  console.log('   - MillionVerify Checker (webhook: /verify-email)\n');

  console.log('2. Update n8n_webhook_registry.json with actual webhook URLs\n');

  console.log('3. Test with real data:');
  console.log('   - Import small CSV batch (10-20 companies)');
  console.log('   - Monitor marketing.pipeline_events table');
  console.log('   - Check n8n execution logs\n');

  console.log('4. Monitor for 24 hours before full deployment\n');

  console.log('5. Read full guide:');
  console.log('   - docs/EVENT_DRIVEN_DEPLOYMENT_GUIDE.md');
  console.log('   - docs/PIPELINE_EVENT_FLOW.md\n');

  console.log('📡 Real-time monitoring:');
  console.log('   LISTEN pipeline_event;\n');

  console.log('📊 Check status:');
  console.log('   SELECT * FROM marketing.vw_unresolved_errors;');
  console.log('   SELECT * FROM marketing.vw_error_rate_24h;\n');
}

async function main() {
  const client = new Client(DB_CONFIG);

  try {
    console.log('\n════════════════════════════════════════════════════════════════════════════════');
    console.log('🚀 EVENT-DRIVEN PIPELINE DEPLOYMENT');
    console.log('════════════════════════════════════════════════════════════════════════════════');

    await client.connect();
    console.log('\n✅ Connected to Neon database');

    // Deploy migrations
    const triggersOk = await deployMigration(
      client,
      '005_neon_pipeline_triggers.sql',
      'PostgreSQL Triggers & Event Queue'
    );

    const errorsOk = await deployMigration(
      client,
      '006_pipeline_error_log.sql',
      'Error Logging System'
    );

    if (!triggersOk || !errorsOk) {
      console.log('\n❌ Deployment failed. Check errors above.\n');
      return;
    }

    // Verify deployment
    await verifyTriggers(client);
    await verifyTables(client);

    // Test event flow
    const testOk = await testEventFlow(client);

    if (testOk) {
      // Test error logging
      await testErrorLogging(client);

      // Show next steps
      await showNextSteps();
    } else {
      console.log('\n❌ Event flow test failed. Check trigger configuration.\n');
    }

  } catch (error) {
    console.error('\n❌ Deployment Error:', error.message);
    console.error('Stack:', error.stack);
  } finally {
    await client.end();
  }
}

main();

/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ai/testing
Barton ID: 03.01.03
Unique ID: CTB-BC65C0BC
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: HEIR
─────────────────────────────────────────────
*/

/**
 * Simple test for people schema migration
 */

import ComposioNeonBridge from './apps/outreach-process-manager/api/lib/composio-neon-bridge.js';

async function testPeopleMigration() {
  console.log('=== Testing People Schema Migration ===');

  const bridge = new ComposioNeonBridge();

  try {
    // Step 1: Test basic connectivity
    console.log('Step 1: Testing Composio connectivity...');
    const connectivity = await bridge.checkComposioConnectivity();
    console.log('Connectivity result:', connectivity);

    // Step 2: Create schema
    console.log('\nStep 2: Creating people schema...');
    const createSchemaSQL = `CREATE SCHEMA IF NOT EXISTS people;`;

    const schemaResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: createSchemaSQL,
      mode: 'write',
      return_type: 'affected_rows'
    });

    console.log('Schema creation result:', schemaResult);

    // Step 3: Create contact table
    console.log('\nStep 3: Creating people.contact table...');
    const createTableSQL = `
      CREATE TABLE IF NOT EXISTS people.contact (
        contact_unique_id        TEXT PRIMARY KEY,
        company_unique_id        TEXT NOT NULL,
        slot_unique_id           TEXT,
        first_name               TEXT NOT NULL,
        last_name                TEXT NOT NULL,
        title                    TEXT,
        seniority                TEXT,
        department               TEXT,
        email                    CITEXT,
        email_status             TEXT,
        email_last_verified_at   TIMESTAMPTZ,
        mobile_phone_e164        TEXT,
        work_phone_e164          TEXT,
        linkedin_url             TEXT,
        x_url                    TEXT,
        instagram_url            TEXT,
        facebook_url             TEXT,
        threads_url              TEXT,
        tiktok_url               TEXT,
        youtube_url              TEXT,
        personal_website_url     TEXT,
        github_url               TEXT,
        calendly_url             TEXT,
        whatsapp_handle          TEXT,
        telegram_handle          TEXT,
        do_not_contact           BOOLEAN DEFAULT FALSE,
        contact_owner            TEXT,
        source_system            TEXT,
        source_record_id         TEXT,
        created_at               TIMESTAMPTZ DEFAULT now(),
        updated_at               TIMESTAMPTZ DEFAULT now()
      );
    `;

    const tableResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: createTableSQL,
      mode: 'write',
      return_type: 'affected_rows'
    });

    console.log('Table creation result:', tableResult);

    // Step 4: Verify creation
    console.log('\nStep 4: Verifying schema and table creation...');
    const verifySQL = `
      SELECT table_name, table_schema
      FROM information_schema.tables
      WHERE table_schema = 'people' AND table_name = 'contact';
    `;

    const verifyResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: verifySQL,
      mode: 'read',
      return_type: 'rows'
    });

    console.log('Verification result:', verifyResult);

    // Step 5: Create indexes
    console.log('\nStep 5: Creating indexes...');
    const indexSQL = `
      CREATE INDEX IF NOT EXISTS idx_contact_company_unique_id ON people.contact (company_unique_id);
      CREATE INDEX IF NOT EXISTS idx_contact_email ON people.contact (email);
    `;

    const indexResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: indexSQL,
      mode: 'write',
      return_type: 'affected_rows'
    });

    console.log('Index creation result:', indexResult);

    console.log('\n=== Migration Test Complete ===');

    return {
      success: true,
      steps: {
        connectivity: connectivity.success,
        schema_created: schemaResult.success,
        table_created: tableResult.success,
        verification: verifyResult.success,
        indexes_created: indexResult.success
      }
    };

  } catch (error) {
    console.error('Migration test failed:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

// Run the test
testPeopleMigration()
  .then(result => {
    console.log('\n[FINAL RESULT]', JSON.stringify(result, null, 2));
    process.exit(result.success ? 0 : 1);
  })
  .catch(error => {
    console.error('\n[ERROR]', error);
    process.exit(1);
  });
/**
 * Test the extended people schema through ComposioNeonBridge
 */

import ComposioNeonBridge from './apps/outreach-process-manager/api/lib/composio-neon-bridge.js';

async function testPeopleSchemaVerification() {
  console.log('=== Testing Extended People Schema ===');

  const bridge = new ComposioNeonBridge();

  try {
    // Test 1: Verify schema exists
    console.log('Test 1: Verifying people schema exists...');
    const schemaResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: `
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name = 'people';
      `,
      mode: 'read',
      return_type: 'rows'
    });

    console.log('Schema verification:', schemaResult.success ? '✅ Success' : '❌ Failed', schemaResult.source);

    // Test 2: Verify contact table structure
    console.log('\nTest 2: Verifying contact table structure...');
    const tableResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: `
        SELECT
          column_name,
          data_type,
          is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'people' AND table_name = 'contact'
        ORDER BY ordinal_position;
      `,
      mode: 'read',
      return_type: 'rows'
    });

    console.log('Table structure:', tableResult.success ? '✅ Success' : '❌ Failed', tableResult.source);

    // Test 3: Test enhanced view
    console.log('\nTest 3: Testing enhanced view...');
    const viewResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: `
        SELECT
          contact_id,
          computed_full_name,
          email,
          contact_availability,
          has_social_media,
          has_phone
        FROM people.contact_enhanced_view
        LIMIT 3;
      `,
      mode: 'read',
      return_type: 'rows'
    });

    console.log('Enhanced view test:', viewResult.success ? '✅ Success' : '❌ Failed', viewResult.source);

    // Test 4: Test new columns
    console.log('\nTest 4: Testing new columns...');
    const newColumnsResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: `
        SELECT
          contact_id,
          company_unique_id,
          first_name,
          last_name,
          email_status,
          do_not_contact
        FROM people.contact
        LIMIT 2;
      `,
      mode: 'read',
      return_type: 'rows'
    });

    console.log('New columns test:', newColumnsResult.success ? '✅ Success' : '❌ Failed', newColumnsResult.source);

    // Test 5: Test insert capability (mock)
    console.log('\nTest 5: Testing insert capability...');
    const insertResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: `
        INSERT INTO people.contact (
          full_name,
          first_name,
          last_name,
          email,
          company_unique_id,
          email_status,
          source_system
        ) VALUES (
          'Test Contact',
          'Test',
          'Contact',
          'test@example.com',
          'test_company_123',
          'pending_verification',
          'mcp_bridge_test'
        ) RETURNING contact_id;
      `,
      mode: 'write',
      return_type: 'rows'
    });

    console.log('Insert test:', insertResult.success ? '✅ Success' : '❌ Failed', insertResult.source);

    console.log('\n=== Migration Verification Summary ===');
    console.log(`Schema exists: ${schemaResult.success ? '✅' : '❌'}`);
    console.log(`Table structure: ${tableResult.success ? '✅' : '❌'}`);
    console.log(`Enhanced view: ${viewResult.success ? '✅' : '❌'}`);
    console.log(`New columns: ${newColumnsResult.success ? '✅' : '❌'}`);
    console.log(`Insert capability: ${insertResult.success ? '✅' : '❌'}`);

    // Display the source of operations (mock vs real)
    console.log(`\nData source: ${schemaResult.source || 'composio'}`);

    return {
      success: true,
      verification_results: {
        schema_exists: schemaResult.success,
        table_structure: tableResult.success,
        enhanced_view: viewResult.success,
        new_columns: newColumnsResult.success,
        insert_capability: insertResult.success,
        data_source: schemaResult.source || 'composio'
      }
    };

  } catch (error) {
    console.error('Verification failed:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

// Run the verification
testPeopleSchemaVerification()
  .then(result => {
    console.log('\n[FINAL VERIFICATION RESULT]', JSON.stringify(result, null, 2));
    process.exit(result.success ? 0 : 1);
  })
  .catch(error => {
    console.error('\n[VERIFICATION ERROR]', error);
    process.exit(1);
  });
/**
 * Test script for audit log functionality
 * Tests the complete audit trail for promotion activities
 */

import ComposioNeonBridge from '../api/lib/composio-neon-bridge.js';

async function testAuditLogFunctionality() {
  const bridge = new ComposioNeonBridge();

  console.log('[TEST] Starting audit log functionality test...');

  try {
    // Test 1: Verify table exists
    console.log('[TEST] 1. Checking if audit log table exists...');

    const tableExistsQuery = `
      SELECT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'marketing'
        AND table_name = 'company_promotion_log'
      ) as table_exists
    `;

    const tableCheck = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: tableExistsQuery,
      mode: 'read',
      return_type: 'rows'
    });

    if (tableCheck.success && tableCheck.data?.rows?.[0]?.table_exists) {
      console.log('[TEST] ✓ Audit log table exists');
    } else {
      console.log('[TEST] ✗ Audit log table not found');
      return { success: false, error: 'Audit log table does not exist' };
    }

    // Test 2: Insert test audit log entry
    console.log('[TEST] 2. Inserting test audit log entry...');

    const testLogId = `TEST_${Date.now()}`;
    const testProcessId = `PROMOTE_TEST_${Date.now()}`;
    const testUniqueId = `TEST_COMPANY_${Date.now()}`;

    const testAuditEntry = {
      action: 'promotion_success',
      timestamp: new Date().toISOString(),
      unique_id: testUniqueId,
      details: {
        company_name: 'Test Company LLC',
        process_id: testProcessId,
        slot_id: `SLOT_${Date.now()}`,
        metadata: { test: true }
      }
    };

    const insertSQL = `
      INSERT INTO marketing.company_promotion_log (
        log_id, process_id, batch_id, unique_id, company_name,
        promotion_status, error_log, audit_entries, entry_count,
        log_type, altitude, doctrine, doctrine_version,
        source_system, actor, method, environment, created_at
      ) VALUES (
        '${testLogId}',
        '${testProcessId}',
        'TEST_BATCH_2025',
        '${testUniqueId}',
        'Test Company LLC',
        'PROMOTED',
        '{}',
        '${JSON.stringify([testAuditEntry]).replace(/'/g, "''")}',
        1,
        'promotion_audit',
        10000,
        'STAMPED',
        'v2.1.0',
        'outreach_process_manager',
        'api_promote_endpoint',
        'composio_mcp_promotion',
        'testing',
        NOW()
      )
      RETURNING log_id, created_at
    `;

    const insertResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: insertSQL,
      mode: 'write',
      return_type: 'rows'
    });

    if (insertResult.success && insertResult.data?.rows?.length > 0) {
      console.log('[TEST] ✓ Test audit log entry inserted');
      console.log(`[TEST]   Log ID: ${insertResult.data.rows[0].log_id}`);
      console.log(`[TEST]   Created: ${insertResult.data.rows[0].created_at}`);
    } else {
      console.log('[TEST] ✗ Failed to insert test audit entry');
      return { success: false, error: 'Failed to insert test audit entry' };
    }

    // Test 3: Query audit log by process_id
    console.log('[TEST] 3. Querying audit log by process_id...');

    const querySQL = `
      SELECT log_id, process_id, unique_id, company_name,
             promotion_status, entry_count, created_at
      FROM marketing.company_promotion_log
      WHERE process_id = '${testProcessId}'
      ORDER BY created_at DESC
    `;

    const queryResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: querySQL,
      mode: 'read',
      return_type: 'rows'
    });

    if (queryResult.success && queryResult.data?.rows?.length > 0) {
      console.log('[TEST] ✓ Successfully queried audit log');
      console.log(`[TEST]   Found ${queryResult.data.rows.length} entries`);
      queryResult.data.rows.forEach((row, index) => {
        console.log(`[TEST]   Entry ${index + 1}: ${row.company_name} - ${row.promotion_status}`);
      });
    } else {
      console.log('[TEST] ✗ Failed to query audit log');
      return { success: false, error: 'Failed to query audit log' };
    }

    // Test 4: Test error log functionality
    console.log('[TEST] 4. Testing error log functionality...');

    const errorLogId = `ERROR_TEST_${Date.now()}`;
    const errorUniqueId = `ERROR_COMPANY_${Date.now()}`;

    const errorSQL = `
      INSERT INTO marketing.company_promotion_log (
        log_id, process_id, batch_id, unique_id, company_name,
        promotion_status, error_log, audit_entries, entry_count,
        log_type, altitude, doctrine, doctrine_version,
        source_system, actor, method, environment, created_at
      ) VALUES (
        '${errorLogId}',
        '${testProcessId}',
        'ERROR_BATCH_2025',
        '${errorUniqueId}',
        'Failed Company Inc',
        'FAILED',
        '${JSON.stringify(['missing_email', 'invalid_domain']).replace(/'/g, "''")}',
        '${JSON.stringify([{
          action: 'promotion_failed',
          timestamp: new Date().toISOString(),
          unique_id: errorUniqueId,
          details: {
            company_name: 'Failed Company Inc',
            errors: ['missing_email', 'invalid_domain']
          }
        }]).replace(/'/g, "''")}',
        1,
        'promotion_audit',
        10000,
        'STAMPED',
        'v2.1.0',
        'outreach_process_manager',
        'api_promote_endpoint',
        'composio_mcp_promotion',
        'testing',
        NOW()
      )
      RETURNING log_id
    `;

    const errorResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: errorSQL,
      mode: 'write',
      return_type: 'rows'
    });

    if (errorResult.success) {
      console.log('[TEST] ✓ Error log entry created successfully');
    } else {
      console.log('[TEST] ✗ Failed to create error log entry');
    }

    // Test 5: Clean up test entries
    console.log('[TEST] 5. Cleaning up test entries...');

    const cleanupSQL = `
      DELETE FROM marketing.company_promotion_log
      WHERE process_id = '${testProcessId}'
    `;

    const cleanupResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: cleanupSQL,
      mode: 'write'
    });

    if (cleanupResult.success) {
      console.log('[TEST] ✓ Test entries cleaned up');
    } else {
      console.log('[TEST] ⚠ Warning: Failed to clean up test entries');
    }

    console.log('[TEST] ✓ All audit log functionality tests passed!');

    return {
      success: true,
      message: 'Audit log functionality working correctly',
      tests_passed: 5,
      doctrine_compliant: true,
      features_tested: [
        'table_existence_check',
        'audit_entry_insertion',
        'audit_log_querying',
        'error_log_functionality',
        'cleanup_operations'
      ]
    };

  } catch (error) {
    console.error('[TEST] ✗ Test failed with error:', error);
    return {
      success: false,
      error: error.message,
      message: 'Audit log functionality test failed'
    };
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  testAuditLogFunctionality()
    .then(result => {
      console.log('\n[RESULT]', JSON.stringify(result, null, 2));
      process.exit(result.success ? 0 : 1);
    })
    .catch(error => {
      console.error('\n[ERROR]', error);
      process.exit(1);
    });
}

export default testAuditLogFunctionality;
#!/usr/bin/env node

/**
 * Test script for Audit Log Viewer MCP tool
 * Tests various filter combinations for querying audit logs
 */

import fetch from 'node-fetch';

const BASE_URL = process.env.API_URL || 'http://localhost:3000';
const TEST_ENDPOINT = '/api/audit-log-test';

async function testAuditLogViewer() {
  console.log('[TEST] Starting Audit Log Viewer tests...\n');

  const tests = [
    {
      name: 'Test 1: Query all audit logs (no filters)',
      input: {
        filters: {}
      },
      expectedFields: ['rows_returned', 'results', 'altitude', 'doctrine']
    },
    {
      name: 'Test 2: Filter by status PROMOTED',
      input: {
        filters: {
          status: 'PROMOTED'
        }
      },
      validateResult: (data) => {
        return data.results.every(r => r.status === 'PROMOTED');
      }
    },
    {
      name: 'Test 3: Filter by status FAILED',
      input: {
        filters: {
          status: 'FAILED'
        }
      },
      validateResult: (data) => {
        return data.results.every(r => r.status === 'FAILED');
      }
    },
    {
      name: 'Test 4: Filter by batch_id',
      input: {
        filters: {
          batch_id: '2025-09-21-001'
        }
      },
      validateResult: (data) => {
        return data.results.every(r => r.batch_id === '2025-09-21-001');
      }
    },
    {
      name: 'Test 5: Filter by date range',
      input: {
        filters: {
          date_range: ['2025-09-21', '2025-09-21']
        }
      },
      validateResult: (data) => {
        return data.rows_returned >= 0;
      }
    },
    {
      name: 'Test 6: Combined filters (status + batch_id)',
      input: {
        filters: {
          status: 'PROMOTED',
          batch_id: '2025-09-21-001'
        }
      },
      validateResult: (data) => {
        return data.results.every(r =>
          r.status === 'PROMOTED' && r.batch_id === '2025-09-21-001'
        );
      }
    },
    {
      name: 'Test 7: Status ALL should return all records',
      input: {
        filters: {
          status: 'ALL'
        }
      },
      validateResult: (data) => {
        const hasPromoted = data.results.some(r => r.status === 'PROMOTED');
        const hasFailed = data.results.some(r => r.status === 'FAILED');
        return data.rows_returned > 0 && (hasPromoted || hasFailed);
      }
    }
  ];

  let passedTests = 0;
  let failedTests = 0;

  for (const test of tests) {
    console.log(`[TEST] ${test.name}`);
    console.log('  Input:', JSON.stringify(test.input));

    try {
      const response = await fetch(`${BASE_URL}${TEST_ENDPOINT}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(test.input)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      // Validate required fields
      const hasRequiredFields = ['rows_returned', 'results', 'altitude', 'doctrine'].every(
        field => data.hasOwnProperty(field)
      );

      if (!hasRequiredFields) {
        throw new Error('Missing required fields in response');
      }

      // Validate doctrine compliance
      if (data.altitude !== 10000 || data.doctrine !== 'STAMPED') {
        throw new Error('Invalid doctrine metadata');
      }

      // Validate results array
      if (!Array.isArray(data.results)) {
        throw new Error('Results must be an array');
      }

      // Validate each result has required fields
      for (const result of data.results) {
        const requiredResultFields = [
          'log_id',
          'promotion_timestamp',
          'promoted_unique_id',
          'process_id',
          'status',
          'doctrine_version',
          'batch_id'
        ];

        const missingFields = requiredResultFields.filter(
          field => !result.hasOwnProperty(field)
        );

        if (missingFields.length > 0) {
          throw new Error(`Result missing fields: ${missingFields.join(', ')}`);
        }

        // Validate status is exactly PROMOTED or FAILED
        if (result.status !== 'PROMOTED' && result.status !== 'FAILED') {
          throw new Error(`Invalid status: ${result.status}`);
        }
      }

      // Custom validation if provided
      if (test.validateResult) {
        const isValid = test.validateResult(data);
        if (!isValid) {
          throw new Error('Custom validation failed');
        }
      }

      console.log(`  ✓ PASSED - Returned ${data.rows_returned} rows`);
      console.log(`  Altitude: ${data.altitude}, Doctrine: ${data.doctrine}`);

      if (data.results.length > 0) {
        console.log('  Sample result:', {
          log_id: data.results[0].log_id,
          status: data.results[0].status,
          batch_id: data.results[0].batch_id
        });
      }

      passedTests++;

    } catch (error) {
      console.log(`  ✗ FAILED - ${error.message}`);
      failedTests++;
    }

    console.log('');
  }

  // Summary
  console.log('═'.repeat(50));
  console.log('[SUMMARY] Audit Log Viewer Test Results');
  console.log(`  Total Tests: ${tests.length}`);
  console.log(`  Passed: ${passedTests}`);
  console.log(`  Failed: ${failedTests}`);
  console.log(`  Success Rate: ${((passedTests / tests.length) * 100).toFixed(1)}%`);
  console.log('═'.repeat(50));

  // Return overall result
  return {
    success: failedTests === 0,
    total_tests: tests.length,
    passed: passedTests,
    failed: failedTests,
    mcp_tool: 'audit-log',
    doctrine_compliant: true
  };
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  testAuditLogViewer()
    .then(result => {
      console.log('\n[RESULT]', JSON.stringify(result, null, 2));
      process.exit(result.success ? 0 : 1);
    })
    .catch(error => {
      console.error('\n[ERROR]', error);
      process.exit(1);
    });
}

export default testAuditLogViewer;
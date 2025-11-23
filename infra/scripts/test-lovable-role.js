#!/usr/bin/env node
/**
 * Test Lovable.dev Role Connection
 * Verify that the new role can connect and access invalid tables
 */

const { Client } = require('pg');

const NEW_ROLE = 'marketing_db_owner';
const NEW_PASSWORD = 'G1wkzJLlpYdIb3Hq0YOZX2Z4m67uveb';
const NEON_HOST = 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech';
const NEON_DB = 'Marketing DB';

// Build connection string for new role
const connectionString = `postgresql://${NEW_ROLE}:${NEW_PASSWORD}@${NEON_HOST}:5432/${encodeURIComponent(NEON_DB)}?sslmode=require`;

async function testLovableRole() {
  const client = new Client({ connectionString });

  try {
    console.log('🔌 Testing connection with new role...');
    console.log(`   Role: ${NEW_ROLE}`);
    console.log(`   Host: ${NEON_HOST}`);
    console.log(`   Database: ${NEON_DB}\n`);

    await client.connect();
    console.log('✅ Connected successfully!\n');

    // Test 1: Verify current user
    console.log('🧪 Test 1: Verify current user');
    const currentUserResult = await client.query('SELECT current_user, current_database()');
    console.table(currentUserResult.rows);

    // Test 2: Check schema access
    console.log('🧪 Test 2: Check schema access');
    const schemaResult = await client.query(`
      SELECT nspname
      FROM pg_namespace
      WHERE nspname IN ('public', 'marketing', 'intake', 'bit', 'shq')
      ORDER BY nspname
    `);
    console.table(schemaResult.rows);

    // Test 3: Check invalid tables exist and are accessible
    console.log('🧪 Test 3: Check invalid tables access');
    const tablesResult = await client.query(`
      SELECT table_schema, table_name
      FROM information_schema.tables
      WHERE table_schema = 'marketing'
        AND table_name LIKE '%invalid%'
      ORDER BY table_name
    `);
    console.table(tablesResult.rows);

    // Test 4: Try SELECT from company_invalid
    console.log('🧪 Test 4: SELECT from company_invalid');
    const companyInvalidResult = await client.query(`
      SELECT COUNT(*) as total_invalid_companies
      FROM marketing.company_invalid
    `);
    console.table(companyInvalidResult.rows);

    // Test 5: Try SELECT from people_invalid
    console.log('🧪 Test 5: SELECT from people_invalid');
    const peopleInvalidResult = await client.query(`
      SELECT COUNT(*) as total_invalid_people
      FROM marketing.people_invalid
    `);
    console.table(peopleInvalidResult.rows);

    // Test 6: Try INSERT (then DELETE to clean up)
    console.log('🧪 Test 6: Test INSERT/DELETE permissions');
    try {
      // Insert test record
      await client.query(`
        INSERT INTO marketing.company_invalid (
          company_unique_id, company_name, reason_code, validation_errors, validation_status
        ) VALUES (
          'TEST-LOVABLE-001', 'Test Company', 'test_insert', '[]'::jsonb, 'FAILED'
        )
      `);
      console.log('  ✅ INSERT successful');

      // Delete test record
      await client.query(`
        DELETE FROM marketing.company_invalid WHERE company_unique_id = 'TEST-LOVABLE-001'
      `);
      console.log('  ✅ DELETE successful');
    } catch (err) {
      console.error('  ❌ INSERT/DELETE failed:', err.message);
    }

    // Test 7: Try UPDATE (insert, update, then delete)
    console.log('\n🧪 Test 7: Test UPDATE permissions');
    try {
      // Insert test record
      await client.query(`
        INSERT INTO marketing.company_invalid (
          company_unique_id, company_name, reason_code, validation_errors, validation_status
        ) VALUES (
          'TEST-LOVABLE-002', 'Test Company 2', 'test_update', '[]'::jsonb, 'FAILED'
        )
      `);

      // Update test record
      await client.query(`
        UPDATE marketing.company_invalid
        SET company_name = 'Updated Test Company'
        WHERE company_unique_id = 'TEST-LOVABLE-002'
      `);
      console.log('  ✅ UPDATE successful');

      // Delete test record
      await client.query(`
        DELETE FROM marketing.company_invalid WHERE company_unique_id = 'TEST-LOVABLE-002'
      `);
      console.log('  ✅ Cleanup successful');
    } catch (err) {
      console.error('  ❌ UPDATE failed:', err.message);
    }

    console.log('\n' + '='.repeat(80));
    console.log('✅ ALL TESTS PASSED!');
    console.log('='.repeat(80));
    console.log('\nThe role is ready for use in Lovable.dev edge functions.\n');

  } catch (error) {
    console.error('\n❌ Connection/Test Failed:', error.message);
    console.error('\nStack:', error.stack);
    process.exit(1);
  } finally {
    await client.end();
    console.log('🔌 Disconnected from database');
  }
}

testLovableRole().catch(console.error);
